"""Annotate lunch JSON with dietary / cuisine tags for filtering and display."""

from __future__ import annotations

import json
import re
from typing import Dict, List, Tuple

# Dishes that mention these are not vegetarian, even if the text also says
# "vegetarisk" (a side note) or "nötter" shares a stem with "nöt".
_MEAT_STEMS = ("kyckling", "fläsk", "nöt", "fisk", "lamm", "kött")
_VEG_TAGS = {"veg", "vegan"}


def load_keywords() -> dict:
    with open("data/food_tags.json", encoding="utf-8") as f:
        return json.load(f)


def _keyword_in_text(keyword: str, text: str) -> bool:
    """Match at a word boundary so 'veg' cannot hit 'vegetables' or 'grönsaker'."""
    if not keyword:
        return False
    return re.search(r"\b" + re.escape(keyword), text) is not None


def _strip_false_veg(tags: List[str], text: str) -> List[str]:
    low = text.lower()
    if any(stem in low for stem in _MEAT_STEMS):
        return [tag for tag in tags if tag not in _VEG_TAGS]
    return tags


def _match_tags(text: str, tag_data: dict) -> Tuple[List[str], List[str]]:
    """Return (tag_keys, emojis) ordered by priority, unique."""
    full_text = text.lower()
    matched: List[Tuple[int, str, str]] = []

    for tag, info in tag_data.items():
        keywords = [kw.lower() for kw in info.get("keywords", [])]
        if any(_keyword_in_text(kw, full_text) for kw in keywords):
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


def tags_for_text(text: str, tag_data: dict | None = None) -> List[str]:
    """Tags that the dish's own name and description support.

    Stored tags are not an input. A scraper that glued the rest of the day
    onto one description used to leave Fish and Chicken on a pesto.
    """
    if tag_data is None:
        tag_data = load_keywords()
    tags, _emojis = _match_tags(text or "", tag_data)
    return _strip_false_veg(tags, text or "")


def annotate_menu_data(data: dict, tag_data: dict | None = None) -> dict:
    """Annotate an in-memory lunch_data dict; returns the same dict mutated."""
    if tag_data is None:
        tag_data = load_keywords()

    for _scraper_name, menu in data.items():
        if not isinstance(menu, dict):
            continue

        items = menu.get("items") or []
        item_tag_lists: List[List[str]] = []

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
            tags, emojis = _match_tags(item_text, tag_data)
            tags = _strip_false_veg(tags, item_text)
            emojis = [
                tag_data.get(tag, {}).get("emoji", "")
                for tag in tags
                if tag_data.get(tag, {}).get("emoji")
            ]
            # Keep emoji order stable and unique after veg tags are removed.
            deduped: List[str] = []
            for emoji in emojis:
                if emoji not in deduped:
                    deduped.append(emoji)
            item["tags"] = tags
            item["emoji_tags"] = deduped
            item_tag_lists.append(tags)

        seen: List[str] = []
        for tags in item_tag_lists:
            for tag in tags:
                if tag not in seen:
                    seen.append(tag)
        seen.sort(key=lambda tag: tag_data.get(tag, {}).get("priority", 100))
        emojis: List[str] = []
        for tag in seen:
            emoji = tag_data.get(tag, {}).get("emoji", "")
            if emoji and emoji not in emojis:
                emojis.append(emoji)
        menu["tags"] = seen
        menu["emoji_tags"] = emojis

    return data


def annotate_file(filename: str) -> None:
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)

    annotate_menu_data(data)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Annotated food tags in {filename}")
