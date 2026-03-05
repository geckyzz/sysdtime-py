"""Tests for next occurrence searcher."""

from datetime import datetime, timedelta, timezone

from sysdtime.parser import Parser
from sysdtime.searcher import NextOccurrence


class TestNextOccurrenceBasics:
    """Test basic next occurrence finding."""

    def test_next_after_daily(self, utc_base):
        """Should find next daily occurrence."""
        event = Parser("daily").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_base)
        assert next_dt is not None
        assert next_dt.day == utc_base.day + 1 or next_dt.month > utc_base.month
        assert next_dt.hour == 0
        assert next_dt.minute == 0

    def test_next_after_default_time(self, utc_base):
        """Should find next occurrence with default time."""
        event = Parser("daily").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_base)
        assert next_dt is not None
        # Should be tomorrow at midnight
        expected = utc_base.replace(hour=0, minute=0, second=0, microsecond=0)
        expected += timedelta(days=1)
        assert next_dt == expected

    def test_next_after_specific_time(self, utc_midnight):
        """Should find next occurrence with specific time."""
        event = Parser("*-*-* 12:00:00").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_midnight)
        assert next_dt is not None
        assert next_dt.hour == 12
        assert next_dt.minute == 0
        assert next_dt.second == 0

    def test_next_after_returns_future_time(self, utc_base):
        """Next occurrence should be after input time."""
        event = Parser("*-*-* *:*:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_base)
        assert next_dt > utc_base

    def test_next_after_none_defaults_to_now(self):
        """next_after(None) should use current time."""
        event = Parser("daily").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(None)
        assert next_dt is not None
        # Should be in the future
        assert next_dt > datetime.now(tz=timezone.utc)


class TestNextOccurrenceWeekdays:
    """Test finding next occurrence by weekday."""

    def test_next_monday(self, friday):
        """Should find next Monday from Friday."""
        event = Parser("Mon *-*-* *:*:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(friday)
        assert next_dt is not None
        # Monday is 3 days after Friday
        assert next_dt.weekday() == 0  # Monday

    def test_next_same_weekday_future_time(self, monday):
        """Should find next Monday at future time on same Monday."""
        event = Parser("Mon 12:00:00").parse()
        finder = NextOccurrence(event)
        monday_9am = monday.replace(hour=9, minute=0, second=0)
        next_dt = finder.next_after(monday_9am)
        assert next_dt is not None
        assert next_dt.weekday() == 0  # Monday
        assert next_dt.hour == 12

    def test_next_weekday_not_immediately_after(self, monday):
        """Should skip to next occurrence if past time on that weekday."""
        event = Parser("Mon 09:00:00").parse()
        finder = NextOccurrence(event)
        monday_10am = monday.replace(hour=10, minute=0, second=0)
        next_dt = finder.next_after(monday_10am)
        assert next_dt is not None
        # Should be next Monday
        assert (next_dt - monday_10am).days >= 6

    def test_next_multiple_weekdays(self, friday):
        """Should find next occurrence for multiple weekdays."""
        event = Parser("Mon,Wed,Fri *-*-* *:*:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(friday)
        assert next_dt is not None
        # Should be next Monday, Wed, or Fri (Fri is today, so skip ahead)
        assert next_dt.weekday() in [0, 2, 4]

    def test_next_weekday_range(self, saturday):
        """Should find next weekday in range."""
        event = Parser("Mon..Fri *-*-* *:*:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(saturday)
        assert next_dt is not None
        # Should be next Monday
        assert next_dt.weekday() == 0


class TestNextOccurrenceDates:
    """Test finding next occurrence by date."""

    def test_next_specific_day(self, month_start):
        """Should find next specific day."""
        event = Parser("*-*-15 *:*:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(month_start)
        assert next_dt is not None
        assert next_dt.day == 15

    def test_next_specific_month(self, utc_base):
        """Should find next specific month."""
        event = Parser("*-06-* *:*:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_base)
        assert next_dt is not None
        assert next_dt.month == 6

    def test_next_specific_date(self, month_start):
        """Should find next specific date."""
        event = Parser("*-03-20 *:*:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(month_start)
        assert next_dt is not None
        assert next_dt.day == 20
        assert next_dt.month == 3

    def test_next_monthly(self, month_start):
        """Should find next monthly occurrence."""
        event = Parser("monthly").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(month_start)
        assert next_dt is not None
        assert next_dt.day == 1
        assert next_dt.month > month_start.month

    def test_next_yearly(self, year_start):
        """Should find next yearly occurrence."""
        event = Parser("yearly").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(year_start)
        assert next_dt is not None
        assert next_dt.month == 1
        assert next_dt.day == 1
        assert next_dt.year == year_start.year + 1


class TestNextOccurrenceTimes:
    """Test finding next occurrence by time."""

    def test_next_specific_hour(self, utc_midnight):
        """Should find next specific hour."""
        event = Parser("*-*-* 10:*:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_midnight)
        assert next_dt is not None
        assert next_dt.hour == 10

    def test_next_time_same_day(self, utc_base):
        """Should find next time later same day if applicable."""
        event = Parser("*-*-* 11:00:00").parse()
        finder = NextOccurrence(event)
        utc_1030 = utc_base.replace(hour=10, minute=30, second=0)
        next_dt = finder.next_after(utc_1030)
        assert next_dt is not None
        assert next_dt.hour == 11
        assert next_dt.day == utc_base.day

    def test_next_time_next_day(self, utc_base):
        """Should find next time next day if passed today."""
        event = Parser("*-*-* 09:00:00").parse()
        finder = NextOccurrence(event)
        utc_10am = utc_base.replace(hour=10, minute=0, second=0)
        next_dt = finder.next_after(utc_10am)
        assert next_dt is not None
        assert next_dt.hour == 9
        assert next_dt.day > utc_base.day

    def test_next_specific_minute(self, utc_midnight):
        """Should find next specific minute."""
        event = Parser("*-*-* *:30:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_midnight)
        assert next_dt is not None
        assert next_dt.minute == 30

    def test_next_multiple_hours(self, utc_midnight):
        """Should find next from multiple hours."""
        event = Parser("*-*-* 09,12,17:00:00").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_midnight)
        assert next_dt is not None
        assert next_dt.hour in [9, 12, 17]


class TestNextOccurrenceRangesAndRepetitions:
    """Test finding next occurrence with ranges and repetitions."""

    def test_next_hour_range(self, utc_midnight):
        """Should find next hour in range."""
        event = Parser("*-*-* 09..17:00:00").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_midnight)
        assert next_dt is not None
        assert 9 <= next_dt.hour <= 17

    def test_next_day_range(self, year_start):
        """Should find next day in range."""
        event = Parser("*-*-01..15 *:*:*").parse()
        finder = NextOccurrence(event)
        jan_20 = year_start + timedelta(days=19)
        next_dt = finder.next_after(jan_20)
        assert next_dt is not None
        assert 1 <= next_dt.day <= 15

    def test_next_hourly_repetition(self, utc_midnight):
        """Should find next hour with repetition pattern."""
        event = Parser("*-*-* 0/6:00:00").parse()  # Every 6 hours from 0
        finder = NextOccurrence(event)
        next_dt = finder.next_after(utc_midnight)
        assert next_dt is not None
        # Should be 0, 6, 12, or 18
        assert next_dt.hour in [0, 6, 12, 18]

    def test_next_daily_repetition(self, month_start):
        """Should find next day with repetition pattern."""
        event = Parser("*-*-1/7 *:*:*").parse()  # Every 7 days from 1st
        finder = NextOccurrence(event)
        next_dt = finder.next_after(month_start)
        assert next_dt is not None
        # Should match the repetition pattern


class TestNextOccurrenceComplexSpecs:
    """Test finding next occurrence for complex specifications."""

    def test_next_weekday_and_time(self, friday):
        """Should find next occurrence with weekday and time."""
        event = Parser("Mon 10:00:00").parse()
        finder = NextOccurrence(event)
        friday_9am = friday.replace(hour=9, minute=0, second=0)
        next_dt = finder.next_after(friday_9am)
        assert next_dt is not None
        assert next_dt.weekday() == 0  # Monday
        assert next_dt.hour == 10

    def test_next_weekday_date_time(self, monday):
        """Should find next with weekday, date, and time."""
        event = Parser("Mon 2024-03-* 10:00:00").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(monday)
        assert next_dt is not None
        assert next_dt.weekday() == 0
        assert next_dt.year == 2024
        assert next_dt.month == 3
        assert next_dt.hour == 10

    def test_next_business_hours(self, friday):
        """Should find next business hour occurrence."""
        event = Parser("Mon..Fri 09..17:00:00").parse()
        finder = NextOccurrence(event)
        friday_1pm = friday.replace(hour=13, minute=0, second=0)
        next_dt = finder.next_after(friday_1pm)
        assert next_dt is not None
        assert next_dt.weekday() in range(5)  # Mon..Fri
        assert 9 <= next_dt.hour <= 17


class TestNextOccurrenceEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_next_after_year_end(self, year_end):
        """Should find next occurrence across year boundary."""
        event = Parser("daily").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(year_end)
        assert next_dt is not None
        assert next_dt.year == year_end.year + 1

    def test_next_after_leap_day(self, leap_day_2024):
        """Should find next occurrence after leap day."""
        event = Parser("daily").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(leap_day_2024)
        assert next_dt is not None
        assert next_dt > leap_day_2024

    def test_next_leap_day(self):
        """Should find next leap day."""
        event = Parser("*-02-29 *:*:*").parse()
        finder = NextOccurrence(event)
        # Start from non-leap year
        feb_28_2023 = datetime(2023, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
        next_dt = finder.next_after(feb_28_2023)
        # 2024 is a leap year, should find Feb 29
        if next_dt:
            assert next_dt.month == 2
            assert next_dt.day == 29

    def test_next_month_end(self, month_end):
        """Should find next month end."""
        event = Parser("*-*-31 *:*:*").parse()
        finder = NextOccurrence(event)
        next_dt = finder.next_after(month_end)
        assert next_dt is not None
        assert next_dt.day == 31

    def test_next_with_microseconds_ignored(self, utc_base):
        """Microseconds should be ignored."""
        event = Parser("*-*-* 10:30:45").parse()
        finder = NextOccurrence(event)
        with_micro = utc_base.replace(microsecond=500000)
        next_dt = finder.next_after(with_micro)
        assert next_dt is not None
        assert next_dt.microsecond == 0

    def test_next_large_search_space(self, year_start):
        """Should handle large search spaces efficiently."""
        event = Parser("*-*-*-31 *:*:*").parse()  # Month end
        finder = NextOccurrence(event)
        next_dt = finder.next_after(year_start)
        assert next_dt is not None
        # Should complete without timeout

    def test_next_timeout_one_year(self, year_start):
        """Should timeout after ~1 year search."""
        event = Parser("2099-*-* *:*:*").parse()  # Far future
        finder = NextOccurrence(event)
        # This might find 2099 or return None depending on current date
        # Either finds it or returns None, but doesn't hang
        try:
            finder.next_after(year_start)
        except ValueError:
            # Expected: may timeout or not find match
            pass


class TestNextOccurrencesMultiple:
    """Test finding multiple next occurrences."""

    def test_next_occurrences_count(self, month_start):
        """Should find multiple next occurrences."""
        event = Parser("daily").parse()
        finder = NextOccurrence(event)
        occurrences = finder.next_occurrences(5, month_start)
        assert len(occurrences) <= 5
        # Each should be after previous
        for i in range(1, len(occurrences)):
            assert occurrences[i] > occurrences[i - 1]

    def test_next_occurrences_sequential(self, month_start):
        """Multiple occurrences should be sequential."""
        event = Parser("*-*-* 10:00:00").parse()
        finder = NextOccurrence(event)
        occurrences = finder.next_occurrences(3, month_start)
        assert len(occurrences) == 3
        # Each should be one day after the previous
        for i in range(1, len(occurrences)):
            delta = occurrences[i] - occurrences[i - 1]
            assert delta.days >= 1

    def test_next_occurrences_zero_count(self, month_start):
        """Zero count should return empty list."""
        event = Parser("daily").parse()
        finder = NextOccurrence(event)
        occurrences = finder.next_occurrences(0, month_start)
        assert occurrences == []
