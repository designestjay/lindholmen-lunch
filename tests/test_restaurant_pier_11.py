from pathlib import Path

from scrapers.restaurant_pier_11 import RestaurantPier11Scraper

FIXTURE = Path(__file__).parent / "fixtures" / "pier11.html"


def test_pier11_parses_swedish_weekdays_offline():
    scraper = RestaurantPier11Scraper(html=FIXTURE.read_text(encoding="utf-8"))
    monday = scraper.get_menu_for_day("monday")

    assert monday is not None
    assert len(monday.items) >= 3
    assert all(item.name.strip() for item in monday.items)
    assert monday.items[0].name == "Kebab spiced soy strips"
    assert monday.items[0].price == "124 kr"
    assert RestaurantPier11Scraper.WEEKDAY_FROM_SV["måndag"] == "monday"
    assert RestaurantPier11Scraper.WEEKDAY_FROM_SV["fredag"] == "friday"
    assert set(scraper.get_all_menus()) >= {"monday", "tuesday", "wednesday", "thursday", "friday"}
    assert scraper.get_menu_for_day("måndag") is None
