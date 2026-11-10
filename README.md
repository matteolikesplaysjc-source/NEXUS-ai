# NEXUS AI

NEXUS is a FastAPI-powered AI chat workspace with account sign-up/sign-in, saved conversations, editable memories, and text/Markdown/CSV/JSON/PDF uploads. AI responses use the Groq API; the API key stays on the server.

## Run locally (Windows)

1. Install Python 3.11 or newer.
2. Download/clone this repository and open a terminal in its folder.
3. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
4. Edit `.env` and set:
   - `GROQ_API_KEY` to your private provider key.
   - `NEXUS_SECRET_KEY` to a long random secret string.
   - Keep `COOKIE_SECURE=false` for local HTTP testing.
5. Start NEXUS:
   ```powershell
   uvicorn app:app --reload
   ```
6. Open http://127.0.0.1:8000.

## Deploy on Render

1. In Render, create a **Web Service** and connect this repository.
2. Render should detect the included `render.yaml`; if configuring manually, use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
3. Add private environment variables in Render:
   - `GROQ_API_KEY`: your provider key.
   - `NEXUS_SECRET_KEY`: a long, randomly generated secret. Do not commit it.
   - `COOKIE_SECURE`: `true` for HTTPS deployment.
4. Deploy, then open the HTTPS URL Render gives your service.

The `/health` endpoint can be used for health checks.

## Important deployment notes

- **Never commit a real `.env` file or API key.** The provided `.gitignore` excludes `.env`, virtual environments, and the local `data/` folder.
- The app stores accounts, conversations, memories, and uploads in SQLite/local files. On a free host, that data may be lost during redeploys or restarts. Use persistent storage or a managed database before relying on it for long-term data.
- Before opening the app to the public, consider rate limits, abuse protection, backups, privacy disclosures, and monitoring.
- A working website also requires a valid provider key and available model/usage quota. GitHub stores the source code; it does not host the running AI service by itself.
