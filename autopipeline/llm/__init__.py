"""LLM module exports."""

# Avoid eager import to reduce circular dependencies; import LLMClient where needed
from .types import LLMConfig  # noqa: F401


def __getattr__(name):
    if name == "LLMClient":
        from autopipeline.llm.llm_client import LLMClient
        return LLMClient
    raise AttributeError(name)
