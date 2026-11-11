"""Week arithmetic. Weeks run Sunday-Saturday, as in CIQ."""
from __future__ import annotations

from datetime import date, timedelta

CUTOVER = date(2026, 11, 1)   # first CIQ timesheet week; earlier weeks are CIQ's synced Harvest copy


def last_full_week(run_date: date) -> date:
    """Sunday that starts the last completed Sun-Sat week before run_date."""
    this_sunday = run_date - timedelta(days=(run_date.weekday() + 1) % 7)
    return this_sunday - timedelta(days=7)


def weeks(run_date: date, trend_weeks: int = 3, week: date | None = None) -> dict:
    wk = week or last_full_week(run_date)
    if wk.weekday() != 6:
        raise ValueError(f"{wk} is not a Sunday")
    trend = [wk - timedelta(days=7 * i) for i in range(trend_weeks, 0, -1)]   # oldest first
    return {
        "week": wk,
        "week_end": wk + timedelta(days=6),
        "trend": trend,
        "from": trend[0],
        "uses_harvest_copy": trend[0] < CUTOVER,
    }
