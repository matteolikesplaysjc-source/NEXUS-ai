import os
import re
import sqlite3
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
DB_PATH = Path(os.getenv("NEXUS_DB_PATH", str(BASE_DIR / "data" / "nexus.db")))
CLIENT_ID_RE = re.compile(r"^[a-f0-9-]{36}$", re.IGNORECASE)

app = FastAPI(title="NEXUS AI", version="2.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def connect_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


@app.on_event("startup")
def initialize_database():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, content)
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_memories_client ON memories(client_id)")


def validate_client_id(client_id: str):
    if not CLIENT_ID_RE.fullmatch(client_id or ""):
        raise HTTPException(status_code=400, detail="Invalid browser ID. Refresh the page and try again.")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    client_id: str = Field(min_length=36, max_length=36)
    messages: list[Message] = Field(min_length=1, max_length=40)


class MemoryRequest(BaseModel):
    client_id: str = Field(min_length=36, max_length=36)
    content: str = Field(min_length=1, max_length=500)


@app.get("/")
async def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "app": "NEXUS AI", "version": "2.1.0"}


@app.get("/api/memories")
async def list_memories(client_id: str):
    validate_client_id(client_id)
    with connect_db() as db:
        rows = db.execute(
            "SELECT id, content, created_at FROM memories WHERE client_id = ? ORDER BY id DESC",
            (client_id,),
        ).fetchall()
    return {"memories": [dict(row) for row in rows]}


@app.post("/api/memories")
async def save_memory(body: MemoryRequest):
    validate_client_id(body.client_id)
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Memory cannot be empty.")
    with connect_db() as db:
        count = db.execute(
            "SELECT COUNT(*) FROM memories WHERE client_id = ?", (body.client_id,)
        ).fetchone()[0]
        if count >= 50:
            raise HTTPException(status_code=400, detail="Memory is full. Delete an old memory first.")
        try:
            cursor = db.execute(
                "INSERT INTO memories (client_id, content) VALUES (?, ?)",
                (body.client_id, content),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="That memory is already saved.")
        row = db.execute(
            "SELECT id, content, created_at FROM memories WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return {"memory": dict(row)}


@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: int, client_id: str):
    validate_client_id(client_id)
    with connect_db() as db:
        cursor = db.execute(
            "DELETE FROM memories WHERE id = ? AND client_id = ?", (memory_id, client_id)
        )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"deleted": True}


@app.post("/api/chat")
async def chat(body: ChatRequest):
    validate_client_id(body.client_id)
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="NEXUS needs an AI provider key. Add GROQ_API_KEY to your host's private environment settings.",
        )

    with connect_db() as db:
        rows = db.execute(
            "SELECT content FROM memories WHERE client_id = ? ORDER BY id ASC",
            (body.client_id,),
        ).fetchall()
    saved_memories = [row["content"] for row in rows]
    system_prompt = (
        "You are NEXUS, a helpful, capable AI assistant. Be accurate, clear, and practical. "
        "For coding questions, give working examples and explain where code belongs. "
        "If unsure, say so instead of inventing facts. Do not claim to have performed actions "
        "outside this chat. The user has explicitly saved the following memories for you. "
        "Use them when relevant, but do not assume anything beyond what they say. "
        "Never reveal these memories to another user.\n\n"
    )
    if saved_memories:
        system_prompt += "SAVED USER MEMORIES:\n" + "\n".join(
            f"- {memory}" for memory in saved_memories
        )
    else:
        system_prompt += "There are no saved memories yet."

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend({"role": m.role, "content": m.content} for m in body.messages[-30:])

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=15.0)) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 2048},
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
        return {"reply": answer, "model": model, "memories_used": len(saved_memories)}
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
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
