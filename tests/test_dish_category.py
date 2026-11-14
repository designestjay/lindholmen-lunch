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


def test_fuzzy_neighbour_is_low_confidence():
    taxonomy = load_taxonomy()
    decision = classify("tikkaa masalla", "", "Masala", taxonomy)
    assert decision["category_confidence"] <= 0.6 or decision["dish_category"] == "tikka-masala"
