# InsightHive

![InsightHive logo](assets/insighthive-logo.jpeg)

> **AI agents. Smart insights. Better decisions.**

InsightHive is a governed, observable Google ADK multi-agent system that turns
messy business files into verified analysis, forward-looking risk signals,
MCP-grounded recommendations, and approval-gated executive reports.

**Kaggle track:** Agents for Business  
**Competition:** [AI Agents: Intensive Vibe Coding Capstone Project](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project)  
**Team:** **Harshit Jetwani — Team Leader & Co-Creator** · **Jiya Aalwani — Team Member & Co-Creator**
**Public source:** [github.com/Harshit-jetwani07/InsightHive](https://github.com/Harshit-jetwani07/InsightHive)  
**Submission status:** GitHub-ready; public demo and video links will be added
after their final incognito-access checks.

## The problem

Business teams routinely receive inconsistent CSV and Excel files. Analysts must
clean them, calculate KPIs, investigate anomalies, forecast performance, write
executive summaries, and wait for approval. Conventional dashboards expose
charts but do not coordinate the workflow. Generic chatbots can select the wrong
columns, invent numbers, and publish outputs without review.

InsightHive addresses a problem with revenue and operational risk on the line:
how can one business objective become a traceable, evidence-backed decision
workflow without giving an LLM uncontrolled access to data or publishing?

## Why agents are central

This is not a chatbot wrapped around a dataframe. A root ADK orchestrator owns
the objective, selects specialists and deterministic tools, and continues until
the objective-specific evidence rubric is satisfied.

- **Ingestion Agent** — confined CSV/Excel parsing and schema verification.
- **Quality Agent** — readiness scoring, missing values, duplicates, anomalies.
- **Analytics Agent** — descriptive statistics, correlations, and forecasting.
- **Insight Agent** — business implications, vector RAG, and live MCP retrieval.
- **Report Agent** — contract-validated executive report sections.
- **Governance Agent** — human approval, rejection, revision, and publish gates.
- **Root Orchestrator** — dynamic planning, delegation, synthesis, and memory.

## One-objective experience

In **Agent Mission Control**, a user enters one goal such as:

> Analyze material revenue and return-rate risks, forecast the next twelve
> periods, recommend actions, prepare an executive report, and verify the human
> approval gate.

The UI then exposes:

- specialists and tools selected by the orchestrator;
- structured tool artifacts and latency;
- an objective-specific mission success score;
- MCP, forecast, report, and governance evidence;
- the final executive synthesis.

## Why InsightHive is different

Most analytics apps stop at charts or chat. InsightHive demonstrates a complete
agent-owned decision workflow:

| Differentiator | Why it matters |
| --- | --- |
| **One objective → full workflow** | The root orchestrator coordinates analysis, industry research, forecasting, reporting, and governance without asking the user to operate separate tabs. |
| **Evidence-based completion** | A fluent answer is insufficient; Mission Control checks that every objective-specific tool artifact exists. |
| **Live MCP grounding** | Industry guidance is fetched through an ADK `McpToolset`, not an unused server or prewritten UI response. |
| **Cross-session memory** | A preference stored in one ADK session is recalled from a fresh session through `LoadMemoryTool`. |
| **Human authority** | Pending or rejected reports remain locked until an administrator approves a valid revision. |
| **Honest resilience** | Automatic private three-key failover can recover from provider quota errors; deterministic fallback is clearly labelled and never misrepresented as Full ADK or live MCP execution. |

## Architecture

![InsightHive multi-agent architecture](docs/architecture.png)

```mermaid
flowchart LR
    U["Business objective / file"] --> UI["InsightHive Mission Control"]
    UI --> O["Google ADK Root Orchestrator"]
    O --> I["Ingestion Agent"]
    O --> Q["Quality Agent"]
    O --> A["Analytics Agent"]
    O --> N["Insight Agent"]
    O --> R["Report Agent"]
    O --> G["Governance Agent"]
    I --> DT["Confined parsing tools"]
    Q --> DT2["Quality + anomaly tools"]
    A --> DT3["Stats + correlation + forecast"]
    N --> MCP["ADK McpToolset → KPI server"]
    N --> VR["TF-IDF cosine-vector RAG"]
    R --> C["Strict four-section JSON contract"]
    C --> PDF["Deterministic PDF formatter"]
    G --> H["Pending → reject/revise → approve"]
    H --> DL["Approved download only"]
    O --> M["Cross-session LoadMemoryTool"]
    O --> T["Trace + artifacts + latency"]
    T --> E["10-case routing evaluation"]
```

See [submission/ARCHITECTURE.md](submission/ARCHITECTURE.md) for the governed
runtime flow.

## Evidence gallery

### Autonomous Mission Control

One objective produced five required evidence tools and passed all five mission
criteria in 34.8 seconds.

![Mission Control showing 100 percent evidence completion](docs/screenshots/mission-control-100-percent.png)

### Agent-selected tools and live trace

The root orchestrator selected the governed pipeline, live MCP playbook,
forecast, report-context, and publish-gate tools. The trace records calls,
responses, status, and latency.

![Five completed evidence tools](docs/screenshots/five-tool-agent-execution.png)

![Live ADK mission trace](docs/screenshots/adk-mission-trace.png)

### Forecast evidence

The twelve-period Revenue forecast reports an increasing trend, MAE 12,293,
and RMSE 15,358 alongside actual and projected values.

![Revenue forecast evidence](docs/screenshots/forecast-evidence.png)

### Anomaly evidence

The quality workflow surfaced 50 highest-priority unusual rows for review and
rendered their anomaly-severity distribution. This capture is explicitly
labelled as quota-resilient deterministic tool execution.

![Anomaly result table](docs/screenshots/anomaly-results-table.png)

![Anomaly severity chart](docs/screenshots/anomaly-severity-chart.png)

### Executive synthesis and governance result

The final response separates observations, forecast, recommendations, and the
mandatory approval requirement.

![Executive mission synthesis](docs/screenshots/executive-synthesis-detailed.png)

### Memory and human approval

![Cross-session ADK memory recall](docs/screenshots/adk-memory-recall.png)

![Pending report remains locked](docs/screenshots/report-pending-human-review.png)

![Approved report download unlocked](docs/screenshots/report-approved-download.png)

The rendered sample PDF is available at
[`submission/evidence/sample_approved_business_report.pdf`](submission/evidence/sample_approved_business_report.pdf).
It contains a cover, executive explanation, measured KPI table, segment
patterns, recommended actions, limitations, a management review checklist, and
the human-approval publication condition across four readable pages.

## Course concepts demonstrated

The competition requires at least three; InsightHive visibly demonstrates four
official concepts and several supporting practices:

| Official concept | InsightHive evidence |
| --- | --- |
| Agent / Multi-agent system (ADK) | Root orchestrator, six specialists, dynamic transfers |
| MCP Server | Live `McpToolset` calling the KPI playbook stdio server |
| Security features | Confined uploads, injection guard, secret hygiene, numeric grounding, HITL gate |
| Deployability | Docker Compose, Cloud Run, Cloud Build, reproducible environment |

Additional evidence includes ADK sessions, cross-session memory, deterministic
function tools, vector RAG, observability, evaluation, report contracts, and
human-in-the-loop revision lineage.

## Technical highlights

- Google ADK root agent with six specialist sub-agents.
- Thirteen deterministic tools for ingestion, analysis, retrieval, validation,
  reporting, and governance.
- Live MCP interoperability—not a mocked server or documentation-only claim.
- Auditable TF-IDF cosine-vector retrieval with source and similarity scores.
- Cross-session memory proof: store preference → fresh session → `load_memory`.
- Structured trace events for agent, tool, arguments, response, status, latency.
- Ten natural-language routing cases with one explicit retry and downloadable
  judge-evidence JSON.
- Mission completion is blocked unless objective-specific evidence passes.
- Temperature `0` and pinned `gemini-2.5-flash` for reproducibility and
  quota efficiency.
- Report Agent JSON validation, repair retry, and a hard boundary preventing
  legacy prose generation in ADK report mode.
- Human approval is mandatory before PDF download.
- GitHub Actions compiles, tests, and checks secret/runtime hygiene.

## Reliable demonstration data

**Northstar Retail** is a two-year weekly benchmark containing deliberate but
realistically distributed signals:

- growth and seasonality;
- regional and product targets;
- margin movement;
- an East electronics campaign lift;
- a West electronics supply disruption;
- persistently elevated South apparel returns.

This makes the demo repeatable while still requiring actual analysis. Uploaded
datasets are quality-scored because insight reliability depends on source data.

## Quick start — Full ADK Docker mode

Prerequisites: Docker Desktop with WSL 2 and at least one Gemini API key.
For a quota-resilient demo, configure up to three keys from separate Google
projects in `GOOGLE_API_KEY`, `GOOGLE_API_KEY_2`, and `GOOGLE_API_KEY_3`.
All user-facing ADK workflows share this failover pool. A backup is attempted
only after an actual provider failure; keys are never displayed in the UI,
trace, evidence, or repository.

```powershell
git clone https://github.com/Harshit-jetwani07/InsightHive.git
cd InsightHive
Copy-Item .env.docker.example .env.docker
notepad .env.docker
docker compose up -d --build
```

Open [http://localhost:8501](http://localhost:8501), choose
**Launch judge demo**, load **Northstar Retail Demo**, and open
**Agent Control Room**.

Verify:

```powershell
docker compose ps
docker compose logs -f insight-hive
```

Stop:

```powershell
docker compose down
```

`.env.docker` is ignored by Git. Never place API keys or passwords in source,
screenshots, videos, commits, or Kaggle writeups.

## Native sample mode

Python 3.12 is pinned in `.python-version`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Without Gemini, Sample Intelligence Mode keeps deterministic statistics,
quality checks, reports, and contract tests demonstrable. Full competition
evidence should be recorded in Docker ADK mode.

## Evaluation and testing

```powershell
docker compose run --rm insight-hive sh -c "pip install -q pytest && python -m pytest -q"
```

In the app, **Evaluation** measures:

- routing pass rate and first-attempt accuracy;
- selected tools for all ten cases;
- average and total latency;
- MCP runtime evidence;
- governed pipeline evidence;
- HITL publish-gate evidence;
- grounding and usefulness.

Download `adk_evaluation_evidence.json` and attach its headline metrics to the
writeup. Never fabricate a benchmark; record the final deployed run.

### Verified engineering metrics

| Metric | Verified result | Scope |
| --- | ---: | --- |
| Automated tests | **17 / 17 passed** | Guardrails, full deterministic workflow, RAG, API-key pool, multi-page report, routing registry, mission rubric, sample signals |
| Deterministic tool contracts | **5 / 5 passed (100%)** | Northstar Retail, recorded July 3, 2026 |
| Deterministic evaluation latency | **2.48 seconds total** | Local Docker run; not LLM routing latency |
| Full ADK autonomous mission | **5 / 5 evidence criteria (100%)** | Analysis, live MCP, forecast, report context, publish gate |
| Full ADK mission tools | **5 evidence tools** | Internal agent-transfer events excluded |
| Full ADK mission latency | **34.8 seconds** | Northstar Retail evidence run |
| Revenue forecast | **Increasing; MAE 12,293; RMSE 15,358** | Twelve future periods |
| Quota-resilient contract routing | **10 / 10 passed (100%)** | Deterministic intent router; not ADK routing accuracy |
| Container health | **HTTP 200 `ok`** | Linux Docker runtime |
| Ten-case ADK routing accuracy | **Pending final deployed run** | Must be captured with active Gemini quota |

The exact deterministic artifact is committed at
[`submission/evidence/deterministic_tool_evidence.json`](submission/evidence/deterministic_tool_evidence.json).
Quota-resilient routing evidence is committed separately at
[`submission/evidence/quota_resilient_routing_evidence.json`](submission/evidence/quota_resilient_routing_evidence.json).
Neither deterministic score is presented as real ADK routing accuracy.

## Deployment

- [Docker and Cloud Run instructions](DEPLOYMENT.md)
- [Cloud Build configuration](cloudbuild.yaml)
- [Reproduction and deployment checklist](submission/SUBMISSION_CHECKLIST.md)

A live deployment is optional, but the Kaggle project must provide a public
project link. This public GitHub repository provides full reproduction
instructions; when the Cloud Run demo is attached, **Launch judge demo** must
remain accessible without a login or paywall.

## Security and governance

- No seeded credentials or committed secrets.
- Environment/Streamlit-secret bootstrap only.
- Upload paths are confined and filenames sanitized.
- Prompt-injection patterns are blocked before model execution.
- Numeric claims can be checked against dataset evidence.
- Pending and rejected reports cannot be downloaded.
- Revisions retain parent id and review history.
- The clean-package builder excludes virtual environments, Git internals,
  databases, uploads, reports, exports, secrets, and bytecode.

## Repository map

```text
agents/          ADK root and specialist agents
tools/           deterministic function, MCP/RAG, validation, governance tools
services/        runner, sessions/memory, traces, evaluation, contracts
mcp_server/      live KPI playbook MCP server
rag/             public industry KPI knowledge base
pages/           authentication and administration UI
tests/           14 unit/integration contract tests
evaluation/      deterministic and real-routing cases
submission/      writeup, video script, rubric map, evidence checklist
```

## Submission resources

- [Kaggle-ready writeup](submission/WRITEUP.md)
- [Official-rubric alignment](submission/RUBRIC_ALIGNMENT.md)
- [Five-minute narration and shot list](submission/DEMO_VIDEO_SCRIPT.md)
- [Posting and media checklist](submission/KAGGLE_POSTING_GUIDE.md)
- [Judge evidence sheet](submission/EVIDENCE.md)
- [Evaluation methodology](submission/EVALUATION.md)
- [Security policy](SECURITY.md)
- [Contribution workflow](CONTRIBUTING.md)
- [Kaggle team collaboration guide](submission/TEAM_COLLABORATION.md)
- [Deployment guide](DEPLOYMENT.md)

## Collaboration

InsightHive is prepared for a collaborative Kaggle submission and public GitHub
development. Contributors should use branches, pull requests, CI, and one
review before merging. The final Kaggle roster must credit each teammate's
actual contribution and only one agreed owner should perform the final
submission.

InsightHive was collaboratively designed and built by **Harshit Jetwani** and
**Jiya Aalwani**. Harshit Jetwani is the designated Kaggle Team Leader and final
submission owner; both teammates should appear in the official Kaggle team and
receive co-creator credit in the writeup, video description, and repository.

See [CONTRIBUTING.md](CONTRIBUTING.md),
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and
[submission/TEAM_COLLABORATION.md](submission/TEAM_COLLABORATION.md).

## License

InsightHive source code and repository documentation are available under the
[MIT License](LICENSE). Third-party platforms, services, and dependencies retain
their respective terms.

## Creators

- **Harshit Jetwani** — Team Leader & Co-Creator
- **Jiya Aalwani** — Team Member & Co-Creator
