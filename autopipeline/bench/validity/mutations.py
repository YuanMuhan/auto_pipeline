"""Definitions of validity mutations for PR3 mutation suite."""

import shutil
import yaml
from pathlib import Path


class Mutation:
    def __init__(self, mid, desc, apply_fn, expected_check=None, expected_code=None, expect_pass=False):
        self.id = mid
        self.desc = desc
        self.apply_fn = apply_fn
        self.expected_check = expected_check
        self.expected_code = expected_code
        self.expect_pass = expect_pass


def _load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _save_yaml(data, path: Path):
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def m01_drop_ir_top(path: Path):
    ir = _load_yaml(path / "ir.yaml")
    ir.pop("components", None)
    _save_yaml(ir, path / "ir.yaml")


def m02_bad_component_type(path: Path):
    ir = _load_yaml(path / "ir.yaml")
    if ir.get("components"):
        ir["components"][0]["type"] = "NonCatalogType"
        _save_yaml(ir, path / "ir.yaml")


def m03_alias_processor(path: Path):
    ir = _load_yaml(path / "ir.yaml")
    if ir.get("components"):
        ir["components"][0]["type"] = "processor"
        _save_yaml(ir, path / "ir.yaml")


def m04_drop_bindings_required(path: Path):
    bind = _load_yaml(path / "bindings.yaml")
    bind.pop("component_bindings", None)
    _save_yaml(bind, path / "bindings.yaml")


def m05_coverage_missing_link(path: Path):
    bind = _load_yaml(path / "bindings.yaml")
    eps = bind.get("endpoints") or bind.get("transports") or []
    if eps:
        eps.pop(0)
    _save_yaml(bind, path / "bindings.yaml")


def m06_endpoint_id_missing(path: Path):
    bind = _load_yaml(path / "bindings.yaml")
    if bind.get("endpoints"):
        if isinstance(bind["endpoints"], list):
            if isinstance(bind["endpoints"][0], dict):
                bind["endpoints"][0]["from_endpoint"] = "nonexistent_ep"
        _save_yaml(bind, path / "bindings.yaml")


def m07_endpoint_wrong_type(path: Path):
    di_path = path / "device_info.json"
    if not di_path.exists():
        return
    di = yaml.safe_load(di_path.read_text(encoding="utf-8")) or {}
    if di.get("endpoints"):
        di["endpoints"][0]["type"] = "invalid_type"
        di_path.write_text(yaml.safe_dump(di, allow_unicode=True, sort_keys=False), encoding="utf-8")


def m08_cross_artifact_bad_ref(path: Path):
    bind = _load_yaml(path / "bindings.yaml")
    if bind.get("component_bindings"):
        bind["component_bindings"][0]["component"] = "nonexistent_component"
    _save_yaml(bind, path / "bindings.yaml")


def m09_boundary_url(path: Path):
    ir = _load_yaml(path / "ir.yaml")
    if ir.get("components"):
        cfg = ir["components"][0].get("config", {}) or {}
        cfg["url"] = "https://example.com"
        ir["components"][0]["config"] = cfg
    _save_yaml(ir, path / "ir.yaml")


def m10_remove_compose_service(path: Path):
    compose_path = path / "docker-compose.yml"
    if compose_path.exists():
        lines = compose_path.read_text(encoding="utf-8").splitlines()
        if "services:" in lines:
            # drop the last non-empty line to simulate missing service
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip():
                    lines.pop(i)
                    break
            compose_path.write_text("\n".join(lines), encoding="utf-8")


def m11_break_bindings_hash(path: Path):
    bind = _load_yaml(path / "bindings.yaml")
    bind["app_name"] = (bind.get("app_name") or "app") + "_mutated"
    _save_yaml(bind, path / "bindings.yaml")


def m12_plan_ir_mismatch(path: Path):
    plan = _load_yaml(path / "plan.json")
    plan.pop("components_outline", None)
    (path / "plan.json").write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")


def get_mutations():
    return [
        Mutation("M01_DROP_IR_TOP_FIELD", "Remove components from IR", m01_drop_ir_top, expected_check="ir_schema"),
        Mutation("M02_BAD_COMPONENT_TYPE", "Set component type to non-catalog", m02_bad_component_type, expected_check="ir_component_catalog", expected_code="E_CATALOG_COMPONENT"),
        Mutation("M03_ALIAS_TYPE_NORMALIZE", "Set component type to processor to trigger alias", m03_alias_processor, expect_pass=True),
        Mutation("M04_DROP_BINDINGS_REQUIRED", "Remove component_bindings from bindings", m04_drop_bindings_required, expected_check="bindings_schema"),
        Mutation("M05_COVERAGE_MISSING_LINK", "Remove a binding endpoint/link", m05_coverage_missing_link, expected_check="coverage"),
        Mutation("M06_ENDPOINT_ID_NOT_EXIST", "Use nonexistent endpoint id", m06_endpoint_id_missing, expected_check="endpoint_matching"),
        Mutation("M07_ENDPOINT_WRONG_TYPE", "Set endpoint type invalid", m07_endpoint_wrong_type, expected_check="endpoint_legality"),
        Mutation("M08_CROSS_ARTIFACT_BAD_REF", "Bindings reference missing component", m08_cross_artifact_bad_ref, expected_check="cross_artifact_consistency"),
        Mutation("M09_BOUNDARY_URL_IN_CONFIG", "Add https URL to config", m09_boundary_url, expected_code="E_BOUNDARY"),
        Mutation("M10_REMOVE_COMPOSE_SERVICE", "Remove a compose service", m10_remove_compose_service, expected_check="deploy_generated"),
        Mutation("M11_BREAK_BINDINGS_HASH", "Mutate bindings to break hash", m11_break_bindings_hash, expected_check="generation_consistency"),
        Mutation("M12_PLAN_IR_MISMATCH", "Drop plan components_outline", m12_plan_ir_mismatch, expected_check="plan_schema"),
    ]
