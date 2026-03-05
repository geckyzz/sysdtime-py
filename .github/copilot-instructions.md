# sysdtime-py Copilot Instructions

## Quick Start

**Build & Test:**
```bash
# Sync dependencies and setup development environment (uses uv)
uv sync --dev

# Run all tests (302 test cases)
pytest sysdtime/tests/ -v

# Run a specific test file
pytest sysdtime/tests/test_parser.py -v

# Run tests matching a keyword
pytest sysdtime/tests/ -k "leap" -v

# Run with coverage
pytest sysdtime/tests/ --cov=sysdtime --cov-report=html
```

**Linting & Formatting:**
```bash
# Check code with ruff
ruff check sysdtime/

# Format code with ruff
ruff format sysdtime/

# Both (auto-fix where possible)
ruff check sysdtime/ --fix && ruff format sysdtime/
```

## Architecture Overview

This is a **systemd.time(7) parser** — a pure Python library for parsing calendar events and timestamps.

### Core Module Structure

- **`parser.py`** — Parses calendar event strings into `CalendarEvent` objects. Handles shorthands (`daily`, `weekly`), weekdays, dates, times, timezones, and epoch timestamps.
- **`types.py`** — Data structures: `Spec` (matches individual values/ranges/repetitions), `DateSpec`/`TimeSpec` (component specs), `CalendarEvent` (complete parsed event with `.normalized()` method).
- **`matcher.py`** — Checks if a given datetime matches a calendar event spec.
- **`searcher.py`** — Finds the next occurrence of an event after a given datetime.
- **`timestamp.py`** — Separate parser for timestamp specs (relative like `+3h`, absolute like `2024-03-15T10:30:00`, special tokens like `now`/`today`).
- **`constants.py`** — Regex patterns, timezone aliases (WIB, WITA, WIT, JST), weekday names, and time unit conversions.

### Data Flow

```
Input String
    ↓
Parser.parse() → CalendarEvent
    ↓ (depends on use case)
    ├→ Matcher.matches(datetime) → bool
    ├→ NextOccurrence.next_after(datetime) → datetime
    └→ .normalized() → string representation
```

### Key Classes & Methods

**CalendarEvent** (`types.py`):
- `.normalized()` — Returns canonical form (e.g., `"Mon,Fri *-*-* 09:00:00"`)
- `.is_epoch` — Whether it's an epoch timestamp

**Spec** (`types.py`):
- `.matches(value)` — Basic exact/range/wildcard matching
- `.matches_with_repetition(value, max_value)` — Handles patterns like `1/7` (every 7 starting from 1)

**Parser** (`parser.py`):
- `SHORTHANDS` dict maps shorthand forms to canonical specs
- Order of parsing: timezone → weekdays → date → time → epoch check

**Matcher** (`matcher.py`):
- Matches dates, weekdays, and times independently
- Timezone-aware (handles UTC and IANA timezones)

## Code Conventions

### Patterns

1. **Spec Matching** — All matching logic follows the pattern:
   - Wildcard (`*`) matches anything
   - Exact values in a set
   - Ranges (`start..end` inclusive)
   - Repetitions (`start/step` pattern)
   - Last-day-of-month (`~offset`)

2. **Dataclasses** — Uses `@dataclass` from `types.py` extensively. Always use field defaults for mutable types (`default_factory=set` or `default_factory=list`).

3. **Type Hints** — Python 3.7+ compatible. Use `Optional[T]`, `Set[T]`, `List[T]`, `Tuple[T, ...]`.

4. **Error Handling** — Raises `ValueError` for invalid inputs (bad timezone, malformed specs). Invalid inputs during parsing are caught early with descriptive messages.

5. **Documentation** — Every class and public method has a docstring with:
   - Brief one-liner
   - Args with types
   - Returns with types
   - Example (where helpful)

### Timezone Handling

- Timezone can be specified as `TZ` suffix: `"*-*-* 09:00:00 Europe/Berlin"`
- Aliases: `UTC` or `UTC0`, plus regional: `WIB` (UTC+7), `WITA` (UTC+8), `WIT` (UTC+9), `JST` (UTC+9)
- Uses Python's `zoneinfo.ZoneInfo` for IANA timezones
- Datetime matching is timezone-aware

### Testing Structure

Tests in `sysdtime/tests/`:
- `conftest.py` — Fixtures (base_datetime, leap_day, year_boundary, etc.)
- `test_constants.py` — Timezone aliases, regex patterns, weekday names
- `test_types.py` — Spec, DateSpec, TimeSpec, CalendarEvent
- `test_parser.py` — Parser including shorthands, weekdays, dates, times, epochs
- `test_matcher.py` — Datetime matching against specs
- `test_searcher.py` — Finding next occurrence (handles year boundary, leap days, month-end)
- `test_timestamp.py` — Timestamp parsing (relative, absolute, RFC 3339)
- `test_integration.py` — End-to-end API flows

All tests parametrized heavily. Expected behaviors documented in TEST_SUITE.md.

## Important Notes

- **No external dependencies** for the library itself. Dev dependencies: ruff, pytest, pytest-cov.
- **Python 3.7+** compatible (target version in ruff config).
- **Edge cases to watch:**
  - Leap years (2024 is leap, 1900/2100 are not)
  - Month-end (31st doesn't exist in all months)
  - Leap day (Feb 29 matching)
  - Year boundaries (wrapping from Dec to Jan)
  - Timezone-aware datetime matching
  - Epoch timestamps are fixed points (not recurring)

- **Ruff ignores** (see `pyproject.toml`):
  - `E501` — Line too long (natural for regex patterns)
  - `RUF012` — Mutable class constants (`SHORTHANDS`, `TIME_UNITS` in `constants.py`)

- **Warning** — Package is "vibe-coded" per README. Not production-hardened; use at own risk.

## Public API

All exported from `__init__.py`:
- `parse(spec_str: str) -> CalendarEvent`
- `matches(spec_str: str, dt: datetime) -> bool`
- `next_occurrence(spec_str: str, from_dt: Optional[datetime] = None) -> Optional[datetime]`
- `parse_timestamp(spec_str: str, base_time: Optional[datetime] = None) -> datetime`
- Plus classes: `Parser`, `Matcher`, `NextOccurrence`, `TimestampParser`, `CalendarEvent`

## Configuration

**Pre-commit** (`.pre-commit-config.yaml`):
- Runs ruff check and format before commits
- Uses `ruff-pre-commit` from astral-sh

**Pytest** (`pyproject.toml`):
- Test path: `sysdtime/tests/`
- Files: `test_*.py`
- Output: verbose with short tracebacks

## Publishing & Releases

**Automated PyPI Deployment** (`.github/workflows/publish.yml`):
- Triggered automatically when a **git tag** starting with `v` is pushed
- Uses modern **Trusted Publishing** (no API tokens needed!)
- Workflow steps:
  1. Builds distribution with `python -m build`
  2. Publishes to PyPI using [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
  3. Creates GitHub Release with all commits since previous version tag

**Setup (One-time):**
1. Go to https://pypi.org/manage/account/publishing/
2. Add a "pending publisher":
   - **PyPI Project Name:** `sysdtime-py`
   - **GitHub Repository Owner:** Your username/org
   - **GitHub Repository Name:** `sysdtime-py`
   - **Workflow filename:** `publish.yml`
   - **GitHub Environment name:** `pypi`
3. Click "Add pending publisher"
4. Go to your repo: Settings → Environments → Create environment `pypi`
5. (Optional) Require approval for this environment

**To publish a new version:**
1. Update `version = "x.y.z"` in `pyproject.toml`
2. Commit: `git commit -m "Release x.y.z"`
3. Create and push git tag:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```
4. Workflow automatically:
   - Builds wheel and sdist
   - Publishes to PyPI (no secrets needed!)
   - Creates GitHub Release with commit history

**Why Trusted Publishing?**
- ✅ No API tokens to store
- ✅ Tokens expire automatically per-workflow
- ✅ Each project has isolated credentials
- ✅ More secure than long-lived API tokens
- ✅ Follows official Python Packaging best practices
