"""Bindings Agent - maps IR to physical deployment (placements, transports, endpoints)"""

from typing import Dict, Any, List
from autopipeline.agents.prompt_utils import PromptTemplate


class BindingsAgent:
    """Generate bindings from IR and device info"""

    def __init__(self):
        self.prompt_template = PromptTemplate()

    def generate_bindings(self, ir_data: Dict[str, Any], device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate bindings (placements, transports, endpoints) from IR

        This is a prompt-only simulation - in real implementation, this would call LLM
        """

        # Build prompt using template
        prompt = self.prompt_template.get_binding_prompt(ir_data, device_info)

        # Simulate bindings generation
        bindings = self._simulate_bindings_generation(ir_data, device_info)

        return bindings

    def _simulate_bindings_generation(self, ir_data: Dict[str, Any], device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate bindings generation (placeholder for LLM output)"""

        # Extract available endpoints from device_info
        available_endpoints = []
        device_refs = {}

        for device in device_info.get('devices', []):
            device_id = device.get('id', '')
            device_refs[device_id] = device
            interfaces = device.get('interfaces', {})
            endpoints = interfaces.get('endpoints', [])
            for endpoint in endpoints:
                if 'address' in endpoint:
                    available_endpoints.append({
                        'address': endpoint['address'],
                        'device_id': device_id,
                        'protocol': endpoint.get('protocol', 'unknown')
                    })

        # Generate placements (assign components to layers) - using 'components' instead of 'entities'
        placements = []
        components = ir_data.get('components', ir_data.get('entities', []))  # Backward compatibility

        for i, component in enumerate(components):
            # Simple heuristic: first component -> device, middle -> edge, last -> cloud
            if i == 0:
                layer = 'device'
            elif i == len(components) - 1:
                layer = 'cloud'
            else:
                layer = 'edge'

            # Find suitable device
            device_ref = self._find_device_for_layer(layer, device_info)

            placements.append({
                "component_id": component['id'],  # Changed from entity_id to component_id
                "layer": layer,
                "device_ref": device_ref
            })

        # Generate transports (assign protocols to links)
        transports = []
        links = ir_data.get('links', [])

        for link in links:
            # Simple heuristic: use MQTT for device-edge, HTTP for edge-cloud
            from_layer = self._get_component_layer(link['from'], placements)
            to_layer = self._get_component_layer(link['to'], placements)

            if from_layer == 'device' or to_layer == 'device':
                protocol = 'MQTT'
                qos = 'at_least_once'
            else:
                protocol = 'HTTP'
                qos = 'best_effort'

            transports.append({
                "link_id": link['id'],
                "protocol": protocol,
                "qos": qos
            })

        # Generate endpoints (map to actual addresses)
        endpoints_mapping = []

        for link in links:
            # Use available endpoints from device_info
            if len(available_endpoints) >= 2:
                from_ep = available_endpoints[0]['address']
                to_ep = available_endpoints[min(1, len(available_endpoints)-1)]['address']
            else:
                # Fallback if not enough endpoints
                from_ep = available_endpoints[0]['address'] if available_endpoints else "default_endpoint"
                to_ep = from_ep

            endpoints_mapping.append({
                "link_id": link['id'],
                "from_endpoint": from_ep,
                "to_endpoint": to_ep
            })

        component_bindings = []
        for placement in placements:
            component_bindings.append({
                "component": placement["component_id"],
                "layer": placement["layer"],
                "device_ref": placement["device_ref"]
            })

        return {
            "app_name": ir_data.get("app_name", "app"),
            "version": ir_data.get("version", ir_data.get("metadata", {}).get("version", "1.0")),
            "placements": placements,
            "transports": transports,
            "endpoints": endpoints_mapping,
            "component_bindings": component_bindings
        }

    def _find_device_for_layer(self, layer: str, device_info: Dict[str, Any]) -> str:
        """Find a suitable device for the given layer"""
        devices = device_info.get('devices', [])
        for device in devices:
            device_layer = device.get('layer', '')
            if device_layer == layer:
                return device.get('id', 'unknown')

        # Fallback
        return devices[0].get('id', 'default_device') if devices else 'default_device'

    def _get_component_layer(self, component_id: str, placements: List[Dict[str, Any]]) -> str:
        """Get layer for a component from placements"""
        for placement in placements:
            if placement['component_id'] == component_id:
                return placement['layer']
        return 'unknown'
