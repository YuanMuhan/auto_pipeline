# AutoPipeline - Prompt-only Multi-Agent Pipeline

自动化云-边-端协同零代码开发原型系统（AutoIoT/GPIoT 风格）

## 项目简介

AutoPipeline 是一个研究原型，用于演示 **Prompt-only multi-agent pipeline** 在云-边-端协同开发场景中的应用。系统通过多个专业化 Agent 和严格的边界约束验证器，实现从用户需求到部署配置的完整自动化流程。

### 核心特性

- **完整链路打通**: UserProblem → IR → Bindings → Code → Deploy → Evaluation
- **强约束边界**: IR 层严格禁止实现细节（端口、URL、协议等）
- **自动修复机制**: 验证失败后自动重试（最多3轮）
- **确定性验证**: Schema、边界、覆盖度、端点合法性四重检查
- **文件驱动**: 所有输入输出基于结构化文件

## 目录结构

```
auto_pipeline/
├── autopipeline/                  # 核心代码包
│   ├── agents/                    # 多 Agent 系统
│   │   ├── planner.py            # 任务分解 -> IR
│   │   ├── bindings.py           # IR -> Bindings
│   │   ├── codegen.py            # 代码生成
│   │   ├── deploy.py             # 部署配置生成
│   │   └── repair.py             # 自动修复 Agent
│   ├── verifier/                 # 验证器模块
│   │   ├── schema_checker.py    # JSON Schema 验证
│   │   ├── boundary_checker.py  # IR 边界检查
│   │   ├── coverage_checker.py  # 覆盖度检查
│   │   └── endpoint_checker.py  # 端点合法性检查
│   ├── schemas/                  # Schema 定义
│   │   ├── ir_schema.json       # IR JSON Schema
│   │   └── bindings_schema.json # Bindings JSON Schema
│   ├── runner.py                 # 主流程编排
│   ├── utils.py                  # 工具函数
│   └── __main__.py               # CLI 入口
├── cases/                         # 测试用例目录
│   └── demo001/
│       ├── user_problem.json     # 用户需求描述
│       └── device_info.json      # 设备信息
├── outputs/                       # 产物输出目录（自动生成）
│   └── <CASE_ID>/
│       ├── plan.json             # 生成的 IR
│       ├── bindings.yaml         # 生成的 Bindings
│       ├── generated_code/       # 生成的代码骨架
│       │   ├── cloud/
│       │   ├── edge/
│       │   └── device/
│       ├── docker-compose.yml    # Docker Compose 配置
│       ├── eval.json             # 评估结果
│       └── run.log               # 运行日志
├── requirements.txt              # Python 依赖
└── README.md                     # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行演示案例

**简单监控系统**：
```bash
python -m autopipeline run --case DEMO-MONITORING
```

**智能家居安防系统**（复杂案例）：
```bash
python -m autopipeline run --case DEMO-SMARTHOME
```

### 3. 查看输出

运行完成后，所有产物位于 `outputs/<CASE_ID>/` 目录：

- `plan.json`: 中间表示（IR），描述系统的逻辑实体和数据流
- `bindings.yaml`: 绑定配置，包含部署位置、传输协议、端点映射
- `generated_code/`: 生成的代码骨架（cloud/edge/device 三层）
- `docker-compose.yml`: Docker 部署配置
- `eval.json`: 评估结果（包含所有验证检查的状态）
- `run.log`: 完整运行日志

## 核心概念

### IR (Intermediate Representation)

**中间表示层**，描述系统的逻辑结构，**严格禁止**包含任何实现细节：

```json
{
  "entities": [
    {
      "id": "sensor_collector",
      "type": "data_source",
      "capabilities": ["sense", "collect"]
    }
  ],
  "links": [
    {
      "id": "link_sensor_to_processor",
      "from": "sensor_collector",
      "to": "data_processor",
      "data_type": "sensor_reading"
    }
  ],
  "metadata": {...}
}
```

**禁止出现的关键词**: `entity_id`, `topic`, `url`, `port`, `mqtt`, `http`, `docker`, `endpoint` 等

### Bindings

**绑定层**，负责将 IR 映射到具体的物理部署：

```yaml
placements:
  - entity_id: sensor_collector
    layer: device
    device_ref: temp_sensor_01

transports:
  - link_id: link_sensor_to_processor
    protocol: MQTT
    qos: at_least_once

endpoints:
  - link_id: link_sensor_to_processor
    from_endpoint: device://temp_sensor_01/data
    to_endpoint: edge://gateway_01/input
```

**约束**: `endpoints` 中的地址**必须**来自 `device_info.json` 的 `interfaces.endpoints`，禁止编造。

### 验证流程

系统包含四个确定性验证器：

1. **Schema Checker**: 验证 IR 和 Bindings 是否符合 JSON Schema
2. **Boundary Checker**: 检查 IR 是否违反边界约束（不包含实现细节）
3. **Coverage Checker**: 确保 IR 中所有 `links` 都在 Bindings 中被映射
4. **Endpoint Checker**: 验证 Bindings 中的端点地址都存在于 DeviceInfo

验证失败时，**RepairAgent** 会自动修复（最多3轮重试）。

## 完整工作流程

```
1. Load inputs (user_problem.json + device_info.json)
   ↓
2. Planner Agent → Generate IR
   ↓
3. Verify IR (Schema + Boundary)
   ├─ PASS → Continue
   └─ FAIL → RepairAgent → Retry (最多3次)
   ↓
4. Bindings Agent → Generate Bindings
   ↓
5. Verify Bindings (Schema + Coverage + Endpoint)
   ├─ PASS → Continue
   └─ FAIL → RepairAgent → Retry (最多3次)
   ↓
6. CodeGen → Generate code skeletons
   ↓
7. Deploy → Generate docker-compose.yml
   ↓
8. Evaluation → Run all checks, output eval.json
   ↓
9. Save outputs (plan.json, bindings.yaml, code, logs)
```

## 输出产物说明

### plan.json (IR)

逻辑架构描述，包含：
- `entities`: 系统中的逻辑组件（传感器、处理器、存储等）
- `links`: 组件间的数据流
- `metadata`: 元信息

### bindings.yaml

物理部署映射，包含：
- `placements`: 实体到云/边/端层的分配
- `transports`: 数据流的传输协议（MQTT/HTTP/gRPC）
- `endpoints`: 具体的通信端点地址

### generated_code/

每层生成一个 `main.py`，包含：
- 服务类定义
- 实体能力的 TODO 占位符
- 端点通信函数骨架（带协议提示）
- 主循环逻辑

### docker-compose.yml

Docker Compose 配置文件，为每层创建服务定义（占位符形式）。

### eval.json

评估结果，包含：
- `checks`: 所有验证项的通过/失败状态
- `metrics`: 统计指标（实体数、链接数、层数等）
- `overall_status`: 总体状态 (PASS/FAIL)

## 示例案例说明

### DEMO-MONITORING (简单监控系统)
- **类型**: monitoring
- **架构**: Sensor → Processor → Storage (3层)
- **复杂度**: L1 (基础)
- **用途**: 演示基本的数据采集-处理-存储流程

### DEMO-SMARTHOME (智能家居安防)
- **类型**: automation
- **架构**: 多传感器 → 自动化引擎 → 执行器+通知+存储 (6组件, 5链接)
- **复杂度**: L3 (复杂)
- **设备**: 6个设备，10个预定义 endpoints
- **特性**:
  - 门磁、人体传感器、智能灯联动
  - 支持在家/离家/安防三种模式
  - 使用 `<SECRET_*>` 占位符保护敏感信息
  - 演示 Home Assistant、MQTT、HTTP、云服务集成

## 自定义案例

在 `cases/` 目录下创建新目录（如 `DEMO-MYCASE`，使用大写+连字符格式），提供两个文件：

### user_problem.json

```json
{
  "type": "monitoring",  // 或 "control"
  "description": "你的需求描述",
  "requirements": ["需求1", "需求2"],
  "constraints": {
    "latency": "延迟要求",
    "data_volume": "数据量级"
  }
}
```

### device_info.json

```json
{
  "devices": [
    {
      "id": "device_01",
      "name": "设备名称",
      "layer": "cloud/edge/device",
      "type": "sensor/gateway/server",
      "capabilities": ["能力1", "能力2"],
      "interfaces": {
        "endpoints": [
          {
            "name": "端点名称",
            "address": "layer://device/path",
            "protocol": "MQTT/HTTP",
            "description": "端点描述"
          }
        ]
      },
      "resources": {...}
    }
  ]
}
```

运行：

```bash
python -m autopipeline run --case DEMO-MYCASE
```

**命名规范**：建议使用 `DEMO-<NAME>` 格式（全大写，连字符分隔），例如：
- `DEMO-MONITORING` - 监控系统
- `DEMO-SMARTHOME` - 智能家居
- `DEMO-FACTORY` - 工厂自动化
- `DEMO-AGRICULTURE` - 农业物联网

## 技术栈

- **Python 3.10+**
- **核心依赖**:
  - `pyyaml`: YAML 解析
  - `jsonschema`: JSON Schema 验证
  - `click`: CLI 框架

## 未来扩展点

### 1. LLM 集成
当前版本使用确定性规则模拟 Agent 行为。未来可接入真实 LLM：
- `agents/planner.py`: 将 `_simulate_ir_generation` 替换为 LLM API 调用
- `agents/bindings.py`: 将 `_simulate_bindings_generation` 替换为 LLM API 调用
- `agents/repair.py`: 将 `_simulate_*_repair` 替换为 LLM API 调用

### 2. 更复杂的验证规则
- 资源约束检查（CPU/内存/带宽）
- 安全策略验证
- 性能模拟

### 3. 真实代码生成
当前 CodeGen 只生成骨架和 TODO。可扩展为：
- 完整的业务逻辑实现
- 测试用例生成
- 文档生成

### 4. 运行时支持
- 实际的 Docker 镜像构建
- Kubernetes 部署支持
- 监控和日志收集

### 5. 可视化界面
- IR 和 Bindings 的图形化展示
- 交互式编辑器
- 实时验证反馈

## 常见问题

### Q: 为什么 IR 不能包含端口、URL 等信息？
A: IR 的设计目标是描述**逻辑架构**，与具体实现解耦。这样可以在不修改 IR 的情况下切换底层技术栈（如从 MQTT 切换到 gRPC），提高系统的可维护性和可移植性。

### Q: Bindings 的端点地址格式有什么要求？
A: 端点地址必须在 `device_info.json` 的 `interfaces.endpoints[].address` 中预先定义。系统会验证 Bindings 中引用的地址是否合法，禁止编造地址。

### Q: 验证失败后如何调试？
A: 查看 `outputs/<CASE_ID>/run.log` 获取详细日志，`eval.json` 会列出所有失败的检查项和错误信息。

### Q: 如何添加新的验证规则？
A: 在 `autopipeline/verifier/` 下创建新的 checker 类，在 `runner.py` 的验证流程中调用。

## 许可证

本项目为研究原型，仅供学习和研究使用。

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**Generated by AutoPipeline** - Prompt-only multi-agent pipeline for Cloud-Edge-Device development
