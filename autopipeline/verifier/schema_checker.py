"""Schema validation for plan/IR/Bindings/UserProblem/DeviceInfo with structured failures."""

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, List

from autopipeline.eval.error_codes import ErrorCode, FailureRecord, failure


class SchemaChecker:
    """Validate data against JSON schemas and required fields."""

    def __init__(self, ir_required_fields: List[str], bindings_required_fields: List[str],
                 plan_required_fields: List[str]):
        schema_dir = Path(__file__).parent.parent / "schemas"
        with open(schema_dir / "plan_schema.json", 'r') as f:
            self.plan_schema = json.load(f)
        with open(schema_dir / "ir_schema.json", 'r') as f:
            self.ir_schema = json.load(f)
        with open(schema_dir / "bindings_schema_full.json", 'r') as f:
            self.bindings_schema_full = json.load(f)
        with open(schema_dir / "bindings_schema_core.json", 'r') as f:
            self.bindings_schema_core = json.load(f)
        with open(schema_dir / "user_problem_schema.json", 'r') as f:
            self.user_problem_schema = json.load(f)
        with open(schema_dir / "device_info_schema.json", 'r') as f:
            self.device_info_schema = json.load(f)
        self.ir_required_fields = ir_required_fields
        self.bindings_required_fields = bindings_required_fields
        self.plan_required_fields = plan_required_fields

    def _result(self, ok: bool, failures: List[FailureRecord], warnings: List[str] = None):
        return {
            "pass": ok,
            "failures": failures,
            "warnings": warnings or [],
            "metrics": {}
        }

    def _check_required_fields(self, data: Dict[str, Any], required_fields: List[str], name: str,
                               code: str, stage: str, checker: str) -> List[FailureRecord]:
        missing = [field for field in required_fields if field not in data]
        if missing:
            return [failure(code, stage, checker, f"{name} missing required fields: {', '.join(missing)}",
                            {"missing": missing})]
        return []

    def validate_plan(self, plan_data: Dict[str, Any]):
        """Validate Plan against schema"""
        failures: List[FailureRecord] = []
        warnings: List[str] = []
        try:
            jsonschema.validate(instance=plan_data, schema=self.plan_schema)
            failures.extend(self._check_required_fields(plan_data, self.plan_required_fields, "Plan",
                                                        ErrorCode.E_SCHEMA_UP, "plan", "SchemaChecker"))
        except jsonschema.ValidationError as e:
            failures.append(failure(ErrorCode.E_SCHEMA_UP, "plan", "SchemaChecker",
                                    f"Plan schema validation failed: {e.message}",
                                    {"path": list(e.path)}))
        except Exception as e:
            failures.append(failure(ErrorCode.E_SCHEMA_UP, "plan", "SchemaChecker",
                                    f"Plan schema validation error: {str(e)}"))
        return self._result(len(failures) == 0, failures, warnings)

    def validate_ir(self, ir_data: Dict[str, Any]):
        """Validate IR against schema"""
        failures: List[FailureRecord] = []
        try:
            jsonschema.validate(instance=ir_data, schema=self.ir_schema)
            failures.extend(self._check_required_fields(ir_data, self.ir_required_fields, "IR",
                                                        ErrorCode.E_SCHEMA_IR, "ir", "SchemaChecker"))
        except jsonschema.ValidationError as e:
            failures.append(failure(ErrorCode.E_SCHEMA_IR, "ir", "SchemaChecker",
                                    f"IR schema validation failed: {e.message}",
                                    {"path": list(e.path)}))
        except Exception as e:
            failures.append(failure(ErrorCode.E_SCHEMA_IR, "ir", "SchemaChecker",
                                    f"IR schema validation error: {str(e)}"))
        return self._result(len(failures) == 0, failures)

    def validate_bindings(self, bindings_data: Dict[str, Any], gate_mode: str = "core"):
        """Validate Bindings against schema"""
        failures: List[FailureRecord] = []
        try:
            schema = self.bindings_schema_core if str(gate_mode).lower() == "core" else self.bindings_schema_full
            jsonschema.validate(instance=bindings_data, schema=schema)
            failures.extend(self._check_required_fields(bindings_data, self.bindings_required_fields, "Bindings",
                                                        ErrorCode.E_SCHEMA_BIND, "bindings", "SchemaChecker"))
        except jsonschema.ValidationError as e:
            failures.append(failure(ErrorCode.E_SCHEMA_BIND, "bindings", "SchemaChecker",
                                    f"Bindings schema validation failed: {e.message}",
                                    {"path": list(e.path)}))
        except Exception as e:
            failures.append(failure(ErrorCode.E_SCHEMA_BIND, "bindings", "SchemaChecker",
                                    f"Bindings schema validation error: {str(e)}"))
        return self._result(len(failures) == 0, failures)

    def validate_user_problem(self, user_problem: Dict[str, Any]):
        failures: List[FailureRecord] = []
        warnings: List[str] = []
        try:
            jsonschema.validate(instance=user_problem, schema=self.user_problem_schema)
            missing_soft = [fld for fld in ["id", "title", "target"] if fld not in user_problem]
            if missing_soft:
                warnings.append(f"UserProblem soft-missing fields: {', '.join(missing_soft)}")
        except jsonschema.ValidationError as e:
            failures.append(failure(ErrorCode.E_SCHEMA_UP, "inputs", "SchemaChecker",
                                    f"UserProblem schema validation failed: {e.message}",
                                    {"path": list(e.path)}))
        except Exception as e:
            failures.append(failure(ErrorCode.E_SCHEMA_UP, "inputs", "SchemaChecker",
                                    f"UserProblem schema validation error: {str(e)}"))
        return self._result(len(failures) == 0, failures, warnings)

    def validate_device_info(self, device_info: Dict[str, Any]):
        failures: List[FailureRecord] = []
        try:
            jsonschema.validate(instance=device_info, schema=self.device_info_schema)
        except jsonschema.ValidationError as e:
            failures.append(failure(ErrorCode.E_SCHEMA_DI, "inputs", "SchemaChecker",
                                    f"DeviceInfo schema validation failed: {e.message}",
                                    {"path": list(e.path)}))
        except Exception as e:
            failures.append(failure(ErrorCode.E_SCHEMA_DI, "inputs", "SchemaChecker",
                                    f"DeviceInfo schema validation error: {str(e)}"))
        return self._result(len(failures) == 0, failures)
