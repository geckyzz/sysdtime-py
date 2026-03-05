"""Tests for data types and dataclasses."""

from sysdtime.types import CalendarEvent, DateSpec, Spec, TimeSpec, _ensure_wildcard_if_empty


class TestSpec:
    """Test Spec dataclass."""

    def test_spec_default_values(self):
        """Default spec should have no values/ranges/wildcard."""
        spec = Spec()
        assert spec.values == set()
        assert spec.ranges == []
        assert spec.is_wildcard is False

    def test_spec_exact_values(self):
        """Spec with values should match those values."""
        spec = Spec(values={1, 5, 15})
        assert spec.matches(1) is True
        assert spec.matches(5) is True
        assert spec.matches(15) is True
        assert spec.matches(7) is False

    def test_spec_range(self):
        """Spec with range should match values in range."""
        spec = Spec(ranges=[(1, 7)])
        assert spec.matches(1) is True
        assert spec.matches(4) is True
        assert spec.matches(7) is True
        assert spec.matches(0) is False
        assert spec.matches(8) is False

    def test_spec_multiple_ranges(self):
        """Spec with multiple ranges should match any range."""
        spec = Spec(ranges=[(1, 5), (10, 15)])
        assert spec.matches(3) is True
        assert spec.matches(12) is True
        assert spec.matches(7) is False

    def test_spec_wildcard_matches_all(self):
        """Wildcard spec should match any value."""
        spec = Spec(is_wildcard=True)
        assert spec.matches(0) is True
        assert spec.matches(100) is True
        assert spec.matches(-5) is True

    def test_spec_last_day(self):
        """Last day spec should have appropriate flags."""
        spec = Spec(is_last_day=True, last_day_offset=3)
        assert spec.is_last_day is True
        assert spec.last_day_offset == 3

    def test_spec_repetition(self):
        """Spec with repetition should match pattern."""
        spec = Spec(repetitions=7, start_value=1)
        assert spec.matches_with_repetition(1, 31) is True
        assert spec.matches_with_repetition(8, 31) is True
        assert spec.matches_with_repetition(15, 31) is True
        assert spec.matches_with_repetition(2, 31) is False

    def test_spec_repetition_no_start(self):
        """Repetition without start should use modulo."""
        spec = Spec(repetitions=2)
        assert spec.matches_with_repetition(0, 59) is True
        assert spec.matches_with_repetition(2, 59) is True
        assert spec.matches_with_repetition(1, 59) is False

    def test_spec_repetition_boundary(self):
        """Repetition should respect boundaries."""
        spec = Spec(repetitions=7, start_value=1)
        assert spec.matches_with_repetition(1, 31) is True
        assert spec.matches_with_repetition(32, 31) is False  # > max_value

    def test_spec_values_and_ranges(self):
        """Spec with both values and ranges should match either."""
        spec = Spec(values={5}, ranges=[(10, 15)])
        assert spec.matches(5) is True
        assert spec.matches(12) is True
        assert spec.matches(6) is False


class TestEnsureWildcardIfEmpty:
    """Test _ensure_wildcard_if_empty helper."""

    def test_empty_spec_becomes_wildcard(self):
        """Empty spec should become wildcard."""
        spec = Spec()
        _ensure_wildcard_if_empty(spec)
        assert spec.is_wildcard is True

    def test_spec_with_values_stays_unchanged(self):
        """Spec with values should not become wildcard."""
        spec = Spec(values={1, 2, 3})
        _ensure_wildcard_if_empty(spec)
        assert spec.is_wildcard is False

    def test_spec_with_ranges_stays_unchanged(self):
        """Spec with ranges should not become wildcard."""
        spec = Spec(ranges=[(1, 10)])
        _ensure_wildcard_if_empty(spec)
        assert spec.is_wildcard is False

    def test_spec_already_wildcard_stays_wildcard(self):
        """Already wildcard spec should stay wildcard."""
        spec = Spec(is_wildcard=True)
        _ensure_wildcard_if_empty(spec)
        assert spec.is_wildcard is True


class TestDateSpec:
    """Test DateSpec dataclass."""

    def test_date_spec_default(self):
        """Default DateSpec should have wildcard components."""
        ds = DateSpec()
        assert ds.year.is_wildcard is True
        assert ds.month.is_wildcard is True
        assert ds.day.is_wildcard is True

    def test_date_spec_custom_components(self):
        """DateSpec with custom components."""
        year_spec = Spec(values={2024})
        month_spec = Spec(values={3})
        day_spec = Spec(values={15})
        ds = DateSpec(year=year_spec, month=month_spec, day=day_spec)
        assert 2024 in ds.year.values
        assert 3 in ds.month.values
        assert 15 in ds.day.values

    def test_date_spec_post_init(self):
        """DateSpec __post_init__ ensures wildcard for empty components."""
        ds = DateSpec()
        assert ds.year.is_wildcard is True
        assert ds.month.is_wildcard is True
        assert ds.day.is_wildcard is True


class TestTimeSpec:
    """Test TimeSpec dataclass."""

    def test_time_spec_default(self):
        """Default TimeSpec should have wildcard components."""
        ts = TimeSpec()
        assert ts.hour.is_wildcard is True
        assert ts.minute.is_wildcard is True
        assert ts.second.is_wildcard is True

    def test_time_spec_custom_components(self):
        """TimeSpec with custom components."""
        hour_spec = Spec(values={9})
        minute_spec = Spec(values={30})
        second_spec = Spec(values={0})
        ts = TimeSpec(hour=hour_spec, minute=minute_spec, second=second_spec)
        assert 9 in ts.hour.values
        assert 30 in ts.minute.values
        assert 0 in ts.second.values

    def test_time_spec_post_init(self):
        """TimeSpec __post_init__ ensures wildcard for empty components."""
        ts = TimeSpec()
        assert ts.hour.is_wildcard is True
        assert ts.minute.is_wildcard is True
        assert ts.second.is_wildcard is True

    def test_time_spec_partial(self):
        """TimeSpec with partial specification."""
        hour_spec = Spec(values={9, 17})
        ts = TimeSpec(hour=hour_spec)
        assert ts.hour.is_wildcard is False
        assert ts.minute.is_wildcard is True
        assert ts.second.is_wildcard is True


class TestCalendarEvent:
    """Test CalendarEvent dataclass."""

    def test_calendar_event_default(self):
        """Default CalendarEvent should have UTC and all weekdays."""
        ce = CalendarEvent()
        assert ce.timezone == "UTC"
        assert ce.explicit_timezone is False
        assert ce.is_epoch is False
        assert ce.epoch_time is None
        assert ce.weekdays == set(range(7))

    def test_calendar_event_specific_weekdays(self):
        """CalendarEvent with specific weekdays."""
        ce = CalendarEvent(weekdays={0, 4})  # Mon, Fri
        assert 0 in ce.weekdays
        assert 4 in ce.weekdays
        assert 1 not in ce.weekdays

    def test_calendar_event_timezone(self):
        """CalendarEvent with custom timezone."""
        ce = CalendarEvent(timezone="Asia/Tokyo", explicit_timezone=True)
        assert ce.timezone == "Asia/Tokyo"
        assert ce.explicit_timezone is True

    def test_calendar_event_epoch(self):
        """CalendarEvent as epoch timestamp."""
        ce = CalendarEvent(is_epoch=True, epoch_time=1234567890)
        assert ce.is_epoch is True
        assert ce.epoch_time == 1234567890

    def test_calendar_event_original_spec(self):
        """CalendarEvent should preserve original spec."""
        spec_str = "Mon,Fri 09:00:00"
        ce = CalendarEvent(original_spec=spec_str)
        assert ce.original_spec == spec_str

    def test_calendar_event_normalized_all_weekdays(self):
        """Normalized form should omit weekdays if all 7."""
        ce = CalendarEvent(
            weekdays=set(range(7)),
            date=DateSpec(),
            time=TimeSpec(),
        )
        norm = ce.normalized()
        assert norm == "*-*-* *:*:*"

    def test_calendar_event_normalized_specific_weekdays(self):
        """Normalized form should include specific weekdays."""
        ce = CalendarEvent(
            weekdays={0, 4},  # Mon, Fri
            date=DateSpec(),
            time=TimeSpec(),
        )
        norm = ce.normalized()
        assert "Mon" in norm
        assert "Fri" in norm

    def test_calendar_event_normalized_with_timezone(self):
        """Normalized form should include explicit timezone."""
        ce = CalendarEvent(
            timezone="Asia/Tokyo",
            explicit_timezone=True,
            date=DateSpec(),
            time=TimeSpec(),
        )
        norm = ce.normalized()
        assert "Asia/Tokyo" in norm

    def test_calendar_event_normalized_without_timezone(self):
        """Normalized form should omit implicit UTC."""
        ce = CalendarEvent(
            timezone="UTC",
            explicit_timezone=False,
            date=DateSpec(),
            time=TimeSpec(),
        )
        norm = ce.normalized()
        assert "UTC" not in norm

    def test_calendar_event_normalized_epoch(self):
        """Normalized form should use @ for epoch."""
        ce = CalendarEvent(is_epoch=True, epoch_time=1234567890)
        norm = ce.normalized()
        assert norm == "@1234567890"

    def test_calendar_event_normalized_specific_date_time(self):
        """Normalized form should format date and time correctly."""
        year_spec = Spec(values={2024})
        month_spec = Spec(values={3})
        day_spec = Spec(values={15})
        date_spec = DateSpec(year=year_spec, month=month_spec, day=day_spec)

        hour_spec = Spec(values={9})
        minute_spec = Spec(values={30})
        second_spec = Spec(values={0})
        time_spec = TimeSpec(hour=hour_spec, minute=minute_spec, second=second_spec)

        ce = CalendarEvent(date=date_spec, time=time_spec)
        norm = ce.normalized()
        assert "2024" in norm
        assert "03" in norm
        assert "15" in norm
        assert "09" in norm
        assert "30" in norm


class TestCalendarEventNormalizedFormats:
    """Test various normalized output formats."""

    def test_normalized_day_ranges(self):
        """Test normalized output with day ranges."""
        day_spec = Spec(ranges=[(1, 7)])
        date_spec = DateSpec(day=day_spec)
        ce = CalendarEvent(date=date_spec)
        norm = ce.normalized()
        assert "01..07" in norm

    def test_normalized_month_list(self):
        """Test normalized output with month list."""
        month_spec = Spec(values={1, 4, 7, 10})
        date_spec = DateSpec(month=month_spec)
        ce = CalendarEvent(date=date_spec)
        norm = ce.normalized()
        assert "01" in norm
        assert "04" in norm

    def test_normalized_hour_repetition(self):
        """Test normalized output with hour repetition."""
        hour_spec = Spec(values={0}, ranges=[(0, 23)], repetitions=2, start_value=0)
        time_spec = TimeSpec(hour=hour_spec)
        ce = CalendarEvent(time=time_spec)
        norm = ce.normalized()
        # Should contain the range with repetition
        assert "00" in norm

    def test_normalized_compact_format(self):
        """Normalized output should be compact."""
        ce = CalendarEvent(
            weekdays={0, 4},
            date=DateSpec(),
            time=TimeSpec(),
        )
        norm = ce.normalized()
        # Should be single line without extra spaces
        assert "\n" not in norm
        assert "  " not in norm
