# InsightHive — Winning Five-Minute Demo Script

Maximum permitted length: **5:00**. Target export length: **4:40–4:55**.

Do not wait for long operations on camera. Warm the Cloud Run container, run the
evaluation beforehand, and use clean cuts while preserving an honest end-to-end
mission demonstration.

## 0:00–0:25 — Hook: problem and value

**Screen:** InsightHive logo, then premium landing page.

**Say:**

“Business decisions often start with messy files and end in disconnected
spreadsheets, forecasts, reports, and approval emails. A dashboard can show
charts, while a chatbot can generate text—but neither owns the complete,
governed workflow. InsightHive turns one business objective into verified
analysis, forward-looking risk, prioritized action, and a human-approved
executive report.”

## 0:25–0:45 — Why agents and category fit

**Screen:** Architecture diagram; briefly highlight orchestrator and six agents.

**Say:**

“InsightHive is entered in Agents for Business because revenue, margin, returns,
and operational risk are on the line. Agents are central: a Google ADK root
orchestrator delegates to ingestion, quality, analytics, insight, report, and
governance specialists. Deterministic tools calculate facts; agents coordinate
decisions.”

## 0:45–1:55 — Hero demo: one autonomous mission

**Screen:** Enter guest workspace, load Northstar Retail, open Agent Control
Room. Keep the API-key field hidden.

**Mission text:**

> Analyze material revenue and return-rate risks, forecast the next twelve
> periods, recommend prioritized actions, prepare an executive report, and
> verify the human approval gate.

**Say while it runs:**

“Northstar Retail provides two years of reproducible business signals:
seasonality, targets, a campaign lift, a supply disruption, and elevated
returns. I give the system one objective—not a sequence of button clicks.”

**After completion, show:** mission score, success criteria, tool timeline,
forecast artifact, MCP artifact.

**Say:**

“This timeline is generated from the real ADK trace. The orchestrator selected
specialists and tools at runtime. Mission completion is evidence-based: because
I requested a forecast, MCP grounding, an executive report, and governance,
those artifacts must exist. Fluent text alone cannot produce a completed
status.”

Spend the most time here. This is the project’s main differentiator.

## 1:55–2:25 — Live MCP and grounded insight

**Screen:** Expand `mcp_get_industry_kpi_playbook`, then Agent Trace.

**Say:**

“The Insight Agent uses a live ADK McpToolset connected to an stdio KPI server.
This is not an unused MCP folder: the tool call, response, agent author, and
latency are visible. Verified dataset metrics remain separate from industry
guidance, and local TF-IDF vector retrieval reports its source and similarity.”

## 2:25–2:50 — Cross-session memory

**Screen:** Cross-session Memory Proof; show source and fresh recall sessions.

**Say:**

“InsightHive also demonstrates ADK memory. I store a preference in one session,
open a fresh session, and the orchestrator calls LoadMemoryTool before recalling
it. This proves continuity rather than merely preserving text in the browser.”

## 2:50–3:35 — Human-in-the-loop governance

**Screen:** Generate report → pending/locked; cut to admin rejection; return to
auto-revise; show linked revision approved and PDF unlocked.

**Say:**

“For high-impact business outputs, autonomy must stop at the right boundary.
The Report Agent returns a strict four-section JSON contract, while a
deterministic formatter creates the PDF. Download remains locked while pending.
An administrator rejects the first version with feedback; the agent creates a
linked revision; only explicit approval unlocks publication. The model can
recommend—it cannot approve itself.”

## 3:35–4:10 — Evaluation, security, observability

**Screen:** Pre-run Evaluation results; show ten cases, first-attempt accuracy,
MCP/HITL/pipeline proof, evidence download. Briefly show blocked injection.

**Say:**

“Quality is measured in the product. Ten natural-language cases test real
orchestrator tool selection with a reported retry policy. The dashboard exposes
accuracy, latency, MCP, pipeline, and publish-gate evidence as downloadable
JSON. Prompt injection is blocked before model execution, uploads are confined,
numeric claims can be grounded, and no API key or password is committed.”

Do not run all ten cases during recording; show the verified completed run.

## 4:10–4:35 — Build and deployability

**Screen:** Repository tree, Dockerfile, CI workflow, tests, Cloud Run diagram.

**Say:**

“The application is reproducible with Python 3.12 and Docker, deployable to
Cloud Run, and tested in GitHub Actions. Fourteen contract and integration tests
cover guardrails, vector retrieval, report boundaries, routing registry, sample
signals, and mission success logic. The clean-package builder removes secrets,
databases, uploads, reports, virtual environments, and bytecode.”

## 4:35–4:55 — Close

**Screen:** InsightHive logo plus GitHub and live-demo URLs.

**Say:**

“InsightHive is not a chatbot wrapped around a dataframe. It is an observable,
evaluated, memory-enabled, MCP-connected, human-governed agent system designed
to turn business data into decisions people can trust.”

## Recording priorities

| Feature | Time | Priority |
| --- | ---: | --- |
| Mission Control + evidence rubric | 70 sec | Highest |
| HITL reject/revise/approve | 45 sec | Highest |
| MCP runtime proof | 30 sec | High |
| Evaluation/security | 35 sec | High |
| Memory proof | 25 sec | Medium-high |
| Architecture/problem | 45 sec | Required |
| Repository/deployment | 25 sec | Required |

## YouTube upload

**Recommended title:**  
`InsightHive — Governed Multi-Agent Business Intelligence | Google ADK Kaggle Capstone`

**Recommended description:**

```text
InsightHive turns one business objective into verified analysis, forecasting,
MCP-grounded recommendations, and human-approved executive reports.

Track: Agents for Business
Live demo: show the final verified public URL on screen
GitHub: https://github.com/Harshit-jetwani07/InsightHive

Built with Google ADK, Gemini, MCP, Streamlit, Docker, and Cloud Run.
```

Set visibility to **Public**, enable HD processing, verify audio, and confirm the
final duration is no more than five minutes before attaching it to Kaggle.
