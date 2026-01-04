"""Catalog helper utilities."""

import yaml
from pathlib import Path
from typing import Set


def load_catalog_types(index_path: Path) -> Set[str]:
    """Load all component type_name entries from catalog index/profile files."""
    types: Set[str] = set()
    if not index_path.exists():
        return types
    index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    components = index.get("components") or []
    for comp in components:
        ref = comp.get("file") or comp.get("path")
        if not ref:
            continue
        profile_path = (index_path.parent / ref).resolve()
        if not profile_path.exists():
            continue
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        tname = profile.get("type_name")
        if tname:
            types.add(str(tname))
    return types
