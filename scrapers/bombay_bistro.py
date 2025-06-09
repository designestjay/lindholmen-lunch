from bs4 import BeautifulSoup
from datetime import date
import re
import logging
import requests
import unicodedata

from scrapers.base import LunchScraper, MenuItem, DailyMenu
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BombayBistroScraper(LunchScraper):
    URL = "https://www.bombaybistro.se/lunch/"

    def __init__(self):
        self._menus = {}
        self.fetch()

    def fetch(self):
        response = requests.get(self.URL)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        current_week = date.today().isocalendar().week
        lunch_number = ((current_week) % 4) + 1
        lunch_header_text = f"LUNCH {lunch_number}"
        logger.debug(f"Current week: {current_week}, selecting: {lunch_header_text}")

        # Find all H2s to locate correct lunch cycle
        lunch_headers = soup.find_all("h2", string=re.compile(r"LUNCH \d+", re.IGNORECASE))
        if lunch_number > len(lunch_headers):
            logger.debug("Lunch number out of range.")
            return

        selected_header = lunch_headers[lunch_number - 1]
        logger.debug(f"Using header: {selected_header.get_text(strip=True)}")

        # Step up high enough to include all content blocks under this lunch section
        container = selected_header.find_parent("div", class_="elementor-widget-container")
        if not container:
            logger.debug("Could not find container around lunch header")
            return

        content = []
        for sibling in container.find_parent().find_next_siblings():
            logger.debug(f"Scanning sibling: {sibling.name} - class: {sibling.get('class')}")
            if sibling.find("h2", string=re.compile(r"LUNCH \d+", re.IGNORECASE)):
                break  # Stop when reaching the next lunch section
            content.append(sibling)

        weekday_map = {
            "monday": "MÅNDAG",
            "tuesday": "TISDAG",
            "wednesday": "ONSDAG",
            "thursday": "TORSDAG",
            "friday": "FREDAG"
        }

        current_day = None
        day_text_blocks: Dict[str, list[str]] = {day: [] for day in weekday_map}

        stop_weekday_parsing = False
        for elem in content:
            if stop_weekday_parsing:
                break
            for tag in elem.find_all(["h5", "p"], recursive=True):
                if tag.name == "h5":
                    heading = tag.get_text(strip=True).upper()
                    if heading == "ANDRA ALTERNATIV":
                        logger.debug("Stopping weekday parsing at ANDRA ALTERNATIV")
                        stop_weekday_parsing = True
                        break


                    for eng_day, swe_day in weekday_map.items():
                        if heading == swe_day:
                            logger.debug(f"Matched heading: {heading} → {eng_day}")
                            current_day = eng_day
                            break
                elif tag.name == "p" and current_day:
                    text = tag.get_text(separator="\n", strip=True)
                    logger.debug(f"Adding text to {current_day}: {text}")
                    day_text_blocks[current_day].append(text)



        for day, blocks in day_text_blocks.items():
            if not blocks:
                continue
            lines = "\n".join(blocks).split("\n")
            items = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue

                if is_all_caps(line):
                    description_lines = []
                    i += 1
                    while i < len(lines) and not is_all_caps(lines[i].strip()):
                        description_lines.append(lines[i].strip())
                        i += 1
                    description_line = f"{' '.join(description_lines)}" if description_lines else line
                    clean_name, _ = extract_price(line)
                    items.append(MenuItem(name=clean_name, description=description_line, price="129 kr"))
                else:
                    items.append(MenuItem(name=line, price="129 kr"))
                    i += 1
            self._menus[day] = DailyMenu(day=day, items=items)

        # ALSO include "ANDRA ALTERNATIV" — available every day
        alt_items = []
        alt_heading = soup.find("h5", string=re.compile("ANDRA ALTERNATIV", re.IGNORECASE))
        if alt_heading:
            logger.debug("Found ANDRA ALTERNATIV heading")

            # Get outer wrapper that contains all following menu items
            section_container = alt_heading.find_parent("div", class_="elementor-widget-container")
            if section_container:
                # Look for the next <p> tags within the same parent section
                for p in section_container.find_all_next("p"):
                    # Stop if we reach a new section like "LUNCH 2", "MÅNDAG", etc.
                    if p.find_previous("h5") and re.search(r"\b(LUNCH|MÅNDAG|TISDAG|ONSDAG|TORSDAG|FREDAG|DAGENS VEG)\b", p.text, re.IGNORECASE):
                        break
                    text = p.get_text(separator="\n", strip=True)
                    for line in text.split("\n"):
                        clean = line.strip()
                        if clean:
                            logger.debug(f"Adding ANDRA ALTERNATIV item: {clean}")
                            alt_items.append(MenuItem(name=clean, category="ANDRA ALTERNATIV"))

        # Add them to all existing weekday menus
        for day in weekday_map:
            if not alt_items:
                continue

            alt_lines = [item.name for item in alt_items]
            merged_items = []
            i = 0
            while i < len(alt_lines):
                line = alt_lines[i]
                clean_name, price = extract_price(line)
                if is_all_caps(line):
                    description_lines = []
                    i += 1
                    while i < len(alt_lines) and not is_all_caps(alt_lines[i]):
                        description_lines.append(alt_lines[i])
                        i += 1
                    description_line = f"{' '.join(description_lines)}" if description_lines else None
                    merged_items.append(MenuItem(name=clean_name, description=description_line, price=price, category="ANDRA ALTERNATIV"))
                else:
                    merged_items.append(MenuItem(name=clean_name, price=price, category="ANDRA ALTERNATIV"))
                    i += 1

            if day in self._menus:
                self._menus[day].items.extend(merged_items)
            else:
                self._menus[day] = DailyMenu(day=day, items=merged_items)


    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        return self._menus.get(day.lower())

    def get_all_menus(self) -> Dict[str, DailyMenu]:
        return self._menus


def is_all_caps(line: str) -> bool:
    normalized = unicodedata.normalize("NFKD", line).encode("ASCII", "ignore").decode()
    return normalized.isupper()


def extract_price(text: str) -> tuple[str, Optional[str]]:
    match = re.search(r"\b(\d{2,3})\s*kr\b", text, re.IGNORECASE)
    if match:
        price = f"{match.group(1)} kr"
        # Remove the price part from the original text
        cleaned = re.sub(r"\b(\d{2,3})\s*kr\b", "", text, flags=re.IGNORECASE).strip(" –-")
        return cleaned, price
    return text.strip(), None