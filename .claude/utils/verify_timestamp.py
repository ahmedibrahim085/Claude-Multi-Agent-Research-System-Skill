#!/usr/bin/env python3
"""
Timestamp Verification Utility

MANDATORY tool for analyzing timestamps to prevent timezone confusion.
NEVER analyze timestamps mentally - ALWAYS use this utility.

Usage:
    # Analyze timestamp from JSON file
    python verify_timestamp.py <file_path> <field_name>

    # Analyze raw ISO timestamp
    python verify_timestamp.py --raw "2025-12-11T11:10:21+00:00" "Event name"

Examples:
    python verify_timestamp.py ~/.claude_code_search/.../index_state.json last_incremental_index
    python verify_timestamp.py --raw "2025-12-11T11:10:21+00:00" "Last reindex"
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone


def format_timestamp_analysis(timestamp_str: str, label: str) -> dict:
    """Analyze timestamp and return formatted output with timezone safety

    Args:
        timestamp_str: ISO format timestamp (e.g., "2025-12-11T11:10:21+00:00")
        label: Human-readable label for the event

    Returns:
        dict with formatted strings ready for reporting
    """
    try:
        # Parse timestamp
        event_time = datetime.fromisoformat(timestamp_str)

        # Handle timezone-naive timestamps (assume UTC)
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
            tz_warning = "⚠️  Timezone-naive timestamp, assuming UTC"
        else:
            tz_warning = None

        # Get current time
        now_utc = datetime.now(timezone.utc)

        # Calculate elapsed
        elapsed_seconds = (now_utc - event_time).total_seconds()
        elapsed_minutes = elapsed_seconds / 60

        # Convert to local for display
        event_local = event_time.astimezone()
        now_local = now_utc.astimezone()

        # Format output
        return {
            'success': True,
            'label': label,
            'raw_timestamp': timestamp_str,
            'event_utc': event_time.strftime("%H:%M:%S UTC"),
            'event_local': event_local.strftime("%H:%M:%S %Z"),
            'now_utc': now_utc.strftime("%H:%M:%S UTC"),
            'now_local': now_local.strftime("%H:%M:%S %Z"),
            'elapsed_seconds': elapsed_seconds,
            'elapsed_minutes': elapsed_minutes,
            'elapsed_display': format_elapsed(elapsed_seconds),
            'tz_warning': tz_warning,
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'raw_timestamp': timestamp_str
        }


def format_elapsed(seconds: float) -> str:
    """Format elapsed time in human-readable format"""
    if seconds < 0:
        return f"{-seconds:.0f} seconds in the future (clock skew?)"

    if seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes} min {secs} sec"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} hr {minutes} min"


def print_analysis(result: dict):
    """Print formatted timestamp analysis"""
    if not result['success']:
        print(f"❌ Error: {result['error']}")
        print(f"Raw timestamp: {result['raw_timestamp']}")
        return

    print(f"\n{result['label']}:")
    print(f"─" * 60)
    print(f"Raw timestamp: {result['raw_timestamp']}")

    if result['tz_warning']:
        print(f"{result['tz_warning']}")

    print(f"\nEvent time:    {result['event_utc']} ({result['event_local']})")
    print(f"Current time:  {result['now_utc']} ({result['now_local']})")
    print(f"Elapsed:       {result['elapsed_display']} ({result['elapsed_minutes']:.1f} minutes)")
    print()


def analyze_from_file(file_path: str, field_name: str):
    """Read timestamp from JSON file and analyze"""
    file = Path(file_path).expanduser()

    if not file.exists():
        print(f"❌ File not found: {file_path}")
        return 1

    # Show file info
    mod_time = datetime.fromtimestamp(file.stat().st_mtime)
    print(f"File: {file_path}")
    print(f"Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')} (local)")

    # Read JSON
    try:
        with open(file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return 1

    # Get field
    timestamp_str = data.get(field_name)
    if not timestamp_str:
        print(f"❌ Field '{field_name}' not found in JSON")
        print(f"Available fields: {', '.join(data.keys())}")
        return 1

    # Analyze and print
    result = format_timestamp_analysis(timestamp_str, field_name)
    print_analysis(result)

    return 0 if result['success'] else 1


def analyze_raw_timestamp(timestamp_str: str, label: str):
    """Analyze a raw ISO timestamp"""
    result = format_timestamp_analysis(timestamp_str, label)
    print_analysis(result)
    return 0 if result['success'] else 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    if sys.argv[1] == '--raw':
        if len(sys.argv) < 4:
            print("Usage: verify_timestamp.py --raw <timestamp> <label>")
            return 1
        return analyze_raw_timestamp(sys.argv[2], sys.argv[3])
    else:
        if len(sys.argv) < 3:
            print("Usage: verify_timestamp.py <file_path> <field_name>")
            return 1
        return analyze_from_file(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    sys.exit(main())
