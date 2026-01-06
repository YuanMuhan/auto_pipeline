# Gate Map (Preflight Audit)

## gate_mode 口径
- core：schema_up/di/plan/ir/bind、boundary、catalog(unknown type warning)、ir_interface、coverage、endpoint_legality、endpoint_matching、cross_artifact。
- full = core + code_generated + deploy_generated + generation_consistency + runtime_compose/py_compile/compose_exists（如启用）。

## Static gate汇总入口
- 汇总位置：`autopipeline/runner.py::_run_evaluation`
- `checks` 字段来源：`validator_results` 中的状态。`static_fail` 计算：所有 checks 中除 `runtime_compose` 外，`status=="FAIL"` 即视为静态失败。
- `overall_static_status`：有任意非 runtime_compose 的 FAIL 即 FAIL。
- `overall_runtime_status`：仅 runtime_check=True 且 runtime_compose FAIL 时才 FAIL；默认 SKIP。

## 当前参与 static_fail 的检查器
（按 runner “Simplified checks” 列表）
- user_problem_schema / device_info_schema / device_info_catalog
- plan_schema / ir_schema / ir_boundary / ir_component_catalog / ir_interface
- bindings_schema / coverage / endpoint_legality / endpoint_matching / cross_artifact_consistency
- semantic_proxy（warnings-only，但仍参与 status 记录）
- code_generated（生成文件存在+py_compile）
- deploy_generated（docker-compose.yml 存在）
- generation_consistency（bindings_hash 与 manifest/main.py/compose hash 一致）
- runtime_compose（在静态 fail 计算时被排除）

## Exec/runtime 检查（应不影响 static）
- runtime_compose（仅 runtime_check=True 时执行；默认 SKIP，不计入 static_fail）

## 污染点（static 被 exec 项影响）
- code_generated / deploy_generated / generation_consistency 被纳入 static_fail 计算，属于执行/产物一致性检查，会导致“分解层”被“生成层”失败污染。

## 判定建议
- 引入 gate_mode（core|full）或在 static_fail 计算时排除执行类检查：
  - core_static = schema + boundary + catalog + interface + coverage + endpoint + cross_artifact（可选 semantic_proxy）
  - exec_gate = code_generated / deploy_generated / generation_consistency / runtime_compose
- 默认使用 core_static 计算 overall_static_status，exec_gate 结果单独呈现，避免将 codegen/compose 的问题计入“分解成功率”。***
