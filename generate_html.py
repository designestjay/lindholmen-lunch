# file: lindholmen_lunch/generate_html.py

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

from utils.annotate_food_types import annotate_file, annotate_menu_data, load_keywords
from utils.restaurants import display_name, link_key
from utils.utils import get_today_english

STOCKHOLM = ZoneInfo("Europe/Stockholm")

DAY_LABELS = {
    "monday": ("Monday", "Måndag"),
    "tuesday": ("Tuesday", "Tisdag"),
    "wednesday": ("Wednesday", "Onsdag"),
    "thursday": ("Thursday", "Torsdag"),
    "friday": ("Friday", "Fredag"),
    "saturday": ("Saturday", "Lördag"),
    "sunday": ("Sunday", "Söndag"),
}

# Compact filter set — only chips that appear in today's data are rendered.
FILTER_CATALOG = [
    {"key": "vegan", "emoji": "🌱", "label_en": "Veggie", "label_sv": "Vego"},
    {"key": "fish", "emoji": "🐟", "label_en": "Fish", "label_sv": "Fisk"},
    {"key": "chicken", "emoji": "🐔", "label_en": "Chicken", "label_sv": "Kyckling"},
    {"key": "pasta", "emoji": "🍝", "label_en": "Pasta", "label_sv": "Pasta"},
    {"key": "salad", "emoji": "🥗", "label_en": "Salad", "label_sv": "Sallad"},
    {"key": "sushi", "emoji": "🍣", "label_en": "Sushi", "label_sv": "Sushi"},
    {"key": "indian", "emoji": "🇮🇳", "label_en": "Indian", "label_sv": "Indiskt"},
]


def load_restaurant_links() -> dict:
    try:
        with open("data/restaurant_links.json", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("[WARN] restaurant_links.json missing or malformed, skipping links.")
        return {}


def load_scrape_meta(day: str) -> dict:
    path = f"data/scrape_meta_{day}.json"
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _item_search_text(item: dict) -> str:
    return " ".join(
        [
            item.get("name") or "",
            item.get("description") or "",
            item.get("category") or "",
            " ".join(item.get("tags") or []),
        ]
    ).lower()


def prepare_restaurants(lunch_data: dict, restaurant_links: dict) -> list[dict]:
    restaurants = []
    for scraper_key, payload in lunch_data.items():
        if not isinstance(payload, dict):
            continue
        items_out = []
        for item in payload.get("items") or []:
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or "").strip()
            description = (item.get("description") or "").strip()
            # Some scrapers put the whole dish in description with an empty name.
            if not name and description:
                display_item_name = ""
            else:
                display_item_name = name
            items_out.append(
                {
                    "name": display_item_name,
                    "description": description,
                    "category": (item.get("category") or "").strip(),
                    "price": (item.get("price") or "").strip(),
                    "tags": item.get("tags") or [],
                    "emoji_tags": item.get("emoji_tags") or [],
                    "search_text": _item_search_text(item),
                }
            )

        links = restaurant_links.get(link_key(scraper_key)) or {}
        search_parts = [display_name(scraper_key).lower()]
        for item in items_out:
            search_parts.append(item["search_text"])

        restaurants.append(
            {
                "id": scraper_key,
                "name": display_name(scraper_key),
                "dishes": items_out,
                "tags": payload.get("tags") or [],
                "emoji_tags": payload.get("emoji_tags") or [],
                "stale": bool(payload.get("stale")),
                "links": links,
                "search_text": " ".join(search_parts),
            }
        )

    restaurants.sort(key=lambda r: r["name"].lower())
    return restaurants


def available_filters(restaurants: list[dict]) -> list[dict]:
    present = set()
    for r in restaurants:
        present.update(r.get("tags") or [])
    return [opt for opt in FILTER_CATALOG if opt["key"] in present]


def generate_lunch_summary(day: str) -> None:
    """Legacy per-day page generator (kept for compatibility)."""
    data_path = f"data/lunch_data_{day}.json"
    if not os.path.exists(data_path):
        print(f"[WARN] No data file for {day}: {data_path}")
        return

    annotate_file(data_path)

    with open(data_path, encoding="utf-8") as f:
        lunch_data = json.load(f)

    restaurant_links = load_restaurant_links()
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("summary_template.html")
    last_updated = datetime.now(STOCKHOLM).strftime("%Y-%m-%d %H:%M")

    output_html = template.render(
        day=day.capitalize(),
        lunch_data=lunch_data,
        restaurant_links=restaurant_links,
        last_updated=last_updated,
    )

    os.makedirs("docs", exist_ok=True)
    output_path = f"docs/lunch_{day}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_html)
    print(f"[INFO] Generated HTML summary for {day}: {output_path}")


def generate_index_page() -> None:
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)

    today = get_today_english().lower()
    today_data_path = f"data/lunch_data_{today}.json"
    lunch_data: dict = {}

    if os.path.exists(today_data_path):
        annotate_file(today_data_path)
        with open(today_data_path, encoding="utf-8") as f:
            lunch_data = json.load(f)
        # Ensure annotations exist even if file write was skipped somehow.
        annotate_menu_data(lunch_data, load_keywords())

    restaurant_links = load_restaurant_links()
    restaurants = prepare_restaurants(lunch_data, restaurant_links)
    filters = available_filters(restaurants)
    day_en, day_sv = DAY_LABELS.get(today, (today.capitalize(), today.capitalize()))
    last_updated = datetime.now(STOCKHOLM).strftime("%Y-%m-%d %H:%M")
    meta = load_scrape_meta(today)
    stale_count = sum(1 for r in restaurants if r["stale"])

    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")
    html = template.render(
        day=today,
        day_label_en=day_en,
        day_label_sv=day_sv,
        last_updated=last_updated,
        restaurants=restaurants,
        restaurant_ids=[r["id"] for r in restaurants],
        restaurant_count=len(restaurants),
        stale_count=stale_count,
        filter_options=filters,
        scrape_meta=meta,
    )

    (output_dir / "index.html").write_text(html, encoding="utf-8")
    Path("index.html").write_text(html, encoding="utf-8")
    print(f"[INFO] Generated weekly index page: {output_dir / 'index.html'}")
    print("[INFO] Generated root index page: index.html")


if __name__ == "__main__":
    generate_index_page()
