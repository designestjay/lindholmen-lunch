import pytest

pytestmark = pytest.mark.network

# tests/test_bistrot.py

from scrapers.bistrot import BistrotScraper

def print_menu(menu):
    print(f"Menu for {menu.day.capitalize()}:")
    for item in menu.items:
        print(f"• {item}")

def test_bistrot_for_day(day: str):
    scraper = BistrotScraper()
    menu = scraper.get_menu_for_day(day)
    if menu:
        print_menu(menu)
    else:
        print(f"No menu found for {day}.")

if __name__ == "__main__":
    # Change these to test different days
    test_bistrot_for_day("monday")
    #test_bistrot_for_day("wednesday")
    #test_bistrot_for_day("friday")
