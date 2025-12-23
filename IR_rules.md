初始版 IR 规则



1. 顶层结构
app_name: str          # 应用名称（唯一标识）
description: str       # 自然语言描述
version: str           # 版本号

schemas: [...]         # 组件类型/模块类型定义（不含任何协议细节）
components: [...]      # 组件实例（纯逻辑实体，不含部署/协议）
links: [...]           # 组件之间的逻辑依赖关系
policies: [...]        # 事件驱动的业务规则（ECA）
- 约束：Core IR 严禁出现协议/网络相关字段（IP、Port、Topic、URL、认证等），所有通信细节必须由 Bindings 文件提供
- app_name/description/version：用于 NL→IR→代码生成/评测关联；version 为必填，保证样本可追踪
- schemas：类型层与实例层分离；通过复用 schema 支持多个组件实例
- components/links/policies：描述逻辑实体与规则，不涉及部署与通信选择



2. schemas：模块类型定义
schemas:
  - name: str
    properties:           # 状态 & 配置（纯业务类型）
      <prop_name>: <type> # type ∈ {int, float, bool, str, bytes, object}
    services:             # 可调用操作（命令/函数）
      <svc_name>:
        input:
          <arg>: <type>
        output:
          <ret>: <type>
    events:               # 对外发布的事件流
      <evt_name>:
        data:
          <field>: <type>
- 约束：properties/services/events 的命名需语义化（如 temperature、unlock、alarm_triggered），不得出现协议字眼（如 mqtt_publish、http_post）
- 解释：是否“远程可读写”由 Bindings 的 properties.read/write 决定，Core IR 不携带远程/设备孪生等语义
- 说明：事件只有数据结构（data），类型标签作为业务字段放在 data 内（如 data.type="alert"），不在 Core IR 顶层出现



3. components：模块实例
components:
  - name: str              # 实例名，如 cam / auth / lock
    type: str              # 对应 schemas 里的 name
    init_args:             # 初始化参数，对应 schema.properties
      <prop_name>: <value> # 可以是常量或表达式（如 "sensor-fridge-001"）
components把类型和实例分开，同一个 DoorLock schema，可以有多把锁；IR 可以对某把锁做特定策略（按组件 name 区分）
约束：Core IR 不包含部署位置；如需 cloud/edge/device 的放置决策，请在 Bindings 或部署说明中维护



4. links：组件之间的连接关系
links:
  - from: str      # 源组件名
    to: str        # 目标组件名
    # mode: str    # 可选：依赖类型（call/event/stream），v0 先不细分
links 是潜在的数据/控制通路，是拓扑信息，类似于图中的线，便于可视化，便于部署时检查哪些组件必须靠近，便于安全约束看到谁能影响谁



5. policies：事件驱动逻辑
policies:
  - name: str
    description: str       # 可选，自然语言解释
    trigger:
      event: str           # 触发事件表达式，如 "auth.evt.knownPerson"
      condition: str|null  # 条件表达式，如 "confidence > 0.9"
    actions:
      - type: call_service
        target: str        # 组件名，如 lock / audit
        service: str       # service 名，如 unlock / recordEvent
        args:              # 实参，可以用表达式引用当前事件上下文
          <arg>: <expr>    # 如 "auth.evt.knownPerson.user_id"
policies是整个系统的业务逻辑层
NL→IR 的核心任务就是从“门开后计时，超时就报警”这种语句里，提取：
  - 触发事件（doorOpened / timeout / alarmCleared）
  - 条件（超过阈值）
  - 动作调用（startBeep / pushMessage / recordEvent / stopBeep）
forbidden_test_keyword  # 用于验证规则驱动的禁用词测试
