from datetime import datetime, timedelta, timezone

import pytest

from scoring import mean_in_window, night_window, tonight_score

PST = timezone(timedelta(hours=-8))


# ---- tonight_score ----

def test_perfect_night_scores_100():
    assert tonight_score(1.0, 0, 0, 0.0, 0.0) == 100


def test_overcast_night_scores_zero():
    assert tonight_score(1.0, 100, 50, 0.0, 0.0) == 0


def test_cloudy_night_scores_near_zero():
    assert tonight_score(0.9, 98, 40, 0.0, 0.0) <= 2


def test_full_moon_overhead_scores_lower_than_new_moon():
    full = tonight_score(0.9, 10, 40, 1.0, 1.0)
    new = tonight_score(0.9, 10, 40, 0.0, 1.0)
    assert full < new


def test_moon_below_horizon_has_no_penalty():
    assert tonight_score(0.9, 10, 40, 1.0, 0.0) == tonight_score(0.9, 10, 40, 0.0, 0.0)


def test_darker_site_scores_higher():
    assert tonight_score(0.9, 20, 40, 0.3, 0.5) > tonight_score(0.2, 20, 40, 0.3, 0.5)


def test_humid_night_scores_lower_than_dry_night():
    assert tonight_score(0.9, 20, 90, 0.3, 0.5) < tonight_score(0.9, 20, 10, 0.3, 0.5)


def test_full_humidity_costs_30_percent():
    assert tonight_score(1.0, 0, 100, 0.0, 0.0) == 70


def test_out_of_range_inputs_stay_between_0_and_100():
    assert 0 <= tonight_score(1.5, -20, -5, -1.0, -1.0) <= 100
    assert 0 <= tonight_score(-1.0, 150, 120, 2.0, 2.0) <= 100


# ---- night_window ----

def test_afternoon_scores_the_coming_night():
    start, end = night_window(datetime(2026, 11, 11, 14, 0, tzinfo=PST))
    assert start == datetime(2026, 11, 11, 21, 0, tzinfo=PST)
    assert end == datetime(2026, 11, 12, 3, 0, tzinfo=PST)


def test_late_evening_is_inside_tonights_window():
    start, end = night_window(datetime(2026, 11, 11, 23, 0, tzinfo=PST))
    assert start == datetime(2026, 11, 11, 21, 0, tzinfo=PST)
    assert end == datetime(2026, 11, 12, 3, 0, tzinfo=PST)


def test_after_midnight_still_belongs_to_the_previous_evening():
    start, end = night_window(datetime(2026, 11, 12, 1, 30, tzinfo=PST))
    assert start == datetime(2026, 11, 11, 21, 0, tzinfo=PST)
    assert end == datetime(2026, 11, 12, 3, 0, tzinfo=PST)


def test_after_3am_switches_to_the_coming_night():
    start, _ = night_window(datetime(2026, 11, 12, 3, 0, tzinfo=PST))
    assert start == datetime(2026, 11, 12, 21, 0, tzinfo=PST)


# ---- mean_in_window ----

START = datetime(2026, 11, 11, 21, 0, tzinfo=PST)
END = START + timedelta(hours=6)


def test_mean_uses_only_hours_inside_the_window():
    times = ["2026-11-11T20:00", "2026-11-11T21:00", "2026-11-12T02:00", "2026-11-12T03:00"]
    values = [100, 10, 30, 100]
    assert mean_in_window(times, values, START, END) == 20


def test_mean_skips_missing_values():
    times = ["2026-11-11T21:00", "2026-11-11T22:00", "2026-11-11T23:00"]
    assert mean_in_window(times, [None, 10, 30], START, END) == 20


def test_mean_raises_when_no_hours_match():
    with pytest.raises(ValueError):
        mean_in_window(["2026-11-10T21:00"], [50], START, END)