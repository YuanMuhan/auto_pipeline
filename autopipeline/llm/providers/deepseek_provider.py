import json
import os
from typing import Optional, Dict, Any
from urllib import request


class DeepseekProvider:
    """DeepSeek provider wrapper (minimal chat completions)."""

    name = "deepseek"

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com/v1/chat/completions"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set for deepseek provider")
        self.base_url = base_url

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
            raise RuntimeError(f"DeepSeek API request failed: {e}")

        try:
            obj = json.loads(resp_text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"DeepSeek API response is not JSON: {e}")

        choices = obj.get("choices") or []
        text = ""
        if choices:
            message = choices[0].get("message") or {}
            text = message.get("content", "")
        usage = obj.get("usage")
        # Ensure plain text without fences
        if text.strip().startswith("```"):
            text = text.strip().strip("`")
        return {"text": text, "usage": usage}
