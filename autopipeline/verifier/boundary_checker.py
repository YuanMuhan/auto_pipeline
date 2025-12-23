"""Boundary checker - ensures IR doesn't contain implementation details"""

from typing import Dict, Any, Tuple, List
import re


class BoundaryChecker:
    """Check IR for forbidden implementation details"""

    # Forbidden keywords that should NOT appear in IR
    FORBIDDEN_KEYWORDS = [
        'entity_id', 'topic', 'url', 'port', 'mqtt', 'http', 'https',
        'docker', 'k8s', 'kubernetes', 'container', 'host', 'ip',
        'address', 'endpoint', 'socket', 'tcp', 'udp', 'grpc',
        'rest', 'api', 'broker', 'registry', 'deployment'
    ]

    def check_ir(self, ir_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if IR contains forbidden implementation details"""
        violations = []

        # Convert IR to string for keyword search
        ir_str = str(ir_data).lower()

        for keyword in self.FORBIDDEN_KEYWORDS:
            # Use word boundary to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, ir_str):
                violations.append(keyword)

        if violations:
            return False, f"IR boundary violation: forbidden keywords found: {', '.join(violations)}"

        return True, "IR boundary check passed"
