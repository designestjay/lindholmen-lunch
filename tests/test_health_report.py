import json
from datetime import datetime, timedelta, timezone

from main import scrape_for_day
from utils.scrape_health import coverage_should_fail, render_summary, run


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


def _ok(name):
    class Scraper:
        def get_menu_for_day(self, day):
            return _Menu(day)

    Scraper.__name__ = name
    return Scraper


def _down(name):
    class Scraper:
        def get_menu_for_day(self, day):
            raise RuntimeError(name)

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


def test_two_failures_are_missing_in_the_summary(tmp_path):
    scrapers = [_ok("AlphaScraper"), _ok("BetaScraper"), _down("GammaScraper"), _down("DeltaScraper")]
    meta = _scrape(tmp_path, scrapers)
    names = [scraper.__name__ for scraper in scrapers]
    summary = render_summary(meta, names, "7 5 * * 1-5", datetime(2026, 11, 14, 5, 40, tzinfo=timezone.utc))

    assert "Gamma" in summary
    assert "Delta" in summary
    assert summary.count("| missing |") == 2
    assert coverage_should_fail(len(meta["fresh"]), len(names), "7 8 * * 1-5") is False


def test_majority_failure_fails_only_the_last_run(tmp_path):
    scrapers = [_ok("AlphaScraper"), _down("BetaScraper"), _down("GammaScraper"), _down("DeltaScraper")]
    meta = _scrape(tmp_path, scrapers)
    names = [scraper.__name__ for scraper in scrapers]
    fresh = len(meta["fresh"])
    assert fresh == 1
    assert coverage_should_fail(fresh, len(names), "7 8 * * 1-5") is True
    assert coverage_should_fail(fresh, len(names), "7 5 * * 1-5") is False
    assert coverage_should_fail(fresh, len(names), "") is False

    summary_path = tmp_path / "summary.md"
    output_path = tmp_path / "github_output.txt"
    run(
        data_dir=str(tmp_path),
        day="friday",
        schedule="7 8 * * 1-5",
        started_at="2026-11-13T08:40:00Z",
        summary_path=str(summary_path),
        github_output=str(output_path),
        names=names,
    )
    output = output_path.read_text(encoding="utf-8")
    assert "fail=true" in output
    assert "open_issue=true" in output
    summary = summary_path.read_text(encoding="utf-8")
    assert "Beta" in summary
    assert "missing" in summary
    assert "33 min" in summary
