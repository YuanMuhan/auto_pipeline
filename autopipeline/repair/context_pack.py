"""Build repair context for bindings based on raw/norm artifacts and failures."""

from typing import Dict, Any, List
from pathlib import Path
import yaml
import json


def build_bindings_repair_context(run_dir: str, failures: List[Dict[str, Any]]) -> Dict[str, Any]:
    run_path = Path(run_dir)
    ctx: Dict[str, Any] = {
        "previous_bindings_text": "",
        "failure_hints": [],
        "skeleton": {},
        "ir": {},
        "device_info": {},
    }
    # Load previous bindings text if exists
    for name in ["bindings.yaml", "bindings_norm.yaml", "bindings_raw.yaml", "bindings_raw.txt"]:
        p = run_path / name
        if p.exists():
            try:
                ctx["previous_bindings_text"] = p.read_text(encoding="utf-8")[:8000]
                break
            except Exception:
                continue
    # Load ir/device_info if present
    ir_path = run_path / "ir.yaml"
    if ir_path.exists():
        try:
            ctx["ir"] = yaml.safe_load(ir_path.read_text(encoding="utf-8")) or {}
        except Exception:
            ctx["ir"] = {}
    di_candidates = [run_path / "inputs" / "device_info.json", run_path / "device_info.json"]
    for p in di_candidates:
        if p.exists():
            try:
                ctx["device_info"] = json.loads(p.read_text(encoding="utf-8"))
                break
            except Exception:
                continue

    hints = []
    for f in failures or []:
        code = f.get("code")
        if code != "E_SCHEMA_BIND":
            continue
        details = f.get("details", {}) or {}
        hint = {
            "code": code,
            "checker": f.get("checker"),
            "path": details.get("path") or details.get("instance_path") or "",
            "missing": details.get("missing") or details.get("required") or "",
            "message": f.get("message", "").split("\n")[0],
        }
        hints.append(hint)
    ctx["failure_hints"] = hints
    # minimal skeleton (core)
    ctx["skeleton"] = {
        "app_name": "<APP_NAME>",
        "version": "<VERSION>",
        "transports": [],
        "component_bindings": [],
    }
    return ctx
