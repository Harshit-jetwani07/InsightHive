# InsightHive — Official Kaggle Rubric Alignment

Competition: [AI Agents: Intensive Vibe Coding Capstone Project](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project)

**Team:** Harshit Jetwani (Team Leader & Co-Creator) · Jiya Aalwani (Team Member & Co-Creator)

## Selected track: Agents for Business

The official track asks for agents that solve compelling enterprise problems
with cost or revenue on the line, including driving insights. InsightHive turns
business files into governed revenue, margin, return-risk, and operational
decisions, so this is the strongest and most defensible track.

Do not select Freestyle or Concierge Agents.

## 100-point evidence map

### Category 1 — Pitch: Problem, Solution, Value (30 points)

| Criterion | Points | Evidence to present |
| --- | ---: | --- |
| Core Concept & Value | 10 | One objective replaces fragmented cleaning, analysis, forecasting, reporting, and approval. Emphasize revenue/risk impact and why agents are central. |
| YouTube Video | 10 | ≤5 minutes; problem → why agents → architecture → live mission → memory/MCP/HITL/eval → build/close. |
| Writeup | 10 | `submission/WRITEUP.md`: problem, solution, architecture, concepts, differentiators, journey, evaluation, limitations. |

### Category 2 — Implementation: Architecture, Code (70 points)

| Criterion | Points | Evidence to present |
| --- | ---: | --- |
| Technical Implementation | 50 | Google ADK root + six agents; 13 deterministic tools; live MCP; vector RAG; memory; trace; mission rubric; report contract; HITL; routing eval; Docker/Cloud Run; security. |
| Documentation | 20 | Root `README.md`: problem, value, architecture diagram, setup, testing, security, deployment, repository map, submission links. |

Supporting judge documentation:

- `submission/ARCHITECTURE.md` — agents, sequence, trust boundaries, failure handling;
- `submission/EVALUATION.md` — software, tool, routing, and mission evaluation layers;
- `SECURITY.md` — threat model, secret handling, public-demo constraints;
- `CONTRIBUTING.md` — reproducible collaborative engineering workflow;
- `submission/TEAM_COLLABORATION.md` — Kaggle and GitHub team procedure.

## Official course concepts demonstrated

Only three are required. Highlight these four because each has direct evidence:

1. **Agent / Multi-agent system (ADK)** — code and mission trace.
2. **MCP Server** — code plus `mcp_get_industry_kpi_playbook` in trace.
3. **Security features** — code and blocked prompt/download demonstration.
4. **Deployability** — Docker/Cloud Run configuration and public demo.

Do not claim Antigravity or Agents CLI unless they were genuinely used and can
be demonstrated.

## Judge-facing “wow” moments

Prioritize these in order:

1. **One prompt controls the complete workflow.** Show one root-orchestrator
   mission rather than clicking every dashboard tab.
2. **Mission completion requires evidence.** Show missing/pass criteria and
   success score.
3. **MCP is visibly live.** Expand its structured artifact and show it in trace.
4. **Memory survives a session boundary.** Store preference, create fresh
   session, recall through `LoadMemoryTool`.
5. **Human authority is enforced.** Pending report cannot download; rejection
   creates linked revision; approval unlocks PDF.
6. **Quality claims are measurable.** Show ten routing cases and downloadable
   evidence JSON.

## Required submission assets

- Kaggle Writeup with title, subtitle, detailed analysis, and selected track.
- Media Gallery with a required cover image.
- Public YouTube video, five minutes or less.
- Public project link without login/paywall, if applicable; otherwise public
  GitHub repository with detailed setup.
- Final **Submit** action before the deadline. Drafts are not judged.

## Recommended media gallery

1. Cover: `assets/insighthive-logo.jpeg`.
2. Agent Mission Control with success rubric.
3. Dynamic agent/tool timeline with MCP artifact open.
4. Cross-session memory proof.
5. Pending/rejected/revised/approved report flow.
6. Evaluation metrics and evidence-download button.
7. Architecture diagram exported from the README Mermaid diagram.

## Claims policy

- Never show an API key, password, `.env.docker`, admin credential, or private
  dataset in screenshots/video.
- Never publish estimated evaluation numbers. Use the final deployed evidence.
- Clearly distinguish deterministic sample mode from Full ADK mode.
- State limitations honestly; reliability mechanisms are a strength.
