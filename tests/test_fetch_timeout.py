import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from main import scrape_for_day
from scrapers.base import fetch_html

STOCKHOLM = ZoneInfo("Europe/Stockholm")


class TimeoutScraper:
    def get_menu_for_day(self, day):
        fetch_html("https://example.test/lunch")
        return None


def test_timeout_is_missing_without_hanging(monkeypatch, tmp_path):
    def boom(self, url, **kwargs):
        raise requests.Timeout("slow")

    monkeypatch.setattr(requests.Session, "get", boom)
    delays = []
    started = time.monotonic()
    meta = scrape_for_day(
        "friday",
        refresh=True,
        data_dir=str(tmp_path),
        scrapers=[TimeoutScraper],
        now=datetime(2026, 11, 13, 11, 0, tzinfo=STOCKHOLM),
        max_retries=2,
        sleeper=delays.append,
    )
    elapsed = time.monotonic() - started

    assert meta["missing"] == ["TimeoutScraper"]
    assert meta["fresh"] == []
    assert delays == [3, 4]
    assert elapsed < 2
