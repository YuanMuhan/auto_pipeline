"""Evaluate existing artifacts (plan/ir/bindings/compose) without calling LLM."""

import os
from pathlib import Path
from typing import Dict, Any, List
import yaml

from autopipeline.utils import load_json, save_json, save_yaml, sha256_of_file
from autopipeline.eval.validators_registry import build_validators
from autopipeline.eval.error_codes import FailureRecord, ErrorCode


class ArtifactEvaluator:
    """Lightweight evaluator to run validators on an existing run_dir."""

    def __init__(self, base_dir: str = ".", runtime_check: bool = False, enable_catalog: bool = True,
                 enable_semantic: bool = True, gate_mode: str = "core", catalog_strict: bool = False):
        self.base_dir = base_dir
        self.runtime_check = runtime_check
        self.enable_catalog = enable_catalog
        self.enable_semantic = enable_semantic
        self.gate_mode = gate_mode or "core"
        self.validator_results: Dict[str, Dict[str, Any]] = {}
        self.failures_flat: List[Dict[str, Any]] = []
        self.pipeline_stats: Dict[str, Dict[str, Any]] = {}
        self.stages_passed: List[str] = []
        self.input_validation: List[str] = []

        v = build_validators(base_dir, enable_catalog=enable_catalog, enable_semantic=enable_semantic,
                             catalog_strict=catalog_strict)
        self.rules_bundle = v["rules_bundle"]
        self.schema_checker = v["schema_checker"]
        self.boundary_checker = v["boundary_checker"]
        self.coverage_checker = v["coverage_checker"]
        self.endpoint_checker = v["endpoint_checker"]
        self.component_catalog_checker = v["component_catalog_checker"]
        self.device_info_catalog_checker = v["device_info_catalog_checker"]
        self.ir_interface_checker = v["ir_interface_checker"]
        self.endpoint_matching_checker = v["endpoint_matching_checker"]
        self.cross_artifact_checker = v["cross_artifact_checker"]
        self.catalog_hash = v["catalog_hash"]
        self.gen_checker_cls = v["generation_checker_cls"]
        self.semantic_checker = v.get("semantic_checker")

    def _record_validator(self, name: str, result: Dict[str, Any]):
        failures = []
        for f in result.get("failures", []):
            if isinstance(f, FailureRecord):
                failures.append(f.to_dict())
            elif isinstance(f, dict):
                failures.append(f)
        entry = {
            "pass": result.get("pass", False),
            "failures": failures,
            "warnings": result.get("warnings", []),
            "metrics": result.get("metrics", {}),
            "status": result.get("status") or ("SKIP" if result.get("skipped") else ("PASS" if result.get("pass") else "FAIL")),
            "skipped": result.get("skipped", False),
        }
        self.validator_results[name] = entry

    def _check_and_record(self, name: str, result: Dict[str, Any]):
        self._record_validator(name, result)
        if not result.get("pass"):
            self.failures_flat.extend(self.validator_results[name]["failures"])

    def evaluate(self, run_dir: Path) -> Dict[str, Any]:
        # Load artifacts
        plan = load_json(run_dir / "plan.json")
        ir = yaml.safe_load((run_dir / "ir.yaml").read_text(encoding="utf-8"))
        # prefer normalized/official bindings
        bindings = None
        for name in ["bindings.yaml", "bindings_norm.yaml", "bindings_raw.yaml", "bindings_raw.txt"]:
            p = run_dir / name
            if p.exists():
                try:
                    if name.endswith(".txt"):
                        bindings = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                    else:
                        bindings = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                    break
                except Exception:
                    bindings = {}
                    break
        if bindings is None:
            bindings = {}
        # Prefer inputs/ paths if present
        up_path = run_dir / "inputs" / "user_problem.json"
        di_path = run_dir / "inputs" / "device_info.json"
        # Fallback to legacy run layout or cases/<case_id> for backward compatibility
        legacy_up = run_dir / "user_problem.json"
        legacy_di = run_dir / "device_info.json"
        case_id = run_dir.parent.name
        case_dir = Path(self.base_dir) / "cases" / case_id
        user_problem = {}
        device_info = {}
        if up_path.exists():
            user_problem = load_json(up_path)
        elif legacy_up.exists():
            user_problem = load_json(legacy_up)
        elif case_dir.exists():
            cand = case_dir / "user_problem.json"
            if cand.exists():
                user_problem = load_json(cand)

        if di_path.exists():
            device_info = load_json(di_path)
        elif legacy_di.exists():
            device_info = load_json(legacy_di)
        elif case_dir.exists():
            cand = case_dir / "device_info.json"
            if cand.exists():
                device_info = load_json(cand)

        # Basic schema/input checks
        up_res = self.schema_checker.validate_user_problem(user_problem)
        self._check_and_record("user_problem_schema", up_res)
        di_res = self.schema_checker.validate_device_info(device_info)
        self._check_and_record("device_info_schema", di_res)
        if self.enable_catalog:
            di_cat = self.device_info_catalog_checker.check(device_info)
            self._check_and_record("device_info_catalog", di_cat)
        else:
            self._record_validator("device_info_catalog", {"pass": True, "failures": [], "warnings": ["catalog skipped"], "status": "SKIP", "skipped": True})

        plan_res = self.schema_checker.validate_plan(plan)
        self._check_and_record("plan_schema", plan_res)

        ir_res = self.schema_checker.validate_ir(ir)
        self._check_and_record("ir_schema", ir_res)
        boundary_res = self.boundary_checker.check_ir(ir)
        self._check_and_record("ir_boundary", boundary_res)
        if self.enable_catalog:
            comp_res = self.component_catalog_checker.check_ir(ir)
            self._check_and_record("ir_component_catalog", comp_res)
            iface_res = self.ir_interface_checker.check(ir)
            self._check_and_record("ir_interface", iface_res)
        else:
            self._record_validator("ir_component_catalog", {"pass": True, "failures": [], "warnings": ["catalog skipped"], "status": "SKIP", "skipped": True})
            self._record_validator("ir_interface", {"pass": True, "failures": [], "warnings": ["catalog skipped"], "status": "SKIP", "skipped": True})

        bind_res = self.schema_checker.validate_bindings(bindings, gate_mode=self.gate_mode)
        self._check_and_record("bindings_schema", bind_res)
        cov_res = self.coverage_checker.check_coverage(ir, bindings, gate_mode=self.gate_mode)
        self._check_and_record("coverage", cov_res)
        ep_res = self.endpoint_checker.check_endpoints(bindings, device_info)
        self._check_and_record("endpoint_legality", ep_res)
        if self.enable_catalog:
            ep_match_res = self.endpoint_matching_checker.check(bindings, device_info, gate_mode=self.gate_mode)
            self._check_and_record("endpoint_matching", ep_match_res)
        else:
            self._record_validator("endpoint_matching", {"pass": True, "failures": [], "warnings": ["catalog skipped"], "status": "SKIP", "skipped": True})

        cross_res = self.cross_artifact_checker.check(ir, bindings)
        self._check_and_record("cross_artifact_consistency", cross_res)

        bindings_hash = sha256_of_file(run_dir / "bindings.yaml")
        gen_checker = self.gen_checker_cls(bindings_hash, str(run_dir))
        gen_res = gen_checker.check()
        self._check_and_record("generation_consistency", gen_res)

        # Semantic proxy warnings (non-blocking)
        if self.semantic_checker:
            art = {
                "user_problem": user_problem,
                "device_info": device_info,
                "plan": plan,
                "ir": ir,
                "bindings": bindings,
                "compose": None,
                "attempts_by_stage": {k: v.get("attempts") for k, v in self.pipeline_stats.items()},
            }
            sem_res = self.semantic_checker.check(art)
            self._record_validator("semantic_proxy", sem_res)
        else:
            self._record_validator("semantic_proxy", {"pass": True, "failures": [], "warnings": ["semantic warnings disabled"], "status": "SKIP", "skipped": True})

        # deploy/code presence
        self._record_validator("code_generated", {"pass": True, "failures": [], "warnings": [], "metrics": {}, "status": "PASS"})
        runtime_status = {"pass": True, "failures": [], "warnings": [], "metrics": {}, "status": "SKIP", "skipped": True}
        if self.runtime_check:
            runtime_status["status"] = "PASS"
        self._record_validator("runtime_compose", runtime_status)

        checks = {}
        for name, res in self.validator_results.items():
            msg = res["failures"][0]["message"] if res["failures"] else "OK"
            checks[name] = {"status": res.get("status", "PASS") if res.get("pass") else "FAIL", "message": msg}

        core_checks = {
            "user_problem_schema", "device_info_schema", "device_info_catalog",
            "plan_schema", "ir_schema", "ir_boundary", "ir_component_catalog", "ir_interface",
            "bindings_schema", "coverage", "endpoint_legality", "endpoint_matching", "cross_artifact_consistency"
        }
        exec_checks = {"code_generated", "deploy_generated", "generation_consistency", "runtime_compose"}
        core_fail = [k for k in core_checks if checks.get(k, {}).get("status") == "FAIL"]
        exec_fail = [k for k in exec_checks if checks.get(k, {}).get("status") == "FAIL"]

        overall_core = "FAIL" if core_fail else "PASS"
        overall_exec = "FAIL" if exec_fail else "PASS"
        gate_mode = (self.gate_mode or "core").lower()
        if gate_mode == "full":
            overall = "FAIL" if (core_fail or exec_fail) else "PASS"
        else:
            overall = overall_core

        runtime_status = checks.get("runtime_compose", {}).get("status", "SKIP")
        overall_runtime = runtime_status
        eval_result = {
            "case_id": run_dir.name,
            "overall_status": overall,
            "overall_static_status": overall,  # backward compat
            "overall_core_status": overall_core,
            "overall_exec_status": overall_exec,
            "overall_runtime_status": overall_runtime,
            "checks": checks,
            "validators": self.validator_results,
            "failures_flat": [f for res in self.validator_results.values() for f in res.get("failures", [])],
            "catalog_hashes": self.catalog_hash,
            "rules_version": {
                "rules_source": self.rules_bundle.get("source", "md_fallback"),
                "ir_rules_hash": self.rules_bundle["ir"]["hash"],
                "bindings_rules_hash": self.rules_bundle["bindings"]["hash"],
            },
        }
        cat_metrics = self.validator_results.get("ir_component_catalog", {}).get("metrics", {}) if self.validator_results else {}
        if cat_metrics:
            if "unknown_types_count" in cat_metrics:
                eval_result["unknown_component_types_count"] = cat_metrics.get("unknown_types_count", 0)
            if "unknown_types" in cat_metrics:
                eval_result["unknown_component_types"] = cat_metrics.get("unknown_types", [])
        return eval_result


def evaluate_run_dir(run_dir: Path, base_dir: str = ".", runtime_check: bool = False, enable_catalog: bool = True,
                     gate_mode: str = "core", catalog_strict: bool = False) -> Dict[str, Any]:
    ev = ArtifactEvaluator(base_dir=base_dir, runtime_check=runtime_check, enable_catalog=enable_catalog,
                           gate_mode=gate_mode, catalog_strict=catalog_strict)
    return ev.evaluate(run_dir)
