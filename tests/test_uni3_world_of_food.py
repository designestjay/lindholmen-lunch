# tests/test_uni3_world_of_food.py

from scrapers.uni3_world_of_food import Uni3WorldOfFoodScraper
import logging
logging.basicConfig(level=logging.INFO)

def test_uni3_for_day(day: str):
    scraper = Uni3WorldOfFoodScraper()
    menu = scraper.get_menu_for_day(day)

    if not menu:
        print(f"No menu found for {day}.")
        return

    print(f"Menu for {day.capitalize()}:")
    last_category = None
    for item in menu.items:
        if item.category != last_category:
            print(f"\n== {item.category.upper() if item.category else 'DAGENS'} ==")
            last_category = item.category
        print(f"• {item}")

if __name__ == "__main__":
    test_uni3_for_day("monday")
    test_uni3_for_day("tuesday")
    test_uni3_for_day("wednesday")
    test_uni3_for_day("thursday")
    test_uni3_for_day("friday")
