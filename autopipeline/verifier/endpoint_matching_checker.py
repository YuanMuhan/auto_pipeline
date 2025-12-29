"""Endpoint matching checker - validates bindings endpoints against device_info definitions"""

from typing import Dict, Any, List

from autopipeline.eval.error_codes import ErrorCode, failure


class EndpointMatchingChecker:
    def __init__(self, endpoint_types: Dict[str, Any]):
        self.endpoint_types = endpoint_types.get("endpoint_types", [])
        self.type_map = {et["name"]: et for et in self.endpoint_types}

    def _direction_allowed(self, etype: str, role: str) -> bool:
        if etype == "mqtt_pub":
            return role == "source"
        if etype == "mqtt_sub":
            return role == "sink"
        if etype == "ha_state":
            return role == "sink"
        if etype == "ha_service":
            return role == "source"
        if etype == "http":
            return True
        return True

    def _requires_payload(self, etype: str) -> bool:
        return etype in ("mqtt_pub", "mqtt_sub", "http")

    def _collect_device_endpoints(self, device_info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        ep_map = {}
        for dev in device_info.get("devices", []):
            for ep in dev.get("interfaces", {}).get("endpoints", []):
                if "address" in ep:
                    ep_map[ep["address"]] = ep
                if "id" in ep:
                    ep_map[ep["id"]] = ep
        return ep_map

    def check(self, bindings_data: Dict[str, Any], device_info: Dict[str, Any]):
        errors: List = []
        warnings: List[str] = []
        ep_map = self._collect_device_endpoints(device_info)
        endpoints = bindings_data.get("endpoints", [])

        for ep_bind in endpoints:
            link_id = ep_bind.get("link_id")
            for role, key in (("source", "from_endpoint"), ("sink", "to_endpoint")):
                ref = ep_bind.get(key)
                if not ref:
                    warnings.append(f"link {link_id}: {key} missing")
                    continue
                if ref not in ep_map:
                    errors.append(failure(ErrorCode.E_ENDPOINT_CHECK, "bindings", "EndpointMatchingChecker",
                                          f"link {link_id}: endpoint ref '{ref}' not found in device_info",
                                          {"link_id": link_id, "endpoint_ref": ref}))
                    continue
                ep_def = ep_map[ref]
                etype = ep_def.get("type") or ep_def.get("protocol")
                if etype not in self.type_map:
                    errors.append(failure(ErrorCode.E_ENDPOINT_TYPE, "bindings", "EndpointMatchingChecker",
                                          f"link {link_id}: endpoint {ref} has unknown type '{etype}'",
                                          {"endpoint_ref": ref, "type": etype}))
                    continue
                if not self._direction_allowed(etype, role):
                    warnings.append(f"link {link_id}: endpoint {ref} type '{etype}' uncommon as {role}")
                if self._requires_payload(etype) and not ep_def.get("payload_schema"):
                    errors.append(failure(ErrorCode.E_ENDPOINT_MISSING_FIELDS, "bindings", "EndpointMatchingChecker",
                                          f"link {link_id}: endpoint {ref} of type {etype} missing payload_schema",
                                          {"endpoint_ref": ref, "type": etype}))

        return {
            "pass": len(errors) == 0,
            "failures": errors,
            "warnings": warnings,
            "metrics": {}
        }
