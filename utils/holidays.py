"""Swedish public holidays and common bridge days, from data/holidays_se.json."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

_PATH = Path("data/holidays_se.json")


def load_holidays(path: Path | None = None) -> list[dict]:
    source = path or _PATH
    if not source.exists():
        return []
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    days = data.get("days") if isinstance(data, dict) else None
    return [day for day in days or [] if isinstance(day, dict) and day.get("date")]


def holiday_dates(path: Path | None = None) -> list[str]:
    return [day["date"] for day in load_holidays(path)]


def is_holiday(value: date | datetime | str, path: Path | None = None) -> bool:
    if isinstance(value, datetime):
        key = value.date().isoformat()
    elif isinstance(value, date):
        key = value.isoformat()
    else:
        key = str(value)[:10]
    return key in set(holiday_dates(path))
