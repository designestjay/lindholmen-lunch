# tests/test_bombay_bistro.py

from scrapers.bombay_bistro import BombayBistroScraper
import logging
logging.basicConfig(level=logging.INFO)

def test_bombay_bistro_for_day(day: str):
    scraper = BombayBistroScraper()
    menu = scraper.get_menu_for_day(day)

    if not menu:
        print(f"No menu found for {day}.")
        return

    print(f"Menu for {day.capitalize()}:")
    last_category = None
    for item in menu.items:
        if item.category != last_category:
            print(f"\n== {item.category.upper()} ==")
            last_category = item.category
        print(f"• {item}")

if __name__ == "__main__":
    test_bombay_bistro_for_day("monday")
    test_bombay_bistro_for_day("wednesday")
    test_bombay_bistro_for_day("friday")
