"""Repair Agent - automatically fixes IR and Bindings validation errors"""

from typing import Dict, Any, Tuple


class RepairAgent:
    """Repair IR or Bindings based on validation errors using prompt-based reasoning"""

    def __init__(self):
        self.max_repair_attempts = 3

    def repair_ir(self, ir_data: Dict[str, Any], error_message: str, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Repair IR based on validation error

        This is a prompt-only simulation - in real implementation, this would call LLM
        """

        prompt = self._build_ir_repair_prompt(ir_data, error_message, device_info)

        # Simulate repair (in production, this would be LLM-generated)
        repaired_ir = self._simulate_ir_repair(ir_data, error_message)

        return repaired_ir

    def repair_bindings(self, bindings_data: Dict[str, Any], error_message: str,
                       ir_data: Dict[str, Any], device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Repair Bindings based on validation error

        This is a prompt-only simulation - in real implementation, this would call LLM
        """

        prompt = self._build_bindings_repair_prompt(bindings_data, error_message, ir_data, device_info)

        # Simulate repair
        repaired_bindings = self._simulate_bindings_repair(bindings_data, error_message, ir_data, device_info)

        return repaired_bindings

    def _build_ir_repair_prompt(self, ir_data: Dict[str, Any], error_message: str,
                                device_info: Dict[str, Any]) -> str:
        """Build prompt for IR repair (simulation)"""
        return f"""
You are an IR repair agent.

Current IR (with errors):
{ir_data}

Validation Error:
{error_message}

Available Devices:
{device_info}

Fix the IR to pass validation. Remember:
- IR must not contain implementation details (ports, URLs, endpoints, etc.)
- All required fields must be present
- Follow the IR schema strictly

Output the corrected IR in JSON format.
"""

    def _build_bindings_repair_prompt(self, bindings_data: Dict[str, Any], error_message: str,
                                     ir_data: Dict[str, Any], device_info: Dict[str, Any]) -> str:
        """Build prompt for Bindings repair (simulation)"""
        return f"""
You are a Bindings repair agent.

Current Bindings (with errors):
{bindings_data}

Validation Error:
{error_message}

IR:
{ir_data}

Available Devices:
{device_info}

Fix the Bindings to pass validation. Remember:
- All IR links must be covered
- Endpoints must reference valid addresses from device_info
- Follow the Bindings schema strictly

Output the corrected Bindings in JSON format.
"""

    def _simulate_ir_repair(self, ir_data: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Simulate IR repair (placeholder for LLM output)"""

        # Simple repair heuristics
        repaired = ir_data.copy()

        # Ensure required fields
        if 'entities' not in repaired:
            repaired['entities'] = []
        if 'links' not in repaired:
            repaired['links'] = []
        if 'metadata' not in repaired:
            repaired['metadata'] = {"description": "Repaired IR", "version": "1.0"}

        # Remove forbidden keywords (boundary violations)
        repaired = self._remove_forbidden_keywords(repaired)

        return repaired

    def _simulate_bindings_repair(self, bindings_data: Dict[str, Any], error_message: str,
                                  ir_data: Dict[str, Any], device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Bindings repair (placeholder for LLM output)"""

        repaired = bindings_data.copy()

        # Ensure required fields
        if 'placements' not in repaired:
            repaired['placements'] = []
        if 'transports' not in repaired:
            repaired['transports'] = []
        if 'endpoints' not in repaired:
            repaired['endpoints'] = []

        # Fix coverage: ensure all IR links are in transports and endpoints
        ir_links = {link['id'] for link in ir_data.get('links', [])}
        transport_links = {t['link_id'] for t in repaired.get('transports', [])}
        endpoint_links = {e['link_id'] for e in repaired.get('endpoints', [])}

        # Add missing transports
        missing_links = ir_links - transport_links
        for link_id in missing_links:
            repaired['transports'].append({
                "link_id": link_id,
                "protocol": "HTTP",
                "qos": "best_effort"
            })

        # Add missing endpoints (use valid addresses from device_info)
        valid_addresses = self._extract_valid_addresses(device_info)
        missing_endpoint_links = ir_links - endpoint_links

        for link_id in missing_endpoint_links:
            if len(valid_addresses) >= 2:
                repaired['endpoints'].append({
                    "link_id": link_id,
                    "from_endpoint": valid_addresses[0],
                    "to_endpoint": valid_addresses[1]
                })
            elif len(valid_addresses) == 1:
                repaired['endpoints'].append({
                    "link_id": link_id,
                    "from_endpoint": valid_addresses[0],
                    "to_endpoint": valid_addresses[0]
                })

        return repaired

    def _remove_forbidden_keywords(self, data: Any) -> Any:
        """Recursively remove forbidden keywords from data structure"""
        if isinstance(data, dict):
            # Create new dict without forbidden keys
            return {k: self._remove_forbidden_keywords(v) for k, v in data.items()
                   if k.lower() not in ['url', 'port', 'mqtt', 'http', 'docker', 'endpoint']}
        elif isinstance(data, list):
            return [self._remove_forbidden_keywords(item) for item in data]
        else:
            return data

    def _extract_valid_addresses(self, device_info: Dict[str, Any]) -> list:
        """Extract valid endpoint addresses from device_info"""
        addresses = []
        for device in device_info.get('devices', []):
            interfaces = device.get('interfaces', {})
            endpoints = interfaces.get('endpoints', [])
            for endpoint in endpoints:
                if 'address' in endpoint:
                    addresses.append(endpoint['address'])
        return addresses
