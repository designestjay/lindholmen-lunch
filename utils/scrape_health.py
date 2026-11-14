"""Scrape coverage report for the GitHub Actions job summary.

The last scheduled run of the day fails when fewer than half the restaurants
are fresh, which makes GitHub email the repository owner.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from utils.restaurants import DISPLAY_NAMES, display_name

# Off-peak weekday crons in .github/workflows/update-and-deploy.yml.
# The last one is the run that is allowed to fail the job.
SCHEDULES = ("7 5 * * 1-5", "37 6 * * 1-5", "7 8 * * 1-5")
LAST_SCHEDULE = SCHEDULES[-1]


def load_meta(data_dir: str | Path, day: str) -> dict:
    path = Path(data_dir) / f"scrape_meta_{day}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def coverage_should_fail(fresh: int, total: int, schedule: str) -> bool:
    """Fail only the last scheduled run, and only when fresh is under half."""
    if schedule != LAST_SCHEDULE or total <= 0:
        return False
    return (fresh / total) < 0.5


def cron_delay_minutes(schedule: str, started_at: datetime) -> int | None:
    """Minutes between the cron slot (UTC) and the actual job start."""
    parts = (schedule or "").split()
    if len(parts) < 2:
        return None
    try:
        minute = int(parts[0])
        hour = int(parts[1])
    except ValueError:
        return None
    started = started_at.astimezone(timezone.utc)
    scheduled = started.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return int((started - scheduled).total_seconds() // 60)


def _status_for(name: str, meta: dict) -> str:
    if name in set(meta.get("fresh") or []):
        return "fresh"
    if name in set(meta.get("stale") or []):
        return "stale"
    return "missing"


def render_summary(
    meta: dict,
    names: list[str],
    schedule: str,
    started_at: datetime | None,
) -> str:
    total = len(names) or 1
    rows = [(name, _status_for(name, meta)) for name in names]
    fresh = sum(1 for _, status in rows if status == "fresh")
    stale = sum(1 for _, status in rows if status == "stale")
    missing = sum(1 for _, status in rows if status == "missing")
    lines = [
        f"## Scrape health {meta.get('day') or 'unknown'}",
        "",
        "| Restaurant | Status |",
        "|---|---|",
    ]
    for name, status in rows:
        lines.append(f"| {display_name(name)} | {status} |")
    lines.extend(
        [
            "",
            f"Fresh {fresh} / {total} ({round(100 * fresh / total)}%). Stale {stale}. Missing {missing}.",
        ]
    )
    if schedule:
        lines.append(f"Scheduled cron: `{schedule}`.")
    else:
        lines.append("Not a scheduled run.")
    if started_at is not None:
        lines.append(f"Job started: {started_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC.")
        delay = cron_delay_minutes(schedule, started_at)
        if delay is not None:
            lines.append(f"Start delay versus cron: {delay} min.")
    if coverage_should_fail(fresh, total, schedule):
        lines.append("")
        lines.append("Fresh coverage is under 50% on the last scheduled run. The job will fail.")
    lines.append("")
    return "\n".join(lines)


def _parse_started(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def write_github_output(path: str, values: dict[str, str]) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def run(
    *,
    data_dir: str = "data",
    day: str = "",
    schedule: str = "",
    started_at: str = "",
    summary_path: str = "",
    github_output: str = "",
    names: list[str] | None = None,
) -> int:
    names = names if names is not None else list(DISPLAY_NAMES)
    schedule = (schedule or "").strip()
    day = (day or "").strip().lower()
    meta = load_meta(data_dir, day) if day else {}
    started = _parse_started(started_at)
    summary = render_summary(meta, names, schedule, started)
    print(summary)
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(summary)
            if not summary.endswith("\n"):
                handle.write("\n")
    fresh = sum(1 for name in names if _status_for(name, meta) == "fresh")
    should_fail = coverage_should_fail(fresh, len(names), schedule)
    report_date = ""
    scraped_at = meta.get("scraped_at") or ""
    if isinstance(scraped_at, str) and len(scraped_at) >= 10:
        report_date = scraped_at[:10]
    write_github_output(
        github_output,
        {
            "fail": "true" if should_fail else "false",
            "open_issue": "true" if should_fail else "false",
            "report_date": report_date or day,
        },
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the scrape health summary.")
    parser.add_argument("--day", default=os.environ.get("LUNCH_DAY", ""))
    parser.add_argument("--schedule", default=os.environ.get("LUNCH_SCHEDULE", ""))
    parser.add_argument("--started-at", default=os.environ.get("LUNCH_STARTED_AT", ""))
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--summary", default=os.environ.get("GITHUB_STEP_SUMMARY", ""))
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT", ""))
    args = parser.parse_args()
    return run(
        data_dir=args.data_dir,
        day=args.day,
        schedule=args.schedule,
        started_at=args.started_at,
        summary_path=args.summary,
        github_output=args.github_output,
    )


if __name__ == "__main__":
    raise SystemExit(main())
