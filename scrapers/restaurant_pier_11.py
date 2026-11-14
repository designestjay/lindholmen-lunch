# file: scrapers/restaurant_pier_11.py

import logging
import re
from typing import Dict, Optional

from bs4 import BeautifulSoup

from scrapers.base import DailyMenu, LunchScraper, MenuItem, fetch_html

logger = logging.getLogger(__name__)


class RestaurantPier11Scraper(LunchScraper):
    URL = "https://ericssonbynordrest.se/restaurang/restaurant-pier-11/"

    # Day headings are <span data-en="Monday" data-sv="Måndag">.
    WEEKDAY_FROM_EN = {
        "monday": "monday",
        "tuesday": "tuesday",
        "wednesday": "wednesday",
        "thursday": "thursday",
        "friday": "friday",
    }
    WEEKDAY_FROM_SV = {
        "måndag": "monday",
        "tisdag": "tuesday",
        "onsdag": "wednesday",
        "torsdag": "thursday",
        "fredag": "friday",
    }

    def __init__(self, html: str | None = None):
        self._menus: Dict[str, DailyMenu] = {}
        if html is not None:
            self.parse(html)
        else:
            self.fetch()

    def fetch(self) -> None:
        self.parse(fetch_html(self.URL))

    def parse(self, html: str) -> None:
        soup = BeautifulSoup(html, "html.parser")
        price = self._price(soup)
        panel = soup.select_one(".castit-weekpanel.is-active") or soup.select_one(".castit-weekpanel")
        self._menus = {}
        if not panel:
            logger.info("Pier 11: no week panel in the page")
            return

        for day in panel.select("section.castit-day"):
            heading = day.select_one(".castit-day__title [data-en], .castit-day__title [data-sv]")
            eng = self._day_key(heading)
            if not eng:
                continue
            items = []
            for dish in day.select(".castit-dish"):
                name = self._swedish(dish.select_one(".castit-dish__title"))
                if not name:
                    continue
                description = self._swedish(dish.select_one(".castit-dish__desc"))
                items.append(MenuItem(name=name, description=description, category="Dagens", price=price))
            if items:
                self._menus[eng] = DailyMenu(day=eng, items=items)

        logger.info("Parsed Pier 11 menu for days: %s", list(self._menus.keys()))

    def _day_key(self, heading) -> Optional[str]:
        if heading is None:
            return None
        english = (heading.get("data-en") or "").strip().lower()
        swedish = (heading.get("data-sv") or heading.get_text(" ", strip=True) or "").strip().lower()
        return self.WEEKDAY_FROM_EN.get(english) or self.WEEKDAY_FROM_SV.get(swedish)

    @staticmethod
    def _swedish(node) -> str:
        if node is None:
            return ""
        carrier = node.select_one("[data-sv]") or node
        text = carrier.get("data-sv") or carrier.get_text(" ", strip=True)
        return " ".join(str(text).split())

    @staticmethod
    def _price(soup) -> str:
        meta = soup.select_one(".castit-lunch-meta")
        text = meta.get_text(" ", strip=True) if meta else ""
        match = re.search(r"(\d+)\s*(?:SEK|kr)", text, re.I)
        if not match:
            return ""
        return f"{match.group(1)} kr"

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
