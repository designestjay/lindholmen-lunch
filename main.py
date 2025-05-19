# file: lindholmen_lunch/main.py

import argparse
import json
import logging
import os
import time
import traceback

from scrapers.kooperativet import KooperativetScraper
from scrapers.district_one import DistrictOneScraper
from scrapers.bombay_bistro import BombayBistroScraper
from scrapers.cuckoos_nest import CuckoosNestScraper
#from scrapers.uni3_world_of_food import Uni3WorldOfFoodScraper
from scrapers.miss_f import MissFScraper
from scrapers.benne_pastabar import BennePastabarScraper
from scrapers.ls_kitchen import LsKitchenScraper
from scrapers.bistrot import BistrotScraper
from scrapers.mimolett import MimolettScraper
from scrapers.oishii import OishiiScraper
from scrapers.mat_minnen import MatMinnenScraper
from scrapers.encounter_asian import EncounterAsianScraper
from utils import get_today_english
from generate_html import generate_lunch_summary, generate_index_page


logging.basicConfig(level=logging.INFO)

OUTPUT_DIR = "docs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SCRAPERS = [
    KooperativetScraper,
    DistrictOneScraper,
    BombayBistroScraper,
    CuckoosNestScraper,
    #Uni3WorldOfFoodScraper,
    MissFScraper,
    BennePastabarScraper,
    LsKitchenScraper,
    BistrotScraper,
    MimolettScraper,
    OishiiScraper,
    MatMinnenScraper,
    EncounterAsianScraper,
]

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]

def scrape_for_day(day: str, refresh: bool = False):
    logging.info(f"Scraping lunch menus for {day.capitalize()}")

    filepath = f"data/lunch_data_{day}.json"
    if os.path.exists(filepath) and not refresh:
        logging.info(f"Skipping scraping for {day} (cached file exists).")
        generate_lunch_summary(day)
        return

    results = {}

    for scraper_cls in SCRAPERS:
        attempts = 0
        max_retries = 2
        while attempts <= max_retries:
            try:
                scraper = scraper_cls()

                # If the scraper supports get_all_menus(), use that instead
                all_menus = scraper.get_all_menus()
                if all_menus:
                    menu = all_menus.get(day.lower())
                    if not menu:
                        logging.warning(f"No menu found in get_all_menus() for {scraper_cls.__name__} on {day}")
                        break
                    results[scraper_cls.__name__] = {
                        "day": menu.day,
                        "items": [
                            {"name": item.name, "category": item.category or "", "description": item.description or ""}
                            for item in menu.items
                        ]
                    }
                    break

                else:
                    # Fallback to per-day
                    menu = scraper.get_menu_for_day(day)
                    if not menu:
                        logging.warning(f"No menu found for {scraper_cls.__name__} on {day}")
                        break  # no point retrying if no data for this day
                    results[scraper_cls.__name__] = {
                        "day": menu.day,
                        "items": [
                            {
                                "name": item.name,
                                "category": item.category or "",
                                "description": item.description or "",
                            }
                            for item in menu.items
                        ]
                    }
                    break
            except Exception as e:
                attempts += 1
                logging.error(f"[{scraper_cls.__name__}] Error on attempt {attempts} for {day}: {e}")
                traceback.print_exc()
                if attempts > max_retries:
                    logging.warning(f"[{scraper_cls.__name__}] Gave up after {max_retries} retries.")
                else:
                    delay = 2 + attempts  # increase delay slightly each retry
                    logging.info(f"[{scraper_cls.__name__}] Retrying in {delay} seconds...")
                    time.sleep(delay)




    if results:
        os.makedirs("data", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logging.info(f"Wrote lunch data to {filepath}")
    else:
        logging.warning(f"No results to write for {day}. Skipping JSON and HTML.")
        return
    generate_lunch_summary(day)

def main():
    parser = argparse.ArgumentParser(description="Run Lindholmen lunch scrapers.")
    parser.add_argument("--day", type=str, help="Weekday to scrape (e.g., monday)", choices=WEEKDAYS)
    parser.add_argument("--all", action="store_true", help="Scrape all weekdays (mon–fri)")
    parser.add_argument("--refresh", action="store_true", help="Force re-scraping even if data exists")

    args = parser.parse_args()

    if args.all:
        for day in WEEKDAYS:
            scrape_for_day(day, refresh=args.refresh)
    else:
        day = args.day or get_today_english()
        scrape_for_day(day, refresh=args.refresh)

if __name__ == "__main__":
    main()
    generate_index_page()
