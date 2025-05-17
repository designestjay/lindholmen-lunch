# lindholmen_lunch/scrapers/cuckoos_nest.py

from bs4 import BeautifulSoup
import requests
import logging
from scrapers.base import LunchScraper, DailyMenu, MenuItem
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CuckoosNestScraper(LunchScraper):
    URL = "https://www.cuckoosnest.se/menyer/lunch"

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self):
        response = requests.get(self.URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        left_column = soup.select_one("div.content-region")
        if not left_column:
            logger.warning("Could not find left column with Swedish menu")
            return

        items = []
        current_category = None

        for tag in left_column.find_all(["h3", "h4", "p"]):
            text = tag.get_text(strip=True)
            if not text:
                continue

            tag_text = text.upper()
            if "FISK" in tag_text:
                current_category = "FISK"
            elif "KÖTT" in tag_text:
                current_category = "KÖTT"
            elif "VEG" in tag_text:
                current_category = "VEG"
            elif "CAESARSALLAD" in tag_text:
                current_category = "CEASARSALLAD"
            elif "RÄKMACKA" in tag_text:
                current_category = "RÄKMACKA"
            elif "DOUBLE SMASHED CHEESEBURGER" in tag_text:
                current_category = "DOUBLE SMASHED CHEESEBURGER"
            elif tag.name == "p":
                items.append(MenuItem(name=text, category=current_category))

        if items:
            # The menu is weekly and valid Mon–Fri
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                self._menus[day] = DailyMenu(day=day, items=items.copy())

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
