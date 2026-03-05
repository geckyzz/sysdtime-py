"""Searcher for finding next occurrences of calendar events."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from .constants import MAX_SEARCH_ITERATIONS
from .matcher import Matcher
from .types import CalendarEvent


class NextOccurrence:
    """Finds the next occurrence of a calendar event.

    Searches forward from a given datetime to find the next time
    that matches the calendar event specification. Uses granularity-aware
    stepping to efficiently skip non-matching intervals.
    """

    def __init__(self, event: CalendarEvent):
        """Initialize next occurrence finder with calendar event.

        Args:
            event: CalendarEvent to find occurrences for
        """
        self.event = event
        self.matcher = Matcher(event)

    def _get_search_step(self) -> timedelta:
        """Determine optimal search step based on event granularity.

        Returns shorter steps for fine-grained specs, longer for coarse ones.

        Returns:
            timedelta representing the search step duration
        """
        # If all time components are wildcard, we can skip to next day
        if (
            self.event.time.hour.is_wildcard
            and self.event.time.minute.is_wildcard
            and self.event.time.second.is_wildcard
        ):
            return timedelta(days=1)

        # If minute and second are wildcard, we can skip to next hour
        if self.event.time.minute.is_wildcard and self.event.time.second.is_wildcard:
            return timedelta(hours=1)

        # If second is wildcard, skip to next minute
        if self.event.time.second.is_wildcard:
            return timedelta(minutes=1)

        # Otherwise use 1-second granularity
        return timedelta(seconds=1)

    def next_after(self, from_dt: Optional[datetime] = None) -> Optional[datetime]:
        """Find the next datetime matching the event after from_dt.

        Searches forward using granularity-aware stepping to efficiently
        find the next matching datetime. Search is limited to 1 year.

        Args:
            from_dt: Base datetime (defaults to current UTC time)

        Returns:
            Next matching datetime, or None if none found within 1 year
        """
        if from_dt is None:
            from_dt = datetime.now(tz=timezone.utc)

        from_dt = from_dt.replace(microsecond=0)
        current = from_dt + timedelta(seconds=1)
        step = self._get_search_step()

        # Calculate iteration limit based on step size
        if step == timedelta(days=1):
            max_iterations = 366  # 1 year in days
        elif step == timedelta(hours=1):
            max_iterations = 366 * 24  # 1 year in hours
        elif step == timedelta(minutes=1):
            max_iterations = 366 * 24 * 60  # 1 year in minutes
        else:
            max_iterations = MAX_SEARCH_ITERATIONS  # 1 year in seconds

        iterations = 0
        while iterations < max_iterations:
            if self.matcher.matches(current):
                return current

            current += step
            iterations += 1

        return None

    def next_occurrences(
        self,
        count: int,
        from_dt: Optional[datetime] = None,
    ) -> List[datetime]:
        """Find the next N occurrences.

        Args:
            count: Number of occurrences to find
            from_dt: Base datetime (defaults to current UTC time)

        Returns:
            List of next matching datetimes (may be shorter than count)
        """
        results = []
        current = from_dt
        for _ in range(count):
            next_dt = self.next_after(current)
            if next_dt is None:
                break
            results.append(next_dt)
            current = next_dt
        return results
