#!/usr/bin/env python3
"""Command-line interface for sysdtime-py package.

Provides utilities for parsing and checking systemd calendar events and timestamps.
Supports both interactive mode and subcommands.

Examples:
    # Interactive mode
    python main.py

    # Subcommand mode
    python main.py parse "Mon,Fri 09:00:00"
    python main.py matches "daily" "2024-03-15 10:00:00"
    python main.py next-occurrence "daily" "2024-03-15 10:00:00"
    python main.py parse-timestamp "today"
    python main.py parse-timestamp "+3h" "2024-03-15 10:00:00"
"""

import argparse
import sys
from datetime import datetime, timezone

from sysdtime import matches, next_occurrence, parse, parse_timestamp


def cmd_parse(args):
    """Parse a calendar event specification."""
    try:
        event = parse(args.spec)
        print("Parsed calendar event:")
        print("  Normalized: {}".format(event.normalized()))
        if hasattr(event, "weekdays") and event.weekdays is not None:
            weekday_names = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
            weekdays_str = ",".join(weekday_names[i] for i in sorted(event.weekdays))
            print("  Weekdays: {}".format(weekdays_str))
        print("  Timezone: {}".format(event.timezone))
    except ValueError as e:
        print("Error parsing spec: {}".format(e), file=sys.stderr)
        return 1
    return 0


def cmd_matches(args):
    """Check if a datetime matches a calendar event specification."""
    try:
        dt = datetime.fromisoformat(args.datetime)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        result = matches(args.spec, dt)
        status = "matches" if result else "does not match"
        print("DateTime {} {} the specification".format(args.datetime, status))
        if args.verbose:
            print("  Spec: {}".format(args.spec))
            print("  DateTime: {}".format(dt))
    except ValueError as e:
        print("Error: {}".format(e), file=sys.stderr)
        return 1
    return 0


def cmd_next_occurrence(args):
    """Find the next occurrence of a calendar event."""
    try:
        from_dt = None
        if args.from_datetime:
            from_dt = datetime.fromisoformat(args.from_datetime)
            if from_dt.tzinfo is None:
                from_dt = from_dt.replace(tzinfo=timezone.utc)

        next_dt = next_occurrence(args.spec, from_dt)
        print("Next occurrence: {}".format(next_dt))
        if args.verbose and from_dt:
            print("  From: {}".format(from_dt))
            print("  Spec: {}".format(args.spec))
    except ValueError as e:
        print("Error: {}".format(e), file=sys.stderr)
        return 1
    return 0


def cmd_parse_timestamp(args):
    """Parse a timestamp specification."""
    try:
        base_time = None
        if args.base_time:
            base_time = datetime.fromisoformat(args.base_time)
            if base_time.tzinfo is None:
                base_time = base_time.replace(tzinfo=timezone.utc)

        dt = parse_timestamp(args.spec, base_time)
        print("Parsed timestamp: {}".format(dt))
        if args.verbose:
            print("  Spec: {}".format(args.spec))
            if base_time:
                print("  Base time: {}".format(base_time))
    except ValueError as e:
        print("Error: {}".format(e), file=sys.stderr)
        return 1
    return 0


def interactive_mode():
    """Run interactive CLI mode."""
    print("sysdtime-py - systemd.time(7) parser")
    print("=" * 60)
    print("\nEnter 'help' for command help, 'quit' to exit\n")

    while True:
        try:
            line = input("sysdtime> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            return 0

        if not line:
            continue

        if line.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            return 0

        if line.lower() == "help":
            print_interactive_help()
            continue

        # Parse the input as a command
        parts = line.split(maxsplit=1)
        command = parts[0].lower()
        args_str = parts[1] if len(parts) > 1 else ""

        if command == "parse":
            if not args_str:
                print("Usage: parse <spec>")
                continue
            try:
                event = parse(args_str)
                print("  Normalized: {}".format(event.normalized()))
            except ValueError as e:
                print("  Error: {}".format(e))

        elif command == "matches":
            parts = args_str.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: matches <spec> <datetime>")
                continue
            try:
                dt = datetime.fromisoformat(parts[1])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                result = matches(parts[0], dt)
                print("  Match: {}".format(result))
            except ValueError as e:
                print("  Error: {}".format(e))

        elif command == "next":
            parts = args_str.split(maxsplit=1)
            if not parts:
                print("Usage: next <spec> [from_datetime]")
                continue
            try:
                from_dt = None
                if len(parts) > 1:
                    from_dt = datetime.fromisoformat(parts[1])
                    if from_dt.tzinfo is None:
                        from_dt = from_dt.replace(tzinfo=timezone.utc)
                next_dt = next_occurrence(parts[0], from_dt)
                print("  Next: {}".format(next_dt))
            except ValueError as e:
                print("  Error: {}".format(e))

        elif command == "timestamp":
            parts = args_str.split(maxsplit=1)
            if not parts:
                print("Usage: timestamp <spec> [base_time]")
                continue
            try:
                base_time = None
                if len(parts) > 1:
                    base_time = datetime.fromisoformat(parts[1])
                    if base_time.tzinfo is None:
                        base_time = base_time.replace(tzinfo=timezone.utc)
                dt = parse_timestamp(parts[0], base_time)
                print("  Parsed: {}".format(dt))
            except ValueError as e:
                print("  Error: {}".format(e))

        else:
            print("Unknown command: '{}'. Type 'help' for available commands.".format(command))


def print_interactive_help():
    """Print help for interactive mode."""
    print("""
Available commands:
  parse <spec>                     Parse calendar event spec
  matches <spec> <datetime>        Check if datetime matches spec
  next <spec> [from_datetime]      Find next occurrence
  timestamp <spec> [base_time]     Parse timestamp spec
  help                             Show this help message
  quit                             Exit the program

Examples:
  > parse Mon,Fri 09:00:00
  > matches daily 2024-03-15 10:00:00
  > next daily 2024-03-15
  > timestamp today
  > timestamp +3h 2024-03-15 10:00:00
""")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        prog="sysdtime",
        description="Parse systemd.time(7) calendar events and timestamps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode (default):
    python main.py

  Parse a calendar event:
    python main.py parse "Mon,Fri 09:00:00"

  Check if datetime matches:
    python main.py matches "daily" "2024-03-15 10:00:00"

  Find next occurrence:
    python main.py next-occurrence "daily" "2024-03-15 10:00:00"

  Parse a timestamp:
    python main.py parse-timestamp "today"
    python main.py parse-timestamp "+3h" "2024-03-15 10:00:00"
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="available commands")

    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse a calendar event")
    parse_parser.add_argument("spec", help="Calendar event specification")
    parse_parser.set_defaults(func=cmd_parse)

    # Matches command
    matches_parser = subparsers.add_parser(
        "matches", help="Check if datetime matches a specification"
    )
    matches_parser.add_argument("spec", help="Calendar event specification")
    matches_parser.add_argument("datetime", help="Datetime to check (YYYY-MM-DD HH:MM:SS format)")
    matches_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    matches_parser.set_defaults(func=cmd_matches)

    # Next occurrence command
    next_parser = subparsers.add_parser(
        "next-occurrence", help="Find the next occurrence of a calendar event"
    )
    next_parser.add_argument("spec", help="Calendar event specification")
    next_parser.add_argument(
        "--from",
        dest="from_datetime",
        help="From datetime (YYYY-MM-DD HH:MM:SS format), default is now",
    )
    next_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    next_parser.set_defaults(func=cmd_next_occurrence)

    # Parse timestamp command
    timestamp_parser = subparsers.add_parser(
        "parse-timestamp", help="Parse a timestamp specification"
    )
    timestamp_parser.add_argument("spec", help="Timestamp specification")
    timestamp_parser.add_argument(
        "--base",
        dest="base_time",
        help="Base time for relative timestamps (YYYY-MM-DD HH:MM:SS format)",
    )
    timestamp_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    timestamp_parser.set_defaults(func=cmd_parse_timestamp)

    args = parser.parse_args()

    # If no command is given, use interactive mode
    if not args.command:
        return interactive_mode()

    # Run the subcommand
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
