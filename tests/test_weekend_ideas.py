import gzip
import json
import re
from pathlib import Path

from generate_html import generate_index_page

PALETTE = {"beef", "pork", "chicken", "fish", "veg", "other"}


def _html():
    generate_index_page(day="friday")
    return Path("docs/index.html").read_text(encoding="utf-8")


def _ideas(html):
    match = re.search(
        r'<script type="application/json" id="weekend-ideas">(.*?)</script>',
        html,
        re.S,
    )
    assert match, "script#weekend-ideas"
    ideas = json.loads(match.group(1))
    raw = match.group(1).encode("utf-8")
    assert len(gzip.compress(raw)) <= 5 * 1024
    return ideas


def test_weekend_ideas_json_is_drawings_only_and_small():
    html = _html()
    ideas = _ideas(html)
    library = json.loads(Path("data/dish_library.json").read_text(encoding="utf-8"))["categories"]
    drawn = {path.stem for path in Path("docs/assets/dishes").glob("*.svg")}
    slugs = [item["slug"] for item in ideas]
    assert "naan" not in slugs
    assert "raita-chutney" not in slugs
    assert slugs == sorted(slugs)
    for item in ideas:
        assert item["slug"] in drawn
        assert library[item["slug"]].get("idea") is not False
        assert item["idea_protein"] in PALETTE
        assert set(item) == {"slug", "name", "what", "idea_protein"}
        assert set(item["name"]) == {"sv", "en"}
        assert set(item["what"]) == {"sv", "en"}


def test_idea_protein_values_are_in_the_palette():
    library = json.loads(Path("data/dish_library.json").read_text(encoding="utf-8"))["categories"]
    for slug, entry in library.items():
        assert entry.get("idea_protein") in PALETTE, slug
    assert library["naan"]["idea"] is False
    assert library["raita-chutney"]["idea"] is False
    assert library["salmon"]["idea_protein"] == "fish"
    assert library["yakitori"]["idea_protein"] == "chicken"
    assert library["steak"]["idea_protein"] == "beef"
    assert library["pasta-pesto"]["idea_protein"] == "veg"


def test_idea_slots_are_fixed_and_the_sheet_hides_the_link():
    html = _html()
    assert html.count('class="idea-card"') == 6
    assert "height: 248px" in html
    assert 'id="weekend-ideas"' in html
    assert "Vanligast:" in html and "Usually:" in html
    assert 'dataset.source === "idea"' in html
    assert "ideaLink.hidden = true" in html


def test_reel_slot_is_fixed_and_hidden_from_at():
    html = _html()
    assert 'id="pick-reel" aria-hidden="true"' in html
    assert "width: 128px" in html and "height: 128px" in html
    assert "width: 160px" in html and "height: 160px" in html
    assert ".reel-notch" in html and "#c8ff36" in html
    assert "function spinReel(slugs, target)" in html
    assert "height: 20px" in html
    assert "-webkit-line-clamp: 2" in html
