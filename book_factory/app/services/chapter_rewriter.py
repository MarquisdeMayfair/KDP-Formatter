"""Rewrite chapters with author voice notes."""
from __future__ import annotations

from app.services.anthropic_client import AnthropicClient


class ChapterRewriter:
    """Rewrite draft chapters by weaving in author notes."""

    def __init__(self, anthropic: AnthropicClient) -> None:
        self.anthropic = anthropic

    async def rewrite(
        self,
        draft_md: str,
        author_notes: str,
        topic_name: str,
        silo_name: str,
        voice_preset: str,
    ) -> str:
        system_prompt = (
            "You are an editor and ghostwriter. Rewrite the chapter by weaving in "
            "the author's notes, opinions, and experiences. Keep the structure clear, "
            "punchy, and practical."
        )
        user_prompt = (
            f"Topic: {topic_name}\n"
            f"Chapter: {silo_name}\n"
            f"Voice preset: {voice_preset}\n\n"
            "Draft material:\n---\n"
            f"{draft_md}\n"
            "---\n\n"
            "Author notes (to weave in):\n---\n"
            f"{author_notes}\n"
            "---\n\n"
            "Rewrite the chapter. Preserve factual accuracy but add the author's "
            "voice and opinions. Output only the final chapter text."
        )
        return await self.anthropic.generate(system_prompt, user_prompt, max_tokens=4500)
