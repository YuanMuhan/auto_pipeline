"""Coverage checker - ensures all IR links are mapped in bindings"""

from typing import Dict, Any, Tuple, Set


class CoverageChecker:
    """Check that all IR links are covered in bindings"""

    def check_coverage(self, ir_data: Dict[str, Any], bindings_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if all IR links are mapped in bindings"""

        # Extract all link IDs from IR
        ir_links: Set[str] = set()
        for link in ir_data.get('links', []):
            ir_links.add(link['id'])

        # Extract all link IDs from bindings (transports and endpoints)
        bindings_links: Set[str] = set()
        for transport in bindings_data.get('transports', []):
            bindings_links.add(transport['link_id'])

        for endpoint in bindings_data.get('endpoints', []):
            bindings_links.add(endpoint['link_id'])

        # Check coverage
        unmapped_links = ir_links - bindings_links

        if unmapped_links:
            return False, f"Coverage check failed: unmapped IR links: {', '.join(unmapped_links)}"

        return True, f"Coverage check passed: all {len(ir_links)} IR links are mapped in bindings"
