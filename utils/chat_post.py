"""Post today's lunch menus to Slack and Teams incoming webhooks.

The scheduled path is `.github/workflows/post-chat.yml`. Guards and payloads
are pure so tests can pass a clock and a fake poster. Importing this module
does not read ``CHAT_WEBHOOKS`` and does not open a socket.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from generate_html import SITE, SV_DAY_LONG
from utils.holidays import is_holiday
from utils.restaurants import display_name
from utils.sources import is_inactive, is_link_only, load_sources

logger = logging.getLogger(__name__)

STOCKHOLM = ZoneInfo("Europe/Stockholm")
ENGLISH_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]
SV_MONTHS = [
    "januari",
    "februari",
    "mars",
    "april",
    "maj",
    "juni",
    "juli",
    "augusti",
    "september",
    "oktober",
    "november",
    "december",
]
FOOTER = "För att stoppa de här inläggen, ta bort webhooken. [Jay's contact]"
LIME = "#c8ff36"
MAX_NAME = 80
MAX_RESTAURANTS = 12
STATE_KEEP_DAYS = 14
WORKFLOW_NAME = "Post lunch to chat"
_POST_TIME = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class ConfigError(Exception):
    """CHAT_WEBHOOKS cannot be used. The message must not contain the secret."""


class TransportError(Exception):
    """HTTP failed before a status code. ``status`` is ``timeout`` or ``error``."""

    def __init__(self, status: str):
        super().__init__(status)
        self.status = status


@dataclass(frozen=True)
class Target:
    name: str
    kind: str
    url: str
    post_time: str | None


@dataclass(frozen=True)
class RestaurantLine:
    display_name: str
    dishes: list[str]


class _Redactor:
    def __init__(self) -> None:
        self.secret = ""
        self.urls: list[str] = []

    def clean(self, message: str) -> str:
        return redact(message, self.secret, self.urls)


def redact(text: str, secret: str | None, urls: list[str]) -> str:
    """Replace the raw secret and each target URL. Empty strings are left alone."""
    if secret:
        text = text.replace(secret, "***")
    for url in sorted((url for url in urls if url), key=len, reverse=True):
        text = text.replace(url, "***")
    return text


def _log(message: str, redactor: _Redactor | None = None) -> None:
    if redactor is not None:
        message = redactor.clean(message)
    logger.info("%s", message)


def to_stockholm(now: datetime) -> datetime:
    if now.tzinfo is None:
        return now.replace(tzinfo=STOCKHOLM)
    return now.astimezone(STOCKHOLM)


def stockholm_date(value: str | None) -> date | None:
    """Calendar date in Europe/Stockholm. Naive timestamps are Stockholm."""
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=STOCKHOLM)
    return parsed.astimezone(STOCKHOLM).date()


def header_text(now: datetime) -> str:
    local = to_stockholm(now)
    weekday = SV_DAY_LONG[local.weekday()].capitalize()
    month = SV_MONTHS[local.month - 1]
    return f"{weekday} {local.day} {month}"


def truncate_name(name: str) -> str:
    if len(name) <= MAX_NAME:
        return name
    return name[: MAX_NAME - 1] + "…"


def mask_url(url: str) -> str:
    """Keep ``https://`` and the host. Drop the path, query, and port."""
    host = urlparse(url).hostname or ""
    return f"https://{host}/***"


def host_allowed(kind: str, url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    host = parsed.hostname or ""
    if kind == "slack":
        return host == "hooks.slack.com"
    if kind == "teams":
        return host.endswith(".logic.azure.com")
    return False


def parse_targets(raw: str) -> list[Target]:
    """Parse ``CHAT_WEBHOOKS``. Raises ``ConfigError`` with a safe message."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ConfigError("Post failed: CHAT_WEBHOOKS is not valid JSON.") from None
    if not isinstance(data, list):
        raise ConfigError("Post failed: CHAT_WEBHOOKS must be a JSON list.")
    targets: list[Target] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            raise ConfigError("Post failed: CHAT_WEBHOOKS has an invalid target.")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError("Post failed: CHAT_WEBHOOKS has an invalid target.")
        name = name.strip()
        if name in seen:
            raise ConfigError(f"Post failed: duplicate target name {name}.")
        seen.add(name)
        kind = item.get("type")
        kind = kind.strip().lower() if isinstance(kind, str) else ""
        url = item.get("url")
        url = url.strip() if isinstance(url, str) else ""
        post_time = None
        if "post_time" in item and item["post_time"] is not None:
            value = item["post_time"]
            if not isinstance(value, str) or _POST_TIME.fullmatch(value) is None:
                raise ConfigError(f"Post failed: bad post_time for {name}.")
            post_time = value
        targets.append(Target(name=name, kind=kind, url=url, post_time=post_time))
    return targets


def _dish_lines(items: list) -> list[str]:
    names: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        name = name.strip()
        if not name:
            continue
        names.append(truncate_name(name))
    if not names:
        return []
    shown = names[:2]
    extra = len(names) - len(shown)
    if extra:
        shown.append(f"och {extra} till")
    return shown


def select_restaurants(
    lunch: dict, sources: dict, today: date
) -> tuple[list[RestaurantLine], bool]:
    """Fresh restaurants for ``today``, sorted by display name, capped at 12."""
    rows: list[RestaurantLine] = []
    if not isinstance(lunch, dict):
        return [], False
    for key, value in lunch.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        if is_inactive(key, sources) or is_link_only(key, sources):
            continue
        items = value.get("items")
        if not isinstance(items, list) or not items:
            continue
        if value.get("stale") is True or value.get("closed") is True:
            continue
        fetched = value.get("fetched_at")
        if stockholm_date(fetched if isinstance(fetched, str) else None) != today:
            continue
        dishes = _dish_lines(items)
        if not dishes:
            continue
        rows.append(RestaurantLine(display_name(key), dishes))
    rows.sort(key=lambda row: row.display_name.casefold())
    overflow = len(rows) > MAX_RESTAURANTS
    return rows[:MAX_RESTAURANTS], overflow


def build_slack_payload(header: str, rows: list[RestaurantLine], overflow: bool) -> dict:
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": header, "emoji": False},
        }
    ]
    for row in rows:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{row.display_name}*\n" + "\n".join(row.dishes),
                },
            }
        )
    if overflow:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Fler menyer på sidan."},
            }
        )
    blocks.append(
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Öppna menyn", "emoji": False},
                    "url": SITE,
                    "action_id": "open_menu",
                }
            ],
        }
    )
    blocks.append(
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": FOOTER}],
        }
    )
    return {
        "text": f"{header} · Lunch på Lindholmen",
        "attachments": [{"color": LIME, "blocks": blocks}],
    }


def build_teams_payload(header: str, rows: list[RestaurantLine], overflow: bool) -> dict:
    body: list[dict] = [
        {
            "type": "TextBlock",
            "text": header,
            "weight": "Bolder",
            "size": "Large",
            "wrap": True,
        },
        {
            "type": "TextBlock",
            "text": "Lunch på Lindholmen",
            "isSubtle": True,
            "wrap": True,
            "spacing": "None",
        },
    ]
    for row in rows:
        body.append(
            {
                "type": "TextBlock",
                "text": row.display_name,
                "weight": "Bolder",
                "wrap": True,
                "spacing": "Medium",
            }
        )
        body.append(
            {
                "type": "TextBlock",
                "text": "\n\n".join(row.dishes),
                "wrap": True,
                "spacing": "None",
            }
        )
    if overflow:
        body.append(
            {
                "type": "TextBlock",
                "text": "Fler menyer på sidan.",
                "wrap": True,
                "spacing": "Medium",
            }
        )
    body.append(
        {
            "type": "TextBlock",
            "text": FOOTER,
            "wrap": True,
            "size": "Small",
            "isSubtle": True,
            "spacing": "Medium",
        }
    )
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": body,
                    "actions": [
                        {"type": "Action.OpenUrl", "title": "Öppna menyn", "url": SITE}
                    ],
                },
            }
        ],
    }


def calendar_skip(now: datetime) -> str | None:
    local = to_stockholm(now)
    if local.weekday() >= 5:
        return "Post skip: weekend."
    if is_holiday(local.date()):
        return "Post skip: holiday."
    return None


def past_cutoff(now: datetime) -> bool:
    local = to_stockholm(now)
    return (local.hour, local.minute) >= (13, 0)


def before_post_time(now: datetime, post_time: str) -> bool:
    hour, minute = (int(part) for part in post_time.split(":"))
    local = to_stockholm(now)
    return (local.hour, local.minute) < (hour, minute)


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def menu_skip(data_dir: Path, now: datetime) -> str | None:
    """Skip line when the weekday meta file is not today's scrape."""
    local = to_stockholm(now)
    weekday = ENGLISH_DAYS[local.weekday()]
    today = local.date().isoformat()
    meta = _read_json(data_dir / f"scrape_meta_{weekday}.json")
    if meta is None:
        return f"Post skip: lunch data is for none, not {today}."
    scraped = stockholm_date(meta.get("scraped_at") if isinstance(meta.get("scraped_at"), str) else None)
    if meta.get("day") != weekday or scraped != local.date():
        label = scraped.isoformat() if scraped is not None else "none"
        return f"Post skip: lunch data is for {label}, not {today}."
    return None


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "days": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "days": {}}
    days = data.get("days") if isinstance(data, dict) else None
    if not isinstance(days, dict):
        days = {}
    clean = {
        key: value
        for key, value in days.items()
        if isinstance(key, str) and isinstance(value, dict)
    }
    return {"version": 1, "days": clean}


def prune_state(state: dict, today: date) -> dict:
    kept = {}
    for key, value in state.get("days", {}).items():
        try:
            parsed = date.fromisoformat(key)
        except ValueError:
            continue
        if (today - parsed).days <= STATE_KEEP_DAYS:
            kept[key] = value
    return {"version": 1, "days": kept}


def already_posted(state: dict, today: date, name: str) -> bool:
    day_state = state.get("days", {}).get(today.isoformat(), {})
    if not isinstance(day_state, dict):
        return False
    entry = day_state.get(name)
    return isinstance(entry, dict) and entry.get("status") == "ok"


def record_success(state: dict, today: date, name: str, posted_at: str) -> dict:
    pruned = prune_state(state, today)
    day_key = today.isoformat()
    day_state = dict(pruned["days"].get(day_key) or {})
    day_state[name] = {"posted_at": posted_at, "status": "ok"}
    days = dict(pruned["days"])
    days[day_key] = day_state
    return {"version": 1, "days": days}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "days": state.get("days") or {}}
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def format_posted_at(now: datetime) -> str:
    local = to_stockholm(now).replace(second=0, microsecond=0)
    return local.isoformat(timespec="minutes")


def _failure_label(exc: BaseException) -> str:
    try:
        import requests
    except ImportError:
        return "error"
    if isinstance(exc, requests.Timeout):
        return "timeout"
    return "error"


def _silence_http_loggers() -> list[tuple[logging.Logger, int]]:
    previous = []
    for name in ("urllib3", "urllib3.connectionpool", "requests"):
        item = logging.getLogger(name)
        previous.append((item, item.level))
        item.setLevel(logging.CRITICAL)
    return previous


def _restore_http_loggers(previous: list[tuple[logging.Logger, int]]) -> None:
    for item, level in previous:
        item.setLevel(level)


def deliver(target: Target, payload: dict, secret: str) -> int:
    """POST one payload. Raises ``TransportError`` without the webhook URL."""
    import requests

    previous = _silence_http_loggers()
    try:
        try:
            response = requests.post(
                target.url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
        except requests.Timeout:
            raise TransportError("timeout") from None
        except requests.RequestException as exc:
            redact(str(exc), secret, [target.url])
            raise TransportError("error") from None
        return int(response.status_code)
    finally:
        _restore_http_loggers(previous)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def commit_state(state_path: Path, day: date) -> bool:
    """Commit and push the state file on main. Never force-pushes.

    Outside the post workflow this is a no-op success: the file is already
    written, and tests must not push.
    """
    if os.environ.get("GITHUB_WORKFLOW") != WORKFLOW_NAME:
        return True
    repo = Path.cwd()
    head = _git(["rev-parse", "--abbrev-ref", "HEAD"], repo)
    if head.returncode != 0 or head.stdout.strip() != "main":
        return False
    _git(["config", "--local", "user.email", "action@github.com"], repo)
    _git(["config", "--local", "user.name", "GitHub Action"], repo)
    rel = os.path.relpath(state_path, repo)
    if _git(["add", "--", rel], repo).returncode != 0:
        return False
    staged = _git(["diff", "--staged", "--quiet", "--", rel], repo)
    if staged.returncode == 0:
        return True
    if staged.returncode != 1:
        return False
    message = f"Chat post state: {day.isoformat()}"
    if _git(["commit", "-m", message], repo).returncode != 0:
        return False
    for _attempt in range(3):
        pulled = _git(["pull", "--rebase", "origin", "main"], repo)
        if pulled.returncode != 0:
            _git(["rebase", "--abort"], repo)
            return False
        pushed = _git(["push", "origin", "main"], repo)
        if pushed.returncode == 0:
            return True
    return False


def run(
    now: datetime,
    env: Mapping[str, str],
    data_dir: Path,
    state_path: Path,
    poster: Callable[[Target, dict], int],
    committer: Callable[[date], bool] | None = None,
) -> int:
    """Apply the guards and post. ``poster`` performs the HTTP call."""
    data_dir = Path(data_dir)
    state_path = Path(state_path)
    redactor = _Redactor()

    raw = env.get("CHAT_WEBHOOKS")
    if raw is None or not str(raw).strip():
        _log("Post skip: CHAT_WEBHOOKS is not set.")
        return 0
    raw = str(raw)
    redactor.secret = raw
    try:
        targets = parse_targets(raw)
    except ConfigError as exc:
        _log(str(exc), redactor)
        return 1
    redactor.urls = [target.url for target in targets]

    only = str(env.get("CHAT_ONLY") or "").strip()
    if only:
        targets = [target for target in targets if target.name == only]
        if not targets:
            _log(f"Post skip: no target named {only}.", redactor)
            return 1

    skip = calendar_skip(now)
    if skip:
        _log(skip, redactor)
        return 0

    ready: list[Target] = []
    for target in targets:
        if target.post_time and before_post_time(now, target.post_time):
            _log(f"Post skip: before post time for {target.name}.", redactor)
            continue
        ready.append(target)
    if not ready:
        return 0

    if past_cutoff(now):
        _log("Post skip: past the 13:00 Europe/Stockholm cutoff.", redactor)
        return 0

    problem = menu_skip(data_dir, now)
    if problem:
        _log(problem, redactor)
        return 0

    local = to_stockholm(now)
    weekday = ENGLISH_DAYS[local.weekday()]
    lunch = _read_json(data_dir / f"lunch_data_{weekday}.json") or {}
    sources = load_sources(data_dir / "sources.json")
    rows, overflow = select_restaurants(lunch, sources, local.date())
    if not rows:
        _log("Post skip: no fresh menus for today.", redactor)
        return 0

    header = header_text(now)
    payloads = {
        "slack": build_slack_payload(header, rows, overflow),
        "teams": build_teams_payload(header, rows, overflow),
    }
    dry_run = str(env.get("CHAT_DRY_RUN") or "").strip().lower() == "true"
    today = local.date()
    posted: list[str] = []
    failed = False

    for target in ready:
        if target.kind not in {"slack", "teams"}:
            _log(f"Post skip: unknown type for {target.name}.", redactor)
            continue
        if not host_allowed(target.kind, target.url):
            _log(
                f"Post skip: refused host for {target.name} {mask_url(target.url)}.",
                redactor,
            )
            continue
        if already_posted(load_state(state_path), today, target.name):
            _log(f"Post skip: already posted {target.name}.", redactor)
            continue
        payload = payloads[target.kind]
        if dry_run:
            _log(
                f"Post dry-run: {target.name} {target.kind} {mask_url(target.url)}",
                redactor,
            )
            _log(json.dumps(payload, ensure_ascii=False, indent=2), redactor)
            continue
        try:
            status = poster(target, payload)
        except TransportError as exc:
            _log(f"Post failed: {target.name} status={exc.status}", redactor)
            failed = True
            continue
        except Exception as exc:
            redact(str(exc), redactor.secret, redactor.urls)
            _log(f"Post failed: {target.name} status={_failure_label(exc)}", redactor)
            failed = True
            continue
        if isinstance(status, int) and 200 <= status < 300:
            _log(f"Post ok: {target.name}", redactor)
            posted.append(target.name)
        else:
            code = status if isinstance(status, int) else "error"
            _log(f"Post failed: {target.name} status={code}", redactor)
            failed = True

    if posted:
        state = load_state(state_path)
        posted_at = format_posted_at(now)
        for name in posted:
            state = record_success(state, today, name, posted_at)
        save_state(state_path, state)
        if committer is not None and not committer(today):
            for name in posted:
                _log(f"Post failed: {name} posted but state was not saved.", redactor)
            return 1
    if failed:
        return 1
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    data_dir = Path("data")
    state_path = data_dir / "chat_post_state.json"
    secret = os.environ.get("CHAT_WEBHOOKS") or ""

    def poster(target: Target, payload: dict) -> int:
        return deliver(target, payload, secret)

    def committer(day: date) -> bool:
        return commit_state(state_path, day)

    return run(
        datetime.now(STOCKHOLM),
        os.environ,
        data_dir,
        state_path,
        poster,
        committer=committer,
    )


if __name__ == "__main__":
    raise SystemExit(main())
