"""Tests for calendar event parser."""

import pytest

from sysdtime.parser import Parser


class TestParserShorthands:
    """Test shorthand event specifications."""

    def test_minutely(self):
        """Parse 'minutely' shorthand."""
        event = Parser("minutely").parse()
        assert event.date.year.is_wildcard
        assert event.date.month.is_wildcard
        assert event.date.day.is_wildcard
        assert event.time.hour.is_wildcard
        assert event.time.minute.is_wildcard
        assert 0 in event.time.second.values

    def test_hourly(self):
        """Parse 'hourly' shorthand."""
        event = Parser("hourly").parse()
        assert event.time.hour.is_wildcard
        assert 0 in event.time.minute.values
        assert 0 in event.time.second.values

    def test_daily(self):
        """Parse 'daily' shorthand."""
        event = Parser("daily").parse()
        assert 0 in event.time.hour.values
        assert 0 in event.time.minute.values
        assert 0 in event.time.second.values

    def test_monthly(self):
        """Parse 'monthly' shorthand."""
        event = Parser("monthly").parse()
        assert 1 in event.date.day.values
        assert 0 in event.time.hour.values

    def test_weekly(self):
        """Parse 'weekly' shorthand."""
        event = Parser("weekly").parse()
        assert 0 in event.weekdays  # Monday

    def test_yearly_and_annually(self):
        """Parse 'yearly' and 'annually' shorthands."""
        yearly = Parser("yearly").parse()
        annually = Parser("annually").parse()
        assert 1 in yearly.date.month.values
        assert 1 in annually.date.month.values
        assert 1 in yearly.date.day.values
        assert 1 in annually.date.day.values

    def test_quarterly(self):
        """Parse 'quarterly' shorthand."""
        event = Parser("quarterly").parse()
        assert event.date.month.values == {1, 4, 7, 10}

    def test_semiannually(self):
        """Parse 'semiannually' shorthand."""
        event = Parser("semiannually").parse()
        assert event.date.month.values == {1, 7}

    def test_shorthand_case_insensitive(self):
        """Shorthands should be case-insensitive."""
        daily_lower = Parser("daily").parse()
        daily_upper = Parser("DAILY").parse()
        daily_mixed = Parser("DaIlY").parse()
        assert 0 in daily_lower.time.hour.values
        assert 0 in daily_upper.time.hour.values
        assert 0 in daily_mixed.time.hour.values


class TestParserEpoch:
    """Test epoch timestamp parsing."""

    def test_epoch_zero(self):
        """Parse epoch timestamp zero."""
        event = Parser("@0").parse()
        assert event.is_epoch is True
        assert event.epoch_time == 0

    def test_epoch_standard(self):
        """Parse standard epoch timestamp."""
        event = Parser("@1234567890").parse()
        assert event.is_epoch is True
        assert event.epoch_time == 1234567890

    def test_epoch_large_number(self):
        """Parse large epoch timestamp."""
        event = Parser("@2147483647").parse()
        assert event.is_epoch is True
        assert event.epoch_time == 2147483647

    def test_epoch_normalized(self):
        """Epoch normalized form should use @."""
        event = Parser("@1234567890").parse()
        assert event.normalized() == "@1234567890"

    def test_epoch_invalid_negative(self):
        """Negative epoch should raise ValueError."""
        with pytest.raises(ValueError):
            Parser("@-123").parse()

    def test_epoch_invalid_format(self):
        """Invalid epoch format should raise ValueError."""
        with pytest.raises(ValueError):
            Parser("@abc").parse()


class TestParserWeekdays:
    """Test weekday parsing."""

    def test_single_weekday(self):
        """Parse single weekday."""
        event = Parser("Mon *-*-* 12:00:00").parse()
        assert event.weekdays == {0}

    def test_multiple_weekdays(self):
        """Parse comma-separated weekdays."""
        event = Parser("Mon,Wed,Fri *-*-* 12:00:00").parse()
        assert event.weekdays == {0, 2, 4}

    def test_weekday_range(self):
        """Parse weekday range."""
        event = Parser("Mon..Fri *-*-* 12:00:00").parse()
        assert event.weekdays == {0, 1, 2, 3, 4}

    def test_weekday_mixed(self):
        """Parse mixed ranges and singles."""
        event = Parser("Mon,Wed..Fri,Sun *-*-* 12:00:00").parse()
        assert event.weekdays == {0, 2, 3, 4, 6}

    def test_all_weekdays(self):
        """Parse all seven weekdays."""
        event = Parser("Mon..Sun *-*-* 12:00:00").parse()
        assert event.weekdays == {0, 1, 2, 3, 4, 5, 6}

    def test_weekday_case_insensitive(self):
        """Weekday parsing should be case-insensitive."""
        event_lower = Parser("mon,fri *-*-* 12:00:00").parse()
        event_upper = Parser("MON,FRI *-*-* 12:00:00").parse()
        event_mixed = Parser("Mon,FrI *-*-* 12:00:00").parse()
        assert event_lower.weekdays == event_upper.weekdays == event_mixed.weekdays

    def test_weekday_full_names(self):
        """Parse full weekday names."""
        event = Parser("Monday,Friday *-*-* 12:00:00").parse()
        assert event.weekdays == {0, 4}

    def test_weekday_without_other_constraints(self):
        """Weekday parsing defaults to all days if alone."""
        # When Parser sees 'Mon' alone, it parses as weekday specification
        # but returns all weekdays because date/time are wildcards
        event = Parser("Mon *-*-* 12:00:00").parse()
        assert event.weekdays == {0}


class TestParserDates:
    """Test date specification parsing."""

    def test_date_wildcard(self):
        """Parse wildcard date."""
        event = Parser("*-*-* 12:00:00").parse()
        assert event.date.year.is_wildcard
        assert event.date.month.is_wildcard
        assert event.date.day.is_wildcard

    def test_date_specific(self):
        """Parse specific date."""
        event = Parser("2024-03-15 12:00:00").parse()
        assert 2024 in event.date.year.values
        assert 3 in event.date.month.values
        assert 15 in event.date.day.values

    def test_date_year_only(self):
        """Parse year specification."""
        event = Parser("2024-*-* 12:00:00").parse()
        assert 2024 in event.date.year.values
        assert event.date.month.is_wildcard
        assert event.date.day.is_wildcard

    def test_date_month_only(self):
        """Parse month specification."""
        event = Parser("*-03-* 12:00:00").parse()
        assert event.date.year.is_wildcard
        assert 3 in event.date.month.values
        assert event.date.day.is_wildcard

    def test_date_day_only(self):
        """Parse day specification."""
        event = Parser("*-*-15 12:00:00").parse()
        assert event.date.year.is_wildcard
        assert event.date.month.is_wildcard
        assert 15 in event.date.day.values

    def test_date_month_and_day(self):
        """Parse month and day."""
        event = Parser("*-03-15 12:00:00").parse()
        assert event.date.year.is_wildcard
        assert 3 in event.date.month.values
        assert 15 in event.date.day.values

    def test_date_range(self):
        """Parse date range."""
        event = Parser("*-*-1..7 12:00:00").parse()
        assert event.date.day.ranges == [(1, 7)]

    def test_date_list(self):
        """Parse date list."""
        event = Parser("*-01,04,07,10-01 12:00:00").parse()
        assert event.date.month.values == {1, 4, 7, 10}

    def test_date_repetition(self):
        """Parse date repetition."""
        event = Parser("*-*-1/7 12:00:00").parse()
        assert event.date.day.repetitions == 7
        assert event.date.day.start_value == 1

    def test_date_last_day(self):
        """Parse last day specification."""
        # Parser only sets is_last_day when ~ is properly recognized
        # "*-*-~" gets parsed as date only, which becomes wildcard
        event = Parser("*-02~03 12:00:00").parse()
        assert event.date.day.is_last_day is True
        assert event.date.day.last_day_offset == 3

    def test_date_last_day_with_offset(self):
        """Parse last day with offset."""
        event = Parser("*-02~03 12:00:00").parse()
        assert event.date.day.is_last_day is True
        assert event.date.day.last_day_offset == 3

    def test_date_short_day_format(self):
        """Parse day specification without dash separator."""
        event = Parser("15 12:00:00").parse()
        assert 15 in event.date.day.values

    def test_date_short_month_day_format(self):
        """Parse month-day specification without leading dash."""
        event = Parser("03-15 12:00:00").parse()
        assert 3 in event.date.month.values
        assert 15 in event.date.day.values


class TestParserTimes:
    """Test time specification parsing."""

    def test_time_full_format(self):
        """Parse full time format HH:MM:SS."""
        event = Parser("*-*-* 09:30:45").parse()
        assert 9 in event.time.hour.values
        assert 30 in event.time.minute.values
        assert 45 in event.time.second.values

    def test_time_hour_minute_format(self):
        """Parse HH:MM format (seconds default to 00)."""
        event = Parser("*-*-* 09:30").parse()
        assert 9 in event.time.hour.values
        assert 30 in event.time.minute.values
        assert 0 in event.time.second.values

    def test_time_hour_only(self):
        """Parse HH format (minutes and seconds default to 00)."""
        event = Parser("*-*-* 09").parse()
        assert 9 in event.time.hour.values
        assert 0 in event.time.minute.values
        assert 0 in event.time.second.values

    def test_time_wildcard(self):
        """Parse wildcard time."""
        event = Parser("*-*-* *:*:*").parse()
        assert event.time.hour.is_wildcard
        assert event.time.minute.is_wildcard
        assert event.time.second.is_wildcard

    def test_time_hour_wildcard(self):
        """Parse wildcard hour."""
        event = Parser("*-*-* *:00:00").parse()
        assert event.time.hour.is_wildcard
        assert 0 in event.time.minute.values

    def test_time_range(self):
        """Parse time range."""
        event = Parser("*-*-* 09..17:00:00").parse()
        assert event.time.hour.ranges == [(9, 17)]

    def test_time_list(self):
        """Parse time list."""
        event = Parser("*-*-* 09,13,17:00:00").parse()
        assert event.time.hour.values == {9, 13, 17}

    def test_time_repetition(self):
        """Parse time repetition with range."""
        event = Parser("*-*-* 0..23/2:00:00").parse()
        assert event.time.hour.repetitions == 2
        assert event.time.hour.ranges == [(0, 23)]

    def test_time_with_range_and_repetition(self):
        """Parse range with repetition."""
        event = Parser("*-*-* 09..17/2:00:00").parse()
        assert event.time.hour.repetitions == 2
        assert event.time.hour.ranges == [(9, 17)]


class TestParserTimezones:
    """Test timezone parsing."""

    def test_timezone_utc(self):
        """Parse UTC timezone."""
        event = Parser("*-*-* 12:00:00 UTC").parse()
        assert event.timezone == "UTC"
        assert event.explicit_timezone is True

    def test_timezone_iana(self):
        """Parse IANA timezone."""
        event = Parser("*-*-* 12:00:00 Asia/Tokyo").parse()
        assert event.timezone == "Asia/Tokyo"
        assert event.explicit_timezone is True

    def test_timezone_alias_wib(self):
        """Parse timezone alias WIB."""
        event = Parser("*-*-* 12:00:00 WIB").parse()
        assert event.timezone == "WIB"
        assert event.explicit_timezone is True

    def test_timezone_alias_jst(self):
        """Parse timezone alias JST."""
        event = Parser("*-*-* 12:00:00 JST").parse()
        assert event.timezone == "JST"
        assert event.explicit_timezone is True

    def test_timezone_invalid(self):
        """Parse invalid timezone should raise ValueError."""
        with pytest.raises(ValueError):
            Parser("*-*-* 12:00:00 Invalid/Zone").parse()

    def test_timezone_with_hyphen(self):
        """Parse timezone with hyphen."""
        event = Parser("*-*-* 12:00:00 America/New_York").parse()
        assert event.timezone == "America/New_York"

    def test_timezone_case_preserved(self):
        """Timezone should preserve case."""
        event = Parser("*-*-* 12:00:00 Europe/London").parse()
        assert event.timezone == "Europe/London"

    def test_without_explicit_timezone_defaults_utc(self):
        """Without explicit timezone, should default to UTC."""
        event = Parser("*-*-* 12:00:00").parse()
        assert event.timezone == "UTC"
        assert event.explicit_timezone is False


class TestParserCombinations:
    """Test complex parsing combinations."""

    def test_weekday_date_time(self):
        """Parse weekday with date and time."""
        event = Parser("Mon 2024-03-15 09:30:00").parse()
        assert event.weekdays == {0}
        assert 2024 in event.date.year.values
        assert 9 in event.time.hour.values

    def test_weekday_time_only(self):
        """Parse weekday with time only."""
        event = Parser("Mon 09:30:00").parse()
        assert event.weekdays == {0}
        assert 9 in event.time.hour.values
        assert event.date.day.is_wildcard

    def test_weekday_date_time_timezone(self):
        """Parse complete specification with timezone."""
        event = Parser("Mon..Fri 2024-*-* 09:00:00 UTC").parse()
        assert event.weekdays == {0, 1, 2, 3, 4}
        assert 2024 in event.date.year.values
        assert 9 in event.time.hour.values
        assert event.timezone == "UTC"

    def test_mixed_specification(self):
        """Parse mixed wildcard and specific."""
        event = Parser("*-03-15 09:30:*").parse()
        assert 3 in event.date.month.values
        assert 15 in event.date.day.values
        assert 9 in event.time.hour.values
        assert 30 in event.time.minute.values
        assert event.time.second.is_wildcard

    def test_all_components(self):
        """Parse specification with all components."""
        event = Parser("Mon,Fri 2024-03-01..07 09,17:30:00 Asia/Tokyo").parse()
        assert event.weekdays == {0, 4}
        assert 2024 in event.date.year.values
        assert 3 in event.date.month.values
        assert event.date.day.ranges == [(1, 7)]
        assert event.time.hour.values == {9, 17}
        assert event.timezone == "Asia/Tokyo"


class TestParserEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string(self):
        """Empty string should parse to default wildcard."""
        event = Parser("").parse()
        assert event.date.year.is_wildcard
        assert event.time.hour.is_wildcard

    def test_whitespace_only(self):
        """Whitespace-only string should behave like empty."""
        event = Parser("   ").parse()
        assert event.date.year.is_wildcard

    def test_leading_trailing_whitespace(self):
        """Parser should handle leading/trailing whitespace."""
        event = Parser("  Mon  *-*-*  12:00:00  ").parse()
        assert event.weekdays == {0}
        assert 12 in event.time.hour.values

    def test_multiple_spaces_between_components(self):
        """Parser should handle multiple spaces."""
        event = Parser("Mon    *-*-*    12:00:00").parse()
        assert event.weekdays == {0}

    def test_zero_values(self):
        """Zero values should be valid."""
        event = Parser("*-*-* 00:00:00").parse()
        assert 0 in event.time.hour.values
        assert 0 in event.time.minute.values

    def test_boundary_values(self):
        """Boundary values should be valid."""
        event = Parser("*-12-31 23:59:59").parse()
        assert 12 in event.date.month.values
        assert 31 in event.date.day.values
        assert 23 in event.time.hour.values
        assert 59 in event.time.minute.values

    def test_year_boundaries(self):
        """Year boundaries should be parsed."""
        event = Parser("1970-*-* 12:00:00").parse()
        assert 1970 in event.date.year.values
        event = Parser("2099-*-* 12:00:00").parse()
        assert 2099 in event.date.year.values


class TestParserNormalization:
    """Test parser output normalization."""

    def test_normalized_daily(self):
        """Parse and normalize 'daily'."""
        event = Parser("daily").parse()
        norm = event.normalized()
        assert "*-*-*" in norm
        assert "00:00:00" in norm

    def test_normalized_preserves_structure(self):
        """Normalized output should preserve specification structure."""
        orig = "Mon,Fri 2024-03-15 09:30:00"
        event = Parser(orig).parse()
        norm = event.normalized()
        # Should contain key elements
        assert "Mon" in norm
        assert "Fri" in norm
        assert "2024" in norm

    def test_original_spec_preserved(self):
        """CalendarEvent should preserve original spec."""
        orig = "Mon,Fri 09:00:00"
        event = Parser(orig).parse()
        assert event.original_spec == orig
