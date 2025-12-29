"""Component catalog checker - ensures IR component types and interface usage are from catalog"""

from typing import Dict, Any, Set, List

from autopipeline.catalog.profile_loader import ProfileLoader
from autopipeline.eval.error_codes import ErrorCode, failure


class ComponentCatalogChecker:
    def __init__(self, base_dir: str):
        self.loader = ProfileLoader(base_dir)
        self.types: Set[str] = self.loader.list_types()

    def check_ir(self, ir_data: Dict[str, Any]):
        """Returns structured result with failures/warnings."""
        components = ir_data.get("components", ir_data.get("entities", []))
        failures: List = []
        warnings: List[str] = []

        invalid = []
        for comp in components:
            ctype = comp.get("type")
            if ctype not in self.types:
                invalid.append(ctype)
        if invalid:
            failures.append(failure(ErrorCode.E_CATALOG_COMPONENT, "ir", "ComponentCatalogChecker",
                                    f"IR component types not in catalog: {', '.join(filter(None, invalid))}",
                                    {"invalid_types": invalid}))

        comp_map = {c.get("id"): c for c in components}

        for comp in components:
            cid = comp.get("id")
            ctype = comp.get("type")
            if ctype not in self.types:
                continue
            interfaces = self.loader.get_interfaces(ctype)
            for field in ["uses", "inputs", "outputs", "ports"]:
                if field in comp:
                    ports = comp.get(field) or []
                    for p in ports:
                        if p not in interfaces["all_interfaces"]:
                            failures.append(failure(ErrorCode.E_CATALOG_COMPONENT, "ir", "ComponentCatalogChecker",
                                                    f"component {cid} uses unknown port '{p}' not in profile {ctype}",
                                                    {"component": cid, "port": p, "type": ctype}))
            if not any(k in comp for k in ["uses", "inputs", "outputs", "ports"]):
                warnings.append(f"component {cid} has no explicit ports; skipping port validation")

        for link in ir_data.get("links", []):
            from_id = link.get("from")
            to_id = link.get("to")
            from_port = link.get("from_port") or (link.get("from") if isinstance(link.get("from"), dict) else None)
            to_port = link.get("to_port") or (link.get("to") if isinstance(link.get("to"), dict) else None)
            if isinstance(link.get("from"), dict):
                from_port = link["from"].get("port")
                from_id = link["from"].get("component") or link["from"].get("id")
            if isinstance(link.get("to"), dict):
                to_port = link["to"].get("port")
                to_id = link["to"].get("component") or link["to"].get("id")

            if not from_port or not to_port:
                warnings.append(f"link {link.get('id')} missing explicit ports; skipping port validation")
                continue

            for cid, port in [(from_id, from_port), (to_id, to_port)]:
                comp = comp_map.get(cid, {})
                ctype = comp.get("type")
                if ctype not in self.types:
                    continue
                interfaces = self.loader.get_interfaces(ctype)
                if port not in interfaces["all_interfaces"]:
                    failures.append(failure(ErrorCode.E_CATALOG_COMPONENT, "ir", "ComponentCatalogChecker",
                                            f"link {link.get('id')}: port '{port}' not in profile of component {cid} ({ctype})",
                                            {"component": cid, "port": port, "type": ctype, "link": link.get("id")}))

        for pol in ir_data.get("policies", []):
            actions = pol.get("actions", [])
            for act in actions:
                target = act.get("target") or act.get("component")
                service = act.get("service")
                if not target or not service:
                    continue
                comp = comp_map.get(target, {})
                ctype = comp.get("type")
                if ctype in self.types:
                    interfaces = self.loader.get_interfaces(ctype)
                    if service not in interfaces["provided_services"] and service not in interfaces["required_services"]:
                        warnings.append(f"policy {pol.get('name')}: service '{service}' not in component {target} profile")

        return {
            "pass": len(failures) == 0,
            "failures": failures,
            "warnings": warnings,
            "metrics": {}
        }
