"""One-time OAuth bootstrap and shared credential helper for the Gmail API.

Run directly to authenticate: python tools/gmail_auth.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

# gmail.send alone cannot read a profile -- userinfo.email is added purely so
# verify_connection() can confirm which account is authenticated.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def _paths() -> tuple[Path, Path]:
    credentials_path = Path(os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials.json"))
    token_path = Path(os.environ.get("GMAIL_TOKEN_PATH", "token.json"))
    return credentials_path, token_path


def get_credentials(credentials_path: Path | None = None, token_path: Path | None = None) -> Credentials:
    """Loads cached credentials, refreshing if needed. Raises RefreshError if the
    refresh token was revoked/expired -- callers should not retry the browser
    flow themselves, that requires interactive human access."""
    default_credentials_path, default_token_path = _paths()
    credentials_path = credentials_path or default_credentials_path
    token_path = token_path or default_token_path

    if not token_path.exists():
        raise FileNotFoundError(
            f"{token_path} not found. Run `python tools/gmail_auth.py` once to authenticate."
        )

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
        else:
            raise RefreshError("Stored Gmail credentials are invalid and cannot be refreshed.")

    return creds


def verify_connection(creds: Credentials) -> str:
    """Confirms the credentials work and returns the authenticated email address.

    Uses the userinfo endpoint, not Gmail's users().getProfile() -- the
    gmail.send scope alone doesn't grant permission to read a profile."""
    session = AuthorizedSession(creds)
    response = session.get("https://www.googleapis.com/oauth2/v3/userinfo")
    response.raise_for_status()
    return response.json()["email"]


def bootstrap() -> None:
    credentials_path, token_path = _paths()

    if not credentials_path.exists():
        print(
            f"Missing {credentials_path}. Create an OAuth 2.0 Desktop app client in "
            "Google Cloud Console (with the Gmail API enabled) and download it as "
            f"{credentials_path}. See workflows/newsletter.md for the full walkthrough."
        )
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    token_path.write_text(creds.to_json())

    if not creds.refresh_token:
        print(
            "Warning: no refresh_token was returned. Revoke prior access at "
            "https://myaccount.google.com/permissions and re-run this script."
        )

    email = verify_connection(creds)
    print(f"Authenticated as {email}. Token saved to {token_path}.")


if __name__ == "__main__":
    bootstrap()
