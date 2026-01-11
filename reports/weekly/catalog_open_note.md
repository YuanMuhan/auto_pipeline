# catalog open 模式说明

- 现状：组件 catalog 不再硬失败未知类型，IR/component.type 未命中白名单时仅记录 warning/metrics（unknown_types），core gate 继续通过后续检查。
- 原因：IR 定位为“逻辑层中间产物”，强调流程可行性与规则驱动；避免因封闭库导致静态 PASS=0。
- 风险：未知类型可能隐藏语义歧义；需配合后续 placement/Bindings/semantic proxy 检查，或在需要时用 alias/normalizer 做规范化。
- 口径：core 只告警统计，full/执行层也不因未知类型阻断。若需更严格，可在 catalog_strict 下观察影响（预审计已有 synth gold）。 
