# NEXUS AI

A web-based AI chat app built with FastAPI, Groq, and a responsive frontend.

## Features
- AI chat powered by Groq (the API key stays on the server)
- **Persistent, user-managed memory** stored in SQLite
- Saved memories are included in future AI requests for that browser
- Add and delete memories in the Memory panel
- Health endpoint for hosting checks

## Run locally (Windows)
1. Install Python 3.11 or newer.
2. Open a terminal in this folder.
3. Run:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
4. Add your Groq key to `.env`: `GROQ_API_KEY=your_key_here`.
5. Start the app with `uvicorn app:app --reload`.
6. Open http://127.0.0.1:8000.

## Deploy on Render
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Add `GROQ_API_KEY` in Render's Environment settings.
- Set `NEXUS_DB_PATH` to a path on a mounted persistent disk, for example `/var/data/nexus.db`, if you want memories to survive redeploys/restarts. Without persistent disk, local SQLite data on an ephemeral host can be lost.

## Memory and privacy
Memories are explicitly added and deleted by the user in the Memory panel. They are separated using a random browser ID stored in that browser's local storage. This is a lightweight personal-project setup, **not account authentication**; do not use it for sensitive information or as a public multi-user service without adding real sign-in and access controls.

## Environment variables
- `GROQ_API_KEY` — required; keep private.
- `GROQ_MODEL` — optional; defaults to `llama-3.3-70b-versatile`.
- `NEXUS_DB_PATH` — optional SQLite file path; defaults to `data/nexus.db`.

Never put API keys in frontend JavaScript or commit your real `.env` file.
