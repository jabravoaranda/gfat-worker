from __future__ import annotations

import pytest

from tasks.lidar import parse_time_interval


def test_parse_time_interval_accepts_hour_minute():
    start, end = parse_time_interval("00:30", "01:30")

    assert start.hour == 0
    assert start.minute == 30
    assert start.second == 0
    assert end.hour == 1
    assert end.minute == 30
    assert end.second == 0


def test_parse_time_interval_accepts_hour_minute_second():
    start, end = parse_time_interval("00:30:15", "01:30:45")

    assert start.second == 15
    assert end.second == 45


def test_parse_time_interval_rejects_invalid_value():
    with pytest.raises(ValueError):
        parse_time_interval("bad", "01:30")

