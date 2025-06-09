# tests/test_restaurant_pier_11.py

from scrapers.restaurant_pier_11 import RestaurantPier11Scraper
import logging
logging.basicConfig(level=logging.INFO)

def test_pier11_for_day(day: str):
    scraper = RestaurantPier11Scraper()
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
    test_pier11_for_day("monday")
    test_pier11_for_day("tuesday")
    test_pier11_for_day("wednesday")
    test_pier11_for_day("thursday")
    test_pier11_for_day("friday")
