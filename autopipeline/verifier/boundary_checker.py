"""Boundary checker - ensures IR doesn't contain implementation details"""

from typing import Dict, Any, List
import re

from autopipeline.eval.error_codes import ErrorCode, failure


class BoundaryChecker:
    """Check IR for forbidden implementation details"""

    def __init__(self, forbidden_keywords: List[str]):
        # Deduplicate and normalize
        self.forbidden_keywords = sorted(set([kw.lower() for kw in forbidden_keywords]))

    def check_ir(self, ir_data: Dict[str, Any]):
        """Check if IR contains forbidden implementation details"""
        violations = []
        ir_str = str(ir_data).lower()

        for keyword in self.forbidden_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, ir_str):
                violations.append(keyword)

        if violations:
            return {
                "pass": False,
                "failures": [failure(ErrorCode.E_BOUNDARY, "ir", "BoundaryChecker",
                                     f"IR boundary violation: forbidden keywords found: {', '.join(violations)}",
                                     {"violations": violations})],
                "warnings": [],
                "metrics": {}
            }

        return {
            "pass": True,
            "failures": [],
            "warnings": [],
            "metrics": {}
        }
