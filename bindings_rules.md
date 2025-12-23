````markdown
# =========================================================
# bindings.yaml 规则说明（适配 Core IR / AppSpec v0）
# =========================================================
# 目标：把 Core IR 里的组件/属性/服务/事件，绑定到具体的通信通道（协议）上。
# - Core IR（IR.yaml 等）负责：app_name / schemas / components / links / policies
# - Bindings（bindings.yaml）只负责：transports / component_bindings（协议细节）
#
# 本文件是“规范说明”，不是具体场景；所有名字均为占位示例。

---

## 0. 顶层结构

```yaml
app_name: "<must_match_core_app_name>"
version: "0.1.0"

transports: []          # 通信通道列表
component_bindings: []  # 每个组件的协议绑定
````

* `app_name`：**必须和 Core IR 中的 `app_name` 完全一致**。
* `version`：bindings 自己的版本号（与 Core IR 的 version 可以不同）。
* `transports`：声明系统中可用的通信通道（MQTT Broker、HTTP 服务端口、485 总线等）。
* `component_bindings`：对 Core IR 里的每一个组件（`components[*].name`）定义它的属性/服务/事件如何走具体协议。

---

## 1. transports：通信通道

### 1.1 通用结构

```yaml
transports:
  - id: str           # 在 bindings 内唯一，用于 component_bindings 引用
    type: str         # "local" | "fieldbus" | "mqtt" | "http_client" | "http_server" | ...
    placement: str    # "cloud" | "edge" | "device"（该通道所在层级）
    config: object    # 协议相关配置，字段依据 type 细化
```

### 1.2 type 取值与 config 约定

#### (1) local

* 语义：同进程内本地调用（函数调用 / 直接 GPIO / SDK）。
* 典型用于：逻辑组件之间的调用、简单驱动在同一容器内。

```yaml
- id: "local_default"
  type: "local"
  placement: "edge"
  config: {}
```

#### (2) fieldbus（现场总线，例如 Modbus）

```yaml
- id: "fieldbus_xxx"
  type: "fieldbus"
  placement: "edge"
  config:
    protocol: "modbus_rtu"    # 或 "modbus_tcp" / "custom"
    port: "/dev/ttyUSB0"      # 或 IP:port 等
    baudrate: 9600
    parity: "N"
    stopbits: 1
    timeout_ms: 500
```

#### (3) mqtt（消息总线）

```yaml
- id: "mqtt_xxx"
  type: "mqtt"
  placement: "edge"           # 举例，可根据实际放 cloud/edge/device
  config:
    broker_url: "mqtt://host:1883"
    client_id_prefix: "app_"
    username_env: "MQTT_USER" # 从环境变量读取
    password_env: "MQTT_PASS"
    qos: 1
    retain_default: false
```

#### (4) http_client（作为客户端调用外部 HTTP / REST）

```yaml
- id: "http_client_xxx"
  type: "http_client"
  placement: "cloud"
  config:
    base_url: "https://api.example.com"
    default_headers:
      User-Agent: "my-app/0.1"
    auth:
      type: "token"          # "token" | "basic" | "none" | "custom"
      token_env: "API_TOKEN" # 对应类型的配置
    timeout_ms: 3000
    retry:
      max_attempts: 3
      backoff_ms: 500
```

#### (5) http_server（作为服务端暴露 HTTP 接口 / 接收 Webhook）

```yaml
- id: "http_server_xxx"
  type: "http_server"
  placement: "edge"
  config:
    listen: "0.0.0.0:8080"
    base_path: "/api"
    # 可扩展 TLS / 认证 / 路由前缀等
```

> 说明：后续如需 BLE / Zigbee / LoRa / NB-IoT 等，可新增自定义 type（如 `"ble"`, `"zigbee"`），并在 `config` 中约定相应字段即可；不改变整体结构。

---

## 2. component_bindings：组件级协议绑定

### 2.1 通用结构

```yaml
component_bindings:
  - component: str     # 来自 Core IR 的 components[*].name
    transport: str     # 上方 transports[*].id
    properties:        # 对应 schema.properties
      <prop_name>:
        read:  <ReadBindingSpec | null>
        write: <WriteBindingSpec | null>
    services:          # 对应 schema.services
      <svc_name>:
        # 对 client 型协议（mqtt/http_client/fieldbus）
        request:  <RequestBindingSpec>
        # 对 server 型协议（http_server 等）
        endpoint: <EndpointBindingSpec>
    events:            # 对应 schema.events
      <evt_name>:
        publish:  <PublishBindingSpec>   # 我方主动发出的事件（往外推）
        callback: <CallbackBindingSpec>  # 我方被动接收的回调（仅对 server 型协议有意义）
```

> 注意：
>
> * 某些字段视协议类型可能为 `null` 或根本不出现（例如 local 类型大部分都不需要）。
> * 同一个组件理论上可以绑定到多个 transport（例如属性走 fieldbus，事件走 mqtt），v0 建议一个组件优先只绑定 1~2 个通道，便于实现。

---

## 3. 各协议下的 Binding 规范

下面是 **抽象规范**，不绑定具体场景名字。

### 3.1 fieldbus 类型的属性绑定

适用于：读/写寄存器、线圈等。

```yaml
properties:
  <prop_name>:
    read:
      function_code: int        # 如 3=读保持寄存器，4=读输入寄存器等
      address: int              # 起始地址
      length: int               # 寄存器数量
      scale: float              # 原始值 * scale = 业务值
      poll_interval_ms: int     # 轮询周期（仅对 read 有意义）
    write:
      function_code: int        # 如 6=写单寄存器
      address: int
      length: int | null        # 若写单寄存器，可省略或置 null
      scale: float | null       # 业务值 / scale = 写入的原始值
```

* 对 `services` / `events`，通常 fieldbus 不直接承载（由本地逻辑组件封装成属性读写即可），v0 可以不做 detail 约束。

---

### 3.2 mqtt 类型的属性 / 服务 / 事件绑定

#### 属性（properties）

```yaml
properties:
  <prop_name>:
    read:
      topic: str
      qos: int
    write:
      topic: str
      qos: int
      payload_template: object  # 发送 payload 的结构，其中 "$value" 表示当前写入值
```

例：写属性时生成 payload：

```yaml
payload_template:
  action: "set_<prop_name>"
  value: "$value"
```

#### 服务（services）

```yaml
services:
  <svc_name>:
    request:
      topic: str
      qos: int
      payload_template: object  # 使用 "$args.xxx" 引用 service 入参
```

例：

```yaml
payload_template:
  action: "<svc_name>"
  args: "$args"    # or 分字段 "$args.some_param"
```

#### 事件（events）

```yaml
events:
  <evt_name>:
    publish:
      topic: str
      qos: int
      payload_template: object  # 使用 "$event.xxx" 引用事件 data
```

例：

```yaml
payload_template:
  type: "<evt_name>"
  data: "$event"
```

---

### 3.3 http_client 类型的服务 / 事件绑定

#### 服务（services，作为客户端调用）

```yaml
services:
  <svc_name>:
    request:
      method: "GET" | "POST" | "PUT" | "DELETE" | ...
      path: str                 # 相对 config.base_url 的 path，可含占位符
      query: object             # 映射查询参数，支持 "$args.xxx"
      headers: object           # 额外头部，支持 "$args.xxx"
      body_template: object     # 请求体模板，支持 "$args.xxx"
```

例如：

```yaml
body_template:
  title: "$args.title"
  message: "$args.message"
  level: "$args.level"
```

#### 事件（events，作为客户端向外部上报）

```yaml
events:
  <evt_name>:
    publish:
      method: "POST"
      path: str
      query: object
      headers: object
      body_template: object     # 使用 "$event.xxx" 映射事件 data
```

---

### 3.4 http_server 类型的服务 / 事件绑定

#### 服务（services，作为 HTTP Server 接收请求 → 调用本地 service）

```yaml
services:
  <svc_name>:
    endpoint:
      method: "GET" | "POST" | ...
      path: str                 # 如 "/resource/{id}/action"
      auth: str | object        # 认证方式描述（如 "none" / "token_optional" 等）
      body_mapping: object      # HTTP 入参如何映射到 service input
```

* `body_mapping` 中可使用：

  * `$path.xxx`：URL 路径中的变量；
  * `$query.xxx`：查询参数；
  * `$body.xxx`：请求体字段。

示意：

```yaml
body_mapping:
  some_arg: "$body.some_arg"
  res_id:   "$path.id"
```

#### 事件（events，作为 HTTP Server 主动回调外部 Webhook）

```yaml
events:
  <evt_name>:
    callback:
      method: "POST"
      path: str                 # 回调路径
      headers: object
      body_template: object     # 使用 "$event.xxx" 映射事件 data
```

---

### 3.5 local 类型的绑定

* local 类型通常表示“无网络协议，代码内部直接调用”。
* 大多数情况下可以选择**不配置 properties/services/events**，由 runtime 解释为“本地调用”。

```yaml
properties: {}
services: {}
events: {}
```

---

## 4. 约束与行为约定

1. **与 Core IR 的一致性**

   * `bindings.app_name` 必须等于 Core IR 中的 `app_name`。
   * `component_bindings[*].component` 必须出现在 Core IR 的 `components[*].name` 中。
   * 允许部分组件不在 `component_bindings` 中出现，此时 runtime 可按规则默认使用 `local`（或报错，视实现策略），但**不得默认为 MQTT 等网络协议**。

2. **职责分离**

   * bindings.yaml 中不允许出现 `schemas / components / links / policies` 的定义——这些全部来自 Core IR 文件。
   * bindings 只描述“如何通信”，不重复业务逻辑。

3. **代码生成行为（强约束）**

   * 代码生成时，**仅根据 bindings 决定用哪种协议**；不得在“没有任何 bindings”的前提下自动选择 MQTT/HTTP 等默认协议。
   * 发现绑定缺失时，应显式返回错误或提示“协议未指定”，要求用户补充 bindings，而不是“猜一个”。

4. **多通道绑定**

   * 理论上同一组件可以出现在多个 `component_bindings` 条目中（例如属性走 fieldbus，事件走 mqtt），此时 runtime 需要支持合并。
   * 为简化实现，v0 推荐策略：

     * 一个组件优先绑定一个主要 transport；
     * 如确需多通道，在文档中明确说明每个通道负责的子集（如“属性走 fieldbus，事件走 mqtt”）。

5. **校验规则清单（实现建议）**

   * 检查 `app_name` 与 Core IR 一致；
   * 检查 `component_bindings[*].component` 均存在于 Core IR；
   * 检查 `properties/services/events` 的名称均来源于对应 `schemas`；
   * 检查 `transport` 引用的 `id` 在 `transports` 中有效；
   * 在缺失绑定时，禁止选择任何网络协议（仅允许 `local` 或报错）。

---

## 5. 附录：最小示例（非规范的一部分）

> 仅作为阅读辅助示例，实际门禁/场景不在此描述。

```yaml
app_name: "demo_app"
version: "0.1.0"

transports:
  - id: "edge_mqtt"
    type: "mqtt"
    placement: "edge"
    config:
      broker_url: "mqtt://edge-broker:1883"
      client_id_prefix: "demo_"
      username_env: "MQTT_USER"
      password_env: "MQTT_PASS"
      qos: 1
      retain_default: false

  - id: "edge_fieldbus"
    type: "fieldbus"
    placement: "edge"
    config:
      protocol: "modbus_rtu"
      port: "/dev/ttyUSB0"
      baudrate: 9600
      parity: "N"
      stopbits: 1
      timeout_ms: 500

  - id: "cloud_http"
    type: "http_client"
    placement: "cloud"
    config:
      base_url: "https://api.example.com"
      default_headers: {}
      auth:
        type: "token"
        token_env: "API_TOKEN"
      timeout_ms: 3000
      retry:
        max_attempts: 3
        backoff_ms: 500

component_bindings:
  # 组件 sensor_1 的“多通道绑定”示例：属性走 fieldbus，事件走 mqtt
  - component: "sensor_1"
    transport: "edge_fieldbus"
    properties:
      value:
        read:
          function_code: 4
          address: 0
          length: 1
          scale: 1.0
          poll_interval_ms: 500
        write: null
    services: {}
    events: {}

  - component: "sensor_1"
    transport: "edge_mqtt"
    properties: {}
    services: {}
    events:
      alarm:
        publish:
          topic: "demo/sensor_1/alarm"
          qos: 1
          payload_template:
            type: "alarm"
            data: "$event"

  - component: "notifier"
    transport: "cloud_http"
    properties: {}
    services:
      send_notification:
        request:
          method: "POST"
          path: "/notify"
          query: {}
          headers: {}
          body_template:
            message: "$args.message"
            level: "$args.level"
    events: {}
```

> 你在真实项目中只需要遵守上面的“结构 + 字段约定”，然后针对每个应用写自己的 bindings.yaml 即可。

```
```
