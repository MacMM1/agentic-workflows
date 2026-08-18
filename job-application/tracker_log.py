#!/usr/bin/env python3
"""Append one row to saved-applications/tracker.csv, creating it with the standard header if missing.

Usage:
  python job-application/tracker_log.py --company "Acme Ltd" --role "Business Development" \
      --source-link "https://example.com/job/123" --status applied \
      --materials-folder "saved-applications/business-development-2026-08-04" \
      --notes "Referee requested"
"""
import argparse
import csv
import datetime as dt
from pathlib import Path

COLUMNS = [
    "date_applied", "company", "role", "source_link", "status",
    "materials_folder", "follow_up_sent", "follow_up_date", "notes",
]


def log(tracker_path: Path, row: dict) -> None:
    is_new = not tracker_path.exists()
    with tracker_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerow({col: row.get(col, "") for col in COLUMNS})
    print(f"{'Created' if is_new else 'Appended to'} {tracker_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tracker", type=Path, default=Path("saved-applications/tracker.csv"))
    parser.add_argument("--date-applied", default=dt.date.today().isoformat())
    parser.add_argument("--company", default="")
    parser.add_argument("--role", default="")
    parser.add_argument("--source-link", default="")
    parser.add_argument("--status", default="applied")
    parser.add_argument("--materials-folder", default="")
    parser.add_argument("--follow-up-sent", default="")
    parser.add_argument("--follow-up-date", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    row = {
        "date_applied": args.date_applied,
        "company": args.company,
        "role": args.role,
        "source_link": args.source_link,
        "status": args.status,
        "materials_folder": args.materials_folder,
        "follow_up_sent": args.follow_up_sent,
        "follow_up_date": args.follow_up_date,
        "notes": args.notes,
    }
    log(args.tracker, row)


if __name__ == "__main__":
    main()
