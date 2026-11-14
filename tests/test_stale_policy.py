import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from main import scrape_for_day

STOCKHOLM = ZoneInfo("Europe/Stockholm")


class _Item:
    def __init__(self, name):
        self.name = name
        self.category = ""
        self.description = ""
        self.price = "90 kr"


class _Menu:
    def __init__(self, day):
        self.day = day
        self.items = [_Item("Sallad")]


class OkScraper:
    def get_menu_for_day(self, day):
        return _Menu(day)


class BoomScraper:
    def get_menu_for_day(self, day):
        raise RuntimeError("down")


class AlsoDownScraper:
    def get_menu_for_day(self, day):
        raise RuntimeError("down")


def _write_previous(directory, name, scraped_at, fetched_at):
    payload = {
        name: {
            "day": "friday",
            "items": [{"name": "Gammal rätt", "description": "", "category": "", "price": "100 kr"}],
            "fetched_at": fetched_at,
        }
    }
    meta = {
        "day": "friday",
        "scraped_at": scraped_at.isoformat(timespec="minutes"),
        "fresh": [name],
        "stale": [],
        "missing": [],
    }
    (directory / "lunch_data_friday.json").write_text(json.dumps(payload), encoding="utf-8")
    (directory / "scrape_meta_friday.json").write_text(json.dumps(meta), encoding="utf-8")


def test_week_old_previous_is_missing(tmp_path):
    now = datetime(2026, 11, 14, 9, 0, tzinfo=STOCKHOLM)
    old = now - timedelta(days=7)
    _write_previous(tmp_path, "BoomScraper", old, old.isoformat(timespec="minutes"))

    meta = scrape_for_day(
        "friday",
        refresh=True,
        data_dir=str(tmp_path),
        scrapers=[BoomScraper],
        now=now,
        max_retries=0,
        sleeper=lambda _delay: None,
    )

    assert meta["missing"] == ["BoomScraper"]
    assert meta["stale"] == []
    saved = json.loads((tmp_path / "lunch_data_friday.json").read_text(encoding="utf-8"))
    assert "BoomScraper" not in saved


def test_same_day_previous_is_stale_and_keeps_fetched_at(tmp_path):
    now = datetime(2026, 11, 14, 9, 0, tzinfo=STOCKHOLM)
    earlier = now - timedelta(hours=2)
    fetched_at = earlier.isoformat(timespec="minutes")
    _write_previous(tmp_path, "BoomScraper", earlier, fetched_at)

    meta = scrape_for_day(
        "friday",
        refresh=True,
        data_dir=str(tmp_path),
        scrapers=[BoomScraper],
        now=now,
        max_retries=0,
        sleeper=lambda _delay: None,
    )

    assert meta["stale"] == ["BoomScraper"]
    assert meta["missing"] == []
    saved = json.loads((tmp_path / "lunch_data_friday.json").read_text(encoding="utf-8"))
    assert saved["BoomScraper"]["stale"] is True
    assert saved["BoomScraper"]["fetched_at"] == fetched_at


def test_fresh_scrape_sets_fetched_at(tmp_path):
    now = datetime(2026, 11, 14, 7, 12, tzinfo=STOCKHOLM)
    meta = scrape_for_day(
        "friday",
        refresh=True,
        data_dir=str(tmp_path),
        scrapers=[OkScraper],
        now=now,
        max_retries=0,
        sleeper=lambda _delay: None,
    )
    assert meta["fresh"] == ["OkScraper"]
    saved = json.loads((tmp_path / "lunch_data_friday.json").read_text(encoding="utf-8"))
    assert saved["OkScraper"]["fetched_at"] == "2026-11-14T07:12+01:00"
    assert saved["OkScraper"]["stale"] is False
