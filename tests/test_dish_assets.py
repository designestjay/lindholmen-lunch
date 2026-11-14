import gzip
from xml.etree import ElementTree

from utils.dish_svg import FILL_COLOURS, GZIP_LIMIT, RAW_LIMIT, check_dish_svg
from pathlib import Path

DISHES = Path("docs/assets/dishes")


def _svg(body: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f"{body}</svg>"
    ).encode()


def test_committed_dish_svgs_pass_the_style_check():
    files = sorted(DISHES.glob("*.svg"))
    assert files == [DISHES / "placeholder.svg"]
    for path in files:
        assert check_dish_svg(path.read_bytes()) == []


def test_lime_and_the_soft_secondary_fill_are_allowed():
    svg = _svg(
        '<path d="M8 40h48" fill="#fff4cc" stroke="#111" stroke-width="1.25"/>'
        '<path d="M20 28h12" fill="#c8ff36" stroke="#111"/>'
    )
    assert check_dish_svg(svg) == []


def test_a_fill_outside_the_palette_is_rejected():
    svg = _svg('<path d="M8 8h20" fill="#ff00aa" stroke="#111"/>')
    problems = check_dish_svg(svg)
    assert any("fill" in problem for problem in problems)
    assert "#ff00aa" not in FILL_COLOURS


def test_raw_may_reach_7kb_while_gzip_stays_capped():
    assert RAW_LIMIT == 7 * 1024
    assert GZIP_LIMIT == int(2.5 * 1024)
    bulky = _svg('<path d="M0 0h1" stroke="#111" fill="none"/>' + (" " * 6000))
    assert len(bulky) <= RAW_LIMIT
    assert check_dish_svg(bulky) == []
    over = _svg('<path d="M0 0' + (" l1 0" * 2000) + '" stroke="#111" fill="none"/>')
    assert len(over) > RAW_LIMIT
    assert any("raw" in problem for problem in check_dish_svg(over))
    repetitive = _svg(
        "".join(
            f'<path d="M{i % 60} {i % 60}h2" stroke="#111" fill="none"/>'
            for i in range(800)
        )
    )
    assert len(gzip.compress(repetitive)) > GZIP_LIMIT or len(repetitive) > RAW_LIMIT
    assert check_dish_svg(repetitive)


def test_placeholder_stays_a_neutral_line():
    text = (DISHES / "placeholder.svg").read_text(encoding="utf-8")
    root = ElementTree.fromstring(text.encode())
    assert root.get("viewBox") == "0 0 64 64"
    assert "c8ff36" not in text.lower()
    assert "fff4cc" not in text.lower()
