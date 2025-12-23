# 案例命名规范

## 统一命名格式

所有测试案例统一使用 **`DEMO-<NAME>`** 格式：
- 全部大写
- 使用连字符分隔
- 具有描述性的名称

## 已有案例

### DEMO-MONITORING
- **类型**: monitoring
- **描述**: 简单监控系统
- **复杂度**: L1 (基础)
- **架构**: Sensor → Processor → Storage
- **组件数**: 3
- **链接数**: 2
- **用途**: 演示基本的数据采集-处理-存储流程

**运行**:
```bash
python -m autopipeline run --case DEMO-MONITORING
```

### DEMO-SMARTHOME
- **类型**: automation
- **描述**: 智能家居安防自动化系统
- **复杂度**: L3 (复杂)
- **架构**: 多传感器 → 自动化引擎 → 执行器+通知+存储
- **组件数**: 6
- **链接数**: 5
- **设备数**: 6 (door_sensor, motion_sensor, smart_light, edge_gateway, cloud_automation, cloud_storage)
- **端点数**: 10 (包含 ha_entity, mqtt, http, https)
- **特性**:
  - 门磁、人体传感器、智能灯联动
  - 支持在家/离家/安防三种模式
  - 使用 `<SECRET_*>` 占位符保护敏感信息
  - 演示 Home Assistant、MQTT、HTTP、云服务集成

**运行**:
```bash
python -m autopipeline run --case DEMO-SMARTHOME
```

## 建议的扩展案例

以下是建议的未来案例命名和方向：

### DEMO-FACTORY
**工厂自动化**
- 类型: control
- 场景: 生产线监控和控制
- 设备: PLC、传感器、执行器、MES系统
- 复杂度: L2-L3

### DEMO-AGRICULTURE
**农业物联网**
- 类型: monitoring + control
- 场景: 智慧农业（温室、灌溉）
- 设备: 土壤传感器、气象站、水泵控制
- 复杂度: L2

### DEMO-TRAFFIC
**智能交通**
- 类型: analytics
- 场景: 城市交通流量监测和信号灯控制
- 设备: 摄像头、雷达、信号灯控制器
- 复杂度: L3

### DEMO-HEALTHCARE
**医疗监护**
- 类型: monitoring + alert
- 场景: 远程病人监护
- 设备: 生命体征传感器、报警系统
- 复杂度: L2

### DEMO-ENERGY
**能源管理**
- 类型: monitoring + optimization
- 场景: 智能楼宇能源优化
- 设备: 电表、HVAC控制器、光伏逆变器
- 复杂度: L3

## 命名规范说明

### ✅ 推荐的命名

- `DEMO-MONITORING` - 清晰表达"监控"用途
- `DEMO-SMARTHOME` - 智能家居（单词组合）
- `DEMO-FACTORY` - 简短明了
- `DEMO-TRAFFIC-CONTROL` - 多词用连字符

### ❌ 不推荐的命名

- `demo001` - 小写，无描述性
- `Demo_Monitoring` - 混合大小写，使用下划线
- `DEMO-test-case-1` - 过于冗长
- `mycase` - 缺少前缀

## 创建新案例的步骤

1. **选择命名**: 使用 `DEMO-<NAME>` 格式
2. **创建目录**: `mkdir cases/DEMO-<NAME>`
3. **创建输入文件**:
   - `cases/DEMO-<NAME>/user_problem.json`
   - `cases/DEMO-<NAME>/device_info.json`
   - `cases/DEMO-<NAME>/README.md` (可选，但推荐)
4. **运行测试**: `python -m autopipeline run --case DEMO-<NAME>`
5. **检查输出**: `ls outputs/DEMO-<NAME>/`

## 案例复杂度分级

- **L1 (基础)**: 3-4个组件，简单链式架构
- **L2 (中等)**: 4-6个组件，有分支或汇聚
- **L3 (复杂)**: 6+个组件，多模式/多路径

## 输出产物位置

所有案例的输出都在 `outputs/<CASE_ID>/` 目录：

```
outputs/
├── DEMO-MONITORING/
│   ├── plan.json
│   ├── bindings.yaml
│   ├── generated_code/
│   ├── docker-compose.yml
│   ├── eval.json
│   └── run.log
└── DEMO-SMARTHOME/
    ├── plan.json
    ├── bindings.yaml
    ├── generated_code/
    ├── docker-compose.yml
    ├── eval.json
    └── run.log
```

---

遵循统一的命名规范有助于：
- 快速识别案例用途
- 保持项目结构清晰
- 便于案例管理和扩展
- 提高可读性和可维护性
