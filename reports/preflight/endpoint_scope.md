# Endpoint Scope Audit

## 现状
- `endpoint_checker.py`：只校验 **bindings 引用的 endpoints**（from_endpoint/to_endpoint）是否出现在 device_info.devices[].interfaces.endpoints[].address；未引用的 endpoints 不检查，不会 FAIL。
- `endpoint_matching_checker.py`：仅遍历 bindings.endpoints 列表；对缺失 ref 报 warning，对不存在的 ref 报 ERROR（E_ENDPOINT_CHECK/E_ENDPOINT_TYPE/E_ENDPOINT_MISSING_FIELDS）。未被绑定引用的 device_info endpoints 不检查。

## 结论
- 当前 scope 已限定在 “被 bindings 引用的端点”，不存在“全量 device_info 端点导致误杀”的问题。
- 无需代码改动；后续若要进一步放宽，可将缺失 payload_schema 等弱化为 WARNING，但本次不变更。

## 建议
- 保持引用端点的严格校验（方向/必填字段），未引用端点保持忽略。
- 在 eval 中继续记录 metrics（referenced/invalid）用于观测问题集中度。***
