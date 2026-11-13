# file: lindholmen_lunch/main.py

import argparse
import json
import logging
import os
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from scrapers.kooperativet import KooperativetScraper
from scrapers.district_one import DistrictOneScraper
from scrapers.bombay_bistro import BombayBistroScraper
from scrapers.cuckoos_nest import CuckoosNestScraper
from scrapers.uni3_world_of_food import Uni3WorldOfFoodScraper
from scrapers.miss_f import MissFScraper
from scrapers.benne_pastabar import BennePastabarScraper
from scrapers.ls_kitchen import LsKitchenScraper
from scrapers.bistrot import BistrotScraper
from scrapers.mimolett import MimolettScraper
from scrapers.oishii import OishiiScraper
from scrapers.mat_minnen import MatMinnenScraper
from scrapers.encounter_asian import EncounterAsianScraper
from scrapers.masala import MasalaScraper
from scrapers.restaurant_pier_11 import RestaurantPier11Scraper
from utils.utils import get_today_english
from generate_html import generate_index_page

logging.basicConfig(level=logging.INFO)

OUTPUT_DIR = "docs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SCRAPERS = [
    KooperativetScraper,
    DistrictOneScraper,
    BombayBistroScraper,
    CuckoosNestScraper,
    Uni3WorldOfFoodScraper,
    MissFScraper,
    BennePastabarScraper,
    LsKitchenScraper,
    BistrotScraper,
    MimolettScraper,
    OishiiScraper,
    MatMinnenScraper,
    EncounterAsianScraper,
    MasalaScraper,
    RestaurantPier11Scraper,
]

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
STOCKHOLM = ZoneInfo("Europe/Stockholm")


def _menu_payload(menu) -> dict:
    return {
        "day": menu.day,
        "items": [
            {
                "name": item.name,
                "category": item.category or "",
                "description": item.description or "",
                "price": item.price or "",
            }
            for item in menu.items
        ],
        "stale": False,
    }


def _load_previous(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as exc:
        logging.warning("Could not read previous data %s: %s", filepath, exc)
        return {}


def _scrape_one(scraper_cls, day: str, cache: dict | None):
    """Return a menu payload dict, or None if this restaurant has no menu today."""
    if cache is not None and scraper_cls.__name__ in cache:
        scraper = cache[scraper_cls.__name__]
    else:
        scraper = scraper_cls()
        if cache is not None and hasattr(scraper, "get_all_menus"):
            all_menus = scraper.get_all_menus()
            if all_menus:
                cache[scraper_cls.__name__] = scraper

    all_menus = scraper.get_all_menus()
    if all_menus:
        menu = all_menus.get(day.lower())
        if not menu or not getattr(menu, "items", None):
            return None
        return _menu_payload(menu)

    menu = scraper.get_menu_for_day(day)
    if not menu or not getattr(menu, "items", None):
        return None
    return _menu_payload(menu)


def scrape_for_day(day: str, refresh: bool = False, cache: dict = None):
    logging.info("Scraping lunch menus for %s", day.capitalize())

    filepath = f"data/lunch_data_{day}.json"
    if os.path.exists(filepath) and not refresh:
        logging.info("Skipping scraping for %s (cached file exists).", day)
        return

    previous = _load_previous(filepath)
    results = {}
    ok, stale_kept, failed = [], [], []

    for scraper_cls in SCRAPERS:
        name = scraper_cls.__name__
        attempts = 0
        max_retries = 2
        got = None

        while attempts <= max_retries:
            try:
                got = _scrape_one(scraper_cls, day, cache)
                break
            except Exception as e:
                attempts += 1
                logging.error("[%s] Error on attempt %s for %s: %s", name, attempts, day, e)
                traceback.print_exc()
                if attempts > max_retries:
                    logging.warning("[%s] Gave up after %s retries.", name, max_retries)
                else:
                    delay = 2 + attempts
                    logging.info("[%s] Retrying in %s seconds...", name, delay)
                    time.sleep(delay)

        if got and got.get("items"):
            results[name] = got
            ok.append(name)
            continue

        prev = previous.get(name)
        if isinstance(prev, dict) and prev.get("items"):
            carried = dict(prev)
            carried["stale"] = True
            carried["day"] = day.lower()
            # Drop annotation fields; generate_html will re-annotate.
            carried.pop("tags", None)
            carried.pop("emoji_tags", None)
            for item in carried.get("items") or []:
                if isinstance(item, dict):
                    item.pop("tags", None)
                    item.pop("emoji_tags", None)
            results[name] = carried
            stale_kept.append(name)
            logging.warning("[%s] No fresh menu; keeping previous data as stale.", name)
        else:
            failed.append(name)
            logging.warning("[%s] No menu for %s (and no previous data to keep).", name, day)

    logging.info(
        "Scrape summary for %s: %s fresh, %s stale, %s missing",
        day,
        len(ok),
        len(stale_kept),
        len(failed),
    )
    if failed:
        logging.info("Missing restaurants: %s", ", ".join(failed))

    meta = {
        "day": day,
        "scraped_at": datetime.now(STOCKHOLM).isoformat(timespec="minutes"),
        "fresh": ok,
        "stale": stale_kept,
        "missing": failed,
    }

    if results:
        os.makedirs("data", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        with open(f"data/scrape_meta_{day}.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        logging.info("Wrote lunch data to %s", filepath)
    else:
        logging.warning("No results to write for %s. Leaving existing file untouched.", day)


def main():
    parser = argparse.ArgumentParser(description="Run Lindholmen lunch scrapers.")
    parser.add_argument("--day", type=str, help="Weekday to scrape (e.g., monday)", choices=WEEKDAYS)
    parser.add_argument("--all", action="store_true", help="Scrape all weekdays (mon–fri)")
    parser.add_argument("--refresh", action="store_true", help="Force re-scraping even if data exists")

    args = parser.parse_args()

    if args.all:
        weekly_scraper_cache = {}
        for day in WEEKDAYS:
            scrape_for_day(day, refresh=args.refresh, cache=weekly_scraper_cache)
    else:
        day = args.day or get_today_english()
        scrape_for_day(day, refresh=args.refresh)


if __name__ == "__main__":
    main()
    generate_index_page()
