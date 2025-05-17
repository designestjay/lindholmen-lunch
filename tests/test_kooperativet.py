# tests/test_kooperativet.py

from scrapers.kooperativet import KooperativetScraper

def print_menu(menu):
    print(f"Menu for {menu.day.capitalize()}:")
    current_category = None
    for item in menu.items:
        if item.category != current_category:
            current_category = item.category
            print(f"\n== {current_category or 'Other'} ==")
        print(f"• {item}")

def test_kooperativet_for_day(day: str):
    scraper = KooperativetScraper()

    menu = scraper.get_menu_for_day(day)
    if menu:
        print_menu(menu)
    else:
        print(f"No menu found for {day}.")

if __name__ == "__main__":
    # Change this to test a different day
    test_kooperativet_for_day("monday")
    test_kooperativet_for_day("wednesday")
    test_kooperativet_for_day("friday")
