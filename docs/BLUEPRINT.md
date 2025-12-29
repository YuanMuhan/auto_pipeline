# BLUEPRINT（文字版存档）

本文件是当前 AutoPipeline 的蓝图化文字说明，用于对齐命名与阶段职责，不改变现有 pipeline 逻辑。

## Task Decomposition
- **Plan（plan.json）**：Planner Agent 产物，任务分解与逻辑轮廓（不含实现细节）。
- **IR（ir.yaml）**：IR Agent 产物，逻辑中间表示；遵循 IR rules + Component Catalog。
- **Placement Plan（placement_plan.json，planned/optional）**：用于后续扩展的部署/分层规划，当前阶段尚未落地，仅预留命名。
- **Bindings（bindings.yaml）**：Bindings Agent 产物，将 IR 映射到物理端点/协议；遵循 bindings rules + Endpoint Catalog。

## Code Generation
- **Backend Router**：根据 case/约束选择生成路线。
- **DIY 路线**：直接使用生成的 IR/Bindings 构建 skeleton（main.py）、manifest 与 docker-compose。
- **COTS 路线**：预留给商用组件/平台选择器（Platform Selector / Entity Mapping / Automation/Flow Generator），当前未启用。

## Verifier / Repair 循环
- **Verifier**：在 IR、Placement（预留）、Bindings、Runtime（生成产物）上进行多轮校验（schema、边界、catalog、接口匹配、生成一致性等）。
- **Repair**：当校验失败时，对 IR / Bindings 触发 Repair Agent 循环（最多 N 轮），以 LLM 生成修复稿。
- **Runtime 校验（预留）**：对生成的 compose/config 等做最小 runtime 检查；失败时记为 runtime 级错误。

## 产出
- 固定落盘：plan.json、ir.yaml、bindings.yaml、generated_code/、docker-compose.yml、eval.json、run.log。
- 追溯链：bindings_hash 写入 manifest/main.py/docker-compose；rules/catalog/schema hash 写入 eval.json；LLM 调用统计写入 eval.json。
