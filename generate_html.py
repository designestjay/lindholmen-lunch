# file: lindholmen_lunch/generate_html.py

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

from utils.annotate_food_types import annotate_file, annotate_menu_data, load_keywords
from utils.restaurants import DISPLAY_NAMES, display_name, link_key
from utils.dish_category import classify, coverage_line, load_library, load_taxonomy, normalise, update_image_queue
from utils.dish_svg import PROTEIN_LABELS, protein_for
from utils.holidays import holiday_dates
from utils.sources import is_inactive, is_link_only, is_rotating, load_sources
from utils.utils import get_today_english

STOCKHOLM = ZoneInfo("Europe/Stockholm")
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
SITE = "https://iamjaydesign.com/lindholmen-lunch"

DAY_LABELS = {
    "monday": ("Monday", "Måndag"),
    "tuesday": ("Tuesday", "Tisdag"),
    "wednesday": ("Wednesday", "Onsdag"),
    "thursday": ("Thursday", "Torsdag"),
    "friday": ("Friday", "Fredag"),
    "saturday": ("Saturday", "Lördag"),
    "sunday": ("Sunday", "Söndag"),
}

SV_DAY_SHORT = ["mån", "tis", "ons", "tor", "fre", "lör", "sön"]
SV_DAY_LONG = ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"]
EN_DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
EN_DAY_LONG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SV_MONTH = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
EN_MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Chip order matches the 5-second task. A chip is rendered only when today's
# dishes actually contain that token.
FILTERS = [
    {"key": "vego", "label_en": "Veggie", "label_sv": "Vego"},
    {"key": "fish", "label_en": "Fish", "label_sv": "Fisk"},
    {"key": "chicken", "label_en": "Chicken", "label_sv": "Kyckling"},
    {"key": "under130", "label_en": "Under 130 kr", "label_sv": "Under 130 kr"},
    {"key": "pasta", "label_en": "Pasta", "label_sv": "Pasta"},
    {"key": "asian", "label_en": "Asian", "label_sv": "Asiatiskt"},
    {"key": "indian", "label_en": "Indian", "label_sv": "Indiskt"},
    {"key": "salad", "label_en": "Salad", "label_sv": "Sallad"},
    {"key": "sushi", "label_en": "Sushi", "label_sv": "Sushi"},
]

PILL_SPECS = [
    ("vego", {"veg", "vegan"}, "Veggie", "Vego"),
    ("fish", {"fish"}, "Fish", "Fisk"),
    ("chicken", {"chicken"}, "Chicken", "Kyckling"),
    ("pasta", {"pasta"}, "Pasta", "Pasta"),
    ("salad", {"salad"}, "Salad", "Sallad"),
    ("sushi", {"sushi"}, "Sushi", "Sushi"),
    ("indian", {"indian"}, "Indian", "Indiskt"),
    ("asian", {"japanese", "thai", "korean"}, "Asian", "Asiatiskt"),
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


def parse_price(value: str) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", value)
    if not match:
        return None
    return int(match.group(0))


_PRICE_AMOUNT = re.compile(r"\d+(?:[.,]\d+)?")
_PRICE_UNIT = re.compile(r"\s*(?:kr|sek)\b", re.IGNORECASE)
_DISH_ACRONYMS = {"BBQ", "IPA"}


def split_price(price_raw: str) -> tuple[str, str]:
    """Keep the first amount in the price column and return any further amounts as a note."""
    text = (price_raw or "").strip()
    amounts = list(_PRICE_AMOUNT.finditer(text))
    if len(amounts) < 2:
        return text, ""
    unit = _PRICE_UNIT.match(text, amounts[0].end())
    end = unit.end() if unit else amounts[0].end()
    primary = text[:end].strip(" ,;/")
    note = text[end:].lstrip(" ,;/-–—").strip()
    return primary, note


def sentence_case_dish(name: str) -> str:
    """Sentence-case a fully uppercase dish name, keeping BBQ and IPA."""
    text = (name or "").strip()
    if len(text) <= 3 or text != text.upper() or not any(ch.isalpha() for ch in text):
        return text
    words = []
    for index, word in enumerate(text.split()):
        letters = "".join(ch for ch in word if ch.isalpha())
        if letters in _DISH_ACRONYMS:
            words.append(word)
            continue
        lower = word.lower()
        if index == 0 and lower:
            lower = lower[0].upper() + lower[1:]
        words.append(lower)
    return " ".join(words)


def dish_filter_tokens(tags: list[str] | None, price: int | None) -> list[str]:
    """Tokens the filter chips match. `vego` covers both veg and vegan."""
    tokens = set(tags or [])
    if tokens & {"veg", "vegan"}:
        tokens.add("vego")
    if tokens & {"japanese", "thai", "korean"}:
        tokens.add("asian")
    if price is not None and 0 < price <= 130:
        tokens.add("under130")
    return sorted(tokens)


def pills_for(tags: list[str] | None) -> list[dict]:
    tagset = set(tags or [])
    pills = []
    for key, keys, label_en, label_sv in PILL_SPECS:
        if tagset & keys:
            pills.append({"key": key, "en": label_en, "sv": label_sv})
    if any(pill["key"] == "sushi" for pill in pills):
        pills = [pill for pill in pills if pill["key"] != "asian"]
    return pills


def _parse_stamp(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=STOCKHOLM)
    return parsed.astimezone(STOCKHOLM)


def format_stamp(when: datetime) -> dict:
    local = when.astimezone(STOCKHOLM)
    weekday = local.weekday()
    month = local.month - 1
    return {
        "iso": local.date().isoformat(),
        "hhmm": local.strftime("%H:%M"),
        "trust_sv": f"{SV_DAY_SHORT[weekday].capitalize()} {local.day} {SV_MONTH[month]}",
        "trust_en": f"{EN_DAY_SHORT[weekday]} {local.day} {EN_MONTH[month]}",
        "long_sv": f"{SV_DAY_LONG[weekday]} {local.day} {SV_MONTH[month]}",
        "long_en": f"{EN_DAY_LONG[weekday]} {local.day} {EN_MONTH[month]}",
        "short_sv": f"{SV_DAY_SHORT[weekday]} {local.day} {SV_MONTH[month]}",
        "short_en": f"{EN_DAY_SHORT[weekday]} {local.day} {EN_MONTH[month]}",
    }


def prepare_restaurants(lunch_data: dict, restaurant_links: dict, fallback_stamp: dict | None) -> list[dict]:
    restaurants = []
    queue_rows = []
    taxonomy = load_taxonomy()
    library = (load_library().get("categories") or {})
    sources = load_sources()
    for scraper_key, payload in lunch_data.items():
        if not isinstance(payload, dict):
            continue
        if is_inactive(scraper_key, sources) or is_link_only(scraper_key, sources):
            continue
        items_out = []
        for item in payload.get("items") or []:
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or "").strip()
            description = (item.get("description") or "").strip()
            price_raw = (item.get("price") or "").strip()
            price_value = parse_price(price_raw)
            tags = item.get("tags") or []
            if name:
                display_item_name = sentence_case_dish(name)
                visible_description = description
            elif description:
                display_item_name = sentence_case_dish(description)
                visible_description = ""
            else:
                display_item_name = ""
                visible_description = ""
            price_text, price_note = split_price(price_raw) if price_value is not None else ("", "")
            decision = classify(
                display_item_name or name,
                visible_description or description,
                display_name(scraper_key),
                taxonomy,
            )
            slug = decision.get("dish_category") or ""
            entry = library.get(slug) if slug else None
            has_text = bool(entry and (entry.get("what") or {}).get("sv"))
            svg_file = Path(f"docs/assets/dishes/{slug}.svg") if slug else None
            has_svg = bool(svg_file and svg_file.is_file())
            confidence = float(decision.get("category_confidence") or 0)
            protein = protein_for(
                f"{display_item_name or name} {visible_description or description}",
                tags,
                slug,
            )
            protein_sv, protein_en = PROTEIN_LABELS.get(protein, ("", ""))
            pills = pills_for(tags)
            if protein_sv and all(pill["sv"] != protein_sv for pill in pills):
                pills = pills + [{"key": protein, "en": protein_en, "sv": protein_sv}]
            items_out.append(
                {
                    "name": display_item_name,
                    "description": visible_description,
                    "category": (item.get("category") or "").strip(),
                    "price": price_text,
                    "price_note": price_note,
                    "tags": tags,
                    "pills": pills,
                    "protein": protein or "",
                    "protein_sv": protein_sv,
                    "protein_en": protein_en,
                    "filter_tokens": " ".join(dish_filter_tokens(tags, price_value)),
                    "search_text": _item_search_text(item),
                    "dish_category": slug,
                    "dish_confidence": confidence,
                    "dish_image": (
                        f"assets/dishes/{slug}.svg" if has_svg
                        else ("assets/dishes/placeholder.svg" if has_text else "")
                    ),
                    "dish_sheet": has_text,
                    "shown_image": bool(has_svg and entry and entry.get("status") == "approved" and confidence >= 0.8),
                }
            )
            queue_rows.append(
                {
                    "key": normalise(display_item_name or name),
                    "name": display_item_name or name,
                    "description": visible_description or description,
                    "restaurant": display_name(scraper_key),
                    "dish_category": slug or None,
                    "category_confidence": confidence,
                    "ignored": bool(decision.get("ignored")),
                    "closed_dish": bool(decision.get("closed")),
                }
            )

        links = restaurant_links.get(link_key(scraper_key)) or {}
        search_parts = [display_name(scraper_key).lower()]
        token_set = set()
        for item in items_out:
            search_parts.append(item["search_text"])
            token_set.update(item["filter_tokens"].split())

        fetched = _parse_stamp(payload.get("fetched_at"))
        stamp = format_stamp(fetched) if fetched else fallback_stamp
        restaurants.append(
            {
                "id": scraper_key,
                "name": display_name(scraper_key),
                "name_lower": display_name(scraper_key).lower(),
                "dishes": items_out,
                "tags": payload.get("tags") or [],
                "filter_tokens": " ".join(sorted(token_set)),
                "stale": bool(payload.get("stale")),
                "closed": bool(payload.get("closed")),
                "rotating": is_rotating(scraper_key, sources),
                "link_only": False,
                "links": links,
                "search_text": " ".join(search_parts),
                "stale_short_sv": stamp["short_sv"] if stamp else "",
                "stale_short_en": stamp["short_en"] if stamp else "",
            }
        )

    restaurants.extend(link_only_restaurants(restaurant_links, sources))
    restaurants.sort(key=lambda row: (row["stale"], row["name_lower"]))
    for index, restaurant in enumerate(restaurants, start=1):
        restaurant["rank"] = f"{index:02d}"
    prepare_restaurants.queue_rows = queue_rows
    return restaurants


def link_only_restaurants(restaurant_links: dict, sources: dict) -> list[dict]:
    cards = []
    for scraper_key, info in sources.items():
        if not info.get("link_only"):
            continue
        links = dict(restaurant_links.get(link_key(scraper_key)) or {})
        human = info.get("human_link") or links.get("url") or ""
        links["url"] = human
        name = info.get("display") or display_name(scraper_key)
        cards.append(
            {
                "id": scraper_key,
                "name": name,
                "name_lower": name.lower(),
                "dishes": [],
                "tags": [],
                "filter_tokens": "",
                "stale": False,
                "closed": False,
                "rotating": False,
                "link_only": True,
                "links": links,
                "search_text": name.lower(),
                "stale_short_sv": "",
                "stale_short_en": "",
            }
        )
    return cards


def available_filters(restaurants: list[dict]) -> list[dict]:
    present = set()
    for restaurant in restaurants:
        present.update((restaurant.get("filter_tokens") or "").split())
    return [opt for opt in FILTERS if opt["key"] in present]


def restaurant_directory(links: dict) -> list[dict]:
    sources = load_sources()
    rows = []
    for scraper_key in DISPLAY_NAMES:
        if is_inactive(scraper_key, sources):
            continue
        info = links.get(link_key(scraper_key)) or {}
        rows.append(
            {
                "name": display_name(scraper_key),
                "url": info.get("url") or "",
                "map": info.get("map") or "",
            }
        )
    rows.sort(key=lambda row: row["name"].lower())
    return rows


def missing_restaurants(meta: dict, links: dict) -> list[dict]:
    sources = load_sources()
    rows = []
    names = list(meta.get("missing") or []) + list(meta.get("wrong_week") or [])
    for scraper_key in names:
        if is_inactive(scraper_key, sources) or is_link_only(scraper_key, sources):
            continue
        info = links.get(link_key(scraper_key)) or {}
        rows.append(
            {
                "name": display_name(scraper_key),
                "url": info.get("url") or "",
                "map": info.get("map") or "",
            }
        )
    rows.sort(key=lambda row: row["name"].lower())
    return rows


def write_sitemap(lastmod: str) -> None:
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{SITE}/</loc><lastmod>{lastmod}</lastmod></url>
  <url><loc>{SITE}/privacy.html</loc><lastmod>{lastmod}</lastmod></url>
</urlset>
"""
    Path("docs/sitemap.xml").write_text(body, encoding="utf-8")


def write_privacy() -> None:
    """Render the privacy page from SITE so the canonical URL is not hardcoded."""
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template_path = Path("templates/privacy.html")
    template_bytes = template_path.read_bytes()
    html = env.get_template("privacy.html").render(site=SITE)
    # Jinja normalizes newlines and drops the trailing one. Keep the
    # template's so a regen does not rewrite the whole page.
    if b"\r\n" in template_bytes:
        html = html.replace("\r\n", "\n").replace("\n", "\r\n")
        if template_bytes.endswith(b"\r\n") and not html.endswith("\r\n"):
            html += "\r\n"
    elif template_bytes.endswith(b"\n") and not html.endswith("\n"):
        html += "\n"
    Path("docs").mkdir(exist_ok=True)
    Path("docs/privacy.html").write_text(html, encoding="utf-8", newline="")
    Path("privacy.html").write_text(html, encoding="utf-8", newline="")


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


def generate_index_page(day: str | None = None) -> None:
    output_dir = Path("docs")
    output_dir.mkdir(exist_ok=True)

    today = (day or get_today_english()).lower()
    today_data_path = f"data/lunch_data_{today}.json"
    lunch_data: dict = {}

    if os.path.exists(today_data_path):
        annotate_file(today_data_path)
        with open(today_data_path, encoding="utf-8") as f:
            lunch_data = json.load(f)
        annotate_menu_data(lunch_data, load_keywords())

    restaurant_links = load_restaurant_links()
    meta = load_scrape_meta(today)
    stamp = _parse_stamp(meta.get("scraped_at"))
    formatted = format_stamp(stamp) if stamp else None
    restaurants = prepare_restaurants(lunch_data, restaurant_links, formatted)
    filters = available_filters(restaurants)
    day_en, day_sv = DAY_LABELS.get(today, (today.capitalize(), today.capitalize()))
    missing = missing_restaurants(meta, restaurant_links)
    sources = load_sources()
    fresh_count = sum(
        1 for restaurant in restaurants
        if not restaurant["stale"] and not restaurant.get("link_only") and not restaurant.get("closed")
    )
    total = sum(
        1 for key in DISPLAY_NAMES
        if not is_inactive(key, sources) and not is_link_only(key, sources)
    )
    menu_date = formatted["iso"] if formatted else ""
    queue_new = update_image_queue(getattr(prepare_restaurants, "queue_rows", []), menu_date or "1970-01-01")
    print(coverage_line(getattr(prepare_restaurants, "queue_rows", []), queue_new))
    present = sorted({
        item["dish_category"]
        for restaurant in restaurants
        for item in restaurant["dishes"]
        if item.get("dish_sheet") and item.get("dish_category")
    })
    library = load_library().get("categories") or {}
    dish_info = {slug: library[slug] for slug in present if slug in library}
    holidays = ",".join(holiday_dates())
    hhmm = formatted["hhmm"] if formatted else ""
    trust_sv = formatted["trust_sv"] if formatted else day_sv
    trust_en = formatted["trust_en"] if formatted else day_en
    date_copy = {
        "h1_sm_today_sv": "Lunch på Lindholmen idag",
        "h1_sm_today_en": "Lunch in Lindholmen today",
        "h1_lg_today_sv": "Lunch idag.",
        "h1_lg_today_en": "Lunch today.",
        "h1_sm_weekend_sv": "Lunch på Lindholmen i fredags",
        "h1_sm_weekend_en": "Lunch in Lindholmen last Friday",
        "h1_lg_weekend_sv": "Fredagens lunch.",
        "h1_lg_weekend_en": "Friday's lunch.",
        "missing_today_sv": f"Ingen meny hittad idag ({len(missing)})",
        "missing_today_en": f"No menu found today ({len(missing)})",
        "missing_weekend_sv": f"Ingen meny hittad i fredags ({len(missing)})",
        "missing_weekend_en": f"No menu found on Friday ({len(missing)})",
        "missing_day_sv": f"Ingen meny hittad {day_sv.lower()} ({len(missing)})",
        "missing_day_en": f"No menu found on {day_en} ({len(missing)})",
    }
    if formatted:
        date_copy.update({
            "wrong_sv": f"Det här är menyn från {formatted['long_sv']}. Dagens menyer kommer runt 08:00.",
            "wrong_en": f"This is {formatted['long_en']}'s menu. Today's menus arrive around 08:00.",
            "soon_sv": f"Det här är menyn från {formatted['long_sv']}. Dagens menyer kommer snart.",
            "soon_en": f"This is {formatted['long_en']}'s menu. Today's menus are coming soon.",
            "weekend_sv": "Helg. Lunchen är tillbaka på måndag.",
            "weekend_en": "It's the weekend. Lunch is back on Monday.",
        })
    else:
        date_copy.update({
            "wrong_sv": "Det här är inte dagens meny. Dagens menyer kommer runt 08:00.",
            "wrong_en": "This is not today's menu. Today's menus arrive around 08:00.",
            "soon_sv": "Det här är inte dagens meny. Dagens menyer kommer snart.",
            "soon_en": "This is not today's menu. Today's menus are coming soon.",
            "weekend_sv": "Helg. Lunchen är tillbaka på måndag.",
            "weekend_en": "It's the weekend. Lunch is back on Monday.",
        })

    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html")
    html = template.render(
        day=today,
        day_label_en=day_en,
        day_label_sv=day_sv,
        menu_date=menu_date,
        scraped_at_hhmm=hhmm,
        trust_sv=trust_sv,
        trust_en=trust_en,
        date_copy=date_copy,
        restaurants=restaurants,
        restaurant_ids=[restaurant["id"] for restaurant in restaurants],
        restaurant_count=len(restaurants),
        fresh_count=fresh_count,
        total_restaurants=total,
        stale_count=sum(1 for restaurant in restaurants if restaurant["stale"]),
        missing_restaurants=missing,
        missing_count=len(missing),
        directory=restaurant_directory(restaurant_links),
        filter_options=filters,
        scrape_meta=meta,
        site=SITE,
        dish_info=dish_info,
        holiday_dates=holidays,
    )

    (output_dir / "index.html").write_text(html, encoding="utf-8")
    write_privacy()
    lastmod = menu_date or datetime.now(STOCKHOLM).date().isoformat()
    write_sitemap(lastmod)
    print(f"[INFO] Generated index page: {output_dir / 'index.html'}")


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Render the Lindholmen Lunch page.")
    parser.add_argument(
        "--day",
        choices=WEEKDAYS,
        help="Weekday to render. Defaults to today in Europe/Stockholm.",
    )
    args = parser.parse_args()
    generate_index_page(day=args.day)


if __name__ == "__main__":
    _cli()
