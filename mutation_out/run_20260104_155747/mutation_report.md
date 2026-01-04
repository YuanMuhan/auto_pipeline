# Mutation Report

## M01_DROP_IR_TOP_FIELD (HIT)
- desc: Remove components from IR
- expected: check=ir_schema code=None expect_pass=False
- overall: FAIL
- failed_checks: ir_schema;cross_artifact_consistency
- error_code_top1: E_CATALOG_COMPONENT

## M02_BAD_COMPONENT_TYPE (HIT)
- desc: Set component type to non-catalog
- expected: check=ir_component_catalog code=E_CATALOG_COMPONENT expect_pass=False
- overall: FAIL
- failed_checks: ir_component_catalog;ir_interface
- error_code_top1: E_CATALOG_COMPONENT

## M03_ALIAS_TYPE_NORMALIZE (HIT)
- desc: Set component type to processor to trigger alias
- expected: check=None code=None expect_pass=True
- overall: PASS
- failed_checks: 
- error_code_top1: 

## M04_DROP_BINDINGS_REQUIRED (HIT)
- desc: Remove component_bindings from bindings
- expected: check=bindings_schema code=None expect_pass=False
- overall: FAIL
- failed_checks: bindings_schema;generation_consistency
- error_code_top1: E_UNKNOWN

## M05_COVERAGE_MISSING_LINK (MISS)
- desc: Remove a binding endpoint/link
- expected: check=coverage code=None expect_pass=False
- overall: FAIL
- failed_checks: generation_consistency
- error_code_top1: E_UNKNOWN
- overshadowed_by: generation_consistency

## M06_ENDPOINT_ID_NOT_EXIST (HIT)
- desc: Use nonexistent endpoint id
- expected: check=endpoint_matching code=None expect_pass=False
- overall: FAIL
- failed_checks: endpoint_legality;endpoint_matching;generation_consistency
- error_code_top1: E_ENDPOINT_CHECK

## M07_ENDPOINT_WRONG_TYPE (MISS)
- desc: Set endpoint type invalid
- expected: check=endpoint_legality code=None expect_pass=False
- overall: PASS
- failed_checks: 
- error_code_top1: 

## M08_CROSS_ARTIFACT_BAD_REF (HIT)
- desc: Bindings reference missing component
- expected: check=cross_artifact_consistency code=None expect_pass=False
- overall: FAIL
- failed_checks: cross_artifact_consistency;generation_consistency
- error_code_top1: E_UNKNOWN

## M09_BOUNDARY_URL_IN_CONFIG (HIT)
- desc: Add https URL to config
- expected: check=None code=E_BOUNDARY expect_pass=False
- overall: FAIL
- failed_checks: ir_boundary
- error_code_top1: E_BOUNDARY

## M10_REMOVE_COMPOSE_SERVICE (MISS)
- desc: Remove a compose service
- expected: check=deploy_generated code=None expect_pass=False
- overall: PASS
- failed_checks: 
- error_code_top1: 

## M11_BREAK_BINDINGS_HASH (HIT)
- desc: Mutate bindings to break hash
- expected: check=generation_consistency code=None expect_pass=False
- overall: FAIL
- failed_checks: cross_artifact_consistency;generation_consistency
- error_code_top1: E_UNKNOWN

## M12_PLAN_IR_MISMATCH (MISS)
- desc: Drop plan components_outline
- expected: check=plan_schema code=None expect_pass=False
- overall: FAIL
- failed_checks: 
- error_code_top1: E_UNKNOWN
