from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .config import (
    GOOGLE_CALENDAR_SCOPES,
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_REDIRECT_URI,
)
from .token_store import JsonFileStore


logger = logging.getLogger(__name__)


class GoogleCalendarAuthError(RuntimeError):
    pass


class GoogleCalendarConfigError(RuntimeError):
    pass


class GoogleCalendarService:
    def __init__(self, token_store: JsonFileStore):
        self.token_store = token_store

    def ensure_credentials_file(self) -> None:
        if not GOOGLE_CREDENTIALS_PATH.exists():
            raise GoogleCalendarConfigError(
                "Google client secrets file is missing. "
                f"Expected at {GOOGLE_CREDENTIALS_PATH}"
            )

    def get_authorization_url(self, actor_id: str, flow_state_store: JsonFileStore) -> str:
        from google_auth_oauthlib.flow import Flow

        self.ensure_credentials_file()
        flow = Flow.from_client_secrets_file(
            str(GOOGLE_CREDENTIALS_PATH),
            scopes=GOOGLE_CALENDAR_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        flow_state_store.set(state, {"actor_id": actor_id})
        return auth_url

    def exchange_code(self, code: str, state: str, actor_id: str) -> None:
        from google_auth_oauthlib.flow import Flow

        self.ensure_credentials_file()
        flow = Flow.from_client_secrets_file(
            str(GOOGLE_CREDENTIALS_PATH),
            scopes=GOOGLE_CALENDAR_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        self.token_store.set(actor_id, json_credentials(credentials))
        logger.info("Stored Google OAuth tokens for actor_id=%s", actor_id)

    def _load_credentials(self, actor_id: str) -> Credentials:
        payload = self.token_store.get(actor_id)
        if not payload:
            logger.warning("No Google tokens found for actor_id=%s", actor_id)
            raise GoogleCalendarAuthError(
                "Google Calendar is not connected for actor_id="
                f"{actor_id}. Open /auth/google/start?actor_id={actor_id} first."
            )

        logger.info("Loaded Google tokens for actor_id=%s", actor_id)
        credentials = Credentials.from_authorized_user_info(
            payload, scopes=GOOGLE_CALENDAR_SCOPES
        )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self.token_store.set(actor_id, json_credentials(credentials))
            logger.info("Refreshed Google tokens for actor_id=%s", actor_id)
        return credentials

    def _build_client(self, actor_id: str):
        credentials = self._load_credentials(actor_id)
        return build("calendar", "v3", credentials=credentials)

    def get_calendar_events_today(self, actor_id: str, timezone: str = "UTC") -> dict[str, Any]:
        logger.info(
            "Fetching calendar events for actor_id=%s timezone=%s",
            actor_id,
            timezone,
        )
        service = self._build_client(actor_id)
        tz = ZoneInfo(timezone)
        today_start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=today_start.isoformat(),
                timeMax=today_end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return {"events": events_result.get("items", []), "timezone": timezone}

    def create_calendar_event(
        self,
        actor_id: str,
        summary: str,
        start_time: str,
        end_time: str,
        timezone: str = "UTC",
        description: str | None = None,
        location: str | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "Creating calendar event for actor_id=%s summary=%s start=%s end=%s timezone=%s",
            actor_id,
            summary,
            start_time,
            end_time,
            timezone,
        )
        service = self._build_client(actor_id)
        event = {
            "summary": summary,
            "description": description or "This event was created by cs-agent.",
            "location": location,
            "start": {"dateTime": start_time, "timeZone": timezone},
            "end": {"dateTime": end_time, "timeZone": timezone},
        }
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        logger.info(
            "Created calendar event for actor_id=%s event_id=%s",
            actor_id,
            created_event.get("id"),
        )
        return {
            "event_created": True,
            "event_id": created_event.get("id"),
            "htmlLink": created_event.get("htmlLink"),
        }

    def get_connection_status(self, actor_id: str) -> dict[str, Any]:
        payload = self.token_store.get(actor_id)
        if not payload:
            return {
                "connected": False,
                "actor_id": actor_id,
                "reason": "No stored Google OAuth tokens",
            }

        credentials = self._load_credentials(actor_id)
        return {
            "connected": True,
            "actor_id": actor_id,
            "has_refresh_token": bool(credentials.refresh_token),
            "scopes": list(credentials.scopes or []),
        }


def json_credentials(credentials: Credentials) -> dict[str, Any]:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
