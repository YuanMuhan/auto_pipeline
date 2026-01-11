# Evaluation Report - DEMO-MONITORING
- Status: PASS
- Static: PASS
- Runtime: SKIP
- Time: 2026-01-11T19:08:23.199383
- Output dir: .\outputs_temp_repair\DEMO-MONITORING\run=20260111_190815_b6071d
- Run id: run=20260111_190815_b6071d

## Config
- LLM: provider=openai model=gpt-4o-mini temp=0.0
- prompt_tier: P0
- cache_enabled: False
- enable_repair: True

## Metrics
- total_duration_ms: 7141
- total_attempts: 6
- attempts_by_stage: {'inputs': 1, 'plan': 1, 'ir': 1, 'bindings': 1, 'codegen': 1, 'deploy': 1}
- tokens_total: 3492

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
  - W_UP_DI_DEVICE_NOT_FOUND: User problem mentions devices not found in device_info details={'up_terms': ['analytics', 'cloud', 'high frequency sensor readings', 'home', 'monitoring', 'real-time for alerts, periodic for storage', 'smart', 'system', 'temperature', 'with'], 'di_devices': ['cloud analytics server', 'cloud_server_01', 'edge gateway', 'edge_gateway_01', 'temp_sensor_01', 'temperature sensor device'], 'unmatched': ['analytics', 'cloud', 'high frequency sensor readings', 'home', 'monitoring', 'real-time for alerts, periodic for storage', 'smart', 'system', 'temperature', 'with']}
  - W_DI_UNUSED_ENDPOINTS: Most device_info endpoints are unused in bindings details={'di_endpoints': 3, 'used_endpoints': 0, 'ratio': 0.0}
  - W_PLAN_IR_MISMATCH: Plan and IR components diverge details={'plan_refs': ['data_processor', 'sensor_collector', 'storage_service'], 'ir_components': ['temp_sensor_01', 'edge_gateway_01', 'cloud_server_01'], 'missing_in_ir': ['data_processor', 'sensor_collector', 'storage_service'], 'unused_in_plan': ['cloud_server_01', 'edge_gateway_01', 'temp_sensor_01']}
  - W_MULTI_LAYER_WEAK: Hints suggest multi-layer but artifacts show single/unknown layer details={'hint_sources': ['up', 'di'], 'observed_layers': []}

## Files
- eval.json: outputs_temp_repair\DEMO-MONITORING\run=20260111_190815_b6071d\eval.json
- run.log: outputs_temp_repair\DEMO-MONITORING\run=20260111_190815_b6071d\run.log