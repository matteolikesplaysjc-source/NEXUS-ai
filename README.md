# NEXUS AI

A web-based AI chat app built with FastAPI and a simple responsive frontend.

## Features
- Responsive chat UI with a conversation transcript
- Server-side AI API calls (the API key is never sent to the browser)
- Clear errors when the AI provider is not configured
- Health endpoint for hosting checks
- Ready for deployment on Render

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
4. Add your AI provider key to `.env` as `GROQ_API_KEY=your_key_here`.
5. Start the app with `uvicorn app:app --reload`.
6. Open http://127.0.0.1:8000.

You can also run `python app.py` after installing dependencies.

## Deploy on Render
1. Create a Render Web Service from this GitHub repository.
2. Use the Python runtime.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add `GROQ_API_KEY` in Render's Environment settings. Optionally set `GROQ_MODEL`.
6. Deploy. Render will provide an HTTPS `onrender.com` address.

## Environment variables
- `GROQ_API_KEY` — required for AI answers; keep it private.
- `GROQ_MODEL` — optional model override; default is `llama-3.3-70b-versatile`.

Never put API keys in frontend JavaScript or commit your real `.env` file. The included `.gitignore` excludes it.

## Important
This is a starter app, not a finished multi-user commercial service. Before sharing widely, add authentication, rate limits, usage limits, monitoring, and an appropriate privacy policy. The free hosting tier may sleep when idle, and local files on free hosting may not persist.
