from pathlib import Path

from scrapers.uni3_world_of_food import Uni3WorldOfFoodScraper

FIXTURE = Path(__file__).parent / "fixtures" / "uni3_week.xml"


def test_friday_stations_are_separate_dishes():
    scraper = Uni3WorldOfFoodScraper(rss=FIXTURE.read_text(encoding="utf-8"))
    friday = scraper.get_menu_for_day("friday")

    assert friday is not None
    assert [item.category for item in friday.items] == ["Metal", "Water", "Fire"]
    pesto, salmon, chicken = friday.items
    assert pesto.name == "Pasta pesto"
    assert pesto.description == "getost, bakade tomater, vitlöksstekta brödsmulor, pesto"
    assert "lax" not in pesto.description
    assert "kyckling" not in pesto.description.lower()
    assert "chicken" not in pesto.description.lower()
    assert "goat" not in pesto.description.lower()

    assert salmon.name == "Halstrad lax"
    assert "romsås" in salmon.description
    assert "pesto" not in salmon.description.lower()
    assert "kyckling" not in salmon.description.lower()

    assert "dopiaza" in chicken.name.lower()
    assert "kycklinglår" in chicken.description
    assert "lax" not in chicken.description.lower()
    assert "pesto" not in chicken.description.lower()


def test_separate_paragraphs_stay_one_dish_each():
    scraper = Uni3WorldOfFoodScraper(rss=FIXTURE.read_text(encoding="utf-8"))
    monday = scraper.get_menu_for_day("monday")

    assert monday is not None
    assert len(monday.items) == 4
    names = [item.name for item in monday.items]
    assert "Bakad fisk" in names
    assert "Pokebowl" in names
    for item in monday.items:
        assert item.description
        assert "<" not in item.description
        for other in names:
            if other != item.name:
                assert other.lower() not in item.description.lower()
