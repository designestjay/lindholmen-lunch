from utils.dish_category import classify, load_taxonomy


def test_known_dishes_and_exclusions():
    taxonomy = load_taxonomy()
    butter = classify("Butter chicken", "", "Masala", taxonomy)
    assert butter["dish_category"] == "butter-chicken"
    assert classify("Indisk curry", "", "Miss F", taxonomy)["dish_category"] == "indian-curry"
    paneer = classify("Paneer tikka", "", "Bombay Bistro", taxonomy)
    assert paneer["dish_category"] != "tikka-masala"
    assert classify("Läsk", "", "Oishii", taxonomy).get("ignored") is True
    assert classify("Stängt", "", "Bistrot", taxonomy).get("closed") is True
    assert classify("Beef pho", "", "Encounter Asian", taxonomy)["dish_category"] == "pho"
    medaljong = classify("Fläskmedaljong", "", "Kooperativet", taxonomy)
    assert medaljong["dish_category"] != "bean-lentil"


def test_pesto_on_a_ham_sandwich_is_not_pasta_pesto():
    taxonomy = load_taxonomy()
    sandwich = classify("Lufttorkad skinka/mozzarella/pesto", "", "Miss F", taxonomy)
    assert sandwich["dish_category"] != "pasta-pesto"
    assert classify("Pasta pesto", "getost, bakade tomater, pesto", "Uni3", taxonomy)["dish_category"] == "pasta-pesto"
    assert classify("Penne Pesto", "", "Benne Pastabar", taxonomy)["dish_category"] == "pasta-pesto"
    assert classify("Swedish Pesto", "", "Benne Pastabar", taxonomy)["dish_category"] == "pasta-pesto"
    assert classify("Pasta med bacon och pesto", "", "Benne Pastabar", taxonomy)["dish_category"] == "pasta-pesto"


def test_batch_two_names():
    taxonomy = load_taxonomy()
    assert classify("Bibibamp (Kyckling)", "", "Encounter Asian", taxonomy)["dish_category"] == "bibimbap"
    assert classify("Bibibamp (Veg)", "", "Encounter Asian", taxonomy)["dish_category"] == "bibimbap"
    caesar = "Ceasarsallad med grillad kyckling, grana padano, romansallad, bacon, brödkrutonger samt husets ceasardressing."
    assert classify(caesar, "", "District One", taxonomy)["dish_category"] == "caesar-salad"
    assert classify("Ceasar", "", "District One", taxonomy)["dish_category"] == "caesar-salad"
    machili = classify(
        "Machili bengali",
        'Laxfilé med grön chili och tamarind, tillagad i kryddad med färsk koriander och indiska "Panch phoron" (fem kryddor)',
        "Masala",
        taxonomy,
    )
    assert machili["dish_category"] == "salmon"
    yakiniku = classify("Yakiniku", "Skivad entrecote, grönsaker, ris, yakinikusås & sallad", "Oishii", taxonomy)
    assert yakiniku["dish_category"] == "korean-bbq"
    assert yakiniku["dish_category"] != "steak"
    bento = classify("Bentolåda", "Yakiniku, yakitori, sushi, sallad & ris", "Oishii", taxonomy)
    assert bento["dish_category"] is None
    assert classify("Bento", "3 maki, 2 nigri, 2 kycklingspett", "Oishii", taxonomy)["dish_category"] is None
    for name in ("Mangolassi", "Mineralvatten", "Papadom", "Myntasås", "Chili pickles", "Dressing"):
        assert classify(name, "", "Masala", taxonomy).get("ignored") is True
    assert classify("Slow tomato", "tomatsås", "Benne Pastabar", taxonomy)["dish_category"] == "pasta-tomato"
    assert classify("Smoked pig", "bacon i en krämig sås", "Benne Pastabar", taxonomy)["dish_category"] == "pasta-cream"
    assert classify("Swedish cheese", "ostsås", "Benne Pastabar", taxonomy)["dish_category"] == "pasta-cream"
    assert classify("The shrooms", "svampsås", "Benne Pastabar", taxonomy)["dish_category"] == "pasta-cream"
    assert classify("Silky Bird", "kyckling i tomatsås", "Benne Pastabar", taxonomy)["dish_category"] == "pasta-tomato"
    assert classify("Silky salsiccia", "salsiccia i tomatsås", "Benne Pastabar", taxonomy)["dish_category"] == "pasta-tomato"
    assert classify("Slow tomato", "tomatsås", "Miss F", taxonomy)["dish_category"] != "pasta-tomato"


def test_fuzzy_neighbour_is_low_confidence():
    taxonomy = load_taxonomy()
    decision = classify("tikkaa masalla", "", "Masala", taxonomy)
    assert decision["category_confidence"] <= 0.6 or decision["dish_category"] == "tikka-masala"


def test_new_keywords_reach_drawn_categories():
    taxonomy = load_taxonomy()
    assert classify("Bakad uer", "blomkål", "Uni3", taxonomy)["dish_category"] == "white-fish"
    assert classify("Baked Haddock", "", "Pier 11", taxonomy)["dish_category"] == "white-fish"
    assert classify("tofuwok serveras med ris", "", "Cuckoo's Nest", taxonomy)["dish_category"] == "wok"
    assert classify("Stir Fried Garlic and Pepper Tofu", "", "Kooperativet", taxonomy)["dish_category"] == "wok"
    assert classify("Högrevsburgare med brioche, sallad", "", "Cuckoo's Nest", taxonomy)["dish_category"] == "burger"
    assert classify("Tiramisu", "", "Benne Pastabar", taxonomy)["dish_category"] == "dessert-cake"
    assert classify("Kycklinggryta med ingefära", "", "Cuckoo's Nest", taxonomy)["dish_category"] == "stew-bourguignon"
    assert classify("Methi malai", "", "Bombay Bistro", taxonomy)["dish_category"] == "indian-curry"


def test_drawing_fallback_only_for_confident_rows_and_existing_files():
    from pathlib import Path

    from generate_html import drawing_slug

    taxonomy = load_taxonomy()
    dishes = Path("docs/assets/dishes")
    fallbacks = {key: value for key, value in taxonomy["drawing_fallback"].items() if not key.startswith("_")}
    for category, borrowed in fallbacks.items():
        assert category in taxonomy["categories"], category
        assert not (dishes / f"{category}.svg").exists(), category
        assert (dishes / f"{borrowed}.svg").is_file(), borrowed
    assert drawing_slug("ramen", 0.92, taxonomy) == "noodle-soup"
    assert drawing_slug("vindaloo", 0.92, taxonomy) == "indian-curry"
    assert drawing_slug("roasted-cauliflower", 0.72, taxonomy) == "roasted-cauliflower"
    assert drawing_slug("sushi-mix", 0.6, taxonomy) == "sushi-mix"
    assert drawing_slug("garlic-bread", 0.92, taxonomy) == "garlic-bread"
    assert drawing_slug("", 0.92, taxonomy) == ""
