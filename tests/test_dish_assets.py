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
)

DISHES = Path("docs/assets/dishes")
PAGE = "#f2f2f0"


def _svg(paths: int = 5, d: str = "M8 40h48", group_stroke: str = "currentColor") -> bytes:
    body = "".join(
        f'<path vector-effect="non-scaling-stroke" d="{d}"/>'
        for _ in range(paths)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" color="#111" fill="none">'
        f'<g id="art" stroke="{group_stroke}" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round">'
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
    assert [path.name for path in files] == ["placeholder.svg"]
    for path in files:
        assert check_dish_svg(path.read_bytes()) == []


def test_currentcolor_stroke_passes_and_a_fill_fails():
    assert check_dish_svg(_svg()) == []
    filled = _svg().replace(b"<path ", b'<path fill="#c8ff36" ', 1)
    assert any("fill" in problem for problem in check_dish_svg(filled))
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
