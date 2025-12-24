import os
import yaml
from typing import Dict, Any, List
from autopipeline.llm.hash_utils import stable_hash, text_hash


def _read_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_component_profiles(base_dir: str) -> Dict[str, Any]:
    index_path = os.path.join(base_dir, "catalog", "components", "index.yaml")
    index = _read_yaml(index_path)
    profiles = {}
    for item in index.get("components", []):
        path = os.path.join(base_dir, item["path"])
        profiles[item["type_name"]] = _read_yaml(path)
    return {"index": index, "profiles": profiles, "index_path": index_path}


def load_endpoint_types(base_dir: str) -> Dict[str, Any]:
    path = os.path.join(base_dir, "catalog", "endpoint_types.yaml")
    data = _read_yaml(path)
    return {"data": data, "path": path}


def component_types_summary(profiles: Dict[str, Any], limit: int = 10) -> str:
    lines: List[str] = []
    items = list(profiles.items())[:limit]
    for name, prof in items:
        kind = prof.get("kind", "")
        provided = prof.get("provided", {})
        ev = provided.get("events", [])
        svc = provided.get("services", [])
        lines.append(f"- {name} ({kind}) ev:{len(ev)} svc:{len(svc)}")
    if len(profiles) > limit:
        lines.append(f"... ({len(profiles)-limit} more)")
    return "\n".join(lines)


def endpoint_types_summary(data: Dict[str, Any], limit: int = 5) -> str:
    lines: List[str] = []
    items = data.get("endpoint_types", [])[:limit]
    for et in items:
        lines.append(
            f"- {et.get('name')} dir:{et.get('direction')} required:{','.join(et.get('required_fields', []))}"
        )
    if len(data.get("endpoint_types", [])) > limit:
        lines.append("... more endpoint types defined")
    return "\n".join(lines)


def catalog_hashes(base_dir: str) -> Dict[str, str]:
    comp_index = os.path.join(base_dir, "catalog", "components", "index.yaml")
    endpoint_path = os.path.join(base_dir, "catalog", "endpoint_types.yaml")
    with open(comp_index, "r", encoding="utf-8") as f:
        comp_hash = text_hash(f.read())
    with open(endpoint_path, "r", encoding="utf-8") as f:
        ep_hash = text_hash(f.read())
    return {"components_index_hash": comp_hash, "endpoint_types_hash": ep_hash}
