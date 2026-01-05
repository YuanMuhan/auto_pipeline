"""Component catalog checker - ensures IR component types and interface usage are from catalog"""

from typing import Dict, Any, Set, List
from pathlib import Path

from autopipeline.catalog.profile_loader import ProfileLoader
from autopipeline.catalog.catalog_utils import load_catalog_types
from autopipeline.eval.error_codes import ErrorCode, failure
import yaml
import os
import re


class ComponentCatalogChecker:
    def __init__(self, base_dir: str, strict: bool = False):
        self.loader = ProfileLoader(base_dir)
        self.types: Set[str] = self.loader.list_types()
        self.strict = strict
        alias_path = os.path.join(base_dir, "catalog", "type_aliases.yaml")
        if os.path.exists(alias_path):
            self.aliases = yaml.safe_load(open(alias_path, "r", encoding="utf-8")) or {}
        else:
            self.aliases = {}
        # Normalize alias targets to valid catalog types
        valid_types = load_catalog_types(Path(base_dir) / "catalog" / "components" / "index.yaml")
        self.alias_warnings: List[str] = []

        def _variants(name: str):
            variants = set()
            lower = name.lower()
            variants.add(lower)
            variants.add(lower.replace("_", ""))
            variants.add(lower.replace("-", ""))
            # camel to snake-ish
            s = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
            variants.add(s)
            variants.add(s.replace("_", ""))
            return variants

        fixed_aliases = {}
        for k, v in self.aliases.items():
            target = v
            if target in valid_types:
                fixed_aliases[k] = target
                continue
            candidates = []
            target_variants = _variants(target)
            for vt in valid_types:
                if _variants(vt) & target_variants:
                    candidates.append(vt)
            if len(candidates) == 1:
                fixed_aliases[k] = candidates[0]
                if candidates[0] != target:
                    self.alias_warnings.append(f"alias target fixed: {target} -> {candidates[0]}")
            else:
                fixed_aliases[k] = target
                self.alias_warnings.append(f"alias target not resolved: {target} (candidates={candidates})")
        self.aliases = fixed_aliases

    def check_ir(self, ir_data: Dict[str, Any]):
        """Returns structured result with failures/warnings."""
        components = ir_data.get("components", ir_data.get("entities", []))
        failures: List = []
        warnings: List[str] = []
        metrics: Dict[str, Any] = {}

        warnings.extend(self.alias_warnings)
        # Normalize aliases
        for comp in components:
            ctype = comp.get("type")
            if not ctype:
                continue
            alias_key = str(ctype).lower()
            if alias_key in self.aliases:
                new_type = self.aliases[alias_key]
                if new_type != ctype:
                    warnings.append(f"normalized component {comp.get('id')} type {ctype} -> {new_type}")
                comp["type"] = new_type

        invalid: List[str] = []
        invalid_entries: List[Dict[str, Any]] = []
        for comp in components:
            ctype = comp.get("type")
            if ctype not in self.types:
                invalid.append(ctype)
                invalid_entries.append({"id": comp.get("id"), "type": ctype})
        if invalid:
            metrics["unknown_types"] = invalid_entries
            metrics["unknown_types_count"] = len(invalid_entries)
            msg = f"IR component types not in catalog: {', '.join(filter(None, invalid))}"
            if self.strict:
                failures.append(failure(ErrorCode.E_CATALOG_COMPONENT, "ir", "ComponentCatalogChecker", msg,
                                        {"invalid_types": invalid}))
            else:
                warnings.append(f"{msg} (open mode: treated as warning)")

        comp_map = {c.get("id"): c for c in components}

        for comp in components:
            cid = comp.get("id")
            ctype = comp.get("type")
            if ctype not in self.types:
                # open mode: no profile to validate interfaces
                warnings.append(f"component {cid} type '{ctype}' has no catalog spec; skip port validation")
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
            "metrics": metrics
        }
