from bs4 import BeautifulSoup
import requests
from typing import Dict, Optional
from scrapers.base import LunchScraper, DailyMenu, MenuItem

class OishiiScraper(LunchScraper):
    URL = "https://oishii.se/lunchmeny/"

    def __init__(self):
        response = requests.get(self.URL)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.text, "html.parser")
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self) -> None:
        categories = self.soup.find_all("h1")
        items = []

        for category_tag in categories:
            category = category_tag.get_text(strip=True)
            menu_block = category_tag.find_next("div", class_="pricelist_container")
            if not menu_block:
                continue

            for row in menu_block.find_all("div", class_="menurow"):
                name_tag = row.find("span", class_="endsofdots")
                description_tag = row.find("div", class_="description")
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    description = description_tag.get_text(strip=True) if description_tag else None
                    items.append(MenuItem(name=name, description=description, category=category))

        # Oishii's menu appears the same for all weekdays
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            self._menus[day] = DailyMenu(day=day, items=items)

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
