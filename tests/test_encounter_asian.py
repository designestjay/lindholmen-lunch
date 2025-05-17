# tests/test_encounter_asian.py

from scrapers.encounter_asian import EncounterAsianScraper
import logging
logging.basicConfig(level=logging.INFO)

def print_menu(menu):
    print(f"Menu for {menu.day.capitalize()}:")
    current_category = None
    for item in menu.items:
        if item.category != current_category:
            current_category = item.category
            print(f"\n== {current_category or 'Other'} ==")
        description = f" – {item.description}" if item.description else ""
        print(f"• {item.name}{description}")

def test_encounter_asian_for_day(day: str):
    scraper = EncounterAsianScraper()
    menu = scraper.get_menu_for_day(day)
    if menu:
        print_menu(menu)
    else:
        print(f"No menu found for {day}.")

if __name__ == "__main__":
    #test_encounter_asian_for_day("monday")
    #test_encounter_asian_for_day("wednesday")
    test_encounter_asian_for_day("friday")
