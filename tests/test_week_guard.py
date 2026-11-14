from datetime import datetime
from zoneinfo import ZoneInfo

from utils.week_guard import accept_menu

STOCKHOLM = ZoneInfo("Europe/Stockholm")


def test_numbered_week_must_match_the_target_week():
    friday = datetime(2026, 11, 13, 14, 0, tzinfo=STOCKHOLM)
    assert friday.isocalendar().week == 46
    assert accept_menu(47, day="friday", now=friday, week_marker_required=True) == "wrong_week"
    assert accept_menu(46, day="friday", now=friday, week_marker_required=True) == "ok"


def test_friday_afternoon_refuses_a_weekly_page_with_no_week():
    morning = datetime(2026, 11, 13, 12, 0, tzinfo=STOCKHOLM)
    afternoon = datetime(2026, 11, 13, 14, 0, tzinfo=STOCKHOLM)
    assert accept_menu(None, day="friday", now=morning, week_marker_required=True) == "ok"
    assert accept_menu(None, day="friday", now=afternoon, week_marker_required=True) == "wrong_week"


def test_fixed_menu_is_accepted_on_friday_afternoon():
    afternoon = datetime(2026, 11, 13, 14, 0, tzinfo=STOCKHOLM)
    assert accept_menu(None, day="friday", now=afternoon, week_marker_required=False) == "ok"
