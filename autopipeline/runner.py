"""Main pipeline runner - orchestrates the entire workflow"""

import os
import time
import subprocess
import py_compile
from datetime import datetime
from typing import Dict, Any, Tuple, List

from autopipeline.utils import load_json, save_json, save_yaml, ensure_dir, sha256_of_file
from autopipeline.agents.planner import PlannerAgent
from autopipeline.agents.ir_agent import IRAgent
from autopipeline.agents.bindings import BindingsAgent
from autopipeline.agents.repair import RepairAgent
from autopipeline.agents.codegen import CodeGenAgent
from autopipeline.agents.deploy import DeployAgent
from autopipeline.verifier.rules_loader import load_rules_bundle
from autopipeline.verifier.schema_checker import SchemaChecker
from autopipeline.verifier.boundary_checker import BoundaryChecker
from autopipeline.verifier.coverage_checker import CoverageChecker
from autopipeline.verifier.endpoint_checker import EndpointChecker
from autopipeline.verifier.component_catalog_checker import ComponentCatalogChecker
from autopipeline.verifier.ir_interface_checker import IRInterfaceChecker
from autopipeline.verifier.endpoint_matching_checker import EndpointMatchingChecker
from autopipeline.verifier.device_info_catalog_checker import DeviceInfoCatalogChecker
from autopipeline.catalog.render import catalog_hashes, component_types_summary, endpoint_types_summary, load_component_profiles, load_endpoint_types
from autopipeline.verifier.generation_checker import GenerationConsistencyChecker
from autopipeline.verifier.cross_artifact_checker import CrossArtifactChecker
from autopipeline.llm import LLMClient
from autopipeline.llm.types import LLMConfig
from autopipeline.llm.hash_utils import stable_hash
from autopipeline.eval.error_codes import FailureRecord, ErrorCode


class PipelineRunner:
    """Orchestrates the entire AutoPipeline workflow"""

    def __init__(self, case_id: str, base_dir: str = ".", llm_config: LLMConfig = None,
                 output_root: str = "outputs", enable_repair: bool = True, enable_catalog: bool = True,
                 runtime_check: bool = False):
        self.case_id = case_id
        self.base_dir = base_dir
        self.case_dir = os.path.join(base_dir, "cases", case_id)
        self.output_root = output_root
        self.output_dir = os.path.join(base_dir, output_root, case_id)
        self.llm_config = llm_config or LLMConfig()
        self.enable_repair = enable_repair
        self.enable_catalog = enable_catalog
        self.runtime_check = runtime_check

        # Logs and stage tracking
        self.logs: List[str] = []
        self.stages_passed: List[str] = []
        self.input_validation: List[str] = []
        self.validator_results: Dict[str, Dict[str, Any]] = {}
        self.failures_flat: List[Dict[str, Any]] = []
        self.pipeline_stats: Dict[str, Dict[str, Any]] = {}

        # Initialize agents
        self.planner = PlannerAgent()
        self.llm_client = LLMClient(base_dir=base_dir, config=self.llm_config, logger=self.log)
        self.ir_agent = IRAgent(self.llm_client)
        self.bindings_agent = BindingsAgent(self.llm_client)
        self.repair_agent = RepairAgent(self.llm_client)
        self.codegen = CodeGenAgent()
        self.deploy = DeployAgent()

        # Load rules once
        self.rules_bundle = load_rules_bundle()

        # Initialize verifiers with rules
        plan_required_fields = ["app_name", "description", "version", "problem_type",
                                "components_outline", "links_outline"]
        self.schema_checker = SchemaChecker(
            ir_required_fields=self.rules_bundle["ir"]["required_fields"],
            bindings_required_fields=self.rules_bundle["bindings"]["required_fields"],
            plan_required_fields=plan_required_fields
        )
        self.boundary_checker = BoundaryChecker(
            forbidden_keywords=self.rules_bundle["ir"]["forbidden_keywords"]
        )
        self.coverage_checker = CoverageChecker()
        self.endpoint_checker = EndpointChecker()
        self.component_catalog_checker = ComponentCatalogChecker(base_dir)
        self.device_info_catalog_checker = DeviceInfoCatalogChecker(base_dir)
        self.ir_interface_checker = IRInterfaceChecker(self.component_catalog_checker)
        self.endpoint_matching_checker = EndpointMatchingChecker(load_endpoint_types(base_dir)["data"])
        self.cross_artifact_checker = CrossArtifactChecker()

        combined_rules_hash = stable_hash({
            "ir": self.rules_bundle["ir"]["hash"],
            "bindings": self.rules_bundle["bindings"]["hash"]
        })
        self.rules_ctx = {
            "rules_hash": combined_rules_hash,
            "case_id": self.case_id
        }
        schemas_dir = os.path.join(base_dir, "autopipeline", "schemas")
        self.schema_versions = {
            "plan_schema": sha256_of_file(os.path.join(schemas_dir, "plan_schema.json")),
            "ir_schema": sha256_of_file(os.path.join(schemas_dir, "ir_schema.json")),
            "bindings_schema": sha256_of_file(os.path.join(schemas_dir, "bindings_schema.json")),
        }
        self.catalog_hash = catalog_hashes(base_dir)

    def log(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

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
            "metrics": result.get("metrics", {})
        }
        self.validator_results[name] = entry

    def _record_stage(self, name: str, start_time: float, attempts: int, passed: bool):
        duration_ms = int((time.time() - start_time) * 1000)
        self.pipeline_stats[name] = {
            "pass": passed,
            "duration_ms": duration_ms,
            "attempts": attempts
        }

    def _skip_validator(self, name: str, warning: str):
        self._record_validator(name, {
            "pass": True,
            "failures": [],
            "warnings": [warning],
            "metrics": {}
        })

    @staticmethod
    def _failure_message(res: Dict[str, Any]) -> str:
        fails = res.get("failures", [])
        if not fails:
            return ""
        f = fails[0]
        if isinstance(f, FailureRecord):
            return f.message
        if isinstance(f, dict):
            return f.get("message", "")
        return str(f)

    def _runtime_compose_check(self, deploy_file: str):
        cmd = ["docker", "compose", "-f", deploy_file, "config"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            return {
                "pass": True,
                "failures": [],
                "warnings": ["docker not available; skipped runtime check"],
                "metrics": {}
            }
        if proc.returncode != 0:
            return {
                "pass": False,
                "failures": [{
                    "code": ErrorCode.E_RUNTIME_COMPOSE_CONFIG,
                    "stage": "runtime",
                    "checker": "RuntimeChecker",
                    "message": proc.stderr.strip() or "docker compose config failed"
                }],
                "warnings": [],
                "metrics": {}
            }

        # Optional up/down check
        up_proc = subprocess.run(["docker", "compose", "-f", deploy_file, "up", "-d"],
                                 capture_output=True, text=True, check=False)
        if up_proc.returncode != 0:
            return {
                "pass": False,
                "failures": [{
                    "code": ErrorCode.E_RUNTIME_COMPOSE_CONFIG,
                    "stage": "runtime",
                    "checker": "RuntimeChecker",
                    "message": up_proc.stderr.strip() or "docker compose up failed"
                }],
                "warnings": [],
                "metrics": {}
            }
        time.sleep(5)
        ps_proc = subprocess.run(["docker", "compose", "-f", deploy_file, "ps"],
                                 capture_output=True, text=True, check=False)
        warnings = []
        if ps_proc.returncode != 0:
            warnings.append(ps_proc.stderr.strip() or "docker compose ps failed")
        subprocess.run(["docker", "compose", "-f", deploy_file, "down"], capture_output=True, text=True, check=False)
        return {"pass": True, "failures": [], "warnings": warnings, "metrics": {}}

    def _validate_codegen(self, codegen_result: Dict[str, Any]) -> Dict[str, Any]:
        failures = []
        warnings = []
        generated = codegen_result.get("generated_files", {})
        for layer, path in generated.items():
            if not os.path.exists(path):
                failures.append({
                    "code": ErrorCode.E_UNKNOWN,
                    "stage": "codegen",
                    "checker": "CodeGenValidator",
                    "message": f"{layer} main.py missing"
                })
                continue
            try:
                py_compile.compile(path, doraise=True)
            except Exception as e:
                failures.append({
                    "code": ErrorCode.E_UNKNOWN,
                    "stage": "codegen",
                    "checker": "CodeGenValidator",
                    "message": f"{layer} main.py py_compile failed: {e}"
                })
        if not generated:
            failures.append({
                "code": ErrorCode.E_UNKNOWN,
                "stage": "codegen",
                "checker": "CodeGenValidator",
                "message": "No code generated"
            })
        return {"pass": len(failures) == 0, "failures": failures, "warnings": warnings, "metrics": {}}

    def run(self) -> Dict[str, Any]:
        """Run the complete pipeline"""

        start_time = time.time()
        self.log(f"Starting pipeline for case: {self.case_id}")

        # Ensure output directory exists
        ensure_dir(self.output_dir)

        # Step 1: Load inputs
        self.log("Step 1: Loading user problem and device info")
        user_problem, device_info = self._load_inputs()

        # Step 2: Generate Plan
        self.log("Step 2: Generating Plan (Planner Agent)")
        plan_start = time.time()
        plan_data = self._generate_and_validate_plan(user_problem, device_info)
        self._record_stage("plan", plan_start, attempts=1, passed=True)

        # Step 3: Generate IR
        self.log("Step 3: Generating IR (IR Agent)")
        ir_start = time.time()
        ir_data, ir_attempts = self._generate_and_validate_ir(plan_data, user_problem, device_info)
        self._record_stage("ir", ir_start, attempts=ir_attempts, passed=True)

        # Step 4: Generate Bindings
        self.log("Step 4: Generating Bindings (Bindings Agent)")
        bind_start = time.time()
        bindings_data, bind_attempts = self._generate_and_validate_bindings(ir_data, device_info)
        self._record_stage("bindings", bind_start, attempts=bind_attempts, passed=True)
        bindings_file = os.path.join(self.output_dir, "bindings.yaml")
        bindings_hash = sha256_of_file(bindings_file)

        # Step 5: Generate Code
        self.log("Step 5: Generating code skeletons (CodeGen)")
        codegen_start = time.time()
        codegen_result = self.codegen.generate_code(bindings_data, ir_data, self.output_dir,
                                                    bindings_hash, self.case_id)
        self.stages_passed.append("codegen")
        self._record_stage("codegen", codegen_start, attempts=1, passed=True)
        codegen_validator = self._validate_codegen(codegen_result)
        self._record_validator("code_generated", codegen_validator)

        # Step 6: Generate Deployment
        self.log("Step 6: Generating docker-compose.yml (Deploy)")
        deploy_start = time.time()
        deploy_file = self.deploy.generate_deployment(bindings_data, self.output_dir, bindings_hash)
        self.stages_passed.append("deploy")
        self._record_stage("deploy", deploy_start, attempts=1, passed=True)

        # Step 7: Run evaluation
        self.log("Step 7: Running evaluation")
        eval_start = time.time()
        eval_result = self._run_evaluation(plan_data, ir_data, device_info, bindings_data, codegen_result, deploy_file, bindings_hash, eval_start)

        # Step 8: Generate report
        from autopipeline.eval.report import generate_report
        report_path = generate_report(eval_result, self.output_dir)
        self.log(f"Saved report to {report_path}")

        # Step 9: Save run log
        self.log("Step 9: Saving run log")
        self._save_run_log()

        elapsed_time = time.time() - start_time
        self.log(f"Pipeline completed in {elapsed_time:.2f} seconds")

        return eval_result

    def _load_inputs(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Load user problem and device info"""
        try:
            user_problem = load_json(os.path.join(self.case_dir, "user_problem.json"))
            device_info = load_json(os.path.join(self.case_dir, "device_info.json"))
            self.log("Successfully loaded input files")
            # Schema validation
            up_result = self.schema_checker.validate_user_problem(user_problem)
            di_result = self.schema_checker.validate_device_info(device_info)
            self._record_validator("user_problem_schema", up_result)
            self._record_validator("device_info_schema", di_result)
            self.input_validation = []
            if up_result["warnings"]:
                self.input_validation.extend([f"UserProblem warning: {w}" for w in up_result["warnings"]])
            if not up_result["pass"]:
                raise ValueError(up_result["failures"][0]["message"])
            if not di_result["pass"]:
                raise ValueError(di_result["failures"][0]["message"])
            # Catalog validation for device_info
            if self.enable_catalog:
                di_catalog_result = self.device_info_catalog_checker.check(device_info)
                self._record_validator("device_info_catalog", di_catalog_result)
                if di_catalog_result["warnings"]:
                    self.input_validation.extend([f"DeviceInfo warning: {w}" for w in di_catalog_result["warnings"]])
                if not di_catalog_result["pass"]:
                    raise ValueError(di_catalog_result["failures"][0]["message"])
            else:
                self._skip_validator("device_info_catalog", "Skipped catalog validation (--no-catalog)")
            return user_problem, device_info
        except Exception as e:
            self.log(f"Error loading inputs: {str(e)}", "ERROR")
            raise

    def _generate_and_validate_plan(self, user_problem: Dict[str, Any],
                                    device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate plan and validate schema"""
        plan_data = self.planner.generate_plan(user_problem, device_info)

        res = self.schema_checker.validate_plan(plan_data)
        self._record_validator("plan_schema", res)
        if not res["pass"]:
            first_msg = res["failures"][0]["message"] if res["failures"] else "Plan validation failed"
            self.log(f"Plan schema validation failed: {first_msg}", "ERROR")
            raise ValueError("Failed to generate valid plan")

        plan_file = os.path.join(self.output_dir, "plan.json")
        save_json(plan_data, plan_file)
        self.log(f"Saved Plan to {plan_file}")
        self.stages_passed.append("plan")
        return plan_data

    def _generate_and_validate_ir(self, plan_data: Dict[str, Any], user_problem: Dict[str, Any],
                                  device_info: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Generate IR with auto-repair loop (max 3 attempts)"""

        ir_data = None
        last_error = ""
        attempts_used = 0
        max_attempts = 1 if not self.enable_repair else 3
        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            self.log(f"IR generation attempt {attempt}/3")

            if attempt == 1:
                ir_data = self.ir_agent.generate_ir(plan_data, user_problem, device_info,
                                                    self.rules_ctx, self.schema_versions)
            else:
                ir_data = self.repair_agent.repair_ir(ir_data, last_error, device_info,
                                                      self.rules_ctx, self.schema_versions)

            schema_res = self.schema_checker.validate_ir(ir_data)
            self._record_validator("ir_schema", schema_res)
            if not schema_res["pass"]:
                last_error = self._failure_message(schema_res) or "IR schema failed"
                self.log(f"IR schema validation failed: {last_error}", "WARNING")
                continue

            boundary_res = self.boundary_checker.check_ir(ir_data)
            self._record_validator("ir_boundary", boundary_res)
            if not boundary_res["pass"]:
                last_error = self._failure_message(boundary_res) or "IR boundary failed"
                self.log(f"IR boundary check failed: {last_error}", "WARNING")
                continue

            if self.enable_catalog:
                comp_res = self.component_catalog_checker.check_ir(ir_data)
                self._record_validator("ir_component_catalog", comp_res)
                if not comp_res["pass"]:
                    last_error = self._failure_message(comp_res) or "IR catalog failed"
                    self.log(f"IR component catalog check failed: {last_error}", "WARNING")
                    continue

                iface_res = self.ir_interface_checker.check(ir_data)
                self._record_validator("ir_interface", iface_res)
                if not iface_res["pass"]:
                    last_error = self._failure_message(iface_res) or "IR interface failed"
                    self.log(f"IR interface check failed: {last_error}", "WARNING")
                    continue
            else:
                self._skip_validator("ir_component_catalog", "Skipped catalog validation (--no-catalog)")
                self._skip_validator("ir_interface", "Skipped catalog validation (--no-catalog)")

            self.log("IR validation passed")
            break

        else:
            self.log("IR generation failed after 3 attempts", "ERROR")
            raise ValueError("Failed to generate valid IR")

        ir_file = os.path.join(self.output_dir, "ir.yaml")
        save_yaml(ir_data, ir_file)
        self.log(f"Saved IR to {ir_file}")
        self.stages_passed.append("ir")

        return ir_data, attempts_used

    def _generate_and_validate_bindings(self, ir_data: Dict[str, Any],
                                        device_info: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Generate Bindings with auto-repair loop (max 3 attempts)"""

        bindings_data = None
        last_error = ""
        attempts_used = 0
        max_attempts = 1 if not self.enable_repair else 3
        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            self.log(f"Bindings generation attempt {attempt}/3")

            if attempt == 1:
                bindings_data = self.bindings_agent.generate_bindings(ir_data, device_info,
                                                                      self.rules_ctx, self.schema_versions)
            else:
                bindings_data = self.repair_agent.repair_bindings(bindings_data, last_error,
                                                                  ir_data, device_info,
                                                                  self.rules_ctx, self.schema_versions)

            schema_res = self.schema_checker.validate_bindings(bindings_data)
            self._record_validator("bindings_schema", schema_res)
            if not schema_res["pass"]:
                last_error = self._failure_message(schema_res) or "Bindings schema failed"
                self.log(f"Bindings schema validation failed: {last_error}", "WARNING")
                continue

            coverage_res = self.coverage_checker.check_coverage(ir_data, bindings_data)
            self._record_validator("coverage", coverage_res)
            if not coverage_res["pass"]:
                last_error = self._failure_message(coverage_res) or "Coverage failed"
                self.log(f"Coverage check failed: {last_error}", "WARNING")
                continue

            endpoint_res = self.endpoint_checker.check_endpoints(bindings_data, device_info)
            self._record_validator("endpoint_legality", endpoint_res)
            if not endpoint_res["pass"]:
                last_error = self._failure_message(endpoint_res) or "Endpoint legality failed"
                self.log(f"Endpoint legality check failed: {last_error}", "WARNING")
                continue

            if self.enable_catalog:
                ep_match_res = self.endpoint_matching_checker.check(bindings_data, device_info)
                self._record_validator("endpoint_matching", ep_match_res)
                if not ep_match_res["pass"]:
                    last_error = self._failure_message(ep_match_res) or "Endpoint matching failed"
                    self.log(f"Endpoint matching check failed: {last_error}", "WARNING")
                    continue
            else:
                self._skip_validator("endpoint_matching", "Skipped catalog validation (--no-catalog)")

            cross_res = self.cross_artifact_checker.check(ir_data, bindings_data)
            self._record_validator("cross_artifact_consistency", cross_res)
            if not cross_res["pass"]:
                last_error = self._failure_message(cross_res) or "Cross artifact consistency failed"
                self.log(f"Cross-artifact check failed: {last_error}", "WARNING")
                continue

            self.log("Bindings validation passed")
            break

        else:
            self.log("Bindings generation failed after 3 attempts", "ERROR")
            raise ValueError("Failed to generate valid Bindings")

        bindings_file = os.path.join(self.output_dir, "bindings.yaml")
        save_yaml(bindings_data, bindings_file)
        self.log(f"Saved Bindings to {bindings_file}")
        self.stages_passed.append("bindings")

        return bindings_data, attempts_used

    def _run_evaluation(self, plan_data: Dict[str, Any], ir_data: Dict[str, Any], device_info: Dict[str, Any],
                        bindings_data: Dict[str, Any], codegen_result: Dict[str, Any],
                        deploy_file: str, bindings_hash: str, eval_start: float) -> Dict[str, Any]:
        """Run deterministic evaluation"""

        rules_version = {
            "ir_rules_hash": self.rules_bundle["ir"]["hash"],
            "bindings_rules_hash": self.rules_bundle["bindings"]["hash"],
            "ir_required_fields": len(self.rules_bundle["ir"]["required_fields"]),
            "ir_forbidden_keywords": len(self.rules_bundle["ir"]["forbidden_keywords"]),
            "bindings_required_fields": len(self.rules_bundle["bindings"]["required_fields"]),
            "bindings_forbidden_keywords": len(self.rules_bundle["bindings"]["forbidden_keywords"])
        }

        eval_result = {
            "case_id": self.case_id,
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "metrics": {},
            "overall_status": "PASS",
            "stages_passed": (self.stages_passed + ["eval"]),
            "rules_version": rules_version,
            "bindings_hash": bindings_hash,
            "catalog_hashes": self.catalog_hash,
            "validators": {},
            "failures_flat": [],
            "pipeline": {"stages": self.pipeline_stats},
            "llm": {
                "provider": self.llm_config.provider,
                "model": self.llm_config.model,
                "temperature": self.llm_config.temperature,
                "cache_dir": self.llm_config.cache_dir,
                "cache_enabled": self.llm_config.cache_enabled,
                "calls_total": self.llm_client.stats["calls_total"],
                "calls_by_stage": self.llm_client.stats["calls_by_stage"],
                "cache_hits": self.llm_client.stats["cache_hits"],
                "cache_misses": self.llm_client.stats["cache_misses"],
                "usage_tokens_total": self.llm_client.stats["usage_tokens_total"],
                "prompt_template_hashes": self.llm_client.stats["prompt_template_hashes"],
                "rules_hash": rules_version["ir_rules_hash"] + rules_version["bindings_rules_hash"],
                "schema_hashes": self.schema_versions,
            }
        }

        # Carry validators collected during generation
        eval_result["validators"] = self.validator_results
        eval_result["failures_flat"] = [f for res in self.validator_results.values() for f in res.get("failures", [])]

        # Code/deploy presence as simple validators
        def add_simple_validator(name: str, passed: bool, message: str, failures: List[Dict[str, Any]] = None):
            result = {
                "pass": passed,
                "failures": failures or [],
                "warnings": [],
                "metrics": {}
            }
            self._record_validator(name, result)

        code_failures = []
        if not codegen_result["generated_files"]:
            code_failures.append({"code": ErrorCode.E_UNKNOWN, "stage": "codegen", "checker": "CodeGenAgent",
                                  "message": codegen_result["summary"]})
        add_simple_validator("code_generated", bool(codegen_result["generated_files"]), codegen_result["summary"], code_failures)

        deploy_exists = os.path.exists(deploy_file)
        deploy_failures = [] if deploy_exists else [{"code": ErrorCode.E_RUNTIME_COMPOSE_CONFIG, "stage": "deploy",
                                                    "checker": "DeployAgent",
                                                    "message": f"docker-compose.yml missing at {deploy_file}"}]
        add_simple_validator("deploy_generated", deploy_exists, f"docker-compose.yml at {deploy_file}", deploy_failures)

        gen_checker = GenerationConsistencyChecker(bindings_hash, self.output_dir)
        gen_res = gen_checker.check()
        self._record_validator("generation_consistency", gen_res)
        eval_result["generated_manifest_present"] = os.path.exists(
            os.path.join(self.output_dir, "generated_code", "manifest.json"))
        eval_result["generation_consistency_pass"] = gen_res["pass"]

        if self.runtime_check:
            runtime_res = self._runtime_compose_check(deploy_file)
            self._record_validator("runtime_compose", runtime_res)
        else:
            self._skip_validator("runtime_compose", "Runtime check disabled")

        # Metrics
        components = ir_data.get('components', ir_data.get('entities', []))
        eval_result["metrics"]["num_components"] = len(components)
        eval_result["metrics"]["num_entities"] = len(components)
        eval_result["metrics"]["num_links"] = len(ir_data.get("links", []))
        eval_result["metrics"]["num_placements"] = len(bindings_data.get("placements", []))
        eval_result["metrics"]["num_layers"] = len(codegen_result["generated_files"])

        # Simplified checks (backward compatibility)
        for name in ["user_problem_schema", "device_info_schema", "device_info_catalog",
                     "plan_schema", "ir_schema", "ir_boundary", "ir_component_catalog", "ir_interface",
                     "bindings_schema", "coverage", "endpoint_legality", "endpoint_matching", "cross_artifact_consistency",
                     "code_generated", "deploy_generated", "generation_consistency", "runtime_compose"]:
            res = self.validator_results.get(name, {"pass": True, "failures": [], "warnings": []})
            msg = res["failures"][0]["message"] if res["failures"] else "OK"
            eval_result["checks"][name] = {"status": "PASS" if res.get("pass") else "FAIL", "message": msg}

        failed_checks = [k for k, v in eval_result["checks"].items() if v["status"] == "FAIL"]
        if failed_checks:
            eval_result["overall_status"] = "FAIL"
            eval_result["failed_checks"] = failed_checks

        eval_result["input_validation"] = self.input_validation

        eval_result["input_validation"] = self.input_validation

        # Refresh pipeline stages with eval duration included
        self._record_stage("eval", eval_start, attempts=1, passed=(eval_result.get("overall_status") == "PASS"))
        eval_result["pipeline"] = {"stages": self.pipeline_stats}
        eval_result["validators"] = self.validator_results
        eval_result["failures_flat"] = [f for res in self.validator_results.values() for f in res.get("failures", [])]

        eval_file = os.path.join(self.output_dir, "eval.json")
        save_json(eval_result, eval_file)
        self.log(f"Saved evaluation to {eval_file}")

        return eval_result

    def _save_run_log(self):
        """Save run log to file"""
        log_file = os.path.join(self.output_dir, "run.log")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.logs))
        self.log(f"Saved run log to {log_file}")
