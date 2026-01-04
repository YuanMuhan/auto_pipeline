"""Semantic Proxy Checker: non-blocking semantic risk hints (warnings-only)."""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Set
from pathlib import Path
import yaml
import json


@dataclass
class WarningRecord:
    code: str
    stage: str
    checker: str
    message: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _lower_set(values: List[str]) -> Set[str]:
    return set([v.lower() for v in values if isinstance(v, str)])


def _extract_devices(di: Dict[str, Any]) -> Set[str]:
    devs = set()
    for key in ["devices", "entities", "inventory", "device_list"]:
        items = di.get(key) or []
        if isinstance(items, dict):
            items = items.values()
        for item in items:
            if isinstance(item, dict):
                for k in ["id", "name", "device_id"]:
                    if item.get(k):
                        devs.add(str(item[k]).lower())
            elif isinstance(item, str):
                devs.add(item.lower())
    return devs


def _extract_endpoints(di: Dict[str, Any]) -> List[Dict[str, Any]]:
    eps = []
    candidates = di.get("endpoints") or di.get("devices", [])
    if isinstance(candidates, dict):
        candidates = candidates.values()
    for item in candidates:
        if isinstance(item, dict) and item.get("endpoints"):
            endpoints = item.get("endpoints") or []
            for ep in endpoints:
                if isinstance(ep, dict):
                    eps.append(ep)
        elif isinstance(item, dict) and {"id", "type"} & set(item.keys()):
            eps.append(item)
    return eps


def _extract_up_terms(up: Dict[str, Any]) -> Set[str]:
    terms = set()
    for key in ["devices", "entities", "targets", "constraints"]:
        vals = up.get(key) or []
        if isinstance(vals, dict):
            vals = vals.values()
        for v in vals:
            if isinstance(v, dict):
                for k in ["id", "name", "device", "entity"]:
                    if v.get(k):
                        terms.add(str(v[k]).lower())
            elif isinstance(v, str):
                terms.add(v.lower())
    # light fallback from text fields
    for key in ["title", "description", "context"]:
        txt = up.get(key)
        if isinstance(txt, str):
            for token in txt.replace(",", " ").split():
                if len(token) > 3:
                    terms.add(token.lower())
    return terms


def _extract_ir_components(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    comps = ir.get("components") or ir.get("entities") or []
    return comps if isinstance(comps, list) else []


def _component_identifier(comp: Dict[str, Any]) -> str:
    return str(comp.get("id") or comp.get("name") or comp.get("component") or "").lower()


class SemanticProxyChecker:
    """Non-blocking semantic checker; only emits warnings."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir

    def _warn(self, code: str, message: str, details: Dict[str, Any]) -> Dict[str, Any]:
        return WarningRecord(code=code, stage="semantic", checker="SemanticProxyChecker",
                             message=message, details=details).to_dict()

    def check(self, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        warnings: List[Dict[str, Any]] = []
        required_files = ["user_problem", "device_info", "plan", "ir", "bindings"]
        missing = [k for k in required_files if artifacts.get(k) is None]
        if missing:
            warnings.append(self._warn("W_SEMANTIC_INPUT_MISSING",
                                       "Semantic checker skipped missing artifacts",
                                       {"missing": missing}))
            return {"pass": True, "status": "PASS", "warnings": warnings, "failures": []}

        up = artifacts["user_problem"] or {}
        di = artifacts["device_info"] or {}
        plan = artifacts["plan"] or {}
        ir = artifacts["ir"] or {}
        bindings = artifacts["bindings"] or {}
        compose = artifacts.get("compose") or {}
        attempts_by_stage = artifacts.get("attempts_by_stage") or {}

        di_devices = _extract_devices(di)
        di_endpoints = _extract_endpoints(di)
        di_endpoint_ids = _lower_set([ep.get("id") or ep.get("endpoint_id") or "" for ep in di_endpoints])
        up_terms = _extract_up_terms(up)

        # W_UP_DI_DEVICE_NOT_FOUND
        unmatched = sorted(list(up_terms - di_devices))
        if up_terms and unmatched and di_devices:
            warnings.append(self._warn("W_UP_DI_DEVICE_NOT_FOUND",
                                       "User problem mentions devices not found in device_info",
                                       {"up_terms": sorted(list(up_terms)),
                                        "di_devices": sorted(list(di_devices)),
                                        "unmatched": unmatched}))

        # W_DI_UNUSED_ENDPOINTS
        bindings_eps = set()
        for cb in bindings.get("component_bindings", []):
            if isinstance(cb, dict):
                for key in ["endpoint_id", "endpoint"]:
                    if cb.get(key):
                        bindings_eps.add(str(cb[key]).lower())
                for grp in ["events", "services", "properties", "bindings", "actions"]:
                    for item in cb.get(grp, []) or []:
                        if isinstance(item, dict):
                            ep = item.get("endpoint_id") or item.get("endpoint")
                            if ep:
                                bindings_eps.add(str(ep).lower())
        if di_endpoint_ids:
            ratio = len(bindings_eps & di_endpoint_ids) / max(len(di_endpoint_ids), 1)
            if ratio < 0.2:
                warnings.append(self._warn("W_DI_UNUSED_ENDPOINTS",
                                           "Most device_info endpoints are unused in bindings",
                                           {"di_endpoints": len(di_endpoint_ids),
                                            "used_endpoints": len(bindings_eps & di_endpoint_ids),
                                            "ratio": ratio}))

        # W_PLAN_IR_MISMATCH
        plan_refs = set()
        for key in ["components_outline", "components", "steps"]:
            vals = plan.get(key) or []
            for v in vals:
                if isinstance(v, dict):
                    for k in ["id", "name", "component"]:
                        if v.get(k):
                            plan_refs.add(str(v[k]).lower())
                elif isinstance(v, str):
                    plan_refs.add(v.lower())
        ir_components = [_component_identifier(c) for c in _extract_ir_components(ir)]
        missing_in_ir = sorted(list(plan_refs - set(ir_components)))
        unused_in_plan = sorted(list(set(ir_components) - plan_refs))
        if (missing_in_ir or len(unused_in_plan) > len(ir_components) * 0.5) and (plan_refs or ir_components):
            warnings.append(self._warn("W_PLAN_IR_MISMATCH",
                                       "Plan and IR components diverge",
                                       {"plan_refs": sorted(list(plan_refs)),
                                        "ir_components": ir_components,
                                        "missing_in_ir": missing_in_ir,
                                        "unused_in_plan": unused_in_plan}))

        # W_IR_BINDINGS_GAP
        needs_binding = []
        bound_components = set([str(cb.get("component") or cb.get("component_id") or "").lower()
                                for cb in bindings.get("component_bindings", []) if isinstance(cb, dict)])
        for comp in _extract_ir_components(ir):
            ctype = str(comp.get("type") or "").lower()
            cid = _component_identifier(comp)
            if not cid:
                continue
            if any(tag in ctype for tag in ["sensor", "actuator", "gateway", "device", "controller"]):
                if cid not in bound_components:
                    needs_binding.append(cid)
        if needs_binding:
            warnings.append(self._warn("W_IR_BINDINGS_GAP",
                                       "Some IR components likely require bindings but are missing",
                                       {"missing_bindings": needs_binding}))

        # W_ENDPOINT_KIND_SUSPICIOUS (light heuristic)
        for cb in bindings.get("component_bindings", []) or []:
            if not isinstance(cb, dict):
                continue
            ep_id = str(cb.get("endpoint_id") or cb.get("endpoint") or "").lower()
            if not ep_id:
                continue
            ep = next((e for e in di_endpoints if str(e.get("id") or e.get("endpoint_id") or "").lower() == ep_id), None)
            if not ep:
                continue
            direction = str(ep.get("direction") or "").lower()
            ep_type = str(ep.get("type") or ep.get("protocol") or "").lower()
            binding_usage = [k for k in ["events", "services", "properties", "actions"] if cb.get(k)]
            if direction in {"subscribe", "read"} and any(u in ["services", "actions"] for u in binding_usage):
                warnings.append(self._warn("W_ENDPOINT_KIND_SUSPICIOUS",
                                           "Endpoint direction/type seems mismatched with binding usage",
                                           {"endpoint_id": ep_id, "endpoint_type": ep_type,
                                            "direction": direction, "usage": binding_usage}))

        # W_MULTI_LAYER_WEAK
        hint_sources = []
        up_text = " ".join([str(up.get(k, "")) for k in ["title", "description", "context"]])
        if any(tok in up_text.lower() for tok in ["cloud", "edge", "device"]):
            hint_sources.append("up")
        if di_devices and any("cloud" in d or "edge" in d for d in di_devices):
            hint_sources.append("di")
        observed_layers = set()
        for comp in _extract_ir_components(ir):
            layer = comp.get("layer") or comp.get("placement") or comp.get("deploy")
            if layer:
                observed_layers.add(str(layer).lower())
        if len(observed_layers) <= 1 and hint_sources:
            warnings.append(self._warn("W_MULTI_LAYER_WEAK",
                                       "Hints suggest multi-layer but artifacts show single/unknown layer",
                                       {"hint_sources": hint_sources, "observed_layers": list(observed_layers)}))

        # W_UNUSED_COMPONENTS
        link_refs = set()
        for l in ir.get("links", []) or []:
            if isinstance(l, dict):
                for k in ["from", "to", "source", "target"]:
                    v = l.get(k)
                    if isinstance(v, dict):
                        link_refs.add(str(v.get("component") or v.get("id") or v.get("name") or "").lower())
                    elif v:
                        link_refs.add(str(v).lower())
                for k in ["from_component", "to_component"]:
                    if l.get(k):
                        link_refs.add(str(l[k]).lower())
        unused = []
        for comp in _extract_ir_components(ir):
            cid = _component_identifier(comp)
            if not cid:
                continue
            if cid not in link_refs and cid not in bound_components:
                unused.append(cid)
        if unused:
            warnings.append(self._warn("W_UNUSED_COMPONENTS",
                                       "Components appear unused in links/bindings",
                                       {"unused_components": unused}))

        # W_RULES_TOO_STRICT_HINT
        ir_attempts = attempts_by_stage.get("ir")
        bind_attempts = attempts_by_stage.get("bindings")
        if (ir_attempts and ir_attempts > 1) or (bind_attempts and bind_attempts > 1):
            warnings.append(self._warn("W_RULES_TOO_STRICT_HINT",
                                       "Repair attempts >1; constraints/prompt may be too strict or unstable",
                                       {"attempts_by_stage": attempts_by_stage}))

        return {"pass": True, "status": "PASS", "warnings": warnings, "failures": []}
