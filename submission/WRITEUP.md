# InsightHive: From Messy Business Files to Governed Decisions

## Subtitle

One objective. Seven coordinated Google ADK agents. Verifiable analysis,
MCP-grounded recommendations, and human-approved executive reports.

**Track:** Agents for Business  
**Team:** **Jiya Aalwani (Team Lead & Co-Creator)** and
**Harshit Jetwani (Co-Creator)**  
**Public project:** [InsightHive on GitHub](https://github.com/Harshit-jetwani07/InsightHive)

**YouTube demo:** Insert the verified public video URL before submission.

## The problem

Business decisions rarely begin with clean data. Teams receive inconsistent CSV
and Excel exports, spend hours identifying useful columns, calculate KPIs in
separate tools, investigate anomalies, build forecasts, draft reports, and then
coordinate approval through email. The cost is more than analyst time: slow or
unverified analysis can affect revenue, inventory, margin, customer experience,
and operational risk.

Dashboards help users inspect charts, but they do not own an objective from end
to end. Generic data chatbots have the opposite problem: they sound helpful but
may use the wrong field, invent a number, skip uncertainty, or publish a report
without review.

I built InsightHive to answer a practical question:

> Can a business user state one objective and receive a complete,
> evidence-backed decision workflow—while preserving traceability, security,
> and human authority?

## The solution

InsightHive is a governed agentic decision-intelligence platform built with
Google ADK. A user uploads a business file or opens the reproducible Northstar
Retail demo, then gives **Agent Mission Control** one objective:

> Analyze material revenue and return-rate risks, forecast the next twelve
> periods, recommend prioritized actions, prepare an executive report, and
> verify the approval gate.

The root orchestrator plans the work and delegates it to six specialists:

1. **Ingestion Agent** confines file access, parses CSV/Excel, and verifies the
   schema.
2. **Quality Agent** scores readiness and investigates missing values,
   duplicates, and anomalies.
3. **Analytics Agent** selects statistics, correlations, and forecasting tools.
4. **Insight Agent** combines verified metrics with industry guidance from
   vector retrieval and a live MCP server.
5. **Report Agent** produces a strict four-section executive-report contract
   and validates numeric grounding.
6. **Governance Agent** enforces pending, rejected, revised, and approved states.

The interface renders the actual ADK trace—not a pre-scripted animation. Judges
can inspect the selected specialist, tool name, structured result, status, and
latency. A deterministic mission rubric checks whether the objective received
the evidence it requested. The mission cannot be marked complete merely because
the model returned fluent text.

## Why agents?

This workflow contains different responsibilities, permissions, and stopping
conditions. A single prompt cannot safely replace them.

- Parsing requires confined filesystem behavior.
- Analysis requires deterministic computation rather than model arithmetic.
- Recommendations require external business context without contaminating
  measured facts.
- Reporting requires a machine-checkable content contract.
- Publication requires human approval.

Agents make those boundaries explicit while allowing one orchestrator to
coordinate them dynamically. The value of the system is therefore not “chat
with a spreadsheet”; it is controlled delegation across an auditable business
process.

## Architecture and course concepts

InsightHive demonstrates four concepts explicitly listed in the competition
rubric:

### 1. Agent / multi-agent system with Google ADK

A root `LlmAgent` coordinates six ADK sub-agents. Mission Control sends one
`AUTONOMOUS MISSION` request; the orchestrator chooses transfers and tools.
Temperature is zero and the model is pinned for reproducible routing.

### 2. MCP server

The Insight Agent owns a real ADK `McpToolset` connected through stdio to the
KPI playbook MCP server. The trace records
`mcp_get_industry_kpi_playbook`, proving that MCP is part of runtime execution
rather than an unused server in the repository.

### 3. Security features

Uploads are confined to an application directory; filenames are sanitized.
Prompt-injection patterns are blocked before model execution. Secrets are loaded
from environment variables or private Streamlit configuration and are excluded
from Git, Docker context, CI, and the clean-package builder. Numeric claims can
be checked against dataset values. Most importantly, pending or rejected reports
cannot be downloaded.

### 4. Deployability

The same Python 3.12 Linux image runs locally through Docker Compose and can be
deployed to Cloud Run. Cloud Build, health checks, environment templates, and
reproduction instructions are included. A keyless sample mode preserves a
deterministic demonstration when external AI is unavailable.

Supporting concepts include ADK sessions, cross-session memory,
human-in-the-loop revision lineage, tool observability, vector RAG, contract
validation, and agent-level evaluation.

## Three differentiators

### A mission is scored, not merely answered

The objective text determines required evidence. If it asks for a forecast,
report, MCP grounding, or approval check, the corresponding tool evidence must
appear. Missing evidence produces **needs review**, not a false success.

### Reports remain under human control

The Report Agent must return valid JSON with executive summary, findings,
recommendations, and limitations. Invalid output receives one repair attempt.
The deterministic PDF formatter cannot silently call a legacy LLM author in ADK
mode. After generation, download remains locked until an administrator approves
the report. A rejection can produce a linked revision that preserves review
lineage.

### Quality is visible

The evaluation tab sends ten natural-language cases through the real
orchestrator and checks the tools it selected. It reports pass rate,
first-attempt accuracy, retry recovery, and latency, with dedicated proof for
MCP, the governed pipeline, and the HITL publish gate. Results can be downloaded
as JSON instead of being claimed without evidence.

## Reproducible demo

Northstar Retail contains two years of weekly data with growth, seasonality,
targets, margins, campaign lift, supply disruption, and elevated returns. These
signals make the walkthrough repeatable while still requiring genuine
calculation.

The winning demo sequence is:

1. Load Northstar Retail and launch one autonomous mission.
2. Show the mission rubric and dynamic agent/tool timeline.
3. Expand the MCP and forecast artifacts.
4. Store a user preference, start a fresh session, and show `LoadMemoryTool`
   recalling it.
5. Generate a report, prove download is blocked, reject it as admin, create a
   linked revision, approve it, and unlock the PDF.
6. Show Agent Trace and the ten-case evaluation evidence.

## Evaluation and engineering quality

The repository contains fourteen unit and integration contract tests covering
guardrails, sample-data signals, vector retrieval, report contracts, routing
registry integrity, and mission completion logic. GitHub Actions runs Python
3.12 compilation, tests, and secret/runtime hygiene checks on every push.

InsightHive also contains a clean-source builder that uses an allow list and
generates SHA-256 checksums. Virtual environments, databases, secrets, uploads,
reports, exports, Git history, and bytecode are excluded.

## Collaboration and reproducibility

InsightHive was collaboratively conceived and built by **Jiya Aalwani** and
**Harshit Jetwani**, with Jiya serving as the designated Kaggle Team Lead and
final submission owner. Both teammates contributed as co-creators and are
credited together across the repository, writeup, and demo.

The project is prepared for a collaborative submission. Agent engineering,
evaluation, product UX, documentation, and demo production can be reviewed
through GitHub branches and pull requests, while CI provides one shared quality
gate. Final team credits will map each collaborator to a concrete contribution.
Only one agreed team owner will perform the Kaggle submission, preventing
duplicate entries or conflicting project versions.

Reproduction does not depend on a developer workstation: Python 3.12, Docker,
environment templates, Cloud Build, health checks, tests, and deployment steps
are included in the public repository. Secrets and runtime data are explicitly
excluded.

## Build journey

The project began as a dashboard-oriented analyst application. The main design
challenge was making agents central rather than decorative. I progressively
moved ingestion, forecasting, anomaly investigation, reporting, and evaluation
behind ADK routing; replaced a scripted “agent pipeline” with a single
orchestrator-owned mission; connected the MCP server to the live runtime; added
cross-session memory proof; separated report authorship from deterministic PDF
formatting; and turned governance into an enforceable tool and UI gate.

This journey also exposed a real deployment issue: managed Windows Application
Control blocked native Python extensions. Instead of weakening the agent
implementation, I added a reproducible Linux Docker path matching Cloud Run.

## Limitations and next steps

The demo uses in-memory ADK sessions and SQLite; production scale would use
persistent session storage, Cloud SQL, and object storage. TF-IDF vector
retrieval was chosen for transparent evidence and low-cost reproducibility;
larger knowledge bases could add managed embeddings. LLM routing can still be
affected by quota or provider availability, so deterministic tools, retries,
mission scoring, and sample mode are retained as resilience layers.

## Closing

InsightHive’s core idea is simple: business AI should not only generate an
answer—it should show how the answer was produced, prove that required evidence
exists, and know when a human must decide.
