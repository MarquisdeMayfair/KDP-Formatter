"""X API client for fetching tweet text via OAuth 1.0a."""
from __future__ import annotations

import re
from typing import Optional
from requests_oauthlib import OAuth1Session

from app.config import settings

STATUS_ID_RE = re.compile(r"/status/(\d+)")


def extract_status_id(url: str) -> Optional[str]:
    match = STATUS_ID_RE.search(url)
    if not match:
        return None
    return match.group(1)


def _oauth_session() -> OAuth1Session:
    if not all([
        settings.x_consumer_key,
        settings.x_consumer_secret,
        settings.x_access_token,
        settings.x_access_token_secret,
    ]):
        raise ValueError("X OAuth credentials missing")

    return OAuth1Session(
        settings.x_consumer_key,
        client_secret=settings.x_consumer_secret,
        resource_owner_key=settings.x_access_token,
        resource_owner_secret=settings.x_access_token_secret,
    )


def fetch_tweet_text(status_id: str) -> str:
    session = _oauth_session()
    url = "https://api.x.com/1.1/statuses/show.json"
    params = {"id": status_id, "tweet_mode": "extended"}
    resp = session.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get("full_text") or data.get("text") or ""
