"""Utilities to inject deterministic constraints into prompts."""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import yaml

from autopipeline.catalog.catalog_utils import load_catalog_types
from autopipeline.catalog.render import load_endpoint_types
from autopipeline.utils import load_json
from autopipeline.llm.hash_utils import text_hash


def _catalog_types_text(base_dir: Path) -> Tuple[str, str]:
    index_path = base_dir / "catalog" / "components" / "index.yaml"
    types = sorted(load_catalog_types(index_path))
    text = "Allowed component types:\n" + "\n".join([f"- {t}" for t in types])
    return text, text_hash(text)


def _endpoint_types_text(base_dir: Path) -> Tuple[str, str]:
    ep_data = load_endpoint_types(str(base_dir))["data"]
    # ep_data may be dict with names or list under key endpoint_types
    if isinstance(ep_data, dict) and "endpoint_types" in ep_data:
        ep_list = ep_data.get("endpoint_types") or []
    elif isinstance(ep_data, list):
        ep_list = ep_data
    else:
        ep_list = []
    ep_map = {}
    for item in ep_list:
        if isinstance(item, dict) and item.get("name"):
            ep_map[item["name"]] = item
    if not ep_map and isinstance(ep_data, dict):
        ep_map = {k: v for k, v in ep_data.items() if isinstance(v, dict)}
    lines = ["Endpoint types:"]
    for name in sorted(ep_map.keys()):
        item = ep_map[name] or {}
        direction = item.get("direction") or item.get("default_direction")
        req_fields = item.get("required_fields") or []
        lines.append(f"- {name}: direction={direction}, required_fields={sorted(req_fields)}")
    text = "\n".join(lines)
    return text, text_hash(text)


def _rules_text(base_dir: Path, rules_bundle: Dict[str, Any]) -> Tuple[str, str, str]:
    ir_req = sorted(rules_bundle["ir"].get("required_fields", []))
    bind_req = sorted(rules_bundle["bindings"].get("required_fields", []))
    forbid_kw = sorted(rules_bundle["ir"].get("forbidden_keywords", []))
    forbid_rg = sorted(rules_bundle["ir"].get("forbidden_regex", []))
    req_lines = [
        "Rules required fields:",
        "IR:",
        *(f"- {f}" for f in ir_req),
        "Bindings:",
        *(f"- {f}" for f in bind_req),
    ]
    forbid_lines = [
        "Forbidden keywords:",
        *(f"- {f}" for f in forbid_kw),
        "Forbidden regex:",
        *(f"- {f}" for f in forbid_rg),
    ]
    req_text = "\n".join(req_lines)
    forbid_text = "\n".join(forbid_lines)
    return req_text, forbid_text, text_hash(req_text + "\n" + forbid_text)


def _schema_required_text(base_dir: Path) -> Tuple[str, str]:
    schemas = {
        "ir_schema": base_dir / "autopipeline" / "schemas" / "ir_schema.json",
        "bindings_schema": base_dir / "autopipeline" / "schemas" / "bindings_schema.json",
    }
    lines = ["Schema required fields (top-level):"]
    for name, path in schemas.items():
        req = []
        if path.exists():
            try:
                data = load_json(path)
                req = data.get("required", []) or []
            except Exception:
                req = []
        lines.append(f"- {name}: {sorted(req)}")
    text = "\n".join(lines)
    return text, text_hash(text)


def build_prompt_injections(base_dir: Path, rules_bundle: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Return placeholder->text map and hashes for deterministic prompt injections."""
    catalog_text, catalog_hash = _catalog_types_text(base_dir)
    endpoint_text, endpoint_hash = _endpoint_types_text(base_dir)
    rules_req_text, rules_forbid_text, rules_hash = _rules_text(base_dir, rules_bundle)
    schema_text, schema_hash = _schema_required_text(base_dir)
    injections = {
        "CATALOG_TYPES": catalog_text,
        "ENDPOINT_TYPES_SUMMARY": endpoint_text,
        "RULES_REQUIRED_FIELDS": rules_req_text,
        "RULES_FORBIDDEN": rules_forbid_text,
        "SCHEMA_REQUIRED_FIELDS": schema_text,
    }
    hashes = {
        "catalog_types_hash": catalog_hash,
        "endpoint_types_hash": endpoint_hash,
        "rules_bundle_hash": rules_hash,
        "schema_required_hash": schema_hash,
    }
    return injections, hashes
