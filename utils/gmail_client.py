# Gmail integration using OAuth 2.0
# Fetches emails from the connected Gmail account

import base64
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import config

CLIENT_SECRET_FILE = "client_secret.json"

def _get_client_config() -> dict:
    # Build the client config dict from st.secrets if available,
    # otherwise fall back to the local client_secret.json file
    try:
        oauth = st.secrets["google_oauth"]
        return {
            "installed": {
                "client_id": oauth["client_id"],
                "project_id": oauth["project_id"],
                "auth_uri": oauth["auth_uri"],
                "token_uri": oauth["token_uri"],
                "auth_provider_x509_cert_url": oauth["auth_provider_x509_cert_url"],
                "client_secret": oauth["client_secret"],
                "redirect_uris": list(oauth["redirect_uris"]),
            }
        }
    except Exception:
        # Running locally with the file present
        with open(CLIENT_SECRET_FILE) as f:
            return json.load(f)


def get_auth_url() -> tuple:
    client_config = _get_client_config()

    # Create flow from dict instead of from file
    flow = Flow.from_client_config(
        client_config,
        scopes=config.GMAIL_SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",
    )

    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
    )

    return auth_url, flow


def exchange_code_for_credentials(flow, code: str):
    """Exchange the authorisation code for credentials."""
    flow.fetch_token(code=code)
    return flow.credentials


def fetch_emails(credentials, max_results: int = config.GMAIL_MAX_RESULTS) -> list:
    """
    Fetch the latest emails from Gmail inbox.
    Returns a list of email dicts compatible with the rest of the system.
    """
    service = build("gmail", "v1", credentials=credentials)

    # Get list of message IDs from inbox
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg_meta in messages:
        msg = service.users().messages().get(
            userId="me",
            id=msg_meta["id"],
            format="full",
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

        # Extract body text from the message payload
        body = _extract_body(msg["payload"])

        # Parse sender name and email from the From header
        from_raw = headers.get("From", "Unknown <>")
        from_name, from_email = _parse_sender(from_raw)

        emails.append({
            "id": msg_meta["id"],
            "from_name": from_name,
            "from_email": from_email,
            "subject": headers.get("Subject", "(No Subject)"),
            "body": body,
            "date": headers.get("Date", ""),
            "source": "gmail",
        })

    return emails


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from a Gmail message payload."""

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        # Recurse into nested parts if plain text not found at top level
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result

    elif payload.get("mimeType") == "text/plain":
        data = payload["body"].get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return "(No body content)"


def _parse_sender(from_header: str) -> tuple:
    """Parse 'Display Name <email@domain.com>' into (name, email)."""
    if "<" in from_header and ">" in from_header:
        name = from_header.split("<")[0].strip().strip('"')
        email = from_header.split("<")[1].replace(">", "").strip()
        return name or email, email
    return from_header.strip(), from_header.strip()
