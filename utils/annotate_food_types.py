"""Annotate lunch JSON with dietary / cuisine tags for filtering and display."""

from __future__ import annotations

import json
from typing import Dict, List, Tuple


def load_keywords() -> dict:
    with open("data/food_tags.json", encoding="utf-8") as f:
        return json.load(f)


def _match_tags(text: str, tag_data: dict) -> Tuple[List[str], List[str]]:
    """Return (tag_keys, emojis) ordered by priority, unique."""
    full_text = text.lower()
    matched: List[Tuple[int, str, str]] = []

    for tag, info in tag_data.items():
        keywords = [kw.lower() for kw in info.get("keywords", [])]
        if any(kw in full_text for kw in keywords):
            matched.append((info.get("priority", 100), tag, info.get("emoji", "")))

    matched.sort(key=lambda row: row[0])
    tags: List[str] = []
    emojis: List[str] = []
    seen_tags = set()
    seen_emoji = set()
    for _, tag, emoji in matched:
        if tag not in seen_tags:
            tags.append(tag)
            seen_tags.add(tag)
        if emoji and emoji not in seen_emoji:
            emojis.append(emoji)
            seen_emoji.add(emoji)
    return tags, emojis


def annotate_menu_data(data: dict, tag_data: dict | None = None) -> dict:
    """Annotate an in-memory lunch_data dict; returns the same dict mutated."""
    if tag_data is None:
        tag_data = load_keywords()

    for _scraper_name, menu in data.items():
        if not isinstance(menu, dict):
            continue

        items = menu.get("items") or []
        restaurant_parts: List[str] = []

        for item in items:
            if not isinstance(item, dict):
                continue
            item_text = " ".join(
                [
                    item.get("name") or "",
                    item.get("description") or "",
                    item.get("category") or "",
                ]
            )
            restaurant_parts.append(item_text)
            tags, emojis = _match_tags(item_text, tag_data)
            item["tags"] = tags
            item["emoji_tags"] = emojis

        tags, emojis = _match_tags(" ".join(restaurant_parts), tag_data)
        menu["tags"] = tags
        menu["emoji_tags"] = emojis

    return data


def annotate_file(filename: str) -> None:
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)

    annotate_menu_data(data)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Annotated food tags in {filename}")
