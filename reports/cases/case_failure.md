# Failure Case (A1, core gate)

- run_dir: `outputs_temp_fail/DEMO-MONITORING/run=20260107_143222_f87890`
- case: DEMO-MONITORING
- provider: openai
- core_status: FAIL  | exec_status: SKIP
- top_errors: ['E_SCHEMA_BIND']
- warnings_count: 23
- tokens_total: 3492
- calls_total: 2
- total_duration_ms: 8497
- attempts_total: 4
- artifacts: {'plan': True, 'ir': True, 'bindings': True, 'eval': True}
- top_error_repro: 1
- summary: Core gate FAIL，top_error=E_SCHEMA_BIND, repro=1
- schema_bind_missing: [{'path': '', 'missing': ['component_bindings'], 'message': 'Bindings missing required fields: component_bindings', 'success_has': 'true'}]
- schema_bind_note: None

## Summary
Core gate FAIL，top_error=E_SCHEMA_BIND, repro=1

## Schema Bind Missing Fields
| path | missing/required | message | success_has |
|---|---|---|---|
|  | ['component_bindings'] | Bindings missing required fields: component_bindings | true |
