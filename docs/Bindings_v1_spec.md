# Bindings v1 规范（最小可消费版本）

## 顶层字段（core）
- `app_name`（必填，缺省时回填 IR/UNKNOWN）
- `version`（必填，缺省时回填 IR/UNKNOWN）
- `transports`（列表，允许为空列表）
- `component_bindings`（列表，允许 stub）

## Stub 规则（core）
- 当绑定无法完整生成时，为 IR 每个 component 生成占位：
  ```yaml
  component_bindings:
    - component: <component_id>
      bindings: []
      is_stub: true
      need_impl: true
  ```
- stub 仅表示“待补齐/待实现”，在 core gate 允许以 warning 通过；full gate 仍需真实绑定。

## 可选字段（core）
- `placements`、`endpoints`、`device_ref` 等均为 optional，可留空或由后续阶段补齐。

## full 口径
- `bindings_schema_full.json`（沿用原严格 schema）：要求 placements/transports/endpoints 等与 device_info 对齐。
- core 口径使用 `bindings_schema_core.json`：只卡最小可消费结构。

## 校验与降级
- gate_mode=core：stub 触发 coverage/endpoint_matching 警告，不阻断。
- gate_mode=full：严格执行 schema/coverage/endpoint_matching。

## 落盘约定
- `bindings_raw.yaml`：原始输出（可不合法）必写。
- `bindings_norm.yaml`：normalizer 归一化后的可消费版本（必写）。
- `bindings.yaml`：通过 schema（core/full）后写出的规范版本。***
