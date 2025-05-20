import json
import re

def load_keywords():
    with open("data/food_tags.json", encoding="utf-8") as f:
        return json.load(f)

import json

def load_keywords():
    with open("data/food_tags.json", encoding="utf-8") as f:
        return json.load(f)

def annotate_file(filename: str):
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)

    tag_data = load_keywords()

    for scraper_name, menu in data.items():
        # Combine name, description, and category into a searchable text block
        text_parts = []
        for item in menu.get("items", []):
            text_parts.append(item.get("name", ""))
            text_parts.append(item.get("description", ""))
            text_parts.append(item.get("category", ""))

        full_text = " ".join(text_parts).lower()

        matched_tags = []

        for tag, info in tag_data.items():
            keywords = [kw.lower() for kw in info["keywords"]]
            emoji = info["emoji"]
            priority = info.get("priority", 100)  # Default priority if missing
            if any(kw in full_text for kw in keywords):
                matched_tags.append((priority, emoji))

        # Sort by priority and keep only unique emojis
        sorted_emojis = []
        seen = set()
        for _, emoji in sorted(matched_tags):
            if emoji not in seen:
                sorted_emojis.append(emoji)
                seen.add(emoji)

        menu["emoji_tags"] = sorted_emojis

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Annotated emoji tags in {filename} (prioritized & fuzzy match)")

