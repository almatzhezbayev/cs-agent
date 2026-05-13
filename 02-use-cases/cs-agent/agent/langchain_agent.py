from langchain.agents import create_agent
from dotenv import load_dotenv 

load_dotenv()

class LangChainAgent:
    def __init__(self):
        self._agent = self._build_agent()

    def _build_agent(self):

        return create_agent(
            model="openai:gpt-5.4-mini",
            tools=[],  # no tools
            system_prompt="You are a helpful customer support backend agent.",
        )

    async def respond(self, message: str) -> str:
        if not self._agent:
            return ""

        result = await self._agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]}
        )

        # holds full conversation list
        messages = result.get("messages", [])
        if not messages:
            return ""

        last = messages[-1]

        return getattr(last, "content", "") or ""