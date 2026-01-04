# Evaluation Report - DEMO-MONITORING
- Status: PASS
- Static: PASS
- Runtime: SKIP
- Time: 2026-01-04T15:14:17.274541
- Output dir: .\outputs_pr2_runs\DEMO-MONITORING\run=20260104_151417_c584d2
- Run id: run=20260104_151417_c584d2

## Config
- LLM: provider=mock model=None temp=0.0
- prompt_tier: P0
- cache_enabled: False
- enable_repair: True

## Metrics
- total_duration_ms: 48
- total_attempts: 6
- attempts_by_stage: {'inputs': 1, 'plan': 1, 'ir': 1, 'bindings': 1, 'codegen': 1, 'deploy': 1}
- tokens_total: 0

## Checks (status/message)
- user_problem_schema: PASS (OK)
- device_info_schema: PASS (OK)
- device_info_catalog: PASS (OK)
- plan_schema: PASS (OK)
- ir_schema: PASS (OK)
- ir_boundary: PASS (OK)
- ir_component_catalog: PASS (OK)
- ir_interface: PASS (OK)
- bindings_schema: PASS (OK)
- coverage: PASS (OK)
- endpoint_legality: PASS (OK)
- endpoint_matching: PASS (OK)
- cross_artifact_consistency: PASS (OK)
- code_generated: PASS (OK)
- deploy_generated: PASS (OK)
- generation_consistency: PASS (OK)
- runtime_compose: SKIP (OK)

## Files
- eval.json: outputs_pr2_runs\DEMO-MONITORING\run=20260104_151417_c584d2\eval.json
- run.log: outputs_pr2_runs\DEMO-MONITORING\run=20260104_151417_c584d2\run.log