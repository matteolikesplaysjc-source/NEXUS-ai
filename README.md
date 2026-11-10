# NEXUS AI v3

A personal AI chat web app with accounts, saved memory, persistent chat history, document uploads, and browser voice features.

## Features
- Email + password accounts; passwords are hashed with PBKDF2-HMAC-SHA256.
- Signed, HTTP-only session cookie.
- User-owned long-term memories: create, edit, and delete.
- Conversations and messages stored in SQLite and restored after refresh.
- Upload TXT, Markdown, CSV, JSON, and PDF files (up to 5 MB each); text is extracted and added as context to a chat.
- Voice input using the browser Speech Recognition API when supported; spoken answers using Speech Synthesis.
- Groq API integration with configurable model; API key remains on the server.

## Run locally (Windows)
1. Install Python 3.11+.
2. In this folder, run:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
3. Edit `.env` and set `GROQ_API_KEY` and a long random `NEXUS_SECRET_KEY`.
4. Run `uvicorn app:app --reload`.
5. Open http://127.0.0.1:8000.

## Deploy
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Add `GROQ_API_KEY`, `NEXUS_SECRET_KEY`, and `GROQ_MODEL` as private environment variables.
- Attach persistent storage and set `NEXUS_DB_PATH` and `NEXUS_UPLOAD_DIR` to paths on it.
- Set `COOKIE_SECURE=true` when using HTTPS.
- Ensure the host's storage is backed up; SQLite and uploaded files are stored on disk.

## Important setup notes
- The default model is `openai/gpt-oss-120b` on Groq. Set `GROQ_MODEL` to another model currently enabled for your Groq account if needed. Model availability and pricing are controlled by the provider.
- Voice input depends on browser support for the Web Speech API and may require microphone permission. Spoken output uses the browser's speech engine.
- PDF text extraction works for text-based PDFs, not scanned image-only PDFs.
- This starter account system does not include email verification, password reset, MFA, or social login. Add those before using it for a public production service.
- Use HTTPS in production. Do not commit real API keys or secret keys.

## Existing data
The v3 schema creates new account-based tables. The old anonymous browser-ID memories are not automatically migrated into accounts. Back up your database before deploying schema changes.
