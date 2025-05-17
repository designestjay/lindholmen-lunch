from scrapers.miss_f import MissFScraper

def test_miss_f_for_day(day: str):
    scraper = MissFScraper()
    menu = scraper.get_menu_for_day(day)
    if not menu:
        print(f"No menu found for {day}.")
        return

    print(f"Menu for {day.capitalize()}:")
    last_cat = None
    for item in menu.items:
        if item.category != last_cat:
            print(f"\n== {item.category.upper()} ==")
            last_cat = item.category
        print(f"• {item}")

if __name__ == "__main__":
    test_miss_f_for_day("wednesday")
