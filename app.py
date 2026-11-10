import os
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="NEXUS AI", version="2.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)

class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=40)

@app.get("/")
async def home():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "app": "NEXUS AI", "version": "2.0.0"}

@app.post("/api/chat")
async def chat(body: ChatRequest):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="NEXUS needs an AI provider key before it can answer. Add GROQ_API_KEY to your local .env file or your host's private environment settings."
        )

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    messages = [
        {
            "role": "system",
            "content": (
                "You are NEXUS, a helpful, capable AI assistant. Be accurate, clear, "
                "and practical. For coding questions, give working examples and explain "
                "where code belongs. If you are unsure, say so instead of inventing facts. "
                "Do not claim to have performed actions outside this chat."
            ),
        }
    ]
    messages.extend({"role": m.role, "content": m.content} for m in body.messages[-30:])

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=15.0)) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                },
            )
        if response.status_code >= 400:
            detail = "The AI provider returned an error. Check the provider key, model name, and usage limits."
            try:
                provider_message = response.json().get("error", {}).get("message")
                if provider_message:
                    detail = str(provider_message)[:500]
            except Exception:
                pass
            raise HTTPException(status_code=502, detail=detail)

        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise HTTPException(status_code=502, detail="The AI provider returned an empty answer.")
        return {"reply": answer, "model": model}
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="The AI request timed out. Please try again.")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not reach the AI provider. Please try again.")
    except (KeyError, IndexError, TypeError, ValueError):
        raise HTTPException(status_code=502, detail="The AI provider returned an unexpected response.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=int(os.getenv("PORT", "8000")), reload=False)
