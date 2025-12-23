# DEMO-001 案例说明

## 场景描述

智能家居安防自动化系统，多设备协同场景（L3复杂度）：

- **设备层 (Device)**:
  - 门磁传感器（主卧门）
  - 人体传感器（客厅）
  - 智能灯（客厅）

- **边缘层 (Edge)**:
  - Home Assistant 网关（本地自动化引擎）

- **云层 (Cloud)**:
  - 自动化服务（规则引擎 + 通知）
  - 存储服务（时序数据库）

## 自动化逻辑

### 1. 在家模式 (Home Mode)
- 夜间（22:00-06:00）检测到人体活动 → 自动开灯
- 无人体活动超过5分钟 → 自动关灯

### 2. 离家模式 (Away Mode)
- 任何门磁触发 → 立即推送通知
- 人体传感器触发 → 高优先级警报

### 3. 安防模式 (Security Mode)
- 门磁打开 AND 人体检测 → 触发警报 + 录像
- 连续异常 → 通知紧急联系人

### 4. 容错处理
- 传感器离线检测
- 故障通知
- 降级策略

## 数据流链路

```
门磁传感器 ──┐
            ├──> HA网关 ──> 云自动化服务 ──> 通知推送
人体传感器 ──┤              │
            │              ├──> 云存储服务
            └──> 智能灯 <───┘
```

## Endpoints 映射约束

### Device Layer (3 endpoints)
1. `ha_entity://binary_sensor.bedroom_door_contact` - 门磁状态
2. `ha_entity://binary_sensor.living_room_motion` - 人体传感器
3. `ha_service://light.living_room_main` - 灯光控制

### Edge Layer (3 endpoints)
4. `mqtt://ha_broker/homeassistant/events/#` - MQTT 订阅
5. `mqtt://ha_broker/homeassistant/commands` - MQTT 发布
6. `http://<SECRET_HA_HOST>:8123/api/webhook/<SECRET_WEBHOOK_ID>` - Webhook

### Cloud Layer (4 endpoints)
7. `https://<SECRET_CLOUD_API>/api/v1/events` - 事件接收
8. `https://api.pushover.net/1/messages.json?token=<SECRET_PUSHOVER_TOKEN>` - 通知推送
9. `https://<SECRET_CLOUD_DB>/write?db=smarthome&precision=s` - 数据写入
10. `https://<SECRET_CLOUD_DB>/query?db=smarthome` - 数据查询

注意：实际的 bindings.endpoints 只能从这 10 个地址中选择，不能编造新地址。

## 期望的 IR 约束

IR 中**不应该出现**：
- ❌ 任何具体的 `address`、`url`、`topic`
- ❌ `mqtt`、`http`、`ha_entity`、`ha_service` 等协议细节
- ❌ `port`、`host`、`token`、`webhook_id` 等实现细节

IR 应该只包含**逻辑组件**和**抽象数据流**：
- ✅ `door_monitor` (逻辑组件，类型：data_source)
- ✅ `motion_detector` (逻辑组件，类型：sensor)
- ✅ `automation_engine` (逻辑组件，类型：processor)
- ✅ `link: door_monitor → automation_engine` (抽象数据流)

## 预期输出产物

运行 `python -m autopipeline run --case DEMO-001` 后，应在 `outputs/DEMO-001/` 生成：

### 1. plan.json (IR)
```json
{
  "components": [
    {"id": "door_monitor", "type": "data_source", "capabilities": ["detect_state_change"]},
    {"id": "motion_detector", "type": "sensor", "capabilities": ["detect_motion"]},
    {"id": "lighting_controller", "type": "actuator", "capabilities": ["control_light"]},
    {"id": "automation_engine", "type": "processor", "capabilities": ["rule_eval", "event_routing"]},
    {"id": "notification_service", "type": "notification", "capabilities": ["push_alert"]},
    {"id": "data_recorder", "type": "storage", "capabilities": ["store", "query"]}
  ],
  "links": [
    {"id": "link_door_to_engine", "from": "door_monitor", "to": "automation_engine", "data_type": "state_event"},
    {"id": "link_motion_to_engine", "from": "motion_detector", "to": "automation_engine", "data_type": "motion_event"},
    {"id": "link_engine_to_light", "from": "automation_engine", "to": "lighting_controller", "data_type": "control_command"},
    {"id": "link_engine_to_notify", "from": "automation_engine", "to": "notification_service", "data_type": "alert"},
    {"id": "link_engine_to_storage", "from": "automation_engine", "to": "data_recorder", "data_type": "event_log"}
  ],
  "logic": {...},
  "metadata": {...}
}
```

### 2. bindings.yaml
```yaml
placements:
  - component_id: door_monitor
    layer: device
    device_ref: door_sensor_main
  - component_id: motion_detector
    layer: device
    device_ref: motion_sensor_living
  - component_id: lighting_controller
    layer: device
    device_ref: smart_light_living
  - component_id: automation_engine
    layer: edge
    device_ref: edge_gateway_ha
  - component_id: notification_service
    layer: cloud
    device_ref: cloud_automation_service
  - component_id: data_recorder
    layer: cloud
    device_ref: cloud_storage_service

transports:
  - link_id: link_door_to_engine
    protocol: MQTT
    qos: at_least_once
  - link_id: link_motion_to_engine
    protocol: MQTT
    qos: at_least_once
  - link_id: link_engine_to_light
    protocol: home_assistant_service
    qos: best_effort
  - link_id: link_engine_to_notify
    protocol: HTTP
    qos: at_least_once
  - link_id: link_engine_to_storage
    protocol: HTTP
    qos: best_effort

endpoints:
  - link_id: link_door_to_engine
    from_endpoint: ha_entity://binary_sensor.bedroom_door_contact
    to_endpoint: mqtt://ha_broker/homeassistant/events/#
  - link_id: link_motion_to_engine
    from_endpoint: ha_entity://binary_sensor.living_room_motion
    to_endpoint: mqtt://ha_broker/homeassistant/events/#
  - link_id: link_engine_to_light
    from_endpoint: mqtt://ha_broker/homeassistant/commands
    to_endpoint: ha_service://light.living_room_main
  - link_id: link_engine_to_notify
    from_endpoint: http://<SECRET_HA_HOST>:8123/api/webhook/<SECRET_WEBHOOK_ID>
    to_endpoint: https://api.pushover.net/1/messages.json?token=<SECRET_PUSHOVER_TOKEN>
  - link_id: link_engine_to_storage
    from_endpoint: https://<SECRET_CLOUD_API>/api/v1/events
    to_endpoint: https://<SECRET_CLOUD_DB>/write?db=smarthome&precision=s
```

注意：所有 `from_endpoint` 和 `to_endpoint` 的地址都必须来自 `device_info.json` 中定义的 endpoints。

### 3. generated_code/
- `device/main.py` - 设备层代码骨架（门磁、人体、灯控制）
- `edge/main.py` - 边缘层代码骨架（HA自动化引擎）
- `cloud/main.py` - 云层代码骨架（规则引擎 + 通知 + 存储）

### 4. docker-compose.yml
Docker Compose 配置文件，定义三层服务。

### 5. eval.json
```json
{
  "case_id": "DEMO-001",
  "overall_status": "PASS",
  "checks": {
    "ir_schema": {"status": "PASS"},
    "ir_boundary": {"status": "PASS"},  // 确保IR中无forbidden tokens
    "bindings_schema": {"status": "PASS"},
    "coverage": {"status": "PASS"},  // 所有5条link都被映射
    "endpoint_legality": {"status": "PASS"}  // 所有endpoint都来自device_info
  },
  "metrics": {
    "num_components": 6,
    "num_links": 5,
    "num_placements": 6,
    "num_layers": 3
  }
}
```

### 6. run.log
完整的运行日志，包含所有验证步骤和生成过程。

## 验证要点

1. **IR 边界检查**: IR 中不应包含任何 `ha_entity://`、`mqtt://`、`https://` 等地址
2. **Endpoints 合法性**: bindings 中的所有 endpoint 地址必须在 device_info 的 10 个 endpoints 中
3. **覆盖度检查**: IR 中的 5 条 links 都必须在 bindings.transports 和 bindings.endpoints 中出现
4. **Schema 验证**: 所有输出必须符合各自的 JSON Schema
