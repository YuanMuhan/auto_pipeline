# Preflight Ablation

| mode | total | pass | fail | top_errors | top_checkers |
|---|---|---|---|---|---|
| gate_core | 3 | 0 | 3 | [('E_SCHEMA_UP', 2), ('E_SCHEMA_BIND', 2), ('E_UNKNOWN', 2)] | [('SchemaChecker', 6), ('GenerationConsistencyChecker', 3), ('EndpointMatchingChecker', 2)] |
| gate_full | 3 | 0 | 3 | [('E_SCHEMA_UP', 2), ('E_SCHEMA_BIND', 2), ('E_UNKNOWN', 2)] | [('SchemaChecker', 6), ('GenerationConsistencyChecker', 3), ('EndpointMatchingChecker', 2)] |
| catalog_open | 3 | 0 | 3 | [('E_SCHEMA_UP', 2), ('E_SCHEMA_BIND', 2), ('E_UNKNOWN', 2)] | [('SchemaChecker', 6), ('GenerationConsistencyChecker', 3), ('EndpointMatchingChecker', 2)] |
| catalog_strict | 3 | 0 | 3 | [('E_CATALOG_COMPONENT', 2), ('E_ENDPOINT_MISSING_FIELDS', 1)] | [('SchemaChecker', 6), ('ComponentCatalogChecker', 6), ('GenerationConsistencyChecker', 3)] |

## Details
| case | mode | status | top_error_codes | run_dir |
|---|---|---|---|---|
| synth_boundary_forbidden | gate_core | FAIL | ['E_SCHEMA_UP', 'E_BOUNDARY', 'E_SCHEMA_BIND', 'E_UNKNOWN'] | outputs_preflight_synth\synth_boundary_forbidden\run=synthetic |
| synth_endpoint_missing_fields | gate_core | FAIL | ['E_ENDPOINT_MISSING_FIELDS'] | outputs_preflight_synth\synth_endpoint_missing_fields\run=synthetic |
| synth_unknown_type | gate_core | FAIL | ['E_SCHEMA_UP', 'E_SCHEMA_BIND', 'E_UNKNOWN'] | outputs_preflight_synth\synth_unknown_type\run=synthetic |
| synth_boundary_forbidden | gate_full | FAIL | ['E_SCHEMA_UP', 'E_BOUNDARY', 'E_SCHEMA_BIND', 'E_UNKNOWN'] | outputs_preflight_synth\synth_boundary_forbidden\run=synthetic |
| synth_endpoint_missing_fields | gate_full | FAIL | ['E_ENDPOINT_MISSING_FIELDS'] | outputs_preflight_synth\synth_endpoint_missing_fields\run=synthetic |
| synth_unknown_type | gate_full | FAIL | ['E_SCHEMA_UP', 'E_SCHEMA_BIND', 'E_UNKNOWN'] | outputs_preflight_synth\synth_unknown_type\run=synthetic |
| synth_boundary_forbidden | catalog_open | FAIL | ['E_SCHEMA_UP', 'E_BOUNDARY', 'E_SCHEMA_BIND', 'E_UNKNOWN'] | outputs_preflight_synth\synth_boundary_forbidden\run=synthetic |
| synth_endpoint_missing_fields | catalog_open | FAIL | ['E_ENDPOINT_MISSING_FIELDS'] | outputs_preflight_synth\synth_endpoint_missing_fields\run=synthetic |
| synth_unknown_type | catalog_open | FAIL | ['E_SCHEMA_UP', 'E_SCHEMA_BIND', 'E_UNKNOWN'] | outputs_preflight_synth\synth_unknown_type\run=synthetic |
| synth_boundary_forbidden | catalog_strict | FAIL | ['E_CATALOG_COMPONENT'] | outputs_preflight_synth\synth_boundary_forbidden\run=synthetic |
| synth_endpoint_missing_fields | catalog_strict | FAIL | ['E_ENDPOINT_MISSING_FIELDS'] | outputs_preflight_synth\synth_endpoint_missing_fields\run=synthetic |
| synth_unknown_type | catalog_strict | FAIL | ['E_CATALOG_COMPONENT'] | outputs_preflight_synth\synth_unknown_type\run=synthetic |
