from pathlib import Path

from generate_html import generate_index_page


def test_friday_page_uses_scrape_time_not_render_time():
    generate_index_page(day="friday")
    html = Path("docs/index.html").read_text(encoding="utf-8")
    assert 'data-menu-date="2026-11-13"' in html
    assert "16:13" in html
    assert "Visa alla 25 rätter" in html
    assert "9" in html and "av" in html and "15" in html
    assert "6" in html and "saknas" in html
    assert "Kooperativet" in html
    assert "googletagmanager.com" not in html
    assert "googlesyndication.com" not in html
    assert "fonts.googleapis.com" not in html
    assert "adsbygoogle" not in html
    lowered = html.lower()
    assert "fawenah@gmail.com" not in lowered
