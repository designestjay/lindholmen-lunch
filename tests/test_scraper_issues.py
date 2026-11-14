from utils.scraper_issues import plan_issues


def test_two_failing_weekdays_open_one_issue_and_a_fresh_day_closes_it():
    sources = {
        "BistrotScraper": {"source": {"url": "https://bistrot.se/"}},
    }
    history = {}
    first = plan_issues(
        {"menu_date": "2026-11-12", "missing": ["BistrotScraper"], "missing_reason": {"BistrotScraper": "timeout"}},
        history,
        sources=sources,
    )
    assert first["open"] == []
    second = plan_issues(
        {"menu_date": "2026-11-13", "missing": ["BistrotScraper"], "missing_reason": {"BistrotScraper": "empty"}},
        history,
        sources=sources,
    )
    assert len(second["open"]) == 1
    assert second["open"][0]["title"] == "Scraper: Bistrot failing"
    third = plan_issues(
        {"menu_date": "2026-11-16", "missing": ["BistrotScraper"], "missing_reason": {"BistrotScraper": "timeout"}},
        history,
        sources=sources,
    )
    assert third["open"] == []
    assert len(third["comment"]) == 1
    closed = plan_issues(
        {"menu_date": "2026-11-17", "fresh": ["BistrotScraper"]},
        history,
        sources=sources,
    )
    assert closed["close"][0]["title"] == "Scraper: Bistrot failing"
