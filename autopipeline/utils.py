"""Utility functions for AutoPipeline"""

import json
import yaml
import os
from pathlib import Path
from typing import Any, Dict
import hashlib


def load_json(filepath: str) -> Dict[str, Any]:
    """Load JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], filepath: str, indent: int = 2) -> None:
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_yaml(filepath: str) -> Dict[str, Any]:
    """Load YAML file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict[str, Any], filepath: str) -> None:
    """Save data to YAML file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def ensure_dir(path: str) -> None:
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)


def sha256_of_text(text: str) -> str:
    """Compute SHA256 hash of given text"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha256_of_file(filepath: str) -> str:
    """Compute SHA256 hash of a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return sha256_of_text(content)


def sha256_of_dict(data: Dict[str, Any]) -> str:
    """Compute SHA256 hash of a dict by stable JSON dump"""
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return sha256_of_text(serialized)
