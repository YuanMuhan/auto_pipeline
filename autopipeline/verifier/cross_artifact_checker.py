"""Cross-artifact consistency checker between IR and Bindings."""

from typing import Dict, Any, List
from autopipeline.eval.error_codes import ErrorCode, failure


class CrossArtifactChecker:
    def check(self, ir_data: Dict[str, Any], bindings_data: Dict[str, Any]) -> Dict[str, Any]:
        failures: List[Dict[str, Any]] = []
        warnings: List[str] = []

        # app_name/version match
        if ir_data.get("app_name") and bindings_data.get("app_name") and ir_data.get("app_name") != bindings_data.get("app_name"):
            failures.append(failure(ErrorCode.E_UNKNOWN, "bindings", "CrossArtifactChecker",
                                    f"app_name mismatch IR={ir_data.get('app_name')} Bindings={bindings_data.get('app_name')}",
                                    {"ir_app_name": ir_data.get("app_name"), "bindings_app_name": bindings_data.get("app_name")}).to_dict())
        if ir_data.get("version") and bindings_data.get("version") and ir_data.get("version") != bindings_data.get("version"):
            failures.append(failure(ErrorCode.E_UNKNOWN, "bindings", "CrossArtifactChecker",
                                    f"version mismatch IR={ir_data.get('version')} Bindings={bindings_data.get('version')}",
                                    {"ir_version": ir_data.get("version"), "bindings_version": bindings_data.get("version")}).to_dict())

        # components referenced in bindings exist in IR
        ir_components = {c.get("id") for c in ir_data.get("components", ir_data.get("entities", []))}
        for cb in bindings_data.get("component_bindings", []):
            comp = cb.get("component") or cb.get("component_id")
            if comp and comp not in ir_components:
                failures.append(failure(ErrorCode.E_CATALOG_COMPONENT, "bindings", "CrossArtifactChecker",
                                        f"component_binding references missing component {comp}",
                                        {"component": comp}).to_dict())

        # placements components check
        for pl in bindings_data.get("placements", []):
            comp = pl.get("component_id") or pl.get("entity_id")
            if comp and comp not in ir_components:
                failures.append(failure(ErrorCode.E_CATALOG_COMPONENT, "bindings", "CrossArtifactChecker",
                                        f"placement references missing component {comp}",
                                        {"component": comp}).to_dict())

        # endpoints link_id exist in IR
        ir_links = {l.get("id") for l in ir_data.get("links", [])}
        for ep in bindings_data.get("endpoints", []):
            lid = ep.get("link_id")
            if lid and lid not in ir_links:
                failures.append(failure(ErrorCode.E_COVERAGE, "bindings", "CrossArtifactChecker",
                                        f"endpoint link_id {lid} not found in IR.links",
                                        {"link_id": lid}).to_dict())

        # deployment orchestrator vs compose
        deployment = bindings_data.get("deployment", {})
        orchestrator = deployment.get("orchestrator")
        if orchestrator and orchestrator.lower() not in ("compose", "docker-compose"):
            warnings.append(f"Deployment orchestrator '{orchestrator}' not supported; using compose by default")

        return {
            "pass": len(failures) == 0,
            "failures": failures,
            "warnings": warnings,
            "metrics": {}
        }
