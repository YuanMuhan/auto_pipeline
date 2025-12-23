"""Schema validation for IR and Bindings"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, Tuple


class SchemaChecker:
    """Validate data against JSON schemas"""

    def __init__(self):
        schema_dir = Path(__file__).parent.parent / "schemas"
        with open(schema_dir / "ir_schema.json", 'r') as f:
            self.ir_schema = json.load(f)
        with open(schema_dir / "bindings_schema.json", 'r') as f:
            self.bindings_schema = json.load(f)

    def validate_ir(self, ir_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate IR against schema"""
        try:
            jsonschema.validate(instance=ir_data, schema=self.ir_schema)
            return True, "IR schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"IR schema validation failed: {e.message}"
        except Exception as e:
            return False, f"IR schema validation error: {str(e)}"

    def validate_bindings(self, bindings_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Bindings against schema"""
        try:
            jsonschema.validate(instance=bindings_data, schema=self.bindings_schema)
            return True, "Bindings schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"Bindings schema validation failed: {e.message}"
        except Exception as e:
            return False, f"Bindings schema validation error: {str(e)}"
