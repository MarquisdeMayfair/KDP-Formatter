"""Auto ingestion pipeline: fetch, clean, chunk, classify, extract."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import asyncio
import httpx
from bs4 import BeautifulSoup

from app.services.ollama_client import OllamaClient
from app.services.x_client import extract_status_id, fetch_tweet_payload, fetch_thread_text, fetch_username

URL_RE = re.compile(r"https?://\\S+")
X_DOMAINS = ("x.com", "twitter.com")
from app.services.storage import silo_dir


@dataclass
class Chunk:
    text: str


def is_x_url(url: str) -> bool:
    return any(domain in (url or "") for domain in X_DOMAINS)


async def fetch_and_clean(url: str, timeout: int = 20) -> str:
    if url.startswith("file:"):
        path = url.replace("file:", "", 1)
        return Path(path).read_text(encoding="utf-8", errors="ignore").strip()
    if is_x_url(url):
        status_id = extract_status_id(url)
        if not status_id:
            raise ValueError("Invalid X status URL")
        payload = await asyncio.to_thread(fetch_tweet_payload, status_id)
        text = payload.get("text", "")
        author_id = payload.get("author_id")
        conversation_id = payload.get("conversation_id")

        if author_id and conversation_id:
            username = await asyncio.to_thread(fetch_username, author_id)
            if username:
                thread = await asyncio.to_thread(fetch_thread_text, conversation_id, username)
                if thread:
                    return "\n\n".join(thread)

        return text

    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        resp = await client.get(url)
        if resp.status_code in {403, 429, 451}:
            # Fallback to Jina reader to bypass common bot blocks.
            reader_url = f"https://r.jina.ai/http://{url}"
            resp = await client.get(reader_url)
        resp.raise_for_status()
        html = resp.text
    cleaned = _clean_html(html)
    if _looks_blocked(cleaned):
        raise ValueError("Blocked or captcha page")
    return cleaned


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines())
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def _looks_blocked(text: str) -> bool:
    markers = [
        "403 forbidden",
        "access denied",
        "request blocked",
        "enable javascript",
        "captcha",
        "cloudflare",
        "robot check",
        "not authorized",
        "temporarily unavailable",
    ]
    sample = text.lower()[:2000]
    return any(marker in sample for marker in markers)


def chunk_text(text: str, max_chars: int = 3500) -> list[Chunk]:
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars:
            if current:
                chunks.append(Chunk(text=current.strip()))
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        chunks.append(Chunk(text=current.strip()))
    return chunks


def append_to_silo(slug: str, silo_number: int, content: str) -> Path:
    draft_path = silo_dir(slug, silo_number) / "draft.md"
    with open(draft_path, "a", encoding="utf-8") as handle:
        handle.write("\n\n" + content.strip())
    return draft_path


async def classify_chunk(ollama: OllamaClient, chunk: str, topic_name: str) -> int:
    prompt = (
        "Classify this text into a chapter silo (0-10). "
        "Return only the silo number.\n\n"
        f"Topic: {topic_name}\n\n"
        f"Text:\n{chunk[:3000]}"
    )
    return await _parse_int(ollama, prompt)


async def extract_nuggets(ollama: OllamaClient, chunk: str, topic_name: str, silo_title: str) -> str:
    prompt = (
        "You are building a structured draft pack for a book chapter. "
        "Output only the sectioned markdown below, no preamble.\n\n"
        "Rules:\n"
        "- No filler phrases like 'Here are...' or 'In summary'.\n"
        "- No verbatim copying; paraphrase into concise, actionable points.\n"
        "- Prefer concrete facts, steps, gotchas, commands, examples.\n"
        "- If data is thin, add 2-3 questions to research rather than invent.\n\n"
        "Format (exact headings):\n"
        "## Chapter Goal\n"
        "- 1 sentence on what the reader will achieve.\n"
        "## Key Facts\n"
        "- 5-12 bullets of factual nuggets.\n"
        "## Process / Steps\n"
        "- 3-10 bullets of steps or workflow.\n"
        "## Examples / Use Cases\n"
        "- 3-8 bullets of real scenarios or applications.\n"
        "## Gotchas / Risks\n"
        "- 3-8 bullets of failure modes, limits, or caveats.\n"
        "## Voice Hooks\n"
        "- 3-6 bullets written as if from the author's voice (short, punchy).\n"
        "## Open Questions\n"
        "- 1-5 bullets of gaps to fill later (if any).\n\n"
        f"Topic: {topic_name}\n"
        f"Silo: {silo_title}\n\n"
        f"Text:\n{chunk[:3500]}"
    )
    return await ollama.generate(prompt)


async def _parse_int(ollama: OllamaClient, prompt: str) -> int:
    response = await ollama.generate(prompt)
    match = re.search(r"\b(10|[0-9])\b", response)
    if not match:
        return 0
    return int(match.group(1))
