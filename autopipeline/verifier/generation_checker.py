"""Generation consistency checker - ensures generated artifacts trace back to bindings"""

import json
import os

from autopipeline.eval.error_codes import ErrorCode, failure


class GenerationConsistencyChecker:
    """Check manifest/main.py/docker-compose traceability against bindings hash"""

    def __init__(self, bindings_hash: str, output_dir: str):
        self.bindings_hash = bindings_hash
        self.output_dir = output_dir

    def check(self):
        failures = []
        manifest_path = os.path.join(self.output_dir, "generated_code", "manifest.json")
        compose_path = os.path.join(self.output_dir, "docker-compose.yml")
        main_paths = [
            os.path.join(self.output_dir, "generated_code", layer, "main.py")
            for layer in ("cloud", "edge", "device")
        ]

        if not os.path.exists(manifest_path):
            failures.append(failure(ErrorCode.E_UNKNOWN, "codegen", "GenerationConsistencyChecker",
                                    "Manifest file missing"))
            return {"pass": False, "failures": failures, "warnings": [], "metrics": {}}

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception as e:
            failures.append(failure(ErrorCode.E_UNKNOWN, "codegen", "GenerationConsistencyChecker",
                                    f"Failed to read manifest: {str(e)}"))
            return {"pass": False, "failures": failures, "warnings": [], "metrics": {}}

        if manifest.get("bindings_hash") != self.bindings_hash:
            failures.append(failure(ErrorCode.E_UNKNOWN, "codegen", "GenerationConsistencyChecker",
                                    "bindings_hash mismatch in manifest",
                                    {"manifest_bindings_hash": manifest.get("bindings_hash"),
                                     "expected": self.bindings_hash}))

        main_has_hash = False
        for path in main_paths:
            if not os.path.exists(path):
                continue
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if self.bindings_hash in content:
                    main_has_hash = True
        if not main_has_hash:
            failures.append(failure(ErrorCode.E_UNKNOWN, "codegen", "GenerationConsistencyChecker",
                                    "bindings_hash not found in any main.py"))

        if not os.path.exists(compose_path):
            failures.append(failure(ErrorCode.E_RUNTIME_COMPOSE_CONFIG, "deploy", "GenerationConsistencyChecker",
                                    "docker-compose.yml missing"))
        else:
            with open(compose_path, 'r', encoding='utf-8') as f:
                compose_content = f.read()
                if self.bindings_hash not in compose_content:
                    failures.append(failure(ErrorCode.E_RUNTIME_COMPOSE_CONFIG, "deploy", "GenerationConsistencyChecker",
                                            "bindings_hash not found in docker-compose.yml"))

        return {"pass": len(failures) == 0, "failures": failures, "warnings": [], "metrics": {}}
