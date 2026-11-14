from datetime import datetime
from zoneinfo import ZoneInfo

STOCKHOLM = ZoneInfo("Europe/Stockholm")


def get_today_swedish():
    days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    return days[datetime.now(STOCKHOLM).weekday()]


def get_today_english():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[datetime.now(STOCKHOLM).weekday()]
