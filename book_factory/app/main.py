"""FastAPI entrypoint for Book Factory."""
from __future__ import annotations

import logging
import json
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api import silos, topics, trends, sources, eve, compile, settings as settings_api, ingest, discovery, autopilot
from app.config import settings
from app.database import init_db
from app.services.metrics import word_count
from app.services.storage import SILO_TITLES
from app.services.trend_monitor import TrendMonitor
from app.services.storage import ensure_topic_structure, silo_paths, slugify
from app.services.source_inbox import append_sources
from app.services.discovery import collect_discovery_urls, github_search_repos
from app.services.source_queue import queue_sources

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
    Path(settings.storage_path).mkdir(parents=True, exist_ok=True)
    logger.info("Book Factory started")

    if settings.trend_rss_feeds:
        import asyncio
        asyncio.create_task(_trend_loop())


async def _trend_loop() -> None:
    from sqlalchemy import select, and_
    from app.database import AsyncSessionLocal
    from app import models

    monitor = TrendMonitor()
    while True:
        async with AsyncSessionLocal() as session:
            candidates = monitor.fetch()
            for candidate in candidates:
                exists = await session.execute(
                    select(models.TrendCandidate).where(
                        and_(
                            models.TrendCandidate.topic_name == candidate.topic_name,
                            models.TrendCandidate.source == candidate.source,
                        )
                    )
                )
                if exists.scalar_one_or_none():
                    continue
                session.add(candidate)
            await session.commit()
        await asyncio.sleep(settings.trend_poll_interval_seconds)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/docs", response_class=HTMLResponse)
async def api_docs(request: Request):
    return templates.TemplateResponse("api_docs.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request, topic: str | None = None):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app import models

    async with AsyncSessionLocal() as session:
        topics_result = await session.execute(select(models.Topic).order_by(models.Topic.created_at.desc()))
        topics_list = topics_result.scalars().all()

        silos = []
        selected_topic = None
        if topic:
            selected_topic = next((t for t in topics_list if t.slug == topic), None)
        if not selected_topic and topics_list:
            selected_topic = topics_list[0]

        if selected_topic:
            silos_result = await session.execute(
                select(models.Silo).where(models.Silo.topic_id == selected_topic.id).order_by(models.Silo.silo_number)
            )
            silos = silos_result.scalars().all()

            for silo in silos:
                draft_wc = word_count(silo.draft_md_path or "")
                final_wc = word_count(silo.final_txt_path or "")
                silo.draft_word_count = draft_wc
                silo.final_word_count = final_wc

        trends_result = await session.execute(select(models.TrendCandidate).order_by(models.TrendCandidate.discovered_at.desc()))
        trends_list = trends_result.scalars().all()

        autopilot_status = {}
        autopilot_last = None
        if selected_topic:
            metrics_dir = Path(settings.storage_path) / selected_topic.slug / "metrics"
            status_path = metrics_dir / "autopilot_status.json"
            log_path = metrics_dir / "autopilot.jsonl"

            if status_path.exists():
                try:
                    autopilot_status = json.loads(status_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    autopilot_status = {}

            if log_path.exists():
                try:
                    with open(log_path, "rb") as handle:
                        try:
                            handle.seek(-2048, 2)
                        except OSError:
                            handle.seek(0)
                        chunk = handle.read().decode("utf-8", errors="ignore")
                        lines = [line for line in chunk.splitlines() if line.strip()]
                        if lines:
                            autopilot_last = json.loads(lines[-1])
                except (OSError, json.JSONDecodeError):
                    autopilot_last = None

    context = {
        "request": request,
        "topics": topics_list,
        "selected_topic": selected_topic,
        "silos": silos,
        "silo_titles": SILO_TITLES,
        "trends": trends_list,
        "autopilot_status": autopilot_status,
        "autopilot_last": autopilot_last,
    }
    return templates.TemplateResponse("dashboard.html", context)


@app.post("/dashboard/topics")
async def dashboard_create_topic(
    name: str = Form(...),
    book_title: str = Form(""),
    series_name: str = Form(""),
    subtitle: str = Form(""),
    author_voice_preset: str = Form("default"),
    target_audience: str = Form(""),
    stance: str = Form(""),
    draft_target_words: int = Form(25000),
):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app import models

    async with AsyncSessionLocal() as session:
        slug = slugify(name)
        existing = await session.execute(select(models.Topic).where(models.Topic.slug == slug))
        if existing.scalar_one_or_none():
            return {"error": "Topic already exists"}

        topic = models.Topic(
            slug=slug,
            name=name,
            series_name=series_name or None,
            book_title=book_title or name,
            subtitle=subtitle or None,
            author_voice_preset=author_voice_preset or "default",
            target_audience=target_audience or None,
            stance=stance or None,
            draft_target_words=draft_target_words,
            status="research",
        )
        session.add(topic)
        await session.flush()

        ensure_topic_structure(slug)
        for silo_number, title in SILO_TITLES.items():
            draft_path, final_path, audio_path = silo_paths(slug, silo_number)
            session.add(
                models.Silo(
                    topic_id=topic.id,
                    silo_number=silo_number,
                    name_template=title,
                    draft_md_path=str(draft_path),
                    final_txt_path=str(final_path),
                    review_audio_path=str(audio_path),
                    status="drafting" if silo_number == 0 else "empty",
                )
            )

        await session.commit()

    return {"message": "Topic created"}


@app.post("/dashboard/topics/{slug}/sources")
async def dashboard_add_sources(slug: str, urls: str = Form("")):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app import models

    url_list = [line.strip() for line in urls.splitlines() if line.strip()]
    if not url_list:
        return {"error": "No URLs provided"}

    async with AsyncSessionLocal() as session:
        topic_result = await session.execute(select(models.Topic).where(models.Topic.slug == slug))
        topic = topic_result.scalar_one_or_none()
        if not topic:
            return {"error": "Topic not found"}

        append_sources(slug, url_list, source="dashboard")
        for url in url_list:
            session.add(models.SourceDoc(topic_id=topic.id, url=url, status="pending"))

        await session.commit()

    return {"message": "Sources added"}


@app.post("/dashboard/topics/{slug}/discover")
async def dashboard_discover_sources(slug: str):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app import models

    async with AsyncSessionLocal() as session:
        topic_result = await session.execute(select(models.Topic).where(models.Topic.slug == slug))
        topic = topic_result.scalar_one_or_none()
        if not topic:
            return {"error": "Topic not found"}

        feed_urls = collect_discovery_urls(topic.name, per_feed=8)
        repos = await github_search_repos(topic.name, limit=8)
        candidates = list(dict.fromkeys(feed_urls + repos))
        await queue_sources(session, topic.id, topic.slug, candidates, source_label="discovery")

    return RedirectResponse(url=f"/dashboard?topic={slug}", status_code=303)


app.include_router(topics.router, prefix="/api/v1")
app.include_router(silos.router, prefix="/api/v1")
app.include_router(trends.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(eve.router, prefix="/api/v1")
app.include_router(autopilot.router, prefix="/api/v1")
app.include_router(compile.router, prefix="/api/v1")
app.include_router(settings_api.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(discovery.router, prefix="/api/v1")
