"""Chapter writer using Anthropic."""
from __future__ import annotations

from app.services.anthropic_client import AnthropicClient


class WriterService:
    """Write polished chapters from draft material."""

    def __init__(self, anthropic: AnthropicClient) -> None:
        self.anthropic = anthropic

    async def write_chapter(
        self,
        draft_md: str,
        topic_name: str,
        silo_name: str,
        voice_preset: str,
    ) -> str:
        system_prompt = (
            "You are a nonfiction book ghostwriter. Write in the author's voice "
            "and keep the chapter structured, practical, and original."
        )
        user_prompt = (
            f"Topic: {topic_name}\n"
            f"Chapter: {silo_name}\n"
            f"Voice preset: {voice_preset}\n\n"
            "Use the draft notes below as source material. Do not copy phrases verbatim. "
            "Produce polished prose suitable for publishing.\n\n"
            "Draft material:\n---\n"
            f"{draft_md}\n"
            "---\n\n"
            "Output only the final chapter text."
        )
        return await self.anthropic.generate(system_prompt, user_prompt, max_tokens=4000)
