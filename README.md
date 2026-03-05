# sysdtime-py

A vibe-coded pure Python implementation for parsing [systemd.time(7)](https://man7.org/linux/man-pages/man7/systemd.time.7.html)
calendar event and timestamp specifications.

> [!WARNING]
>
> This package is entirely vibe-coded. Do not use in system-critical deployments.

## Features

- **Calendar Event Parsing**: Parse systemd calendar event specifications
  - Weekday constraints (`Mon`, `Fri`, `Mon..Fri`, `Mon,Wed,Fri`)
  - Date specifications with wildcards, ranges, lists, and repetitions
  - Time specifications with full feature support
  - Last-day-of-month syntax (`~`)
  - Epoch timestamps (`@seconds-since-epoch` format)
  - Timezone support (IANA, UTC, regional aliases: WIB, WITA, WIT, JST)
  - Shorthand forms (`daily`, `weekly`, `hourly`, `monthly`, etc.)

- **Timestamp Parsing**: Parse systemd timestamp specifications
  - Relative timestamps (`+3h`, `-5s`, `11min ago`)
  - Special tokens (`now`, `today`, `yesterday`, `tomorrow`)
  - ISO 8601 with T separator (`2024-03-15T10:30:00`)
  - RFC 3339 with timezone offsets (`2024-03-15T10:30:00+01:00`, `2024-03-15T10:30:00Z`)
  - All systemd time units (microseconds to years)

## Installation

```bash
pip install sysdtime-py
```

Or with `uv`:

```bash
uv pip install sysdtime-py
```

## Quick Start

### Calendar Events

```python
from sysdtime import parse, matches, next_occurrence
from datetime import datetime, timezone

# Parse and normalize a calendar event
event = parse('Mon,Fri 09:00:00')
print(event.normalized())  # Mon,Fri *-*-* 09:00:00

# Check if a datetime matches the specification
dt = datetime(2024, 3, 15, 9, 0, 0, tzinfo=timezone.utc)
print(matches('Mon,Fri 09:00:00', dt))  # True

# Find the next occurrence
next_dt = next_occurrence('daily', dt)
print(next_dt)  # 2024-03-16 00:00:00+00:00
```

### Timestamp Parsing

```python
from sysdtime import parse_timestamp
from datetime import datetime, timezone

# Parse special tokens
now = parse_timestamp('now')
today = parse_timestamp('today')
tomorrow = parse_timestamp('tomorrow')

# Parse relative timestamps
base = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
later = parse_timestamp('+3h30min', base)

# Parse absolute timestamps with RFC 3339 offsets
dt = parse_timestamp('2024-03-15T10:30:00+01:00')
```

## Supported Formats

### Calendar Events

Follows the systemd.time(7) specification:

```
DOW [DOW...] YYYY-MM-DD [YYYY-MM-DD...] HH:MM:SS [HH:MM:SS...]
```

Where:
- `DOW`: Day of week (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
- `YYYY-MM-DD`: Date (year, month, day)
- `HH:MM:SS`: Time (hours, minutes, seconds)

All components support:
- Wildcards (`*`)
- Ranges (`1..5`)
- Lists (`1,3,5`)
- Repetitions (`*/5`, `1..10/2`)

### Timestamps

- **Tokens**: `now`, `today`, `yesterday`, `tomorrow`
- **Relative**: `+3h`, `-5s`, `+1M`, `-2w`, `11min ago`
- **Absolute**: `2024-03-15`, `2024-03-15 10:30:00`, `2024-03-15T10:30:00`
- **RFC 3339**: `2024-03-15T10:30:00Z`, `2024-03-15T10:30:00+01:00`

## API Reference

### `parse(spec_str: str) -> CalendarEvent`

Parse a calendar event specification string.

**Args:**
- `spec_str`: Calendar event specification

**Returns:**
- `CalendarEvent`: Parsed event object

**Raises:**
- `ValueError`: For invalid specifications

### `matches(spec_str: str, dt: datetime) -> bool`

Check if a datetime matches a calendar event specification.

**Args:**
- `spec_str`: Calendar event specification
- `dt`: Datetime to check

**Returns:**
- `bool`: True if datetime matches

### `next_occurrence(spec_str: str, from_dt: Optional[datetime] = None) -> datetime`

Find the next occurrence of a calendar event.

**Args:**
- `spec_str`: Calendar event specification
- `from_dt`: Reference datetime (defaults to now)

**Returns:**
- `datetime`: Next matching datetime

### `parse_timestamp(spec_str: str, base_time: Optional[datetime] = None) -> datetime`

Parse a timestamp specification.

**Args:**
- `spec_str`: Timestamp specification
- `base_time`: Reference time for relative specs (defaults to now)

**Returns:**
- `datetime`: Parsed datetime with timezone info

## Module Structure

- `sysdtime.parser`: Calendar event parsing
- `sysdtime.matcher`: Datetime matching logic
- `sysdtime.searcher`: Next occurrence search algorithm
- `sysdtime.timestamp`: Timestamp parsing
- `sysdtime.types`: Data structures (CalendarEvent, DateSpec, TimeSpec)
- `sysdtime.constants`: Configuration and patterns

## Performance Notes

- Calendar event parsing: O(n) where n is spec complexity
- Datetime matching: O(1)
- Next occurrence search: O(1) for daily/hourly (granularity-aware stepping), O(n) for minutely/secondly
- Timestamp parsing: O(1) for most expressions

## Compatibility

- Python 3.7+
- No external dependencies
- Pure Python implementation

## Development

Install with development dependencies:

```bash
uv sync --dev
```

Run linting and formatting:

```bash
ruff check sysdtime/
ruff format sysdtime/
```

Run tests:

```bash
pytest
```

## License

MIT - See LICENSE file

## Acknowledgments

This is a vibe-coded implementation based on the [systemd.time(7)](https://man7.org/linux/man-pages/man7/systemd.time.7.html) specification. Use at your own risk.
