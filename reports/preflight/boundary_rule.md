# Boundary Rule Audit

## 现状（改前）
- BoundaryChecker 对 forbidden_keywords 使用全字匹配，一旦命中即 ERROR。
- forbidden_regex 命中也 ERROR。
- 可能误杀：IR 中概念性词（mqtt/http/url/ip）即便没有具体实现细节也会被判 FAIL。

## 调整（已提交）
- forbidden_keywords 命中仅记为 WARNING（Concept keyword ...）。
- 仅 forbidden_regex 命中仍为 ERROR，保留对具体实现形态（如 URL、IP、token 形态）的硬约束。
- metrics 维持不变；warnings 将随 validators.semantic_proxy 等一同落盘。

## 预期影响
- 减少因抽象描述被边界检查卡死的误杀；真正包含 URL/IP/token 的内容仍会 FAIL。
- 观察点：E_BOUNDARY 频次应下降，warning 增加；后续若仍有误杀，可进一步收紧 regex 仅匹配具体形态。***
