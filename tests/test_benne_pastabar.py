from scrapers.benne_pastabar import BennePastabarScraper

def test_benne_pastabar_for_day(day: str):
    scraper = BennePastabarScraper()
    menu = scraper.get_menu_for_day(day)
    if not menu:
        print(f"No menu found for {day}.")
        return

    print(f"Menu for {day.capitalize()}:")
    for item in menu.items:
        print(f"• {item}")

if __name__ == "__main__":
    test_benne_pastabar_for_day("wednesday")
