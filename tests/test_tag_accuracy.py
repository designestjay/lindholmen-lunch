import json
from pathlib import Path

from generate_html import dish_filter_tokens
from utils.annotate_food_types import annotate_menu_data

MEAT_STEMS = ("kyckling", "fläsk", "nöt", "fisk")


def _item(name, description=""):
    return {
        "DemoScraper": {
            "day": "friday",
            "items": [{"name": name, "description": description, "category": "", "price": ""}],
        }
    }


def test_chicken_stew_with_vegetables_is_not_veg():
    data = _item("Kycklinggryta med grönsaker")
    annotate_menu_data(data)
    tags = data["DemoScraper"]["items"][0]["tags"]
    assert "veg" not in tags
    assert "vegan" not in tags


def test_vegetarian_lasagna_is_veg():
    data = _item("Vegetarisk lasagne")
    annotate_menu_data(data)
    tags = data["DemoScraper"]["items"][0]["tags"]
    assert "veg" in tags
    assert "pasta" in tags


def test_explicit_vegan_is_not_only_a_substring():
    data = _item("Vegansk böngryta")
    annotate_menu_data(data)
    tags = data["DemoScraper"]["items"][0]["tags"]
    assert "vegan" in tags


def test_vego_chip_covers_veg_and_vegan():
    assert "vego" in dish_filter_tokens(["veg"], None)
    assert "vego" in dish_filter_tokens(["vegan"], None)
    assert "under130" in dish_filter_tokens([], 129)
    assert "under130" not in dish_filter_tokens([], 131)


def test_friday_data_has_no_veg_tag_on_meat_or_fish():
    raw = json.loads(Path("data/lunch_data_friday.json").read_text(encoding="utf-8"))
    for menu in raw.values():
        if not isinstance(menu, dict):
            continue
        menu.pop("tags", None)
        menu.pop("emoji_tags", None)
        for item in menu.get("items") or []:
            if isinstance(item, dict):
                item.pop("tags", None)
                item.pop("emoji_tags", None)
    annotate_menu_data(raw)
    for menu in raw.values():
        for item in menu.get("items") or []:
            text = " ".join(
                [
                    item.get("name") or "",
                    item.get("description") or "",
                    item.get("category") or "",
                ]
            ).lower()
            if any(stem in text for stem in MEAT_STEMS):
                assert "veg" not in (item.get("tags") or []), text
