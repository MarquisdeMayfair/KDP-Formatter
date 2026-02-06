"""Ghostwriter swarm orchestration."""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy import select

from app import models
from app.config import settings
from app.database import AsyncSessionLocal
from app.services.anthropic_client import AnthropicClient
from app.services.ollama_client import OllamaClient
from app.services.openai_compat_client import OpenAICompatClient
from app.services.storage import SILO_TITLES, silo_dir, topic_dir
from app.services.author_notes import read_notes
from app.services.x_client import search_recent_tweets
from app.services.discovery import cse_search
from app.services.ingestion import fetch_and_clean


@dataclass
class ChapterContext:
    silo_number: int
    title: str
    goal: str
    outline: list[str]
    notes: str
    ideas: list[str]
    draft_notes: str
    author_notes: str
    x_notes: str
    web_notes: str


def swarm_draft_path(slug: str, silo_number: int) -> Path:
    return silo_dir(slug, silo_number) / "swarm_draft.md"


def swarm_review_path(slug: str, silo_number: int) -> Path:
    return silo_dir(slug, silo_number) / "swarm_review.json"


def _select_writer_provider() -> tuple[str, object]:
    provider = settings.swarm_writer_provider
    if provider == "anthropic":
        return provider, AnthropicClient()
    if provider == "openai":
        return provider, OpenAICompatClient(
            settings.openai_api_key,
            settings.openai_base_url,
            settings.openai_model,
            settings.openai_compat_path,
        )
    if provider == "grok":
        return provider, OpenAICompatClient(
            settings.grok_api_key,
            settings.grok_base_url,
            settings.grok_model,
            settings.openai_compat_path,
        )
    return "ollama", OllamaClient()


def _select_research_provider() -> tuple[str, object | None]:
    provider = settings.swarm_research_provider
    if provider == "none":
        return provider, None
    if provider == "anthropic":
        return provider, AnthropicClient()
    if provider == "openai":
        return provider, OpenAICompatClient(
            settings.openai_api_key,
            settings.openai_base_url,
            settings.openai_model,
            settings.openai_compat_path,
        )
    if provider == "grok":
        return provider, OpenAICompatClient(
            settings.grok_api_key,
            settings.grok_base_url,
            settings.grok_model,
            settings.openai_compat_path,
        )
    return "ollama", OllamaClient()


def _log_swarm(slug: str, record: dict) -> None:
    metrics_dir = topic_dir(slug) / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    log_path = metrics_dir / "swarm.jsonl"
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _read_draft_notes(slug: str, silo_number: int) -> str:
    draft_path = silo_dir(slug, silo_number) / "draft.md"
    if not draft_path.exists():
        return ""
    return draft_path.read_text(encoding="utf-8", errors="ignore")


async def _web_evidence(topic_name: str, chapter_title: str, outline: list[str]) -> str:
    if not settings.swarm_use_web or not settings.google_cse_api_key:
        return ""
    query = f"{topic_name} {chapter_title}"
    if outline:
        query = f"{query} {outline[0]}"
    urls = cse_search(
        query,
        date_restrict=settings.google_cse_date_restrict,
        num=settings.swarm_web_sources_per_chapter,
    )
    if not urls:
        return ""
    snippets: list[str] = []
    for url in urls[: settings.swarm_web_sources_per_chapter]:
        try:
            text = await fetch_and_clean(url)
        except Exception:
            continue
        words = text.split()
        snippet = " ".join(words[: settings.swarm_web_max_words])
        if snippet:
            snippets.append(f"URL: {url}\n{snippet}")
    return "\n\n".join(snippets)


async def _generate(provider: str, client: object, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    if provider == "ollama":
        # Ollama client accepts a single prompt
        return await client.generate(system_prompt + "\n\n" + user_prompt)
    return await client.generate(system_prompt, user_prompt, max_tokens=max_tokens)


async def ensure_briefs(topic_id: int, slug: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(models.ChapterBrief).where(models.ChapterBrief.topic_id == topic_id)
        )
        existing = {(row.silo_number): row for row in result.scalars().all()}
        for silo_num, title in SILO_TITLES.items():
            if silo_num in existing:
                continue
            session.add(
                models.ChapterBrief(
                    topic_id=topic_id,
                    silo_number=silo_num,
                    title=title,
                    goal="",
                    outline=[],
                    notes="",
                    status="draft",
                )
            )
        await session.commit()


async def auto_assign_ideas(topic_id: int, topic_name: str, idea_ids: Iterable[int] | None = None) -> int:
    ollama = OllamaClient()
    updated = 0
    async with AsyncSessionLocal() as session:
        query = select(models.IdeaItem).where(models.IdeaItem.topic_id == topic_id)
        if idea_ids:
            query = query.where(models.IdeaItem.id.in_(list(idea_ids)))
        else:
            query = query.where(models.IdeaItem.status == "backlog")
        result = await session.execute(query)
        ideas = result.scalars().all()

        if not ideas:
            return 0

        for idea in ideas:
            prompt = (
                "Assign this idea to the best chapter silo (0-10). "
                "Return only the number.\n\n"
                f"Topic: {topic_name}\n"
                "Silos:\n"
                + "\n".join([f"{k}: {v}" for k, v in SILO_TITLES.items()])
                + "\n\nIdea:\n"
                + idea.text[:800]
            )
            response = await ollama.generate(prompt)
            silo_num = 0
            for token in response.split():
                if token.isdigit():
                    silo_num = int(token)
                    break
            idea.silo_number = silo_num
            idea.status = "assigned"
            updated += 1
        await session.commit()
    return updated


async def _build_context(
    topic_id: int,
    topic_name: str,
    slug: str,
    silo_number: int,
    include_unassigned: bool,
) -> ChapterContext:
    async with AsyncSessionLocal() as session:
        brief_result = await session.execute(
            select(models.ChapterBrief).where(
                models.ChapterBrief.topic_id == topic_id,
                models.ChapterBrief.silo_number == silo_number,
            )
        )
        brief = brief_result.scalar_one_or_none()
        if not brief:
            title = SILO_TITLES.get(silo_number, f"Silo {silo_number}")
            goal = ""
            outline = []
            notes = ""
        else:
            title = brief.title
            goal = brief.goal
            outline = list(brief.outline or [])
            notes = brief.notes or ""

        ideas_query = select(models.IdeaItem).where(
            models.IdeaItem.topic_id == topic_id,
            models.IdeaItem.silo_number == silo_number,
        )
        result = await session.execute(ideas_query)
        ideas = [item.text for item in result.scalars().all()]

        if include_unassigned:
            unassigned_result = await session.execute(
                select(models.IdeaItem).where(
                    models.IdeaItem.topic_id == topic_id,
                    models.IdeaItem.silo_number.is_(None),
                )
            )
            ideas.extend([item.text for item in unassigned_result.scalars().all()])

    draft_notes = _read_draft_notes(slug, silo_number)
    author_notes = read_notes(slug, silo_number)

    x_notes = ""
    if settings.swarm_use_x and settings.x_bearer_token:
        query = f"{topic_name} {title}"
        tweets = await asyncio.to_thread(search_recent_tweets, query, 6)
        if tweets:
            x_notes = "\n".join(f"- {item['text']}" for item in tweets)

    web_notes = await _web_evidence(topic_name, title, outline)

    return ChapterContext(
        silo_number=silo_number,
        title=title,
        goal=goal,
        outline=outline,
        notes=notes,
        ideas=ideas,
        draft_notes=draft_notes,
        author_notes=author_notes,
        x_notes=x_notes,
        web_notes=web_notes,
    )


async def _research_memo(context: ChapterContext, topic_name: str) -> str:
    provider, client = _select_research_provider()
    if client is None:
        return ""
    system_prompt = (
        "You are a research assistant. Create a concise memo with factual anchors, "
        "gaps, and questions. Avoid speculation."
    )
    user_prompt = (
        f"Topic: {topic_name}\n"
        f"Chapter: {context.title}\n"
        f"Goal: {context.goal}\n"
        f"Outline: {context.outline}\n\n"
        f"Brief notes:\n{context.notes}\n\n"
        "Ideas:\n" + "\n".join(f"- {idea}" for idea in context.ideas[:25]) + "\n\n"
        "Draft notes:\n" + context.draft_notes[:4000] + "\n\n"
        "Author notes:\n" + context.author_notes[:1500] + "\n\n"
        "X notes:\n" + context.x_notes[:1500] + "\n\n"
        "Web evidence:\n" + context.web_notes[:4000]
    )
    return await _generate(provider, client, system_prompt, user_prompt, max_tokens=1200)


async def _write_chapter(context: ChapterContext, topic_name: str, voice_preset: str) -> str:
    provider, client = _select_writer_provider()
    system_prompt = (
        "You are a senior ghostwriter. Write original prose with a clear narrative arc. "
        "Do not copy phrases from sources. If evidence is weak, flag gaps."
    )
    user_prompt = (
        f"Topic: {topic_name}\n"
        f"Chapter: {context.title}\n"
        f"Voice: {voice_preset}\n\n"
        f"Chapter goal: {context.goal}\n"
        f"Outline: {context.outline}\n\n"
        f"Brief notes:\n{context.notes}\n\n"
        "Idea pool (scrum backlog):\n" + "\n".join(f"- {idea}" for idea in context.ideas[:30]) + "\n\n"
        "Author notes:\n" + context.author_notes[:2000] + "\n\n"
        "Draft notes (do not copy verbatim):\n" + context.draft_notes[:4000] + "\n\n"
        "X notes (signals only, paraphrase):\n" + context.x_notes[:1000] + "\n\n"
        "Web evidence (paraphrase, cite by URL if useful):\n" + context.web_notes[:4000] + "\n\n"
        "Write the chapter in coherent narrative form. Use section headings if helpful."
    )

    return await _generate(provider, client, system_prompt, user_prompt, max_tokens=3200)


async def _review_chapter(context: ChapterContext, topic_name: str, chapter_text: str) -> dict:
    provider, client = _select_writer_provider()
    system_prompt = "You are a meticulous book editor."
    user_prompt = (
        f"Topic: {topic_name}\n"
        f"Chapter: {context.title}\n"
        f"Goal: {context.goal}\n"
        f"Outline: {context.outline}\n\n"
        "Evaluate the chapter for coverage, coherence, repetition, and missing evidence. "
        "Return JSON with keys: score (1-10), strengths (list), gaps (list), risks (list).\n\n"
        f"Chapter text:\n{chapter_text[:4000]}"
    )
    response = await _generate(provider, client, system_prompt, user_prompt, max_tokens=800)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"score": 0, "strengths": [], "gaps": ["Review parse failed"], "risks": [response]}


async def run_swarm(
    topic_id: int,
    slug: str,
    topic_name: str,
    voice_preset: str,
    silos: Iterable[int] | None = None,
    include_unassigned_ideas: bool = True,
) -> dict:
    await ensure_briefs(topic_id, slug)
    selected = list(silos) if silos else list(SILO_TITLES.keys())

    semaphore = asyncio.Semaphore(settings.swarm_max_parallel)

    async def _run_silo(silo_number: int) -> dict:
        async with semaphore:
            start = time.monotonic()
            context = await _build_context(
                topic_id,
                topic_name,
                slug,
                silo_number,
                include_unassigned_ideas,
            )
            research_memo = await _research_memo(context, topic_name)
            if research_memo:
                context.notes = (context.notes + "\n\n" + research_memo).strip()
            chapter_text = await _write_chapter(context, topic_name, voice_preset)
            draft_path = swarm_draft_path(slug, silo_number)
            draft_path.write_text(chapter_text.strip(), encoding="utf-8")

            review = await _review_chapter(context, topic_name, chapter_text)
            review_path = swarm_review_path(slug, silo_number)
            review_path.write_text(json.dumps(review, indent=2), encoding="utf-8")

            duration = round(time.monotonic() - start, 2)
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "silo": silo_number,
                "title": context.title,
                "duration_seconds": duration,
                "word_count": len(chapter_text.split()),
                "review_score": review.get("score", 0),
            }
            _log_swarm(slug, record)
            return record

    results = await asyncio.gather(*[_run_silo(silo) for silo in selected], return_exceptions=True)
    completed = []
    errors = []
    for result in results:
        if isinstance(result, Exception):
            errors.append(str(result))
        else:
            completed.append(result)

    return {
        "completed": completed,
        "errors": errors,
        "count": len(completed),
    }
