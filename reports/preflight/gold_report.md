# Preflight Gold Tests Report

Total: 6  Passed: 6  Failed: 0

| case | expected_status | actual_status | expected_codes | actual_codes | result | notes |
|---|---|---|---|---|---|---|
| must_fail1_bad_link | FAIL | FAIL | [] | ['E_SCHEMA_UP', 'E_UNKNOWN'] | PASS |  |
| must_fail2_bad_bindings_schema | FAIL | FAIL | [] | ['E_SCHEMA_UP', 'E_SCHEMA_BIND', 'E_COVERAGE', 'E_UNKNOWN'] | PASS |  |
| must_fail3_endpoint_conflict | FAIL | FAIL | [] | ['E_ENDPOINT_MISSING_FIELDS', 'E_SCHEMA_UP', 'E_ENDPOINT_MISSING_FIELDS', 'E_ENDPOINT_MISSING_FIELDS', 'E_UNKNOWN'] | PASS |  |
| must_pass1_unknown_type | PASS | PASS | [] | ['E_UNKNOWN'] | PASS |  |
| must_pass2_unused_endpoint | PASS | PASS | [] | ['E_UNKNOWN'] | PASS |  |
| must_pass3_boundary_concept | PASS | PASS | [] | ['E_UNKNOWN'] | PASS |  |
