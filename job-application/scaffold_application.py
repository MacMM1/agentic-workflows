#!/usr/bin/env python3
"""Scaffold and finalize a job application folder in one command each,
instead of six manual docx_convert.py calls.

start:  create saved-applications/<role-category>-<date>/ and working .md
        copies of the CV and cover letter, ready to edit.
finish: convert the edited working copies into the final .docx files
        in that same folder.

Usage:
  python job-application/scaffold_application.py start --role-category "Quant Graduate Analyst" --company "Haystack"
  # ... edit the two .tmp/*.md files it prints ...
  python job-application/scaffold_application.py finish --slug quant-graduate-analyst-2026-08-04
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from docx_convert import to_md, to_docx

SOURCE_CV = Path("saved-applications/cv-source-materials/cv-master.docx")
SOURCE_COVER = Path("saved-applications/cv-source-materials/cover-letter-template.docx")


def slugify(text: str) -> str:
    return "-".join(text.lower().split())


def start(role_category: str, company: str, date: str) -> None:
    if not SOURCE_CV.exists():
        sys.exit(f"Missing {SOURCE_CV} -- add it to saved-applications/cv-source-materials/ first")
    if not SOURCE_COVER.exists():
        sys.exit(f"Missing {SOURCE_COVER} -- add it to saved-applications/cv-source-materials/ first")

    slug = f"{slugify(role_category)}-{date}"
    app_dir = Path("saved-applications") / slug
    app_dir.mkdir(parents=True, exist_ok=True)

    cv_md = Path(".tmp") / f"{slug}-cv.md"
    cover_md = Path(".tmp") / f"{slug}-cover-letter.md"
    to_md(SOURCE_CV, cv_md)
    to_md(SOURCE_COVER, cover_md)

    meta = {
        "role_category": role_category,
        "company": company,
        "date": date,
        "slug": slug,
        "cv_working_copy": str(cv_md),
        "cover_letter_working_copy": str(cover_md),
    }
    (app_dir / ".application-meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"\nApplication folder: {app_dir}")
    print("Edit these, then run:")
    print(f"  python job-application/scaffold_application.py finish --slug {slug}")
    print(f"Working copies:\n  {cv_md}\n  {cover_md}")


def finish(slug: str) -> None:
    app_dir = Path("saved-applications") / slug
    meta_path = app_dir / ".application-meta.json"
    if not meta_path.exists():
        sys.exit(f"No metadata at {meta_path} -- run 'start' first")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    role_slug = slugify(meta["role_category"])

    cv_out = app_dir / f"cv-{role_slug}.docx"
    cover_out = app_dir / f"cover-letter-{role_slug}.docx"

    to_docx(SOURCE_CV, Path(meta["cv_working_copy"]), cv_out)
    to_docx(SOURCE_COVER, Path(meta["cover_letter_working_copy"]), cover_out)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)

    p1 = sub.add_parser("start", help="Create the application folder and working copies")
    p1.add_argument("--role-category", required=True)
    p1.add_argument("--company", required=True)
    p1.add_argument("--date", default=dt.date.today().isoformat())

    p2 = sub.add_parser("finish", help="Convert edited working copies into final docx files")
    p2.add_argument("--slug", required=True, help="Folder name under saved-applications/, e.g. quant-graduate-analyst-2026-08-04")

    args = parser.parse_args()
    if args.mode == "start":
        start(args.role_category, args.company, args.date)
    else:
        finish(args.slug)


if __name__ == "__main__":
    main()
