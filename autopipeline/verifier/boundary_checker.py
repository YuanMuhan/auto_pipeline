"""Boundary checker - ensures IR doesn't contain implementation details"""

from typing import Dict, Any, Tuple, List
import re


class BoundaryChecker:
    """Check IR for forbidden implementation details"""

    def __init__(self, forbidden_keywords: List[str]):
        # Deduplicate and normalize
        self.forbidden_keywords = sorted(set([kw.lower() for kw in forbidden_keywords]))

    def check_ir(self, ir_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if IR contains forbidden implementation details"""
        violations = []

        # Convert IR to string for keyword search
        ir_str = str(ir_data).lower()

        for keyword in self.forbidden_keywords:
            # Use word boundary to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, ir_str):
                violations.append(keyword)

        if violations:
            return False, f"IR boundary violation: forbidden keywords found: {', '.join(violations)}"

        return True, "IR boundary check passed"
