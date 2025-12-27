"""Profile loader for component catalog"""

import os
import yaml
from typing import Dict, Any, Set, Tuple


class ProfileLoader:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        index_path = os.path.join(base_dir, "catalog", "components", "index.yaml")
        with open(index_path, "r", encoding="utf-8") as f:
            index = yaml.safe_load(f)
        self.profiles: Dict[str, Dict[str, Any]] = {}
        for item in index.get("components", []):
            path = os.path.join(base_dir, item["path"])
            with open(path, "r", encoding="utf-8") as pf:
                self.profiles[item["type_name"]] = yaml.safe_load(pf)

    def list_types(self) -> Set[str]:
        return set(self.profiles.keys())

    def get_profile(self, type_name: str) -> Dict[str, Any]:
        if type_name not in self.profiles:
            raise KeyError(f"Component type '{type_name}' not found in catalog")
        return self.profiles[type_name]

    def get_interfaces(self, type_name: str) -> Dict[str, Set[str]]:
        prof = self.get_profile(type_name)
        provided = prof.get("provided", {})
        required = prof.get("required", {})
        if isinstance(required, list):
            required = {"events": [], "properties": [], "services": []}
        def collect(section):
            items = section if isinstance(section, list) else []
            names = set()
            for item in items:
                if isinstance(item, dict) and "name" in item:
                    names.add(item["name"])
                elif isinstance(item, str):
                    names.add(item)
            return names
        provided_events = collect(provided.get("events", []))
        provided_props = collect(provided.get("properties", []))
        provided_services = collect(provided.get("services", []))
        required_events = collect(required.get("events", []))
        required_props = collect(required.get("properties", []))
        required_services = collect(required.get("services", []))
        return {
            "provided_events": provided_events,
            "provided_properties": provided_props,
            "provided_services": provided_services,
            "required_events": required_events,
            "required_properties": required_props,
            "required_services": required_services,
            "all_interfaces": provided_events | provided_props | provided_services | required_events | required_props | required_services,
        }
