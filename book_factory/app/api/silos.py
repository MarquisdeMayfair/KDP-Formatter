"""Silo endpoints for writing and voice loop."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.anthropic_client import AnthropicClient
from app.services.author_notes import append_notes, read_notes
from app.services.chapter_rewriter import ChapterRewriter
from app.services.ollama_client import OllamaClient
from app.services.summary_builder import SummaryBuilder
from app.services.tts import TTSService
from app.services.writer import WriterService

router = APIRouter(prefix="/topics/{slug}/silos", tags=["silos"])


def _load_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Draft not found") from exc


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


async def _get_topic_and_silo(db: AsyncSession, slug: str, silo_number: int) -> tuple[models.Topic, models.Silo]:
    topic_result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = topic_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    silo_result = await db.execute(
        select(models.Silo).where(
            models.Silo.topic_id == topic.id,
            models.Silo.silo_number == silo_number,
        )
    )
    silo = silo_result.scalar_one_or_none()
    if not silo:
        raise HTTPException(status_code=404, detail="Silo not found")
    return topic, silo


@router.get("", response_model=list[schemas.SiloSummary])
async def list_silos(slug: str, db: AsyncSession = Depends(get_db)):
    topic_result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = topic_result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    silos_result = await db.execute(
        select(models.Silo).where(models.Silo.topic_id == topic.id).order_by(models.Silo.silo_number)
    )
    return silos_result.scalars().all()


@router.post("/{silo_number}/write", response_model=schemas.WriteResponse)
async def write_chapter(slug: str, silo_number: int, db: AsyncSession = Depends(get_db)):
    topic, silo = await _get_topic_and_silo(db, slug, silo_number)
    draft_md = _load_text(silo.draft_md_path)

    writer = WriterService(AnthropicClient())
    final_text = await writer.write_chapter(
        draft_md=draft_md,
        topic_name=topic.name,
        silo_name=silo.custom_title or silo.name_template,
        voice_preset=topic.author_voice_preset,
    )

    _write_text(silo.final_txt_path, final_text)
    silo.final_word_count = len(final_text.split())
    silo.status = "complete"
    await db.commit()

    return {"message": "Chapter written", "final_path": silo.final_txt_path}


@router.get("/{silo_number}/review-pack", response_model=schemas.ReviewPack)
async def review_pack(slug: str, silo_number: int, db: AsyncSession = Depends(get_db)):
    topic, silo = await _get_topic_and_silo(db, slug, silo_number)
    draft_md = _load_text(silo.draft_md_path)

    summary_builder = SummaryBuilder(OllamaClient())
    pack = await summary_builder.build_review_pack(
        draft_md=draft_md,
        silo_name=silo.custom_title or silo.name_template,
        topic_name=topic.name,
    )
    return pack


@router.post("/{silo_number}/draft-audio")
async def draft_audio(slug: str, silo_number: int, db: AsyncSession = Depends(get_db)):
    _, silo = await _get_topic_and_silo(db, slug, silo_number)
    draft_md = _load_text(silo.draft_md_path)

    tts = TTSService()
    await tts.generate_audio(draft_md, silo.review_audio_path)
    return {"message": "Audio generated", "audio_path": silo.review_audio_path}


@router.get("/{silo_number}/draft-audio")
async def get_draft_audio(slug: str, silo_number: int, db: AsyncSession = Depends(get_db)):
    _, silo = await _get_topic_and_silo(db, slug, silo_number)
    return FileResponse(silo.review_audio_path, media_type="audio/mpeg", filename="draft.mp3")


@router.post("/{silo_number}/author-notes", response_model=schemas.AuthorNoteOut)
async def add_author_notes(
    slug: str,
    silo_number: int,
    payload: schemas.AuthorNoteCreate,
    db: AsyncSession = Depends(get_db),
):
    topic, silo = await _get_topic_and_silo(db, slug, silo_number)
    append_notes(slug, silo_number, payload.text)

    note = models.AuthorNote(
        topic_id=topic.id,
        silo_id=silo.id,
        text=payload.text,
        source=payload.source,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.post("/{silo_number}/rewrite", response_model=schemas.RewriteResponse)
async def rewrite_chapter(slug: str, silo_number: int, db: AsyncSession = Depends(get_db)):
    topic, silo = await _get_topic_and_silo(db, slug, silo_number)
    draft_md = _load_text(silo.draft_md_path)
    notes = read_notes(slug, silo_number)
    if not notes:
        raise HTTPException(status_code=400, detail="No author notes found")

    rewriter = ChapterRewriter(AnthropicClient())
    final_text = await rewriter.rewrite(
        draft_md=draft_md,
        author_notes=notes,
        topic_name=topic.name,
        silo_name=silo.custom_title or silo.name_template,
        voice_preset=topic.author_voice_preset,
    )

    _write_text(silo.final_txt_path, final_text)
    silo.final_word_count = len(final_text.split())
    silo.status = "complete"
    await db.commit()

    return {"message": "Chapter rewritten", "final_path": silo.final_txt_path}
