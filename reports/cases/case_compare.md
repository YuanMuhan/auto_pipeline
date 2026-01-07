# Success vs Failure (core gate)

| item | success | failure |
|---|---|---|
| run_dir | `outputs_temp_fail/DEMO-MONITORING/run=20260107_191352_464575` | `outputs_temp_fail/DEMO-MONITORING/run=20260107_143222_f87890` |
| bundle_dir | `reports/cases/bundles/success` | `reports/cases/bundles/failure` |
| core_status | PASS | FAIL |
| exec_status | PASS | SKIP |
| top_errors | [] | ['E_SCHEMA_BIND'] |
| warnings_count | 28 | 23 |
| tokens_total | 3492 | 3492 |
| calls_total | 2 | 2 |
| total_duration_ms | 8211 | 8497 |
| attempts_total | 6 | 4 |
| artifacts | {'plan': True, 'ir': True, 'bindings': True, 'eval': True} | {'plan': True, 'ir': True, 'bindings': True, 'eval': True} |

## Root Cause
- Failure category: **schema** (top error: E_SCHEMA_BIND)
- Suggested next steps:
  1) 检查 schema 必填字段；2) 评估是否可提供默认值或 normalizer；3) 确认 prompt 是否输出缺失字段。

## Bindings Diff (Success vs Failure)
| path | missing/required | message | success_has |
|---|---|---|---|
|  | ['component_bindings'] | Bindings missing required fields: component_bindings | true |
