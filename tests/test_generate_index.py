from pathlib import Path

from generate_html import dish_pills, generate_index_page, sentence_case_dish, split_price


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
