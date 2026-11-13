"""Scoring and time-window logic for tonight's stargazing score.

Everything here is plain Python: no internet and no extra packages,
so it is easy to test (see tests/test_scoring.py).
"""
from datetime import datetime, timedelta

DARK_START_HOUR = 21  # the dark window starts at 9 pm local time
DARK_HOURS = 6        # ...and lasts 6 hours (until 3 am)


def night_window(now):
    """Return (start, end) of the dark window to score.

    `now` must be a timezone-aware local datetime. From 3 am to 9 pm we score
    the coming night. Between 9 pm and 3 am we are inside tonight's window,
    so we keep scoring that same window until it ends.
    """
    start = now.replace(hour=DARK_START_HOUR, minute=0, second=0, microsecond=0)
    if now.hour < (DARK_START_HOUR + DARK_HOURS) % 24:
        start -= timedelta(days=1)
    return start, start + timedelta(hours=DARK_HOURS)


def mean_in_window(times, values, start, end):
    """Average the values whose timestamp falls in [start, end).

    `times` are local 'YYYY-MM-DDTHH:MM' strings, as Open-Meteo returns them
    when you ask for a timezone. Missing values (None) are skipped.
    """
    picked = []
    for stamp, value in zip(times, values):
        if value is None:
            continue
        when = datetime.fromisoformat(stamp).replace(tzinfo=start.tzinfo)
        if start <= when < end:
            picked.append(value)
    if not picked:
        raise ValueError("no forecast hours fall inside the night window")
    return sum(picked) / len(picked)


def _clamp(x, low, high):
    return min(max(x, low), high)


def tonight_score(dark, cloud_pct, humidity_pct, moon_illum, moon_up_fraction):
    """Combine everything into one 0-100 score (higher = better night).

    dark             0-1, from the light pollution atlas
    cloud_pct        0-100, average cloud cover during the dark window
    humidity_pct     0-100, average relative humidity (a stand-in for haze)
    moon_illum       0-1, how much of the moon is lit
    moon_up_fraction 0-1, share of the dark window the moon is above the horizon
    """
    dark = _clamp(dark, 0.0, 1.0)
    clear = 1 - _clamp(cloud_pct, 0, 100) / 100
    haze = 1 - 0.3 * (_clamp(humidity_pct, 0, 100) / 100)
    moon = 1 - 0.8 * _clamp(moon_illum, 0.0, 1.0) * _clamp(moon_up_fraction, 0.0, 1.0)
    return round(100 * dark * clear * haze * moon)