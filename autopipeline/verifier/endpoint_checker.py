"""Endpoint legality checker - ensures bindings only reference valid device endpoints"""

from typing import Dict, Any, Set

from autopipeline.eval.error_codes import ErrorCode, failure


class EndpointChecker:
    """Check that bindings only reference endpoints from DeviceInfo"""

    def check_endpoints(self, bindings_data: Dict[str, Any], device_info: Dict[str, Any]):
        """Check if all endpoints in bindings are valid"""

        valid_endpoints: Set[str] = set()
        for device in device_info.get('devices', []):
            interfaces = device.get('interfaces', {})
            endpoints = interfaces.get('endpoints', [])
            for endpoint in endpoints:
                if 'address' in endpoint:
                    valid_endpoints.add(endpoint['address'])

        referenced_endpoints: Set[str] = set()
        for endpoint_mapping in bindings_data.get('endpoints', []):
            if 'from_endpoint' in endpoint_mapping:
                referenced_endpoints.add(endpoint_mapping['from_endpoint'])
            if 'to_endpoint' in endpoint_mapping:
                referenced_endpoints.add(endpoint_mapping['to_endpoint'])

        invalid_endpoints = referenced_endpoints - valid_endpoints

        if invalid_endpoints:
            return {
                "pass": False,
                "failures": [failure(ErrorCode.E_ENDPOINT_CHECK, "bindings", "EndpointChecker",
                                     f"Endpoint legality check failed: invalid endpoints not in DeviceInfo: {', '.join(invalid_endpoints)}",
                                     {"invalid_endpoints": sorted(invalid_endpoints)})],
                "warnings": [],
                "metrics": {"referenced": len(referenced_endpoints), "invalid": len(invalid_endpoints)}
            }

        return {
            "pass": True,
            "failures": [],
            "warnings": [],
            "metrics": {"referenced": len(referenced_endpoints), "invalid": 0}
        }
