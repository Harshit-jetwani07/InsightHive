# Judge Evidence

**Team:** Harshit Jetwani (Team Leader & Co-Creator) · Jiya Aalwani (Team Member & Co-Creator)

## Verified engineering evidence

Validated in the Linux Docker runtime on **July 3, 2026**:

| Check | Verified result |
| --- | --- |
| Automated test suite | **17/17 passed** |
| Source compilation | **Passed** |
| Container health endpoint | **HTTP 200 / `ok`** |
| Live ADK smoke test | **Root agent selected and completed `run_full_analysis_pipeline`** |
| Autonomous Northstar mission | **5/5 evidence criteria, 100%, 34.8 seconds** |
| Mission evidence tools | `run_full_analysis_pipeline`, `mcp_get_industry_kpi_playbook`, `run_forecast`, `get_business_context_snapshot`, `check_publish_gate` |
| Live MCP transport | **Passed** (`ListToolsRequest` and `CallToolRequest` observed) |
| Revenue forecast | **Increasing; MAE 12,293; RMSE 15,358; 12 periods** |
| Quota-resilient anomaly scan | **50 highest-priority unusual rows returned with severity scores** |
| Cross-session memory | **Preference recalled through Google ADK Memory Service** |
| Human approval gate | **Pending download locked; approved download unlocked** |
| Generated report | **Four-page PDF, 4,434 extracted text characters, visual render passed** |
| Deterministic tool contracts | **5/5 passed, 100%, 2.48 seconds total** |
| Quota-resilient contract router | **10/10 passed, 100%** |

Machine-readable artifacts:

- [`deterministic_tool_evidence.json`](evidence/deterministic_tool_evidence.json)
- [`quota_resilient_routing_evidence.json`](evidence/quota_resilient_routing_evidence.json)
- [`sample_approved_business_report.pdf`](evidence/sample_approved_business_report.pdf)

## Claim boundaries

The quota-resilient contract-router result is deliberately reported separately.
It proves deterministic intent routing during provider unavailability and is
**not** presented as real ADK/LLM routing accuracy.

The captured Full ADK mission is real: the root orchestrator selected all five
evidence tools, including the MCP playbook, forecast, report context, and human
publish gate. Its trace is retained in the evidence gallery.

## Provider-backed routing claim boundary

A stable final ten-case provider-backed ADK routing suite was not captured.
Therefore no provider-backed pass rate, first-attempt accuracy, average latency,
or grounding-judge score is claimed. The 10/10 quota-resilient result remains
clearly labelled as deterministic routing, while the real autonomous Full ADK
mission is supported by its five captured tool calls and trace.

All headline claims map to direct proof in
[`docs/evidence/README.md`](../docs/evidence/README.md).

## Screenshot index

1. Mission summary: [`mission-control-100-percent.png`](../docs/screenshots/mission-control-100-percent.png)
2. Executive synthesis: [`executive-synthesis-detailed.png`](../docs/screenshots/executive-synthesis-detailed.png)
3. Forecast: [`forecast-evidence.png`](../docs/screenshots/forecast-evidence.png)
4. Five-tool execution: [`five-tool-agent-execution.png`](../docs/screenshots/five-tool-agent-execution.png)
5. ADK mission trace: [`adk-mission-trace.png`](../docs/screenshots/adk-mission-trace.png)
6. Memory recall: [`adk-memory-recall.png`](../docs/screenshots/adk-memory-recall.png)
7. Pending report gate: [`report-pending-human-review.png`](../docs/screenshots/report-pending-human-review.png)
8. Approved report: [`report-approved-download.png`](../docs/screenshots/report-approved-download.png)
9. Resilient routing summary: [`resilient-routing-summary.png`](../docs/screenshots/resilient-routing-summary.png)
10. Resilient routing cases: [`resilient-routing-cases.png`](../docs/screenshots/resilient-routing-cases.png)
11. Anomaly result table: [`anomaly-results-table.png`](../docs/screenshots/anomaly-results-table.png)
12. Anomaly severity chart: [`anomaly-severity-chart.png`](../docs/screenshots/anomaly-severity-chart.png)

Public demo URL: **add after Cloud Run deployment**
