"""Utilities to decode LLM outputs with raw logging."""

import json
import os
from typing import Any, Tuple, Optional

import yaml

from autopipeline.utils import ensure_dir
from autopipeline.eval.error_codes import ErrorCode


class LLMOutputFormatError(Exception):
    """Raised when LLM output cannot be parsed into expected format."""

    def __init__(self, message: str, stage: str = "", attempt: int = 0, raw_path: Optional[str] = None):
        super().__init__(message)
        self.stage = stage
        self.attempt = attempt
        self.raw_path = raw_path
        self.code = ErrorCode.E_LLM_OUTPUT_FORMAT


def _save_raw(text: str, output_dir: Optional[str], stage: str, attempt: int, as_json: Optional[Any] = None) -> str:
    if not output_dir:
        return ""
    ensure_dir(output_dir)
    raw_path = os.path.join(output_dir, f"{stage}_attempt{attempt}.txt")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(text)
    if as_json is not None:
        json_path = os.path.join(output_dir, f"{stage}_attempt{attempt}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(as_json, jf, ensure_ascii=False, indent=2)
    return raw_path


def decode_payload(text: str, expected: str, stage: str, attempt: int, output_dir: Optional[str] = None) -> Tuple[Any, Optional[str]]:
    """
    Decode LLM payload safely.
    - expected: "yaml", "json", or "text"
    - returns (obj, raw_path)
    """
    raw_path = _save_raw(text, output_dir, stage, attempt)
    try:
        if expected == "json":
            obj = json.loads(text)
        elif expected == "yaml":
            obj = yaml.safe_load(text)
        else:
            obj = text
    except Exception as e:
        raise LLMOutputFormatError(f"{stage} decode failed: {e}", stage=stage, attempt=attempt, raw_path=raw_path)

    # If we decoded into a mapping, also save JSON for quick inspection
    if isinstance(obj, dict):
        _save_raw(text, output_dir, stage, attempt, as_json=obj)

    return obj, raw_path


def populate_ir_defaults(obj: Any, case_id: str = "", plan_data: Optional[Dict[str, Any]] = None,
                         user_problem: Optional[Dict[str, Any]] = None, fallback: Optional[Dict[str, Any]] = None) -> Any:
    """Populate missing top-level IR fields from available context without changing existing values."""
    if not isinstance(obj, dict):
        return obj
    meta = obj.get("metadata", {}) if isinstance(obj.get("metadata", {}), dict) else {}
    def _first(*vals):
        for v in vals:
            if v:
                return v
        return None
    if not obj.get("app_name"):
        obj["app_name"] = _first(
            (plan_data or {}).get("app_name") if isinstance(plan_data, dict) else None,
            meta.get("name"),
            (user_problem or {}).get("title") if isinstance(user_problem, dict) else None,
            case_id,
        )
    if not obj.get("description"):
        obj["description"] = _first(
            (plan_data or {}).get("description") if isinstance(plan_data, dict) else None,
            (user_problem or {}).get("description") if isinstance(user_problem, dict) else None,
            meta.get("description"),
        )
    if not obj.get("version"):
        obj["version"] = _first(
            (plan_data or {}).get("version") if isinstance(plan_data, dict) else None,
            meta.get("version"),
            "1.0",
        )
    if "schemas" not in obj:
        obj["schemas"] = []
    if "policies" not in obj:
        obj["policies"] = []
    return obj


def minimal_ir_check(obj: Any) -> bool:
    """Minimal IR sanity check to avoid passing obviously wrong payload."""
    return isinstance(obj, dict) and any(k in obj for k in ("app_name", "description", "version", "schemas"))


def minimal_bindings_check(obj: Any) -> bool:
    """Minimal bindings sanity check."""
    return isinstance(obj, dict) and ("component_bindings" in obj or "placements" in obj or "transports" in obj)
