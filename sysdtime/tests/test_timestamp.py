"""Tests for timestamp parser."""

from datetime import datetime, timedelta, timezone

import pytest

from sysdtime.timestamp import TimestampParser, parse_timestamp


class TestTimestampParserSpecialTokens:
    """Test special time token parsing."""

    def test_parse_now(self):
        """Parse 'now' token."""
        base = datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = parse_timestamp("now", base)
        assert result == base

    def test_parse_today(self):
        """Parse 'today' token."""
        base = datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = parse_timestamp("today", base)
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_parse_yesterday(self):
        """Parse 'yesterday' token."""
        base = datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = parse_timestamp("yesterday", base)
        assert result.day == 14
        assert result.hour == 0
        assert result.minute == 0

    def test_parse_tomorrow(self):
        """Parse 'tomorrow' token."""
        base = datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = parse_timestamp("tomorrow", base)
        assert result.day == 16
        assert result.hour == 0

    def test_parse_case_insensitive(self):
        """Token parsing should be case-insensitive."""
        base = datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone.utc)
        assert parse_timestamp("NOW", base).hour == base.hour
        assert parse_timestamp("Today", base).day == base.day
        assert parse_timestamp("YESTERDAY", base).day == 14
        assert parse_timestamp("ToMoRrOw", base).day == 16


class TestTimestampParserRelative:
    """Test relative timestamp parsing."""

    def test_parse_relative_hours(self):
        """Parse relative hours."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+3h", base)
        assert result == base + timedelta(hours=3)

    def test_parse_relative_minutes(self):
        """Parse relative minutes."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+30min", base)
        assert result == base + timedelta(minutes=30)

    def test_parse_relative_seconds(self):
        """Parse relative seconds."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+45s", base)
        assert result == base + timedelta(seconds=45)

    def test_parse_relative_days(self):
        """Parse relative days."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+5d", base)
        assert result == base + timedelta(days=5)

    def test_parse_relative_weeks(self):
        """Parse relative weeks."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+2w", base)
        assert result == base + timedelta(weeks=2)

    def test_parse_relative_negative(self):
        """Parse negative relative time."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("-2h", base)
        assert result == base - timedelta(hours=2)

    def test_parse_relative_combined(self):
        """Parse combined relative time units."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+3h30min", base)
        expected = base + timedelta(hours=3, minutes=30)
        assert result == expected

    def test_parse_relative_ago(self):
        """Parse 'ago' suffix."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("2h ago", base)
        assert result == base - timedelta(hours=2)

    def test_parse_relative_multiple_units(self):
        """Parse multiple relative units."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+1d2h30min15s", base)
        expected = base + timedelta(days=1, hours=2, minutes=30, seconds=15)
        assert result == expected

    def test_parse_relative_float_values(self):
        """Parse float values in relative time."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+1.5h", base)
        assert result == base + timedelta(hours=1.5)

    def test_parse_relative_invalid_unit(self):
        """Invalid unit should raise ValueError."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            parse_timestamp("+5xyz", base)


class TestTimestampParserAbsolute:
    """Test absolute timestamp parsing."""

    def test_parse_iso8601_full(self):
        """Parse full ISO 8601 format."""
        result = parse_timestamp("2024-03-15T10:30:45")
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45

    def test_parse_iso8601_with_space(self):
        """Parse ISO 8601 with space instead of T."""
        result = parse_timestamp("2024-03-15 10:30:45")
        assert result.year == 2024
        assert result.hour == 10

    def test_parse_iso8601_date_only(self):
        """Parse ISO 8601 date only."""
        result = parse_timestamp("2024-03-15")
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 0

    def test_parse_iso8601_time_only(self):
        """Parse time specification."""
        result = parse_timestamp("10:30:45")
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45

    def test_parse_rfc3339_with_z(self):
        """Parse RFC 3339 with Z suffix."""
        result = parse_timestamp("2024-03-15T10:30:45Z")
        assert result.tzinfo == timezone.utc
        assert result.year == 2024

    def test_parse_rfc3339_with_offset(self):
        """Parse RFC 3339 with timezone offset."""
        result = parse_timestamp("2024-03-15T10:30:45+01:00")
        assert result.tzinfo is not None
        expected_offset = timedelta(hours=1)
        assert result.tzinfo.utcoffset(None) == expected_offset

    def test_parse_rfc3339_with_offset_no_colon(self):
        """Parse RFC 3339 with offset without colon."""
        result = parse_timestamp("2024-03-15T10:30:45+0100")
        assert result.tzinfo is not None

    def test_parse_rfc3339_negative_offset(self):
        """Parse RFC 3339 with negative offset."""
        result = parse_timestamp("2024-03-15T10:30:45-05:00")
        assert result.tzinfo is not None
        expected_offset = timedelta(hours=-5)
        assert result.tzinfo.utcoffset(None) == expected_offset

    def test_parse_with_timezone_name(self):
        """Parse with IANA timezone name."""
        result = parse_timestamp("2024-03-15 10:30:45 UTC")
        assert result.tzinfo == timezone.utc

    def test_parse_with_timezone_alias(self):
        """Parse with timezone alias."""
        result = parse_timestamp("2024-03-15 10:30:45 JST")
        assert result.tzinfo is not None

    def test_parse_partial_time(self):
        """Parse time with missing components."""
        result = parse_timestamp("10:30")
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0

    def test_parse_hour_only(self):
        """Parse hour only."""
        result = parse_timestamp("10")
        assert result.hour == 10
        assert result.minute == 0

    def test_parse_with_weekday(self):
        """Parse with weekday prefix (should ignore)."""
        result = parse_timestamp("Fri 2024-03-15 10:30:45")
        assert result.year == 2024
        assert result.month == 3

    def test_parse_default_timezone_utc(self):
        """Default timezone should be UTC."""
        result = parse_timestamp("2024-03-15 10:30:45")
        assert result.tzinfo == timezone.utc


class TestTimestampParserEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_parse_leap_day(self):
        """Parse leap day."""
        result = parse_timestamp("2024-02-29 12:00:00")
        assert result.day == 29
        assert result.month == 2

    def test_parse_year_boundary(self):
        """Parse at year boundary."""
        result = parse_timestamp("2024-12-31T23:59:59")
        assert result.year == 2024
        assert result.month == 12

    def test_parse_midnight(self):
        """Parse midnight."""
        result = parse_timestamp("2024-03-15T00:00:00")
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_parse_end_of_day(self):
        """Parse end of day."""
        result = parse_timestamp("2024-03-15T23:59:59")
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59

    def test_parse_timezone_offset_half_hour(self):
        """Parse timezone with half-hour offset."""
        result = parse_timestamp("2024-03-15T10:30:45+05:30")
        assert result.tzinfo is not None

    def test_parse_fractional_seconds(self):
        """Parse fractional seconds (should truncate)."""
        result = parse_timestamp("2024-03-15T10:30:45.123456")
        assert result.second == 45
        # Fractional part should be dropped


class TestTimestampParserTimeUnits:
    """Test all supported time unit formats."""

    def test_time_unit_microseconds(self):
        """Parse microseconds."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+1000000us", base)
        assert result == base + timedelta(seconds=1)

    def test_time_unit_milliseconds(self):
        """Parse milliseconds."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+1000ms", base)
        assert result == base + timedelta(seconds=1)

    def test_time_unit_second_variants(self):
        """Parse second variants."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        for unit in ["s", "sec", "seconds", "second"]:
            result = parse_timestamp(f"+5{unit}", base)
            assert result == base + timedelta(seconds=5)

    def test_time_unit_minute_variants(self):
        """Parse minute variants."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        for unit in ["m", "min", "minute", "minutes"]:
            result = parse_timestamp(f"+5{unit}", base)
            assert result == base + timedelta(minutes=5)

    def test_time_unit_hour_variants(self):
        """Parse hour variants."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        for unit in ["h", "hr", "hour", "hours"]:
            result = parse_timestamp(f"+5{unit}", base)
            assert result == base + timedelta(hours=5)

    def test_time_unit_day_variants(self):
        """Parse day variants."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        for unit in ["d", "day", "days"]:
            result = parse_timestamp(f"+5{unit}", base)
            assert result == base + timedelta(days=5)

    def test_time_unit_week_variants(self):
        """Parse week variants."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        for unit in ["w", "week", "weeks"]:
            result = parse_timestamp(f"+5{unit}", base)
            assert result == base + timedelta(weeks=5)

    def test_time_unit_month(self):
        """Parse month unit."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+1M", base)
        # Month is approximately 30.44 days
        assert result > base

    def test_time_unit_year(self):
        """Parse year unit."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+1y", base)
        # Year is approximately 365.25 days
        assert result > base


class TestTimestampParserIntegration:
    """Test integration scenarios."""

    def test_parse_complex_relative(self):
        """Parse complex relative expression."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+1d2h30min45s", base)
        expected = base + timedelta(days=1, hours=2, minutes=30, seconds=45)
        assert result == expected

    def test_parse_with_base_time(self):
        """Parsing with explicit base time."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_timestamp("+1h", base)
        assert result == datetime(2024, 3, 15, 11, 30, 0, tzinfo=timezone.utc)

    def test_parse_timezone_preservation(self):
        """Timezone should be preserved."""
        result = parse_timestamp("2024-03-15T10:30:45+02:00")
        offset = result.tzinfo.utcoffset(None)
        assert offset == timedelta(hours=2)

    def test_parser_class_multiple_calls(self):
        """TimestampParser should handle multiple parses."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        parser = TimestampParser("+2h", base)
        result1 = parser.parse()
        result2 = parser.parse()
        assert result1 == result2

    def test_parse_various_separators(self):
        """Parse with various datetime separators."""
        # Both should produce same result
        with_t = parse_timestamp("2024-03-15T10:30:45")
        with_space = parse_timestamp("2024-03-15 10:30:45")
        assert with_t.year == with_space.year
        assert with_t.hour == with_space.hour


class TestTimestampParserErrors:
    """Test error handling."""

    def test_error_invalid_relative_format(self):
        """Invalid relative format should raise ValueError."""
        base = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            parse_timestamp("+xyz", base)

    def test_error_invalid_absolute_date(self):
        """Invalid date should raise ValueError."""
        with pytest.raises(ValueError):
            parse_timestamp("2024-13-45")

    def test_error_invalid_absolute_time(self):
        """Invalid time should raise ValueError."""
        with pytest.raises(ValueError):
            parse_timestamp("25:75:90")

    def test_error_invalid_timezone_offset(self):
        """Invalid timezone offset should raise ValueError."""
        with pytest.raises(ValueError):
            parse_timestamp("2024-03-15T10:30:45+99:99")
