from __future__ import annotations

import base64
from dataclasses import dataclass
from email.message import EmailMessage as MimeEmailMessage
from pathlib import Path
from typing import Iterable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from amis_agent.application.services.email import EmailMessage
from amis_agent.core.config import get_settings


@dataclass(frozen=True)
class GmailSender:
    credentials_file: str
    token_file: str
    scopes: Iterable[str]
    redirect_uri: str | None = None
    expected_sender: str | None = None

    @staticmethod
    def build_raw_message(message: EmailMessage) -> str:
        mime = MimeEmailMessage()
        mime["To"] = message.to_email
        mime["From"] = f"{message.from_name} <{message.from_email}>"
        mime["Subject"] = message.subject
        mime.set_content(message.body)
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("utf-8")
        return raw

    def _load_credentials(self) -> Credentials:
        creds: Credentials | None = None
        token_path = Path(self.token_file)
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                if self.redirect_uri:
                    flow.redirect_uri = self.redirect_uri
                settings = get_settings()
                oauth_mode = (settings.google_oauth_mode or "auto").lower()
                if oauth_mode == "manual":
                    # Force out-of-band redirect so Google shows a code to paste.
                    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
                    auth_url, _ = flow.authorization_url(
                        access_type="offline",
                        prompt="consent",
                        include_granted_scopes="true",
                    )
                    print("Authorize this application by visiting this URL:\n", auth_url)
                    code = input("Paste the authorization code here: ").strip()
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                else:
                    try:
                        creds = flow.run_local_server(
                            host="localhost",
                            port=0,
                            bind_addr="127.0.0.1",
                            open_browser=False,
                        )
                    except Exception:
                        # Fallback to manual copy/paste flow if localhost callback fails.
                        auth_url, _ = flow.authorization_url(
                            access_type="offline",
                            prompt="consent",
                            include_granted_scopes="true",
                        )
                        print("Authorize this application by visiting this URL:\n", auth_url)
                        code = input("Paste the authorization code here: ").strip()
                        flow.fetch_token(code=code)
                        creds = flow.credentials
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
        return creds

    def _ensure_sender(self, service) -> None:
        if not self.expected_sender:
            raise ValueError("GMAIL_SENDER is required")
        try:
            profile = service.users().getProfile(userId="me").execute()
        except HttpError as exc:
            if exc.resp.status == 403:
                raise ValueError(
                    "gmail_profile_scope_missing: add gmail.readonly to GOOGLE_SCOPES and re-auth"
                ) from exc
            raise
        email = profile.get("emailAddress")
        if email != self.expected_sender:
            raise ValueError(f"authenticated_sender_mismatch:{email}")

    def send(self, message: EmailMessage) -> dict:
        creds = self._load_credentials()
        service = build("gmail", "v1", credentials=creds)
        self._ensure_sender(service)
        raw = self.build_raw_message(message)
        return (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )


def from_settings() -> GmailSender:
    settings = get_settings()
    scopes = [s.strip() for s in settings.google_scopes.split(",") if s.strip()]
    token_file = _token_file_for_sender(settings.google_token_file, settings.gmail_sender)
    return GmailSender(
        credentials_file=settings.google_credentials_file,
        token_file=token_file,
        scopes=scopes,
        redirect_uri=settings.google_redirect_uri,
        expected_sender=settings.gmail_sender,
    )


def _token_file_for_sender(token_file: str, sender: str) -> str:
    path = Path(token_file)
    if "{email}" in token_file:
        return token_file.replace("{email}", sender)
    if path.suffix:
        return str(path.with_name(f"{path.stem}.{sender}{path.suffix}"))
    return f"{token_file}.{sender}"

