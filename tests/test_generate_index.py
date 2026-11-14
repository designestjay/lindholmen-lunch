from pathlib import Path

from generate_html import generate_index_page, sentence_case_dish, split_price


def test_friday_page_uses_scrape_time_not_render_time():
    generate_index_page(day="friday")
    html = Path("docs/index.html").read_text(encoding="utf-8")
    assert 'data-menu-date="2026-11-13"' in html
    assert "16:13" in html
    assert "Visa alla 25 rätter" in html
    assert "9 av" in html or ">9<" in html
    assert ">13<" in html
    assert "4 saknas" in html or ">4<" in html
    assert "Mat &amp; Minnen" not in html and "Mat & Minnen" not in html
    assert "https://mimolett.kvartersmenyn.se/" in html
    assert "Menyn finns på restaurangens sida" in html
    assert "Roterande meny" in html
    assert "assets/dishes/placeholder.svg" in html
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


def test_dish_case_and_price_split():
    assert sentence_case_dish("MURG METHI MALAI") == "Murg methi malai"
    assert sentence_case_dish("BBQ WINGS") == "BBQ wings"
    assert sentence_case_dish("IPA") == "IPA"
    assert sentence_case_dish("Fish soup") == "Fish soup"
    assert split_price("119 kr, takeaway 114 kr") == ("119 kr", "takeaway 114 kr")
    assert split_price("119\u00a0kr") == ("119\u00a0kr", "")
