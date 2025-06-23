# file: lindholmen_lunch/scrapers/encounter_asian.py

import logging
from typing import Dict, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import traceback
from scrapers.base import LunchScraper, DailyMenu, MenuItem, get_chrome_options

logger = logging.getLogger(__name__)

class EncounterAsianScraper(LunchScraper):
    URL = "https://tamed.se/take-away-meny/encounter-sushi"

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}

        # Check if selenium is available
        chrome_options = get_chrome_options(enable_javascript=True, load_images=False)
        if chrome_options is None:
            # Selenium not available, skip this scraper
            logger.warning(f"Selenium not available, skipping {self.__class__.__name__}")
            return

        try:
            with webdriver.Chrome(options=chrome_options) as driver:
                driver.set_page_load_timeout(15)
                driver.get(self.URL)

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul[class*='MuiList-root']"))
                )

                html = driver.page_source
                logger.debug("Fetched rendered HTML (first 500 chars):\n%s", html[:500])
                self.soup = BeautifulSoup(html, "html.parser")

        except WebDriverException as e:
            logger.error("WebDriver error: %s", str(e))
            traceback.print_exc()
            return

        except Exception as e:
            logger.error("Error while loading or parsing Encounter Asian menu:")
            traceback.print_exc()
            return

        self.fetch()

    def fetch(self) -> None:
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        items = []

        menu_list = self.soup.select_one("ul[class*='MuiList-root']")
        if not menu_list:
            logger.warning("Menu list container not found.")
            return

        containers = menu_list.select("div[class*='MuiGrid-container']")

        for container in containers:
            children = container.select("div[class*='MuiGrid-item']")
            if len(children) < 2:
                continue

            text_block = children[0]
            price_block = children[1]

            title_elem = text_block.select_one("span[class*='MuiListItemText-primary']")
            desc_elem = text_block.select_one("p[class*='MuiListItemText-secondary']")
            price_elem = price_block.select_one("p")

            if not title_elem:
                continue

            full_name = title_elem.get_text(strip=True)
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            price = price_elem.get_text(strip=True) if price_elem else ""

            # Extract category from prefix (e.g., SUSHI - Mix 12 bitar → SUSHI)
            if " - " in full_name:
                category, name = full_name.split(" - ", 1)
            elif " " in full_name:
                category, name = full_name.split(" ", 1)
            else:
                category = full_name
                name = full_name

            item = MenuItem(
                name=name.strip(),
                category=category.strip(),
                description=description.strip(),
                price=price.strip()
            )
            logger.debug("Parsed item: %s", item)
            items.append(item)

        if not items:
            logger.warning("No menu items parsed.")
            return

        for day in weekdays:
            self._menus[day] = DailyMenu(day=day, items=list(items))

        logger.debug("Parsed %d items for Encounter Asian Cuisine.", len(items))
        logger.debug("DailyMenu contents: %s", self._menus)

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        logger.debug("Looking up menu for: %s", day.lower())
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus

