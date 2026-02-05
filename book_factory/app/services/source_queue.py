"""Queue new source URLs into the database and inbox."""
from __future__ import annotations

from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.services.source_inbox import append_sources


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except ValueError:
        return ""


async def queue_sources(
    session: AsyncSession,
    topic_id: int,
    slug: str,
    urls: list[str] | list[tuple[str, str]],
    source_label: str = "discovery",
) -> int:
    if not urls:
        return 0

    result = await session.execute(
        select(models.SourceDoc.url).where(models.SourceDoc.topic_id == topic_id)
    )
    existing = {row[0] for row in result.all() if row[0]}

    new_urls: list[tuple[str, str]] = []
    for item in urls:
        if isinstance(item, tuple):
            url, label = item
        else:
            url, label = item, source_label
        if url in existing:
            continue
        new_urls.append((url, label))
    if not new_urls:
        return 0

    append_sources(slug, new_urls, source=source_label)

    for url, label in new_urls:
        session.add(
            models.SourceDoc(
                topic_id=topic_id,
                url=url,
                domain=_domain(url),
                status="pending",
                source=label,
            )
        )

    await session.commit()
    return len(new_urls)
