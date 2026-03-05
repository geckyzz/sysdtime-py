"""Matcher for checking datetime against calendar event specifications."""

from datetime import datetime, timedelta

from .types import CalendarEvent


class Matcher:
    """Matches datetimes against calendar event specifications.

    Provides methods to check if a datetime matches a parsed calendar event,
    considering all constraints (weekday, date, time).
    """

    def __init__(self, event: CalendarEvent):
        """Initialize matcher with calendar event.

        Args:
            event: CalendarEvent to match against
        """
        self.event = event

    def matches(self, dt: datetime) -> bool:
        """Check if datetime matches the calendar event.

        Checks all constraints:
        - Weekday constraint (if specified)
        - Date specification (year, month, day)
        - Time specification (hour, minute, second)

        Args:
            dt: datetime object to check (should have timezone info)

        Returns:
            True if all constraints match, False otherwise
        """
        if dt.weekday() not in self.event.weekdays:
            return False

        if not self._date_matches(dt):
            return False

        if not self._time_matches(dt):
            return False

        return True

    def _date_matches(self, dt: datetime) -> bool:
        """Check if date components match specification.

        Args:
            dt: datetime object to check

        Returns:
            True if date matches, False otherwise
        """
        if not self.event.date.year.matches(dt.year):
            return False

        if not self.event.date.month.matches(dt.month):
            return False

        if self.event.date.day.is_last_day:
            return self._is_last_day_of_month(dt)

        # Use matches_with_repetition for day to handle patterns like 1/7
        if not self.event.date.day.matches_with_repetition(dt.day, 31):
            return False

        return True

    def _time_matches(self, dt: datetime) -> bool:
        """Check if time components match specification.

        Args:
            dt: datetime object to check

        Returns:
            True if time matches, False otherwise
        """
        if not self.event.time.hour.matches_with_repetition(dt.hour, 23):
            return False

        if not self.event.time.minute.matches_with_repetition(dt.minute, 59):
            return False

        if not self.event.time.second.matches_with_repetition(dt.second, 59):
            return False

        return True

    def _is_last_day_of_month(self, dt: datetime) -> bool:
        """Check if date is the nth-to-last day of the month.

        For example, offset=0 means last day, offset=3 means 3rd-to-last.

        Args:
            dt: datetime object to check

        Returns:
            True if date is the specified last day, False otherwise
        """
        offset = self.event.date.day.last_day_offset or 0

        # Calculate last day of month
        next_month = dt.replace(day=1)
        if dt.month == 12:
            next_month = next_month.replace(year=dt.year + 1)
        else:
            next_month = next_month.replace(month=dt.month + 1)

        last_day = (next_month - timedelta(days=1)).day

        if offset == 0:
            return dt.day == last_day

        target_day = last_day - offset
        return dt.day == target_day if target_day > 0 else False
