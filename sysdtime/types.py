"""Data structures for calendar event specifications."""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

from .constants import WEEKDAY_SHORT


@dataclass
class Spec:
    """Represents a specification component (date, time, or weekday).

    A spec can match values in several ways:
    - Wildcard (*): matches any value
    - Exact values: fixed set of integers
    - Ranges: start..end inclusive
    - Repetitions: start/step pattern
    - Last-day syntax: ~offset for days from end of month

    Attributes:
        values: Set of specific integer values to match
        ranges: List of (start, end) tuples for range matching
        repetitions: Step size for repetition patterns
        start_value: Starting value for repetition patterns
        is_wildcard: True if matches any value
        is_last_day: True if using last-day-of-month syntax
        last_day_offset: Offset from end of month (e.g., 3 = 3rd to last)
    """

    values: Set[int] = field(default_factory=set)
    ranges: List[Tuple[int, int]] = field(default_factory=list)
    repetitions: Optional[int] = None
    start_value: Optional[int] = None
    is_wildcard: bool = False
    is_last_day: bool = False
    last_day_offset: Optional[int] = None

    def matches(self, value: int) -> bool:
        """Check if a single value matches this spec.

        Args:
            value: Integer value to check

        Returns:
            True if value matches, False otherwise
        """
        if self.is_wildcard:
            return True
        if value in self.values:
            return True
        for start, end in self.ranges:
            if start <= value <= end:
                return True
        return False

    def matches_with_repetition(self, value: int, max_value: int) -> bool:
        """Check if value matches considering repetition patterns.

        For patterns like 1/7 (every 7 days starting from 1st), checks:
        - Exact value matches
        - Range membership
        - Repetition: (value - start) % step == 0

        Args:
            value: Integer value to check
            max_value: Maximum valid value for boundary checking

        Returns:
            True if value matches, False otherwise
        """
        if self.is_wildcard:
            return True
        if not self.repetitions:
            return self.matches(value)
        if self.start_value is not None:
            if value < self.start_value or value > max_value:
                return False
            return (value - self.start_value) % self.repetitions == 0
        return value % self.repetitions == 0


def _ensure_wildcard_if_empty(spec: Spec) -> None:
    """Helper to set wildcard flag if spec has no values or ranges.

    Args:
        spec: Spec object to update
    """
    if not spec.is_wildcard and not spec.values and not spec.ranges:
        spec.is_wildcard = True


@dataclass
class DateSpec:
    """Represents a date specification (year-month-day).

    Attributes:
        year: Spec for year component
        month: Spec for month component (1-12)
        day: Spec for day component (1-31, with last-day support)
    """

    year: Spec = field(default_factory=Spec)
    month: Spec = field(default_factory=Spec)
    day: Spec = field(default_factory=Spec)

    def __post_init__(self):
        """Ensure all components default to wildcard if empty."""
        _ensure_wildcard_if_empty(self.year)
        _ensure_wildcard_if_empty(self.month)
        _ensure_wildcard_if_empty(self.day)


@dataclass
class TimeSpec:
    """Represents a time specification (hour:minute:second).

    Attributes:
        hour: Spec for hour component (0-23)
        minute: Spec for minute component (0-59)
        second: Spec for second component (0-59)
    """

    hour: Spec = field(default_factory=Spec)
    minute: Spec = field(default_factory=Spec)
    second: Spec = field(default_factory=Spec)

    def __post_init__(self):
        """Ensure all components default to wildcard if empty."""
        _ensure_wildcard_if_empty(self.hour)
        _ensure_wildcard_if_empty(self.minute)
        _ensure_wildcard_if_empty(self.second)


def _format_spec(spec: Spec, pad_width: Optional[int] = None) -> str:
    """Format a spec for display in normalized output.

    Args:
        spec: Spec object to format
        pad_width: Width to pad numeric values (e.g., 2 for '01')

    Returns:
        Formatted specification string
    """
    if spec.is_wildcard:
        return "*"
    if spec.values:
        values_str = ",".join(
            str(v).zfill(pad_width) if pad_width else str(v) for v in sorted(spec.values)
        )
        return values_str
    if spec.ranges:
        parts = []
        for start, end in spec.ranges:
            if start == end:
                val_str = str(start).zfill(pad_width) if pad_width else str(start)
                parts.append(val_str)
            else:
                start_str = str(start).zfill(pad_width) if pad_width else str(start)
                end_str = str(end).zfill(pad_width) if pad_width else str(end)
                if spec.repetitions:
                    parts.append("{0}..{1}/{2}".format(start_str, end_str, spec.repetitions))
                else:
                    parts.append("{0}..{1}".format(start_str, end_str))
        return ",".join(parts)
    return "*"


@dataclass
class CalendarEvent:
    """Complete calendar event specification.

    Represents a fully parsed calendar event that can be matched against
    datetimes and used to find next occurrences.

    Attributes:
        weekdays: Set of weekday indices (0=Mon, 6=Sun) that match
        date: DateSpec for date component matching
        time: TimeSpec for time component matching
        timezone: Timezone name (e.g., 'UTC', 'Asia/Tokyo')
        explicit_timezone: True if timezone was explicitly specified
        is_epoch: True if this is a one-off epoch timestamp
        epoch_time: Unix timestamp (seconds since epoch) if is_epoch=True
        original_spec: Original specification string for reference
    """

    weekdays: Set[int] = field(default_factory=lambda: set(range(7)))
    date: DateSpec = field(default_factory=DateSpec)
    time: TimeSpec = field(default_factory=TimeSpec)
    timezone: str = "UTC"
    explicit_timezone: bool = False
    is_epoch: bool = False
    epoch_time: Optional[int] = None
    original_spec: str = ""

    def normalized(self) -> str:
        """Return normalized form of calendar event.

        Converts the parsed event into a canonical string representation
        that follows systemd.time(7) format conventions.

        Returns:
            Normalized specification string (e.g., 'Mon,Fri *-*-* 09:00:00')
        """
        if self.is_epoch:
            return "@{0}".format(self.epoch_time)

        weekday_part = ""
        if len(self.weekdays) < 7:
            weekday_list = sorted(self.weekdays)
            weekday_part = ",".join(WEEKDAY_SHORT[i] for i in weekday_list) + " "

        year_str = (
            "*" if self.date.year.is_wildcard else _format_spec(self.date.year, pad_width=None)
        )
        month_str = (
            "*" if self.date.month.is_wildcard else _format_spec(self.date.month, pad_width=2)
        )
        day_str = "*" if self.date.day.is_wildcard else _format_spec(self.date.day, pad_width=2)
        date_part = "{0}-{1}-{2}".format(year_str, month_str, day_str)

        hour_str = "*" if self.time.hour.is_wildcard else _format_spec(self.time.hour, pad_width=2)
        minute_str = (
            "*" if self.time.minute.is_wildcard else _format_spec(self.time.minute, pad_width=2)
        )
        second_str = (
            "*" if self.time.second.is_wildcard else _format_spec(self.time.second, pad_width=2)
        )
        time_part = "{0}:{1}:{2}".format(hour_str, minute_str, second_str)

        tz_part = " {0}".format(self.timezone) if self.explicit_timezone else ""
        return "{0}{1} {2}{3}".format(weekday_part, date_part, time_part, tz_part).rstrip()
