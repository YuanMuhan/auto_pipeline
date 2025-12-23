import hashlib
import json
from typing import Any


def stable_dumps(obj: Any) -> str:
    """Stable JSON serialization for hashing."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def stable_hash(obj: Any) -> str:
    """SHA256 hash of a Python object using stable JSON serialization."""
    return hashlib.sha256(stable_dumps(obj).encode("utf-8")).hexdigest()


def text_hash(text: str) -> str:
    """SHA256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
