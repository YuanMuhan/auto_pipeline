# Bindings Repair Before/After (run=20260107_143222_f87890)

- run_dir: `outputs_temp_fail\DEMO-MONITORING\run=20260107_143222_f87890`
- replay_dir: `outputs_temp_fail\DEMO-MONITORING\run=20260107_143222_f87890\replay_repair`
- before top_error: E_SCHEMA_BIND
- after top_error: NONE

## Before: schema bind missing fields (Top 5)

| path | missing/required | message |
|---|---|---|
|  | ['component_bindings'] | Bindings missing required fields: component_bindings |

## After: schema bind missing fields (Top 5)

无 E_SCHEMA_BIND 详情


## Repair Trace 摘要

- attempt=None strategy=deterministic_patch patch_actions=5 hints=1 artifact=replay_repair\bindings_patched_attempt1.yaml

## After Error Explanation

- after 已 PASS（无 top_error）

## 生成的文件

- outputs_temp_fail\DEMO-MONITORING\run=20260107_143222_f87890\replay_repair\bindings_patched_attempt1.yaml
- outputs_temp_fail\DEMO-MONITORING\run=20260107_143222_f87890\replay_repair\bindings_norm.yaml
- outputs_temp_fail\DEMO-MONITORING\run=20260107_143222_f87890\replay_repair\eval_repaired.json
- outputs_temp_fail\DEMO-MONITORING\run=20260107_143222_f87890\replay_repair\repair_trace.json