from bs4 import BeautifulSoup
from scrapers.base import LunchScraper, MenuItem, DailyMenu
from typing import Dict, Optional
import requests
from datetime import date

class BennePastabarScraper(LunchScraper):
    URL = "https://bennepastabar.se/#menu"

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self) -> None:
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch Benne Pastabar page: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        categorized_items = {
            "Benne Pasta": [],
            "The Visitor": [],
            "Benne Bites": []
        }

        # Benne Pasta and Visitor (both in <article>)
        for article in soup.find_all("article"):
            name_tag = article.find("h4")
            desc_tag = article.find("p")
            if name_tag and desc_tag:
                name = name_tag.get_text(strip=True)
                desc = desc_tag.get_text(strip=True)
                full = f"{name} - {desc}"

                if article.find(class_="thevisitor-lable"):
                    categorized_items["The Visitor"].append(MenuItem(name=full, category="The Visitor"))
                else:
                    categorized_items["Benne Pasta"].append(MenuItem(name=full, category="Benne Pasta"))

        # Benne Bites
        for figure in soup.select("div.bites-wrapper .figure"):
            name_tag = figure.find("h4")
            desc_tag = figure.find("p")
            if name_tag and desc_tag:
                name = name_tag.get_text(strip=True)
                desc = desc_tag.get_text(strip=True)
                categorized_items["Benne Bites"].append(MenuItem(name=f"{name} - {desc}", category="Benne Bites"))

        # Apply menu to all weekdays
        all_items = []
        for items in categorized_items.values():
            all_items.extend(items)

        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            self._menus[day] = DailyMenu(day=day, items=all_items.copy())


    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
