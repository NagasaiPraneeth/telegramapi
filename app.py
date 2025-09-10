# app.py
import os
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import PlainTextResponse
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

API_ID = "24297842"
API_HASH = "03c06aeb6d9b9adc9e16511a4b0ce2d3"
SESSION = os.getenv("SESSION_NAME", "jobs_session_api")
CHANNEL = os.getenv("CHANNEL", "jobs_and_internships_updates")
API_KEY = "5999"

app = FastAPI()
client = TelegramClient(SESSION, API_ID, API_HASH)
client_lock = asyncio.Lock()

def require_api_key(x_api_key: str = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "Unauthorized")

@app.on_event("startup")
async def startup():
    await client.start()
    print("✅ Telegram client started with session:", SESSION)

@app.on_event("shutdown")
async def shutdown():
    await client.disconnect()
    print("❌ Telegram client stopped")

@app.get("/latest-messages", dependencies=[Depends(require_api_key)])
async def latest_messages(limit: int = 10):
    messages = []
    async with client_lock:
        try:
            async for msg in client.iter_messages(CHANNEL, limit=limit*2):
                if msg.text:
                    messages.append({"id": msg.id, "date": msg.date.isoformat(), "text": msg.text})
                if len(messages) >= limit:
                    break
        except RpcError as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {"messages": list(reversed(messages))}

@app.get("/latest-messages-txt", response_class=PlainTextResponse, dependencies=[Depends(require_api_key)])
async def latest_messages_txt(limit: int = 10):
    data = await latest_messages(limit)
    texts = [m["text"] for m in data["messages"]]
    return ("\n#####\n").join(texts)
