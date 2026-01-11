"""Bindings normalizer - ensures minimal consumable structure and stubs."""

from typing import Dict, Any, List, Tuple
import yaml


def normalize_bindings(bindings_raw: Any, ir: Dict[str, Any], device_info: Dict[str, Any],
                       gate_mode: str = "core", placement: Dict[str, Any] = None) -> Tuple[Dict[str, Any], List[str]]:
    actions: List[str] = []
    # if raw is text, try parse
    if isinstance(bindings_raw, str):
        try:
            bindings = yaml.safe_load(bindings_raw) or {}
            actions.append("parsed_text_to_yaml")
        except Exception:
            # parse failed, return minimal skeleton
            bindings = {}
            actions.append("parse_failed_text")
    else:
        bindings = bindings_raw or {}

    # ensure dict
    if not isinstance(bindings, dict):
        actions.append("bindings_not_dict_reset")
        bindings = {}

    # fill app_name/version from IR
    if not bindings.get("app_name"):
        bindings["app_name"] = ir.get("app_name") or "UNKNOWN_APP"
        actions.append("fill_app_name")
    if not bindings.get("version"):
        bindings["version"] = ir.get("version") or "UNKNOWN_VERSION"
        actions.append("fill_version")

    # normalize transports/endpoints/component_bindings shapes
    for key in ["transports", "endpoints", "placements"]:
        val = bindings.get(key)
        if val is None:
            bindings[key] = []
            actions.append(f"fill_empty_{key}")
        elif isinstance(val, dict):
            bindings[key] = [val]
            actions.append(f"wrap_dict_{key}")
        elif not isinstance(val, list):
            bindings[key] = []
            actions.append(f"reset_invalid_{key}")

    # component_bindings
    cb = bindings.get("component_bindings")
    if cb is None:
        cb = []
        actions.append("fill_empty_component_bindings")
    elif isinstance(cb, dict):
        cb = [cb]
        actions.append("wrap_dict_component_bindings")
    elif not isinstance(cb, list):
        cb = []
        actions.append("reset_invalid_component_bindings")
    bindings["component_bindings"] = cb

    # stub generation if empty
    if not cb:
        components = ir.get("components", ir.get("entities", [])) or []
        stub_list = []
        for comp in components:
            cid = comp.get("id") or comp.get("name") or "unknown_component"
            stub_list.append({
                "component": cid,
                "bindings": [],
                "is_stub": True,
                "need_impl": True,
            })
        bindings["component_bindings"] = stub_list
        actions.append("generate_stub_component_bindings")

    # backfill placement_node_id from placement plan if available
    placement_map = {}
    if placement:
        for cp in placement.get("component_placements", []) or []:
            cid = cp.get("component_id")
            if cid:
                placement_map[cid] = cp.get("target_node_id")
    for entry in bindings["component_bindings"]:
        cid = entry.get("component") or entry.get("component_id")
        if "placement_node_id" not in entry or not entry.get("placement_node_id"):
            if cid in placement_map:
                entry["placement_node_id"] = placement_map[cid]
                actions.append(f"fill_placement_for_{cid}")

    return bindings, actions
