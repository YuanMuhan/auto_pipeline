# Preflight Recommendations

- gate_mode 默认 core，端到端/full 场景再打开 exec 检查；文档中注明 core 对应 Plan→IR→Bindings，full 额外包含生成/一致性/runtime。
- boundary：保持 regex=ERROR、关键词=WARNING 的策略；如需再收紧仅匹配 URL/IP/密钥形态，避免描述词误杀。
- catalog：默认开放（unknown type 记 warning + metrics），需要严格时使用 catalog_strict；在 strict 下预期出现 E_CATALOG_COMPONENT（如 ablation 所示）。
- endpoint scope：继续仅对被引用端点做 ERROR 校验；可考虑后续 stub/占位策略，但需新增 W_ENDPOINT_STUB_* 而非降级严重错误。
- 证据生成：运行 `python -m tools.preflight.run_gold --gate_mode core` 与 `python -m tools.preflight.run_ablation --base_dir outputs_preflight_synth --modes gate_core,gate_full,catalog_open,catalog_strict` 作为回归；gold 现已 6/6 PASS，ablation 显示 strict/boundary/endpoint 差异。
