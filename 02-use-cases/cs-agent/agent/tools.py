from __future__ import annotations

import json
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from .customer_support_service import CustomerSupportService
from .google_calendar import (
    GoogleCalendarAuthError,
    GoogleCalendarConfigError,
    GoogleCalendarService,
)


logger = logging.getLogger(__name__)


def build_tools(
    actor_id: str,
    calendar_service: GoogleCalendarService,
    customer_support_service: CustomerSupportService,
):
    @tool
    def current_time(timezone: str = "UTC") -> str:
        """Return the current date and time for a given IANA timezone."""
        now = datetime.now(ZoneInfo(timezone))
        return json.dumps({"current_time": now.isoformat(), "timezone": timezone})

    @tool
    def get_calendar_events_today(timezone: str = "UTC") -> str:
        """Retrieve today's Google Calendar events for the authenticated user."""
        try:
            logger.info(
                "Tool get_calendar_events_today called for actor_id=%s timezone=%s",
                actor_id,
                timezone,
            )
            return json.dumps(
                calendar_service.get_calendar_events_today(
                    actor_id=actor_id, timezone=timezone
                )
            )
        except (GoogleCalendarAuthError, GoogleCalendarConfigError) as exc:
            return json.dumps({"error": str(exc), "events": []})
        except Exception as exc:  # pragma: no cover - defensive tool boundary
            return json.dumps({"error": str(exc), "events": []})

    @tool
    def create_calendar_event(
        summary: str,
        start_time: str,
        end_time: str,
        timezone: str = "UTC",
        description: str | None = None,
        location: str | None = None,
    ) -> str:
        """Create a Google Calendar event for the authenticated user."""
        try:
            logger.info(
                "Tool create_calendar_event called for actor_id=%s summary=%s start=%s end=%s timezone=%s",
                actor_id,
                summary,
                start_time,
                end_time,
                timezone,
            )
            return json.dumps(
                calendar_service.create_calendar_event(
                    actor_id=actor_id,
                    summary=summary,
                    start_time=start_time,
                    end_time=end_time,
                    timezone=timezone,
                    description=description,
                    location=location,
                )
            )
        except (GoogleCalendarAuthError, GoogleCalendarConfigError) as exc:
            return json.dumps({"error": str(exc), "event_created": False})
        except Exception as exc:  # pragma: no cover - defensive tool boundary
            return json.dumps({"error": str(exc), "event_created": False})

    @tool
    def get_customer_profile(
        customer_id: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> str:
        """Look up a customer profile by customer_id, email, or phone."""
        try:
            logger.info(
                "Tool get_customer_profile called customer_id=%s email=%s phone=%s",
                customer_id,
                email,
                phone,
            )
            return customer_support_service.get_customer_profile(
                customer_id=customer_id,
                email=email,
                phone=phone,
            )
        except Exception as exc:
            return f"Error retrieving customer profile: {exc}"

    @tool
    def check_warranty_status(
        serial_number: str,
        customer_email: str | None = None,
    ) -> str:
        """Check warranty status by serial number and optionally verify by customer email."""
        try:
            logger.info(
                "Tool check_warranty_status called serial_number=%s customer_email=%s",
                serial_number,
                customer_email,
            )
            return customer_support_service.check_warranty_status(
                serial_number=serial_number,
                customer_email=customer_email,
            )
        except Exception as exc:
            return f"Error checking warranty status: {exc}"

    return [
        current_time,
        get_calendar_events_today,
        create_calendar_event,
        get_customer_profile,
        check_warranty_status,
    ]
