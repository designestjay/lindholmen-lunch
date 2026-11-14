from pathlib import Path

from scrapers.district_one import DistrictOneScraper

FIXTURE = Path(__file__).parent / "fixtures" / "district_one.html"


def test_district_one_parses_homepage_lunch_offline():
    scraper = DistrictOneScraper(html=FIXTURE.read_text(encoding="utf-8"))
    monday = scraper.get_menu_for_day("monday")

    assert monday is not None
    assert len(monday.items) >= 3
    assert all(item.name.strip() for item in monday.items)
    assert any("torsfile" in item.name.lower() for item in monday.items)
    assert monday.items[0].price == "135 kr"
    assert DistrictOneScraper.WEEKDAY_FROM_SV["måndag"] == "monday"
    assert DistrictOneScraper.WEEKDAY_FROM_SV["fredag"] == "friday"
    friday = scraper.get_menu_for_day("friday")
    assert friday is not None
    assert len(friday.items) >= 3
    assert scraper.get_menu_for_day("måndag") is None
