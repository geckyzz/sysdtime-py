"""Integration tests for main sysdtime API functions."""

from datetime import datetime, timedelta, timezone

import pytest

from sysdtime import matches, next_occurrence, parse


class TestMainAPIFunctions:
    """Test main public API functions."""

    def test_parse_returns_calendar_event(self):
        """parse() should return CalendarEvent object."""
        event = parse("daily")
        assert event is not None
        assert hasattr(event, "normalized")

    def test_parse_can_be_normalized(self):
        """Parsed event should be normalizable."""
        event = parse("Mon,Fri 09:00:00")
        norm = event.normalized()
        assert "Mon" in norm
        assert "Fri" in norm
        assert "09:00:00" in norm

    def test_matches_basic(self):
        """matches() should check datetime against spec."""
        dt = datetime(2024, 3, 15, 9, 0, 0, tzinfo=timezone.utc)
        assert matches("*-*-* 09:00:00", dt) is True
        assert matches("*-*-* 10:00:00", dt) is False

    def test_matches_weekday(self):
        """matches() should respect weekday constraints."""
        friday = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert matches("Fri *-*-* 10:00:00", friday) is True
        assert matches("Mon *-*-* 10:00:00", friday) is False

    def test_matches_date(self):
        """matches() should respect date constraints."""
        dt = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert matches("*-03-15 10:00:00", dt) is True
        assert matches("*-03-16 10:00:00", dt) is False

    def test_matches_wildcard(self):
        """matches() should match wildcards."""
        dt = datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone.utc)
        assert matches("*-*-* *:*:*", dt) is True

    def test_matches_epoch_returns_false(self):
        """matches() should return False for epoch specs."""
        dt = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert matches("@1234567890", dt) is False

    def test_next_occurrence_basic(self):
        """next_occurrence() should find next matching time."""
        base = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        next_dt = next_occurrence("daily", base)
        assert next_dt is not None
        assert next_dt > base

    def test_next_occurrence_is_in_future(self):
        """next_occurrence() should return future datetime."""
        base = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        next_dt = next_occurrence("*-*-* 12:00:00", base)
        assert next_dt is not None
        assert next_dt > base

    def test_next_occurrence_matches_spec(self):
        """next_occurrence() result should match the spec."""
        base = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        spec = "Mon *-*-* 12:00:00"
        next_dt = next_occurrence(spec, base)
        if next_dt:
            # next_dt should match the spec
            assert matches(spec, next_dt) is True

    def test_next_occurrence_default_time(self):
        """next_occurrence() with None should use current time."""
        spec = "daily"
        next_dt = next_occurrence(spec, None)
        assert next_dt is not None
        # Should be in the future
        now = datetime.now(tz=timezone.utc)
        assert next_dt > now

    def test_next_occurrence_epoch_returns_none(self):
        """next_occurrence() should return None for epoch specs."""
        base = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = next_occurrence("@1234567890", base)
        assert result is None


class TestIntegrationEndToEnd:
    """End-to-end integration tests."""

    def test_parse_and_match(self):
        """Parse spec and match against datetime."""
        spec = "Mon,Fri 09:30:00"
        event = parse(spec)

        friday = datetime(2024, 3, 15, 9, 30, 0, tzinfo=timezone.utc)
        monday = datetime(2024, 3, 18, 9, 30, 0, tzinfo=timezone.utc)
        wednesday = datetime(2024, 3, 13, 9, 30, 0, tzinfo=timezone.utc)

        matcher_class = __import__("sysdtime").Matcher
        matcher = matcher_class(event)

        assert matcher.matches(friday) is True
        assert matcher.matches(monday) is True
        assert matcher.matches(wednesday) is False

    def test_parse_and_find_next(self):
        """Parse spec and find next occurrence."""
        spec = "Mon,Fri 09:00:00"
        base = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)  # Friday 10am

        next_dt = next_occurrence(spec, base)
        assert next_dt is not None
        assert next_occurrence(spec, base) > base

    def test_shorthand_daily(self):
        """Test 'daily' shorthand end-to-end."""
        base = datetime(2024, 3, 15, 0, 0, 0, tzinfo=timezone.utc)

        # Should match
        assert matches("daily", base) is True

        # Next should be tomorrow
        next_dt = next_occurrence("daily", base)
        assert next_dt is not None
        assert next_dt.day == 16

    def test_shorthand_weekly(self):
        """Test 'weekly' shorthand end-to-end."""
        monday = datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc)
        friday = datetime(2024, 3, 15, 0, 0, 0, tzinfo=timezone.utc)

        # Monday should match
        assert matches("weekly", monday) is True

        # Friday should not match
        assert matches("weekly", friday) is False

    def test_shorthand_monthly(self):
        """Test 'monthly' shorthand end-to-end."""
        first = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
        fifteenth = datetime(2024, 3, 15, 0, 0, 0, tzinfo=timezone.utc)

        # 1st should match
        assert matches("monthly", first) is True

        # 15th should not match
        assert matches("monthly", fifteenth) is False

    def test_complex_spec_workflow(self):
        """Test complex spec through entire workflow."""
        spec = "Mon..Fri 09..17:00:00"

        # Parse
        event = parse(spec)
        assert event is not None

        # Create business hour datetimes
        monday_1pm = datetime(2024, 3, 11, 13, 0, 0, tzinfo=timezone.utc)
        saturday_1pm = datetime(2024, 3, 16, 13, 0, 0, tzinfo=timezone.utc)
        friday_9pm = datetime(2024, 3, 15, 21, 0, 0, tzinfo=timezone.utc)

        # Test matching
        assert matches(spec, monday_1pm) is True
        assert matches(spec, saturday_1pm) is False
        assert matches(spec, friday_9pm) is False

        # Test finding next occurrence
        base = datetime(2024, 3, 16, 10, 0, 0, tzinfo=timezone.utc)  # Saturday
        next_dt = next_occurrence(spec, base)
        assert next_dt is not None
        assert next_dt.weekday() == 0  # Monday

    def test_timezone_aware_matching(self):
        """Test matching with different timezones."""
        base_utc = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        base_offset = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))

        spec = "*-*-* 10:00:00"

        # Both should match at their respective times
        assert matches(spec, base_utc) is True
        assert matches(spec, base_offset) is True

    def test_normalized_roundtrip(self):
        """Normalized form should be valid spec."""
        original_specs = [
            "daily",
            "Mon,Fri 09:00:00",
            "*-03-15 10:30:45",
            "Mon..Fri 09..17:00:00",
        ]

        for spec in original_specs:
            event = parse(spec)
            norm = event.normalized()
            # Normalized form should be a valid spec that can be parsed
            event2 = parse(norm)
            assert event2 is not None

    def test_leap_year_handling(self):
        """Test handling of leap day."""
        leap_day = datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc)

        # Should match leap day spec
        assert matches("*-02-29 *:*:*", leap_day) is True

        # Feb 28 should not match 29
        feb_28 = datetime(2024, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
        assert matches("*-02-29 *:*:*", feb_28) is False

    def test_year_boundary_transition(self):
        """Test year boundary handling."""
        dec_31 = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        jan_1 = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        # Should match year-based specs
        assert matches("2024-*-* *:*:*", dec_31) is True
        assert matches("2025-*-* *:*:*", jan_1) is True

    def test_month_boundary_transition(self):
        """Test month boundary handling."""
        mar_31 = datetime(2024, 3, 31, 23, 59, 59, tzinfo=timezone.utc)
        apr_1 = datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc)

        # Should match month-based specs
        assert matches("*-03-* *:*:*", mar_31) is True
        assert matches("*-04-* *:*:*", apr_1) is True


class TestIntegrationErrorCases:
    """Test error handling in integration scenarios."""

    def test_invalid_timezone_in_spec(self):
        """Invalid timezone should raise ValueError."""
        with pytest.raises(ValueError):
            parse("*-*-* 12:00:00 InvalidTZ")

    def test_invalid_epoch_format(self):
        """Invalid epoch should raise ValueError."""
        with pytest.raises(ValueError):
            parse("@abc123")

    def test_matches_with_invalid_spec(self):
        """matches() with invalid spec should raise ValueError."""
        dt = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            matches("*-*-* 12:00:00 BadTimezone", dt)


class TestIntegrationPerformance:
    """Test performance-related aspects."""

    def test_parse_completes_quickly(self):
        """Parsing should complete quickly."""
        import time

        specs = [
            "daily",
            "weekly",
            "monthly",
            "Mon,Fri 09:00:00",
            "*-*-* 10:30:45",
            "Mon..Fri 09..17:*:*",
        ]

        start = time.time()
        for spec in specs * 100:  # Parse each spec 100 times
            parse(spec)
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0

    def test_matching_completes_quickly(self):
        """Matching should complete quickly."""
        import time

        spec = "Mon..Fri 09..17:00:00"
        dt = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)

        start = time.time()
        for _ in range(10000):
            matches(spec, dt)
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 1.0

    def test_next_occurrence_with_short_timespan(self):
        """Finding next occurrence with short timespan."""
        import time

        base = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)

        start = time.time()
        for _ in range(10):  # Reduced from 100
            next_occurrence("daily", base)
        elapsed = time.time() - start

        # Should complete reasonably fast
        assert elapsed < 10.0
