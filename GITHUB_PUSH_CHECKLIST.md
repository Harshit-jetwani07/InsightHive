# InsightHive GitHub Push Checklist

- [ ] Final collaborator GitHub accounts invited.
- [ ] `main` branch protection and Capstone CI required where available.
- [ ] Pull-request and issue templates present.
- [ ] Team credits agreed and ready for Kaggle writeup/video description.
- [ ] Repository name, description, topics, and social preview use InsightHive.
- [ ] Public clone tested from an incognito/logged-out browser.

## Included

- Application source: `app.py`, `agents/`, `tools/`, `services/`, `utils/`, `pages/`
- Agent assets: `rag/`, `mcp_server/`, `evaluation/`
- Tests and CI: `tests/`, `.github/workflows/ci.yml`
- Brand asset: `assets/insighthive-logo.jpeg`
- Deployment: `Dockerfile`, `compose.yaml`, `cloudbuild.yaml`, deployment scripts
- Documentation, submission evidence templates, examples, and `LICENSE`
- Official-rubric map, Kaggle posting guide, live-demo checklist, and timed
  YouTube narration script
- Empty runtime placeholders: `data/.gitkeep`, `uploads/.gitkeep`,
  `reports/.gitkeep`, `exports/.gitkeep`

## Excluded

- `.venv/`, Python bytecode, caches
- `.env`, `.env.docker`, Streamlit private secrets
- SQLite databases and user records
- Uploaded datasets, generated reports, exports
- `dist/` build artifacts
- Local editor/Codex metadata

## Final commands

Run only after confirming the Git author and empty GitHub repository URL:

```powershell
git commit -m "Initial release: InsightHive Google ADK capstone"
git remote add origin <repository-url>
git push -u origin main
```
