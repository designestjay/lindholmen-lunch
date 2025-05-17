from bs4 import BeautifulSoup
import requests
import re
import logging
from datetime import date
from scrapers.base import LunchScraper, MenuItem, DailyMenu
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class DistrictOneScraper(LunchScraper):
    URL = "https://www.districtone.se/lunch.html"

    def __init__(self):
        self._menus = {}
        self.fetch()

    def fetch(self):
        response = requests.get(self.URL)
        soup = BeautifulSoup(response.content, "html.parser")

        weekday_map = {
            "måndag": "monday",
            "tisdag": "tuesday",
            "onsdag": "wednesday",
            "torsdag": "thursday",
            "fredag": "friday",
        }

        current_day = None
        current_category = None
        day_text_blocks: Dict[str, list[MenuItem]] = {v: [] for v in weekday_map.values()}

        def normalize(text: str) -> str:
            return text.strip().lower()

        # Find the large lunch block
        lunch_block = soup.find("div", class_="styles_contentContainer__lrPIa")
        if not lunch_block:
            logger.debug("Could not find lunch content container.")
            return

        # Extract all <p> elements
        paragraphs = lunch_block.find_all("p")
        for p in paragraphs:
            text = p.get_text(separator=" ", strip=True)
            normalized = normalize(text)

            # End of relevant content
            if "kontakta oss" in normalized or "öppettider" in normalized:
                break

            # Detect weekday
            if normalized in weekday_map:
                current_day = weekday_map[normalized]
                current_category = None
                continue

            # Ignore if we don't have a current_day
            if not current_day:
                continue

            # Detect new category
            if p.find("span", style=re.compile("underline")):
                current_category = text.strip()
                continue

            # Add menu item
            if text and not text.startswith("..."):
                item = MenuItem(name=text.strip(), category=current_category)
                day_text_blocks[current_day].append(item)

        for day, items in day_text_blocks.items():
            if items:
                self._menus[day] = DailyMenu(day=day, items=items)

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
