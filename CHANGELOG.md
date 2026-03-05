# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-03-05

### Added
- Initial release of sysdtime-py
- **Calendar Event Parsing**
  - Full support for systemd.time(7) calendar specifications
  - Weekday constraints (Mon, Tue, Mon..Fri, Mon,Wed,Fri, etc.)
  - Date specifications with wildcards, ranges, lists, and repetitions
  - Time specifications with full feature support
  - Last-day-of-month syntax (~)
  - Epoch timestamps (@seconds-since-epoch format)
  - Timezone support (IANA, UTC, and regional aliases: WIB, WITA, WIT, JST)
  - Shorthand forms (daily, weekly, hourly, monthly, quarterly, semiannually, yearly)

- **Timestamp Parsing**
  - Special tokens: now, today, yesterday, tomorrow
  - Relative timestamps: +3h, -5s, 11min ago (all systemd time units)
  - Absolute timestamps: ISO 8601 with T separator
  - RFC 3339 with timezone offsets (+01:00, -05:30, Z)
  - All systemd time units (microseconds to years)

- **Core Functionality**
  - `parse()`: Parse calendar event specifications
  - `matches()`: Check if datetime matches specification
  - `next_occurrence()`: Find next matching occurrence
  - `parse_timestamp()`: Parse timestamp specifications

- **Modularized Package Structure**
  - `constants.py`: Configuration and regex patterns
  - `types.py`: Data structures (CalendarEvent, DateSpec, TimeSpec)
  - `parser.py`: Calendar event parsing logic
  - `matcher.py`: Datetime matching engine
  - `searcher.py`: Next occurrence search algorithm
  - `timestamp.py`: Timestamp parsing

- **Documentation**
  - Comprehensive README with examples
  - API documentation (API.md)
  - Type hints throughout codebase
  - Detailed docstrings for all public functions

- **Development Setup**
  - pyproject.toml with ruff configuration (Python 3.7+ target)
  - .pre-commit-config.yaml for automated code quality
  - Ruff linting and formatting enforced
  - Pure Python implementation (no external dependencies)

### Performance
- Calendar event parser: O(n) where n is spec complexity
- Datetime matching: O(1)
- Next occurrence search:
  - Daily events: ~366 iterations (granularity-aware stepping)
  - Hourly events: ~8,784 iterations
  - Minutely events: ~527k iterations
  - Secondly events: ~31M iterations (worst case)
- Timestamp parsing: O(1) for most expressions

### Notes
- This is a vibe-coded implementation - use at your own risk
- Not recommended for system-critical deployments
- All 140 tests passing (99 calendar event + 41 timestamp)
- Python 3.7+ compatibility ensured
