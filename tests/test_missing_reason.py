from datetime import datetime, timedelta, timezone

import requests

from main import scrape_for_day
from utils.scrape_health import render_summary


class _Item:
    def __init__(self):
        self.name = "Sallad"
        self.category = ""
        self.description = ""
        self.price = "90 kr"


class _Menu:
    def __init__(self, day):
        self.day = day
        self.items = [_Item()]


def _named(name, method):
    class Scraper:
        def get_menu_for_day(self, day):
            return method(day)

    Scraper.__name__ = name
    return Scraper


def _scrape(tmp_path, scrapers):
    now = datetime(2026, 11, 14, 9, 0, tzinfo=timezone(timedelta(hours=1)))
    return scrape_for_day(
        "friday",
        refresh=True,
        data_dir=str(tmp_path),
        scrapers=scrapers,
        now=now,
        max_retries=0,
        sleeper=lambda _delay: None,
    )


def test_http_timeout_error_and_empty_reasons(tmp_path):
    response = requests.Response()
    response.status_code = 404

    def http_down(_day):
        raise requests.HTTPError(response=response)

    def timed_out(_day):
        raise requests.Timeout("slow")

    def crashed(_day):
        raise RuntimeError("down")

    def blank(_day):
        return None

    scrapers = [
        _named("DistrictOneScraper", http_down),
        _named("PierScraper", timed_out),
        _named("GammaScraper", crashed),
        _named("DeltaScraper", blank),
        _named("AlphaScraper", lambda day: _Menu(day)),
    ]
    meta = _scrape(tmp_path, scrapers)

    assert meta["missing_reason"] == {
        "DistrictOneScraper": "http_404",
        "PierScraper": "timeout",
        "GammaScraper": "error:RuntimeError",
        "DeltaScraper": "empty",
    }
    assert "AlphaScraper" not in meta["missing_reason"]

    summary = render_summary(meta, [scraper.__name__ for scraper in scrapers], "", None)
    assert "| District One | missing | http_404 |" in summary
    assert "| Pier | missing | timeout |" in summary
    assert "| Gamma | missing | error:RuntimeError |" in summary
    assert "| Delta | missing | empty |" in summary
    assert "| Alpha | fresh |  |" in summary
