"""Strategy router for bindings repair."""

from typing import List, Dict, Any


def choose_strategy(failure_hints: List[Dict[str, Any]], prev_parse_ok: bool, attempt_idx: int,
                    last_top_error: str = None, stagnation_count: int = 0) -> Dict[str, str]:
    """
    Return {"strategy": "...", "reason": "..."}.
    Strategies: deterministic, llm_patch, regenerate, stop.
    """
    top_error = failure_hints[0]["code"] if failure_hints else last_top_error
    if not prev_parse_ok:
        return {"strategy": "regenerate", "reason": "parse_failed"}
    if top_error == "E_SCHEMA_BIND":
        if stagnation_count >= 1:
            return {"strategy": "llm_patch", "reason": "schema_bind_stagnation"}
        return {"strategy": "deterministic", "reason": "schema_bind_missing_fields"}
    if attempt_idx > 3:
        return {"strategy": "stop", "reason": "max_attempts"}
    return {"strategy": "regenerate", "reason": "default_regen"}
