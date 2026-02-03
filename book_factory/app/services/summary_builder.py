"""Build review packs for author voice loop."""
from __future__ import annotations

import json

from app.services.ollama_client import OllamaClient


class SummaryBuilder:
    """Generate summary and prompt questions for a draft."""

    def __init__(self, ollama: OllamaClient) -> None:
        self.ollama = ollama

    async def build_review_pack(self, draft_md: str, silo_name: str, topic_name: str) -> dict:
        summary = await self._summarise(draft_md, silo_name, topic_name)
        prompts = await self._generate_prompts(draft_md, silo_name, topic_name)

        return {
            "summary": summary,
            "prompt_questions": prompts,
            "word_count": len(draft_md.split()),
            "source_count": draft_md.count("[^src-")
        }

    async def _summarise(self, draft_md: str, silo_name: str, topic_name: str) -> str:
        prompt = (
            "Summarise this draft chapter in 4-5 bullet points. "
            "Be specific about what claims and topics it covers. "
            "Note any gaps or areas that feel thin.\n\n"
            f"Chapter: {silo_name}\n"
            f"Book topic: {topic_name}\n\n"
            "Draft:\n---\n"
            f"{draft_md[:6000]}\n"
            "---\n\n"
            "Respond with a brief, direct summary. No preamble."
        )
        return await self.ollama.generate(prompt)

    async def _generate_prompts(self, draft_md: str, silo_name: str, topic_name: str) -> list[str]:
        prompt = (
            "You're helping an author add their personal perspective to a draft chapter.\n\n"
            f"Chapter: {silo_name}\n"
            f"Book topic: {topic_name}\n\n"
            "Draft covers:\n---\n"
            f"{draft_md[:4000]}\n"
            "---\n\n"
            "Generate 5 specific questions to prompt the author's own opinions and experiences. "
            "Respond with ONLY a JSON array of 5 question strings."
        )
        response = await self.ollama.generate(prompt)
        try:
            parsed = json.loads(response)
            if isinstance(parsed, list) and len(parsed) == 5:
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass

        return [
            f"What's your honest take on {topic_name}?",
            "What do most people get wrong about this?",
            "Can you share a personal experience related to this chapter?",
            "What would you add that the sources don't cover?",
            "Is there anything in this draft you'd push back on?",
        ]
