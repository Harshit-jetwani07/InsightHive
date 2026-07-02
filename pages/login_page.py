import streamlit as st
import hashlib
import secrets
import re
import os
import smtplib
from email.message import EmailMessage
from utils.auth import get_conn, log_activity, authenticate, create_user


def password_strength(password: str) -> tuple[int, str]:
    strength = 0
    if len(password) >= 8:
        strength += 1
    if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
        strength += 1
    if re.search(r"\d", password):
        strength += 1
    if re.search(r"[_@$%&*!#.-]", password):
        strength += 1
    labels = ["Weak", "Moderate", "Strong", "Excellent"]
    return strength, labels[max(strength, 1) - 1] if password else "Weak"


def user_exists(username: str = "", email: str = "") -> tuple[bool, str]:
    conn = get_conn()
    row = conn.execute(
        "SELECT username,email FROM users WHERE lower(username)=lower(?) OR lower(email)=lower(?)",
        (username.strip(), email.strip())
    ).fetchone()
    conn.close()
    if not row:
        return False, ""
    if row["username"].lower() == username.strip().lower():
        return True, "Username already exists."
    return True, "Email is already registered."


def get_smtp_setting(key: str, default: str = "") -> str:
    try:
        if "smtp" in st.secrets and key in st.secrets["smtp"]:
            return str(st.secrets["smtp"][key])
    except Exception:
        pass
    return os.getenv(f"SMTP_{key.upper()}", default)


def send_otp_email(to_email: str, username: str, otp: str) -> tuple[bool, str]:
    host = get_smtp_setting("host")
    port = int(get_smtp_setting("port", "587") or "587")
    sender = get_smtp_setting("user")
    password = get_smtp_setting("password")
    from_email = get_smtp_setting("from_email", sender)

    if not host or not sender or not password or not from_email:
        return False, "SMTP email settings are not configured."

    msg = EmailMessage()
    msg["Subject"] = "InsightHive password reset OTP"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(
        f"Hi {username},\n\n"
        f"Your InsightHive password reset OTP is: {otp}\n\n"
        "This code is valid for this reset session. If you did not request this, ignore this email.\n\n"
        "InsightHive"
    )

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        return True, "OTP sent to your registered email."
    except Exception as exc:
        return False, f"Email delivery failed: {exc}"


def mask_email(email: str) -> str:
    if "@" not in email:
        return email
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked = name[0] + "*"
    else:
        masked = name[0] + "*" * (len(name) - 2) + name[-1]
    return f"{masked}@{domain}"


def show_login_page():
    """Render the public product landing and secure workspace access."""
    st.markdown("""
    <style>
    .stApp {
        background:
            radial-gradient(circle at 12% 18%, rgba(92, 72, 210, .22), transparent 30rem),
            radial-gradient(circle at 86% 78%, rgba(20, 184, 166, .13), transparent 28rem),
            #070914 !important;
    }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stHeader"], header { display: none !important; }
    .block-container {
        padding-top: 2.6rem !important;
        padding-bottom: 2.6rem !important;
        max-width: 1280px !important;
    }
    
    div[data-testid="stVerticalBlock"] > div:has(.custom-login-box) {
        background: linear-gradient(160deg, #0f0f2a 0%, #14142e 100%) !important;
        border: 1px solid #2a2a5a !important;
        border-radius: 16px !important;
        padding: 35px 30px !important;
        max-width: 400px !important;
        margin: 0 auto !important;
        box-shadow: 0 10px 40px rgba(124, 106, 247, 0.15) !important;
    }
    div[data-testid="stVerticalBlock"] > div:has(.auth-shell-marker) {
        background: linear-gradient(155deg, rgba(17, 20, 48, .96), rgba(11, 18, 35, .96));
        border: 1px solid rgba(139, 124, 255, .28);
        border-radius: 24px;
        padding: 28px 30px 24px;
        box-shadow: 0 30px 90px rgba(0, 0, 0, .40);
    }
    .landing-kicker {
        display: inline-flex; align-items: center; gap: 8px;
        color: #7cebd8; font-size: .75rem; font-weight: 700;
        letter-spacing: .15em; text-transform: uppercase;
        border: 1px solid rgba(72, 219, 194, .25);
        background: rgba(27, 163, 143, .09);
        border-radius: 999px; padding: 7px 11px;
    }
    .landing-kicker:before {
        content: ""; width: 7px; height: 7px; border-radius: 50%;
        background: #55e6cc; box-shadow: 0 0 14px #55e6cc;
    }
    .brand-logo-marker { display: none; }
    .brand-overline {
        color: #7cebd8; font-size: .72rem; font-weight: 700;
        letter-spacing: .20em; text-transform: uppercase; margin: 8px 0 4px;
    }
    .brand-wordmark {
        color: #f7f5ff; font-size: clamp(3rem, 5.2vw, 4.8rem);
        line-height: .98; letter-spacing: -.055em; font-weight: 780;
        margin: 0 0 12px;
        text-shadow: 0 10px 38px rgba(0, 0, 0, .35);
    }
    .brand-wordmark span {
        background: linear-gradient(110deg, #7ddcf7 0%, #8d79ff 46%, #a146ff 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .brand-tagline {
        color: #9ea6c3; font-size: .9rem; font-weight: 500;
        letter-spacing: .04em; margin-bottom: 18px;
    }
    .landing-title {
        color: #f6f4ff; font-size: clamp(2.35rem, 4.4vw, 4.1rem);
        line-height: .98; letter-spacing: -.055em; font-weight: 750;
        margin: 22px 0 22px; max-width: 760px;
    }
    .landing-title span {
        background: linear-gradient(110deg, #a99cff, #67dfd0);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .landing-copy {
        color: #a8adc6; font-size: 1.08rem; line-height: 1.72;
        max-width: 650px; margin-bottom: 30px;
    }
    .landing-proof {
        display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px; max-width: 680px; margin: 0 0 28px;
    }
    .proof-card {
        min-height: 104px; padding: 15px;
        background: rgba(14, 18, 38, .66);
        border: 1px solid rgba(135, 124, 230, .18);
        border-radius: 15px;
    }
    .proof-card strong {
        color: #f0edff; display: block; font-size: 1.04rem; margin-bottom: 5px;
    }
    .proof-card span { color: #7f879f; font-size: .79rem; line-height: 1.35; }
    .landing-footnote {
        color: #6f7891; font-size: .78rem; letter-spacing: .02em;
    }
    .auth-eyebrow {
        color: #67dfd0; font-size: .72rem; font-weight: 700;
        letter-spacing: .14em; text-transform: uppercase; margin-top: 8px;
    }
    .auth-title {
        color: #f5f2ff; font-size: 1.75rem; font-weight: 700;
        letter-spacing: -.025em; margin: 7px 0 3px;
    }
    .auth-copy { color: #858ca7; font-size: .88rem; margin-bottom: 18px; }
    .login-title { text-align: center; font-size: 1.65rem; font-weight: 700; color: #a090f7; margin-bottom: 2px; }
    .login-sub { text-align: center; color: #6060a0; font-size: 0.88rem; margin-bottom: 20px; }
    .stTextInput > div > div > input {
        background: rgba(11, 14, 33, .90) !important;
        border: 1px solid rgba(129, 113, 238, .30) !important;
        color: #ededff !important; border-radius: 11px !important;
        min-height: 3rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #8c7cf8 !important;
        box-shadow: 0 0 0 3px rgba(124, 106, 247, .13) !important;
    }
    
    div[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }
    div[data-testid="stFormSubmitButtonHint"] { display: none !important; }
    
    /*  TARGETED CENTER ALIGNMENT JUGAD FOR SIGN IN BUTTON */
    div[data-testid="stForm"] .stFormSubmitButton {
        display: flex !important;
        justify-content: center !important; /* Rocket center alignment block lock */
        width: 100% !important;
        margin-top: 25px !important;
    }
    div[data-testid="stForm"] .stFormSubmitButton button {
        background: linear-gradient(115deg, #6555d8 0%, #806cf5 55%, #39bfa9 145%) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.65rem 2.5rem !important; /* Smooth professional padding shape */
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(124, 106, 247, 0.25) !important;
    }
    div[data-testid="stVerticalBlock"] > div:has(.auth-shell-marker) .stButton > button {
        width: 100% !important;
        border-radius: 10px !important;
    }
    
    .link-wrapper {
        text-align: center;
        margin-top: 15px;
    }
    div.link-wrapper button {
        background: transparent !important;
        color: #7c6af7 !important;
        border: none !important;
        box-shadow: none !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
    }
    div.link-wrapper button:hover {
        color: #bfa6ff !important;
        text-decoration: underline !important;
    }
    @media (max-width: 850px) {
        .block-container { padding: 1.25rem 1rem 2rem !important; }
        .landing-title { font-size: 2.75rem; margin-top: 20px; }
        .brand-wordmark { font-size: 3.15rem; }
        .landing-proof { grid-template-columns: 1fr; }
        .proof-card { min-height: auto; }
        div[data-testid="stVerticalBlock"] > div:has(.auth-shell-marker) {
            padding: 22px 20px 18px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # State routers initializations
    if "reset_mode" not in st.session_state:
        st.session_state["reset_mode"] = "login"
    if "show_forgot_link" not in st.session_state:
        st.session_state["show_forgot_link"] = False

    current_mode = st.session_state["reset_mode"]

    if current_mode == "login":
        story_col, access_col = st.columns([1.3, .7], gap="large")
        with story_col:
            logo_col, wordmark_col = st.columns([.38, .62], gap="medium")
            with logo_col:
                st.markdown(
                    '<div class="brand-logo-marker"></div>',
                    unsafe_allow_html=True,
                )
                st.image("assets/insighthive-logo.jpeg", width=210)
            with wordmark_col:
                st.markdown(
                    """
                    <div class="brand-overline">Agentic decision intelligence</div>
                    <div class="brand-wordmark">Insight<span>Hive</span></div>
                    <div class="brand-tagline">AI agents. Smart insights. Better decisions.</div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown(
                """
                <div class="landing-kicker">Google ADK multi-agent intelligence</div>
                <div class="landing-title">Turn raw business data into<br><span>governed decisions.</span></div>
                <div class="landing-copy">
                  InsightHive coordinates specialist AI agents to inspect business data,
                  detect material risks, forecast what comes next, ground recommendations
                  through MCP, and prepare evidence-backed reports for human approval.
                </div>
                <div class="landing-proof">
                  <div class="proof-card"><strong>6 specialists</strong><span>One orchestrator coordinates ingestion, quality, analytics, insight, reporting, and governance.</span></div>
                  <div class="proof-card"><strong>Live evidence</strong><span>Every conclusion is connected to tool calls, traces, forecasts, and measurable success criteria.</span></div>
                  <div class="proof-card"><strong>Human governed</strong><span>Reports remain blocked until the approval gate confirms a reviewer has accepted them.</span></div>
                </div>
                <div class="landing-footnote">Built for the Google × Kaggle AI Agents Capstone · Agents for Business</div>
                """,
                unsafe_allow_html=True,
            )

        with access_col:
            st.markdown('<div class="auth-shell-marker"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="auth-eyebrow">Decision workspace</div>'
                '<div class="auth-title">Welcome to InsightHive</div>'
                '<div class="auth-copy">Sign in securely or launch the judge-ready sample experience.</div>',
                unsafe_allow_html=True,
            )
            with st.form(key="form_execution_login_premium"):
                username_input = st.text_input(
                    "Username", placeholder="Enter username", key="premium_login_username"
                )
                password_input = st.text_input(
                    "Password", type="password", placeholder="Enter password",
                    key="premium_login_password"
                )
                login_btn = st.form_submit_button("Sign in to workspace")

                if login_btn:
                    if not username_input or not password_input:
                        st.error("Please enter both username and password.")
                    else:
                        user = authenticate(username_input.strip(), password_input)
                        if user:
                            st.session_state["logged_in"] = True
                            st.session_state["role"] = user["role"]
                            st.session_state["username"] = user["username"]
                            st.session_state["current_page"] = "Dashboard"
                            st.session_state["show_forgot_link"] = False
                            log_activity(user["username"], "Login", "Session authorized.")
                            st.rerun()
                        else:
                            st.error("Invalid username, password, or inactive account.")

            link_col1, link_col2 = st.columns(2)
            with link_col1:
                if st.button("Forgot password?", key="premium_forgot"):
                    st.session_state["reset_mode"] = "forgot"
                    st.rerun()
            with link_col2:
                if st.button("Create account", key="premium_register"):
                    st.session_state["show_forgot_link"] = False
                    st.session_state["reset_mode"] = "register"
                    st.rerun()

            app_environment = os.getenv("APP_ENV", "development").lower()
            guest_enabled = (
                os.getenv("ALLOW_GUEST_DEMO", "").lower() == "true"
                or app_environment != "production"
            )
            if guest_enabled:
                st.divider()
                st.caption(
                    "Public judge demo · temporary isolated workspace · no account required"
                )
                if st.button(
                    "Launch judge demo →",
                    key="premium_guest_demo",
                    use_container_width=True,
                ):
                    guest_name = f"guest_{secrets.token_hex(3)}"
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "guest"
                    st.session_state["username"] = guest_name
                    st.session_state["current_page"] = "Dashboard"
                    st.session_state["auto_load_sample"] = True
                    log_activity(
                        guest_name, "Guest Demo Login",
                        "Temporary sample workspace created."
                    )
                    st.rerun()
        return

    with st.container():
        st.markdown('<div class="custom-login-box"></div>', unsafe_allow_html=True)
        
        #  1 LOGIN VIEW MODE (CENTERED STRINGS) 
        if current_mode == "login":
            _, logo_col, _ = st.columns([1, 1.45, 1])
            with logo_col:
                st.image("assets/insighthive-logo.jpeg", use_container_width=True)
            st.markdown('<div class="login-title">InsightHive</div><div class="login-sub">AI agents. Smart insights. Better decisions.</div>', unsafe_allow_html=True)
            
            with st.form(key="form_execution_login_isolated"):
                username_input = st.text_input("Username", placeholder="Enter username", key="login_username_widget")
                password_input = st.text_input("Password", type="password", placeholder="Enter password", key="login_password_widget")
                login_btn = st.form_submit_button("Sign In")

                if login_btn:
                    if not username_input or not password_input:
                        st.error("Please enter both username and password.")
                    else:
                        user = authenticate(username_input.strip(), password_input)
                        if user:
                            st.session_state["logged_in"] = True
                            st.session_state["role"] = user["role"]
                            st.session_state["username"] = user["username"]
                            st.session_state["current_page"] = "Dashboard"
                            st.session_state["show_forgot_link"] = False
                            log_activity(user["username"], "Login", "Session authorized.")
                            st.rerun()
                        else:
                            st.error("Invalid username, password, or inactive account.")
                            
            st.markdown('<div class="link-wrapper">', unsafe_allow_html=True)
            link_col1, link_col2 = st.columns(2)
            with link_col1:
                if st.button("Forgot Password?", key="lnk_switch_to_forgot"):
                    st.session_state["reset_mode"] = "forgot"
                    st.rerun()
            with link_col2:
                if st.button("Create Account", key="lnk_switch_to_register"):
                    st.session_state["show_forgot_link"] = False
                    st.session_state["reset_mode"] = "register"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            app_environment = os.getenv("APP_ENV", "development").lower()
            guest_enabled = (
                os.getenv("ALLOW_GUEST_DEMO", "").lower() == "true"
                or app_environment != "production"
            )
            if guest_enabled:
                st.divider()
                if st.button("Explore Sample Workspace", key="guest_demo_login", use_container_width=True):
                    guest_name = f"guest_{secrets.token_hex(3)}"
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "guest"
                    st.session_state["username"] = guest_name
                    st.session_state["current_page"] = "Dashboard"
                    st.session_state["auto_load_sample"] = True
                    log_activity(guest_name, "Guest Demo Login", "Temporary sample workspace created.")
                    st.rerun()

        #  2 PUBLIC REGISTRATION VIEW MODE
        elif current_mode == "register":
            _, logo_col, _ = st.columns([1, 1.45, 1])
            with logo_col:
                st.image("assets/insighthive-logo.jpeg", use_container_width=True)
            st.markdown('<div class="login-title">Create InsightHive Account</div><div class="login-sub">Start with a standard user workspace</div>', unsafe_allow_html=True)

            with st.form(key="form_execution_register_isolated"):
                reg_username = st.text_input("Username", placeholder="e.g. harshit_data", key="register_username_widget")
                reg_email = st.text_input("Email Address", placeholder="name@example.com", key="register_email_widget")
                reg_password = st.text_input("Password", type="password", placeholder="Choose a password", key="register_password_widget")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="register_confirm_widget")

                if reg_password:
                    strength, label = password_strength(reg_password)
                    colors = ["#ff4b4b", "#ffaa00", "#ccff00", "#00ffcc"]
                    display_strength = max(strength, 1)
                    st.markdown(
                        f"<p style='font-size:0.8rem; margin:0;'>Strength: <span style='color:{colors[display_strength-1]};'>{label}</span></p>",
                        unsafe_allow_html=True
                    )
                    st.progress(strength / 4)

                register_btn = st.form_submit_button("Create Account")

                if register_btn:
                    username = reg_username.strip()
                    email = reg_email.strip()
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

                    if not username or not email or not reg_password or not reg_confirm:
                        st.error("Please fill all registration fields.")
                    elif not re.match(r"^[a-zA-Z0-9_]{3,30}$", username):
                        st.error("Username must be 3-30 characters and can contain only letters, numbers, and underscores.")
                    elif not re.match(email_pattern, email):
                        st.error("Invalid email format.")
                    elif reg_password != reg_confirm:
                        st.error("Password and Confirm Password do not match.")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        exists, message = user_exists(username, email)
                        if exists:
                            st.error(message)
                        elif create_user(username, email, reg_password, "user"):
                            log_activity(username, "Register", "Self-service user account created.")
                            st.success("Account created successfully. Please sign in.")
                            st.session_state["reset_mode"] = "login"
                            st.session_state["show_forgot_link"] = False
                            st.rerun()
                        else:
                            st.error("Account creation failed. Try a different username or email.")

            st.markdown('<div class="link-wrapper">', unsafe_allow_html=True)
            if st.button("Back to Login", key="lnk_register_back_to_login"):
                st.session_state["show_forgot_link"] = False
                st.session_state["reset_mode"] = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        #  3 FORGOT VIEW MODE 
        elif current_mode == "forgot":
            _, logo_col, _ = st.columns([1, 1.45, 1])
            with logo_col:
                st.image("assets/insighthive-logo.jpeg", use_container_width=True)
            st.markdown('<div class="login-title">InsightHive</div><div class="login-sub">Reset access securely</div>', unsafe_allow_html=True)
            
            with st.form(key="form_execution_forgot_isolated"):
                target_user = st.text_input("Username or Email", placeholder="Enter your username or registered email", key="forgot_username_widget")
                gen_otp_btn = st.form_submit_button("Send OTP")
                
                if gen_otp_btn:
                    if target_user:
                        conn = get_conn()
                        user = conn.execute(
                            "SELECT * FROM users WHERE lower(username)=lower(?) OR lower(email)=lower(?)",
                            (target_user.strip(), target_user.strip())
                        ).fetchone()
                        conn.close()
                        
                        if user:
                            generated_otp = str(secrets.randbelow(899999) + 100000)
                            sent, message = send_otp_email(user["email"], user["username"], generated_otp)
                            if sent:
                                st.session_state["recovery_otp"] = generated_otp
                                st.session_state["recovery_user"] = user["username"]
                                st.session_state["recovery_email"] = user["email"]
                                st.session_state["reset_mode"] = "verify"
                                log_activity(user["username"], "Password OTP Sent", f"OTP sent to {mask_email(user['email'])}")
                                st.success(f"OTP sent to {mask_email(user['email'])}.")
                                st.rerun()
                            else:
                                st.error(message)
                                st.caption("Admin must configure SMTP settings in Streamlit secrets for email OTP delivery.")
                        else:
                            st.error("No account found for this username or email.")
                    else:
                        st.warning("Please enter your username or registered email.")
                        
            st.markdown('<div class="link-wrapper">', unsafe_allow_html=True)
            if st.button("Back to Login", key="lnk_back_to_login_view"):
                st.session_state["show_forgot_link"] = False 
                st.session_state["reset_mode"] = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        #  4 VERIFY VIEW MODE 
        elif current_mode == "verify":
            _, logo_col, _ = st.columns([1, 1.45, 1])
            with logo_col:
                st.image("assets/insighthive-logo.jpeg", use_container_width=True)
            st.markdown('<div class="login-title">InsightHive Security Key</div><div class="login-sub">Enter verification token</div>', unsafe_allow_html=True)
            
            if st.session_state.get("recovery_email"):
                st.info(f"Enter the OTP sent to {mask_email(st.session_state.get('recovery_email'))}.")
            else:
                st.info("Enter the OTP sent to your registered email.")
            
            with st.form(key="form_execution_verify_isolated"):
                input_otp = st.text_input("Enter 6-Digit OTP", placeholder="", key="verify_otp_widget")
                new_pwd = st.text_input("New Password", type="password", placeholder="", key="verify_pwd_widget")
                confirm_pwd = st.text_input("Confirm New Password", type="password", placeholder="", key="verify_confirm_widget")
                reset_submit = st.form_submit_button("Deploy New Password")
                
                if reset_submit:
                    if input_otp == st.session_state.get("recovery_otp"):
                        if new_pwd == confirm_pwd:
                            if len(new_pwd) >= 6:
                                conn = get_conn()
                                fresh_salt = secrets.token_hex(8)
                                hashed_val = hashlib.sha256(f"{fresh_salt}{new_pwd}".encode()).hexdigest()
                                
                                conn.execute(
                                    "UPDATE users SET password = ?, salt = ? WHERE username = ?",
                                    (hashed_val, fresh_salt, st.session_state.get("recovery_user"))
                                )
                                conn.commit()
                                conn.close()
                                
                                st.success("Access credentials updated. Proceeding to login.")
                                log_activity(st.session_state.get("recovery_user"), "Password Reset", "Password reset completed after email OTP verification.")
                                st.session_state["show_forgot_link"] = False 
                                st.session_state["reset_mode"] = "login"
                                st.session_state.pop("recovery_otp", None)
                                st.session_state.pop("recovery_user", None)
                                st.session_state.pop("recovery_email", None)
                                st.rerun()
                            else:
                                st.error("Password string must contain at least 6 characters.")
                        else:
                            st.error("Matching logic check failed: Mismatch strings.")
                    else:
                        st.error("Token verification string match failed.")
                        
            st.markdown('<div class="link-wrapper">', unsafe_allow_html=True)
            if st.button("Cancel Process", key="lnk_cancel_otp_flow_view"):
                st.session_state["show_forgot_link"] = False
                st.session_state["reset_mode"] = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

#  SINGLE DIRECT PAGE EXECUTION BRIDGE 
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if __name__ == "__main__":
    if not st.session_state["logged_in"]:
        show_login_page()
    else:
        st.markdown("<div style='text-align:center; padding:50px;'><h3>Dashboard Authenticated Successfully</h3><p style='color:#6060a0;'>Use the main sidebar panel to jump to workspaces.</p></div>", unsafe_allow_html=True)

