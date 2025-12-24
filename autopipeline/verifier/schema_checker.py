"""Schema validation for IR and Bindings"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, Tuple, List


class SchemaChecker:
    """Validate data against JSON schemas"""

    def __init__(self, ir_required_fields: List[str], bindings_required_fields: List[str],
                 plan_required_fields: List[str]):
        schema_dir = Path(__file__).parent.parent / "schemas"
        with open(schema_dir / "plan_schema.json", 'r') as f:
            self.plan_schema = json.load(f)
        with open(schema_dir / "ir_schema.json", 'r') as f:
            self.ir_schema = json.load(f)
        with open(schema_dir / "bindings_schema.json", 'r') as f:
            self.bindings_schema = json.load(f)
        with open(schema_dir / "user_problem_schema.json", 'r') as f:
            self.user_problem_schema = json.load(f)
        with open(schema_dir / "device_info_schema.json", 'r') as f:
            self.device_info_schema = json.load(f)
        self.ir_required_fields = ir_required_fields
        self.bindings_required_fields = bindings_required_fields
        self.plan_required_fields = plan_required_fields

    def _check_required_fields(self, data: Dict[str, Any], required_fields: List[str], name: str) -> Tuple[bool, str]:
        missing = [field for field in required_fields if field not in data]
        if missing:
            return False, f"{name} missing required fields: {', '.join(missing)}"
        return True, f"{name} required fields present"

    def validate_plan(self, plan_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Plan against schema"""
        try:
            jsonschema.validate(instance=plan_data, schema=self.plan_schema)
            ok, msg = self._check_required_fields(plan_data, self.plan_required_fields, "Plan")
            if not ok:
                return False, msg
            return True, "Plan schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"Plan schema validation failed: {e.message}"
        except Exception as e:
            return False, f"Plan schema validation error: {str(e)}"

    def validate_ir(self, ir_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate IR against schema"""
        try:
            jsonschema.validate(instance=ir_data, schema=self.ir_schema)
            ok, msg = self._check_required_fields(ir_data, self.ir_required_fields, "IR")
            if not ok:
                return False, msg
            return True, "IR schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"IR schema validation failed: {e.message}"
        except Exception as e:
            return False, f"IR schema validation error: {str(e)}"

    def validate_bindings(self, bindings_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Bindings against schema"""
        try:
            jsonschema.validate(instance=bindings_data, schema=self.bindings_schema)
            ok, msg = self._check_required_fields(bindings_data, self.bindings_required_fields, "Bindings")
            if not ok:
                return False, msg
            return True, "Bindings schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"Bindings schema validation failed: {e.message}"
        except Exception as e:
            return False, f"Bindings schema validation error: {str(e)}"

    def validate_user_problem(self, user_problem: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            jsonschema.validate(instance=user_problem, schema=self.user_problem_schema)
            missing_soft = []
            for soft_field in ["id", "title", "target"]:
                if soft_field not in user_problem:
                    missing_soft.append(soft_field)
            if missing_soft:
                return True, f"UserProblem soft-missing fields: {', '.join(missing_soft)}"
            return True, "UserProblem schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"UserProblem schema validation failed: {e.message}"
        except Exception as e:
            return False, f"UserProblem schema validation error: {str(e)}"

    def validate_device_info(self, device_info: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            jsonschema.validate(instance=device_info, schema=self.device_info_schema)
            return True, "DeviceInfo schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"DeviceInfo schema validation failed: {e.message}"
        except Exception as e:
            return False, f"DeviceInfo schema validation error: {str(e)}"
