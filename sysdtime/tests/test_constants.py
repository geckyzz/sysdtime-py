"""Tests for constants and configuration."""

import re

from sysdtime.constants import (
    EPOCH_PATTERN,
    MAX_SEARCH_ITERATIONS,
    MAX_YEAR,
    MIN_YEAR,
    TIMEZONE_ALIASES,
    TIMEZONE_PATTERN,
    WEEKDAY_NAMES,
    WEEKDAY_PATTERN,
    WEEKDAY_SHORT,
)


class TestTimezoneAliases:
    """Test timezone alias mappings."""

    def test_utc_alias(self):
        """UTC should map to UTC."""
        assert TIMEZONE_ALIASES["UTC"] == "UTC"

    def test_indonesia_aliases(self):
        """Indonesian timezone aliases should map correctly."""
        assert TIMEZONE_ALIASES["WIB"] == "Asia/Jakarta"
        assert TIMEZONE_ALIASES["WITA"] == "Asia/Makassar"
        assert TIMEZONE_ALIASES["WIT"] == "Asia/Jayapura"

    def test_japan_alias(self):
        """JST should map to Asia/Tokyo."""
        assert TIMEZONE_ALIASES["JST"] == "Asia/Tokyo"

    def test_all_aliases_have_values(self):
        """All aliases should have non-empty values."""
        for alias, tz in TIMEZONE_ALIASES.items():
            assert isinstance(alias, str)
            assert isinstance(tz, str)
            assert len(alias) > 0
            assert len(tz) > 0


class TestWeekdayConstants:
    """Test weekday name constants."""

    def test_weekday_short_length(self):
        """WEEKDAY_SHORT should have exactly 7 entries."""
        assert len(WEEKDAY_SHORT) == 7

    def test_weekday_short_values(self):
        """WEEKDAY_SHORT should be 3-letter abbreviations."""
        expected = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        assert WEEKDAY_SHORT == expected

    def test_weekday_names_mapping_full(self):
        """Full weekday names should map to correct indices."""
        assert WEEKDAY_NAMES["monday"] == 0
        assert WEEKDAY_NAMES["tuesday"] == 1
        assert WEEKDAY_NAMES["wednesday"] == 2
        assert WEEKDAY_NAMES["thursday"] == 3
        assert WEEKDAY_NAMES["friday"] == 4
        assert WEEKDAY_NAMES["saturday"] == 5
        assert WEEKDAY_NAMES["sunday"] == 6

    def test_weekday_names_mapping_short(self):
        """Short weekday names should map to correct indices."""
        assert WEEKDAY_NAMES["mon"] == 0
        assert WEEKDAY_NAMES["tue"] == 1
        assert WEEKDAY_NAMES["wed"] == 2
        assert WEEKDAY_NAMES["thu"] == 3
        assert WEEKDAY_NAMES["fri"] == 4
        assert WEEKDAY_NAMES["sat"] == 5
        assert WEEKDAY_NAMES["sun"] == 6

    def test_weekday_names_complete(self):
        """All 14 weekday name mappings should exist."""
        assert len(WEEKDAY_NAMES) == 14  # 7 full + 7 short

    def test_weekday_names_case_insensitive(self):
        """All weekday names should be lowercase in mapping."""
        for key in WEEKDAY_NAMES.keys():
            assert key == key.lower()


class TestPatterns:
    """Test regex patterns."""

    def test_timezone_pattern_utc(self):
        """Timezone pattern should match UTC."""
        match = re.search(TIMEZONE_PATTERN, "*-*-* 12:00:00 UTC")
        assert match is not None
        assert match.group(2) == "UTC"

    def test_timezone_pattern_iana(self):
        """Timezone pattern should match IANA names."""
        match = re.search(TIMEZONE_PATTERN, "*-*-* 12:00:00 Asia/Tokyo")
        assert match is not None
        assert match.group(2) == "Asia/Tokyo"

    def test_timezone_pattern_alias(self):
        """Timezone pattern should match aliases."""
        match = re.search(TIMEZONE_PATTERN, "*-*-* 12:00:00 WIB")
        assert match is not None
        assert match.group(2) == "WIB"

    def test_timezone_pattern_underscore(self):
        """Timezone pattern should handle underscores."""
        match = re.search(TIMEZONE_PATTERN, "*-*-* 12:00:00 America/New_York")
        assert match is not None
        assert match.group(2) == "America/New_York"

    def test_timezone_pattern_hyphen(self):
        """Timezone pattern should handle hyphens."""
        match = re.search(TIMEZONE_PATTERN, "*-*-* 12:00:00 America/Los-Angeles")
        assert match is not None
        assert match.group(2) == "America/Los-Angeles"

    def test_timezone_pattern_no_match_empty(self):
        """Timezone pattern should not match without timezone."""
        match = re.search(TIMEZONE_PATTERN, "*-*-* 12:00:00")
        assert match is None

    def test_weekday_pattern_single(self):
        """Weekday pattern should match single day."""
        match = re.match(WEEKDAY_PATTERN, "Mon *-*-* 12:00:00", re.IGNORECASE)
        assert match is not None

    def test_weekday_pattern_range(self):
        """Weekday pattern should match range."""
        match = re.match(WEEKDAY_PATTERN, "Mon..Fri *-*-* 12:00:00", re.IGNORECASE)
        assert match is not None

    def test_weekday_pattern_list(self):
        """Weekday pattern should match comma-separated list."""
        match = re.match(WEEKDAY_PATTERN, "Mon,Wed,Fri *-*-* 12:00:00", re.IGNORECASE)
        assert match is not None

    def test_weekday_pattern_mixed(self):
        """Weekday pattern should match mixed ranges and singles."""
        match = re.match(WEEKDAY_PATTERN, "Mon..Wed,Fri,Sun *-*-* 12:00:00", re.IGNORECASE)
        assert match is not None

    def test_weekday_pattern_case_insensitive(self):
        """Weekday pattern should be case-insensitive."""
        match = re.match(WEEKDAY_PATTERN, "MON,FRI *-*-* 12:00:00", re.IGNORECASE)
        assert match is not None

    def test_weekday_pattern_short_names(self):
        """Weekday pattern should match short names."""
        match = re.match(WEEKDAY_PATTERN, "Mon,Fri *-*-* 12:00:00", re.IGNORECASE)
        assert match is not None

    def test_weekday_pattern_full_names(self):
        """Weekday pattern should match full names."""
        match = re.match(WEEKDAY_PATTERN, "Monday,Friday *-*-* 12:00:00", re.IGNORECASE)
        assert match is not None

    def test_epoch_pattern_valid(self):
        """Epoch pattern should match valid epoch timestamps."""
        match = re.match(EPOCH_PATTERN, "@1234567890")
        assert match is not None
        assert match.group(1) == "1234567890"

    def test_epoch_pattern_zero(self):
        """Epoch pattern should match zero."""
        match = re.match(EPOCH_PATTERN, "@0")
        assert match is not None

    def test_epoch_pattern_large_number(self):
        """Epoch pattern should match large numbers."""
        match = re.match(EPOCH_PATTERN, "@2147483647")
        assert match is not None

    def test_epoch_pattern_no_match_negative(self):
        """Epoch pattern should not match negative numbers."""
        match = re.match(EPOCH_PATTERN, "@-123")
        assert match is None

    def test_epoch_pattern_no_match_no_at(self):
        """Epoch pattern should require @ prefix."""
        match = re.match(EPOCH_PATTERN, "1234567890")
        assert match is None


class TestConstants:
    """Test constant values."""

    def test_min_year(self):
        """MIN_YEAR should be 1970 (Unix epoch)."""
        assert MIN_YEAR == 1970

    def test_max_year(self):
        """MAX_YEAR should be 2099."""
        assert MAX_YEAR == 2099

    def test_year_range(self):
        """Year range should be reasonable."""
        assert MIN_YEAR < MAX_YEAR
        assert MAX_YEAR - MIN_YEAR == 129

    def test_max_search_iterations(self):
        """MAX_SEARCH_ITERATIONS should represent approximately 1 year."""
        # 366 days * 24 hours * 60 minutes * 60 seconds
        expected = 366 * 24 * 60 * 60
        assert MAX_SEARCH_ITERATIONS == expected

    def test_max_search_iterations_type(self):
        """MAX_SEARCH_ITERATIONS should be an integer."""
        assert isinstance(MAX_SEARCH_ITERATIONS, int)
        assert MAX_SEARCH_ITERATIONS > 0
