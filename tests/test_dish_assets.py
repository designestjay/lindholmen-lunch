import gzip
from pathlib import Path

from utils.dish_svg import (
    FILL_COLOURS,
    GZIP_LIMIT,
    MAX_PATHS,
    MAX_SUBPATHS,
    PROTEIN_STROKES,
    RAW_LIMIT,
    STROKE_COLOURS,
    check_dish_svg,
    contrast_ratio,
    detect_protein,
    protein_for,
)

DISHES = Path("docs/assets/dishes")
PAGE = "#f2f2f0"


def _svg(
    paths: int = 5,
    d: str = "M8 40h48",
    group_stroke: str = "currentColor",
    width: str = "1.25",
    vector: bool = True,
    path_attrs: str = "",
) -> bytes:
    effect = ' vector-effect="non-scaling-stroke"' if vector else ""
    extra = f" {path_attrs}" if path_attrs else ""
    body = "".join(
        f"<path{effect}{extra} d=\"{d}\"/>"
        for _ in range(paths)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" color="#111" fill="none">'
        f'<g id="art" stroke="{group_stroke}" stroke-width="{width}" fill="none" stroke-linecap="round" stroke-linejoin="round">'
        f"{body}</g></svg>"
    ).encode()


def test_module_contract():
    import utils.dish_svg as dish_svg
    assert dish_svg.__doc__ == (
        "Line art is ink-only: strokes are currentColor and the root colour is #111. "
        "The protein colour comes from the page via CSS on the <use> host."
    )
    assert STROKE_COLOURS == {"currentcolor"}
    assert FILL_COLOURS == {"none", "transparent"}
    assert MAX_PATHS == 12
    assert MAX_SUBPATHS == 160
    assert RAW_LIMIT == 7 * 1024
    assert GZIP_LIMIT == int(2.5 * 1024)


def test_protein_strokes_clear_the_page_background():
    assert set(PROTEIN_STROKES) == {"beef", "pork", "chicken", "fish", "veg", "other"}
    for colour in PROTEIN_STROKES.values():
        assert contrast_ratio(colour, PAGE) >= 4.5


def test_committed_dish_svgs_pass_the_style_check():
    files = sorted(DISHES.glob("*.svg"))
    assert [path.name for path in files] == [
        "caesar-salad.svg",
        "dumplings.svg",
        "kottbullar.svg",
        "lamb.svg",
        "naan.svg",
        "noodle-soup.svg",
        "pasta-cream.svg",
        "pasta-pesto.svg",
        "pho.svg",
        "raita-chutney.svg",
        "salad-bowl.svg",
        "salmon.svg",
        "shrimp.svg",
        "steak.svg",
        "sushi-mix.svg",
        "tandoori.svg",
        "tempura.svg",
        "tikka-masala.svg",
        "white-fish.svg",
        "wok.svg",
        "yakitori.svg",
    ]
    for path in files:
        assert check_dish_svg(path.read_bytes()) == [], path.name
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert '<g id="art"' in text and 'fill="none"' in text.split("<g id=\"art\"", 1)[1].split(">", 1)[0]
        assert 'fill="currentColor"' not in text
    for name in ("kottbullar", "pasta-cream", "pho", "salad-bowl", "sushi-mix", "tikka-masala"):
        assert 'stroke-width="1.75"' in (DISHES / f"{name}.svg").read_text(encoding="utf-8")


def test_currentcolor_stroke_passes_and_a_fill_fails():
    assert check_dish_svg(_svg()) == []
    assert check_dish_svg(_svg(vector=False)) == []
    assert check_dish_svg(_svg(width="3")) == []
    assert any("fill" in problem for problem in check_dish_svg(_svg(path_attrs='fill="currentColor"')))
    bare = _svg().replace(b'stroke-width="1.25" fill="none"', b'stroke-width="1.25"', 1)
    assert any("art fill" in problem for problem in check_dish_svg(bare))
    filled = _svg().replace(b"<path ", b'<path fill="#c8ff36" ', 1)
    assert any("fill" in problem for problem in check_dish_svg(filled))
    styled = _svg().replace(b"<path ", b'<path style="fill: #c8ff36" ', 1)
    assert any("fill" in problem for problem in check_dish_svg(styled))
    transparent_root = _svg().replace(b'color="#111" fill="none"', b'color="#111" fill="transparent"', 1)
    assert any("root fill" in problem for problem in check_dish_svg(transparent_root))
    assert any("stroke-width" in problem for problem in check_dish_svg(_svg(width="1.2")))
    assert any("stroke-width" in problem for problem in check_dish_svg(_svg(width="3.1")))
    odd = _svg().replace(b'vector-effect="non-scaling-stroke"', b'vector-effect="fixed-position"', 1)
    assert any("vector-effect" in problem for problem in check_dish_svg(odd))
    assert "#fff4cc" not in FILL_COLOURS
    assert "#c8ff36" not in FILL_COLOURS


def test_precision_transform_and_path_count():
    precise = _svg(d="M8.25 40h48")
    assert any("decimal" in problem for problem in check_dish_svg(precise))
    transformed = _svg().replace(b"<g ", b'<g transform="translate(1 1)" ', 1)
    assert any("transform" in problem for problem in check_dish_svg(transformed))
    assert any("paths" in problem for problem in check_dish_svg(_svg(paths=4)))
    assert any("paths" in problem for problem in check_dish_svg(_svg(paths=13)))
    many = _svg(d="M1 1" + " m2 0" * 161)
    assert any("subpaths" in problem for problem in check_dish_svg(many))


def test_raw_budget_still_caps_at_7kb():
    over = _svg(d="M0 0" + " l1 0" * 2000)
    assert len(over) > RAW_LIMIT
    assert any("raw" in problem for problem in check_dish_svg(over))
    repetitive = _svg(paths=12, d="M0 0h1")
    assert len(gzip.compress(repetitive)) <= GZIP_LIMIT


def test_protein_comes_from_the_dish_text():
    assert detect_protein("Nötkött med sås") == "beef"
    assert detect_protein("Fläskfilé") == "pork"
    assert detect_protein("Kyckling tikka") == "chicken"
    assert detect_protein("Chili shrimp") == "fish"
    assert detect_protein("Laxfilé") == "fish"
    assert detect_protein("Räkor") == "fish"
    assert detect_protein("Vegetarisk lasagne") == "veg"
    assert detect_protein("Kyckling och räkor") is None
    assert detect_protein("Murg methi malai") is None
    assert detect_protein("Soppa", tags=["fish"]) == "fish"
    assert detect_protein("Kyckling", tags=["veg"]) is None
    assert protein_for("Pho", category="pho") == "beef"
    assert protein_for("Pho med kyckling", category="pho") == "chicken"
    assert protein_for("Köttbullar", category="kottbullar") == "beef"
    assert protein_for("Vegobullar", category="kottbullar") == "veg"
    assert protein_for("Kyckling och räkor", category="pho") is None
    assert protein_for("Tikka masala", category="tikka-masala") == "chicken"
    assert protein_for("Sallad", category="salad-bowl") == "veg"
    assert protein_for("Sushi", category="sushi-mix") == "fish"
    assert protein_for("Krämig pasta", category="pasta-cream") is None
    assert protein_for("Pasta pesto", category="pasta-pesto") == "veg"
    assert protein_for("Halstrad", category="salmon") == "fish"
    assert protein_for("Dagens", category="shrimp") == "fish"
    assert protein_for("Dagens", category="white-fish") == "fish"
    assert protein_for("Spett", category="yakitori") == "chicken"
    assert protein_for("Grillat", category="tandoori") == "chicken"
    assert protein_for("Entrecôte", category="steak") == "beef"
    assert protein_for("Sås", category="raita-chutney") == "veg"
    assert protein_for("Kyckling", category="steak") == "chicken"
    assert protein_for("Naan", category="naan") is None
    assert protein_for("Wok", category="wok") is None
    assert protein_for("Lamm", category="lamb") is None
    assert protein_for(
        "Pasta pesto getost, bakade tomater, pesto",
        ["fish", "chicken", "beef"],
        "pasta-pesto",
    ) is None
    assert protein_for("Lufttorkad skinka/mozzarella/pesto", ["pork"]) == "pork"
    assert protein_for("Fläskpasta", category="pasta-cream") == "pork"
