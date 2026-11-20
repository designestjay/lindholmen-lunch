from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import generate_html
from generate_html import dish_pills, generate_index_page, sentence_case_dish, split_price

FIXTURES = Path(__file__).parent / "fixtures"
STOCKHOLM = ZoneInfo("Europe/Stockholm")
PINNED_MENU_DATE = "2026-11-13"
PINNED_SCRAPE_HHMM = "16:13"

# generate_index_page reads these data files and may rewrite these outputs.
_RESTORE = (
    Path("data/lunch_data_friday.json"),
    Path("data/scrape_meta_friday.json"),
    Path("data/image-queue.json"),
    Path("docs/index.html"),
    Path("docs/preview.html"),
    Path("docs/privacy.html"),
    Path("docs/sitemap.xml"),
    Path("privacy.html"),
)


@pytest.fixture
def pinned_friday_menu():
    """Render against a pinned Friday scrape, then put live repo files back."""
    backups = {path: path.read_bytes() for path in _RESTORE if path.exists()}
    Path("data/lunch_data_friday.json").write_bytes(
        (FIXTURES / "friday_page_lunch_data.json").read_bytes()
    )
    Path("data/scrape_meta_friday.json").write_bytes(
        (FIXTURES / "friday_page_scrape_meta.json").read_bytes()
    )
    try:
        yield
    finally:
        for path, payload in backups.items():
            path.write_bytes(payload)


def _freeze_now(monkeypatch, when: datetime) -> None:
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return when.astimezone(tz) if tz is not None else when.replace(tzinfo=None)

    monkeypatch.setattr(generate_html, "datetime", FrozenDateTime)


@pytest.mark.parametrize(
    "render_at",
    [
        datetime(2026, 11, 27, 3, 17, tzinfo=STOCKHOLM),
        datetime(2026, 11, 18, 18, 40, tzinfo=STOCKHOLM),
    ],
    ids=["later-friday", "wednesday"],
)
def test_friday_page_uses_scrape_time_not_render_time(
    pinned_friday_menu, monkeypatch, render_at
):
    """data-menu-date comes from scrape_meta.scraped_at, not the clock at render time."""
    _freeze_now(monkeypatch, render_at)
    generate_index_page(day="friday")
    html = Path("docs/index.html").read_text(encoding="utf-8")
    assert f'data-menu-date="{PINNED_MENU_DATE}"' in html
    assert PINNED_SCRAPE_HHMM in html
    assert f'data-menu-date="{render_at.date().isoformat()}"' not in html
    assert "Visa alla 25 rätter" in html
    assert "9 av" in html or ">9<" in html
    assert ">13<" in html
    assert "4 saknas" in html or ">4<" in html
    assert "Mat &amp; Minnen" not in html and "Mat & Minnen" not in html
    assert "https://mimolett.kvartersmenyn.se/" in html
    assert "Menyn finns på restaurangens sida" in html
    assert "Roterande meny" in html
    assert "placeholder.svg" not in html
    assert html.count('class="dish-thumb"') > 0
    assert html.count('href="assets/dishes/') == html.count('class="dish-thumb"')
    assert 'class="dish-ask"' in html
    assert "Generell beskrivning av rätten" in html
    assert "Stängt idag." in html
    assert "Utkast" in html
    assert "Kooperativet" in html
    assert "googletagmanager.com" not in html
    assert "googlesyndication.com" not in html
    assert "fonts.googleapis.com" not in html
    assert "adsbygoogle" not in html
    lowered = html.lower()
    assert "fawenah@gmail.com" not in lowered
    assert "Murg methi malai" in html
    assert "MURG METHI MALAI" not in html
    assert "119 kr, takeaway" not in html
    assert "takeaway 114 kr" in html
    assert 'class="price-note"' in html
    assert 'src="assets/analytics.js" defer' in html
    assert "text-underline-offset: 3px" in html
    assert ".pick { align-items: center; }" in html
    assert ".menu-item::marker { content: none; }" in html
    assert "is-plain" in html
    pesto = html.find('data-dish-name="Pasta pesto"')
    assert pesto > 0
    row = html[pesto:html.find("</li>", pesto)]
    assert ">Fish<" not in row
    assert ">Chicken<" not in row
    assert ">Pasta<" in row
    assert "Halstrad lax" not in row
    assert "Halstrad lax" in html


def test_pills_use_this_dish_only():
    pills = dish_pills(
        "Pasta pesto",
        "getost, bakade tomater, vitlöksstekta brödsmulor, pesto",
        "Metal",
    )
    assert [pill["en"] for pill in pills] == ["Pasta"]
    sushi = dish_pills("9 bitar nigri", "5 Lax, 4 avokado", "Sushi")
    assert [pill["en"] for pill in sushi] == ["Fish", "Sushi"]


def test_dish_case_and_price_split():
    assert sentence_case_dish("MURG METHI MALAI") == "Murg methi malai"
    assert sentence_case_dish("BBQ WINGS") == "BBQ wings"
    assert sentence_case_dish("IPA") == "IPA"
    assert sentence_case_dish("Fish soup") == "Fish soup"
    assert split_price("119 kr, takeaway 114 kr") == ("119 kr", "takeaway 114 kr")
    assert split_price("119\u00a0kr") == ("119\u00a0kr", "")
