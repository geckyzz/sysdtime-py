"""Timestamp parser for systemd timestamp specifications."""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from zoneinfo import ZoneInfo

from .constants import TIMEZONE_ALIASES


class TimestampParser:
    """Parser for systemd timestamp specifications.

    Handles parsing of absolute and relative timestamps including:
    - Special tokens: now, today, yesterday, tomorrow
    - Relative expressions: +3h, -5s, 11min ago
    - Absolute timestamps with ISO 8601 T separator and RFC 3339 offsets
    - Standard date/time formats
    """

    # Time unit patterns (all systemd-supported units)
    TIMESPAN_PATTERN = re.compile(r"([-+]?\d+(?:\.\d+)?)\s*([a-zA-Z]+)")

    # Time unit conversions to seconds
    TIME_UNITS = {
        "usec": 1e-6,
        "us": 1e-6,
        "μs": 1e-6,
        "msec": 1e-3,
        "ms": 1e-3,
        "seconds": 1,
        "second": 1,
        "sec": 1,
        "s": 1,
        "minutes": 60,
        "minute": 60,
        "min": 60,
        "m": 60,
        "hours": 3600,
        "hour": 3600,
        "hr": 3600,
        "h": 3600,
        "days": 86400,
        "day": 86400,
        "d": 86400,
        "weeks": 604800,
        "week": 604800,
        "w": 604800,
        "months": 2629746,
        "month": 2629746,
        "M": 2629746,  # 30.44 days
        "years": 31556952,
        "year": 31556952,
        "y": 31556952,  # 365.25 days
    }

    # RFC 3339 timezone offset pattern
    TZ_OFFSET_PATTERN = re.compile(r"([+-])(\d{1,2}):?(\d{2})?")

    def __init__(self, spec_str: str, base_time: Optional[datetime] = None):
        """Initialize timestamp parser.

        Args:
            spec_str: Timestamp specification string
            base_time: Reference time for relative expressions (defaults to now)
        """
        self.spec_str = spec_str.strip()
        self.base_time = base_time or datetime.now(tz=timezone.utc)

    def parse(self) -> datetime:
        """Parse timestamp specification into datetime object.

        Supports:
        - Special tokens: now, today, yesterday, tomorrow
        - Relative expressions: +3h, -5s, 11min ago
        - Absolute timestamps with optional T separator and timezone

        Returns:
            Parsed datetime object with timezone information

        Raises:
            ValueError: For invalid timestamp specifications
        """
        # First check for special tokens (case-insensitive)
        spec_lower = self.spec_str.lower()

        # Handle special time tokens
        if spec_lower == "now":
            return self.base_time
        elif spec_lower == "today":
            return self.base_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif spec_lower == "yesterday":
            yesterday = self.base_time - timedelta(days=1)
            return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        elif spec_lower == "tomorrow":
            tomorrow = self.base_time + timedelta(days=1)
            return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

        # Handle relative timestamps: +3h30min, -5s, 11min ago (case-sensitive for units!)
        if self.spec_str.startswith("+") or self.spec_str.startswith("-"):
            return self._parse_relative(self.spec_str)

        if spec_lower.endswith(" ago"):
            return self._parse_relative("-" + self.spec_str[:-4])

        # Handle absolute timestamps (ISO 8601 with T separator, RFC 3339, etc.)
        return self._parse_absolute(self.spec_str)

    def _parse_relative(self, expr: str) -> datetime:
        """Parse relative time expression like +3h30min or -5s.

        Args:
            expr: Expression starting with + or -, e.g., '+3h30min', '-5s'

        Returns:
            Calculated datetime

        Raises:
            ValueError: For invalid timespan
        """
        sign = 1 if expr[0] == "+" else -1
        timespan_str = expr[1:]

        total_seconds = 0.0
        matches = self.TIMESPAN_PATTERN.findall(timespan_str)

        if not matches:
            raise ValueError("Invalid relative timestamp: {0}".format(expr))

        for value_str, unit_str in matches:
            # First check exact match (case-sensitive for 'M' month)
            if unit_str in self.TIME_UNITS:
                unit_seconds = self.TIME_UNITS[unit_str]
            else:
                # Then try case-insensitive match
                unit_lower = unit_str.lower()
                if unit_lower not in self.TIME_UNITS:
                    raise ValueError("Unknown time unit: {0}".format(unit_str))
                unit_seconds = self.TIME_UNITS[unit_lower]

            value = float(value_str)
            total_seconds += value * unit_seconds

        delta = timedelta(seconds=sign * total_seconds)
        return self.base_time + delta

    def _parse_absolute(self, spec: str) -> datetime:
        """Parse absolute timestamp specification.

        Supports:
        - ISO 8601 with T separator: 2024-03-15T10:30:00
        - RFC 3339 with offset: 2024-03-15T10:30:00+01:00
        - Standard format: 2024-03-15 10:30:00 UTC

        Args:
            spec: Timestamp string

        Returns:
            Parsed datetime with timezone

        Raises:
            ValueError: For invalid format
        """
        # Replace T with space for consistency
        spec = spec.replace("T", " ")

        # Extract timezone from end
        tz_info = None
        # Try RFC 3339 offset format first (Z, +HH:MM, -HH:MM)
        if spec.endswith("Z"):
            tz_info = timezone.utc
            spec = spec[:-1].strip()
        else:
            # Check for RFC 3339 timezone offset
            offset_match = re.search(r"([+-]\d{2}:?\d{2})$", spec)
            if offset_match:
                tz_str = offset_match.group(1)
                spec = spec[: offset_match.start()].strip()
                tz_info = self._parse_timezone_offset(tz_str)

        # Extract timezone name if present (IANA or alias)
        parts = spec.rsplit(None, 1)
        if len(parts) == 2 and not parts[1][0].isdigit():
            spec_part, tz_name = parts
            # Check if it's a timezone
            if tz_name in TIMEZONE_ALIASES or self._is_valid_timezone(tz_name):
                spec = spec_part
                if not tz_info:
                    tz_info = self._parse_timezone(tz_name)

        # Default to UTC if no timezone specified
        if not tz_info:
            tz_info = timezone.utc

        # Parse the date/time part
        dt = self._parse_datetime_components(spec)

        # Apply timezone
        return dt.replace(tzinfo=tz_info)

    def _parse_timezone_offset(self, tz_offset: str) -> timezone:
        """Parse RFC 3339 timezone offset like +01:00 or -05:30.

        Args:
            tz_offset: Offset string, e.g., '+01:00', '-05:30'

        Returns:
            timezone object

        Raises:
            ValueError: For invalid offset format
        """
        match = self.TZ_OFFSET_PATTERN.match(tz_offset)
        if not match:
            raise ValueError("Invalid timezone offset: {0}".format(tz_offset))

        sign = 1 if match.group(1) == "+" else -1
        hours = int(match.group(2))
        minutes = int(match.group(3) or 0)

        offset_seconds = sign * (hours * 3600 + minutes * 60)
        return timezone(timedelta(seconds=offset_seconds))

    def _parse_timezone(self, tz_str: str) -> timezone:
        """Parse IANA or alias timezone name.

        Args:
            tz_str: Timezone name, e.g., 'UTC', 'Asia/Tokyo', 'WIB'

        Returns:
            timezone object
        """
        if tz_str in TIMEZONE_ALIASES:
            tz_str = TIMEZONE_ALIASES[tz_str]

        if tz_str == "UTC":
            return timezone.utc

        return timezone(ZoneInfo(tz_str))

    def _is_valid_timezone(self, tz_str: str) -> bool:
        """Check if string is a valid timezone name.

        Args:
            tz_str: Timezone name to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            ZoneInfo(tz_str)
            return True
        except Exception:
            return False

    def _parse_datetime_components(self, spec: str) -> datetime:
        """Parse date and time components.

        Handles:
        - Full: 2024-03-15 10:30:45
        - Date only: 2024-03-15
        - Time only: 10:30:45 or 10:30 or 10
        - Weekday: Fri 2024-03-15 10:30:00 (weekday ignored for parsing)

        Args:
            spec: Date/time specification string

        Returns:
            Parsed datetime (with default timezone UTC if not set)
        """
        spec = spec.strip()

        # Remove weekday prefix if present
        weekday_pattern = r"^(?:Mon|Monday|Tue|Tuesday|Wed|Wednesday|Thu|Thursday|Fri|Friday|Sat|Saturday|Sun|Sunday)\s+"
        spec = re.sub(weekday_pattern, "", spec, flags=re.IGNORECASE)

        # Split into date and time parts
        parts = spec.split()
        date_part = None
        time_part = None

        for part in parts:
            if ":" in part:
                # This is time (HH:MM:SS or HH:MM or HH)
                time_part = part
            elif "-" in part and part.count("-") == 2:
                # This is date (YYYY-MM-DD)
                date_part = part
            elif part.isdigit() and 1 <= len(part) <= 2:
                # 1-2 digits: hour (HH)
                time_part = part
            elif part.isdigit() and 4 <= len(part) <= 8:
                # Could be YYYY, MMDD, YYYYMMDD
                if len(part) == 4:
                    # Year only - not valid, need date
                    pass
                else:
                    date_part = part

        # Parse date
        if date_part:
            try:
                if "-" in date_part:
                    dt = datetime.strptime(date_part, "%Y-%m-%d")
                else:
                    raise ValueError("Invalid date format: {0}".format(date_part))
            except ValueError as err:
                raise ValueError("Invalid date: {0}".format(date_part)) from err
        else:
            # Default to today
            dt = self.base_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # Parse time
        if time_part:
            try:
                # Handle fractional seconds
                if "." in time_part:
                    time_part = time_part.split(".")[0]

                # Pad with :00 if needed
                time_parts = time_part.split(":")
                while len(time_parts) < 3:
                    time_parts.append("00")
                time_part = ":".join(time_parts[:3])

                time_obj = datetime.strptime(time_part, "%H:%M:%S").time()
                dt = dt.replace(hour=time_obj.hour, minute=time_obj.minute, second=time_obj.second)
            except ValueError as err:
                raise ValueError("Invalid time: {0}".format(time_part)) from err

        return dt


def parse_timestamp(
    spec_str: str,
    base_time: Optional[datetime] = None,
) -> datetime:
    """Parse a timestamp specification into a datetime object.

    Supports systemd.time(7) timestamp formats:
    - Special tokens: now, today, yesterday, tomorrow
    - Relative expressions: +3h, -5s, 11min ago
    - Absolute timestamps: 2024-03-15 10:30:00 UTC
    - ISO 8601: 2024-03-15T10:30:00
    - RFC 3339: 2024-03-15T10:30:00+01:00 or 2024-03-15T10:30:00Z

    Args:
        spec_str: Timestamp specification
        base_time: Reference time for relative expressions (defaults to now)

    Returns:
        Parsed datetime with timezone information

    Raises:
        ValueError: For invalid timestamp specifications

    Example:
        >>> from datetime import datetime, timezone
        >>> dt = parse_timestamp('today')
        >>> dt.hour, dt.minute, dt.second
        (0, 0, 0)

        >>> dt = parse_timestamp('+3h', datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc))
        >>> dt
        datetime.datetime(2024, 3, 15, 13, 0, tzinfo=datetime.timezone.utc)

        >>> dt = parse_timestamp('2024-03-15T10:30:00+01:00')
        >>> dt.tzinfo
        datetime.timezone(datetime.timedelta(seconds=3600))
    """
    parser = TimestampParser(spec_str, base_time)
    return parser.parse()
