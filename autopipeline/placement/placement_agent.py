"""Deterministic placement plan generator (baseline heuristic)."""

from typing import Dict, Any, List
from collections import defaultdict


class PlacementAgent:
    """Generate a minimal placement plan based on IR and device_info."""

    def __init__(self):
        pass

    @staticmethod
    def _node_catalog(device_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes = []
        for dev in device_info.get("devices", []):
            node_id = dev.get("id") or dev.get("name")
            clazz = dev.get("layer") or dev.get("class") or "edge"
            nodes.append({
                "node_id": node_id,
                "class": clazz,
                "capabilities": dev.get("capabilities", []),
            })
        # ensure at least one of each class
        have = {n["class"] for n in nodes}
        for cls in ["device", "edge", "cloud"]:
            if cls not in have:
                nodes.append({"node_id": f"{cls}_default", "class": cls, "capabilities": []})
        return nodes

    @staticmethod
    def _infer_class(comp_type: str, comp_name: str = "") -> str:
        text = (comp_type or comp_name or "").lower()
        if any(k in text for k in ["sensor", "actuator", "device", "thing", "light", "lock"]):
            return "device"
        if any(k in text for k in ["gateway", "router", "bridge", "broker", "edge"]):
            return "edge"
        if any(k in text for k in ["cloud", "api", "service", "server", "db"]):
            return "cloud"
        if any(k in text for k in ["ml", "inference", "analytics", "model", "ai"]):
            return "cloud"
        # default heuristic
        return "edge"

    def generate_placement_plan(self, plan: Dict[str, Any], ir: Dict[str, Any],
                                device_info: Dict[str, Any]) -> Dict[str, Any]:
        nodes = self._node_catalog(device_info)
        nodes_by_class = defaultdict(list)
        for n in nodes:
            nodes_by_class[n["class"]].append(n)

        comp_places = []
        for comp in ir.get("components", []) or []:
            cid = comp.get("id") or comp.get("name") or "unknown_component"
            ctype = comp.get("type") or ""
            target_class = self._infer_class(ctype, comp.get("name", ""))
            target_node = nodes_by_class[target_class][0]["node_id"] if nodes_by_class[target_class] else f"{target_class}_default"
            rationale = f"heuristic: {ctype or 'unknown'} -> {target_class}"
            comp_places.append({
                "component_id": cid,
                "target_node_id": target_node,
                "rationale": rationale,
                "constraints_used": []
            })

        # optional link placements
        link_places = []
        for link in ir.get("links", []) or []:
            lid = link.get("id")
            # default transport hint based on endpoints if possible
            transport_hint = "unspecified"
            src = link.get("from", {})
            tgt = link.get("to", {})
            if isinstance(src, str):
                src = {"component": src}
            if isinstance(tgt, str):
                tgt = {"component": tgt}
            src_comp = src.get("component") or src.get("component_id")
            tgt_comp = tgt.get("component") or tgt.get("component_id")
            src_node = None
            tgt_node = None
            for p in comp_places:
                if p["component_id"] == src_comp:
                    src_node = p["target_node_id"]
                if p["component_id"] == tgt_comp:
                    tgt_node = p["target_node_id"]
            if src_node and tgt_node:
                if src_node == tgt_node:
                    transport_hint = "local"
                else:
                    # cloud/edge/device combos
                    transport_hint = "mqtt" if ("device" in src_node or "device" in tgt_node) else "http"
            link_places.append({
                "link_id": lid or f"link_{len(link_places)}",
                "transport_hint": transport_hint
            })

        placement_plan = {
            "app_name": ir.get("app_name") or plan.get("app_name") or "UNKNOWN_APP",
            "version": ir.get("version") or plan.get("version") or "UNKNOWN_VERSION",
            "nodes": nodes,
            "component_placements": comp_places,
            "link_placements": link_places,
            "warnings": [],
        }
        return placement_plan
