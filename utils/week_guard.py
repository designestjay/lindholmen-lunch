"""Decide whether a scraped menu is the week we asked for."""

from __future__ import annotations

from datetime import datetime, timedelta

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]


def date_for_weekday(day: str, now: datetime):
    """Calendar date of `day` in the same week as `now`."""
    wanted = WEEKDAYS.index(day.lower())
    return now.date() - timedelta(days=now.weekday() - wanted)


def accept_menu(
    source_week,
    *,
    day: str,
    now: datetime,
    week_marker_required: bool,
) -> str:
    """Return 'ok' or 'wrong_week'.

    A numbered week that is not the target week's ISO week is never shown.
    On Friday after 13:00 local, a weekly source with no week number is
    also refused, so a next-week page cannot sneak in unlabelled.
    """
    target = date_for_weekday(day, now).isocalendar().week
    friday_afternoon = day.lower() == "friday" and now.hour >= 13
    if source_week is None:
        if friday_afternoon and week_marker_required:
            return "wrong_week"
        return "ok"
    try:
        week = int(source_week)
    except (TypeError, ValueError):
        return "wrong_week" if (friday_afternoon and week_marker_required) else "ok"
    if week != target:
        return "wrong_week"
    return "ok"
