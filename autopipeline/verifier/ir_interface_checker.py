"""IR interface-level checker using component profiles"""

from autopipeline.verifier.component_catalog_checker import ComponentCatalogChecker


class IRInterfaceChecker:
    def __init__(self, catalog_checker: ComponentCatalogChecker):
        self.catalog_checker = catalog_checker

    def check(self, ir_data):
        return self.catalog_checker.check_ir(ir_data)
