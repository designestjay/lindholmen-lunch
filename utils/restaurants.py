"""Restaurant display helpers shared by scraping and HTML generation."""

from __future__ import annotations

DISPLAY_NAMES = {
    "KooperativetScraper": "Kooperativet",
    "DistrictOneScraper": "District One",
    "BombayBistroScraper": "Bombay Bistro",
    "CuckoosNestScraper": "Cuckoo's Nest",
    "Uni3WorldOfFoodScraper": "Uni3 World of Food",
    "MissFScraper": "Miss F",
    "BennePastabarScraper": "Benne Pastabar",
    "LsKitchenScraper": "LS Kitchen",
    "BistrotScraper": "Bistrot",
    "MimolettScraper": "Mimolett",
    "OishiiScraper": "Oishii",
    "MatMinnenScraper": "Mat & Minnen",
    "EncounterAsianScraper": "Encounter Asian",
    "MasalaScraper": "Masala",
    "RestaurantPier11Scraper": "Pier 11",
}

# Keys used in data/restaurant_links.json
LINK_KEYS = {
    "KooperativetScraper": "Kooperativet",
    "DistrictOneScraper": "DistrictOne",
    "BombayBistroScraper": "BombayBistro",
    "CuckoosNestScraper": "CuckoosNest",
    "Uni3WorldOfFoodScraper": "Uni3WorldOfFood",
    "MissFScraper": "MissF",
    "BennePastabarScraper": "BennePastabar",
    "LsKitchenScraper": "LsKitchen",
    "BistrotScraper": "Bistrot",
    "MimolettScraper": "Mimolett",
    "OishiiScraper": "Oishii",
    "MatMinnenScraper": "MatMinnen",
    "EncounterAsianScraper": "EncounterAsian",
    "MasalaScraper": "Masala",
    "RestaurantPier11Scraper": "RestaurantPier11",
}


def display_name(scraper_key: str) -> str:
    if scraper_key in DISPLAY_NAMES:
        return DISPLAY_NAMES[scraper_key]
    cleaned = scraper_key.replace("Scraper", "").replace("_", " ")
    return cleaned


def link_key(scraper_key: str) -> str:
    return LINK_KEYS.get(scraper_key, scraper_key.replace("Scraper", ""))
