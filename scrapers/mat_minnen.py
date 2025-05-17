# file: lindholmen_lunch/scrapers/mat_minnen.py

import re
from typing import Dict, Optional
import requests
import logging
from bs4 import BeautifulSoup
from scrapers.base import LunchScraper, DailyMenu, MenuItem

logger = logging.getLogger(__name__)

class MatMinnenScraper(LunchScraper):
    URL = "https://matminnen.se/lunchmeny"

    def __init__(self):
        response = requests.get(self.URL)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.text, "html.parser")
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self) -> None:
        weekdays = ["måndag", "tisdag", "onsdag", "torsdag", "fredag"]
        body = self.soup.select_one(".contentgroup__body")
        if not body:
            return
        logging.debug("Print body: %s", body)

        paragraphs = body.find_all("p")
        current_day = None
        items_by_day: Dict[str, list] = {day: [] for day in weekdays}
        weekly_items = []

        for p in paragraphs:
            text = p.get_text(strip=True)
            logging.debug("Text: %s", text)
            if not text:
                continue

            lowered = text.lower()

            if any(lowered == day for day in weekdays):
                current_day = lowered
                continue

            if "veckans sallad" in lowered:
                current_day = "veckans sallad"
                continue

            # Match item with description split by – or -
            parts = re.split(r"\s*[-–]\s*", text, maxsplit=1)
            name = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""

            item = MenuItem(name=name, description=description)
            logging.debug("Item: %s", item)

            if current_day in weekdays:
                items_by_day[current_day].append(item)
            elif current_day == "veckans sallad":
                item.category = "Veckans sallad"
                weekly_items.append(item)

        logging.debug("Items by day: %s", items_by_day)
        # Save daily menus
        for day, items in items_by_day.items():
            if items:
                self._menus[day] = DailyMenu(day=day, items=items)

        # Add weekly items to all days
        if weekly_items:
            for menu in self._menus.values():
                menu.items.extend(weekly_items)

        logging.debug("Final menus: %s", self._menus)

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        day = day.lower()
        day_map = {
            "monday": "måndag",
            "tuesday": "tisdag",
            "wednesday": "onsdag",
            "thursday": "torsdag",
            "friday": "fredag",
        }
        swedish_day = day_map.get(day, day)
        return self._menus.get(swedish_day)


    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
