"""Decide which scraper GitHub issues to open, comment on, or close.

The workflow applies data/issue_actions.json. This module never calls GitHub.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from utils.restaurants import display_name
from utils.sources import is_inactive, is_link_only, load_sources

FAILING = {"missing", "wrong_week", "static_old"}
HISTORY_LIMIT = 8


def _status(name: str, meta: dict) -> tuple[str, str]:
    reasons = meta.get("missing_reason") or {}
    if name in set(meta.get("fresh") or []):
        return "fresh", ""
    if name in set(meta.get("closed") or []):
        return "fresh", ""
    if name in set(meta.get("wrong_week") or []):
        return "wrong_week", reasons.get(name) or "wrong_week"
    if name in set(meta.get("stale") or []):
        return "static_old", reasons.get(name) or ""
    if name in set(meta.get("missing") or []):
        return "missing", reasons.get(name) or "empty"
    return "missing", reasons.get(name) or "empty"


def _record(history: dict, name: str, day_date: str, status: str, reason: str) -> None:
    rows = [row for row in history.get(name) or [] if row.get("date") != day_date]
    rows.append({"date": day_date, "status": status, "reason": reason})
    rows.sort(key=lambda row: row["date"])
    history[name] = rows[-HISTORY_LIMIT:]


def _last_fresh(rows: list[dict]) -> str:
    fresh = [row["date"] for row in rows if row.get("status") == "fresh"]
    return fresh[-1] if fresh else ""


def plan_issues(meta: dict, history: dict, *, sources: dict | None = None) -> dict:
    """Update history in place and return open/comment/close actions."""
    sources = sources if sources is not None else load_sources()
    day_date = (meta.get("menu_date") or meta.get("scraped_at") or "")[:10]
    actions = {"open": [], "comment": [], "close": []}
    if not day_date:
        return actions
    names = set(meta.get("fresh") or [])
    names.update(meta.get("stale") or [])
    names.update(meta.get("missing") or [])
    names.update(meta.get("wrong_week") or [])
    names.update(meta.get("closed") or [])
    for name in sorted(names):
        if is_inactive(name, sources) or is_link_only(name, sources):
            continue
        status, reason = _status(name, meta)
        _record(history, name, day_date, status, reason)
        rows = history.get(name) or []
        title = f"Scraper: {display_name(name)} failing"
        recent = rows[-5:]
        body = "\n".join(
            [
                f"Restaurant: {display_name(name)}",
                f"Status: {status}",
                f"Reason: {reason or '-'}",
                f"Source: {(sources.get(name) or {}).get('source', {}).get('url', '')}",
                f"Last fresh date: {_last_fresh(rows) or '-'}",
                "",
                "Recent runs:",
                *[f"- {row['date']}: {row['status']} {row.get('reason') or ''}".rstrip() for row in recent],
            ]
        )
        failing_days = [row for row in rows if row.get("status") in FAILING]
        distinct = []
        for row in failing_days:
            if row["date"] not in distinct:
                distinct.append(row["date"])
        if status == "fresh":
            if len(distinct) >= 2:
                actions["close"].append({"title": title, "body": f"{display_name(name)} is fresh again ({day_date})."})
            continue
        if len(distinct) < 2:
            continue
        if distinct[-1] != day_date:
            continue
        if len(distinct) == 2:
            actions["open"].append({"title": title, "body": body, "label": "scraper"})
        else:
            actions["comment"].append({"title": title, "body": body})
    return actions


def write_actions(data_dir: Path, day: str) -> dict:
    meta_path = data_dir / f"scrape_meta_{day}.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    history_path = data_dir / "scraper_status_history.json"
    history = {}
    if history_path.exists():
        loaded = json.loads(history_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            history = loaded
    actions = plan_issues(meta, history)
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    actions_path = data_dir / "issue_actions.json"
    actions_path.write_text(json.dumps(actions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan per-restaurant scraper issues.")
    parser.add_argument("--day", required=True)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    write_actions(Path(args.data_dir), args.day.lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
