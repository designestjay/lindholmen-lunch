# file: scrapers/restaurant_pier_11.py

import logging
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from scrapers.base import LunchScraper, MenuItem, DailyMenu

logger = logging.getLogger(__name__)

class RestaurantPier11Scraper(LunchScraper):
    URL = "https://ericssonbynordrest.se/restaurang/restaurant-pier-11/#lunch-menu"
    _PRICE = "110 kr"

    WEEKDAY_MAP = {
        "monday": "monday",
        "tuesday": "tuesday",
        "wednesday": "wednesday",
        "thursday": "thursday",
        "friday": "friday"
    }

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self) -> None:
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
        except Exception as e:
            logger.error("Failed to fetch Pier 11 page: %s", e)
            return

        soup = BeautifulSoup(response.content, "html.parser")
        weekday_items = soup.select("div.weekday-item")

        for weekday_div in weekday_items:
            swe_wrapper = weekday_div.select_one(".sprak-wrapper-swe")
            if not swe_wrapper:
                continue

            day_heading = swe_wrapper.find("h3")
            if not day_heading:
                continue

            day = self.WEEKDAY_MAP.get(day_heading.get_text(strip=True).lower())
            if not day:
                continue

            items = []
            for ratter_div in swe_wrapper.select(".ratter"):
                full_text = ratter_div.get_text(strip=True)
                if not full_text:
                    continue

                parts = full_text.split(",", 1)
                name = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""

                items.append(MenuItem(name=name, description=description, category="Dagens", price=self._PRICE))

            if items:
                self._menus[day] = DailyMenu(day=day, items=items)

        logger.info("Parsed Pier 11 menu for days: %s", list(self._menus.keys()))

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
