"""Coverage checker - ensures all IR links are mapped in bindings"""

from typing import Dict, Any, Set

from autopipeline.eval.error_codes import ErrorCode, failure


class CoverageChecker:
    """Check that all IR links are covered in bindings"""

    def check_coverage(self, ir_data: Dict[str, Any], bindings_data: Dict[str, Any]):
        """Check if all IR links are mapped in bindings"""

        ir_links: Set[str] = {link['id'] for link in ir_data.get('links', [])}

        bindings_links: Set[str] = set()
        for transport in bindings_data.get('transports', []):
            bindings_links.add(transport['link_id'])
        for endpoint in bindings_data.get('endpoints', []):
            bindings_links.add(endpoint['link_id'])

        unmapped_links = ir_links - bindings_links

        if unmapped_links:
            return {
                "pass": False,
                "failures": [failure(ErrorCode.E_COVERAGE, "bindings", "CoverageChecker",
                                     f"Coverage check failed: unmapped IR links: {', '.join(unmapped_links)}",
                                     {"unmapped_links": sorted(unmapped_links)})],
                "warnings": [],
                "metrics": {"coverage_ratio": len(ir_links - unmapped_links) / len(ir_links) if ir_links else 1.0}
            }

        return {
            "pass": True,
            "failures": [],
            "warnings": [],
            "metrics": {"coverage_ratio": 1.0}
        }
