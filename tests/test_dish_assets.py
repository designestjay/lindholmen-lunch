import gzip
import re
from pathlib import Path

DISHES = Path("docs/assets/dishes")


def test_placeholder_stays_inside_the_svg_budget():
    svg = (DISHES / "placeholder.svg").read_bytes()
    text = svg.decode("utf-8")
    assert len(svg) <= 6 * 1024
    assert len(gzip.compress(svg)) <= int(2.5 * 1024)
    assert text.count("<path") <= 40
    assert 'viewBox="0 0 64 64"' in text
    assert "c8ff36" not in text.lower()
    for forbidden in ("<image", "<text", "<filter", "<linearGradient", "<radialGradient"):
        assert forbidden not in text
    colours = set(re.findall(r"#[0-9a-fA-F]{3,8}", text))
    assert colours <= {"#111"}
