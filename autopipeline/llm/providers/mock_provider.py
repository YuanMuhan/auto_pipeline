import os
from pathlib import Path
from typing import Optional, Dict, Any


class MockProvider:
    """Mock provider: reads pre-baked outputs from cases/<case_id>/mock or gold."""

    name = "mock"

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def call(self, *, case_id: str, stage: str, model: Optional[str], prompt: str,
             temperature: float = 0.0, max_tokens: Optional[int] = None, **_) -> Dict[str, Any]:
        stage_to_file = {
            "generate_ir": "ir.yaml",
            "generate_bindings": "bindings.yaml",
            "repair_ir": "repair_ir.yaml",
            "repair_bindings": "repair_bindings.yaml",
        }
        filename = stage_to_file.get(stage)
        if not filename:
            raise ValueError(f"Unsupported stage for mock provider: {stage}")

        search_paths = [
            self.base_dir / "cases" / case_id / "mock" / filename,
            self.base_dir / "cases" / case_id / "gold" / filename,
        ]
        for path in search_paths:
            if path.exists():
                return {"text": path.read_text(encoding="utf-8"), "usage": None}
        raise FileNotFoundError(
            f"Mock/gold output not found for stage '{stage}'. "
            f"Checked: {', '.join(str(p) for p in search_paths)}"
        )
