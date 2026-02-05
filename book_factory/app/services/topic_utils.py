"""Helpers for topic keywords, aliases, and query building."""
from __future__ import annotations

import re
from typing import Iterable


def parse_list_field(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[,\n]", raw)
    cleaned = [part.strip() for part in parts if part.strip()]
    return list(dict.fromkeys(cleaned))


def parse_url_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    if "\n" in raw:
        parts = raw.splitlines()
    else:
        parts = raw.split(",")
    cleaned = [part.strip() for part in parts if part.strip()]
    return list(dict.fromkeys(cleaned))


def format_list_field(values: Iterable[str] | None, sep: str = ", ") -> str:
    if not values:
        return ""
    return sep.join([value for value in values if value])


def normalize_terms(topic_name: str, keywords: Iterable[str] | None = None) -> list[str]:
    terms: list[str] = []
    if topic_name:
        terms.append(topic_name.strip())
    if keywords:
        terms.extend([term.strip() for term in keywords if term and term.strip()])
    return list(dict.fromkeys([term for term in terms if term]))


def build_or_query(terms: Iterable[str]) -> str:
    items: list[str] = []
    for term in terms:
        if not term:
            continue
        safe = term.replace('"', "").strip()
        if not safe:
            continue
        items.append(f'"{safe}"')
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"({ ' OR '.join(items) })"


def text_mentions_term(text: str, terms: Iterable[str]) -> bool:
    if not terms:
        return True
    sample = text.lower()
    for term in terms:
        if term and term.lower() in sample:
            return True
    return False
