# Deployment Guide

**Team:** Jiya Aalwani (Team Lead & Co-Creator) · Harshit Jetwani (Co-Creator)

## Local Full ADK on Windows

Install Docker Desktop with its WSL 2 backend, then run:

```powershell
Copy-Item .env.docker.example .env.docker
notepad .env.docker
.\RUN_FULL_ADK_DOCKER.ps1
```

The script builds and starts the Linux container at `http://localhost:8501`.
This is the supported Full ADK route on managed Windows computers because
Application Control may block unsigned native `.pyd` extensions on the host.
The restriction is imposed by Windows policy and cannot be repaired by pinning
another NumPy, Pydantic, or PyArrow wheel.

Verify the runtime after startup:

```powershell
docker compose ps
docker compose logs -f insight-hive
```

Stop it with `docker compose down`. Keep `.env.docker` private; it is ignored by
Git.

## Native local sample mode

Use Python 3.12:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Native mode is suitable for deterministic Sample Intelligence when host policy
permits the scientific Python dependencies. Use Docker for the complete ADK +
MCP runtime. Configure a strong bootstrap admin password from `.env.example`;
no default credentials are seeded.

## Streamlit Community Cloud

Deploy `app.py` from a public GitHub repository. Copy
`.streamlit/secrets.example.toml` into private app Secrets and replace every
placeholder. Never commit `.streamlit/secrets.toml`.
Local SQLite data and generated files are ephemeral on free hosting.

## Google Cloud Run

The included `Dockerfile` listens on Cloud Run's `PORT`. A public deployment is
optional under the competition rubric, but InsightHive uses one so judges can
experience the project directly.

### 1. Prepare Google Cloud

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com
```

Create secrets without placing values in shell history where possible:

```bash
gcloud secrets create GOOGLE_API_KEY --replication-policy=automatic
gcloud secrets versions add GOOGLE_API_KEY --data-file=google-api-key.txt
```

Bootstrap admin secrets are needed for the private HITL demonstration. Judges
enter through **Explore Sample Workspace** and do not need those credentials.

```bash
gcloud run deploy insight-hive \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=production,ALLOW_GUEST_DEMO=true,ADK_MODEL=gemini-2.5-flash \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest,BOOTSTRAP_ADMIN_USERNAME=BOOTSTRAP_ADMIN_USERNAME:latest,BOOTSTRAP_ADMIN_EMAIL=BOOTSTRAP_ADMIN_EMAIL:latest,BOOTSTRAP_ADMIN_PASSWORD=BOOTSTRAP_ADMIN_PASSWORD:latest
```

After deployment, copy the service URL and test it in an incognito window.
Judges must be able to open the guest sample without a login or paywall.

The included `cloudbuild.yaml` provides a repeatable image build and deployment
pipeline. Create the `cloud-run-source-deploy` Artifact Registry repository
before using that configuration.

### Reproduce the deployed revision

Record these values in the Kaggle writeup or repository release:

- Git commit SHA;
- Cloud Run region;
- container/image revision;
- configured `ADK_MODEL` (never the key);
- deployment date;
- final public URL.

See [submission/LIVE_DEMO_CHECKLIST.md](submission/LIVE_DEMO_CHECKLIST.md).

## Production upgrades

- Replace SQLite with Cloud SQL.
- Store uploads and approved reports in Cloud Storage.
- Replace in-memory sessions/memory with a persistent ADK-compatible service.
- Require authenticated Cloud Run access for enterprise datasets.
- Keep Gemini and SMTP credentials in Secret Manager.
