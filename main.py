# file: lindholmen_lunch/main.py

import argparse
import json
import logging
import os
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

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


def _same_stockholm_date(scraped_at: str | None, now: datetime) -> bool:
    """True when a previous scrape happened on the same Stockholm calendar day."""
    if not scraped_at:
        return False
    try:
        previous = datetime.fromisoformat(scraped_at)
    except ValueError:
        return False
    if previous.tzinfo is None:
        previous = previous.replace(tzinfo=STOCKHOLM)
    return previous.astimezone(STOCKHOLM).date() == now.astimezone(STOCKHOLM).date()


def _carried_payload(prev: dict, day: str, previous_meta: dict) -> dict:
    """Copy a same-day menu forward and keep the original fetched_at."""
    items = []
    for item in prev.get("items") or []:
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "name": item.get("name") or "",
                "category": item.get("category") or "",
                "description": item.get("description") or "",
                "price": item.get("price") or "",
            }
        )
    return {
        "day": day.lower(),
        "items": items,
        "stale": True,
        "fetched_at": prev.get("fetched_at") or previous_meta.get("scraped_at"),
    }


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

    all_menus = scraper.get_all_menus() if hasattr(scraper, "get_all_menus") else None
    if all_menus:
        menu = all_menus.get(day.lower())
        if not menu or not getattr(menu, "items", None):
            return None
        return _menu_payload(menu)

    menu = scraper.get_menu_for_day(day)
    if not menu or not getattr(menu, "items", None):
        return None
    return _menu_payload(menu)


def _failure_reason(exc: BaseException) -> str:
    """Classify a failed scrape as http_<code>, timeout, or error:<Name>."""
    if isinstance(exc, requests.HTTPError):
        response = getattr(exc, "response", None)
        code = getattr(response, "status_code", None) if response is not None else None
        if isinstance(code, int):
            return f"http_{code}"
        return "error:HTTPError"
    if isinstance(exc, requests.Timeout):
        return "timeout"
    return f"error:{type(exc).__name__}"


def scrape_for_day(
    day: str,
    refresh: bool = False,
    cache: dict | None = None,
    *,
    data_dir: str = "data",
    scrapers=None,
    now: datetime | None = None,
    max_retries: int = 2,
    sleeper=time.sleep,
) -> dict:
    logging.info("Scraping lunch menus for %s", day.capitalize())
    now = now or datetime.now(STOCKHOLM)
    scrapers = scrapers if scrapers is not None else SCRAPERS

    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, f"lunch_data_{day}.json")
    meta_path = os.path.join(data_dir, f"scrape_meta_{day}.json")
    if os.path.exists(filepath) and not refresh:
        logging.info("Skipping scraping for %s (cached file exists).", day)
        return _load_previous(meta_path)

    previous = _load_previous(filepath)
    previous_meta = _load_previous(meta_path)
    same_day = _same_stockholm_date(previous_meta.get("scraped_at"), now)
    results = {}
    ok, stale_kept, failed = [], [], []
    missing_reason = {}

    for scraper_cls in scrapers:
        name = scraper_cls.__name__
        attempts = 0
        got = None
        last_reason = None

        while attempts <= max_retries:
            try:
                got = _scrape_one(scraper_cls, day, cache)
                last_reason = None
                break
            except Exception as e:
                last_reason = _failure_reason(e)
                attempts += 1
                logging.error("[%s] Error on attempt %s for %s: %s", name, attempts, day, e)
                traceback.print_exc()
                if attempts > max_retries:
                    logging.warning("[%s] Gave up after %s retries.", name, max_retries)
                else:
                    delay = 2 + attempts
                    logging.info("[%s] Retrying in %s seconds...", name, delay)
                    sleeper(delay)

        if got and got.get("items"):
            got["stale"] = False
            got["fetched_at"] = now.isoformat(timespec="minutes")
            results[name] = got
            ok.append(name)
            continue

        prev = previous.get(name)
        if same_day and isinstance(prev, dict) and prev.get("items"):
            results[name] = _carried_payload(prev, day, previous_meta)
            stale_kept.append(name)
            logging.warning("[%s] No fresh menu; keeping same-day data as stale.", name)
        else:
            failed.append(name)
            missing_reason[name] = last_reason or "empty"
            logging.warning("[%s] No menu for %s. Not carrying older data.", name, day)

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
        "scraped_at": now.isoformat(timespec="minutes"),
        "fresh": ok,
        "stale": stale_kept,
        "missing": failed,
        "missing_reason": missing_reason,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    logging.info("Wrote lunch data to %s", filepath)
    return meta


def main() -> str | None:
    parser = argparse.ArgumentParser(description="Run Lindholmen lunch scrapers.")
    parser.add_argument("--day", type=str, help="Weekday to scrape (e.g., monday)", choices=WEEKDAYS)
    parser.add_argument("--all", action="store_true", help="Scrape all weekdays (mon–fri)")
    parser.add_argument("--refresh", action="store_true", help="Force re-scraping even if data exists")

    args = parser.parse_args()

    if args.all:
        weekly_scraper_cache = {}
        for day in WEEKDAYS:
            scrape_for_day(day, refresh=args.refresh, cache=weekly_scraper_cache)
        today = get_today_english().lower()
        return today if today in WEEKDAYS else "friday"

    day = (args.day or get_today_english()).lower()
    if day not in WEEKDAYS:
        logging.info("No weekday scrape for %s.", day)
        return None
    scrape_for_day(day, refresh=args.refresh)
    return day


if __name__ == "__main__":
    chosen = main()
    generate_index_page(day=chosen)
