# Judge Evidence

## Verified engineering evidence

Validated in the Linux Docker runtime on **July 2, 2026**:

| Check | Verified result |
| --- | --- |
| Automated test suite | **14/14 passed** |
| Source compilation | **Passed** |
| Container health endpoint | **HTTP 200 / `ok`** |
| Full ADK root-agent health check | **`ADK READY`** |
| Autonomous Northstar mission | **5/5 evidence criteria, 100%** |
| Mission evidence tools | `run_full_analysis_pipeline`, `mcp_get_industry_kpi_playbook`, `run_forecast`, `get_business_context_snapshot`, `check_publish_gate` |
| Live MCP transport | **Passed** (`ListToolsRequest` and `CallToolRequest` observed) |
| Quota-resilience rubric | **5/5 deterministic capability checks** |

The quota-resilience path is clearly labelled in the UI and is not represented
as a Full ADK run. It uses local deterministic tools and TF-IDF retrieval when
the external Gemini free-tier quota is unavailable.

## Final deployed evaluation evidence

Capture these values from **Evaluation → Download Judge Evidence (JSON)** in the
final deployed Full ADK runtime. Do not publish estimated or fabricated scores.

| Metric | Verified result |
| --- | --- |
| Routing pass rate | Pending final deployed run |
| First-attempt accuracy | Pending final deployed run |
| Average case latency | Pending final deployed run |
| MCP runtime case | Pending final deployed run |
| HITL publish-gate case | Pending final deployed run |
| Governed pipeline case | Pending final deployed run |
| Grounding judge score | Pending final deployed run |

Required screenshots:

1. Agent Mission Control success rubric and dynamic tool timeline.
2. Cross-session memory recall showing `LoadMemoryTool`.
3. MCP call in Agent Trace.
4. Rejected report → linked revision → approved download.
5. Ten-case evaluation summary and evidence download.

Public demo URL: **add after Cloud Run deployment**
