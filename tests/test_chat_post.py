"""Chat poster. HTTP is mocked. Nothing here is marked network or browser."""

import json
import logging
import subprocess
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import requests

from generate_html import SITE
from utils.chat_post import (
    build_slack_payload,
    build_teams_payload,
    commit_state,
    deliver,
    header_text,
    main,
    mask_url,
    redact,
    run,
    select_restaurants,
    truncate_name,
)

STOCKHOLM = ZoneInfo("Europe/Stockholm")
ROOT = Path(__file__).resolve().parents[1]
SLACK_URL = "https://hooks.slack.com/services/T000/B000/XXXX"
SLACK_URL_2 = "https://hooks.slack.com/services/T000/B000/YYYY"
TEAMS_URL = "https://unit.logic.azure.com/workflows/abc?sig=supersecret"
TODAY = datetime(2026, 11, 25, 8, 15, tzinfo=STOCKHOLM)
FETCHED = "2026-11-25T08:16+01:00"
SCRAPED = "2026-11-25T08:16+01:00"


@pytest.fixture
def logs(caplog):
    caplog.set_level(logging.INFO, logger="utils.chat_post")
    return caplog


def _menu_item(name, **extra):
    item = {
        "name": name,
        "category": "SALLADER",
        "description": "HIDDEN-DESCRIPTION",
        "price": "130 kr",
    }
    item.update(extra)
    return item


def _restaurant(names, fetched=FETCHED, **flags):
    payload = {
        "day": "wednesday",
        "items": [_menu_item(name) for name in names],
        "stale": False,
        "fetched_at": fetched,
        "source_week": "HIDDEN-WEEK",
    }
    payload.update(flags)
    if fetched is None:
        payload.pop("fetched_at", None)
    return payload


def _write_day(data_dir, lunch, scraped_at=SCRAPED, day="wednesday"):
    data_dir.mkdir(parents=True, exist_ok=True)
    meta = {"day": day, "scraped_at": scraped_at}
    (data_dir / f"scrape_meta_{day}.json").write_text(json.dumps(meta), encoding="utf-8")
    (data_dir / f"lunch_data_{day}.json").write_text(json.dumps(lunch), encoding="utf-8")


def _env(targets, **extra):
    env = {"CHAT_WEBHOOKS": json.dumps(targets)}
    env.update(extra)
    return env


def _slack(name="jay-slack", url=SLACK_URL, **extra):
    target = {"name": name, "type": "slack", "url": url}
    target.update(extra)
    return target


def _teams(name="jay-teams", url=TEAMS_URL, **extra):
    target = {"name": name, "type": "teams", "url": url}
    target.update(extra)
    return target


def _sample_rows():
    names = [
        "Caesarsallad",
        "French Style Caramelized Onion and Chili Ramen",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
    ]
    lunch = {"KooperativetScraper": _restaurant(names)}
    rows, overflow = select_restaurants(lunch, {}, date(2026, 11, 25))
    return rows, overflow


def test_import_does_not_read_secret_or_open_a_socket(monkeypatch):
    monkeypatch.setenv("CHAT_WEBHOOKS", "IMPORT-SECRET-VALUE")
    import socket
    import sys

    def connect(self, address):
        raise AssertionError(f"socket connect {address}")

    monkeypatch.setattr(socket.socket, "connect", connect)
    sys.modules.pop("utils.chat_post", None)
    import utils.chat_post as chat_post

    dumped = " ".join(
        str(getattr(chat_post, name))
        for name in dir(chat_post)
        if not name.startswith("_")
    )
    assert "IMPORT-SECRET-VALUE" not in dumped


def test_header_uses_long_swedish_names():
    assert header_text(datetime(2026, 11, 25, 8, 0, tzinfo=STOCKHOLM)) == "Onsdag 25 november"
    assert header_text(datetime(2026, 11, 23, 8, 0, tzinfo=STOCKHOLM)) == "Måndag 23 november"
    assert header_text(datetime(2026, 6, 1, 8, 0, tzinfo=STOCKHOLM)).endswith(" 1 juni")


def test_slack_payload_shape():
    rows, overflow = _sample_rows()
    header = "Onsdag 25 november"
    payload = build_slack_payload(header, rows, overflow)
    blob = json.dumps(payload, ensure_ascii=False)
    section = payload["attachments"][0]["blocks"][1]["text"]["text"]
    button = payload["attachments"][0]["blocks"][2]["elements"][0]

    assert payload["text"] == "Onsdag 25 november · Lunch på Lindholmen"
    assert payload["attachments"][0]["blocks"][0]["text"]["text"] == header
    assert section == (
        "*Kooperativet*\n"
        "Caesarsallad\n"
        "French Style Caramelized Onion and Chili Ramen\n"
        "och 6 till"
    )
    assert button["url"] == SITE
    assert button["text"]["text"] == "Öppna menyn"
    assert "style" not in button
    assert blob.count("#c8ff36") == 1
    assert payload["attachments"][0]["color"] == "#c8ff36"
    assert "hooks.slack.com" not in blob
    assert "logic.azure.com" not in blob
    assert "HIDDEN-DESCRIPTION" not in blob
    assert "130 kr" not in blob
    assert "HIDDEN-WEEK" not in blob
    assert "SALLADER" not in blob
    assert "[Jay's contact]" in blob


def test_teams_payload_shape():
    rows, overflow = _sample_rows()
    payload = build_teams_payload("Onsdag 25 november", rows, overflow)
    attachment = payload["attachments"][0]
    content = attachment["content"]
    blob = json.dumps(payload, ensure_ascii=False)
    actions = [item for item in content["actions"] if item["type"] == "Action.OpenUrl"]

    assert payload["type"] == "message"
    assert attachment["contentType"] == "application/vnd.microsoft.card.adaptive"
    assert content["version"] == "1.2"
    assert len(actions) == 1
    assert actions[0]["url"] == SITE
    assert actions[0]["title"] == "Öppna menyn"
    assert "Action.Submit" not in blob
    assert "#c8ff36" not in blob
    assert "hooks.slack.com" not in blob
    assert content["body"][2]["text"] == "Kooperativet"
    assert content["body"][3]["text"] == (
        "Caesarsallad\n\n"
        "French Style Caramelized Onion and Chili Ramen\n\n"
        "och 6 till"
    )
    assert "[Jay's contact]" in blob


def test_truncation_and_restaurant_cap():
    assert truncate_name("A" * 80) == "A" * 80
    assert truncate_name("B" * 81) == "B" * 79 + "…"
    assert len(truncate_name("C" * 81)) == 80

    lunch = {}
    for number in range(1, 14):
        names = ["N" * 81, "Second", "Third"] if number == 1 else ["Soup"]
        lunch[f"R{number:02d}"] = _restaurant(names)
    rows, overflow = select_restaurants(lunch, {}, date(2026, 11, 25))
    payload = build_slack_payload("Onsdag 25 november", rows, overflow)
    blob = json.dumps(payload, ensure_ascii=False)

    assert overflow is True
    assert len(rows) == 12
    assert rows[0].display_name == "R01"
    assert rows[0].dishes[0] == "N" * 79 + "…"
    assert rows[0].dishes[-1] == "och 1 till"
    assert "Fler menyer på sidan." in blob
    assert "R13" not in blob


def test_sorts_display_names_with_casefold():
    lunch = {
        "beta": _restaurant(["Soup"]),
        "Alpha": _restaurant(["Salad"]),
    }
    rows, overflow = select_restaurants(lunch, {}, date(2026, 11, 25))
    assert [row.display_name for row in rows] == ["Alpha", "beta"]
    assert overflow is False


def test_mask_url_drops_path_query_and_port():
    masked = mask_url(TEAMS_URL)
    assert mask_url(SLACK_URL) == "https://hooks.slack.com/***"
    assert masked == "https://unit.logic.azure.com/***"
    assert mask_url("https://hooks.slack.com:443/services/T000/B000/XXXX") == (
        "https://hooks.slack.com/***"
    )
    assert "sig=" not in masked
    assert "workflows" not in masked


def test_yesterdays_scrape_skips_without_posting(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(
        data,
        {"KooperativetScraper": _restaurant(["Caesarsallad"])},
        scraped_at="2026-11-24T08:16+01:00",
    )
    calls = []

    def poster(target, payload):
        calls.append(target.name)
        return 200

    code = run(TODAY, _env([_slack()]), data, tmp_path / "state.json", poster)
    assert code == 0
    assert calls == []
    assert "Post skip: lunch data is for 2026-11-24, not 2026-11-25." in logs.text


def test_freshness_filters(tmp_path, logs):
    data = tmp_path / "data"
    lunch = {
        "KooperativetScraper": _restaurant(["Caesarsallad"], fetched="2026-11-25T08:16"),
        "BombayBistroScraper": _restaurant(["Stale Dish"], stale=True),
        "DistrictOneScraper": _restaurant(["Old Dish"], fetched="2026-11-24T08:16+01:00"),
        "CuckoosNestScraper": _restaurant(["Closed Dish"], closed=True),
        "MissFScraper": _restaurant(["No Stamp"], fetched=None),
        "MatMinnenScraper": _restaurant(["Inactive Dish"]),
        "MimolettScraper": _restaurant(["Link Dish"]),
        "OishiiScraper": _restaurant(["", "Kept Dish"]),
    }
    _write_day(data, lunch)
    (data / "sources.json").write_text(
        json.dumps(
            {
                "MatMinnenScraper": {"active": False},
                "MimolettScraper": {"active": True, "link_only": True},
            }
        ),
        encoding="utf-8",
    )
    calls = []

    def poster(target, payload):
        calls.append(payload)
        return 200

    code = run(TODAY, _env([_slack()]), data, tmp_path / "state.json", poster)
    assert code == 0
    assert len(calls) == 1
    blob = json.dumps(calls[0], ensure_ascii=False)
    assert "Caesarsallad" in blob
    assert "Kept Dish" in blob
    for banned in (
        "Stale Dish",
        "Old Dish",
        "Closed Dish",
        "No Stamp",
        "Inactive Dish",
        "Link Dish",
        "HIDDEN-DESCRIPTION",
    ):
        assert banned not in blob


def test_weekend_skips(tmp_path, logs):
    calls = []
    saturday = datetime(2026, 11, 28, 9, 0, tzinfo=STOCKHOLM)
    code = run(saturday, _env([_slack()]), tmp_path, tmp_path / "state.json", lambda t, p: calls.append(t) or 200)
    assert code == 0
    assert calls == []
    assert "Post skip: weekend." in logs.text
    assert not (tmp_path / "state.json").exists()


@pytest.mark.parametrize(
    "day",
    [
        "2026-01-01",  # public, Thursday
        "2026-01-02",  # bridge, Friday
        "2026-06-19",  # eve, Friday
    ],
)
def test_holidays_skip(day, tmp_path, logs):
    when = datetime.fromisoformat(f"{day}T09:00:00").replace(tzinfo=STOCKHOLM)
    calls = []
    code = run(when, _env([_slack()]), tmp_path, tmp_path / "state.json", lambda t, p: calls.append(t) or 200)
    assert code == 0
    assert calls == []
    assert "Post skip: holiday." in logs.text
    assert "weekend" not in logs.text


def test_cutoff_skips_without_recording_state(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["UNIQUE-DISH"])})
    state = tmp_path / "state.json"
    calls = []

    def poster(target, payload):
        calls.append(target.name)
        return 200

    late = datetime(2026, 11, 25, 13, 0, tzinfo=STOCKHOLM)
    assert run(late, _env([_slack()]), data, state, poster) == 0
    assert calls == []
    assert "Post skip: past the 13:00 Europe/Stockholm cutoff." in logs.text
    assert not state.exists()

    logs.clear()
    early = datetime(2026, 11, 25, 12, 59, tzinfo=STOCKHOLM)
    assert run(early, _env([_slack()]), data, state, poster) == 0
    assert calls == ["jay-slack"]


def test_post_time_floor_and_omitted_post_time(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    state = tmp_path / "state.json"
    calls = []

    def poster(target, payload):
        calls.append(target.name)
        return 200

    targets = [
        _slack("later", SLACK_URL, post_time="09:15"),
        _slack("early", SLACK_URL_2),
    ]
    env = _env(targets)

    assert run(datetime(2026, 11, 25, 8, 15, tzinfo=STOCKHOLM), env, data, state, poster) == 0
    assert calls == ["early"]
    assert "Post skip: before post time for later." in logs.text

    calls.clear()
    logs.clear()
    assert run(datetime(2026, 11, 25, 9, 0, tzinfo=STOCKHOLM), env, data, state, poster) == 0
    assert calls == []
    assert "Post skip: before post time for later." in logs.text
    assert "Post skip: already posted early." in logs.text

    calls.clear()
    assert run(datetime(2026, 11, 25, 9, 15, tzinfo=STOCKHOLM), env, data, state, poster) == 0
    assert calls == ["later"]


def test_second_run_does_not_call_the_poster(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    state = tmp_path / "state.json"
    calls = []
    now = datetime(2026, 11, 25, 8, 21, 45, tzinfo=STOCKHOLM)

    def poster(target, payload):
        calls.append(target.name)
        return 204

    assert run(now, _env([_slack()]), data, state, poster) == 0
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["days"]["2026-11-25"]["jay-slack"] == {
        "posted_at": "2026-11-25T08:21+01:00",
        "status": "ok",
    }
    assert run(now, _env([_slack()]), data, state, poster) == 0
    assert calls == ["jay-slack"]
    assert "Post skip: already posted jay-slack." in logs.text


def test_non_2xx_does_not_write_state(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    state = tmp_path / "state.json"
    original = '{"version":1,"days":{},"sentinel":true}\n'
    state.write_text(original, encoding="utf-8")

    def poster(target, payload):
        return 500

    assert run(TODAY, _env([_slack()]), data, state, poster) == 1
    assert state.read_text(encoding="utf-8") == original
    assert "Post failed: jay-slack status=500" in logs.text


def test_partial_failure_retries_only_the_failure(tmp_path):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    state = tmp_path / "state.json"
    calls = []
    failed = {"teams": True}

    def poster(target, payload):
        calls.append(target.name)
        if target.name == "jay-teams" and failed["teams"]:
            return 503
        return 200

    env = _env([_slack(), _teams()])
    assert run(TODAY, env, data, state, poster) == 1
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert set(saved["days"]["2026-11-25"]) == {"jay-slack"}
    assert calls == ["jay-slack", "jay-teams"]

    calls.clear()
    failed["teams"] = False
    assert run(TODAY, env, data, state, poster) == 0
    assert calls == ["jay-teams"]
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert set(saved["days"]["2026-11-25"]) == {"jay-slack", "jay-teams"}


def test_only_posts_one_name(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    calls = []

    def poster(target, payload):
        calls.append(target.name)
        return 200

    env = _env([_slack(), _teams()], CHAT_ONLY="jay-slack")
    assert run(TODAY, env, data, tmp_path / "state.json", poster) == 0
    assert calls == ["jay-slack"]


def test_unknown_only_exits_1(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    calls = []
    env = _env([_slack(), _teams()], CHAT_ONLY="nobody")
    assert run(TODAY, env, data, tmp_path / "state.json", lambda t, p: calls.append(t) or 200) == 1
    assert calls == []
    assert "Post skip: no target named nobody." in logs.text


def test_dry_run_prints_masked_payload_and_sends_nothing(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    state = tmp_path / "state.json"
    state.write_text('{"version": 1, "days": {}}\n', encoding="utf-8")
    before = state.read_text(encoding="utf-8")
    calls = []
    env = _env([_slack(), _teams()], CHAT_DRY_RUN="true")

    assert run(TODAY, env, data, state, lambda t, p: calls.append(t) or 200) == 0
    assert calls == []
    assert state.read_text(encoding="utf-8") == before
    assert "Post dry-run: jay-slack slack https://hooks.slack.com/***" in logs.text
    assert "https://unit.logic.azure.com/***" in logs.text
    assert "sig=" not in logs.text
    assert "services/T000" not in logs.text
    assert "workflows/abc" not in logs.text
    assert "supersecret" not in logs.text
    assert "Caesarsallad" in logs.text
    assert SLACK_URL not in logs.text
    assert TEAMS_URL not in logs.text


def test_dry_run_past_cutoff_does_not_print_the_menu(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["UNIQUE-DISH"])})
    calls = []
    env = _env([_slack(url=SLACK_URL)], CHAT_DRY_RUN="true")
    late = datetime(2026, 11, 25, 16, 41, tzinfo=STOCKHOLM)
    assert run(late, env, data, tmp_path / "state.json", lambda t, p: calls.append(t) or 200) == 0
    assert calls == []
    assert "Post skip: past the 13:00 Europe/Stockholm cutoff." in logs.text
    assert "UNIQUE-DISH" not in logs.text
    assert "hooks.slack.com" not in logs.text


def test_invalid_json_exits_1_without_logging_the_secret(monkeypatch, logs):
    raw = '{"oops": "https://hooks.slack.com/services/RAWTOKEN"'
    monkeypatch.setenv("CHAT_WEBHOOKS", raw)
    monkeypatch.delenv("CHAT_ONLY", raising=False)
    monkeypatch.delenv("CHAT_DRY_RUN", raising=False)
    assert main() == 1
    assert raw not in logs.text
    assert "RAWTOKEN" not in logs.text
    assert "Post failed: CHAT_WEBHOOKS is not valid JSON." in logs.text


def test_invalid_target_shape_does_not_log_the_value(tmp_path, logs):
    raw = '["https://hooks.slack.com/services/RAWTOKEN"]'
    assert run(TODAY, {"CHAT_WEBHOOKS": raw}, tmp_path, tmp_path / "state.json", lambda t, p: 200) == 1
    assert "RAWTOKEN" not in logs.text


def test_empty_secret_exits_0(monkeypatch, logs):
    monkeypatch.delenv("CHAT_WEBHOOKS", raising=False)
    monkeypatch.delenv("CHAT_ONLY", raising=False)
    monkeypatch.delenv("CHAT_DRY_RUN", raising=False)
    assert main() == 0
    assert "Post skip: CHAT_WEBHOOKS is not set." in logs.text


def test_blank_secret_exits_0(tmp_path, logs):
    assert run(TODAY, {"CHAT_WEBHOOKS": "   "}, tmp_path, tmp_path / "state.json", lambda t, p: 200) == 0
    assert "Post skip: CHAT_WEBHOOKS is not set." in logs.text


def test_refused_host_does_not_call_the_poster(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    calls = []
    url = "https://evil.example/hook?sig=supersecret"
    env = _env([_slack(url=url)])
    assert run(TODAY, env, data, tmp_path / "state.json", lambda t, p: calls.append(t) or 200) == 0
    assert calls == []
    assert "Post skip: refused host for jay-slack https://evil.example/***." in logs.text
    assert "sig=" not in logs.text
    assert "supersecret" not in logs.text


def test_bad_post_time_exits_1_without_sending(tmp_path, logs):
    calls = []
    env = _env([_slack(post_time="9:15")])
    assert run(TODAY, env, tmp_path, tmp_path / "state.json", lambda t, p: calls.append(t) or 200) == 1
    assert calls == []
    assert "Post failed: bad post_time for jay-slack." in logs.text


def test_redact_replaces_secret_and_urls():
    secret = json.dumps([{"url": TEAMS_URL}])
    cleaned = redact(f"error {TEAMS_URL} and {secret}", secret, [TEAMS_URL])
    assert "sig=" not in cleaned
    assert "supersecret" not in cleaned
    assert TEAMS_URL not in cleaned
    assert secret not in cleaned
    assert "***" in cleaned


def test_requests_error_is_logged_without_sig(tmp_path, logs, monkeypatch):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    secret = json.dumps([_teams()])

    def boom(*args, **kwargs):
        raise requests.RequestException(f"Max retries exceeded with url: {TEAMS_URL}")

    monkeypatch.setattr(requests, "post", boom)

    def poster(target, payload):
        return deliver(target, payload, secret)

    assert run(TODAY, {"CHAT_WEBHOOKS": secret}, data, tmp_path / "state.json", poster) == 1
    assert "Post failed: jay-teams status=error" in logs.text
    assert "sig=" not in logs.text
    assert "supersecret" not in logs.text
    assert TEAMS_URL not in logs.text
    assert not (tmp_path / "state.json").exists()


def test_requests_timeout_is_logged_without_sig(tmp_path, logs, monkeypatch):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    secret = json.dumps([_teams()])
    seen = {}

    def boom(*args, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        seen["headers"] = kwargs.get("headers")
        raise requests.Timeout(f"read timed out {TEAMS_URL}")

    monkeypatch.setattr(requests, "post", boom)

    def poster(target, payload):
        return deliver(target, payload, secret)

    assert run(TODAY, {"CHAT_WEBHOOKS": secret}, data, tmp_path / "state.json", poster) == 1
    assert seen["timeout"] == 15
    assert seen["headers"]["Content-Type"] == "application/json"
    assert "Post failed: jay-teams status=timeout" in logs.text
    assert "sig=" not in logs.text
    assert "supersecret" not in logs.text


def test_failed_state_save_is_logged(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    state = tmp_path / "state.json"

    def committer(day):
        return False

    code = run(TODAY, _env([_slack()]), data, state, lambda t, p: 200, committer=committer)
    assert code == 1
    assert "Post failed: jay-slack posted but state was not saved." in logs.text
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert "jay-slack" in saved["days"]["2026-11-25"]


def test_prune_drops_dates_older_than_14_days(tmp_path):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps(
            {
                "version": 1,
                "days": {
                    "2026-11-10": {"old": {"posted_at": "2026-11-10T08:00+01:00", "status": "ok"}},
                    "2026-11-11": {"keep": {"posted_at": "2026-11-11T08:00+01:00", "status": "ok"}},
                },
            }
        ),
        encoding="utf-8",
    )
    assert run(TODAY, _env([_slack()]), data, state, lambda t, p: 200) == 0
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert "2026-11-10" not in saved["days"]
    assert "2026-11-11" in saved["days"]
    assert "jay-slack" in saved["days"]["2026-11-25"]


def test_nothing_fresh_skips(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"], stale=True)})
    calls = []
    assert run(TODAY, _env([_slack()]), data, tmp_path / "state.json", lambda t, p: calls.append(t) or 200) == 0
    assert calls == []
    assert "Post skip: no fresh menus for today." in logs.text


def test_unknown_type_does_not_send(tmp_path, logs):
    data = tmp_path / "data"
    _write_day(data, {"KooperativetScraper": _restaurant(["Caesarsallad"])})
    calls = []
    target = {"name": "jay-chat", "type": "discord", "url": SLACK_URL}
    assert run(TODAY, _env([target]), data, tmp_path / "state.json", lambda t, p: calls.append(t) or 200) == 0
    assert calls == []
    assert "Post skip: unknown type for jay-chat." in logs.text


class _Result:
    def __init__(self, code, stdout=""):
        self.returncode = code
        self.stdout = stdout
        self.stderr = ""


def test_commit_state_is_a_noop_outside_the_post_workflow(monkeypatch):
    monkeypatch.delenv("GITHUB_WORKFLOW", raising=False)
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: calls.append(args) or _Result(0))
    assert commit_state(Path("data/chat_post_state.json"), date(2026, 11, 25)) is True
    assert calls == []


def test_commit_state_refuses_to_push_when_not_on_main(monkeypatch):
    monkeypatch.setenv("GITHUB_WORKFLOW", "Post lunch to chat")
    calls = []

    def fake(args, **kwargs):
        calls.append(list(args))
        stdout = "feat/daily-chat-posting\n" if "rev-parse" in args else ""
        return _Result(0, stdout)

    monkeypatch.setattr(subprocess, "run", fake)
    assert commit_state(Path("data/chat_post_state.json"), date(2026, 11, 25)) is False
    assert not any("push" in args for args in calls)


def test_commit_state_aborts_failed_rebase_and_never_force_pushes(monkeypatch):
    monkeypatch.setenv("GITHUB_WORKFLOW", "Post lunch to chat")
    calls = []

    def fake(args, **kwargs):
        calls.append(list(args))
        if args[1] == "rev-parse":
            return _Result(0, "main\n")
        if args[1] == "diff":
            return _Result(1)
        if args[1] == "pull":
            return _Result(1)
        return _Result(0)

    monkeypatch.setattr(subprocess, "run", fake)
    assert commit_state(Path("data/chat_post_state.json"), date(2026, 11, 25)) is False
    assert ["git", "rebase", "--abort"] in calls
    assert ["git", "commit", "-m", "Chat post state: 2026-11-25"] in calls
    assert not any("push" in args for args in calls)
    assert not any(arg.startswith("--force") or arg == "-f" for args in calls for arg in args)


def test_commit_state_pushes_main_without_force(monkeypatch):
    monkeypatch.setenv("GITHUB_WORKFLOW", "Post lunch to chat")
    calls = []
    pushes = {"n": 0}

    def fake(args, **kwargs):
        calls.append(list(args))
        if args[1] == "rev-parse":
            return _Result(0, "main\n")
        if args[1] == "diff":
            return _Result(1)
        if args[1] == "push":
            pushes["n"] += 1
            return _Result(0 if pushes["n"] == 3 else 1)
        return _Result(0)

    monkeypatch.setattr(subprocess, "run", fake)
    assert commit_state(Path("data/chat_post_state.json"), date(2026, 11, 25)) is True
    push_calls = [args for args in calls if args[1] == "push"]
    assert push_calls == [["git", "push", "origin", "main"]] * 3
    assert ["git", "config", "--local", "user.email", "action@github.com"] in calls
    assert ["git", "config", "--local", "user.name", "GitHub Action"] in calls
    assert not any(arg.startswith("--force") or arg == "-f" for args in calls for arg in args)


def test_post_workflow_shape():
    text = (ROOT / ".github/workflows/post-chat.yml").read_text(encoding="utf-8")
    assert text.startswith("name: Post lunch to chat\n")
    assert 'workflows: ["Update Lunch Data and Deploy"]' in text
    assert "types: [completed]" in text
    assert "dry_run:" in text
    assert "only:" in text
    assert "contents: write" in text
    assert "lindholmen-lunch-chat" in text
    assert "cancel-in-progress: false" in text
    assert "ref: main" in text
    assert "fetch-depth: 0" in text
    assert "timeout-minutes: 10" in text
    assert "python -m utils.chat_post" in text
    assert "github.event_name == 'workflow_dispatch' || github.event.workflow_run.conclusion == 'success'" in text
    assert "CHAT_DRY_RUN: ${{ github.event.inputs.dry_run || 'false' }}" in text
    assert "CHAT_ONLY: ${{ github.event.inputs.only || '' }}" in text
    assert text.count("secrets.CHAT_WEBHOOKS") == 1
    for line in text.splitlines():
        if "python -m utils.chat_post" in line:
            assert "CHAT_WEBHOOKS" not in line
            assert "secrets." not in line


def test_deploy_workflow_ignores_only_the_state_file_on_push():
    text = (ROOT / ".github/workflows/update-and-deploy.yml").read_text(encoding="utf-8")
    schedule, _, rest = text.partition("push:")
    push, _, after = rest.partition("workflow_dispatch:")
    assert "chat_post_state.json" not in schedule
    assert "paths-ignore:" in push
    assert "data/chat_post_state.json" in push
    assert "chat_post_state.json" not in after
    assert "CHAT_WEBHOOKS" not in text
    assert "utils.chat_post" not in text
    assert "lindholmen-lunch-daily" in text


def test_readme_points_at_the_plan_without_a_webhook_path():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Post lunch to chat" in readme
    assert "13:00" in readme
    assert "CHAT_WEBHOOKS" in readme
    assert "docs/plans/daily-chat-posting.md" in readme
    assert "hooks.slack.com/services/" not in readme
    assert "logic.azure.com" not in readme
