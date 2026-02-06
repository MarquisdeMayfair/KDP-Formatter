"""X API client for fetching tweet text via Bearer Token (v2)."""
from __future__ import annotations

import re
import time
from typing import Optional

import requests

from app.config import settings

_last_call_ts: float | None = None

STATUS_ID_RE = re.compile(r"/status/(\d+)")


def extract_status_id(url: str) -> Optional[str]:
    match = STATUS_ID_RE.search(url)
    if not match:
        return None
    return match.group(1)


def _bearer_headers() -> dict:
    if not settings.x_bearer_token:
        raise ValueError("X bearer token missing")
    return {"Authorization": f"Bearer {settings.x_bearer_token}"}


def fetch_tweet_payload(status_id: str) -> dict:
    global _last_call_ts
    if _last_call_ts is not None:
        elapsed = time.time() - _last_call_ts
        delay = max(0.0, settings.x_min_seconds_between_calls - elapsed)
        if delay > 0:
            time.sleep(delay)

    url = f"https://api.x.com/2/tweets/{status_id}"
    params = {"tweet.fields": "text,created_at,author_id,conversation_id,entities"}
    resp = requests.get(url, headers=_bearer_headers(), params=params, timeout=20)
    if resp.status_code == 429:
        reset = resp.headers.get("x-rate-limit-reset")
        if reset and reset.isdigit():
            wait_for = max(0, int(reset) - int(time.time()) + 1)
            time.sleep(wait_for)
            resp = requests.get(url, headers=_bearer_headers(), params=params, timeout=20)
    resp.raise_for_status()
    _last_call_ts = time.time()
    data = resp.json()
    payload = data.get("data") or {}
    text = payload.get("text", "")
    urls = []
    entities = payload.get("entities") or {}
    for item in entities.get("urls", []) or []:
        expanded = item.get("expanded_url")
        if expanded:
            urls.append(expanded)
    return {
        "text": text,
        "urls": urls,
        "author_id": payload.get("author_id"),
        "conversation_id": payload.get("conversation_id"),
    }


def fetch_tweet_text(status_id: str) -> str:
    return fetch_tweet_payload(status_id).get("text", "")


def fetch_username(author_id: str) -> Optional[str]:
    global _last_call_ts
    if _last_call_ts is not None:
        elapsed = time.time() - _last_call_ts
        delay = max(0.0, settings.x_min_seconds_between_calls - elapsed)
        if delay > 0:
            time.sleep(delay)
    url = f"https://api.x.com/2/users/{author_id}"
    resp = requests.get(url, headers=_bearer_headers(), timeout=20)
    if resp.status_code == 429:
        reset = resp.headers.get("x-rate-limit-reset")
        if reset and reset.isdigit():
            wait_for = max(0, int(reset) - int(time.time()) + 1)
            time.sleep(wait_for)
            resp = requests.get(url, headers=_bearer_headers(), timeout=20)
    resp.raise_for_status()
    _last_call_ts = time.time()
    data = resp.json()
    return (data.get("data") or {}).get("username")


def fetch_thread_text(conversation_id: str, username: str) -> list[str]:
    global _last_call_ts
    if _last_call_ts is not None:
        elapsed = time.time() - _last_call_ts
        delay = max(0.0, settings.x_min_seconds_between_calls - elapsed)
        if delay > 0:
            time.sleep(delay)
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": f"conversation_id:{conversation_id} from:{username}",
        "max_results": 100,
        "tweet.fields": "created_at",
    }
    resp = requests.get(url, headers=_bearer_headers(), params=params, timeout=20)
    if resp.status_code == 429:
        reset = resp.headers.get("x-rate-limit-reset")
        if reset and reset.isdigit():
            wait_for = max(0, int(reset) - int(time.time()) + 1)
            time.sleep(wait_for)
            resp = requests.get(url, headers=_bearer_headers(), params=params, timeout=20)
    resp.raise_for_status()
    _last_call_ts = time.time()
    data = resp.json()
    tweets = data.get("data") or []
    tweets.sort(key=lambda item: item.get("created_at", ""))
    return [item.get("text", "") for item in tweets if item.get("text")]


def search_recent_tweets(query: str, max_results: int = 10) -> list[dict]:
    """Search recent tweets by query and return text + id + author_id."""
    global _last_call_ts
    if _last_call_ts is not None:
        elapsed = time.time() - _last_call_ts
        delay = max(0.0, settings.x_min_seconds_between_calls - elapsed)
        if delay > 0:
            time.sleep(delay)
    url = "https://api.x.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": max(10, min(max_results, 100)),
        "tweet.fields": "created_at,author_id",
    }
    resp = requests.get(url, headers=_bearer_headers(), params=params, timeout=20)
    if resp.status_code == 429:
        reset = resp.headers.get("x-rate-limit-reset")
        if reset and reset.isdigit():
            wait_for = max(0, int(reset) - int(time.time()) + 1)
            time.sleep(wait_for)
            resp = requests.get(url, headers=_bearer_headers(), params=params, timeout=20)
    resp.raise_for_status()
    _last_call_ts = time.time()
    data = resp.json()
    tweets = data.get("data") or []
    results = []
    for item in tweets[:max_results]:
        results.append({
            "id": item.get("id"),
            "text": item.get("text", ""),
            "author_id": item.get("author_id"),
            "created_at": item.get("created_at"),
        })
    return results
