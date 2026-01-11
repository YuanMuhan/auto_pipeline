# Evaluation Report - DEMO-SMARTHOME
- Status: PASS
- Static: PASS
- Runtime: SKIP
- Time: 2026-01-11T19:08:45.682258
- Output dir: .\outputs_temp_repair\DEMO-SMARTHOME\run=20260111_190832_1f76fd
- Run id: run=20260111_190832_1f76fd

## Config
- LLM: provider=openai model=gpt-4o-mini temp=0.0
- prompt_tier: P1
- cache_enabled: False
- enable_repair: True

## Metrics
- total_duration_ms: 12869
- total_attempts: 6
- attempts_by_stage: {'inputs': 1, 'plan': 1, 'ir': 1, 'bindings': 1, 'codegen': 1, 'deploy': 1}
- tokens_total: 7008

## Checks (status/message)
- user_problem_schema: PASS (OK)
- device_info_schema: PASS (OK)
- device_info_catalog: PASS (OK)
- plan_schema: PASS (OK)
- ir_schema: PASS (OK)
- ir_boundary: PASS (OK)
- ir_component_catalog: PASS (OK)
- ir_interface: PASS (OK)
- bindings_schema: PASS (OK)
- coverage: PASS (OK)
- endpoint_legality: PASS (OK)
- endpoint_matching: PASS (OK)
- cross_artifact_consistency: PASS (OK)
- semantic_proxy: PASS (OK)
- code_generated: PASS (OK)
- deploy_generated: PASS (OK)
- generation_consistency: PASS (OK)
- runtime_compose: SKIP (OK)

## Semantic Warnings (non-blocking)
- warning_count: 4
  - W_UP_DI_DEVICE_NOT_FOUND: User problem mentions devices not found in device_info details={'up_terms': ['传感器事件实时响应（<500ms），通知推送（<2s）', '传感器事件流：10-50 events/min，状态查询：低频', '智能家居安防自动化系统：门磁和人体传感器联动夜间照明，异常情况实时通知，支持离家模式和安防策略', '离家模式需要认证，敏感数据加密传输', '高可用性，支持传感器故障降级'], 'di_devices': ['cloud_automation_service', 'cloud_storage_service', 'door_sensor_main', 'edge_gateway_ha', 'home assistant 边缘网关', 'motion_sensor_living', 'smart_light_living', '主卧门磁传感器', '云端存储服务', '云端自动化服务', '客厅人体传感器', '客厅智能灯'], 'unmatched': ['传感器事件实时响应（<500ms），通知推送（<2s）', '传感器事件流：10-50 events/min，状态查询：低频', '智能家居安防自动化系统：门磁和人体传感器联动夜间照明，异常情况实时通知，支持离家模式和安防策略', '离家模式需要认证，敏感数据加密传输', '高可用性，支持传感器故障降级']}
  - W_DI_UNUSED_ENDPOINTS: Most device_info endpoints are unused in bindings details={'di_endpoints': 6, 'used_endpoints': 0, 'ratio': 0.0}
  - W_PLAN_IR_MISMATCH: Plan and IR components diverge details={'plan_refs': ['automation_engine', 'data_recorder', 'door_monitor', 'lighting_controller', 'motion_detector', 'notification_service'], 'ir_components': ['door_sensor_main', 'motion_sensor_living', 'smart_light_living', 'edge_gateway_ha', 'cloud_automation_service', 'cloud_storage_service'], 'missing_in_ir': ['automation_engine', 'data_recorder', 'door_monitor', 'lighting_controller', 'motion_detector', 'notification_service'], 'unused_in_plan': ['cloud_automation_service', 'cloud_storage_service', 'door_sensor_main', 'edge_gateway_ha', 'motion_sensor_living', 'smart_light_living']}
  - W_MULTI_LAYER_WEAK: Hints suggest multi-layer but artifacts show single/unknown layer details={'hint_sources': ['di'], 'observed_layers': []}

## Files
- eval.json: outputs_temp_repair\DEMO-SMARTHOME\run=20260111_190832_1f76fd\eval.json
- run.log: outputs_temp_repair\DEMO-SMARTHOME\run=20260111_190832_1f76fd\run.log