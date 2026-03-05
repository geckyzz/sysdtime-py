"""Tests for datetime matcher."""

from datetime import datetime, timezone

from sysdtime.matcher import Matcher
from sysdtime.parser import Parser


class TestMatcherBasics:
    """Test basic datetime matching."""

    def test_match_wildcard(self, utc_base):
        """Wildcard should match any datetime."""
        event = Parser("*-*-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True

    def test_match_specific_weekday(self, monday, friday):
        """Should match specific weekday."""
        event = Parser("Mon *-*-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(monday) is True
        assert matcher.matches(friday) is False

    def test_match_weekday_range(self, monday, friday, saturday):
        """Should match weekday range."""
        event = Parser("Mon..Fri *-*-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(monday) is True
        assert matcher.matches(friday) is True
        assert matcher.matches(saturday) is False

    def test_match_multiple_weekdays(self, monday, wednesday, friday, tuesday):
        """Should match multiple specific weekdays."""
        event = Parser("Mon,Wed,Fri *-*-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(monday) is True
        assert matcher.matches(wednesday) is True
        assert matcher.matches(friday) is True
        assert matcher.matches(tuesday) is False

    def test_match_specific_hour(self, utc_base, utc_midnight):
        """Should match specific hour."""
        event = Parser("*-*-* 10:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True
        assert matcher.matches(utc_midnight) is False

    def test_match_specific_minute(self, utc_base):
        """Should match specific minute."""
        event = Parser("*-*-* *:30:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True

    def test_match_specific_second(self, utc_base):
        """Should match specific second."""
        event = Parser("*-*-* *:*:45").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True

    def test_match_full_time(self, utc_base):
        """Should match full time specification."""
        event = Parser("*-*-* 10:30:45").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True

    def test_no_match_different_hour(self, utc_base):
        """Should not match different hour."""
        event = Parser("*-*-* 11:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is False


class TestMatcherDates:
    """Test date matching."""

    def test_match_specific_date(self, utc_base):
        """Should match specific date."""
        event = Parser("*-03-15 *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True

    def test_no_match_different_date(self, utc_base):
        """Should not match different date."""
        event = Parser("*-03-16 *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is False

    def test_match_specific_month(self, utc_base):
        """Should match specific month."""
        event = Parser("*-03-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True

    def test_no_match_different_month(self, utc_base):
        """Should not match different month."""
        event = Parser("*-04-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is False

    def test_match_specific_year(self, utc_base):
        """Should match specific year."""
        event = Parser("2024-*-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True

    def test_no_match_different_year(self, utc_base):
        """Should not match different year."""
        event = Parser("2025-*-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is False

    def test_match_day_range(self, utc_base, month_start):
        """Should match day in range."""
        event = Parser("*-*-01..15 *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True  # 15th
        assert matcher.matches(month_start) is True  # 1st

    def test_no_match_day_outside_range(self, utc_base):
        """Should not match day outside range."""
        event = Parser("*-*-01..14 *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is False  # 15th

    def test_match_day_list(self, month_start, utc_base, month_end):
        """Should match day in list."""
        event = Parser("*-*-01,15,31 *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(month_start) is True  # 1st
        assert matcher.matches(utc_base) is True  # 15th
        assert matcher.matches(month_end) is True  # 31st


class TestMatcherLastDay:
    """Test last day of month matching."""

    def test_match_last_day(self, last_day_feb_2024):
        """Should match last day of month."""
        event = Parser("*-*-~ *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(last_day_feb_2024) is True

    def test_no_match_not_last_day(self):
        """Should not match non-last-day when specified."""
        event = Parser("*-*-01 *:*:*").parse()
        matcher = Matcher(event)
        # Month end (31st) should not match 1st
        month_end = datetime(2024, 3, 31, 12, 0, 0, tzinfo=timezone.utc)
        assert matcher.matches(month_end) is False

    def test_match_last_day_february_leap_year(self, leap_day_2024):
        """Should match Feb 29 in leap year as last day."""
        event = Parser("*-*-~ *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(leap_day_2024) is True

    def test_match_last_day_february_non_leap(self, last_day_feb_2023):
        """Should match Feb 28 in non-leap year as last day."""
        event = Parser("*-*-~ *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(last_day_feb_2023) is True

    def test_match_third_from_last(self):
        """Should match third day from last."""
        event = Parser("*-03~2 *:*:*").parse()
        matcher = Matcher(event)
        # March 31 is last day, 29 is third-to-last (31 - 2 = 29)
        march_29 = datetime(2024, 3, 29, 12, 0, 0, tzinfo=timezone.utc)
        assert matcher.matches(march_29) is True

    def test_no_match_last_day_with_offset_out_of_range(self, last_day_april_2024):
        """Should not match when offset exceeds month days."""
        event = Parser("*-04~35 *:*:*").parse()
        matcher = Matcher(event)
        april_28 = datetime(2024, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        # 35 days from end would be before month start, invalid
        assert matcher.matches(april_28) is False


class TestMatcherRepetition:
    """Test repetition pattern matching."""

    def test_match_hour_repetition(self, utc_base):
        """Should match hour repetition pattern."""
        event = Parser("*-*-* 0/4:*:*").parse()  # Every 4th hour starting from 0
        matcher = Matcher(event)
        dt_0h = datetime(2024, 3, 15, 0, 0, 0, tzinfo=timezone.utc)
        dt_4h = datetime(2024, 3, 15, 4, 0, 0, tzinfo=timezone.utc)
        dt_10h = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert matcher.matches(dt_0h) is True
        assert matcher.matches(dt_4h) is True
        # 10 is not divisible pattern (10 % 4 != 0)
        assert matcher.matches(dt_10h) is False

    def test_match_day_repetition(self, month_start):
        """Should match day repetition pattern."""
        event = Parser("*-*-1/7 *:*:*").parse()  # Every 7 days starting from 1st
        matcher = Matcher(event)
        day_1 = datetime(2024, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
        day_8 = datetime(2024, 3, 8, 12, 0, 0, tzinfo=timezone.utc)
        day_15 = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert matcher.matches(day_1) is True
        assert matcher.matches(day_8) is True
        assert matcher.matches(day_15) is True

    def test_match_minute_repetition(self, utc_base):
        """Should match minute repetition pattern."""
        event = Parser("*-*-* *:0/15:*").parse()  # Every 15th minute starting from 0
        matcher = Matcher(event)
        dt_00 = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        dt_15 = datetime(2024, 3, 15, 10, 15, 0, tzinfo=timezone.utc)
        dt_30 = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert matcher.matches(dt_00) is True
        assert matcher.matches(dt_15) is True
        assert matcher.matches(dt_30) is True

    def test_no_match_outside_repetition(self, utc_base):
        """Should not match outside repetition pattern."""
        event = Parser("*-*-* 0/6:*:*").parse()  # Every 6th hour starting from 0
        matcher = Matcher(event)
        dt_5h = datetime(2024, 3, 15, 5, 0, 0, tzinfo=timezone.utc)
        assert matcher.matches(dt_5h) is False


class TestMatcherCombinations:
    """Test complex matching combinations."""

    def test_match_weekday_and_time(self, monday):
        """Should match when both weekday and time match."""
        event = Parser("Mon 10:30:45").parse()
        monday_1030 = monday  # 10:30:45
        matcher = Matcher(event)
        assert matcher.matches(monday_1030) is True

    def test_no_match_weekday_mismatch(self, tuesday):
        """Should not match when weekday mismatches."""
        event = Parser("Mon 10:30:45").parse()
        matcher = Matcher(event)
        assert matcher.matches(tuesday) is False

    def test_no_match_time_mismatch(self, monday):
        """Should not match when time mismatches."""
        event = Parser("Mon 11:00:00").parse()
        matcher = Matcher(event)
        assert matcher.matches(monday) is False

    def test_match_all_constraints(self, utc_base):
        """Should match when all constraints match."""
        event = Parser("Fri 2024-03-15 10:30:45").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True

    def test_no_match_any_constraint_fails(self, utc_base):
        """Should not match if any single constraint fails."""
        # Same date and time, but wrong weekday
        event = Parser("Mon 2024-03-15 10:30:45").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is False

    def test_match_complex_spec(self, friday):
        """Should match complex specification."""
        event = Parser("Mon..Fri 2024-03-* 09..17:*:00").parse()
        friday_1130 = friday.replace(hour=11, minute=30, second=0)
        matcher = Matcher(event)
        assert matcher.matches(friday_1130) is True

    def test_no_match_complex_spec(self, saturday):
        """Should not match complex spec on wrong day."""
        event = Parser("Mon..Fri 2024-03-* 09..17:*:00").parse()
        matcher = Matcher(event)
        assert matcher.matches(saturday) is False


class TestMatcherEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_match_year_boundary_start(self):
        """Should match at year boundary."""
        event = Parser("2024-*-* *:*:*").parse()
        matcher = Matcher(event)
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert matcher.matches(dt) is True

    def test_match_year_boundary_end(self):
        """Should match at year end."""
        event = Parser("2024-*-* *:*:*").parse()
        matcher = Matcher(event)
        dt = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assert matcher.matches(dt) is True

    def test_match_month_boundary_start(self, month_start):
        """Should match at month start."""
        event = Parser("*-03-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(month_start) is True

    def test_match_month_boundary_end(self, month_end):
        """Should match at month end."""
        event = Parser("*-03-* *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(month_end) is True

    def test_match_day_boundary_midnight(self, utc_midnight):
        """Should match at midnight."""
        event = Parser("*-*-* 00:00:00").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_midnight) is True

    def test_match_day_boundary_end(self):
        """Should match at end of day."""
        event = Parser("*-*-* 23:59:59").parse()
        matcher = Matcher(event)
        dt = datetime(2024, 3, 15, 23, 59, 59, tzinfo=timezone.utc)
        assert matcher.matches(dt) is True

    def test_match_leap_day_february(self, leap_day_2024):
        """Should match leap day in leap year."""
        event = Parser("*-02-29 *:*:*").parse()
        matcher = Matcher(event)
        assert matcher.matches(leap_day_2024) is True

    def test_no_match_february_29_non_leap(self):
        """Should not match Feb 29 in non-leap year."""
        event = Parser("*-02-29 *:*:*").parse()
        matcher = Matcher(event)
        dt = datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
        assert matcher.matches(dt) is False


class TestMatcherWithDifferentTimezones:
    """Test matching with timezone-aware datetimes."""

    def test_match_with_utc(self, utc_base):
        """Should match UTC datetime."""
        event = Parser("*-*-* 10:30:45").parse()
        matcher = Matcher(event)
        assert matcher.matches(utc_base) is True

    def test_match_with_timezone_offset(self):
        """Should match datetime with timezone offset."""
        from datetime import timedelta

        event = Parser("*-*-* 10:30:45").parse()
        matcher = Matcher(event)
        # Same instant as UTC 10:30:45, but in +02:00 timezone
        dt = datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone(timedelta(hours=2)))
        assert matcher.matches(dt) is True
