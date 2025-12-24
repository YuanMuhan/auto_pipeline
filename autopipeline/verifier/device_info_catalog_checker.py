"""DeviceInfo catalog checker - validates endpoints against endpoint_types catalog"""

from typing import Dict, Any, Tuple, List, Set
import re
from autopipeline.catalog.render import load_endpoint_types


class DeviceInfoCatalogChecker:
    def __init__(self, base_dir: str):
        data = load_endpoint_types(base_dir)
        self.endpoint_types = data["data"].get("endpoint_types", [])
        self.type_map = {et["name"]: et for et in self.endpoint_types}

    def check(self, device_info: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        warnings: List[str] = []
        errors: List[str] = []
        devices = device_info.get("devices", [])
        for dev in devices:
            endpoints = dev.get("interfaces", {}).get("endpoints", [])
            for ep in endpoints:
                etype = ep.get("type") or ep.get("protocol")
                if etype not in self.type_map:
                    errors.append(f"device {dev.get('id')} endpoint {ep.get('id', ep.get('name'))}: unknown type '{etype}'")
                    continue
                spec = self.type_map[etype]
                missing = [f for f in spec.get("required_fields", []) if f not in ep]
                if missing:
                    errors.append(f"device {dev.get('id')} endpoint {ep.get('id', ep.get('name'))}: missing fields {missing}")
                # direction check
                if ep.get("direction") and ep.get("direction") != spec.get("direction"):
                    errors.append(f"device {dev.get('id')} endpoint {ep.get('id')}: direction {ep.get('direction')} != {spec.get('direction')}")
                # secret check
                secret_pattern = re.compile(r"<SECRET_[A-Z0-9_]+>")
                for key, val in ep.items():
                    if isinstance(val, str) and ("token" in key or "secret" in key or "auth" in key):
                        if not secret_pattern.search(val):
                            errors.append(f"device {dev.get('id')} endpoint {ep.get('id')}: field {key} must use <SECRET_...> placeholder")
                    if key in ("address", "service") and "SECRET" in str(val):
                        if not secret_pattern.search(str(val)):
                            errors.append(f"device {dev.get('id')} endpoint {ep.get('id')}: secrets must be <SECRET_...>")
        if errors:
            return False, "; ".join(errors), warnings
        return True, "DeviceInfo endpoints conform to catalog", warnings
