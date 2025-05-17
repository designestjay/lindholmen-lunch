# tests/test_mimolett.py

from scrapers.mimolett import MimolettScraper

def print_menu(menu):
    print(f"Menu for {menu.day.capitalize()}:")
    for item in menu.items:
        if item.category:
            print(f"• {item.category}: {item.name}" + (f" - {item.description}" if item.description else ""))
        else:
            print(f"• {item.name}")

def test_mimolett_for_day(day: str):
    scraper = MimolettScraper()
    menu = scraper.get_menu_for_day(day)
    if menu:
        print_menu(menu)
    else:
        print(f"No menu found for {day}.")

if __name__ == "__main__":
    test_mimolett_for_day("monday")
