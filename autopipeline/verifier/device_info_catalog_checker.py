"""DeviceInfo catalog checker - validates endpoints against endpoint_types catalog"""

from typing import Dict, Any, List
import re
from autopipeline.catalog.render import load_endpoint_types
from autopipeline.eval.error_codes import ErrorCode, failure


class DeviceInfoCatalogChecker:
    def __init__(self, base_dir: str):
        data = load_endpoint_types(base_dir)
        self.endpoint_types = data["data"].get("endpoint_types", [])
        self.type_map = {et["name"]: et for et in self.endpoint_types}

    def check(self, device_info: Dict[str, Any]):
        warnings: List[str] = []
        failures: List = []
        devices = device_info.get("devices", [])
        for dev in devices:
            endpoints = dev.get("interfaces", {}).get("endpoints", [])
            for ep in endpoints:
                ep_id = ep.get("id", ep.get("name"))
                etype = ep.get("type") or ep.get("protocol")
                if etype not in self.type_map:
                    failures.append(failure(ErrorCode.E_ENDPOINT_TYPE, "inputs", "DeviceInfoCatalogChecker",
                                            f"device {dev.get('id')} endpoint {ep_id}: unknown type '{etype}'",
                                            {"endpoint": ep_id, "type": etype}))
                    continue
                spec = self.type_map[etype]
                missing = [f for f in spec.get("required_fields", []) if f not in ep]
                if missing:
                    failures.append(failure(ErrorCode.E_ENDPOINT_MISSING_FIELDS, "inputs", "DeviceInfoCatalogChecker",
                                            f"device {dev.get('id')} endpoint {ep_id}: missing fields {missing}",
                                            {"missing": missing, "type": etype}))
                if ep.get("direction") and ep.get("direction") != spec.get("direction"):
                    failures.append(failure(ErrorCode.E_ENDPOINT_TYPE, "inputs", "DeviceInfoCatalogChecker",
                                            f"device {dev.get('id')} endpoint {ep_id}: direction {ep.get('direction')} != {spec.get('direction')}",
                                            {"direction": ep.get("direction"), "expected": spec.get("direction")}))
                secret_pattern = re.compile(r"<SECRET_[A-Z0-9_]+>")
                for key, val in ep.items():
                    if isinstance(val, str) and ("token" in key or "secret" in key or "auth" in key):
                        if not secret_pattern.search(val):
                            failures.append(failure(ErrorCode.E_ENDPOINT_TYPE, "inputs", "DeviceInfoCatalogChecker",
                                                    f"device {dev.get('id')} endpoint {ep_id}: field {key} must use <SECRET_...> placeholder",
                                                    {"field": key}))
                    if key in ("address", "service") and "SECRET" in str(val):
                        if not secret_pattern.search(str(val)):
                            failures.append(failure(ErrorCode.E_ENDPOINT_TYPE, "inputs", "DeviceInfoCatalogChecker",
                                                    f"device {dev.get('id')} endpoint {ep_id}: secrets must be <SECRET_...>",
                                                    {"field": key}))
        return {
            "pass": len(failures) == 0,
            "failures": failures,
            "warnings": warnings,
            "metrics": {}
        }
