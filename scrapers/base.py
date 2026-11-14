from abc import ABC, abstractmethod
import os
import re
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

BOT_UA = "LindholmenLunchBot/1.0 (+https://iamjaydesign.com/lindholmen-lunch/)"

_session = requests.Session()
_session.headers.update({
    "User-Agent": BOT_UA,
    "Accept-Language": "sv-SE,sv;q=0.9",
})

_robots_cache: dict[str, RobotFileParser] = {}
_delayed_hosts: set[str] = set()
_WEEK_RE = re.compile(r"(?<![a-zåäö])(?:vecka|v)\.?\s*(\d{1,2})\b", re.IGNORECASE)


class RobotsDisallowed(Exception):
    """The site's robots.txt disallows this URL for our bot."""


def find_week(text: str) -> int | None:
    match = _WEEK_RE.search(text or "")
    if not match:
        return None
    return int(match.group(1))


def _robots_for(url: str) -> RobotFileParser:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    cached = _robots_cache.get(origin)
    if cached is not None:
        return cached
    parser = RobotFileParser()
    try:
        response = _session.get(origin + "/robots.txt", timeout=(3, 8))
        if response.status_code >= 400:
            parser.parse([])
        else:
            parser.parse(response.text.splitlines())
    except requests.RequestException:
        parser.parse([])
    _robots_cache[origin] = parser
    return parser


def fetch_html(url, *, timeout=(5, 20), headers=None) -> str:
    """GET a page with a shared session. Raises on timeout, HTTP errors and robots.txt."""
    parser = _robots_for(url)
    if not parser.can_fetch(BOT_UA, url):
        raise RobotsDisallowed(url)
    delay = parser.crawl_delay(BOT_UA) or parser.crawl_delay("*")
    host = urlparse(url).netloc
    if delay and host not in _delayed_hosts:
        time.sleep(min(float(delay), 30))
        _delayed_hosts.add(host)
    kwargs = {"timeout": timeout}
    if headers:
        kwargs["headers"] = headers
    response = _session.get(url, **kwargs)
    response.raise_for_status()
    return response.text

def get_chrome_options(enable_javascript=True, load_images=False):
    """
    Get optimal Chrome options for CI/headless environments.
    This ensures consistent configuration across all scrapers.
    
    Args:
        enable_javascript (bool): Whether to enable JavaScript (default: True)
        load_images (bool): Whether to load images (default: False for performance)
    
    Returns:
        Chrome options object if selenium is available, None otherwise
    """
    try:
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        
        # Essential headless options
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Additional stability options for CI
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        # Conditional options
        if not load_images:
            chrome_options.add_argument("--disable-images")
        
        if not enable_javascript:
            chrome_options.add_argument("--disable-javascript")
        
        # Set window size for consistency
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # User agent to appear more like a real browser
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Linux; Ubuntu) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        
        # Memory and performance options
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        
        # Set binary path if available from environment
        chrome_bin = os.environ.get('CHROME_BIN')
        if chrome_bin:
            chrome_options.binary_location = chrome_bin
            
        return chrome_options
    except ImportError:
        # Return None if selenium is not available
        return None

class MenuItem:
    def __init__(
        self,
        name: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[str] = None
    ):
        self.name = name.strip()
        self.category = category.strip() if category else None
        self.description = description.strip() if description else None
        self.price = price.strip() if price else None

    def __repr__(self):
        return (
            f"MenuItem(name={self.name!r}, category={self.category!r}, "
            f"description={self.description!r}, price={self.price!r})"
        )

    def __str__(self):
        if self.price:
            return f"{self.name} – {self.price} - {self.description}"
        elif self.description:
            return f"{self.name} - {self.description}"
        return self.name

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price": self.price
        }

class DailyMenu:
    def __init__(self, day: str, items: List[MenuItem], source_week: int | None = None):
        self.day = day.lower()  # e.g. "monday", "tuesday"
        self.items = items
        self.source_week = source_week

    def __repr__(self):
        return f"DailyMenu(day={self.day!r}, items={self.items!r})"

class LunchScraper(ABC):
    @abstractmethod
    def fetch(self) -> None:
        """Fetch and parse the menu data. Must be called before accessing menu."""
        pass

    @abstractmethod
    def get_menu_for_day(self, day: str) -> Optional[DailyMenu]:
        """Return the menu for the given day (e.g., 'monday')."""
        pass

    # Optional override – not abstract
    def get_all_menus(self) -> Dict[str, DailyMenu]:
        """Return a dictionary of all parsed menus by day (default: empty)."""
        return {}

