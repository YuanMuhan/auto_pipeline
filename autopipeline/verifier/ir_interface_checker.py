"""IR interface-level checker using component profiles"""

from typing import Dict, Any, Tuple, List
from autopipeline.verifier.component_catalog_checker import ComponentCatalogChecker


class IRInterfaceChecker:
    def __init__(self, catalog_checker: ComponentCatalogChecker):
        self.catalog_checker = catalog_checker

    def check(self, ir_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        ok, _msg, errors, warnings = self.catalog_checker.check_ir(ir_data)
        return ok, errors, warnings
