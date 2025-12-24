"""Component catalog checker - ensures IR component types are from catalog"""

from typing import Dict, Any, Tuple, Set

from autopipeline.catalog.render import load_component_profiles


class ComponentCatalogChecker:
    def __init__(self, base_dir: str):
        data = load_component_profiles(base_dir)
        self.types: Set[str] = set(data["profiles"].keys())

    def check_ir(self, ir_data: Dict[str, Any]) -> Tuple[bool, str]:
        components = ir_data.get("components", ir_data.get("entities", []))
        invalid = []
        for comp in components:
            ctype = comp.get("type")
            if ctype not in self.types:
                invalid.append(ctype)
        if invalid:
            return False, f"IR component types not in catalog: {', '.join(filter(None, invalid))}"
        return True, "IR component types valid"
