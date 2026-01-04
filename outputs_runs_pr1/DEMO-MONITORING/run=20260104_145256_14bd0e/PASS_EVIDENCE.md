# PASS Evidence

- eval: outputs_runs_pr1\DEMO-MONITORING\run=20260104_145256_14bd0e\eval.json
- case: DEMO-MONITORING
- status: PASS
- static: PASS
- runtime: SKIP

## Checks
- PASS: overall_status (value=PASS)
- PASS: overall_static_status (value=PASS)
- PASS: overall_runtime_status (value=SKIP)
- WARN: config.provider (value=mock)
- WARN: config.model (value=None)
- PASS: config.prompt_tier (value=P0)
- PASS: config.temperature (value=0.0)
- PASS: config.cache_enabled=False (value=False)
- PASS: config.enable_repair=True (value=True)
- WARN: llm.usage_tokens_total==10019 (value=0)
- PASS: checks.runtime_compose.status (value=SKIP)
- PASS: artifact:plan.json (value=outputs_runs_pr1\DEMO-MONITORING\run=20260104_145256_14bd0e\plan.json)
- PASS: artifact:ir.yaml (value=outputs_runs_pr1\DEMO-MONITORING\run=20260104_145256_14bd0e\ir.yaml)
- PASS: artifact:bindings.yaml (value=outputs_runs_pr1\DEMO-MONITORING\run=20260104_145256_14bd0e\bindings.yaml)
- PASS: artifact:eval.json (value=outputs_runs_pr1\DEMO-MONITORING\run=20260104_145256_14bd0e\eval.json)
- PASS: artifact:report.md (value=outputs_runs_pr1\DEMO-MONITORING\run=20260104_145256_14bd0e\report.md)
- PASS: artifact:run.log (value=outputs_runs_pr1\DEMO-MONITORING\run=20260104_145256_14bd0e\run.log)