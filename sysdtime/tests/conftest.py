"""Shared fixtures and test utilities for sysdtime tests."""

from datetime import datetime, timezone

import pytest


@pytest.fixture
def utc_base():
    """Standard UTC reference datetime: 2024-03-15 10:30:45 UTC (Friday)."""
    return datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone.utc)


@pytest.fixture
def utc_midnight():
    """Midnight UTC: 2024-03-15 00:00:00 UTC."""
    return datetime(2024, 3, 15, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def utc_noon():
    """Noon UTC: 2024-03-15 12:00:00 UTC."""
    return datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def monday():
    """Monday: 2024-03-11 10:30:45 UTC."""
    return datetime(2024, 3, 11, 10, 30, 45, tzinfo=timezone.utc)


@pytest.fixture
def tuesday():
    """Tuesday: 2024-03-12 10:30:45 UTC."""
    return datetime(2024, 3, 12, 10, 30, 45, tzinfo=timezone.utc)


@pytest.fixture
def wednesday():
    """Wednesday: 2024-03-13 10:30:45 UTC."""
    return datetime(2024, 3, 13, 10, 30, 45, tzinfo=timezone.utc)


@pytest.fixture
def thursday():
    """Thursday: 2024-03-14 10:30:45 UTC."""
    return datetime(2024, 3, 14, 10, 30, 45, tzinfo=timezone.utc)


@pytest.fixture
def friday():
    """Friday: 2024-03-15 10:30:45 UTC (same as utc_base)."""
    return datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone.utc)


@pytest.fixture
def saturday():
    """Saturday: 2024-03-16 10:30:45 UTC."""
    return datetime(2024, 3, 16, 10, 30, 45, tzinfo=timezone.utc)


@pytest.fixture
def sunday():
    """Sunday: 2024-03-17 10:30:45 UTC."""
    return datetime(2024, 3, 17, 10, 30, 45, tzinfo=timezone.utc)


@pytest.fixture
def leap_day_2024():
    """Leap day 2024: 2024-02-29 12:00:00 UTC."""
    return datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def leap_day_2000():
    """Leap day 2000: 2000-02-29 12:00:00 UTC."""
    return datetime(2000, 2, 29, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def non_leap_year_feb():
    """Non-leap year February: 2023-02-28 12:00:00 UTC."""
    return datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def year_start():
    """Start of year: 2024-01-01 00:00:00 UTC."""
    return datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def year_end():
    """End of year: 2024-12-31 23:59:59 UTC."""
    return datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


@pytest.fixture
def month_start():
    """Start of month: 2024-03-01 00:00:00 UTC."""
    return datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def month_end():
    """End of month: 2024-03-31 23:59:59 UTC."""
    return datetime(2024, 3, 31, 23, 59, 59, tzinfo=timezone.utc)


@pytest.fixture
def last_day_feb_2024():
    """Last day of February 2024: 2024-02-29 12:00:00 UTC."""
    return datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def last_day_feb_2023():
    """Last day of February 2023: 2023-02-28 12:00:00 UTC."""
    return datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def last_day_april_2024():
    """Last day of April 2024: 2024-04-30 12:00:00 UTC."""
    return datetime(2024, 4, 30, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def edge_case_times():
    """Collection of edge case times for testing."""
    return {
        "midnight": datetime(2024, 3, 15, 0, 0, 0, tzinfo=timezone.utc),
        "one_am": datetime(2024, 3, 15, 1, 0, 0, tzinfo=timezone.utc),
        "noon": datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc),
        "one_pm": datetime(2024, 3, 15, 13, 0, 0, tzinfo=timezone.utc),
        "last_second": datetime(2024, 3, 15, 23, 59, 59, tzinfo=timezone.utc),
    }


@pytest.fixture
def weekday_names_idx():
    """Mapping of weekday names to indices (Monday=0, Sunday=6)."""
    return {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
