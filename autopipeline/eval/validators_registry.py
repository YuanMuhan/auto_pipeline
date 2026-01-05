"""Central registry to build validator instances shared by runner/evaluator."""

import os
from typing import Dict, Any

from autopipeline.verifier.rules_loader import load_rules_bundle
from autopipeline.verifier.schema_checker import SchemaChecker
from autopipeline.verifier.boundary_checker import BoundaryChecker
from autopipeline.verifier.coverage_checker import CoverageChecker
from autopipeline.verifier.endpoint_checker import EndpointChecker
from autopipeline.verifier.component_catalog_checker import ComponentCatalogChecker
from autopipeline.verifier.ir_interface_checker import IRInterfaceChecker
from autopipeline.verifier.endpoint_matching_checker import EndpointMatchingChecker
from autopipeline.verifier.device_info_catalog_checker import DeviceInfoCatalogChecker
from autopipeline.verifier.generation_checker import GenerationConsistencyChecker
from autopipeline.verifier.cross_artifact_checker import CrossArtifactChecker
from autopipeline.catalog.render import load_endpoint_types, catalog_hashes
from autopipeline.checkers.semantic_proxy_checker import SemanticProxyChecker


def build_validators(base_dir: str, enable_catalog: bool = True, enable_semantic: bool = True) -> Dict[str, Any]:
    """Construct all validators with a shared rules bundle."""
    rules_bundle = load_rules_bundle()
    schema_checker = SchemaChecker(
        ir_required_fields=rules_bundle["ir"]["required_fields"],
        bindings_required_fields=rules_bundle["bindings"]["required_fields"],
        plan_required_fields=["app_name", "description", "version", "problem_type", "components_outline", "links_outline"],
    )
    boundary_checker = BoundaryChecker(
        forbidden_keywords=rules_bundle["ir"]["forbidden_keywords"],
        forbidden_regex=rules_bundle["ir"].get("forbidden_regex", []),
    )
    coverage_checker = CoverageChecker()
    endpoint_checker = EndpointChecker()
    component_catalog_checker = ComponentCatalogChecker(base_dir, strict=False)
    device_info_catalog_checker = DeviceInfoCatalogChecker(base_dir)
    ir_interface_checker = IRInterfaceChecker(component_catalog_checker)
    endpoint_matching_checker = EndpointMatchingChecker(load_endpoint_types(base_dir)["data"])
    cross_artifact_checker = CrossArtifactChecker()
    gen_checker = GenerationConsistencyChecker
    cat_hash = catalog_hashes(base_dir)
    semantic_checker = SemanticProxyChecker(base_dir) if enable_semantic else None

    return {
        "rules_bundle": rules_bundle,
        "schema_checker": schema_checker,
        "boundary_checker": boundary_checker,
        "coverage_checker": coverage_checker,
        "endpoint_checker": endpoint_checker,
        "component_catalog_checker": component_catalog_checker,
        "device_info_catalog_checker": device_info_catalog_checker,
        "ir_interface_checker": ir_interface_checker,
        "endpoint_matching_checker": endpoint_matching_checker,
        "cross_artifact_checker": cross_artifact_checker,
        "generation_checker_cls": gen_checker,
        "catalog_hash": cat_hash,
        "semantic_checker": semantic_checker,
    }
