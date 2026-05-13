from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import logging
from pydantic import BaseModel
from agent.langchain_agent import LangChainAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    actor_id: str = "default"

agent = LangChainAgent()

app = FastAPI(title="cs-agent-noaws")

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/auth/google/start")
async def start_google_auth(actor_id: str = "default"):
    logger.info("Starting Google auth for actor_id=%s", actor_id)
    auth_url = agent.calendar_service.get_authorization_url(
        actor_id=actor_id,
        flow_state_store=agent.oauth_state_store,
    )
    return {"authorization_url": auth_url}


@app.get("/auth/google/callback")
async def google_auth_callback(code: str, state: str):
    logger.info("Received Google auth callback for state=%s", state)
    state_payload = agent.oauth_state_store.get(state)
    if not state_payload:
        return {"connected": False, "error": "Unknown or expired OAuth state"}

    actor_id = state_payload["actor_id"]
    agent.calendar_service.exchange_code(code=code, state=state, actor_id=actor_id)
    agent.oauth_state_store.delete(state)
    return RedirectResponse(
        url=f"/auth/google/success?actor_id={actor_id}",
        status_code=302,
    )


@app.get("/auth/google/success")
async def google_auth_success(actor_id: str):
    return {"connected": True, "actor_id": actor_id}


@app.get("/auth/google/status")
async def google_auth_status(actor_id: str = "default"):
    logger.info("Checking Google auth status for actor_id=%s", actor_id)
    return agent.calendar_service.get_connection_status(actor_id=actor_id)


@app.post("/chat")
async def chat(payload: ChatRequest):
    logger.info("Chat request received for actor_id=%s", payload.actor_id)
    answer = await agent.respond(payload.message, actor_id=payload.actor_id)
    return {"answer": answer}
