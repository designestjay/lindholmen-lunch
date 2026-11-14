# file: lindholmen_lunch/scrapers/uni3_world_of_food.py

import logging
import re
from typing import Dict, Optional
from bs4 import BeautifulSoup, Tag
from scrapers.base import LunchScraper, MenuItem, DailyMenu, fetch_html

logger = logging.getLogger(__name__)

_DASH = re.compile(r"\s+[–-]\s+")


class Uni3WorldOfFoodScraper(LunchScraper):
    RSS_URL = "https://www.compass-group.se/menuapi/feed/rss/current-week?costNumber=448305&language=sv"
    _PRICE = "132 kr"

    def __init__(self, rss: str | None = None):
        self._menus: Dict[str, DailyMenu] = {}
        if rss is not None:
            self.parse(rss)
        else:
            self.fetch()

    def fetch(self) -> None:
        self.parse(fetch_html(self.RSS_URL))

    def parse(self, rss_xml: str) -> None:
        soup = BeautifulSoup(rss_xml, "xml")
        weekday_map = {
            "måndag": "monday",
            "tisdag": "tuesday",
            "onsdag": "wednesday",
            "torsdag": "thursday",
            "fredag": "friday",
        }

        for item in soup.find_all("item"):
            title = item.find("title")
            if title is None:
                continue
            match = re.match(r"(\w+), \d{2}-\d{2}-\d{4}", title.get_text().lower())
            if not match:
                continue

            day = weekday_map.get(match.group(1))
            if not day:
                continue

            description = item.find("description")
            if description is None:
                continue
            items = self._dishes(description.get_text())
            if items:
                self._menus[day] = DailyMenu(day=day, items=items)

        logger.info("Parsed Uni3 menu for days: %s", list(self._menus.keys()))

    def _dishes(self, desc_html: str) -> list[MenuItem]:
        """One MenuItem per station. Friday puts every station in a single <p>."""
        desc_soup = BeautifulSoup(desc_html, "html.parser")
        items = []
        for strong in desc_soup.find_all("strong"):
            if not isinstance(strong, Tag):
                continue
            category = strong.get_text(strip=True).rstrip(":").strip()
            swedish = _swedish_after(strong)
            if not category or not swedish:
                continue
            parts = [part.strip() for part in _DASH.split(swedish) if part.strip()]
            if not parts:
                continue
            name = parts[0]
            description = ", ".join(parts[1:]) if len(parts) > 1 else None
            items.append(MenuItem(name=name, description=description, category=category, price=self._PRICE))
        return items

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus


def _swedish_after(strong: Tag) -> str:
    """Swedish text up to the next station. The <em> line is the English translation."""
    chunks = []
    for node in strong.next_siblings:
        name = getattr(node, "name", None)
        if name == "strong":
            break
        if name in {"em", "br"}:
            continue
        if isinstance(node, Tag):
            for em in node.find_all("em"):
                em.extract()
            text = node.get_text(" ", strip=True)
        else:
            text = str(node)
        text = text.replace("\xa0", " ").strip()
        if text:
            chunks.append(text)
    return re.sub(r"\s+", " ", " ".join(chunks)).strip()
