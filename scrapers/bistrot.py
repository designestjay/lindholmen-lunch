# scrapers/bistrot.py
import unicodedata
from bs4 import BeautifulSoup
from scrapers.base import LunchScraper, MenuItem, DailyMenu
from typing import Dict, List, Optional
import requests

class BistrotScraper(LunchScraper):
    URL = "https://bistrot.se/"

    SWEDISH_TO_ENGLISH = {
        "Måndag": "monday",
        "Tisdag": "tuesday",
        "Onsdag": "wednesday",
        "Torsdag": "thursday",
        "Fredag": "friday",
    }

    def __init__(self):
        self._menus: Dict[str, DailyMenu] = {}
        self.fetch()

    def fetch(self) -> None:
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch Bistrot page: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        menu = soup.select_one("div.fdm-the-menu")
        if not menu:
            print("No menu found on Bistrot page.")
            return

        daily_items: Dict[str, List[MenuItem]] = {day: [] for day in self.SWEDISH_TO_ENGLISH.values()}
        shared_items_by_day: Dict[str, List[MenuItem]] = {day: [] for day in self.SWEDISH_TO_ENGLISH.values()}

        section = menu.select_one("ul.fdm-menu")
        current_category = None

        for item in section.select("li.fdm-item"):
            title = item.select_one("p.fdm-item-title")
            content = item.select_one("div.fdm-item-content")
            if not title or not content:
                continue

            header = title.get_text(strip=True)
            lines = [p.get_text(strip=True) for p in content.find_all("p") if p.get_text(strip=True)]
            groups = self._group_lines(lines)

            # Determine category context from header (e.g., "Meny vecka 21", "Vegetarisk Måndag–Tis", etc.)
            normalized = normalize_day_name(header)
            swe_to_eng = {normalize_day_name(k): v for k, v in self.SWEDISH_TO_ENGLISH.items()}

            if "vecka" in header.lower():
                current_category = "Veckans"
                self._add_to_all_days(shared_items_by_day, groups, category=current_category)
            elif "vegetarisk" in header.lower():
                current_category = header
                self._add_to_matching_days(shared_items_by_day, groups, header, category=current_category)
            elif normalized in swe_to_eng:
                eng_day = swe_to_eng[normalized]
                for name, desc in groups:
                    daily_items[eng_day].append(MenuItem(name=name, description=desc, category="Lunch"))
            elif normalize_day_name(header) == "caesarsallad":
                self._add_to_all_days(shared_items_by_day, groups, category="Caesarsallad")



        for day in daily_items:
            full_list = shared_items_by_day[day] + daily_items[day]
            if full_list:
                self._menus[day] = DailyMenu(day=day, items=full_list)

    def _group_lines(self, lines: List[str]) -> List[tuple[str, Optional[str]]]:
        """Group bold (dish name) and plain (description) lines."""
        pairs = []
        i = 0
        while i < len(lines):
            name = lines[i]
            desc = None

            # Look ahead: If next line exists and isn't another title
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Treat lines like "Caesarsallad" as new dish, not description
                if not self._is_new_dish(next_line):
                    desc = next_line
                    i += 1  # consume description

            pairs.append((name, desc))
            i += 1
        return pairs

    def _is_new_dish(self, line: str) -> bool:
        keywords = ["vecka", "vegetarisk", "måndag", "tisdag", "onsdag", "torsdag", "fredag", "caesarsallad"]
        norm = normalize_day_name(line)
        return any(kw in norm for kw in keywords)


    def _add_to_all_days(self, target: Dict[str, List[MenuItem]], groups: List[tuple[str, Optional[str]]], category: Optional[str]):
        for day in target:
            for name, desc in groups:
                target[day].append(MenuItem(name=name, description=desc, category=category))

    def _add_to_matching_days(self, target: Dict[str, List[MenuItem]], groups: List[tuple[str, Optional[str]]], header: str, category: Optional[str]):
        matched_days = []
        for swe_day, eng_day in self.SWEDISH_TO_ENGLISH.items():
            if swe_day.lower() in header.lower():
                matched_days.append(eng_day)

        for day in matched_days:
            for name, desc in groups:
                target[day].append(MenuItem(name=name, description=desc, category=category))

    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus

def normalize_day_name(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()