import json
from utils.annotate_food_types import annotate_menu_data
from utils.restaurants import display_name, link_key


def test_display_names():
    assert display_name("CuckoosNestScraper") == "Cuckoo's Nest"
    assert link_key("BombayBistroScraper") == "BombayBistro"


def test_annotate_adds_tags():
    data = {
        "DemoScraper": {
            "day": "friday",
            "items": [
                {
                    "name": "Vegetarisk pasta",
                    "description": "Med tofu",
                    "category": "",
                    "price": "90 kr",
                }
            ],
        }
    }
    annotate_menu_data(data, {
        "vegan": {"keywords": ["vegetarisk", "tofu"], "emoji": "🌱", "priority": 1},
        "pasta": {"keywords": ["pasta"], "emoji": "🍝", "priority": 2},
    })
    menu = data["DemoScraper"]
    assert "vegan" in menu["tags"]
    assert "pasta" in menu["tags"]
    assert menu["items"][0]["tags"]
