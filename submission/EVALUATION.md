# Evaluation Methodology

**Team:** Harshit Jetwani (Team Leader & Co-Creator) · Jiya Aalwani (Team Member & Co-Creator)

InsightHive separates deterministic software verification from probabilistic
agent-routing evaluation. This prevents a passing tool test from being
misrepresented as proof that an LLM selected the correct tool.

## Layer 1: software contracts

Fourteen automated tests cover:

- prompt guardrails;
- sample-dataset business signals;
- TF-IDF retrieval and source evidence;
- report JSON contract parsing;
- routing-case registry integrity;
- objective-specific mission completion.

GitHub Actions installs `requirements-dev.txt`, compiles the source, checks
secret/runtime hygiene, and runs:

```bash
python -m pytest -q
```

## Layer 2: deterministic tool execution

`run_evaluation_suite()` invokes fixed tools against the active dataset and
checks required response keys. It answers:

> Does each deterministic capability execute and honor its output contract?

This layer does not claim agent-routing accuracy.

## Layer 3: ADK routing evaluation

`run_agent_routing_evaluation()` sends ten natural-language tasks through the
real ADK root orchestrator. Each case has one expected evidence tool:

1. quality evaluation;
2. summary statistics;
3. anomaly detection;
4. forecasting;
5. live MCP industry playbook;
6. report context;
7. dataset overview;
8. correlation analysis;
9. governed analysis pipeline;
10. HITL publish gate.

The evaluator records selected tools, attempts, pass/fail, per-case latency,
first-attempt accuracy, retry recoveries, and total pass rate. A second attempt
is allowed only with an explicit instruction to use the most appropriate
grounded tool.

## Layer 4: objective completion

Mission Control evaluates evidence required by the user objective. A fluent
answer cannot pass by itself. Depending on the objective and schema, completion
may require:

- verified dataset analysis;
- industry grounding;
- forward-looking forecast;
- report context;
- human approval-gate evidence.

Internal `transfer_to_agent` events remain visible in traces but are excluded
from the business-tool count.

## Full ADK versus resilience mode

Full ADK evidence requires an active Gemini quota and is labelled
**Orchestrator-native**. If external quota is unavailable, InsightHive can run
deterministic analytics and local vector retrieval. The UI labels this
**Deterministic resilience runtime** and never presents local retrieval as a
live MCP call.

## Reporting policy

- Never estimate or fabricate evaluation numbers.
- Record model, date, commit SHA, dataset, and deployment revision.
- Run the final evaluation in the deployed Full ADK environment.
- Download the judge-evidence JSON.
- Preserve failures and retries; do not edit the artifact.
- Report deterministic and agent-routing results separately.

Final deployed metrics belong in [EVIDENCE.md](EVIDENCE.md).
