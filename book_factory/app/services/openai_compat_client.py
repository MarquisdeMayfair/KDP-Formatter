"""OpenAI-compatible chat completions client (works for GPT/Grok-compatible endpoints)."""
from __future__ import annotations

from urllib.parse import urljoin

import httpx


class OpenAICompatClient:
    """Minimal OpenAI-compatible client for chat completions."""

    def __init__(self, api_key: str, base_url: str, model: str, path: str = "/v1/chat/completions") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") + "/"
        self.model = model
        self.path = path

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 3000) -> str:
        if not self.api_key:
            raise ValueError("OpenAI-compatible API key is not configured.")
        url = urljoin(self.base_url, self.path.lstrip("/"))
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        return (message.get("content") or "").strip()
