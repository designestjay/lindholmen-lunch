# tests/test_mat_minnen.py


from scrapers.mat_minnen import MatMinnenScraper
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

def test_mat_minnen_for_day(day: str):
    scraper = MatMinnenScraper()

    menu = scraper.get_menu_for_day(day)
    if menu:
        print_menu(menu)
    else:
        print(f"No menu found for {day}.")

if __name__ == "__main__":
    # Change this to test different days
    test_mat_minnen_for_day("monday")
    test_mat_minnen_for_day("wednesday")
    test_mat_minnen_for_day("friday")
