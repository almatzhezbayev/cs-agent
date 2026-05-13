from fastapi import FastAPI
from pydantic import BaseModel
from agent.langchain_agent import LangChainAgent

# Define schema for the chat request
class ChatRequest(BaseModel):
    message: str

agent = LangChainAgent()

app = FastAPI(title="cs-agent-noaws")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(payload: ChatRequest):
    # Get response from LangChainAgent
    answer = await agent.respond(payload.message)
    return {"answer": answer}