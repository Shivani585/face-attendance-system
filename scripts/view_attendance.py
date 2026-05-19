"""
scripts/view_attendance.py — CLI Attendance Report Viewer

Usage:
    python scripts/view_attendance.py            # today
    python scripts/view_attendance.py --all      # all records
    python scripts/view_attendance.py --summary  # totals per person
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.file_handler import (
    read_attendance_records,
    get_attendance_summary,
    setup_logger,
)

logger = setup_logger("ViewAttendance")

COL_W = {"Name": 20, "Date": 12, "Time": 10, "Status": 10}
DIVIDER = "─" * (sum(COL_W.values()) + len(COL_W) * 3)


def _header(cols):
    return "  ".join(c.ljust(COL_W[c]) for c in cols)


def print_records(records, title: str) -> None:
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")
    cols = ["Name", "Date", "Time", "Status"]
    print(_header(cols))
    print(DIVIDER)
    for r in records:
        row = "  ".join(str(r.get(c, "")).ljust(COL_W[c]) for c in cols)
        print(row)
    print(f"\nTotal records: {len(records)}")


def print_summary(summary: dict) -> None:
    print(f"\n{'═'*40}")
    print("  Attendance Summary (All Time)")
    print(f"{'═'*40}")
    for name, count in sorted(summary.items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 30)
        print(f"  {name:<20}  {bar}  {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="View attendance records.")
    parser.add_argument("--all",     action="store_true", help="Show all records")
    parser.add_argument("--summary", action="store_true", help="Show per-person summary")
    parser.add_argument("--date",    type=str, default=None, help="Filter by date YYYY-MM-DD")
    args = parser.parse_args()

    all_records = read_attendance_records()

    if args.summary:
        print_summary(get_attendance_summary())

    elif args.all:
        print_records(all_records, "All Attendance Records")

    else:
        date_filter = args.date or datetime.now().strftime("%Y-%m-%d")
        filtered = [r for r in all_records if r.get("Date") == date_filter]
        print_records(filtered, f"Attendance for {date_filter}")


if __name__ == "__main__":
    main()
