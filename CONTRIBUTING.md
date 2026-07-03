# Contributing to InsightHive

**Maintainers:** Jiya Aalwani and Harshit Jetwani

InsightHive is maintained as a collaborative Google ADK capstone project.
Contributions should preserve three properties: agent behavior must be
observable, numeric claims must come from tools, and report publication must
remain human-governed.

## Collaboration workflow

1. Create or accept an issue describing the change and its acceptance criteria.
2. Create a branch from `main`:

   ```bash
   git switch -c feature/short-description
   ```

3. Keep commits focused and never commit secrets or runtime data.
4. Run the verification commands below.
5. Open a pull request and explain:
   - the user or judge-facing outcome;
   - agent/tool behavior changed;
   - tests added or updated;
   - screenshots for UI changes;
   - security or deployment impact.
6. Require at least one collaborator review before merging.

Direct pushes to `main` should be reserved for the initial repository import or
an explicitly agreed release operation.

## Local verification

Preferred Linux/Docker verification:

```powershell
docker compose up -d --build
docker compose exec -T insight-hive python -m compileall -q app.py agents services tools utils pages mcp_server
docker compose exec -T insight-hive python -m pytest -q
```

The production image intentionally excludes test-only packages. Install
`requirements-dev.txt` in a development environment when running tests outside
CI.

## Agent contribution rules

- Add tools only when their output is deterministic or clearly sourced.
- Keep tool docstrings explicit because ADK uses them for routing.
- Do not turn agent delegation into fake business evidence.
- Record tool calls, responses, status, and latency in the trace.
- Keep temperature at zero for judge-facing routing reproducibility.
- Add or update a natural-language routing case when tool selection changes.
- Never mark a mission complete without objective-specific evidence.
- Preserve the distinction between Full ADK and quota-resilient local mode.

## Security rules

Never commit:

- `.env`, `.env.docker`, or `.streamlit/secrets.toml`;
- Gemini, SMTP, or cloud credentials;
- bootstrap usernames or passwords;
- `data/*.db`, user uploads, reports, or exports;
- `.venv`, `venv`, bytecode, or local Git internals in release archives.

Before merging, run:

```powershell
git diff --cached --name-only
git grep --cached -l -I -E "AIza[0-9A-Za-z_-]{30,}|sk-[0-9A-Za-z]{20,}|gsk_[0-9A-Za-z]{20,}"
```

See [SECURITY.md](SECURITY.md) for the threat model and disclosure process.

## Documentation rules

Update documentation in the same pull request when behavior changes:

- `README.md` for setup or user-visible features;
- `submission/ARCHITECTURE.md` for runtime boundaries;
- `submission/EVALUATION.md` for metrics or test methodology;
- `DEPLOYMENT.md` for environment or cloud changes;
- `submission/WRITEUP.md` for material competition claims.

Claims must be reproducible. Do not publish estimated evaluation scores as
measured results.
