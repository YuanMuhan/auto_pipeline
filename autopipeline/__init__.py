"""AutoPipeline - Prompt-only multi-agent pipeline for Cloud-Edge-Device development"""

__version__ = "0.1.0"


def __getattr__(name):
    """Lazy exports for backward compatibility without eager imports."""
    if name == "LLMClient":
        from autopipeline.llm.llm_client import LLMClient
        return LLMClient
    if name == "load_catalog_types":
        from autopipeline.catalog.catalog_utils import load_catalog_types
        return load_catalog_types
    raise AttributeError(f"module 'autopipeline' has no attribute {name}")


__all__ = ["__version__"]
