# sysdtime-py API Documentation

Complete API reference for the sysdtime-py package.

## Top-Level Functions

### `parse(spec_str: str) -> CalendarEvent`

Parse a calendar event specification string into a `CalendarEvent` object.

**Parameters:**
- `spec_str` (str): Calendar event specification string

**Returns:**
- `CalendarEvent`: Parsed event object with normalized form and matching logic

**Raises:**
- `ValueError`: If the specification is invalid

**Example:**
```python
from sysdtime import parse

event = parse('Mon,Fri 09:00:00')
print(event.normalized())  # Mon,Fri *-*-* 09:00:00
```

---

### `matches(spec_str: str, dt: datetime) -> bool`

Check if a datetime matches a calendar event specification.

**Parameters:**
- `spec_str` (str): Calendar event specification string
- `dt` (datetime): Datetime object to check (should include timezone info)

**Returns:**
- `bool`: `True` if the datetime matches the specification

**Raises:**
- `ValueError`: If the specification is invalid

**Example:**
```python
from sysdtime import matches
from datetime import datetime, timezone

dt = datetime(2024, 3, 15, 9, 0, 0, tzinfo=timezone.utc)
matches('Mon,Fri 09:00:00', dt)  # True (Friday at 9:00 AM)
```

---

### `next_occurrence(spec_str: str, from_dt: Optional[datetime] = None) -> datetime`

Find the next datetime that matches a calendar event specification.

**Parameters:**
- `spec_str` (str): Calendar event specification string
- `from_dt` (datetime, optional): Reference datetime (defaults to now)

**Returns:**
- `datetime`: The next datetime that matches the specification

**Raises:**
- `ValueError`: If the specification is invalid or no match found within search window

**Example:**
```python
from sysdtime import next_occurrence
from datetime import datetime, timezone

dt = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
next_dt = next_occurrence('daily', dt)
# Returns 2024-03-16 00:00:00+00:00
```

**Performance Notes:**
- Daily events: ~366 iterations (granularity-aware)
- Hourly events: ~8,784 iterations
- Minutely events: ~527k iterations
- Secondly events: ~31M iterations (worst case)

---

### `parse_timestamp(spec_str: str, base_time: Optional[datetime] = None) -> datetime`

Parse a timestamp specification string into a datetime object.

**Parameters:**
- `spec_str` (str): Timestamp specification string
- `base_time` (datetime, optional): Reference time for relative specs (defaults to now)

**Returns:**
- `datetime`: Parsed datetime with timezone information

**Raises:**
- `ValueError`: If the timestamp specification is invalid

**Example:**
```python
from sysdtime import parse_timestamp
from datetime import datetime, timezone

# Special tokens
today = parse_timestamp('today')
tomorrow = parse_timestamp('tomorrow')

# Relative timestamps
base = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
later = parse_timestamp('+3h30min', base)  # 2024-03-15 13:30:00

# Absolute timestamps
dt = parse_timestamp('2024-03-15T10:30:00+01:00')

# RFC 3339 format
utc_time = parse_timestamp('2024-03-15T10:30:00Z')
```

---

## Data Classes

### `CalendarEvent`

Represents a parsed calendar event specification.

**Attributes:**
- `weekdays` (Optional[Set[int]]): Weekday constraints (0=Monday, 6=Sunday)
- `date` (DateSpec): Date specification component
- `time` (TimeSpec): Time specification component
- `timezone` (str): Timezone name (default: "UTC")
- `explicit_timezone` (bool): Whether timezone was explicitly specified

**Methods:**

#### `normalized() -> str`

Return the normalized string representation of the event.

**Returns:**
- str: Normalized specification string

**Example:**
```python
event = parse('Mon,Fri 9')
event.normalized()  # 'Mon,Fri *-*-* 09:00:00'
```

---

#### `is_match(dt: datetime) -> bool`

Check if a datetime matches this event specification.

**Parameters:**
- `dt` (datetime): Datetime to check

**Returns:**
- bool: True if datetime matches

**Example:**
```python
event = parse('Mon,Fri 09:00:00')
from datetime import datetime, timezone
dt = datetime(2024, 3, 15, 9, 0, 0, tzinfo=timezone.utc)
event.is_match(dt)  # True
```

---

#### `find_next(from_dt: Optional[datetime] = None) -> datetime`

Find the next occurrence of this event after the given datetime.

**Parameters:**
- `from_dt` (datetime, optional): Reference time (defaults to now)

**Returns:**
- datetime: Next matching datetime

**Example:**
```python
event = parse('daily')
dt = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
event.find_next(dt)  # 2024-03-16 00:00:00+00:00
```

---

### `DateSpec`

Specification for date matching.

**Attributes:**
- `years` (Set[int]): Valid years
- `months` (Set[int]): Valid months (1-12)
- `days` (Set[int]): Valid days (1-31)

**Properties:**
- `is_wildcard` (bool): True if all date components are wildcards
- `is_daily_or_higher` (bool): True if day component is wildcard

---

### `TimeSpec`

Specification for time matching.

**Attributes:**
- `hours` (Set[int]): Valid hours (0-23)
- `minutes` (Set[int]): Valid minutes (0-59)
- `seconds` (Set[int]): Valid seconds (0-59)

**Properties:**
- `is_wildcard` (bool): True if all time components are wildcards
- `is_hourly_or_higher` (bool): True if minute component is wildcard
- `is_minutely_or_higher` (bool): True if second component is wildcard

---

## Classes (Advanced Usage)

### `Parser`

Low-level calendar event parser. Use `parse()` instead for most cases.

```python
from sysdtime import Parser

parser = Parser('Mon,Fri 09:00:00')
event = parser.parse()
```

---

### `Matcher`

Low-level datetime matching engine. Use `matches()` instead for most cases.

```python
from sysdtime import Matcher
from datetime import datetime, timezone

matcher = Matcher('Mon,Fri 09:00:00')
dt = datetime(2024, 3, 15, 9, 0, 0, tzinfo=timezone.utc)
matcher.matches(dt)  # True
```

---

### `NextOccurrence`

Low-level next occurrence search. Use `next_occurrence()` instead for most cases.

```python
from sysdtime import NextOccurrence
from datetime import datetime, timezone

searcher = NextOccurrence('daily')
dt = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
searcher.find_next(dt)  # 2024-03-16 00:00:00+00:00
```

---

## Calendar Event Specification Format

Follows the systemd.time(7) specification format:

```
[DOW] [YYYY-MM-DD] [HH:MM:SS]
```

### Components

#### Day of Week (optional)
- Format: `Mon`, `Mon..Fri`, `Mon,Wed,Fri`, `*`
- Valid: Mon, Tue, Wed, Thu, Fri, Sat, Sun
- Shorthand: Mon, Tue, Wed, Thu, Fri, Sat, Sun

#### Date (optional)
- Format: `YYYY-MM-DD`
- Components support: `*`, ranges (`1..5`), lists (`1,3,5`), repetitions (`*/5`, `1..10/2`)
- Last day of month: `~` (e.g., `*-*-~`)

#### Time (optional)
- Format: `HH:MM:SS`, `HH:MM`, `HH`
- Components support: `*`, ranges, lists, repetitions

### Shorthand Forms

- `minutely`: `*-*-* *:*:00`
- `hourly`: `*-*-* *:00:00`
- `daily`: `*-*-* 00:00:00`
- `weekly`: `Mon *-*-* 00:00:00`
- `monthly`: `*-*-01 00:00:00`
- `quarterly`: `*-01,04,07,10-01 00:00:00`
- `semiannually`: `*-01,07-01 00:00:00`
- `yearly`: `*-01-01 00:00:00`

### Examples

- `daily` - Once per day at midnight
- `Mon,Fri 09:00` - Monday and Friday at 9:00 AM
- `*-*-1,15 *:00:00` - 1st and 15th of every month, every hour
- `Mon..Fri *:00:00` - Weekdays, every hour
- `2024-03-15 10:30:00` - Specific date and time (once)
- `*-03-15 10:30` - March 15th at 10:30 (every year)

---

## Timestamp Specification Format

### Special Tokens

- `now` - Current time
- `today` - Midnight today
- `yesterday` - Midnight yesterday
- `tomorrow` - Midnight tomorrow

### Relative Timestamps

Format: `[+-]VALUE UNIT [VALUE UNIT ...]` or `VALUE UNIT ... ago`

**Supported Units:**
- `usec`, `us` - Microseconds
- `msec`, `ms` - Milliseconds
- `sec`, `s` - Seconds
- `min`, `m` - Minutes
- `h` - Hours
- `d` - Days
- `w` - Weeks
- `M` - Months (30.44 days)
- `y` - Years (365.25 days)

**Examples:**
- `+3h` - 3 hours from base time
- `-5m30s` - 5 minutes 30 seconds ago
- `+1M` - 1 month from base time
- `10min ago` - 10 minutes ago

### Absolute Timestamps

**ISO 8601 Format:**
- `2024-03-15`
- `2024-03-15 10:30:00`
- `2024-03-15T10:30:00`

**RFC 3339 Format:**
- `2024-03-15T10:30:00Z` - UTC
- `2024-03-15T10:30:00+01:00` - With offset
- `2024-03-15T10:30:00-05:30` - With negative offset
- `2024-03-15T10:30:00+0100` - Without colon

**With Timezone:**
- `2024-03-15 10:30:00 UTC`
- `2024-03-15 10:30:00 Asia/Tokyo`
- `2024-03-15 10:30:00 WIB`

**Supported Timezone Aliases:**
- `UTC` - Coordinated Universal Time
- `WIB` - Asia/Jakarta (Western Indonesia Time)
- `WITA` - Asia/Makassar (Central Indonesia Time)
- `WIT` - Asia/Jayapura (Eastern Indonesia Time)
- `JST` - Asia/Tokyo (Japan Standard Time)

---

## Error Handling

All parsing functions raise `ValueError` on invalid input:

```python
from sysdtime import parse, parse_timestamp

try:
    parse('invalid-spec')
except ValueError as e:
    print(f"Parse error: {e}")

try:
    parse_timestamp('not-a-timestamp')
except ValueError as e:
    print(f"Timestamp error: {e}")
```

---

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Parse calendar event | O(n) | n = spec complexity |
| Check datetime match | O(1) | Constant time matching |
| Find next daily event | O(366) | Granularity-aware stepping |
| Find next hourly event | O(8,784) | Granularity-aware stepping |
| Find next minutely event | O(~527k) | Granularity-aware stepping |
| Parse timestamp | O(1) | Most expressions |
| Parse relative timestamp | O(1) | Constant time calculation |

---

## Compatibility

- **Python:** 3.7+
- **Dependencies:** None (pure Python)
- **Timezone:** Uses `zoneinfo` (Python 3.9+) with fallback for older versions

---

## Warnings

> ⚠️ **Warning**: This package is entirely vibe-coded. Do not use in system-critical deployments.

The implementation is based on the systemd.time(7) specification but has not been extensively tested in production environments. Use at your own risk.
