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


def fetch_tweet_text(status_id: str) -> str:
    global _last_call_ts
    if _last_call_ts is not None:
        elapsed = time.time() - _last_call_ts
        delay = max(0.0, settings.x_min_seconds_between_calls - elapsed)
        if delay > 0:
            time.sleep(delay)

    url = f"https://api.x.com/2/tweets/{status_id}"
    params = {"tweet.fields": "text,created_at,author_id"}
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
    return (data.get("data") or {}).get("text", "")
