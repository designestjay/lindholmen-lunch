"""Load data/sources.json. Missing file means every scraper stays active."""

from __future__ import annotations

import json
from pathlib import Path

_PATH = Path("data/sources.json")


def load_sources(path: Path | None = None) -> dict:
    source = path or _PATH
    if not source.exists():
        return {}
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def source_for(name: str, sources: dict | None = None) -> dict:
    return (sources if sources is not None else load_sources()).get(name) or {}


def is_inactive(name: str, sources: dict | None = None) -> bool:
    return source_for(name, sources).get("active") is False


def is_link_only(name: str, sources: dict | None = None) -> bool:
    return bool(source_for(name, sources).get("link_only"))


def week_marker_required(name: str, sources: dict | None = None) -> bool:
    return bool(source_for(name, sources).get("week_marker"))


def is_rotating(name: str, sources: dict | None = None) -> bool:
    info = source_for(name, sources)
    return info.get("cadence") == "rotation" or bool(info.get("rotating"))
