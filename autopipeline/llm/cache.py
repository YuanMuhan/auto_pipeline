import json
import os
from datetime import datetime
from typing import Any, Dict, Tuple


class LLMDiskCache:
    def __init__(self, cache_dir: str = ".cache/llm", enabled: bool = True):
        self.cache_dir = cache_dir
        self.enabled = enabled
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)

    def get(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        if not self.enabled:
            return False, {}
        path = os.path.join(self.cache_dir, f"{key}.json")
        if not os.path.exists(path):
            return False, {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return True, json.load(f)
        except Exception:
            return False, {}

    def set(self, key: str, payload: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        os.makedirs(self.cache_dir, exist_ok=True)
        path = os.path.join(self.cache_dir, f"{key}.json")
        payload = dict(payload)
        payload["created_at"] = datetime.now().isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
