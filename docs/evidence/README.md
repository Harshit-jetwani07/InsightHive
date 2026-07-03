# InsightHive Metric Evidence

This folder indexes the exact logs, JSON artifacts, and screenshots supporting
the headline metrics in the README and Kaggle writeup.

| Claim | Direct proof |
| --- | --- |
| Automated tests: **17/17 passed** | [Terminal screenshot](tests-17-passed.png) · [Text log](test-results.txt) |
| Container health: **HTTP 200 `ok`** | [Terminal screenshot](docker-health-200.png) · [Text log](runtime-health.txt) |
| Deterministic tool evaluation: **5/5 passed** | [Evaluation JSON](../../submission/evidence/deterministic_tool_evidence.json) |
| Autonomous mission: **5/5 evidence criteria, 100%, 34.8 seconds** | [Mission summary](../screenshots/mission-control-100-percent.png) · [Five-tool execution](../screenshots/five-tool-agent-execution.png) |
| Mission selected five evidence tools | [Agent execution table](../screenshots/five-tool-agent-execution.png) · [ADK trace](../screenshots/adk-mission-trace.png) |
| Forecast: **Increasing; MAE 12,293; RMSE 15,358** | [Forecast evidence](../screenshots/forecast-evidence.png) |
| Quota-resilient routing: **10/10 passed** | [Routing summary](../screenshots/resilient-routing-summary.png) · [Routing cases](../screenshots/resilient-routing-cases.png) · [JSON](../../submission/evidence/quota_resilient_routing_evidence.json) |
| Human approval blocks and unlocks report download | [Pending state](../screenshots/report-pending-human-review.png) · [Approved state](../screenshots/report-approved-download.png) |
| Four-page report artifact | [Sample PDF](../../submission/evidence/sample_approved_business_report.pdf) |

## Claim boundary

The 10/10 quota-resilient result evaluates the deterministic contract router
used when the external provider is unavailable. It is not presented as
provider-backed Gemini/ADK routing accuracy. InsightHive does not publish a
headline ten-case provider-routing score because a stable final provider-backed
run was not captured; the real autonomous ADK mission and its five evidence
tools are documented separately above.
