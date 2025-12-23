import os
from typing import Optional, Dict, Any

try:
    import anthropic
except ImportError:  # pragma: no cover - optional dependency
    anthropic = None


class AnthropicProvider:
    """Anthropic provider wrapper."""

    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if self.api_key is None:
            raise RuntimeError("ANTHROPIC_API_KEY is not set for anthropic provider")
        if anthropic is None:
            raise RuntimeError("anthropic package not installed")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def call(self, *, prompt: str, model: str, temperature: float = 0.0,
             max_tokens: Optional[int] = None, **_) -> Dict[str, Any]:
        kwargs = {
            "model": model,
            "max_tokens": max_tokens or 2048,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = self.client.messages.create(**kwargs)
        text_parts = []
        for c in resp.content:
            if hasattr(c, "text"):
                text_parts.append(c.text)
        text = "\n".join(text_parts)
        usage = getattr(resp, "usage", None)
        return {"text": text, "usage": usage}
