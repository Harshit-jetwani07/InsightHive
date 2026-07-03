# Security Policy

**Maintainers:** Jiya Aalwani and Harshit Jetwani

## Scope

InsightHive analyzes user-provided business files and can call an external
Gemini model through Google ADK. The public competition deployment is a demo,
not a production data-processing service. Use only the bundled synthetic
Northstar Retail dataset in the public judge flow.

## Threat model and controls

| Risk | Control |
| --- | --- |
| Path traversal through uploaded filenames | Basename normalization, sanitized names, confined upload directory |
| Prompt injection | Input validation before ADK execution and tool-backed numeric claims |
| LLM arithmetic or fabricated metrics | Deterministic Python analytics tools and structured artifacts |
| Unsupported report claims | Numeric-grounding validation and strict report JSON contract |
| Unauthorized report release | Pending/rejected reports blocked; only approved records unlock download |
| Secret exposure | Environment/Secret Manager loading, ignored private files, CI hygiene checks |
| Public-demo persistence | Temporary guest identity and synthetic sample-only recommendation |
| Provider outage or quota exhaustion | Clearly labelled deterministic resilience mode; no false Full ADK claim |
| Malicious spreadsheet content | No macro execution; supported inputs are parsed as tabular CSV/XLS/XLSX data |

## Secret handling

Use `.env.docker.example`, `.env.example`, or
`.streamlit/secrets.example.toml` only as templates. Real values belong in:

- local ignored files;
- Streamlit Community Cloud private Secrets;
- Google Secret Manager for Cloud Run.

Never place credentials in source, issues, pull requests, screenshots, videos,
Kaggle writeups, shell history, or downloadable evidence.

If a key is exposed:

1. revoke it immediately at the provider;
2. remove it from the current tree and Git history;
3. rotate every credential that shared the same project or account;
4. inspect access and billing logs;
5. document the incident without repeating the secret.

## Public deployment guidance

- Set `APP_ENV=production`.
- Enable guest demo only for the synthetic sample workspace.
- Keep admin credentials private and outside the video.
- Use an isolated Gemini project with budget and quota monitoring.
- Treat local SQLite, uploads, and generated reports as ephemeral.
- Do not invite judges to upload confidential data.

## Reporting a vulnerability

Do not open a public issue containing exploit details, private data, or
credentials. Contact the repository owner privately through the security
contact configured on the GitHub profile. Include affected revision, impact,
reproduction steps, and a suggested remediation when possible.
