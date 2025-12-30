from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class LLMConfig:
    provider: str = "mock"
    model: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    cache_dir: str = ".cache/llm"
    cache_enabled: bool = True
    prompt_tier: str = "P0"
    seed: int = 0


@dataclass
class LLMRequest:
    stage: str
    prompt_name: str
    case_id: str
    prompt_text: str
    rendered_prompt: str
    rules_hash: str
    schema_versions: Dict[str, Any]
    inputs_hash: str
    template_hash: str
    rendered_hash: str
    params: Dict[str, Any]


@dataclass
class LLMResponse:
    text: str
    usage: Optional[Dict[str, Any]] = None
