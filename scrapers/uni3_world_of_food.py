# file: lindholmen_lunch/scrapers/uni3_world_of_food.py

import logging
import re
from datetime import datetime
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from scrapers.base import LunchScraper, MenuItem, DailyMenu

logger = logging.getLogger(__name__)

class Uni3WorldOfFoodScraper(LunchScraper):
    RSS_URL = "https://www.compass-group.se/menuapi/feed/rss/current-week?costNumber=448305&language=sv"

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self) -> None:
        try:
            response = requests.get(self.RSS_URL)
            response.raise_for_status()
        except Exception as e:
            logger.error("Failed to fetch RSS feed: %s", e)
            return

        soup = BeautifulSoup(response.content, "xml")
        weekday_map = {
            "måndag": "monday",
            "tisdag": "tuesday",
            "onsdag": "wednesday",
            "torsdag": "thursday",
            "fredag": "friday"
        }

        for item in soup.find_all("item"):
            title = item.find("title").get_text()
            match = re.match(r"(\w+), \d{2}-\d{2}-\d{4}", title.lower())
            if not match:
                continue

            swedish_day = match.group(1)
            day = weekday_map.get(swedish_day)
            if not day:
                continue

            desc_html = item.find("description").get_text()
            desc_soup = BeautifulSoup(desc_html, "html.parser")
            items = []

            for p in desc_soup.find_all("p"):
                strong = p.find("strong")
                if strong:
                    category = strong.get_text(strip=True).rstrip(":")
                    # Remove the <strong> and <em> parts to get just the Swedish description
                    strong.extract()
                    em = p.find("em")
                    if em:
                        em.extract()
                    name = p.get_text(strip=True, separator=" ")
                    items.append(MenuItem(name=name, category=category))

            if items:
                self._menus[day] = DailyMenu(day=day, items=items)

        logger.info("Parsed Uni3 menu for days: %s", list(self._menus.keys()))

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
