"""Archives a sent newsletter into the persistent newsletters/ directory and updates the index.

Only call this after a successful send -- never archive a newsletter that wasn't sent.

CLI: python tools/archive_newsletter.py --html <path> --content <path>
     --message-id <id> --sent-at <iso timestamp> [--archive-dir <dir>]
"""

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "newsletter"


def update_index(archive_dir: Path, entry: dict) -> None:
    index_path = archive_dir / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"issues": []}
    index["issues"].append(entry)
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def archive_newsletter(html_path: Path, content: dict, message_id: str, sent_at: datetime, archive_dir: Path = Path("newsletters")) -> Path:
    year_dir = archive_dir / str(sent_at.year)
    year_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(content.get("topic", content.get("headline", "newsletter")))
    date_str = sent_at.strftime("%Y-%m-%d")
    filename = f"{date_str}-{slug}.html"
    dest_path = year_dir / filename

    shutil.copyfile(html_path, dest_path)

    entry = {
        "date": date_str,
        "slug": slug,
        "subject": content.get("subject", ""),
        "topic": content.get("topic", ""),
        "message_id": message_id,
        "file": str(dest_path.relative_to(archive_dir.parent)).replace("\\", "/"),
        "source_count": len(content.get("sources", [])),
        "chart_count": len(content.get("charts", [])),
    }
    update_index(archive_dir, entry)

    return dest_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--message-id", required=True)
    parser.add_argument("--sent-at", required=True, help="ISO 8601 timestamp")
    parser.add_argument("--archive-dir", default=Path("newsletters"), type=Path)
    args = parser.parse_args()

    content = json.loads(args.content.read_text(encoding="utf-8"))
    sent_at = datetime.fromisoformat(args.sent_at)

    dest = archive_newsletter(args.html, content, args.message_id, sent_at, args.archive_dir)
    print(f"Archived to {dest}")


if __name__ == "__main__":
    main()
