import json
import os
from typing import Optional, Dict, Any
from urllib import request


class OpenAIProvider:
    """Minimal OpenAI Chat Completions provider (no external deps)."""

    name = "openai"

    def __init__(self, api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set for openai provider")
        # Allow override via env OPENAI_API_BASE (expects full base with /v1)
        base_env = os.getenv("OPENAI_API_BASE")
        # Default改为国内代理域，仍可通过 OPENAI_API_BASE 或入参覆盖
        self.base_url = base_env or base_url or "https://api.gpt.ge/v1/chat/completions"

    def call(self, *, prompt: str, model: str, temperature: float = 0.0,
             max_tokens: Optional[int] = None, **_) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        req = request.Request(self.base_url, data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req) as resp:
                resp_text = resp.read().decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"OpenAI API request failed: {e}")

        try:
            obj = json.loads(resp_text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"OpenAI API response is not JSON: {e}")

        choices = obj.get("choices") or []
        text = ""
        if choices:
            message = choices[0].get("message") or {}
            text = message.get("content", "")
        usage = obj.get("usage")
        if text.strip().startswith("```"):
            text = text.strip().strip("`")
        return {"text": text, "usage": usage}
