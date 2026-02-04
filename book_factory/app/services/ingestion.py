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
from app.services.storage import silo_dir


@dataclass
class Chunk:
    text: str


async def fetch_and_clean(url: str, timeout: int = 20) -> str:
    if "x.com" in url or "twitter.com" in url:
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

    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text
    return _clean_html(html)


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines())
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


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
        "Extract useful nuggets for a draft chapter. "
        "Prefer bullets of facts, steps, gotchas, commands, examples. "
        "Avoid copying sentences verbatim.\n\n"
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
