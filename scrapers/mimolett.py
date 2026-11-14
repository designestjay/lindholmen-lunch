# scrapers/mimolett.py

from bs4 import BeautifulSoup
from scrapers.base import LunchScraper, MenuItem, DailyMenu, fetch_html
from typing import Dict, List, Optional

class MimolettScraper(LunchScraper):
    URL = "https://restaurangmimolett.se/lunch/"
    _PRICE = "129 kr"

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self) -> None:
        soup = BeautifulSoup(fetch_html(self.URL), "html.parser")
        containers = soup.select("div.menu-list")

        items: List[MenuItem] = []

        for container in containers:
            category_elem = container.select_one("h2.menu-list__title")
            if not category_elem:
                continue
            category = category_elem.get_text(strip=True)

            for li in container.select("li.menu-list__item"):
                name = li.select_one(".item_title")
                desc = li.select_one(".desc__content")
                price = li.select_one(".menu-list__item-price")
                if name:
                    items.append(MenuItem(
                        name=name.get_text(strip=True),
                        description=desc.get_text(strip=True) if desc else None,
                        category=category,
                        price=price.get_text(strip=True).replace(":-"," kr") if price else self._PRICE
                    ))

        # Mimolett serves same menu Mon–Fri
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            self._menus[day] = DailyMenu(day=day, items=items)

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
