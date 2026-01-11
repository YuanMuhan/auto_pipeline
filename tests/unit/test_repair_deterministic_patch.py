import unittest
import yaml

from autopipeline.repair.deterministic_patch import apply_deterministic_patch


class TestDeterministicPatchLegacy(unittest.TestCase):
    def test_apply_deterministic_patch_adds_stub_component_bindings(self):
        raw_bindings = {
            "app_name": "demo",
            "version": "1.0",
            # component_bindings intentionally missing
        }
        ir = {
            "components": [
                {"id": "sensor1", "type": "unknown_sensor"},
                {"id": "logic1", "type": "rule_engine"},
            ]
        }
        hints = [{"path": "component_bindings", "missing": "component_bindings", "code": "E_SCHEMA_BIND"}]

        patched, actions = apply_deterministic_patch(raw_bindings, ir, hints)

        self.assertIn("component_bindings", patched)
        self.assertIsInstance(patched["component_bindings"], list)
        self.assertEqual(len(patched["component_bindings"]), len(ir["components"]))
        self.assertTrue(any("patch_component_bindings_stub" in a for a in actions))
        yaml.safe_dump(patched)


if __name__ == "__main__":
    unittest.main()
