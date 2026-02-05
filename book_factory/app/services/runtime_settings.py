"""Runtime settings overrides stored on disk."""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings


def _settings_path() -> Path:
    # Place runtime settings alongside the database file.
    return Path(settings.database_path).parent / "runtime_settings.json"


def load_runtime_settings() -> dict:
    path = _settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_runtime_settings(data: dict) -> None:
    path = _settings_path()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
