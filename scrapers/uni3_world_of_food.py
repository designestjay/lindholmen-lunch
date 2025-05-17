# scrapers/uni3_world_of_food.py

import requests
from datetime import date
from scrapers.base import LunchScraper, MenuItem, DailyMenu
from typing import Dict, Optional

class Uni3WorldOfFoodScraper(LunchScraper):
    API_URL = "https://www.compass-group.se/menuapi/feed/json?costNumber=448305&language=sv"

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self):
        response = requests.get(self.API_URL)
        response.raise_for_status()
        data = response.json()

        for day_entry in data.get("MenusForDays", []):
            date_str = day_entry.get("Date", "")
            day = date.fromisoformat(date_str.split("T")[0]).strftime("%A").lower()
            set_menus = day_entry.get("SetMenus", [])

            items = []
            for menu in set_menus:
                name = menu.get("Name")
                if not name:
                    continue
                components = menu.get("Components", [])
                description = ", ".join(components)
                full_text = f"{name} - {description}" if description else name
                items.append(MenuItem(name=full_text))

            if items:
                self._menus[day] = DailyMenu(day=day, items=items)

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
