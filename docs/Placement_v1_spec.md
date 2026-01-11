# Placement v1 规范（baseline）

目标：为每个 IR 组件分配执行节点（cloud/edge/device），提供可解释的 rationale，并为跨节点链路给出 transport_hint，形成可被 Bindings 消费的中间产物。

## 顶层字段
- `app_name` / `version`
- `nodes`: list
  - `node_id`: 节点标识
  - `class`: cloud | edge | device
  - `capabilities` (可选)
- `component_placements`: list
  - `component_id`
  - `target_node_id`
  - `rationale`（必填，说明分配原因）
  - `constraints_used`（可选）
- `link_placements` (可选)
  - `link_id`
  - `transport_hint`: local/mqtt/http/unspecified
- `warnings` (可选)

## baseline 生成规则（placement_agent.py）
- 节点：从 device_info.devices 提取 (id/layer/capabilities)，不足时补 cloud/edge/device 默认节点。
- 组件归类（基于 type/name 关键词）：
  - sensor/actuator/light/lock -> device
  - gateway/router/broker/edge -> edge
  - cloud/api/service/server/db/inference/analytics -> cloud
  - 其它默认 edge
- 分配：每个 IR component 必须有一条 component_placement；无可用节点时降级到对应 class 的默认节点，并写 rationale。
- 链路 transport_hint：
  - 同节点 -> local
  - device↔edge -> mqtt
  - 其它跨层 -> http
  - 无法判断 -> unspecified + warning

## 校验（core gate）
- `placement_schema`：必有 app_name/version/nodes/component_placements；component_id/target_node_id 必填。
- `placement_checker`：
  - 所有 IR 组件都必须有 placement（E_PLACEMENT_COVERAGE）
  - target_node_id 必须在 nodes 中（E_PLACEMENT_UNKNOWN_NODE）
  - link_placements 若存在，link_id 必须在 IR.links 中（E_PLACEMENT_INVALID_LINK）
  - transport_hint=unspecified -> warning（core）

## 与 Bindings 的关系
- Bindings 正常化时，将根据 placement_plan 回填 component_bindings[*].placement_node_id，供后续消费。

## 产物路径
- 每次 run 固定落盘：`outputs/<case>/run=.../placement_plan.yaml`
