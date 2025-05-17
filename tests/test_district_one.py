# tests/test_district_one.py

from scrapers.district_one import DistrictOneScraper

def test_district_one_for_day(day: str):
    scraper = DistrictOneScraper()
    menu = scraper.get_menu_for_day(day)

    if not menu:
        print(f"No menu found for {day}.")
        return

    print(f"Menu for {day.capitalize()}:")
    last_category = None
    for item in menu.items:
        if item.category != last_category:
            print(f"\n== {item.category.upper()} ==" if item.category else "")
            last_category = item.category
        print(f"• {item}")

if __name__ == "__main__":
    test_district_one_for_day("monday")
    test_district_one_for_day("wednesday")
    test_district_one_for_day("friday")
