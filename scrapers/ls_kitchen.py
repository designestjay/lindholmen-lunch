# scrapers/ls_kitchen.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from scrapers.base import LunchScraper, MenuItem, DailyMenu
from typing import Dict, Optional
import time

class LsKitchenScraper(LunchScraper):
    URL = "https://plateimpact-screen.azurewebsites.net/menu/week/ls-kitchen/c74da2cf-aa1a-4d3a-9ba6-08d5569587a1"

    SWEDISH_TO_ENGLISH = {
        "Måndag": "monday",
        "Tisdag": "tuesday",
        "Onsdag": "wednesday",
        "Torsdag": "thursday",
        "Fredag": "friday"
    }

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self) -> None:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        with webdriver.Chrome(options=options) as driver:
            driver.get(self.URL)
            time.sleep(5)  # Allow time for JS to load content

            soup = BeautifulSoup(driver.page_source, "html.parser")

        for day_div in soup.select("div.day"):
            heading = day_div.find("h2")
            if not heading:
                continue

            swe_day = heading.get_text(strip=True)
            eng_day = self.SWEDISH_TO_ENGLISH.get(swe_day)
            if not eng_day:
                continue

            items = []
            for dish in day_div.select("crbn-week-menu-ls-kitchen-dish"):
                h3 = dish.find("h3")
                if h3:
                    name = h3.get_text(strip=True)
                    if name:
                        items.append(MenuItem(name=name))

            if items:
                self._menus[eng_day] = DailyMenu(day=eng_day, items=items)

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
