"""Main pipeline runner - orchestrates the entire workflow"""

import os
import time
from datetime import datetime
from typing import Dict, Any, Tuple, List

from autopipeline.utils import load_json, save_json, save_yaml, ensure_dir
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
from autopipeline.verifier.generation_checker import GenerationConsistencyChecker
from autopipeline.utils import sha256_of_file


class PipelineRunner:
    """Orchestrates the entire AutoPipeline workflow"""

    def __init__(self, case_id: str, base_dir: str = "."):
        self.case_id = case_id
        self.base_dir = base_dir
        self.case_dir = os.path.join(base_dir, "cases", case_id)
        self.output_dir = os.path.join(base_dir, "outputs", case_id)

        # Initialize agents
        self.planner = PlannerAgent()
        self.ir_agent = IRAgent()
        self.bindings_agent = BindingsAgent()
        self.repair_agent = RepairAgent()
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

        # Logs and stage tracking
        self.logs: List[str] = []
        self.stages_passed: List[str] = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

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
        plan_data = self._generate_and_validate_plan(user_problem, device_info)

        # Step 3: Generate IR
        self.log("Step 3: Generating IR (IR Agent)")
        ir_data = self._generate_and_validate_ir(plan_data, user_problem, device_info)

        # Step 4: Generate Bindings
        self.log("Step 4: Generating Bindings (Bindings Agent)")
        bindings_data = self._generate_and_validate_bindings(ir_data, device_info)
        bindings_file = os.path.join(self.output_dir, "bindings.yaml")
        bindings_hash = sha256_of_file(bindings_file)

        # Step 5: Generate Code
        self.log("Step 5: Generating code skeletons (CodeGen)")
        codegen_result = self.codegen.generate_code(bindings_data, ir_data, self.output_dir,
                                                    bindings_hash, self.case_id)
        self.stages_passed.append("codegen")

        # Step 6: Generate Deployment
        self.log("Step 6: Generating docker-compose.yml (Deploy)")
        deploy_file = self.deploy.generate_deployment(bindings_data, self.output_dir, bindings_hash)
        self.stages_passed.append("deploy")

        # Step 7: Run evaluation
        self.log("Step 7: Running evaluation")
        eval_result = self._run_evaluation(plan_data, ir_data, bindings_data, codegen_result, deploy_file, bindings_hash)

        # Step 8: Save run log
        self.log("Step 8: Saving run log")
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
            return user_problem, device_info
        except Exception as e:
            self.log(f"Error loading inputs: {str(e)}", "ERROR")
            raise

    def _generate_and_validate_plan(self, user_problem: Dict[str, Any],
                                    device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate plan and validate schema"""
        plan_data = self.planner.generate_plan(user_problem, device_info)

        valid, msg = self.schema_checker.validate_plan(plan_data)
        if not valid:
            self.log(f"Plan schema validation failed: {msg}", "ERROR")
            raise ValueError("Failed to generate valid plan")

        plan_file = os.path.join(self.output_dir, "plan.json")
        save_json(plan_data, plan_file)
        self.log(f"Saved Plan to {plan_file}")
        self.stages_passed.append("plan")
        return plan_data

    def _generate_and_validate_ir(self, plan_data: Dict[str, Any], user_problem: Dict[str, Any],
                                  device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate IR with auto-repair loop (max 3 attempts)"""

        ir_data = None
        last_error = ""
        for attempt in range(1, 4):
            self.log(f"IR generation attempt {attempt}/3")

            # Generate IR
            if attempt == 1:
                ir_data = self.ir_agent.generate_ir(plan_data, user_problem, device_info)
            else:
                # Repair from previous attempt
                ir_data = self.repair_agent.repair_ir(ir_data, last_error, device_info)

            # Validate schema
            valid, msg = self.schema_checker.validate_ir(ir_data)
            if not valid:
                self.log(f"IR schema validation failed: {msg}", "WARNING")
                last_error = msg
                continue

            # Validate boundary
            valid, msg = self.boundary_checker.check_ir(ir_data)
            if not valid:
                self.log(f"IR boundary check failed: {msg}", "WARNING")
                last_error = msg
                continue

            # All checks passed
            self.log("IR validation passed")
            break

        else:
            self.log("IR generation failed after 3 attempts", "ERROR")
            raise ValueError("Failed to generate valid IR")

        # Save IR (yaml)
        ir_file = os.path.join(self.output_dir, "ir.yaml")
        save_yaml(ir_data, ir_file)
        self.log(f"Saved IR to {ir_file}")
        self.stages_passed.append("ir")

        return ir_data

    def _generate_and_validate_bindings(self, ir_data: Dict[str, Any],
                                        device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Bindings with auto-repair loop (max 3 attempts)"""

        bindings_data = None
        last_error = ""
        for attempt in range(1, 4):
            self.log(f"Bindings generation attempt {attempt}/3")

            # Generate Bindings
            if attempt == 1:
                bindings_data = self.bindings_agent.generate_bindings(ir_data, device_info)
            else:
                # Repair from previous attempt
                bindings_data = self.repair_agent.repair_bindings(bindings_data, last_error,
                                                                  ir_data, device_info)

            # Validate schema
            valid, msg = self.schema_checker.validate_bindings(bindings_data)
            if not valid:
                self.log(f"Bindings schema validation failed: {msg}", "WARNING")
                last_error = msg
                continue

            # Validate coverage
            valid, msg = self.coverage_checker.check_coverage(ir_data, bindings_data)
            if not valid:
                self.log(f"Coverage check failed: {msg}", "WARNING")
                last_error = msg
                continue

            # Validate endpoint legality
            valid, msg = self.endpoint_checker.check_endpoints(bindings_data, device_info)
            if not valid:
                self.log(f"Endpoint legality check failed: {msg}", "WARNING")
                last_error = msg
                continue

            # All checks passed
            self.log("Bindings validation passed")
            break

        else:
            self.log("Bindings generation failed after 3 attempts", "ERROR")
            raise ValueError("Failed to generate valid Bindings")

        # Save Bindings
        bindings_file = os.path.join(self.output_dir, "bindings.yaml")
        save_yaml(bindings_data, bindings_file)
        self.log(f"Saved Bindings to {bindings_file}")
        self.stages_passed.append("bindings")

        return bindings_data

    def _run_evaluation(self, plan_data: Dict[str, Any], ir_data: Dict[str, Any], bindings_data: Dict[str, Any],
                        codegen_result: Dict[str, Any], deploy_file: str, bindings_hash: str) -> Dict[str, Any]:
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
            "bindings_hash": bindings_hash
        }

        # Check 0: Plan validity
        plan_valid, plan_msg = self.schema_checker.validate_plan(plan_data)
        eval_result["checks"]["plan_schema"] = {"status": "PASS" if plan_valid else "FAIL", "message": plan_msg}

        # Check 1: IR validity
        ir_valid, ir_msg = self.schema_checker.validate_ir(ir_data)
        eval_result["checks"]["ir_schema"] = {"status": "PASS" if ir_valid else "FAIL", "message": ir_msg}

        ir_boundary_valid, ir_boundary_msg = self.boundary_checker.check_ir(ir_data)
        eval_result["checks"]["ir_boundary"] = {"status": "PASS" if ir_boundary_valid else "FAIL",
                                                 "message": ir_boundary_msg}

        # Check 2: Bindings validity
        bindings_valid, bindings_msg = self.schema_checker.validate_bindings(bindings_data)
        eval_result["checks"]["bindings_schema"] = {"status": "PASS" if bindings_valid else "FAIL",
                                                     "message": bindings_msg}

        # Check 3: Coverage
        coverage_valid, coverage_msg = self.coverage_checker.check_coverage(ir_data, bindings_data)
        eval_result["checks"]["coverage"] = {"status": "PASS" if coverage_valid else "FAIL",
                                             "message": coverage_msg}

        # Check 4: Files generated
        eval_result["checks"]["code_generated"] = {
            "status": "PASS" if codegen_result["generated_files"] else "FAIL",
            "message": codegen_result["summary"]
        }

        eval_result["checks"]["deploy_generated"] = {
            "status": "PASS" if os.path.exists(deploy_file) else "FAIL",
            "message": f"docker-compose.yml at {deploy_file}"
        }

        # Check 5: Generation consistency
        gen_checker = GenerationConsistencyChecker(bindings_hash, self.output_dir)
        gen_valid, gen_msg = gen_checker.check()
        eval_result["checks"]["generation_consistency"] = {"status": "PASS" if gen_valid else "FAIL",
                                                           "message": gen_msg}
        eval_result["generated_manifest_present"] = os.path.exists(
            os.path.join(self.output_dir, "generated_code", "manifest.json"))
        eval_result["generation_consistency_pass"] = gen_valid

        # Metrics
        components = ir_data.get('components', ir_data.get('entities', []))  # Support both
        eval_result["metrics"]["num_components"] = len(components)
        eval_result["metrics"]["num_entities"] = len(components)  # Backward compatibility
        eval_result["metrics"]["num_links"] = len(ir_data.get("links", []))
        eval_result["metrics"]["num_placements"] = len(bindings_data.get("placements", []))
        eval_result["metrics"]["num_layers"] = len(codegen_result["generated_files"])

        # Overall status
        failed_checks = [k for k, v in eval_result["checks"].items() if v["status"] == "FAIL"]
        if failed_checks:
            eval_result["overall_status"] = "FAIL"
            eval_result["failed_checks"] = failed_checks

        # Save evaluation result
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
