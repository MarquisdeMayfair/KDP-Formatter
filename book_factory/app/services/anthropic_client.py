"""Anthropic API client via HTTPX."""
from __future__ import annotations

import httpx

from app.config import settings


class AnthropicClient:
    """Thin client for Anthropic Messages API."""

    def __init__(self) -> None:
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.base_url = "https://api.anthropic.com/v1/messages"

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 3000) -> str:
        if not self.api_key:
            raise ValueError("Anthropic API key is not configured.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data.get("content", [])
        if not content:
            return ""
        return "".join(part.get("text", "") for part in content).strip()
