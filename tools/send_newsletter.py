"""Sends a rendered newsletter via the Gmail API with chart images embedded as CID attachments.

CLI: python tools/send_newsletter.py --content <path> --html <path>
     --charts-manifest <path> --to <email> [--from <email>]
"""

import argparse
import json
import os
import re
import sys
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.errors import HttpError

from gmail_auth import get_credentials, verify_connection
from googleapiclient.discovery import build
import base64

load_dotenv()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(address: str) -> bool:
    return bool(EMAIL_RE.match(address))


def build_plain_text(content: dict) -> str:
    lines = [content["headline"], ""]
    for section in content.get("sections", []):
        lines.append(section["heading"])
        lines.append(section["body"])
        lines.append("")

    sources = content.get("sources", [])
    if sources:
        lines.append("Sources:")
        for source in sources:
            lines.append(f"- {source['title']}: {source['url']}")

    return "\n".join(lines)


def build_mime_message(subject: str, sender: str, recipient: str, html_body: str, plain_body: str, chart_paths: dict) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    html_part = msg.get_payload()[1]
    for chart_id, path in chart_paths.items():
        img_data = Path(path).read_bytes()
        html_part.add_related(img_data, maintype="image", subtype="png", cid=f"<{chart_id}@newsletter.local>")

    return msg


def send_message(service, message: EmailMessage) -> dict:
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_newsletter(content_path: Path, html_path: Path, manifest_path: Path, recipient: str, sender: str | None = None) -> dict:
    if not validate_email(recipient):
        print(f"Error: {recipient!r} does not look like a valid email address.")
        sys.exit(1)

    content = json.loads(content_path.read_text(encoding="utf-8"))
    html_body = html_path.read_text(encoding="utf-8")
    plain_body = build_plain_text(content)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    chart_paths = {chart_id: manifest_path.parent / filename for chart_id, filename in manifest.items()}

    sender = sender or os.environ.get("NEWSLETTER_SENDER_EMAIL") or "me"

    try:
        creds = get_credentials()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Gmail credentials are invalid or revoked ({e}). Run `python tools/gmail_auth.py` to re-authenticate.")
        sys.exit(1)

    authenticated_address = verify_connection(creds)
    if sender == "me":
        sender = authenticated_address

    message = build_mime_message(content["subject"], sender, recipient, html_body, plain_body, chart_paths)

    service = build("gmail", "v1", credentials=creds)
    try:
        result = send_message(service, message)
    except HttpError as e:
        status = e.resp.status
        if status == 401:
            print("Error: Gmail credentials rejected (401). Run `python tools/gmail_auth.py` to re-authenticate.")
        elif status == 403:
            print("Error: Gmail API permission/quota error (403).")
        elif status == 400:
            print(f"Error: Gmail API rejected the request (400): {e}")
        else:
            print(f"Error: Gmail API request failed ({status}): {e}")
        sys.exit(1)

    print(f"Sent. Message ID: {result['id']}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--charts-manifest", required=True, type=Path)
    parser.add_argument("--to", required=True)
    parser.add_argument("--from", dest="sender", default=None)
    args = parser.parse_args()

    send_newsletter(args.content, args.html, args.charts_manifest, args.to, args.sender)


if __name__ == "__main__":
    main()
