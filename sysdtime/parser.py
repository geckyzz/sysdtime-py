"""Parser for systemd calendar event specifications."""

import re
from typing import Set, Tuple

from zoneinfo import ZoneInfo

from .constants import (
    EPOCH_PATTERN,
    TIMEZONE_ALIASES,
    TIMEZONE_PATTERN,
    WEEKDAY_NAMES,
    WEEKDAY_PATTERN,
)
from .types import CalendarEvent, DateSpec, Spec, TimeSpec


class Parser:
    """Parser for systemd calendar event specifications.

    Handles parsing of complete calendar event strings including:
    - Shorthand forms (daily, weekly, etc.)
    - Weekday constraints
    - Date and time specifications
    - Timezone specifications
    - Epoch timestamps

    Example:
        >>> p = Parser('Mon,Fri 09:00:00')
        >>> event = p.parse()
        >>> print(event.normalized())
        Mon,Fri *-*-* 09:00:00
    """

    # Shorthand expressions mapped to canonical form
    SHORTHANDS = {
        "minutely": "*-*-* *:*:00",
        "hourly": "*-*-* *:00:00",
        "daily": "*-*-* 00:00:00",
        "monthly": "*-*-01 00:00:00",
        "weekly": "Mon *-*-* 00:00:00",
        "yearly": "*-01-01 00:00:00",
        "annually": "*-01-01 00:00:00",
        "quarterly": "*-01,04,07,10-01 00:00:00",
        "semiannually": "*-01,07-01 00:00:00",
    }

    def __init__(self, spec_str: str):
        """Initialize parser with specification string.

        Args:
            spec_str: Calendar event specification to parse
        """
        self.spec_str = spec_str.strip()

    def parse(self) -> CalendarEvent:
        """Parse calendar event specification.

        Processes the specification string and extracts all components:
        timezone, weekdays, date, and time. Returns a CalendarEvent object.

        Returns:
            CalendarEvent object with parsed components

        Raises:
            ValueError: For invalid timezone specifications
        """
        spec_str = self.spec_str.strip()

        # Check for epoch timestamp first
        if spec_str.startswith("@"):
            return self._parse_epoch(spec_str)

        # Expand shorthand forms
        if spec_str.lower() in self.SHORTHANDS:
            spec_str = self.SHORTHANDS[spec_str.lower()]

        event = CalendarEvent(original_spec=self.spec_str)

        # Extract components in order: timezone, weekdays, then date/time
        tz_part, spec_str = self._extract_timezone_part(spec_str)
        if tz_part:
            event.timezone = self._parse_timezone(tz_part)
            event.explicit_timezone = True

        weekday_part, spec_str = self._extract_weekday_part(spec_str)
        if weekday_part:
            event.weekdays = self._parse_weekdays(weekday_part)

        parts = spec_str.split()

        # Determine if we have date, time, or both
        if len(parts) >= 2:
            event.date = self._parse_date(parts[0])
            event.time = self._parse_time(parts[1])
        elif len(parts) == 1:
            part = parts[0]
            if ":" in part:
                # Contains colon, it's a time specification
                event.time = self._parse_time(part)
                event.date = DateSpec()
            else:
                # Doesn't contain colon, it's a date specification
                event.date = self._parse_date(part)
                event.time = TimeSpec()

        return event

    def _parse_epoch(self, spec_str: str) -> CalendarEvent:
        """Parse epoch timestamp notation (@seconds-since-epoch).

        Args:
            spec_str: Epoch specification like '@1234567890'

        Returns:
            CalendarEvent with epoch flag and timestamp

        Raises:
            ValueError: If epoch format is invalid
        """
        match = re.match(EPOCH_PATTERN, spec_str)
        if not match:
            raise ValueError("Invalid epoch format: {0}".format(spec_str))

        epoch_time = int(match.group(1))
        event = CalendarEvent(original_spec=self.spec_str, is_epoch=True, epoch_time=epoch_time)
        return event

    def _extract_timezone_part(self, spec: str) -> Tuple[str, str]:
        """Extract timezone specification from end of string.

        Timezone must be at the end of the specification, after a space.

        Args:
            spec: Specification string

        Returns:
            Tuple of (timezone_name, remaining_spec)
        """
        spec = spec.strip()
        match = re.search(TIMEZONE_PATTERN, spec)
        if match:
            tz = match.group(2)
            rest = spec[: match.start()].strip()
            return tz, rest
        return "", spec

    def _extract_weekday_part(self, spec: str) -> Tuple[str, str]:
        """Extract weekday specification from beginning of string.

        Weekday specification must be followed by whitespace or date/time.
        Handles single days, ranges (Mon..Fri), and comma-separated lists.

        Args:
            spec: Specification string

        Returns:
            Tuple of (weekday_spec, remaining_spec)
        """
        spec = spec.strip()
        match = re.match(WEEKDAY_PATTERN, spec, re.IGNORECASE)
        if match:
            weekday_part = match.group(0).strip()
            rest = spec[match.end() :].strip()
            return weekday_part, rest
        return "", spec

    def _parse_weekdays(self, weekday_str: str) -> Set[int]:
        """Parse weekday specification into set of indices.

        Supports:
        - Single days: Mon, Tue, etc.
        - Ranges: Mon..Fri
        - Lists: Mon,Wed,Fri
        - Mixed: Mon,Wed..Fri,Sun

        Args:
            weekday_str: Weekday specification string

        Returns:
            Set of weekday indices (0=Mon, 6=Sun)
        """
        weekday_str = weekday_str.lower().strip()
        result = set()

        # Split on commas first, then handle ranges
        comma_parts = weekday_str.split(",")

        for comma_part in comma_parts:
            comma_part = comma_part.strip()
            if ".." in comma_part:
                # Handle range like "Mon..Fri"
                range_parts = comma_part.split("..")
                if len(range_parts) == 2:
                    start_str = range_parts[0].strip()
                    end_str = range_parts[1].strip()
                    if start_str in WEEKDAY_NAMES and end_str in WEEKDAY_NAMES:
                        start_day = WEEKDAY_NAMES[start_str]
                        end_day = WEEKDAY_NAMES[end_str]
                        for d in range(start_day, end_day + 1):
                            result.add(d)
            elif comma_part in WEEKDAY_NAMES:
                result.add(WEEKDAY_NAMES[comma_part])

        return result if result else set(range(7))

    def _parse_timezone(self, tz_str: str) -> str:
        """Parse and validate timezone specification.

        Accepts IANA timezone names, UTC, and regional aliases.

        Args:
            tz_str: Timezone name to parse

        Returns:
            Validated timezone string

        Raises:
            ValueError: If timezone is invalid
        """
        tz_str = tz_str.strip()
        if tz_str in TIMEZONE_ALIASES:
            return tz_str
        try:
            ZoneInfo(tz_str)
            return tz_str
        except Exception as e:
            if tz_str == "UTC":
                return "UTC"
            raise ValueError("Invalid timezone: {0}".format(tz_str)) from e

    def _parse_date(self, date_str: str) -> DateSpec:
        """Parse date specification (YYYY-MM-DD with wildcards/ranges/etc).

        Handles:
        - Wildcards: *, *-03, *-*-15
        - Specific values: 2024, 2024-03-15
        - Ranges: *-01..03, *-*-1..7
        - Lists: *-01,04,07,10, *-*-1,15
        - Repetitions: *-*-1/7
        - Last-day: *~, *-02~03

        Args:
            date_str: Date specification string

        Returns:
            DateSpec object with parsed components
        """
        date_str = date_str.strip()

        # Handle missing dashes
        if "-" not in date_str:
            if date_str.isdigit() and len(date_str) <= 2:
                date_str = "*-*-{0}".format(date_str)
            else:
                date_str = "*-{0}".format(date_str)

        # Parse tilde (last-day) syntax carefully
        components = date_str.split("-")
        parts = []

        for comp in components:
            if "~" in comp:
                # Component contains ~, split it into month and day
                month_part, day_part = comp.split("~", 1)
                if month_part or len(parts) > 0:
                    parts.append(month_part)
                parts.append("~" + day_part)
            else:
                parts.append(comp)

        # Pad to ensure we have year, month, day
        if len(parts) < 3:
            while len(parts) < 3:
                parts.insert(0, "*")

        year_spec = self._parse_spec(parts[0], 1970, 2099)
        month_spec = self._parse_spec(parts[1], 1, 12)
        day_spec = self._parse_spec(parts[2], 1, 31, allow_last_day=True)

        return DateSpec(year=year_spec, month=month_spec, day=day_spec)

    def _parse_time(self, time_str: str) -> TimeSpec:
        """Parse time specification (HH:MM:SS with wildcards/ranges/etc).

        Handles:
        - Wildcards: *, *:00, *:30:00
        - Partial times: 09, 09:30 (seconds default to :00)
        - Ranges: 09..17:00:00
        - Lists: 09,17:00:00
        - Repetitions: */2:00:00

        Args:
            time_str: Time specification string

        Returns:
            TimeSpec object with parsed components
        """
        time_str = time_str.strip()

        # Add missing components
        if time_str.count(":") == 0:
            time_str = "{0}:00:00".format(time_str)
        elif time_str.count(":") == 1:
            time_str = "{0}:00".format(time_str)

        parts = time_str.split(":")
        if len(parts) < 3:
            while len(parts) < 3:
                parts.append("00")

        hour_spec = self._parse_spec(parts[0], 0, 23)
        minute_spec = self._parse_spec(parts[1], 0, 59)
        second_spec = self._parse_spec(parts[2], 0, 59)

        return TimeSpec(hour=hour_spec, minute=minute_spec, second=second_spec)

    def _parse_spec(
        self,
        spec_str: str,
        min_val: int,
        max_val: int,
        allow_last_day: bool = False,
    ) -> Spec:
        """Parse a single specification component.

        Handles:
        - Wildcards: *
        - Exact values: 5, 15
        - Lists: 1,5,15
        - Ranges: 1..7, 9..17
        - Repetitions: 1/7, 9..17/2
        - Last-day syntax (dates only): ~, 02~03

        Args:
            spec_str: Specification string to parse
            min_val: Minimum valid value
            max_val: Maximum valid value
            allow_last_day: If True, enables ~ syntax for last-day

        Returns:
            Spec object with parsed values, ranges, and flags
        """
        spec_str = spec_str.strip()

        spec = Spec()

        # Handle wildcards
        if spec_str == "*":
            spec.is_wildcard = True
            return spec

        # Handle last-day syntax (e.g., ~ or 02~03)
        if allow_last_day and "~" in spec_str:
            spec.is_last_day = True
            spec_str = spec_str.replace("~", "")
            if spec_str:
                try:
                    spec.last_day_offset = int(spec_str)
                except ValueError:
                    spec.last_day_offset = 0
            return spec

        # Parse comma-separated parts
        parts = spec_str.split(",")

        for part in parts:
            if ".." in part:
                # Range syntax: 1..7 or 1..7/2
                range_parts = part.split("..")
                if len(range_parts) == 2:
                    start_str, end_str = range_parts
                    rep_match = re.match(r"(.+)/(\d+)", end_str)
                    if rep_match:
                        end_str = rep_match.group(1)
                        spec.repetitions = int(rep_match.group(2))

                    try:
                        start = int(start_str)
                        end = int(end_str)
                        spec.ranges.append((start, end))
                        spec.start_value = start
                    except ValueError:
                        pass
            elif "/" in part:
                # Repetition syntax: 1/7 (every 7 starting from 1)
                rep_match = re.match(r"(\d+)/(\d+)", part)
                if rep_match:
                    start = int(rep_match.group(1))
                    spec.start_value = start
                    spec.repetitions = int(rep_match.group(2))
                    spec.values.add(start)
                else:
                    try:
                        val = int(part)
                        spec.values.add(val)
                    except ValueError:
                        pass
            else:
                # Simple integer value
                try:
                    val = int(part)
                    spec.values.add(val)
                except ValueError:
                    pass

        # Default to wildcard if nothing matched
        if not spec.values and not spec.ranges:
            spec.is_wildcard = True

        return spec
