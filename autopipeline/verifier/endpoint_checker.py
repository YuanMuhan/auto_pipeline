"""Endpoint legality checker - ensures bindings only reference valid device endpoints"""

from typing import Dict, Any, Tuple, Set


class EndpointChecker:
    """Check that bindings only reference endpoints from DeviceInfo"""

    def check_endpoints(self, bindings_data: Dict[str, Any], device_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if all endpoints in bindings are valid"""

        # Extract valid endpoints from device_info
        valid_endpoints: Set[str] = set()
        for device in device_info.get('devices', []):
            interfaces = device.get('interfaces', {})
            endpoints = interfaces.get('endpoints', [])
            for endpoint in endpoints:
                if 'address' in endpoint:
                    valid_endpoints.add(endpoint['address'])

        # Extract all endpoints referenced in bindings
        referenced_endpoints: Set[str] = set()
        for endpoint_mapping in bindings_data.get('endpoints', []):
            referenced_endpoints.add(endpoint_mapping['from_endpoint'])
            referenced_endpoints.add(endpoint_mapping['to_endpoint'])

        # Check for invalid endpoints
        invalid_endpoints = referenced_endpoints - valid_endpoints

        if invalid_endpoints:
            return False, f"Endpoint legality check failed: invalid endpoints not in DeviceInfo: {', '.join(invalid_endpoints)}"

        return True, f"Endpoint legality check passed: all {len(referenced_endpoints)} endpoints are valid"
