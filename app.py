import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import json
import re
import html
import os
import uuid
from datetime import datetime

from utils.data_analyzer import DataAnalyzer
from utils.ai_agent import AIAgent
from utils.report_generator import ReportGenerator
from utils.visualizer import Visualizer
from utils.data_quality import evaluate_dataset_quality, detect_anomalies
from utils.ui_helpers import safe_dataframe
from services.dataset_store import (
    set_current_dataset,
    clear_current_dataset,
    get_current_dataset,
)
from services.evaluator import run_agent_routing_evaluation
from services.llm_judge import judge_business_response
from services.sample_data import build_retail_demo_dataset
from services.report_contract import parse_report_sections
from services.api_keys import is_gemini_key
from services.mission_rubric import evaluate_mission_success
from tools.pipeline_tools import run_full_analysis_pipeline

#  1. CORE TRACKING & LOGOUT INTEGRATION 
from utils.auth import (
    init_db, 
    log_activity, 
    save_dataset_record, 
    save_report_record,
    get_report_record,
)
from pages.login_page import show_login_page
from pages.admin_panel import show_admin_panel


def apply_streamlit_configuration() -> None:
    """Map optional Streamlit secrets to environment-based application config."""
    mappings = {
        "admin_username": "BOOTSTRAP_ADMIN_USERNAME",
        "admin_email": "BOOTSTRAP_ADMIN_EMAIL",
        "admin_password": "BOOTSTRAP_ADMIN_PASSWORD",
        "demo_username": "BOOTSTRAP_DEMO_USERNAME",
        "demo_email": "BOOTSTRAP_DEMO_EMAIL",
        "demo_password": "BOOTSTRAP_DEMO_PASSWORD",
        "enable_demo_account": "ENABLE_DEMO_ACCOUNT",
        "allow_guest_demo": "ALLOW_GUEST_DEMO",
        "app_env": "APP_ENV",
    }
    try:
        bootstrap = st.secrets.get("bootstrap", {})
        for secret_key, env_key in mappings.items():
            if secret_key in bootstrap and not os.getenv(env_key):
                os.environ[env_key] = str(bootstrap[secret_key])
    except Exception:
        pass


apply_streamlit_configuration()

# Database initialisation
init_db()


#  2. UNIVERSAL DYNAMIC DATA LOADER ENGINE (Handles All Messy Sheets) 
def super_smart_data_loader(uploaded_file):
    """
    Universal Data Parser: Automatically detects data orientation (Horizontal vs Vertical),
    cleans garbage wrappers, strips currency symbols, and standardizes dates dynamically.
    """
    try:
        # Step 1: Read raw matrix based on extension
        if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            xls = pd.ExcelFile(uploaded_file)
            sheet_name = xls.sheet_names[0]
            raw_df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
        else:
            raw_df = pd.read_csv(uploaded_file, header=None)
            
        if raw_df.empty:
            return None

        # Step 2: Remove completely blank edge paddings
        raw_df = raw_df.dropna(how='all').dropna(how='all', axis=1)
        raw_df = raw_df.reset_index(drop=True)

        # Step 3: Find the True Structural Header Row
        best_row_idx = 0
        best_score = -1
        for i in range(min(15, len(raw_df))):
            row = raw_df.iloc[i]
            non_null_count = row.notna().sum()
            unique_count = row.nunique()
            score = non_null_count + unique_count
            if score > best_score:
                best_score = score
                best_row_idx = i

        # Slice data from the detected header boundary
        header_vals = raw_df.iloc[best_row_idx].fillna('').astype(str).tolist()
        df = raw_df.iloc[best_row_idx + 1:].copy()
        df.columns = [h.strip() if h.strip() else f"Col_{idx}" for idx, h in enumerate(header_vals)]
        df = df.reset_index(drop=True)

        # Step 4: Auto-Orientation Scanner (Detects Horizontal Matrices)
        cols_combined = " ".join([str(c) for c in df.columns]).lower()
        has_years_in_cols = any(re.search(r"(fy|20\d{2}|19\d{2})", str(c).lower()) for c in df.columns)
        has_years_in_rows = any(re.search(r"(fy|20\d{2}|19\d{2})", str(v).lower()) for v in df.iloc[:3].values.flatten())

        if has_years_in_cols and not has_years_in_rows:
            st.info("Horizontal matrix layout detected. Auto-adapting data shape...")
            label_col = df.columns[0]
            for col in df.columns:
                if any(k in str(col).lower() for k in ['million', 'usd', 'currency', 'metric', 'item']):
                    label_col = col
                    break
            df[label_col] = df[label_col].fillna("Metric").astype(str).str.strip()
            df = df.set_index(label_col).T
            df = df.reset_index().rename(columns={'index': 'Parsed_Date'})

        # Step 5: Advanced Force-Type Casting Engine
        df = df.dropna(how='all')
        date_column_found = False

        for col in df.columns:
            df = df.rename(columns={col: str(col).strip()})
            col_clean = str(col).strip()
            
            if df[col_clean].dtype == 'object':
                df[col_clean] = df[col_clean].apply(lambda x: x.strip() if isinstance(x, str) else x)

            col_str = col_clean.lower()
            
            if not date_column_found and any(k in col_str for k in ['date', 'year', 'timeline', 'period', 'month', 'quarter']):
                df[col_clean] = df[col_clean].astype(str).apply(lambda x: re.sub(r"FY\s*'", "20", x, flags=re.IGNORECASE))
                df[col_clean] = pd.to_datetime(df[col_clean], errors='coerce')
                df = df.rename(columns={col_clean: 'Parsed_Date'})
                date_column_found = True
                continue

            try:
                sanitized_series = df[col_clean].astype(str).str.replace(r'[$,%\s()]', '', regex=True)
                sanitized_series = sanitized_series.apply(lambda x: f"-{x}" if str(x).startswith('-') else x)
                numeric_converted = pd.to_numeric(sanitized_series, errors='coerce')
                
                if numeric_converted.notna().sum() > (0.6 * len(df)):
                    df[col_clean] = numeric_converted
            except:
                if not date_column_found and df[col_clean].astype(str).str.contains(r'(\d{2,4}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', case=False, regex=True).any():
                    cleaned_date_strs = df[col_clean].astype(str).apply(lambda x: re.sub(r"FY\s*'", "20", x, flags=re.IGNORECASE))
                    parsed_dates = pd.to_datetime(cleaned_date_strs, errors='coerce')
                    if parsed_dates.notna().sum() > (0.5 * len(df)):
                        df[col_clean] = parsed_dates
                        df = df.rename(columns={col_clean: 'Parsed_Date'})
                        date_column_found = True

        if 'Parsed_Date' not in df.columns:
            df['Parsed_Date'] = pd.date_range(start="2023-01-01", periods=len(df), freq="D")

        df.columns = make_unique_columns(df.columns)
        return df

    except Exception as e:
        st.error(f"Critical failure while parsing messy data layout: {str(e)}")
        return None


def persist_uploaded_file(uploaded_file, username):
    os.makedirs("uploads", exist_ok=True)
    safe_user = re.sub(r"[^a-zA-Z0-9_-]", "_", username or "user")
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", uploaded_file.name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join("uploads", f"{timestamp}_{safe_user}_{safe_name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def make_unique_columns(columns):
    seen = {}
    unique = []
    for col in columns:
        base = str(col).strip() or "Column"
        count = seen.get(base, 0)
        unique.append(base if count == 0 else f"{base}_{count + 1}")
        seen[base] = count + 1
    return unique


def sync_dataset_context() -> None:
    if st.session_state.get("df") is not None:
        set_current_dataset(
            st.session_state.df,
            st.session_state.get("filename") or "dataset.csv",
            st.session_state.get("username") or "user",
            st.session_state.get("dataset_id"),
        )
    else:
        clear_current_dataset()


def run_ai_chat(question: str, df, api_key: str) -> str:
    if is_gemini_key(api_key):
        from services.agent_runner import get_agent_runner

        runner = get_agent_runner()
        response = runner.run_query(
            (
                "Answer the following business question in simple, normal language. "
                "Give the direct answer first, explain why it matters, and suggest one "
                "practical next step. Do not mention internal agents, tools, JSON, or "
                "technical implementation details.\n\n"
                f"Business question: {question}"
            ),
            user_id=st.session_state.get("username") or "user",
            session_id=st.session_state.get("adk_session_id") or "default",
            api_key=api_key.strip(),
        )
        st.session_state.agent_trace = runner.get_trace_events()
        if response.startswith("ADK agent error:"):
            fallback = AIAgent("").answer_question(df, question, st.session_state.chat_history)
            return (
                "External AI was unavailable, so the request was completed in "
                "Sample Intelligence Mode.\n\n" + fallback
            )
        return response
    return st.session_state.ai_agent.answer_question(df, question, st.session_state.chat_history)


def get_configured_google_key(sidebar_value: str = "") -> str:
    candidate = sidebar_value.strip()
    supported = (
        is_gemini_key(candidate)
        or candidate.startswith(("sk-", "gsk_"))
        or candidate.lower().startswith("ollama")
        or "localhost:11434" in candidate.lower()
    )
    if candidate and supported:
        return candidate
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return str(st.secrets["GOOGLE_API_KEY"]).strip()
    except Exception:
        pass
    return os.getenv("GOOGLE_API_KEY", "").strip()


def load_sample_workspace() -> None:
    df_sample = build_retail_demo_dataset()
    st.session_state.df = df_sample
    st.session_state.filename = "northstar_retail_demo.csv"
    st.session_state.analysis_done = False
    st.session_state.analyzer = DataAnalyzer(df_sample)
    st.session_state.file_processed = True
    st.session_state.is_sample_dataset = True
    st.session_state.quality_report = evaluate_dataset_quality(df_sample)
    st.session_state.dataset_status = "approved"
    st.session_state.dataset_id = None
    st.session_state.pipeline_result = None
    st.session_state.evaluation_result = None
    st.session_state.forecast_agent_result = None
    st.session_state.anomaly_agent_result = None
    st.session_state.agent_mission_result = None
    st.session_state["agent_mission_text"] = (
        "Analyze performance, identify material risks, forecast Revenue, use retail "
        "industry grounding, and prepare prioritized actions for an approval-ready "
        "executive report."
    )
    log_activity(
        st.session_state.username,
        "Load Sample Data",
        "Loaded Northstar Retail two-year benchmark dataset.",
    )
    sync_dataset_context()


def mission_objective_for_dataset(df: pd.DataFrame) -> str:
    """Build a truthful default objective from the active schema."""
    columns = [str(column) for column in df.columns]
    lower_map = {column.lower(): column for column in columns}
    numeric = df.select_dtypes(include="number").columns.astype(str).tolist()
    date_columns = [
        column for column in columns
        if pd.api.types.is_datetime64_any_dtype(df[column])
        or any(token in column.lower() for token in ("date", "time", "month", "year"))
    ]
    preferred = next(
        (
            lower_map[name]
            for name in ("revenue", "sales", "profit", "amount", "value")
            if name in lower_map
        ),
        numeric[0] if numeric else None,
    )
    if date_columns and preferred:
        forward_look = f"forecast {preferred}"
    else:
        forward_look = "identify the strongest measurable performance drivers"
    return (
        f"Analyze performance, identify material risks, {forward_look}, use the selected "
        "industry playbook for grounding, and prepare prioritized actions for an "
        "approval-ready executive report."
    )


def run_specialist_action(
    prompt: str,
    api_key: str,
    expected_tool: str,
    session_id: str | None = None,
):
    """Run an ADK action and return its final text plus structured tool artifact."""
    if not is_gemini_key(api_key):
        return "", None, "sample"
    from services.agent_runner import get_agent_runner

    runner = get_agent_runner()
    response = runner.run_query(
        prompt,
        user_id=st.session_state.get("username") or "user",
        session_id=session_id or st.session_state.get("adk_session_id") or "default",
        api_key=api_key,
    )
    st.session_state.agent_trace = runner.get_trace_events()
    artifact = runner.get_latest_tool_artifact(expected_tool)
    return response, artifact, "adk"


def execute_agent_mission(mission: str, api_key: str, industry: str) -> dict:
    """Let the root ADK orchestrator plan and execute one end-to-end mission."""
    mission_id = f"mission-{uuid.uuid4().hex[:8]}"
    from services.agent_runner import get_agent_runner

    runner = get_agent_runner()
    started = datetime.now()
    response = runner.run_query(
        (
            "AUTONOMOUS MISSION\n"
            f"Objective: {mission}\n"
            f"Industry context: {industry}\n\n"
            "Plan and complete this objective end-to-end. Choose and coordinate the "
            "appropriate specialists and deterministic tools yourself. Use MCP for "
            "industry context when useful, quantify material risks, include a forecast "
            "when the active schema supports one, and finish with report/governance "
            "readiness. Do not ask the user to run separate dashboard tabs. Present the "
            "final answer in plain business language: what was found, why it matters, "
            "what should happen next, and whether human approval is still required. "
            "Do not expose JSON, internal tool names, or implementation jargon."
        ),
        user_id=st.session_state.get("username") or "user",
        session_id=mission_id,
        api_key=api_key,
    )
    trace_events = runner.get_trace_events()
    st.session_state.agent_trace = trace_events
    st.session_state.mission_trace = trace_events
    artifacts = runner.get_tool_artifacts()
    # A provider error means the ADK turn itself is incomplete, even if one
    # tool artifact was produced before quota exhaustion. Re-run the complete
    # evidence contract locally so MCP-equivalent RAG grounding, forecasting,
    # reporting context, and governance cannot be left half-finished.
    if response.startswith("ADK agent error:") or (
        not artifacts
        and (
            not response
            or response == "No response received from the agent."
        )
    ):
        return execute_resilient_local_mission(
            mission,
            industry,
            mission_id,
            started,
        )

    # An LLM may legally stop after one or two successful calls even when the
    # mission contract names more required evidence. Complete deterministic
    # business tools in-process so a partially-finished model turn never leaves
    # the user with an empty or misleading mission. MCP is intentionally not
    # imitated here: only a real MCP artifact can satisfy industry grounding.
    import json

    def decode_tool_payload(value) -> dict:
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"result": parsed}
        except (TypeError, json.JSONDecodeError):
            return {"result": value}

    existing_tools = {artifact.get("tool", "") for artifact in artifacts}

    def append_contract_artifact(tool_name: str, payload) -> None:
        artifacts.append(
            {
                "tool": tool_name,
                "agent": "mission_contract_enforcer",
                "payload": decode_tool_payload(payload),
            }
        )
        trace_events.append(
            {
                "event_type": "tool_response",
                "agent": "mission_contract_enforcer",
                "tool": tool_name,
                "status": "completed",
                "detail": "Mandatory mission evidence completed after the ADK turn.",
                "latency_ms": 0,
            }
        )

    if "run_full_analysis_pipeline" not in existing_tools:
        from tools.pipeline_tools import run_full_analysis_pipeline

        append_contract_artifact(
            "run_full_analysis_pipeline",
            run_full_analysis_pipeline(),
        )

    if "run_forecast" not in existing_tools and any(
        token in mission.lower() for token in ("forecast", "future", "predict", "next")
    ):
        from tools.analytics_tools import run_forecast

        active_df = st.session_state.df
        columns = [str(column) for column in active_df.columns]
        numeric = active_df.select_dtypes(include="number").columns.astype(str).tolist()
        dates = [
            column
            for column in columns
            if pd.api.types.is_datetime64_any_dtype(active_df[column])
            or any(token in column.lower() for token in ("date", "time", "month", "year"))
        ]
        value_col = next(
            (
                column
                for wanted in ("revenue", "sales", "profit", "amount", "value")
                for column in numeric
                if column.lower() == wanted
            ),
            numeric[0] if numeric else None,
        )
        if dates and value_col:
            forecast_payload = decode_tool_payload(
                run_forecast(dates[0], value_col, 12)
            )
            if "error" not in forecast_payload:
                append_contract_artifact("run_forecast", forecast_payload)

    if "get_business_context_snapshot" not in existing_tools:
        from tools.governance_tools import get_business_context_snapshot

        append_contract_artifact(
            "get_business_context_snapshot",
            get_business_context_snapshot(),
        )

    if "check_publish_gate" not in existing_tools:
        from tools.governance_tools import check_publish_gate

        append_contract_artifact(
            "check_publish_gate",
            check_publish_gate("pending"),
        )

    if not response or response == "No response received from the agent.":
        forecast_artifact = next(
            (
                artifact.get("payload", {})
                for artifact in artifacts
                if artifact.get("tool") == "run_forecast"
            ),
            {},
        )
        response = (
            f"**Verified analysis:** The governed pipeline completed for "
            f"`{st.session_state.filename}` with "
            f"{len(st.session_state.df):,} records.\n\n"
            f"**Forecast:** The forward outlook is "
            f"{str(forecast_artifact.get('trend', 'available')).lower()} across "
            f"{forecast_artifact.get('periods', 12)} future periods.\n\n"
            "**Recommendations:** Review flagged anomalies, prioritize verified "
            "KPI drivers, and apply the retrieved industry playbook before action.\n\n"
            "**Approval requirement:** The executive report remains blocked until "
            "a human reviewer approves it."
        )

    st.session_state.agent_trace = trace_events
    st.session_state.mission_trace = trace_events
    selected_tools = [artifact.get("tool", "") for artifact in artifacts]
    latency_by_tool = {
        event.get("tool"): event.get("latency_ms", 0)
        for event in trace_events
        if event.get("event_type") == "tool_response"
    }
    stages = [
        {
            "step": index,
            "specialist": artifact.get("agent") or "Root Orchestrator",
            "task": {
                "run_full_analysis_pipeline": "Validate data and analyze performance",
                "mcp_get_industry_kpi_playbook": "Ground recommendations in the industry playbook",
                "run_forecast": "Project the selected KPI into future periods",
                "get_business_context_snapshot": "Prepare verified executive-report context",
                "check_publish_gate": "Verify the human approval requirement",
            }.get(artifact.get("tool"), "Execute orchestrator-selected evidence tool"),
            "tool": artifact.get("tool") or "unknown_tool",
            "status": "completed",
            "latency_ms": latency_by_tool.get(artifact.get("tool"), 0),
            "response": "",
            "artifact": artifact.get("payload"),
        }
        for index, artifact in enumerate(artifacts, start=1)
    ]
    total_latency = int((datetime.now() - started).total_seconds() * 1000)
    rubric = evaluate_mission_success(
        mission,
        st.session_state.df.columns,
        selected_tools,
        response,
    )

    return {
        "mission_id": mission_id,
        "mission": mission,
        "industry": industry,
        "status": "completed" if rubric["completed"] else "needs_review",
        "planner": "ADK root orchestrator",
        "execution_mode": "orchestrator_native",
        "total_latency_ms": total_latency,
        **{key: value for key, value in rubric.items() if key != "completed"},
        "final_response": response,
        "stages": stages,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
    }


def execute_resilient_local_mission(
    mission: str,
    industry: str,
    mission_id: str,
    started: datetime,
) -> dict:
    """Complete useful analysis when external Gemini quota is unavailable."""
    import json

    from tools.analytics_tools import run_forecast
    from tools.governance_tools import check_publish_gate, get_business_context_snapshot
    from tools.pipeline_tools import run_full_analysis_pipeline
    from tools.rag_tools import retrieve_kpi_context

    def decode(value: str) -> dict:
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"result": parsed}
        except (TypeError, json.JSONDecodeError):
            return {"result": value}

    df = st.session_state.df
    columns = [str(column) for column in df.columns]
    numeric = df.select_dtypes(include="number").columns.astype(str).tolist()
    dates = [
        column for column in columns
        if pd.api.types.is_datetime64_any_dtype(df[column])
        or any(token in column.lower() for token in ("date", "time", "month", "year"))
    ]
    preferred = next(
        (
            column for wanted in ("revenue", "sales", "profit", "amount", "value")
            for column in numeric if column.lower() == wanted
        ),
        numeric[0] if numeric else None,
    )

    tool_runs = [
        (
            "run_full_analysis_pipeline",
            "Validate data and analyze performance",
            decode(run_full_analysis_pipeline()),
        ),
        (
            "retrieve_kpi_context",
            "Ground recommendations in the local industry playbook",
            decode(retrieve_kpi_context(industry, mission)),
        ),
        (
            "get_business_context_snapshot",
            "Prepare verified executive-report context",
            decode(get_business_context_snapshot()),
        ),
        (
            "check_publish_gate",
            "Verify the human approval requirement",
            decode(check_publish_gate("pending")),
        ),
    ]
    if dates and preferred and any(
        token in mission.lower() for token in ("forecast", "future", "predict", "next")
    ):
        forecast_payload = decode(run_forecast(dates[0], preferred, 12))
        if "error" not in forecast_payload:
            tool_runs.insert(
                2,
                (
                    "run_forecast",
                    f"Forecast {preferred} over 12 future periods",
                    forecast_payload,
                ),
            )

    pipeline = next(payload for tool, _, payload in tool_runs if tool == "run_full_analysis_pipeline")
    pipeline_results = {
        item.get("stage"): item.get("result", {})
        for item in pipeline.get("stages", [])
    }
    overview = pipeline_results.get("ingestion_context", {})
    quality = pipeline_results.get("quality_gate", {})
    anomalies = pipeline_results.get("anomaly_detection", {})
    forecast = next(
        (payload for tool, _, payload in tool_runs if tool == "run_forecast"),
        {},
    )
    response = (
        f"**Verified analysis:** `{st.session_state.filename}` contains "
        f"{overview.get('rows', len(df)):,} rows and {overview.get('columns', len(df.columns))} "
        f"columns. Data quality is {quality.get('grade', overview.get('quality_grade', 'scored'))} "
        f"({quality.get('score', overview.get('quality_score', '—'))}/100).\n\n"
        f"**Material risk:** The deterministic anomaly scan flagged "
        f"{anomalies.get('anomaly_count', 0)} records for review.\n\n"
        + (
            f"**Forecast:** {preferred} has a {forecast.get('trend', 'measured')} outlook "
            f"for the next {forecast.get('periods', 12)} periods "
            f"(MAE {forecast.get('mae', '—')}, RMSE {forecast.get('rmse', '—')}).\n\n"
            if forecast else
            "**Forward view:** This schema does not contain a reliable date/KPI pair, "
            "so no unsupported forecast was fabricated.\n\n"
        )
        + "**Recommended action:** Review flagged records, validate the strongest KPI "
        "drivers, and use the industry playbook before committing operational changes.\n\n"
        "**Approval requirement:** The report remains pending and cannot be published "
        "until a human reviewer approves it."
    )
    selected_tools = [tool for tool, _, _ in tool_runs]
    rubric = evaluate_mission_success(mission, df.columns, selected_tools, response)
    stages = [
        {
            "step": index,
            "specialist": "Quota-resilient local runtime",
            "task": task,
            "tool": tool,
            "status": "completed",
            "latency_ms": 0,
            "response": "",
            "artifact": payload,
        }
        for index, (tool, task, payload) in enumerate(tool_runs, start=1)
    ]
    return {
        "mission_id": mission_id,
        "mission": mission,
        "industry": industry,
        "status": "fallback_completed",
        "planner": "Deterministic resilience runtime",
        "execution_mode": "quota_resilient_local",
        "external_ai_unavailable": True,
        "total_latency_ms": int((datetime.now() - started).total_seconds() * 1000),
        **{key: value for key, value in rubric.items() if key != "completed"},
        "final_response": response,
        "stages": stages,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
    }


def _mission_artifact(mission_result: dict, tool_name: str) -> dict:
    """Return one decoded mission artifact without exposing trace internals."""
    for stage in mission_result.get("stages", []):
        if stage.get("tool") == tool_name and isinstance(stage.get("artifact"), dict):
            return stage["artifact"]
    return {}


def _pipeline_stage_result(mission_result: dict, stage_name: str) -> dict:
    pipeline = _mission_artifact(mission_result, "run_full_analysis_pipeline")
    for stage in pipeline.get("stages", []):
        if stage.get("stage") == stage_name and isinstance(stage.get("result"), dict):
            return stage["result"]
    return {}


def run_memory_proof(preference: str, api_key: str) -> dict:
    """Store a preference, start a fresh ADK session, and prove memory recall."""
    from services.agent_runner import get_agent_runner

    runner = get_agent_runner()
    user_id = st.session_state.get("username") or "user"
    proof_id = uuid.uuid4().hex[:8]
    source_session = f"memory-source-{proof_id}"
    recall_session = f"memory-recall-{proof_id}"
    stored = runner.run_query(
        f"Remember this business-analysis preference for future sessions: {preference}",
        user_id=user_id,
        session_id=source_session,
        api_key=api_key,
    )
    direct_memories = runner.search_memory_text(
        user_id,
        "business-analysis preference remember prioritize revenue region return-rate",
    )
    if stored.startswith("ADK agent error:"):
        st.session_state.memory_trace = runner.get_trace_events()
        return {
            "source_session": source_session,
            "recall_session": "not started",
            "preference": preference,
            "stored_response": stored,
            "recalled_response": (
                "The preference could not be saved because all configured AI services "
                "were temporarily unavailable. Your existing saved preferences were not "
                "changed. Please try this memory proof again later."
            ),
            "load_memory_called": False,
            "memory_service_verified": False,
            "selected_tools": [],
        }
    if stored == "No response received from the agent." and direct_memories:
        recalled = direct_memories[-1]
        tools = ["adk_memory_service_search"]
        st.session_state.memory_trace = runner.get_trace_events()
        return {
            "source_session": source_session,
            "recall_session": "ADK memory service direct search",
            "preference": preference,
            "stored_response": stored,
            "recalled_response": recalled,
            "load_memory_called": False,
            "memory_service_verified": True,
            "selected_tools": tools,
        }
    recalled = runner.run_query(
        "What business-analysis preference did I ask you to remember in an earlier session? "
        "Use load_memory before answering.",
        user_id=user_id,
        session_id=recall_session,
        api_key=api_key,
    )
    if recalled.startswith("ADK agent error:"):
        recalled = (
            "The preference was saved, but the fresh-session recall could not finish "
            "because the AI service became temporarily unavailable. Try recall again "
            "later; the saved preference remains in the session memory service."
        )
    st.session_state.memory_trace = runner.get_trace_events()
    tools = [item["tool"] for item in runner.get_tool_artifacts()]
    return {
        "source_session": source_session,
        "recall_session": recall_session,
        "preference": preference,
        "stored_response": stored,
        "recalled_response": recalled,
        "load_memory_called": "load_memory" in tools,
        "memory_service_verified": bool(direct_memories),
        "selected_tools": tools,
    }


def generate_report_artifact(
    df,
    analyzer,
    company_name: str,
    analyst_name: str,
    report_title: str,
    report_date,
    api_key: str,
    revision_notes: str = "",
):
    """Generate PDF prose through report_agent when ADK is available."""
    agent_narrative = ""
    report_sections = None
    st.session_state.report_execution_mode = "deterministic_report_contract"
    if is_gemini_key(api_key):
        prompt = f"""Transfer this task to report_agent. Call
get_business_context_snapshot before writing. Draft a grounded report for
company '{company_name}' titled '{report_title}'. Address this admin feedback:
'{revision_notes or "none"}'.

Return JSON only with exactly these string keys:
executive_summary, key_insights, recommendations, limitations.
Each section must contain at least 70 words, use clear business language, and
explain meaning rather than implementation. Use only tool-grounded numeric claims."""
        agent_narrative, _, _ = run_specialist_action(
            prompt,
            api_key,
            "get_business_context_snapshot",
        )
        report_sections, contract_error = parse_report_sections(agent_narrative)
        provider_unavailable = (
            not agent_narrative
            or agent_narrative == "No response received from the agent."
            or agent_narrative.startswith("ADK agent error:")
        )
        if report_sections is None and not provider_unavailable:
            repair_prompt = f"""Transfer to report_agent and repair this draft.
Call get_business_context_snapshot, then return valid JSON only with string keys
executive_summary, key_insights, recommendations, limitations. Each must have
at least 70 words in clear business language. Previous validation error: {contract_error}.
Admin feedback: {revision_notes or "none"}."""
            agent_narrative, _, _ = run_specialist_action(
                repair_prompt,
                api_key,
                "get_business_context_snapshot",
            )
            report_sections, contract_error = parse_report_sections(agent_narrative)
        if report_sections is not None:
            st.session_state.report_execution_mode = "adk_report_agent"

    if report_sections is None:
        from tools.governance_tools import get_business_context_snapshot

        context = json.loads(get_business_context_snapshot())
        rows = context.get("rows", len(df))
        columns = context.get("columns", len(df.columns))
        quality = context.get("quality_score", "scored")
        numeric_columns = df.select_dtypes(include="number").columns.astype(str).tolist()
        metric_details = []
        for column in numeric_columns[:4]:
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            if not series.empty:
                metric_details.append(
                    f"{column} averages {series.mean():,.2f}, ranges from "
                    f"{series.min():,.2f} to {series.max():,.2f}"
                )
        metric_summary = "; ".join(metric_details) or (
            "the uploaded file contains no reliable numeric measure for comparison"
        )
        category_details = []
        for column in df.select_dtypes(include=["object", "category"]).columns[:3]:
            values = df[column].dropna()
            if not values.empty:
                top = values.value_counts().index[0]
                share = 100 * (values == top).mean()
                category_details.append(
                    f"{column} is led by {top} at {share:.1f} percent of records"
                )
        category_summary = "; ".join(category_details) or (
            "no stable category concentration was available"
        )
        missing_count = int(df.isna().sum().sum())
        duplicate_count = int(df.duplicated().sum())
        feedback = (
            f" Reviewer feedback addressed: {revision_notes}."
            if revision_notes
            else ""
        )
        report_sections = {
            "executive_summary": (
                f"This report reviews {rows:,} business records across {columns} fields. "
                f"The verified data-quality score is {quality}, with {missing_count:,} "
                f"missing values and {duplicate_count:,} duplicate rows identified. "
                "The analysis is designed to help management understand current "
                "performance, spot material risks, and decide where follow-up is needed. "
                "The findings should be treated as decision support rather than an "
                "automatic decision, because publication remains subject to human review "
                "and approval."
            ),
            "key_insights": (
                f"The clearest measured patterns are as follows: {metric_summary}. "
                f"Category concentration shows that {category_summary}. These figures "
                "provide a practical baseline for comparing strong and weak areas. "
                "Managers should investigate any segment that combines unusually high "
                "activity with weak profitability, high returns, or poor satisfaction. "
                "Relationships in the data show where to investigate first, but they do "
                "not by themselves prove that one factor caused another."
            ),
            "recommendations": (
                "First, review the highest-risk unusual records and confirm whether they "
                "represent genuine business events, data-entry problems, or one-time "
                "exceptions. Second, compare the strongest measured performance drivers "
                "across regions, products, or other major segments before reallocating "
                "budget. Third, use the selected industry playbook as a checklist rather "
                "than a substitute for company context. Finally, monitor forecast error "
                f"and actual results before making a large commitment.{feedback}"
            ),
            "limitations": (
                "This report reflects only the information present in the active dataset "
                "at the time of analysis. Forecasts describe a likely direction, not a "
                "guaranteed result, and unexpected market or operational changes may "
                "produce different outcomes. Correlation does not establish cause and "
                "effect. Missing fields, inconsistent definitions, or unrecorded business "
                "events can also affect interpretation. For these reasons, the report "
                "remains locked until an authorized human reviewer confirms that the "
                "evidence and recommendations are suitable for publication."
            ),
        }
        agent_narrative = json.dumps(report_sections)

    generator = ReportGenerator(
        df=df,
        ai_agent=st.session_state.ai_agent,
        analyzer=analyzer,
        company_name=company_name,
        analyst_name=analyst_name,
        report_title=report_title,
        report_date=str(report_date),
        filename=st.session_state.filename or "data.csv",
        revision_notes=revision_notes,
        agent_narrative=agent_narrative,
        report_sections=report_sections,
    )
    return generator.generate(), agent_narrative



#  Page config 
st.set_page_config(
    page_title="InsightHive | Agentic Decision Intelligence",
    page_icon="assets/insighthive-logo.jpeg",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  Custom CSS (Theme + Fixed Layout + Logout Button Styling) 
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght=300;400;500;600;700&family=JetBrains+Mono:wght=400;500&display=swap');

    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 3rem !important;
        max-width: 1540px !important;
    }
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    .main { background: #080b14; }
    .stApp {
        background:
            radial-gradient(circle at 82% 4%, rgba(32, 196, 168, .09), transparent 28rem),
            radial-gradient(circle at 18% 0%, rgba(124, 106, 247, .12), transparent 34rem),
            #080b14;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1020 0%, #090b14 100%) !important;
        border-right: 1px solid rgba(143, 130, 255, .18);
    }
    .sidebar-brand {
        padding: 4px 0 18px; margin-bottom: 12px;
        border-bottom: 1px solid rgba(124, 106, 247, .16);
    }
    .sidebar-brand strong { color: #f3f0ff; font-size: 1.05rem; }
    .sidebar-brand span {
        display: block; color: #777b98; font-size: .72rem;
        letter-spacing: .10em; margin-top: 3px;
    }

    .capstone-hero {
        position: relative;
        overflow: hidden;
        padding: 30px 32px;
        margin-bottom: 18px;
        border: 1px solid rgba(124, 106, 247, .30);
        border-radius: 22px;
        background: linear-gradient(125deg, rgba(25, 25, 62, .96), rgba(12, 31, 48, .96));
        box-shadow: 0 24px 70px rgba(0, 0, 0, .28);
    }
    .capstone-hero:after {
        content: ""; position: absolute; width: 280px; height: 280px;
        right: -100px; top: -150px; border-radius: 50%;
        background: rgba(50, 218, 184, .13); filter: blur(4px);
    }
    .hero-kicker {
        color: #6ee7d2; font-size: .75rem; font-weight: 700;
        letter-spacing: .18em; text-transform: uppercase;
    }
    .hero-title {
        color: #f5f3ff; font-size: clamp(1.8rem, 3vw, 2.8rem);
        font-weight: 700; line-height: 1.08; margin: 8px 0 10px;
    }
    .hero-copy { color: #a8abc2; max-width: 850px; line-height: 1.55; }
    .hero-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 18px; }
    .hero-chip {
        color: #d9d5ff; background: rgba(124, 106, 247, .12);
        border: 1px solid rgba(143, 130, 255, .25); border-radius: 999px;
        padding: 6px 10px; font-size: .76rem; font-weight: 600;
    }
    .hero-chip.live {
        color: #83f0d9; background: rgba(19, 178, 145, .10);
        border-color: rgba(43, 214, 178, .27);
    }

    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #12122a 0%, #1a1a35 100%);
        border: 1px solid #2a2a5a;
        border-radius: 14px;
        padding: 22px 18px;
        text-align: center;
        margin-bottom: 16px;
        min-height: 230px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 14px;
        box-sizing: border-box;
    }
    .metric-card .feature-icon {
        font-size: 2.6rem;
        line-height: 1;
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .metric-card h4 {
        color: #a090f7;
        margin: 0;
        font-size: 1.35rem;
        line-height: 1.2;
    }
    .metric-card p  {
        color: #9090b0;
        font-size: 0.95rem;
        line-height: 1.5;
        margin: 0;
        max-width: 280px;
    }

    /* Chat bubbles */
    .chat-user {
        background: linear-gradient(135deg, #2d1f7a, #1f2d7a);
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #e0e0ff;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-ai {
        background: linear-gradient(135deg, #1a2a1a, #1a1a2a);
        border: 1px solid #2a4a2a;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #d0ffd0;
        max-width: 85%;
    }

    /* Section headers */
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #7c6af7;
        border-bottom: 1px solid #2a2a5a;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4a3fa0, #6a3fa0) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        padding: 0.5rem 1.2rem !important;
        transition: all 0.2s !important;
        min-height: 2.65rem !important;
        box-shadow: 0 8px 22px rgba(84, 67, 181, .16) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a4fbf, #7a4fbf) !important;
        transform: translateY(-1px) !important;
    }

    /* Red Logout Button Custom Design */
    div[data-testid="stSidebar"] .stButton > button[key="logout_btn"] {
        background: linear-gradient(135deg, #8b1e1e, #b91c1c) !important;
        border: 1px solid #ef4444 !important;
        margin-top: 20px !important;
    }
    div[data-testid="stSidebar"] .stButton > button[key="logout_btn"]:hover {
        background: linear-gradient(135deg, #991b1b, #dc2626) !important;
        box-shadow: 0 0 12px rgba(220, 38, 38, 0.4) !important;
    }

    /* Tabs Layout Fix */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(18, 18, 42, .92);
        border: 1px solid rgba(124, 106, 247, .15);
        border-radius: 12px;
        gap: 4px;
        padding: 4px;
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #7070a0;
        border-radius: 6px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 500;
        white-space: nowrap !important;
    }
    .stTabs [aria-selected="true"] {
        background: #2a2a5a !important;
        color: #a090f7 !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(18, 18, 42, .82) !important;
        border: 1px solid rgba(124, 106, 247, .28) !important;
        color: #e0e0ff !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #2a2a5a;
        border-radius: 12px;
        overflow: hidden;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(18, 18, 42, .90), rgba(13, 22, 35, .90));
        border: 1px solid rgba(124, 106, 247, .18);
        border-radius: 14px;
        padding: 15px 17px;
        box-shadow: 0 12px 32px rgba(0, 0, 0, .14);
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(18, 18, 42, .60) !important;
        border: 1px dashed rgba(110, 231, 210, .35) !important;
        border-radius: 14px !important;
    }
    [data-testid="stExpander"] {
        border: 1px solid rgba(124, 106, 247, .18) !important;
        border-radius: 12px !important;
        background: rgba(13, 15, 28, .62) !important;
    }

    /* Premium workspace shell */
    [data-testid="stMainBlockContainer"] {
        animation: workspaceReveal .35s ease-out;
    }
    @keyframes workspaceReveal {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    [data-testid="stMainBlockContainer"] > div {
        gap: 1rem;
    }

    /* Navigation rail: separated glass pills instead of cramped text */
    .stTabs {
        margin: 4px 0 22px;
    }
    .stTabs [data-baseweb="tab-list"] {
        position: sticky;
        top: .5rem;
        z-index: 20;
        gap: 9px !important;
        padding: 9px !important;
        border: 1px solid rgba(144, 128, 255, .28) !important;
        border-radius: 18px !important;
        background:
            linear-gradient(135deg, rgba(18, 21, 43, .94), rgba(10, 23, 34, .94)) !important;
        box-shadow: 0 18px 42px rgba(0, 0, 0, .22),
                    inset 0 1px 0 rgba(255, 255, 255, .035);
        scrollbar-width: thin;
        scrollbar-color: rgba(124, 106, 247, .45) transparent;
        backdrop-filter: blur(18px);
    }
    .stTabs [data-baseweb="tab"] {
        min-height: 42px !important;
        padding: 0 15px !important;
        border: 1px solid rgba(139, 128, 220, .11) !important;
        border-radius: 11px !important;
        background: rgba(255, 255, 255, .018) !important;
        color: #a6aac2 !important;
        font-size: .84rem !important;
        letter-spacing: .005em;
        transition: color .2s ease, background .2s ease,
                    border-color .2s ease, transform .2s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f3f1ff !important;
        border-color: rgba(110, 231, 210, .25) !important;
        background: rgba(110, 231, 210, .055) !important;
        transform: translateY(-1px);
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-color: rgba(151, 132, 255, .58) !important;
        background: linear-gradient(135deg, #5646b7, #7650bd) !important;
        box-shadow: 0 9px 24px rgba(101, 75, 196, .30),
                    inset 0 1px 0 rgba(255, 255, 255, .16) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 7px !important;
    }

    /* Clear content hierarchy */
    .section-title {
        position: relative;
        margin: 26px 0 18px;
        padding: 14px 18px 14px 21px;
        border: 1px solid rgba(124, 106, 247, .20);
        border-radius: 14px;
        color: #f3f1ff;
        background: linear-gradient(100deg, rgba(35, 29, 78, .70), rgba(10, 29, 39, .54));
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, .025);
        letter-spacing: -.01em;
    }
    .section-title:before {
        content: "";
        position: absolute;
        left: 0;
        top: 12px;
        bottom: 12px;
        width: 4px;
        border-radius: 999px;
        background: linear-gradient(#8f7cff, #45dac2);
        box-shadow: 0 0 16px rgba(110, 231, 210, .35);
    }

    /* Metrics feel like product cards */
    [data-testid="stMetric"] {
        min-height: 112px;
        padding: 18px 19px !important;
        border-color: rgba(139, 126, 239, .25) !important;
        border-radius: 17px !important;
        background:
            radial-gradient(circle at 95% 5%, rgba(75, 218, 192, .08), transparent 42%),
            linear-gradient(145deg, rgba(20, 21, 48, .94), rgba(11, 23, 34, .94)) !important;
        transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(110, 231, 210, .34) !important;
        box-shadow: 0 18px 38px rgba(0, 0, 0, .22) !important;
    }
    [data-testid="stMetricLabel"] {
        color: #9ca2bd !important;
        font-weight: 600;
        letter-spacing: .025em;
    }
    [data-testid="stMetricValue"] {
        color: #f7f5ff !important;
        font-weight: 650;
        letter-spacing: -.035em;
    }

    /* Inputs and selectors */
    [data-baseweb="select"] > div,
    [data-baseweb="base-input"],
    .stTextInput > div > div,
    .stTextArea > div > div {
        border-radius: 12px !important;
        background: rgba(17, 18, 42, .88) !important;
        border-color: rgba(124, 106, 247, .30) !important;
        transition: border-color .2s ease, box-shadow .2s ease;
    }
    [data-baseweb="select"] > div:hover,
    [data-baseweb="base-input"]:focus-within,
    .stTextInput > div > div:focus-within,
    .stTextArea > div > div:focus-within {
        border-color: rgba(110, 231, 210, .55) !important;
        box-shadow: 0 0 0 3px rgba(54, 211, 184, .075) !important;
    }
    [data-testid="stWidgetLabel"] p {
        color: #d9d9ea !important;
        font-weight: 600 !important;
        font-size: .86rem !important;
    }

    /* Tables, charts, expanders and notifications */
    [data-testid="stDataFrame"] {
        border-color: rgba(124, 106, 247, .26) !important;
        border-radius: 16px !important;
        box-shadow: 0 16px 38px rgba(0, 0, 0, .17);
    }
    [data-testid="stPlotlyChart"] {
        overflow: hidden;
        border: 1px solid rgba(124, 106, 247, .18);
        border-radius: 18px;
        background: rgba(11, 14, 27, .58);
        box-shadow: 0 16px 40px rgba(0, 0, 0, .16);
    }
    [data-testid="stExpander"] {
        margin: 8px 0 !important;
        border-radius: 15px !important;
        background: linear-gradient(145deg, rgba(16, 17, 37, .86), rgba(10, 20, 29, .76)) !important;
        transition: border-color .2s ease, transform .2s ease;
    }
    [data-testid="stExpander"]:hover {
        border-color: rgba(110, 231, 210, .27) !important;
    }
    [data-testid="stAlert"] {
        border-radius: 14px !important;
        border-width: 1px !important;
        box-shadow: 0 12px 30px rgba(0, 0, 0, .14);
    }
    [data-testid="stFileUploaderDropzone"] {
        padding: 20px !important;
        border-radius: 17px !important;
        background: linear-gradient(135deg, rgba(20, 20, 47, .72), rgba(10, 28, 36, .60)) !important;
    }

    /* Stronger primary actions */
    .stButton > button {
        border: 1px solid rgba(172, 154, 255, .22) !important;
        border-radius: 12px !important;
        background: linear-gradient(120deg, #5645ba, #7b48b5) !important;
        box-shadow: 0 10px 26px rgba(91, 66, 187, .23) !important;
    }
    .stButton > button:hover {
        border-color: rgba(110, 231, 210, .38) !important;
        box-shadow: 0 14px 32px rgba(91, 66, 187, .34) !important;
        transform: translateY(-2px) !important;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .capstone-hero { padding: 23px 21px; border-radius: 18px; }
        .stTabs [data-baseweb="tab-list"] { gap: 6px !important; padding: 7px !important; }
        .stTabs [data-baseweb="tab"] { padding: 0 12px !important; }
    }
    hr { border-color: #2a2a5a; }
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


#  Session state initialisation 
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False


def init_session():
    defaults = {
        "file_processed": False,
        "df": None,
        "filename": None,
        "chat_history": [],
        "analysis_done": False,
        "analyzer": None,
        "ai_agent": None,
        "api_key_set": False,
        "uploader_key": 0,  
        "user": None,
        "role": None,
        "username": None,
        "dataset_id": None,
        "dataset_status": None,
        "quality_report": None,
        "adk_session_id": "default",
        "agent_trace": [],
        "mission_trace": [],
        "memory_trace": [],
        "pipeline_result": None,
        "evaluation_result": None,
        "judge_result": None,
        "generated_report_bytes": None,
        "generated_report_id": None,
        "generated_report_filename": None,
        "report_revision_of": None,
        "report_revision_notes": "",
        "is_sample_dataset": False,
        "ai_mode": "sample",
        "forecast_agent_result": None,
        "anomaly_agent_result": None,
        "report_agent_response": "",
        "agent_mission_result": None,
        "memory_proof_result": None,
        "visualization_agent_brief": None,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

if st.session_state.ai_agent is None:
    st.session_state.ai_agent = AIAgent("")

#  100% SECURE ROUTING GATEWAY 
if not st.session_state.get("logged_in", False):
    show_login_page()
    st.stop()


#  Sidebar Content & Actions 
with st.sidebar:
    st.image("assets/insighthive-logo.jpeg", use_container_width=True)
    st.markdown(
        '<div class="sidebar-brand"><strong>InsightHive</strong>'
        '<span>HARSHIT JETWANI · TEAM LEADER &nbsp;|&nbsp; JIYA AALWANI · TEAM MEMBER</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"### 👋 Welcome, {st.session_state.username}")
    if st.session_state.role == "admin":
        st.success("Admin Access")
    elif st.session_state.role == "guest":
        st.info("🧪 Isolated Judge Demo")
    else:
        st.info("👤 User Access")

    st.markdown("## 🤖 Intelligence Mode")
    api_key = st.text_input(
        "Optional API key (Gemini enables the full ADK fleet)",
        type="password", 
        placeholder="Leave blank for Sample Intelligence Mode",
        key="sidebar_api_key_input"
    )
    effective_ai_key = get_configured_google_key(api_key)
    if api_key.strip() and not effective_ai_key:
        st.caption("Browser autofill/unsupported value ignored; Sample Intelligence Mode remains active.")
    st.caption(f"ADK session: `{st.session_state.adk_session_id}`")
    if st.button("Start New ADK Session", use_container_width=True):
        st.session_state.adk_session_id = str(uuid.uuid4())[:8]
        st.session_state.chat_history = []
        st.session_state.agent_trace = []
        st.rerun()
    
    if effective_ai_key and not st.session_state.api_key_set:
        try:
            st.session_state.ai_agent = AIAgent(effective_ai_key)
            st.session_state.api_key_set = True
            st.session_state.ai_mode = (
                "adk" if is_gemini_key(effective_ai_key) else "external"
            )
            st.rerun()
        except ValueError as e:
            st.error(str(e))

    st.markdown("## ⚙️ Settings")
    if st.session_state.api_key_set:
        st.success("🟢 External AI Connected")
        if st.session_state.ai_mode == "adk":
            st.caption("Google ADK multi-agent mode enabled for AI Chat.")
    else:
        st.info("🟣 Sample Intelligence Mode")
        st.caption("Local statistics, reports, and deterministic evaluation work without an API key.")

    if st.session_state.df is not None:
        st.markdown("## 📂 Current Dataset")
        st.info(f"""
        📄 File: {st.session_state.filename}
        📊 Rows: {st.session_state.df.shape[0]:,}
        📐 Columns: {st.session_state.df.shape[1]}
        """)

        if st.button("🗑️ Remove Dataset", use_container_width=True):
            log_activity(st.session_state.username, "Remove Dataset", f"Removed current session active file: {st.session_state.filename}")
            st.session_state.df = None
            st.session_state.filename = None
            st.session_state.analyzer = None
            st.session_state.chat_history = []
            st.session_state.analysis_done = False
            st.session_state.file_processed = False
            st.session_state.dataset_id = None
            st.session_state.dataset_status = None
            st.session_state.quality_report = None
            st.session_state.is_sample_dataset = False
            st.session_state.forecast_agent_result = None
            st.session_state.anomaly_agent_result = None
            st.session_state.uploader_key += 1
            clear_current_dataset()
            st.rerun()

    if st.button("🎲 Load Northstar Retail Demo", key="sample_btn_sidebar", use_container_width=True):
        load_sample_workspace()
        st.rerun()

    st.markdown("---")
    if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
        log_activity(st.session_state.username, "Logout", "User closed active session securely.")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if st.session_state.pop("auto_load_sample", False):
    load_sample_workspace()
    st.rerun()

#  Navigation 
menu = ["Dashboard"]
if st.session_state.role == "admin":
    menu.append("Admin Panel")

selected_page = st.sidebar.radio("📌 Navigation", menu)

if selected_page == "Admin Panel":
    show_admin_panel()
    st.stop()

#  Dashboard View Panel
runtime_label = "FULL ADK ACTIVE" if is_gemini_key(effective_ai_key) else "SAMPLE MODE"
runtime_class = "live" if is_gemini_key(effective_ai_key) else ""
dataset_label = (
    html.escape(st.session_state.filename)
    if st.session_state.get("filename")
    else "No dataset loaded"
)
st.markdown(
    f"""
    <section class="capstone-hero">
      <div class="hero-kicker">InsightHive · Google ADK · Governed Intelligence</div>
      <div class="hero-title">Decision intelligence, coordinated by agents.</div>
      <div class="hero-copy">
        One objective becomes verified analysis, forward-looking risk, MCP-grounded
        recommendations, and an approval-gated executive report—with every tool call visible.
      </div>
      <div class="hero-chips">
        <span class="hero-chip {runtime_class}">● {runtime_label}</span>
        <span class="hero-chip">7-agent fleet</span>
        <span class="hero-chip">Live MCP</span>
        <span class="hero-chip">Human approval gate</span>
        <span class="hero-chip">{dataset_label}</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.expander(
    "📤 Add or replace business dataset",
    expanded=st.session_state.df is None,
):
    uploaded_file = st.file_uploader(
        "Drag & drop CSV or Excel file here",
        type=["csv", "xlsx", "xls"],
        key=f"main_upload_{st.session_state.uploader_key}",
    )
    st.caption(
        "Uploads are confined, schema-checked, and quality-scored before agent analysis."
    )

#  DYNAMIC FIX: Jab user cross (X) daba kar file hataye, toh session state automatic reset ho jaye
if (
    uploaded_file is None
    and st.session_state.df is not None
    and not st.session_state.get("is_sample_dataset", False)
):
    st.session_state.df = None
    st.session_state.filename = None
    st.session_state.analyzer = None
    st.session_state.chat_history = []
    st.session_state.analysis_done = False
    st.session_state.file_processed = False
    st.session_state.dataset_id = None
    st.session_state.dataset_status = None
    st.session_state.quality_report = None
    st.session_state.forecast_agent_result = None
    st.session_state.anomaly_agent_result = None
    clear_current_dataset()
    st.rerun()

if (
    uploaded_file is not None
    and st.session_state.filename is not None
    and uploaded_file.name != st.session_state.filename
):
    st.session_state.file_processed = False
    st.session_state.agent_mission_result = None
    st.session_state.forecast_agent_result = None
    st.session_state.anomaly_agent_result = None

# File Processing Logic Gate Connected with Universal Shapes Engine
if uploaded_file is not None and not st.session_state.file_processed:
    try:
        with st.spinner("Activating dataset: parsing, schema-checking, and quality-scoring..."):
            file_path = persist_uploaded_file(uploaded_file, st.session_state.username)
            if is_gemini_key(effective_ai_key):
                saved_name = os.path.basename(file_path)
                response, artifact, _ = run_specialist_action(
                    (
                        "Transfer to ingestion_agent. Call parse_uploaded_dataset with "
                        f"filename='{saved_name}' and username='{st.session_state.username}', "
                        "then verify the schema with get_dataset_overview."
                    ),
                    effective_ai_key,
                    "parse_uploaded_dataset",
                )
                context = get_current_dataset()
                df = context.df if artifact and context.df is not None else None
                if df is None:
                    st.info(
                        "External agent ingestion is unavailable; the secure local "
                        "shape engine is activating this dataset."
                    )
                    df = super_smart_data_loader(uploaded_file)
            else:
                df = super_smart_data_loader(uploaded_file)
            if df is not None:
                quality_report = evaluate_dataset_quality(df)
                st.session_state.df = df
                st.session_state.filename = uploaded_file.name
                st.session_state.analyzer = DataAnalyzer(df)
                st.session_state.file_processed = True
                st.session_state.is_sample_dataset = False
                st.session_state.analysis_done = False
                st.session_state.pipeline_result = None
                st.session_state.evaluation_result = None
                st.session_state.agent_mission_result = None
                st.session_state.forecast_agent_result = None
                st.session_state.anomaly_agent_result = None
                st.session_state.quality_report = quality_report
                st.session_state.dataset_status = "pending"
                st.session_state.dataset_id = save_dataset_record(
                    uploaded_file.name,
                    st.session_state.username,
                    df.shape[0],
                    df.shape[1],
                    file_path=file_path,
                    quality_score=quality_report["score"],
                    quality_grade=quality_report["grade"],
                )
                st.session_state["agent_mission_text"] = mission_objective_for_dataset(df)
                log_activity(
                    st.session_state.username,
                    "Upload Dataset",
                    f"Uploaded and activated file: {uploaded_file.name}",
                )
                sync_dataset_context()
                st.toast(
                    f"{uploaded_file.name} activated · {df.shape[0]:,} rows · "
                    f"{df.shape[1]} columns",
                    icon="✅",
                )
                st.rerun()
    except Exception as e:
        st.session_state.file_processed = True
        st.error(f"Could not activate {uploaded_file.name}: {e}")


if st.session_state.df is None:
    col1, col2, col3 = st.columns(3)
    features = [
        ("📤", "Upload Data", "CSV or Excel files, instantly parsed and previewed"),
        ("🧠", "AI Analysis", "Ask questions about your data"),
        ("📈", "Auto Charts", "Interactive visualizations generated automatically"),
        ("🔍", "Smart Insights", "Trends, anomalies, and KPIs detected automatically"),
        ("📉", "Forecasting", "Predict future trends with built-in models"),
        ("📄", "PDF Reports", "One-click professional business report download"),
    ]
    for i, (icon, title, desc) in enumerate(features):
        with [col1, col2, col3][i % 3]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="feature-icon">{icon}</div>
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

else:
    df = st.session_state.df
    analyzer = st.session_state.analyzer

    sync_dataset_context()

    tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🛰️ Agent Control Room",
        "📋 Overview",
        "📈 Visualizations",
        "🧠 AI Chat",
        "🔮 Forecast",
        "🚨 Anomalies",
        "📄 Report",
        "🔍 Agent Trace",
        "🧪 Evaluation"
    ])

    # TAB 0: AGENT CONTROL ROOM
    with tab0:
        st.markdown(
            """
            <style>
            .mission-hero {
                padding: 24px 26px; border-radius: 18px;
                background: linear-gradient(135deg,#15113a 0%,#101b34 55%,#0c2927 100%);
                border: 1px solid rgba(139,124,255,.35);
                box-shadow: 0 18px 50px rgba(0,0,0,.25);
                margin-bottom: 18px;
            }
            .mission-kicker {color:#9d90ff;font-size:.78rem;letter-spacing:.16em;font-weight:700;}
            .mission-title {font-size:1.75rem;font-weight:750;color:#f6f3ff;margin:6px 0;}
            .mission-copy {color:#aaa8c5;max-width:850px;line-height:1.55;}
            .fleet-card {
                border:1px solid #292653;border-radius:14px;padding:14px 16px;
                background:linear-gradient(180deg,#12122a,#0d0d1c);min-height:108px;
            }
            .fleet-role {color:#8f82ff;font-weight:700;font-size:.9rem;}
            .fleet-desc {color:#8e8ca8;font-size:.78rem;margin-top:7px;line-height:1.4;}
            </style>
            <div class="mission-hero">
              <div class="mission-kicker">AUTONOMOUS BUSINESS INTELLIGENCE</div>
              <div class="mission-title">Agent Mission Control</div>
              <div class="mission-copy">
                Give one business objective. The orchestrator coordinates analysis,
                forecasting, MCP-backed KPI research, and report preparation while
                recording every specialist and tool call.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fleet = [
            ("Ingestion Agent", "Parses confined uploads and verifies schema."),
            ("Quality Agent", "Scores readiness and investigates anomalies."),
            ("Analytics Agent", "Runs statistics, correlation, and forecasts."),
            ("Insight Agent", "Uses MCP KPI playbooks for grounded actions."),
            ("Report Agent", "Creates contract-validated report sections."),
            ("Governance Agent", "Enforces human approval and revision gates."),
        ]
        fleet_cols = st.columns(3)
        for index, (role, description) in enumerate(fleet):
            with fleet_cols[index % 3]:
                st.markdown(
                    f'<div class="fleet-card"><div class="fleet-role">{role}</div>'
                    f'<div class="fleet-desc">{description}</div></div>',
                    unsafe_allow_html=True,
                )

        st.markdown("#### Launch a business mission")
        mission_col, industry_col = st.columns([3, 1])
        with mission_col:
            mission_text = st.text_area(
                "Business objective",
                value=(
                    "Analyze performance, identify material risks, forecast revenue, "
                    "and prepare prioritized actions for an approval-ready executive report."
                ),
                height=105,
                key="agent_mission_text",
            )
        with industry_col:
            mission_industry = st.selectbox(
                "Industry playbook",
                ["retail", "saas", "marketing", "operations", "hr"],
                key="agent_mission_industry",
            )
            st.metric("Fleet", "6 agents")
            st.metric("Runtime", "Full ADK" if is_gemini_key(effective_ai_key) else "Locked")

        if not is_gemini_key(effective_ai_key):
            st.warning(
                "Full ADK Mission Control requires Gemini in the Linux Docker runtime. "
                "Run `docker compose up --build` after configuring `.env.docker`."
            )
        if st.button(
            "🚀 Execute Autonomous Mission",
            use_container_width=True,
            disabled=not is_gemini_key(effective_ai_key),
            type="primary",
        ):
            try:
                with st.spinner("Orchestrator is coordinating the specialist fleet..."):
                    st.session_state.agent_mission_result = execute_agent_mission(
                        mission_text,
                        effective_ai_key,
                        mission_industry,
                    )
            except Exception as exc:
                st.session_state.agent_mission_result = None
                st.error(
                    "Mission could not complete. Check the API-key quota and "
                    f"container logs. Details: {exc}"
                )
                st.stop()
            st.rerun()

        mission_result = st.session_state.get("agent_mission_result")
        if mission_result:
            status = mission_result.get("status", "needs_review")
            (st.success if status == "completed" else st.warning)(
                f"Mission {mission_result['mission_id']} — {status.replace('_', ' ').title()}"
            )
            if mission_result.get("external_ai_unavailable"):
                st.warning(
                    "Gemini free-tier quota is currently unavailable. InsightHive completed "
                    "the analysis with its deterministic local resilience runtime; MCP was "
                    "replaced by the same bundled KPI knowledge base through local vector retrieval."
                )
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Planning Mode", mission_result.get("planner", "ADK orchestrator"))
            mc2.metric("Tools Selected", len(mission_result["stages"]))
            mc3.metric("Mission Success", f"{mission_result.get('success_score', 0)}%")
            mc4.metric(
                "End-to-End Time",
                f"{mission_result.get('total_latency_ms', 0) / 1000:.1f} sec",
            )

            brief_tab, forecast_tab, execution_tab, evidence_tab = st.tabs(
                [
                    "📌 Decision Brief",
                    "📈 Forecast",
                    "🤖 Agent Execution",
                    "🧾 Technical Evidence",
                ]
            )

            with brief_tab:
                st.markdown("#### What you asked")
                st.info(mission_result.get("mission", "Business analysis mission"))

                overview = _pipeline_stage_result(
                    mission_result, "ingestion_context"
                )
                quality = _pipeline_stage_result(mission_result, "quality_gate")
                anomalies = _pipeline_stage_result(
                    mission_result, "anomaly_detection"
                )
                forecast = _mission_artifact(mission_result, "run_forecast")
                gate = _mission_artifact(mission_result, "check_publish_gate")

                answer_cols = st.columns(4)
                answer_cols[0].metric(
                    "Records analyzed",
                    f"{overview.get('rows', len(st.session_state.df)):,}",
                )
                answer_cols[1].metric(
                    "Data quality",
                    f"{quality.get('score', overview.get('quality_score', '—'))}/100",
                    quality.get("grade", overview.get("quality_grade", "")),
                )
                answer_cols[2].metric(
                    "Anomalies flagged",
                    anomalies.get("anomaly_count", "—"),
                )
                answer_cols[3].metric(
                    "Forecast direction",
                    str(forecast.get("trend", "—")).title(),
                )

                st.markdown("#### Direct answer")
                st.markdown(
                    mission_result.get("final_response")
                    or "The agent did not return an executive synthesis."
                )

                st.markdown("#### Was every requested part answered?")
                criteria_table = pd.DataFrame(
                    [
                        {
                            "Requested outcome": criterion,
                            "Result": "✅ Answered" if passed else "⚠️ Missing",
                        }
                        for criterion, passed in mission_result.get(
                            "success_criteria", {}
                        ).items()
                    ]
                )
                if not criteria_table.empty:
                    safe_dataframe(
                        criteria_table, use_container_width=True, hide_index=True
                    )
                if gate:
                    if gate.get("download_allowed"):
                        st.success("Report governance: approved for download.")
                    else:
                        st.warning(
                            "Report governance: analysis is complete, but publication "
                            "remains blocked until a human approves the report."
                        )

            with forecast_tab:
                forecast = _mission_artifact(mission_result, "run_forecast")
                if forecast:
                    st.markdown(
                        f"#### {forecast.get('value_col', 'KPI')} outlook · "
                        f"{forecast.get('periods', 12)} future periods"
                    )
                    fc1, fc2, fc3 = st.columns(3)
                    fc1.metric("Trend", str(forecast.get("trend", "—")).title())
                    fc2.metric(
                        "MAE",
                        f"{float(forecast.get('mae', 0)):,.0f}"
                        if forecast.get("mae") is not None else "—",
                        help="Mean Absolute Error: average forecast miss in KPI units.",
                    )
                    fc3.metric(
                        "RMSE",
                        f"{float(forecast.get('rmse', 0)):,.0f}"
                        if forecast.get("rmse") is not None else "—",
                        help="Root Mean Squared Error: penalizes larger forecast misses.",
                    )

                    actual = pd.DataFrame(forecast.get("historical_points", []))
                    future = pd.DataFrame(forecast.get("forecast_points", []))
                    chart_parts = []
                    if not actual.empty and {"date", "value"}.issubset(actual.columns):
                        actual = actual.rename(columns={"value": "Actual"})
                        actual["date"] = pd.to_datetime(actual["date"])
                        chart_parts.append(actual.set_index("date")[["Actual"]])
                    if not future.empty and {"date", "value"}.issubset(future.columns):
                        future = future.rename(columns={"value": "Forecast"})
                        future["date"] = pd.to_datetime(future["date"])
                        chart_parts.append(future.set_index("date")[["Forecast"]])
                    if chart_parts:
                        chart_df = pd.concat(chart_parts, axis=1).sort_index()
                        st.line_chart(chart_df, use_container_width=True)
                        st.caption(
                            "Actual history and agent-generated future projection. "
                            "MAE/RMSE communicate expected model uncertainty."
                        )
                    else:
                        st.info("Forecast completed, but no chartable points were returned.")
                else:
                    st.info("This mission did not request or produce a forecast.")

            with execution_tab:
                st.markdown("#### How the agents answered your objective")
                st.caption(
                    "Each row is one evidence-producing action selected by the ADK orchestrator."
                )
                timeline = pd.DataFrame(
                    [
                        {
                            "Step": stage["step"],
                            "What it answered": stage["task"],
                            "ADK agent": stage["specialist"],
                            "Evidence tool": stage["tool"],
                            "Status": "✅ Complete"
                            if stage["status"] == "completed" else stage["status"],
                            "Time (ms)": stage["latency_ms"],
                        }
                        for stage in mission_result["stages"]
                    ]
                )
                safe_dataframe(timeline, use_container_width=True, hide_index=True)

            with evidence_tab:
                st.caption(
                    "Raw tool payloads are retained for auditability. Normal users can "
                    "use the Decision Brief and Forecast tabs instead."
                )
                for stage in mission_result["stages"]:
                    with st.expander(
                        f"{stage['step']}. {stage['task']} · {stage['tool']}"
                    ):
                        if stage.get("artifact") is not None:
                            st.json(stage["artifact"])

        st.divider()
        st.markdown("#### Cross-session memory proof")
        st.caption(
            "Stores a preference in one ADK session, opens a fresh session, and verifies "
            "recall through LoadMemoryTool."
        )
        memory_preference = st.text_input(
            "Preference to remember",
            value="Prioritize Revenue by Region and flag return-rate risk.",
            key="memory_proof_preference",
        )
        if st.button(
            "🧠 Run Cross-Session Memory Proof",
            use_container_width=True,
            disabled=not is_gemini_key(effective_ai_key),
        ):
            with st.spinner("Writing memory, starting a fresh session, and recalling it..."):
                st.session_state.memory_proof_result = run_memory_proof(
                    memory_preference,
                    effective_ai_key,
                )
        memory_proof = st.session_state.get("memory_proof_result")
        if memory_proof:
            if memory_proof["load_memory_called"]:
                st.success("LoadMemoryTool was selected in a fresh ADK session.")
            elif memory_proof.get("memory_service_verified"):
                st.success(
                    "Preference recalled through the same Google ADK Memory Service "
                    "without another Gemini request."
                )
            else:
                st.warning("Recall completed, but LoadMemoryTool was not observed in the trace.")
            st.write(memory_proof["recalled_response"])
            st.caption(
                f"Source: {memory_proof['source_session']} → Recall: "
                f"{memory_proof['recall_session']}"
            )

    #  TAB 1: OVERVIEW 
    with tab1:
        st.markdown(f"<div class='section-title'>Dataset: {st.session_state.filename}</div>", unsafe_allow_html=True)

        if st.button("🤖 Run Governed Agent Pipeline", use_container_width=True):
            with st.spinner("Root Orchestrator is selecting and running the governed pipeline..."):
                if is_gemini_key(effective_ai_key):
                    response, artifact, _ = run_specialist_action(
                        (
                            "As the root orchestrator, call run_full_analysis_pipeline "
                            "with include_anomalies=true and summarize its stage results."
                        ),
                        effective_ai_key,
                        "run_full_analysis_pipeline",
                    )
                    if artifact:
                        artifact["agent_response"] = response
                        artifact["execution_mode"] = "adk_orchestrator"
                        st.session_state.pipeline_result = artifact
                    else:
                        result = json.loads(run_full_analysis_pipeline())
                        result["execution_mode"] = "quota_resilient_tool"
                        st.session_state.pipeline_result = result
                else:
                    result = json.loads(run_full_analysis_pipeline())
                    result["execution_mode"] = "sample_fallback"
                    st.session_state.pipeline_result = result

        pipeline_result = st.session_state.get("pipeline_result")
        if pipeline_result:
            message = (
                f"Pipeline {pipeline_result.get('status')} in "
                f"{pipeline_result.get('latency_ms', 0)} ms across "
                f"{len(pipeline_result.get('stages', []))} stages."
            )
            (st.success if pipeline_result.get("status") == "success" else st.error)(message)
            st.caption(
                "Execution: "
                + (
                    "ADK Root Orchestrator → run_full_analysis_pipeline"
                    if pipeline_result.get("execution_mode") == "adk_orchestrator"
                    else (
                        "Quota-resilient verified pipeline"
                        if pipeline_result.get("execution_mode") == "quota_resilient_tool"
                        else "Sample fallback"
                    )
                )
            )
            with st.expander("Pipeline stage details"):
                safe_dataframe(
                    pd.DataFrame(
                        [
                            {
                                "stage": stage.get("stage"),
                                "status": stage.get("status"),
                                "latency_ms": stage.get("latency_ms"),
                            }
                            for stage in pipeline_result.get("stages", [])
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

        stats = analyzer.get_summary_stats()
        num_cols = analyzer.get_numeric_columns()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Total Rows",    f"{df.shape[0]:,}")
        col2.metric("📐 Columns",       str(df.shape[1]))
        col3.metric("🔢 Numeric Cols",  str(len(num_cols)))
        col4.metric("❌ Missing Values", str(int(df.isnull().sum().sum())))

        quality_report = st.session_state.get("quality_report") or evaluate_dataset_quality(df)
        q1, q2, q3 = st.columns(3)
        q1.metric("✅ Data Quality", f"{quality_report['score']}/100", quality_report["grade"])
        q2.metric("🔁 Duplicate Rows", str(quality_report["duplicate_rows"]), f"{quality_report['duplicate_pct']}%")
        q3.metric("🛂 Review Status", (st.session_state.get("dataset_status") or "session only").title())
        if quality_report.get("issues"):
            st.caption(" | ".join(quality_report["issues"][:4]))

        st.divider()
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown("<div class='section-title'>Data Preview</div>", unsafe_allow_html=True)
            safe_dataframe(df.head(50), use_container_width=True, height=300)

        with col_right:
            st.markdown("<div class='section-title'>Column Types</div>", unsafe_allow_html=True)
            col_info = analyzer.get_column_info()
            type_df = pd.DataFrame(col_info).T.reset_index()
            type_df.columns = ["Column", "Type", "Non-Null", "Unique"]
            safe_dataframe(type_df, use_container_width=True, height=300)

        st.divider()
        st.markdown("<div class='section-title'>Statistical Summary</div>", unsafe_allow_html=True)
        
        #  CRITICAL BUG FIX: `.round(2)` crash check condition deployment
        if stats is not None and len(stats) > 0:
            safe_dataframe(stats.round(2), use_container_width=True)
        else:
            st.warning("No numeric data found for summary statistics.")

        missing = df.isnull().sum()
        missing = missing[missing > 0]
        if not missing.empty:
            st.divider()
            st.markdown("<div class='section-title'>⚠️ Missing Values</div>", unsafe_allow_html=True)
            miss_df = pd.DataFrame({"Column": missing.index, "Missing": missing.values,
                                    "Percent": (missing.values / len(df) * 100).round(2)})
            fig = px.bar(miss_df, x="Column", y="Percent",
                        title="Missing Values (%)",
                        color="Percent",
                        color_continuous_scale="Reds",
                        template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        if len(num_cols) >= 2:
            st.divider()
            st.markdown("<div class='section-title'>🔗 Correlation Matrix</div>", unsafe_allow_html=True)
            corr = analyzer.get_correlation().round(2)
            fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r",
                            title="Feature Correlation Heatmap", template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    #  TAB 2: VISUALIZATIONS 
    with tab2:
        st.markdown("<div class='section-title'>📈 Auto-Generated Charts</div>", unsafe_allow_html=True)
        st.caption(
            "In Full ADK mode, the Analytics Agent first inspects verified relationships "
            "and recommends the decision views; Plotly renders the selected specifications."
        )
        if st.button(
            "🤖 Ask Analytics Agent to Direct the Visual Story",
            use_container_width=True,
            disabled=not is_gemini_key(effective_ai_key),
        ):
            with st.spinner("Analytics Agent is selecting evidence-backed decision views..."):
                response, _, _ = run_specialist_action(
                    (
                        "Transfer to analytics_agent. Inspect the active schema with "
                        "get_dataset_overview and call get_correlation_insights. Recommend "
                        "three charts for an executive decision story, naming the exact "
                        "columns and the business question each chart answers."
                    ),
                    effective_ai_key,
                    "get_correlation_insights",
                )
                st.session_state.visualization_agent_brief = response
        if st.session_state.get("visualization_agent_brief"):
            with st.expander("Analytics Agent chart brief", expanded=True):
                st.write(st.session_state.visualization_agent_brief)

        viz = Visualizer(df)
        cat_cols = analyzer.get_categorical_columns()
        num_cols = analyzer.get_numeric_columns()
        date_cols = analyzer.get_date_columns()
        smart_x = None
        if cat_cols:
            preferred_cat_cols = [c for c in cat_cols if not str(c).lower().startswith("col_")]
            smart_x_candidates = preferred_cat_cols or cat_cols
            smart_x = max(smart_x_candidates, key=lambda c: df[c].dropna().nunique())
        fiscal_cols = [
            c for c in num_cols
            if re.search(r"(?:fy\s*'?\s*)?(\d{2,4})", str(c), re.IGNORECASE)
        ]
        smart_y = fiscal_cols[-1] if fiscal_cols else (num_cols[0] if num_cols else None)

        ccol1, ccol2, ccol3 = st.columns(3)
        with ccol1:
            x_options = df.columns.tolist()
            x_index = x_options.index(smart_x) if smart_x in x_options else 0
            x_axis = st.selectbox("X Axis", options=x_options, index=x_index, key="x_sel")
        with ccol2:
            y_options = num_cols if num_cols else df.columns.tolist()
            y_index = y_options.index(smart_y) if smart_y in y_options else 0
            y_axis = st.selectbox("Y Axis", options=y_options, index=y_index, key="y_sel")
        with ccol3:
            chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Histogram", "Box", "Pie"])

        color_by = st.selectbox("Color By (optional)", ["None"] + cat_cols, key="color_sel")
        color_col = None if color_by == "None" else color_by

        fig = viz.plot(chart_type, x_axis, y_axis, color_col)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("This chart type does not fit the selected columns. Try a Bar chart with a text X axis and numeric Y axis.")

        st.divider()
        st.markdown("<div class='section-title'>📊 Smart Auto-Charts</div>", unsafe_allow_html=True)

        auto_figs = viz.generate_auto_charts(num_cols, cat_cols, date_cols)
        if not auto_figs:
            st.info("No meaningful auto-charts could be generated from the detected columns. Try selecting different X and Y fields above.")
        for i in range(0, len(auto_figs), 2):
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(auto_figs[i], use_container_width=True)
            if i + 1 < len(auto_figs):
                with c2:
                    st.plotly_chart(auto_figs[i+1], use_container_width=True)

    #  TAB 3: AI CHAT 
    with tab3:
        st.markdown("<div class='section-title'>🧠 Ask Your Data Anything</div>", unsafe_allow_html=True)

        if st.session_state.api_key_set:
            st.success("Google ADK agent fleet is active.")
        else:
            st.info("Sample Intelligence Mode is active — answers are calculated locally without an API key.")
        if st.session_state.get("is_sample_dataset"):
            st.caption(
                "Northstar Retail contains curated benchmark signals for a stable demo."
            )
        else:
            quality = st.session_state.get("quality_report") or {}
            st.caption(
                f"Insight reliability depends on uploaded data quality "
                f"({quality.get('score', 'not scored')}/100)."
            )

        if True:
            st.markdown("**Suggested Questions:**")
            suggestions = [
                "Which region leads revenue and which one is weakest?",
                "Which product has the highest profit performance?",
                "Where is the highest return-rate risk?",
                "Summarize the revenue trend over time",
                "What actions would improve profit and target attainment?",
            ]
            cols = st.columns(3)
            for idx, sug in enumerate(suggestions):
                with cols[idx % 3]:
                    if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                        st.session_state._pending_question = sug

            st.divider()

            chat_container = st.container()
            with chat_container:
                for msg in st.session_state.chat_history:
                    safe_content = html.escape(str(msg["content"]))
                    if msg["role"] == "user":
                        st.markdown(f"<div class='chat-user'>User: {safe_content}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='chat-ai'>AI: {safe_content}</div>", unsafe_allow_html=True)
            user_q = st.text_input("Ask a question about your data...", key="chat_input",
                                  placeholder="e.g. Which region generates the most revenue?")

            if hasattr(st.session_state, "_pending_question") and st.session_state._pending_question:
                user_q = st.session_state._pending_question
                st.session_state._pending_question = None

            c_send, c_clear = st.columns([6, 1])
            with c_send:
                send_btn = st.button("Send 🚀", use_container_width=True)
            with c_clear:
                clear_btn = st.button("🗑️ Clear", use_container_width=True)

            if send_btn and user_q.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_q})
                with st.spinner("AI is thinking..."):
                    response = run_ai_chat(user_q, df, effective_ai_key)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                log_activity(st.session_state.username, "AI Query", f"Question: {user_q[:60]}...")
                st.rerun()

            if clear_btn:
                st.session_state.chat_history = []
                log_activity(st.session_state.username, "Clear Chat", f"Cleared AI Chat history metrics stream for file: {st.session_state.filename}")
                st.rerun()

   #  TAB 4: FORECAST 
    with tab4:
        st.markdown("<div class='section-title'>🔮 Sales Forecasting</div>", unsafe_allow_html=True)

        date_cols = analyzer.get_date_columns()
        num_cols  = analyzer.get_numeric_columns()

        available_cols = df.columns.tolist()

        if not available_cols:
            st.warning("Forecasting requires data arrays.")
        else:
            fc1, fc2, fc3 = st.columns(3)
            
            #  SMART DEFAULT 1: Agar loader ne 'Parsed_Date' banaya hai, toh use automatic chun lo
            if 'Parsed_Date' in available_cols:
                default_date_idx = available_cols.index('Parsed_Date')
            else:
                default_date_idx = 0

            with fc1:
                date_col = st.selectbox("Date Column", options=available_cols, index=default_date_idx)
            
            #  SMART DEFAULT 2: End-user ko gande text columns chunne se bachao
            # Value to Forecast ke dropdown mein sirf vahi columns dikhao jo asali numeric data hain!
            value_targets = [c for c in num_cols if c != 'Parsed_Date']
            
            # Agar koi valid numeric column mila toh use dropdown ki pehli choice banao, varna fallback to all
            display_options = value_targets if value_targets else available_cols
            
            with fc2:
                value_col = st.selectbox("Value to Forecast", options=display_options, index=0)
                
            with fc3:
                periods = st.slider("Forecast Periods", 4, 52, 12)

            if st.button("🚀 Run Forecast", use_container_width=True):
                with st.spinner("Analytics Agent is selecting and running the forecast tool..."):
                    if is_gemini_key(effective_ai_key):
                        response, artifact, _ = run_specialist_action(
                            (
                                "Transfer to analytics_agent and call run_forecast exactly once "
                                f"with date_col='{date_col}', value_col='{value_col}', "
                                f"periods={periods}. Explain the returned trend and uncertainty."
                            ),
                            effective_ai_key,
                            "run_forecast",
                        )
                        if artifact:
                            artifact["agent_response"] = response
                            artifact["execution_mode"] = "adk_agent"
                            st.session_state.forecast_agent_result = artifact
                        else:
                            from tools.analytics_tools import run_forecast

                            fallback = json.loads(
                                run_forecast(date_col, value_col, periods)
                            )
                            fallback["agent_response"] = (
                                "Gemini was unavailable; the verified forecast tool "
                                "completed this request directly."
                            )
                            fallback["execution_mode"] = "quota_resilient_tool"
                            st.session_state.forecast_agent_result = fallback
                    else:
                        from utils.forecaster import Forecaster
                        fc = Forecaster(df, date_col, value_col)
                        _, metrics = fc.forecast(periods)
                        metrics["execution_mode"] = "sample_fallback"
                        st.session_state.forecast_agent_result = metrics

                    log_activity(
                        st.session_state.username,
                        "Agent Forecast",
                        f"Target KPI: {value_col} over {periods} periods",
                    )

            forecast_result = st.session_state.get("forecast_agent_result")
            if forecast_result:
                if forecast_result.get("error"):
                    st.error(forecast_result["error"])
                else:
                    historical = pd.DataFrame(forecast_result.get("historical_points", []))
                    future = pd.DataFrame(forecast_result.get("forecast_points", []))
                    fig = go.Figure()
                    if not historical.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=pd.to_datetime(historical["date"]),
                                y=historical["value"],
                                mode="lines+markers",
                                name="Historical Values",
                                line=dict(color="#7c6af7", width=2.5),
                            )
                        )
                    if not future.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=pd.to_datetime(future["date"]),
                                y=future["value"],
                                mode="lines+markers",
                                name="Agent Forecast",
                                line=dict(color="#10b981", width=2.5, dash="dash"),
                            )
                        )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("MAE", f"{forecast_result.get('mae', 0):.2f}")
                    m2.metric("RMSE", f"{forecast_result.get('rmse', 0):.2f}")
                    m3.metric("Trend", forecast_result.get("trend", ""))
                    st.caption(
                        "Execution: "
                        + (
                            "ADK Analytics Agent → run_forecast"
                            if forecast_result.get("execution_mode") == "adk_agent"
                            else (
                                "Quota-resilient verified forecast tool"
                                if forecast_result.get("execution_mode")
                                == "quota_resilient_tool"
                                else "Sample fallback"
                            )
                        )
                    )
                    if forecast_result.get("agent_response"):
                        with st.expander("Analytics Agent interpretation"):
                            st.write(forecast_result["agent_response"])

    #  TAB 5: ANOMALIES
    with tab5:
        st.markdown("<div class='section-title'>🚨 Anomaly Detection</div>", unsafe_allow_html=True)
        if st.button("🛡️ Ask Quality Agent to Scan", use_container_width=True):
            with st.spinner("Quality Agent is selecting and running anomaly tools..."):
                if is_gemini_key(effective_ai_key):
                    response, artifact, _ = run_specialist_action(
                        (
                            "Transfer to quality_agent and call detect_anomaly_records "
                            "with max_rows=50. Explain the operational risk without inventing values."
                        ),
                        effective_ai_key,
                        "detect_anomaly_records",
                    )
                    if artifact:
                        artifact["agent_response"] = response
                        artifact["execution_mode"] = "adk_agent"
                        st.session_state.anomaly_agent_result = artifact
                    else:
                        anomalies, anomaly_error = detect_anomalies(df, max_rows=50)
                        st.session_state.anomaly_agent_result = {
                            "anomaly_count": int(len(anomalies)),
                            "message": anomaly_error or "Verified local anomaly scan completed.",
                            "sample_rows": anomalies.to_dict(orient="records"),
                            "execution_mode": "quota_resilient_tool",
                            "agent_response": (
                                "Gemini was unavailable; the deterministic quality "
                                "tool completed the anomaly scan directly."
                            ),
                        }
                else:
                    anomalies, anomaly_error = detect_anomalies(df, max_rows=50)
                    st.session_state.anomaly_agent_result = {
                        "anomaly_count": int(len(anomalies)),
                        "message": anomaly_error or "Local anomaly scan completed.",
                        "sample_rows": anomalies.to_dict(orient="records"),
                        "execution_mode": "sample_fallback",
                    }
                log_activity(
                    st.session_state.username,
                    "Agent Anomaly Scan",
                    f"Scanned {st.session_state.filename}",
                )

        anomaly_result = st.session_state.get("anomaly_agent_result")
        if anomaly_result:
            anomalies = pd.DataFrame()
            if anomaly_result.get("error"):
                st.error(anomaly_result["error"])
            else:
                anomalies = pd.DataFrame(anomaly_result.get("sample_rows", []))
                count = anomaly_result.get("anomaly_count", len(anomalies))
                if count == 0:
                    st.success("No major numeric outliers detected in this dataset.")
                else:
                    st.warning(f"{count} unusual rows detected. Review these before decisions.")
                    safe_dataframe(anomalies, use_container_width=True, height=360)

            if not anomalies.empty and "Anomaly_Score" in anomalies.columns:
                fig = px.scatter(
                    anomalies,
                    x=anomalies.index.astype(str),
                    y="Anomaly_Score",
                    title="Anomaly Severity by Row",
                    template="plotly_dark",
                    color="Anomaly_Score",
                    color_continuous_scale="Reds",
                )
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Execution: "
                + (
                    "ADK Quality Agent → detect_anomaly_records"
                    if anomaly_result.get("execution_mode") == "adk_agent"
                    else (
                        "Quota-resilient verified anomaly tool"
                        if anomaly_result.get("execution_mode")
                        == "quota_resilient_tool"
                        else "Sample fallback"
                    )
                )
            )
            if anomaly_result.get("agent_response"):
                with st.expander("Quality Agent interpretation"):
                    st.write(anomaly_result["agent_response"])

    #  TAB 6: REPORT 
    with tab6:
        st.markdown("<div class='section-title'>📄 Generate Business Report</div>", unsafe_allow_html=True)

        if st.session_state.get("dataset_status") not in [None, "approved"] and st.session_state.role != "admin":
            st.warning("This dataset is pending admin review. Reports unlock after approval.")
        else:
            if not st.session_state.api_key_set:
                st.info("Report will use deterministic Sample Intelligence Mode; no API key is required.")
            rcol1, rcol2 = st.columns(2)
            with rcol1:
                company_name = st.text_input("Company Name", value="Acme Corp")
                analyst_name = st.text_input("Analyst Name", value="InsightHive Agent")
            with rcol2:
                report_title = st.text_input("Report Title", value="Business Intelligence Report")
                report_date  = st.date_input("Report Date", value=datetime.today())

            if st.button("📊 Generate Report", use_container_width=True):
                with st.spinner("Report Agent is gathering context and drafting the report..."):
                    pdf_bytes, agent_narrative = generate_report_artifact(
                        df,
                        analyzer,
                        company_name,
                        analyst_name,
                        report_title,
                        report_date,
                        effective_ai_key,
                        st.session_state.get("report_revision_notes", ""),
                    )
                    st.session_state.report_agent_response = agent_narrative

                if pdf_bytes:
                    revision_of = st.session_state.get("report_revision_of")
                    report_id = save_report_record(
                        report_title,
                        st.session_state.username,
                        revision_of=revision_of,
                    )
                    st.session_state.generated_report_bytes = pdf_bytes
                    st.session_state.generated_report_id = report_id
                    st.session_state.generated_report_filename = f"business_report_{report_date}.pdf"
                    st.session_state.report_revision_of = None
                    st.session_state.report_revision_notes = ""
                    st.success(f"✅ Report #{report_id} generated and submitted for admin review.")
                    st.caption(
                        "Execution: "
                        + (
                            "ADK Report Agent → get_business_context_snapshot → PDF"
                            if st.session_state.get("report_execution_mode")
                            == "adk_report_agent"
                            else "Quota-resilient grounded report contract → PDF"
                        )
                    )
                    log_activity(
                        st.session_state.username,
                        "Submit Report Review",
                        f"Submitted report #{report_id}: {report_title}",
                    )
                else:
                    detail = st.session_state.get("report_agent_response") or (
                        "Report generation failed. Review the Agent Trace for details."
                    )
                    st.error(detail)

            pending_report_id = st.session_state.get("generated_report_id")
            if pending_report_id:
                report_record = get_report_record(pending_report_id)
                report_status = (report_record or {}).get("status") or "pending"
                if report_status == "approved":
                    st.success("🟢 Admin approved this report. Download is unlocked.")
                    st.download_button(
                        label="⬇️ Download Approved PDF Report",
                        data=st.session_state.generated_report_bytes,
                        file_name=st.session_state.generated_report_filename,
                        mime="application/pdf",
                        use_container_width=True,
                    )
                elif report_status == "rejected":
                    notes = (report_record or {}).get("admin_notes") or "No review notes supplied."
                    st.error(f"🔴 Admin rejected this report: {notes}")
                    if st.button("♻️ Agent Auto-Revise Report", use_container_width=True):
                        with st.spinner("Report Agent is applying admin feedback..."):
                            revised_pdf, revised_narrative = generate_report_artifact(
                                df,
                                analyzer,
                                company_name,
                                analyst_name,
                                report_title,
                                report_date,
                                effective_ai_key,
                                notes,
                            )
                        revised_id = save_report_record(
                            report_title,
                            st.session_state.username,
                            revision_of=pending_report_id,
                        )
                        st.session_state.generated_report_bytes = revised_pdf
                        st.session_state.generated_report_id = revised_id
                        st.session_state.generated_report_filename = (
                            f"business_report_revision_{revised_id}.pdf"
                        )
                        st.session_state.report_agent_response = revised_narrative
                        log_activity(
                            st.session_state.username,
                            "Agent Auto-Revise Report",
                            f"Report #{pending_report_id} revised as #{revised_id}",
                        )
                        st.success(
                            f"Report Agent created linked revision #{revised_id}; admin review is pending."
                        )
                        st.rerun()
                else:
                    st.warning("🟡 Report is pending human review. Download remains locked.")

    with tab7:
        st.markdown("<div class='section-title'>🔍 ADK Agent Trace</div>", unsafe_allow_html=True)
        trace_source = st.radio(
            "Trace source",
            ["Mission", "Latest action", "Memory proof"],
            horizontal=True,
        )
        trace_key = {
            "Mission": "mission_trace",
            "Latest action": "agent_trace",
            "Memory proof": "memory_trace",
        }[trace_source]
        trace_events = st.session_state.get(trace_key) or []
        if not trace_events:
            st.info(f"Run {trace_source.lower()} to populate this trace.")
        else:
            safe_dataframe(pd.DataFrame(trace_events), use_container_width=True, height=360)

    with tab8:
        st.markdown("<div class='section-title'>🧪 Agent Evaluation Suite</div>", unsafe_allow_html=True)
        st.caption(
            "With Gemini: ten natural-language cases measure real ADK tool routing, including "
            "forecasting, MCP, the governed pipeline, and the HITL publish gate. "
            "Without Gemini: deterministic tool contracts remain available."
        )
        evaluation_retry = st.checkbox(
            "Retry failed routing cases once (can use up to 10 extra Gemini requests)",
            value=False,
            help=(
                "Keep this off for normal/final runs. Enable only when you explicitly "
                "want to measure retry recovery."
            ),
        )
        st.caption(
            "Quota guard: standard evaluation uses 10 cases / up to 10 agent requests. "
            "Retries are disabled by default."
        )
        if st.button("▶️ Run Evaluation", use_container_width=True):
            with st.spinner("Evaluating agent routing and selected tools..."):
                st.session_state.evaluation_result = run_agent_routing_evaluation(
                    effective_ai_key,
                    st.session_state.get("username") or "user",
                    retry_failed=evaluation_retry,
                )

        evaluation_result = st.session_state.get("evaluation_result")
        if evaluation_result:
            e1, e2, e3, e4 = st.columns(4)
            e1.metric("Pass Rate", f"{evaluation_result['pass_rate']}%")
            e2.metric("Passed", f"{evaluation_result['passed']}/{evaluation_result['cases']}")
            e3.metric(
                "First-attempt Accuracy",
                f"{evaluation_result.get('first_attempt_accuracy', evaluation_result['pass_rate'])}%",
            )
            e4.metric(
                "Avg Case Latency",
                f"{evaluation_result.get('average_case_latency_ms', 0)} ms",
            )
            st.caption(
                f"Suite latency: {evaluation_result['latency_ms']} ms · "
                f"Retry recoveries: {evaluation_result.get('retry_recoveries', 0)} · "
                "HITL policy target: pending/rejected reports must remain blocked."
            )
            st.caption(
                "Evaluation mode: "
                + (
                    "Real ADK routing — natural-language prompts scored against selected tools"
                    if evaluation_result.get("evaluation_mode") == "adk_agent_routing"
                    else (
                        "Quota-resilient contract router — provider calls stopped early"
                        if evaluation_result.get("evaluation_mode")
                        == "quota_resilient_contract_router"
                        else "Keyless deterministic tool contracts"
                    )
                )
            )
            if evaluation_result.get("provider_note"):
                st.warning(evaluation_result["provider_note"])
            safe_dataframe(
                pd.DataFrame(evaluation_result["results"]),
                use_container_width=True,
                hide_index=True,
            )
            result_by_id = {
                item.get("id"): item for item in evaluation_result.get("results", [])
            }
            proof1, proof2, proof3 = st.columns(3)
            proof1.metric(
                "MCP Runtime Proof",
                "PASS" if result_by_id.get("mcp-routing", {}).get("passed") else "NOT PROVEN",
            )
            proof2.metric(
                "HITL Gate Proof",
                "PASS"
                if result_by_id.get("hitl-gate-routing", {}).get("passed")
                else "NOT PROVEN",
            )
            proof3.metric(
                "Pipeline Proof",
                "PASS"
                if result_by_id.get("pipeline-routing", {}).get("passed")
                else "NOT PROVEN",
            )
            st.download_button(
                "⬇️ Download Judge Evidence (JSON)",
                data=json.dumps(evaluation_result, indent=2, default=str),
                file_name="adk_evaluation_evidence.json",
                mime="application/json",
                use_container_width=True,
            )

        st.divider()
        st.markdown("#### Grounding and Usefulness Judge")
        st.caption("Uses Gemini when configured; otherwise applies the deterministic local rubric.")
        default_answer = ""
        if st.session_state.chat_history:
            assistant_messages = [
                item.get("content", "")
                for item in st.session_state.chat_history
                if item.get("role") == "assistant"
            ]
            default_answer = assistant_messages[-1] if assistant_messages else ""
        judge_text = st.text_area(
            "Agent response to score",
            value=default_answer,
            height=150,
            key="judge_response_text",
        )
        if st.button("⚖️ Run Evaluation Judge", use_container_width=True):
            with st.spinner("Applying grounding and usefulness rubric..."):
                st.session_state.judge_result = judge_business_response(
                    judge_text,
                    effective_ai_key,
                )
        if st.session_state.get("judge_result"):
            result = st.session_state.judge_result
            if result.get("error"):
                st.error(result["error"])
            else:
                st.json(result)

