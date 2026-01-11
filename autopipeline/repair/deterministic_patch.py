"""Deterministic patch for bindings based on schema hints."""

from copy import deepcopy
from typing import Dict, Any, List, Tuple

from autopipeline.normalize.bindings_normalizer import normalize_bindings


def apply_deterministic_patch(bindings: Dict[str, Any], ir: Dict[str, Any],
                              failure_hints: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Make minimal structural fixes without calling LLM.
    - Ensure transports list exists.
    - Ensure component_bindings exists (stubbed) when missing.
    """
    actions: List[str] = []
    patched = deepcopy(bindings) if bindings is not None else {}
    need_stub = False
    for h in failure_hints or []:
        path = str(h.get("path") or "")
        missing = str(h.get("missing") or h.get("required") or "")
        if "component_bindings" in path or "component_bindings" in missing:
            need_stub = True
        if "transports" in path or "transports" in missing:
            actions.append("ensure_transports_list")

    if not patched.get("transports"):
        patched["transports"] = []
        actions.append("patch_transports_empty")

    if need_stub or not patched.get("component_bindings"):
        actions.append("patch_component_bindings_stub")

    patched_norm, norm_actions = normalize_bindings(patched, ir, {}, gate_mode="core")
    actions.extend(norm_actions)
    return patched_norm, actions


# Backward-compatible alias (runner may import patch_bindings)
def patch_bindings(bindings: Dict[str, Any], ir: Dict[str, Any],
                   failure_hints: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    return apply_deterministic_patch(bindings, ir, failure_hints)
