"""Load verifier rules from rules_bundle.yaml (preferred) or legacy md files."""

from pathlib import Path
import hashlib
import re
import yaml
from typing import Dict, List, Tuple


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _read_rules_file(filename: str) -> (Path, str):
    path = _project_root() / filename
    text = path.read_text(encoding='utf-8', errors='ignore')
    return path, text


def _extract_tokens(text: str, candidates: List[str]) -> List[str]:
    lower_text = text.lower()
    found = []
    for token in candidates:
        pattern = r'\b' + re.escape(token.lower()) + r'\b'
        if re.search(pattern, lower_text):
            found.append(token)
    return found


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _load_yaml_bundle() -> Tuple[Dict, str]:
    path = _project_root() / "rules" / "rules_bundle.yaml"
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    data = yaml.safe_load(text) or {}
    return data, text


def load_ir_rules_from_md() -> Dict:
    path, text = _read_rules_file("IR_rules.md")
    required_candidates = [
        "app_name", "description", "version",
        "schemas", "components", "links", "policies"
    ]
    forbidden_candidates = [
        "entity_id", "topic", "url", "port", "mqtt", "http", "https",
        "docker", "k8s", "kubernetes", "container", "host", "ip",
        "address", "endpoint", "socket", "tcp", "udp", "grpc",
        "rest", "api", "broker", "registry", "deployment"
    ]
    return {
        "path": str(path),
        "hash": _hash_text(text),
        "required_fields": _extract_tokens(text, required_candidates),
        "forbidden_keywords": _extract_tokens(text, forbidden_candidates),
        "raw": text,
    }


def load_bindings_rules_from_md() -> Dict:
    path, text = _read_rules_file("bindings_rules.md")
    required_candidates = [
        "app_name", "version", "transports", "component_bindings"
    ]
    forbidden_candidates = [
        "schemas", "components", "links", "policies"
    ]
    return {
        "path": str(path),
        "hash": _hash_text(text),
        "required_fields": _extract_tokens(text, required_candidates),
        "forbidden_keywords": _extract_tokens(text, forbidden_candidates),
        "raw": text,
    }


def load_rules_bundle() -> Dict:
    yaml_data, yaml_text = _load_yaml_bundle()
    source = "yaml" if yaml_data else "md_fallback"
    if yaml_data:
        ir_rules = yaml_data.get("ir", {})
        bindings_rules = yaml_data.get("bindings", {})
        ir_rules = {
            "path": str((_project_root() / "rules" / "rules_bundle.yaml")),
            "hash": _hash_text(yaml_text),
            "required_fields": ir_rules.get("required_fields", []),
            "forbidden_keywords": ir_rules.get("forbidden_keywords", []),
            "forbidden_regex": ir_rules.get("forbidden_regex", []),
            "raw": yaml_text,
        }
        bindings_rules = {
            "path": str((_project_root() / "rules" / "rules_bundle.yaml")),
            "hash": _hash_text(yaml_text),
            "required_fields": bindings_rules.get("required_fields", []),
            "forbidden_keywords": bindings_rules.get("forbidden_keywords", []),
            "forbidden_regex": bindings_rules.get("forbidden_regex", []),
            "raw": yaml_text,
        }
    else:
        ir_rules = load_ir_rules_from_md()
        bindings_rules = load_bindings_rules_from_md()
        # ensure keys exist for compatibility
        ir_rules.setdefault("forbidden_regex", [])
        bindings_rules.setdefault("forbidden_regex", [])
    bundle_hash = hashlib.sha256((ir_rules.get("hash", "") + bindings_rules.get("hash", "")).encode("utf-8")).hexdigest()
    return {
        "ir": ir_rules,
        "bindings": bindings_rules,
        "source": source,
        "hash": bundle_hash,
    }
