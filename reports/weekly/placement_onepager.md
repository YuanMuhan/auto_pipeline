# Placement baseline 一页（示例：DEMO-MONITORING, provider=mock）

- run_dir: `outputs_temp_place/DEMO-MONITORING/run=20260111_223006_99346c`
- 产物：`placement_plan.yaml`（heuristic，无 LLM），bindings_norm 已回填 placement_node_id

## Nodes
- total: 3
- list: temp_sensor_01 (device), edge_gateway_01 (edge), cloud_server_01 (cloud)

## Component placements（按节点）
- temp_sensor_01: sensor_collector (rationale: TemperatureSensor -> device)
- edge_gateway_01: data_processor, storage_service (rationale: StateTracker/DataStore -> edge)

## Link transport_hint 分布
- http: 1
- local: 1

## Bindings 与 placement 一致性抽样
- sensor_collector -> placement_node_id=temp_sensor_01
- data_processor -> placement_node_id=edge_gateway_01
- storage_service -> placement_node_id=edge_gateway_01 (device_ref=cloud_server_01)

## Metrics
- component_placements: 3 / components: 3（coverage 100%）
- node_distribution: device=1, edge=2, cloud=0（按 target_node_id 计数）
- cross_node_links: 1（http），same_node_links: 1（local）
- transport_hint_distribution: http=1, local=1, unspecified=0

> 备注：当前为启发式 baseline（无算力/延迟优化），主要用于链路打通和可解释占位。 
