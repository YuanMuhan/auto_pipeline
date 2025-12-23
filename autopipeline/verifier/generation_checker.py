"""Generation consistency checker - ensures generated artifacts trace back to bindings"""

import json
import os
from typing import Dict, Tuple
from autopipeline.utils import sha256_of_file


class GenerationConsistencyChecker:
    """Check manifest/main.py/docker-compose traceability against bindings hash"""

    def __init__(self, bindings_hash: str, output_dir: str):
        self.bindings_hash = bindings_hash
        self.output_dir = output_dir

    def check(self) -> Tuple[bool, str]:
        manifest_path = os.path.join(self.output_dir, "generated_code", "manifest.json")
        compose_path = os.path.join(self.output_dir, "docker-compose.yml")
        main_paths = [
            os.path.join(self.output_dir, "generated_code", layer, "main.py")
            for layer in ("cloud", "edge", "device")
        ]

        if not os.path.exists(manifest_path):
            return False, "Manifest file missing"

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception as e:
            return False, f"Failed to read manifest: {str(e)}"

        if manifest.get("bindings_hash") != self.bindings_hash:
            return False, "bindings_hash mismatch in manifest"

        # Check main.py comments for hash
        main_has_hash = False
        for path in main_paths:
            if not os.path.exists(path):
                continue
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if self.bindings_hash in content:
                    main_has_hash = True
        if not main_has_hash:
            return False, "bindings_hash not found in any main.py"

        # Check docker-compose for hash
        if not os.path.exists(compose_path):
            return False, "docker-compose.yml missing"
        with open(compose_path, 'r', encoding='utf-8') as f:
            compose_content = f.read()
            if self.bindings_hash not in compose_content:
                return False, "bindings_hash not found in docker-compose.yml"

        return True, "Generation consistency passed"
