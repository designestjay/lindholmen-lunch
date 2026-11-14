from bs4 import BeautifulSoup
import csv
import io
import json
import logging
import re
from typing import Dict, Optional
from urllib.parse import urljoin

import requests

from scrapers.base import DailyMenu, LunchScraper, MenuItem, fetch_html

logger = logging.getLogger(__name__)

# Homepage day tabs. The dishes themselves are filled from the restaurant's
# own lunch.js (a sheet on the same menu the page renders), with menu.json
# on this domain as the fallback.
_DAY_ROWS = (
    ("mon", "monday", "#lunch-mon .menu-list"),
    ("tue", "tuesday", "#lunch-tue .menu-list"),
    ("wed", "wednesday", "#lunch-wed .menu-list"),
    ("thu", "thursday", "#lunch-thu .menu-list"),
    ("fri", "friday", "#lunch-fri .menu-list"),
    ("all", "all", "#lunch-all"),
)


def menu_from_csv(text: str) -> dict:
    """Parse the CSV shape lunch.js reads into {days: {mon: [{cat, desc}]}}."""
    days = {key: [] for key, _eng, _sel in _DAY_ROWS}
    week = ""
    day_names = {
        "måndag": "mon",
        "tisdag": "tue",
        "onsdag": "wed",
        "torsdag": "thu",
        "fredag": "fri",
        "hela veckan": "all",
    }
    for row in csv.reader(io.StringIO(text)):
        cells = [cell.strip() for cell in row]
        if not any(cells):
            continue
        head = cells[0]
        week_match = re.match(r"vecka\s*(\d+)", head, re.I)
        if week_match:
            week = week_match.group(1)
            continue
        key = day_names.get(head.lower())
        if not key:
            continue
        category = cells[1] if len(cells) > 1 else ""
        description = cells[2] if len(cells) > 2 else ""
        if not description:
            continue
        days[key].append({"cat": category, "desc": description})
    return {"week": week, "days": days}


def menu_from_json(payload: dict) -> dict:
    days = {key: [] for key, _eng, _sel in _DAY_ROWS}
    source = (payload or {}).get("days") or {}
    for key, _eng, _sel in _DAY_ROWS:
        for dish in source.get(key) or []:
            cat = ((dish.get("cat") or {}).get("sv") or "").strip()
            desc = ((dish.get("desc") or {}).get("sv") or "").strip()
            if desc:
                days[key].append({"cat": cat, "desc": desc})
    return {"week": str((payload or {}).get("week") or ""), "days": days}


def fill_lunch_lists(soup: BeautifulSoup, menu: dict) -> None:
    """Write Swedish dishes into the homepage day lists, matching lunch.js."""
    for key, _eng, selector in _DAY_ROWS:
        host = soup.select_one(selector)
        if host is None:
            continue
        host.clear()
        for dish in (menu.get("days") or {}).get(key) or []:
            item = soup.new_tag("li")
            desc = soup.new_tag("span")
            desc.string = dish["desc"]
            category = soup.new_tag("span")
            category["class"] = "price"
            category.string = dish["cat"]
            item.append(desc)
            item.append(category)
            host.append(item)
    label = soup.select_one("#lunch .section-label")
    week = (menu or {}).get("week") or ""
    if label is not None and week:
        label.string = f"Lunchmeny – Vecka {week}"


class DistrictOneScraper(LunchScraper):
    URL = "https://www.districtone.se/"
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
        page = fetch_html(self.URL)
        soup = BeautifulSoup(page, "html.parser")
        if not self._lists_have_dishes(soup):
            menu = self._load_menu()
            if menu:
                fill_lunch_lists(soup, menu)
                page = str(soup)
        self.parse(page)

    def _load_menu(self) -> Optional[dict]:
        try:
            script = fetch_html(urljoin(self.URL, "lunch.js"))
        except requests.RequestException as exc:
            logger.warning("District One lunch.js failed: %s", exc)
            script = ""
        match = re.search(r'SHEET_URL\s*=\s*"([^"]+)"', script or "")
        if match:
            try:
                return menu_from_csv(fetch_html(match.group(1)))
            except requests.RequestException as exc:
                logger.warning("District One menu sheet failed: %s", exc)
        try:
            payload = json.loads(fetch_html(urljoin(self.URL, "menu.json")))
        except (requests.RequestException, json.JSONDecodeError) as exc:
            logger.warning("District One menu.json failed: %s", exc)
            return None
        return menu_from_json(payload)

    @staticmethod
    def _lists_have_dishes(soup: BeautifulSoup) -> bool:
        return bool(soup.select("#lunch-mon li span"))

    def parse(self, html: str) -> None:
        soup = BeautifulSoup(html, "html.parser")
        price = self._price(soup)
        all_week = self._items(soup.select_one("#lunch-all"), price)
        self._menus = {}
        for key, eng, selector in _DAY_ROWS:
            if key == "all":
                continue
            items = self._items(soup.select_one(selector), price) + list(all_week)
            if items:
                self._menus[eng] = DailyMenu(day=eng, items=items)

    @staticmethod
    def _items(node, price: str) -> list:
        if node is None:
            return []
        items = []
        for li in node.select("li"):
            classes = li.get("class") or []
            if "menu-loading" in classes:
                continue
            spans = li.find_all("span", recursive=False)
            if len(spans) >= 2:
                description = spans[0].get_text(" ", strip=True)
                category = spans[1].get_text(" ", strip=True)
            else:
                description = li.get_text(" ", strip=True)
                category = ""
            if not description:
                continue
            items.append(MenuItem(name=description, category=category or None, price=price or None))
        return items

    @staticmethod
    def _price(soup: BeautifulSoup) -> str:
        lunch = soup.select_one("#lunch")
        text = lunch.get_text(" ", strip=True) if lunch else ""
        match = re.search(r"(\d+)\s*kr", text, re.I)
        if not match:
            return ""
        return f"{match.group(1)} kr"

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus
