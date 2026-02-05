"""System settings endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app import schemas
from app.config import settings
from app.services.runtime_settings import load_runtime_settings, save_runtime_settings

router = APIRouter(prefix="/settings", tags=["settings"])


def _current_caps() -> schemas.CapsOut:
    runtime = load_runtime_settings()
    return schemas.CapsOut(
        draft_max_words_per_silo=int(
            runtime.get("draft_max_words_per_silo", settings.draft_max_words_per_silo)
        ),
        draft_max_words_total=int(
            runtime.get("draft_max_words_total", settings.draft_max_words_total)
        ),
    )


@router.get("/caps", response_model=schemas.CapsOut)
async def get_caps():
    return _current_caps()


@router.post("/caps", response_model=schemas.CapsOut)
async def set_caps(request: Request):
    if request.headers.get("content-type", "").startswith("application/json"):
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    update = schemas.CapsUpdate(**payload)
    current = _current_caps()

    new_caps = {
        "draft_max_words_per_silo": update.draft_max_words_per_silo
        if update.draft_max_words_per_silo is not None
        else current.draft_max_words_per_silo,
        "draft_max_words_total": update.draft_max_words_total
        if update.draft_max_words_total is not None
        else current.draft_max_words_total,
    }
    save_runtime_settings(new_caps)

    if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        topic = payload.get("topic", "")
        suffix = f"?topic={topic}" if topic else ""
        return RedirectResponse(url=f"/dashboard{suffix}", status_code=303)

    return schemas.CapsOut(**new_caps)
