"""Headless Chrome smoke for the pick dock and the weekend first paint.

Served over http so fonts and the manifest are same-origin. file:// would log
SEVERE CORS errors that are not product bugs.
"""

import shutil
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

pytestmark = pytest.mark.browser

DOCS = Path(__file__).resolve().parents[1] / "docs"
WEEKDAY = "/?asof=2026-11-13T11:20"
WEEKEND = "/?asof=2026-11-14T10:00"


def _chrome_binary():
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    return None


class _QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS), **kwargs)

    def log_message(self, fmt, *args):
        return


@pytest.fixture(scope="module")
def page():
    binary = _chrome_binary()
    if not binary:
        pytest.skip("Chrome is not installed")
    selenium = pytest.importorskip("selenium")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    server = ThreadingHTTPServer(("127.0.0.1", 0), _QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    options = Options()
    options.binary_location = binary
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {"width": 375, "height": 667, "deviceScaleFactor": 1, "mobile": True},
    )
    host = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        yield driver, host
    finally:
        driver.quit()
        server.shutdown()


def _severe(driver):
    entries = driver.get_log("browser")
    return [entry for entry in entries if entry.get("level") == "SEVERE"]


def _eligible_count(driver):
    return driver.execute_script(
        """
        var count = 0;
        document.querySelectorAll("article.restaurant").forEach(function (card) {
            if (card.hidden) return;
            var ok = Array.prototype.some.call(card.querySelectorAll("li.menu-item"), function (item) {
                return item.dataset.match !== "false" && (item.dataset.name || "").trim();
            });
            if (ok) count += 1;
        });
        return count;
        """
    )


def test_weekend_class_is_set_before_the_body_script(page):
    driver, host = page
    driver.get(host + WEEKEND)
    at_body = driver.execute_script("return window.__lunchClassAtBodyStart || ''")
    assert "is-weekend" in at_body
    hidden = driver.execute_script(
        """
        function shown(id) {
            var node = document.getElementById(id);
            return node ? getComputedStyle(node).display : "missing";
        }
        return { menus: shown("menus"), toolbar: shown("toolbar") };
        """
    )
    assert hidden == {"menus": "none", "toolbar": "none"}
    assert _severe(driver) == []


def test_pick_rolls_without_scrolling_and_respects_vego(page):
    driver, host = page
    driver.get(host + WEEKDAY)
    assert driver.current_url.startswith("http://")
    icon = driver.execute_script(
        """
        var svg = document.querySelector(".dish-thumb .dish-ico");
        var use = svg ? svg.querySelector("use") : null;
        var box = svg ? svg.getBoundingClientRect() : null;
        return {
            href: use ? (use.getAttribute("href") || "") : "",
            width: box ? Math.round(box.width) : 0
        };
        """
    )
    assert icon["href"].endswith("#art")
    assert icon["width"] == 48
    driver.execute_script("document.documentElement.style.scrollBehavior = 'auto'")
    start = driver.execute_script("return window.scrollY")
    fab = driver.find_element("id", "pick-fab")
    names = []
    for _ in range(10):
        fab.click()
        names.append(driver.execute_script("return document.getElementById('pick-card-title').textContent"))
        assert driver.execute_script("return window.scrollY") == start
    assert all(names)
    eligible = _eligible_count(driver)
    first = names[: min(eligible, 10)]
    assert len(set(first)) == len(first)

    driver.find_element("css selector", '.filter-chip[data-tag="vego"]').click()
    fab.click()
    tags = driver.execute_script("return document.getElementById('pick-card').dataset.tags || ''").split()
    assert "vego" in tags
    assert driver.execute_script("return window.scrollY") == start
    assert _severe(driver) == []
