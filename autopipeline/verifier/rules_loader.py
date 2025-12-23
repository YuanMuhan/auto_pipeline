"""Load verifier rules from IR_rules.md and bindings_rules.md"""

from pathlib import Path
import hashlib
import re
from typing import Dict, List


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


def load_ir_rules() -> Dict:
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


def load_bindings_rules() -> Dict:
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
    ir_rules = load_ir_rules()
    bindings_rules = load_bindings_rules()
    return {
        "ir": ir_rules,
        "bindings": bindings_rules
    }
