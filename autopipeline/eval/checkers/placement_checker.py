"""Placement checker: ensure coverage and node validity."""

from typing import Dict, Any, List

from autopipeline.eval.error_codes import ErrorCode, failure


class PlacementChecker:
    def __init__(self):
        pass

    def check(self, placement: Dict[str, Any], ir: Dict[str, Any]) -> Dict[str, Any]:
        failures = []
        warnings: List[str] = []
        nodes = placement.get("nodes") or []
        node_ids = {n.get("node_id") for n in nodes if isinstance(n, dict)}
        comp_places = placement.get("component_placements") or []
        ir_comps = ir.get("components", []) or ir.get("entities", []) or []
        ir_comp_ids = {c.get("id") or c.get("name") for c in ir_comps}

        # coverage
        placed_ids = {p.get("component_id") for p in comp_places if isinstance(p, dict)}
        missing = sorted(list(ir_comp_ids - placed_ids))
        if missing:
            failures.append(failure(ErrorCode.E_PLACEMENT_COVERAGE, "placement", "PlacementChecker",
                                    f"Components missing placement: {', '.join(missing)}",
                                    {"missing_components": missing}))

        # node existence
        for p in comp_places:
            cid = p.get("component_id")
            node = p.get("target_node_id")
            if node and node not in node_ids:
                failures.append(failure(ErrorCode.E_PLACEMENT_UNKNOWN_NODE, "placement", "PlacementChecker",
                                        f"Placement target node not defined: {node} for component {cid}",
                                        {"component_id": cid, "target_node_id": node}))

        # link placements validity if present
        ir_links = {l.get("id") for l in ir.get("links", []) if isinstance(l, dict)}
        for lp in placement.get("link_placements", []) or []:
            lid = lp.get("link_id")
            if lid and ir_links and lid not in ir_links:
                failures.append(failure(ErrorCode.E_PLACEMENT_INVALID_LINK, "placement", "PlacementChecker",
                                        f"Link placement references unknown link_id: {lid}",
                                        {"link_id": lid}))
            if lp.get("transport_hint") == "unspecified":
                warnings.append(f"Link {lid} transport_hint unspecified")

        return {
            "pass": len(failures) == 0,
            "failures": failures,
            "warnings": warnings,
            "metrics": {}
        }
