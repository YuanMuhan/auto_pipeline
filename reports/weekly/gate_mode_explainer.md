# gate_mode 说明（core vs full）

- **core**：面向“可消费的逻辑产物”  
  - 检查项：user_problem_schema, device_info_schema, device_info_catalog, plan_schema, ir_schema, ir_boundary, ir_component_catalog, ir_interface, placement_schema, placement_checker, bindings_schema, coverage, endpoint_legality, endpoint_matching, cross_artifact_consistency, semantic_proxy(非阻断)  
  - 作用：确保 Plan→IR→Placement→Bindings 结构完备、引用闭合、规则/禁用词/接口合法；不包含 codegen/compose。

- **full**：core + 执行层校验  
  - 额外检查：code_generated、deploy_generated、generation_consistency、runtime_compose（以及 py_compile/compose_exists 等）。
  - 作用：用于端到端可执行验证；core 通过后才建议看 full。

- 设计原因：避免执行层失败（manifest/compose 缺失）污染分解阶段成功率，便于分析 IR/Bindings 质量；论文/周报默认用 core 口径，端到端实验再看 full。
