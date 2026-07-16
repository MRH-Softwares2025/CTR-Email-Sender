import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.send",
]


def _client_config():
    client_id = (os.getenv("GOOGLE_OAUTH_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("GOOGLE_OAUTH_CLIENT_SECRET") or "").strip()
    if not client_id or not client_secret:
        raise RuntimeError("Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.")

    return {
        "web": {
            "client_id": client_id,
            "project_id": os.getenv("GOOGLE_OAUTH_PROJECT_ID", "email-automation"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": [],
        }
    }


def build_redirect_uri(base_url: str):
    configured = (os.getenv("GOOGLE_OAUTH_REDIRECT_URI") or "").strip()
    if configured:
        return configured
    return f"{base_url.rstrip('/')}/api/oauth/google/callback"


def build_authorization_url(redirect_uri: str, state: str):
    flow = Flow.from_client_config(_client_config(), scopes=OAUTH_SCOPES)
    flow.redirect_uri = redirect_uri
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return authorization_url


def exchange_code_for_token(code: str, state: str, redirect_uri: str):
    flow = Flow.from_client_config(_client_config(), scopes=OAUTH_SCOPES, state=state)
    flow.redirect_uri = redirect_uri
    flow.fetch_token(code=code)
    return credentials_to_dict(flow.credentials)


def credentials_from_dict(payload: dict):
    if not isinstance(payload, dict):
        return None
    try:
        return Credentials(
            token=payload.get("token"),
            refresh_token=payload.get("refresh_token"),
            token_uri=payload.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=payload.get("client_id") or os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            client_secret=payload.get("client_secret") or os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            scopes=payload.get("scopes") or OAUTH_SCOPES,
        )
    except Exception:
        return None


def credentials_to_dict(creds: Credentials):
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
    }


def ensure_valid_credentials(creds: Credentials):
    if creds is None:
        raise RuntimeError("Missing OAuth credentials")

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds.valid:
        raise RuntimeError("OAuth credentials are invalid. Reconnect Gmail.")

    return creds


def fetch_account_email(creds: Credentials):
    creds = ensure_valid_credentials(creds)
    userinfo = build("oauth2", "v2", credentials=creds, cache_discovery=False)
    profile = userinfo.userinfo().get().execute()
    return (profile.get("email") or "").strip().lower()


def send_gmail_message(creds: Credentials, from_email: str, to_email: str, subject: str, plain_body: str, html_body: str = ""):
    creds = ensure_valid_credentials(creds)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    msg = MIMEMultipart("alternative")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(plain_body or "", "plain"))
    if html_body:
        msg.attach(MIMEText(html_body, "html"))

    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    service.users().messages().send(userId="me", body={"raw": encoded}).execute()
