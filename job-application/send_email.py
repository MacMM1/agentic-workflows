#!/usr/bin/env python3
"""Sends a plain-text email via the Gmail API. Used for follow-up messages
sent directly to an employer once the user has approved the exact text.

Reuses the same Gmail OAuth connection as newsletter/send_newsletter.py
(credentials.json / token.json in the project root).

Usage:
  python job-application/send_email.py --to "hiring@acme.com" \
      --subject "Following up on my application" \
      --body-file ".tmp/business-development-2026-08-04-followup.txt"
"""
import argparse
import base64
import re
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gmail_auth import get_credentials, verify_connection

load_dotenv()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(address: str) -> bool:
    return bool(EMAIL_RE.match(address))


def build_message(subject: str, sender: str, recipient: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)
    return msg


def send_message(service, message: EmailMessage) -> dict:
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_email(to: str, subject: str, body_path: Path, sender: str | None = None) -> dict:
    if not validate_email(to):
        print(f"Error: {to!r} does not look like a valid email address.")
        sys.exit(1)

    if not body_path.exists():
        print(f"Error: {body_path} not found.")
        sys.exit(1)
    body = body_path.read_text(encoding="utf-8")

    try:
        creds = get_credentials()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Gmail credentials are invalid or revoked ({e}). Run `python shared/gmail_auth.py` to re-authenticate.")
        sys.exit(1)

    authenticated_address = verify_connection(creds)
    sender = sender or authenticated_address

    message = build_message(subject, sender, to, body)

    service = build("gmail", "v1", credentials=creds)
    try:
        result = send_message(service, message)
    except HttpError as e:
        status = e.resp.status
        if status == 401:
            print("Error: Gmail credentials rejected (401). Run `python shared/gmail_auth.py` to re-authenticate.")
        elif status == 403:
            print("Error: Gmail API permission/quota error (403).")
        elif status == 400:
            print(f"Error: Gmail API rejected the request (400): {e}")
        else:
            print(f"Error: Gmail API request failed ({status}): {e}")
        sys.exit(1)

    print(f"Sent to {to}. Message ID: {result['id']}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body-file", required=True, type=Path)
    parser.add_argument("--from", dest="sender", default=None)
    args = parser.parse_args()

    send_email(args.to, args.subject, args.body_file, args.sender)


if __name__ == "__main__":
    main()
