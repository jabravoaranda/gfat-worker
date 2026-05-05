from __future__ import annotations

from datetime import date

from scheduled.lidar import yesterday_str


def test_yesterday_handles_month_boundary():
    assert yesterday_str(date(2026, 5, 1)) == "2026-04-30"


def test_yesterday_handles_year_boundary():
    assert yesterday_str(date(2026, 1, 1)) == "2025-12-31"

