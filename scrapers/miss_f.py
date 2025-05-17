from bs4 import BeautifulSoup
from scrapers.base import LunchScraper, MenuItem, DailyMenu
from typing import Dict, Optional
from datetime import date
import requests
import os

class MissFScraper(LunchScraper):
    URL = "https://www.missf.se/"
    LOCAL_FILE = "sample_miss_f.htm"

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self):
        if os.path.exists(self.LOCAL_FILE):
            with open(self.LOCAL_FILE, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
        else:
            response = requests.get(self.URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

        menu_items = []

        for heading_div in soup.find_all("div", class_="seasidetms_heading_wrap"):
            h3 = heading_div.find("h3", class_="seasidetms_heading")
            if not h3:
                continue
            category = h3.get_text(strip=True)

            # Look for the next sibling menu section
            menu_block = heading_div.find_next_sibling("div", class_="seasidetms_menu")
            if not menu_block:
                continue

            for item_div in menu_block.find_all("div", class_="seasidetms_menu_item"):
                title_tag = item_div.find("h5", class_="menu_title")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)

                # Optional description in <ul><li>
                desc_tag = item_div.find("ul", class_="menu_feature_list")
                description = ""
                if desc_tag and desc_tag.find("li"):
                    desc_text = desc_tag.find("li").get_text(strip=True)
                    if desc_text:
                        title += f" – {desc_text}"

                menu_items.append(MenuItem(name=title, category=category))

        # Apply the same menu to all weekdays
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            self._menus[day] = DailyMenu(day=day, items=list(menu_items))  # copy list

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
