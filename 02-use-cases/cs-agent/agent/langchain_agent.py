from langchain.agents import create_agent
from dotenv import load_dotenv
import logging

from .config import (
    CUSTOMERS_DATA_PATH,
    GOOGLE_STATE_PATH,
    GOOGLE_TOKEN_PATH,
    WARRANTIES_DATA_PATH,
)
from .customer_support_repository import LocalCustomerSupportRepository
from .customer_support_service import CustomerSupportService
from .google_calendar import GoogleCalendarService
from .token_store import JsonFileStore
from .tools import build_tools

load_dotenv()
logger = logging.getLogger(__name__)


class LangChainAgent:
    def __init__(self):
        self._calendar_service = GoogleCalendarService(
            token_store=JsonFileStore(GOOGLE_TOKEN_PATH)
        )
        self._customer_support_service = CustomerSupportService(
            repository=LocalCustomerSupportRepository(
                customers_path=CUSTOMERS_DATA_PATH,
                warranties_path=WARRANTIES_DATA_PATH,
            )
        )

    @property
    def calendar_service(self) -> GoogleCalendarService:
        return self._calendar_service

    @property
    def oauth_state_store(self) -> JsonFileStore:
        return JsonFileStore(GOOGLE_STATE_PATH)

    def _build_agent(self, actor_id: str):
        return create_agent(
            model="openai:gpt-5.4-mini",
            tools=build_tools(
                actor_id=actor_id,
                calendar_service=self._calendar_service,
                customer_support_service=self._customer_support_service,
            ),
            system_prompt=(
                "You are a helpful customer support backend agent. "
                "Use tools when they are the best way to answer. "
                "Do not invent calendar results. "
                "Use customer and warranty tools for support lookups when identifiers are available. "
                "If Google Calendar is not connected, tell the user to use the "
                "/auth/google/start endpoint first."
            ),
        )

    async def respond(self, message: str, actor_id: str = "default") -> str:
        logger.info("Agent received message for actor_id=%s: %s", actor_id, message)
        agent = self._build_agent(actor_id=actor_id)

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]}
        )

        messages = result.get("messages", [])
        logger.info("Agent returned %s messages for actor_id=%s", len(messages), actor_id)
        if not messages:
            return ""

        last = messages[-1]

        return getattr(last, "content", "") or ""
