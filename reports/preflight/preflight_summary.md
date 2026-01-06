# Preflight Audit Summary

- gate_mode=core|full 已实现：core 仅统计 schema/boundary/catalog/interface/coverage/endpoint/cross；full 在 core 基础上加 code_generated/deploy_generated/generation_consistency/runtime_compose。eval 输出 overall_core_status/overall_exec_status。
- Catalog 未知类型降级为 warning 并计数，boundary 关键词降级为 warning，regex 命中仍 ERROR；endpoint scope 仅检查 bindings 引用端点。
- gold 测试 6/6 通过（gate_mode=core）；must-pass 样例补齐了 schema/endpoint 必填后可通过，must-fail 保持 FAIL。
- 合成 ablation（outputs_preflight_synth）展示差异：catalog_strict 触发 E_CATALOG_COMPONENT；boundary regex 命中可见 E_BOUNDARY；endpoint 缺必填触发 E_ENDPOINT_MISSING_FIELDS。core/full 口径一致（无 exec 污染）。
- 仍然的主阻断集中在 schema_bind / endpoint_missing_fields / catalog_strict（在 strict 模式下）；generation_consistency 仅在 full 口径时影响 overall_exec_status。
- 后续可选：补充 CHECKERS_MAP/RULEBOOK，将核心 gate 与 exec gate 明确文档化。
