"""Compile manuscript and image placeholders."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app.services.compiler import compile_manuscript, build_image_manifest, apply_images, build_sources_page
from app.services.storage import topic_dir

router = APIRouter(prefix="/topics/{slug}", tags=["compile"])


async def _get_topic(db: AsyncSession, slug: str) -> models.Topic:
    result = await db.execute(select(models.Topic).where(models.Topic.slug == slug))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/compile", response_model=schemas.CompileResponse)
async def compile_topic(slug: str, db: AsyncSession = Depends(get_db)):
    topic = await _get_topic(db, slug)
    silos_result = await db.execute(
        select(models.Silo).where(models.Silo.topic_id == topic.id).order_by(models.Silo.silo_number)
    )
    silos = silos_result.scalars().all()

    source_paths: list[Path] = []
    # Author opening
    front_matter = topic_dir(slug) / "front_matter.md"
    if front_matter.exists():
        source_paths.append(front_matter)

    for silo in silos:
        if silo.final_txt_path and Path(silo.final_txt_path).exists():
            source_paths.append(Path(silo.final_txt_path))
        elif silo.draft_md_path and Path(silo.draft_md_path).exists():
            source_paths.append(Path(silo.draft_md_path))

    # Conclusion
    conclusion = topic_dir(slug) / "conclusion.md"
    if conclusion.exists():
        source_paths.append(conclusion)

    # Sources page
    sources_result = await db.execute(select(models.SourceDoc.url).where(models.SourceDoc.topic_id == topic.id))
    urls = [row[0] for row in sources_result.all() if row[0]]
    sources_path = build_sources_page(slug, urls)
    source_paths.append(sources_path)

    manuscript_path = compile_manuscript(slug, source_paths)
    manifest_path = build_image_manifest(slug, manuscript_path)

    return {
        "message": "Compiled manuscript",
        "manuscript_path": str(manuscript_path),
        "manifest_path": str(manifest_path),
    }


@router.post("/apply-images", response_model=schemas.ApplyImagesResponse)
async def apply_images_endpoint(
    slug: str,
    payload: schemas.ApplyImagesRequest,
    db: AsyncSession = Depends(get_db),
):
    await _get_topic(db, slug)
    output_path = apply_images(slug, payload.replacements)
    return {"message": "Images applied", "manuscript_path": str(output_path)}
