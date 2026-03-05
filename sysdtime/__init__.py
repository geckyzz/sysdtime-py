"""Pure Python systemd calendar event parser

Parses calendar event specifications as defined in systemd.time(7).
Supports:
- Weekday constraints (Mon, Tue, Mon..Fri, Mon,Wed,Fri, etc.)
- Date specifications with wildcards, ranges, lists, and repetitions
- Time specifications with full feature support
- Last-day-of-month syntax (~)
- Epoch timestamps (@seconds-since-epoch format)
- Timezone support (IANA, UTC, and regional: WIB, WITA, WIT, JST)
- Shorthand forms (daily, weekly, hourly, etc.)

Example:
    >>> from sysdtime import parse, matches, next_occurrence
    >>> from datetime import datetime, timezone
    >>>
    >>> # Parse and normalize
    >>> event = parse('Mon,Fri 09:00:00')
    >>> print(event.normalized())
    Mon,Fri *-*-* 09:00:00
    >>>
    >>> # Check if datetime matches
    >>> dt = datetime(2024, 3, 15, 9, 0, 0, tzinfo=timezone.utc)
    >>> matches('Mon,Fri 09:00:00', dt)
    True
    >>>
    >>> # Find next occurrence
    >>> next_dt = next_occurrence('daily', dt)
    >>> print(next_dt)
    2024-03-16 00:00:00+00:00
"""

from datetime import datetime
from typing import Optional

from .matcher import Matcher
from .parser import Parser
from .searcher import NextOccurrence
from .timestamp import TimestampParser, parse_timestamp
from .types import CalendarEvent

__all__ = [
    "CalendarEvent",
    "Matcher",
    "NextOccurrence",
    "Parser",
    "TimestampParser",
    "matches",
    "next_occurrence",
    "parse",
    "parse_timestamp",
]


def parse(spec_str: str) -> CalendarEvent:
    """Parse a calendar event specification string.

    Args:
        spec_str: Calendar event specification (e.g., 'daily', 'Mon,Fri 09:00:00')

    Returns:
        CalendarEvent object with parsed components

    Raises:
        ValueError: For invalid timezone specifications

    Example:
        >>> event = parse('Mon,Fri 09:00:00')
        >>> print(event.normalized())
        Mon,Fri *-*-* 09:00:00
    """
    return Parser(spec_str).parse()


def matches(spec_str: str, dt: datetime) -> bool:
    """Check if a datetime matches a calendar event specification.

    Args:
        spec_str: Calendar event specification
        dt: datetime object to check (should have timezone info)

    Returns:
        True if dt matches the specification, False otherwise

    Example:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2024, 3, 15, 9, 0, 0, tzinfo=timezone.utc)
        >>> matches('Mon,Fri 09:00:00', dt)
        True
    """
    event = parse(spec_str)
    if event.is_epoch:
        return False  # Epoch timestamps don't match datetimes
    matcher = Matcher(event)
    return matcher.matches(dt)


def next_occurrence(
    spec_str: str,
    from_dt: Optional[datetime] = None,
) -> Optional[datetime]:
    """Find the next occurrence of a calendar event.

    Args:
        spec_str: Calendar event specification
        from_dt: Base datetime (defaults to current UTC time)

    Returns:
        Next matching datetime, or None if none found within 1 year

    Example:
        >>> from datetime import datetime, timezone
        >>> base = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
        >>> next_occurrence('daily', base)
        datetime.datetime(2024, 3, 2, 0, 0, 0, tzinfo=datetime.timezone.utc)
    """
    event = parse(spec_str)
    if event.is_epoch:
        return None  # Epoch timestamps are fixed points, not recurring
    finder = NextOccurrence(event)
    return finder.next_after(from_dt)
