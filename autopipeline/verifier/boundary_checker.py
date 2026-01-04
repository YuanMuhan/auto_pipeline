"""Boundary checker - ensures IR doesn't contain implementation details"""

from typing import Dict, Any, List
import re

from autopipeline.eval.error_codes import ErrorCode, failure


class BoundaryChecker:
    """Check IR for forbidden implementation details"""

    def __init__(self, forbidden_keywords: List[str], forbidden_regex: List[str] = None):
        self.forbidden_keywords = sorted(set([kw.lower() for kw in forbidden_keywords]))
        self.forbidden_regex = forbidden_regex or []

    def _check_value(self, value: str, path: str, failures: List[Dict[str, Any]]):
        val_lower = value.lower()
        for keyword in self.forbidden_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, val_lower):
                failures.append(failure(
                    ErrorCode.E_BOUNDARY, "ir", "BoundaryChecker",
                    f"Forbidden keyword '{keyword}' at {path}",
                    {"path": path, "match": keyword, "rule": "forbidden_keywords"}
                ))
        for reg in self.forbidden_regex:
            try:
                m = re.search(reg, value)
            except re.error:
                continue
            if m:
                failures.append(failure(
                    ErrorCode.E_BOUNDARY, "ir", "BoundaryChecker",
                    f"Forbidden pattern matched at {path}: {m.group(0)}",
                    {"path": path, "match": m.group(0), "rule": "forbidden_regex"}
                ))

    def _walk(self, obj: Any, path: str, failures: List[Dict[str, Any]], skip_desc: bool = False):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if skip_desc and k == "description":
                    continue
                new_path = f"{path}.{k}" if path else k
                self._walk(v, new_path, failures, skip_desc=skip_desc and k != "description")
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                new_path = f"{path}[{idx}]"
                self._walk(item, new_path, failures, skip_desc=skip_desc)
        elif isinstance(obj, str):
            self._check_value(obj, path, failures)

    def check_ir(self, ir_data: Dict[str, Any]):
        """Check if IR contains forbidden implementation details"""
        failures: List[Dict[str, Any]] = []
        # components: skip description fields
        components = ir_data.get("components", ir_data.get("entities", []))
        for idx, comp in enumerate(components):
            self._walk(comp, f"components[{idx}]", failures, skip_desc=True)
        # links
        for idx, link in enumerate(ir_data.get("links", [])):
            self._walk(link, f"links[{idx}]", failures, skip_desc=False)
        # schemas / policies if present
        if "schemas" in ir_data:
            self._walk(ir_data.get("schemas"), "schemas", failures, skip_desc=False)
        if "policies" in ir_data:
            self._walk(ir_data.get("policies"), "policies", failures, skip_desc=False)

        if failures:
            return {
                "pass": False,
                "failures": failures,
                "warnings": [],
                "metrics": {}
            }

        return {
            "pass": True,
            "failures": [],
            "warnings": [],
            "metrics": {}
        }
