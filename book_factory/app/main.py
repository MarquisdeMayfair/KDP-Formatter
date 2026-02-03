"""FastAPI entrypoint for Book Factory."""
from __future__ import annotations

import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api import silos, topics, trends
from app.config import settings
from app.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
    Path(settings.storage_path).mkdir(parents=True, exist_ok=True)
    logger.info("Book Factory started")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


app.include_router(topics.router, prefix="/api/v1")
app.include_router(silos.router, prefix="/api/v1")
app.include_router(trends.router, prefix="/api/v1")
