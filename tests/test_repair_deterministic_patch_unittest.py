import unittest

import yaml

from autopipeline.repair.deterministic_patch import apply_deterministic_patch
from autopipeline.eval.validators_registry import build_validators


class TestDeterministicPatch(unittest.TestCase):
    def test_missing_component_bindings_stub_and_schema_core(self):
        raw_bindings = {
            "app_name": "demo",
            "version": "1.0",
        }
        ir = {
            "components": [
                {"id": "sensor1", "type": "unknown_sensor"},
                {"id": "logic1", "type": "rule_engine"},
            ]
        }
        hints = [{"code": "E_SCHEMA_BIND", "path": "component_bindings", "missing": "component_bindings"}]

        patched, actions = apply_deterministic_patch(raw_bindings, ir, hints)

        self.assertIn("component_bindings", patched)
        self.assertEqual(len(patched["component_bindings"]), len(ir["components"]))
        self.assertTrue(any("patch_component_bindings_stub" in a for a in actions))

        # validate with core schema
        v = build_validators(base_dir=".", enable_catalog=True)
        schema_checker = v["schema_checker"]
        res = schema_checker.validate_bindings(patched, gate_mode="core")
        self.assertTrue(res["pass"], res)

        # ensure YAML serializable
        yaml.safe_dump(patched)


if __name__ == "__main__":
    unittest.main()
