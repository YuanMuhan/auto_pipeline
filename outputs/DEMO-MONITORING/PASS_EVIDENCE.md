# PASS Evidence

- eval: outputs\DEMO-MONITORING\eval.json
- case: DEMO-MONITORING
- status: PASS

## Checks
- PASS: overall_status (value=PASS)
- PASS: config.provider (value=deepseek)
- PASS: config.model (value=deepseek-chat)
- PASS: config.prompt_tier (value=P0)
- PASS: config.temperature (value=0.0)
- PASS: config.cache_enabled=False (value=False)
- PASS: config.enable_repair=True (value=True)
- PASS: llm.usage_tokens_total==10019 (value=10019)
- PASS: artifact:plan.json (value=outputs\DEMO-MONITORING\plan.json)
- PASS: artifact:ir.yaml (value=outputs\DEMO-MONITORING\ir.yaml)
- PASS: artifact:bindings.yaml (value=outputs\DEMO-MONITORING\bindings.yaml)
- PASS: artifact:eval.json (value=outputs\DEMO-MONITORING\eval.json)
- PASS: artifact:report.md (value=outputs\DEMO-MONITORING\report.md)
- PASS: artifact:run.log (value=outputs\DEMO-MONITORING\run.log)