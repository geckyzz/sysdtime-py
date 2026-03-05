"""Constants and configuration for systemd calendar event parsing."""

# Timezone name mappings
TIMEZONE_ALIASES = {
    "UTC": "UTC",
    "WIB": "Asia/Jakarta",  # Western Indonesia Time
    "WITA": "Asia/Makassar",  # Central Indonesia Time
    "WIT": "Asia/Jayapura",  # Eastern Indonesia Time
    "JST": "Asia/Tokyo",  # Japan Standard Time
}

# Full weekday names (source of truth)
_WEEKDAY_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Abbreviated weekday names for output
WEEKDAY_SHORT = [name[:3] for name in _WEEKDAY_FULL]

# Weekday name to index mapping (generated from full names)
WEEKDAY_NAMES = {}
for i, full_name in enumerate(_WEEKDAY_FULL):
    WEEKDAY_NAMES[full_name.lower()] = i
    WEEKDAY_NAMES[full_name[:3].lower()] = i

# Regex patterns (compiled once for performance)
_weekday_opts = []
for name in _WEEKDAY_FULL:
    _weekday_opts.append(name.lower())
    _weekday_opts.append(name[:3].lower())
_WEEKDAY_DAY = r"(?:" + "|".join(_weekday_opts) + r")"
WEEKDAY_PATTERN = "^(?:" + _WEEKDAY_DAY + r"(?:\s*\.\.\s*" + _WEEKDAY_DAY + r")?(?:\s*,\s*)?)+\s+"
TIMEZONE_PATTERN = r"(\s+(UTC|WIB|WITA|WIT|JST|[A-Za-z][A-Za-z0-9_/\-]*))$"
EPOCH_PATTERN = r"^@(\d+)$"

# Constants
MIN_YEAR = 1970
MAX_YEAR = 2099
MAX_SEARCH_ITERATIONS = 366 * 24 * 60 * 60  # 1 year
