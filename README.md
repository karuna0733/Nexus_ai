# ◈ Nexus AI — Modern Chat Assistant

**A single-file FastAPI chat application with a glassmorphic 3D UI, multi-provider LLM backends, streaming responses, voice input, and built-in usage-based subscription tiers.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-r128-000000?logo=three.js&logoColor=white)](https://threejs.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Persistence-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black?logo=vercel&logoColor=white)](https://vercel.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)

---

## Overview

Nexus AI is a self-contained chat assistant that pairs a single FastAPI backend with an embedded, animated frontend — no separate frontend build, no template engine, just one file serving a fast, good-looking chat experience. It's built to route between multiple LLM providers, so it keeps working whether you have a paid API key, a free-tier key, or nothing but a local Ollama install.

**Design choice worth calling out:** the entire UI is embedded as an HTML string returned by FastAPI rather than split into a `templates/` + `static/` structure. This was a deliberate simplification to avoid Jinja2/static-file path issues across different hosting environments (especially serverless platforms like Vercel), at the cost of a larger single file.

---

## ⚡ Features

| Feature | Details |
|---|---|
| **Glassmorphic 3D UI** | Dark, glassmorphic interface with a live animated **Three.js** background, smooth transitions, and auto-growing input fields. |
| **Streaming responses** | Uses **Server-Sent Events (SSE)** so AI replies stream token-by-token instead of waiting for the full response. |
| **Multi-provider LLM routing** | Supports **Google Gemini**, **Groq Cloud** (Llama 3.1 and other OSS models), and **local Ollama** as a fully offline fallback. |
| **Auth & persistence** | Registration, login, and session-cookie (`nx_tok`) based auth, with conversation history persisted in a local **SQLite** database (`nexus.db`). |
| **Usage-based plans** | Built-in `free` / `pro` / `enterprise` tiers with per-plan message limits, enforced server-side and queryable via `/api/usage`. |
| **File & image uploads** | Upload text, code, or image files (up to 10 MB) for the model to read or, for images, analyze via Gemini/Groq vision. |
| **Voice input** | Browser speech-recognition integration for hands-free message input. |
| **Deploy-ready** | Preconfigured `vercel.json` for one-click serverless deployment. |

---

## 🧰 Tech Stack

- **Backend:** FastAPI + Uvicorn
- **Frontend:** Embedded HTML/CSS/JS (single file), Three.js (r128) for the animated background
- **Database:** SQLite (`nexus.db`)
- **LLM providers:** Google Gemini API, Groq Cloud API, local Ollama
- **Transport:** Server-Sent Events for streaming chat responses
- **Hosting:** Vercel (serverless Python)

---

## 📡 API Reference

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Serves the chat UI |
| `GET` | `/login` | Serves the login/register UI |
| `POST` | `/api/auth/register` | Create a new account |
| `POST` | `/api/auth/login` | Log in and receive a session cookie |
| `POST` | `/api/auth/logout` | Clear the session |
| `GET` | `/api/convs` | List a user's conversations |
| `GET` | `/api/history/{sid}` | Fetch a conversation's message history |
| `DELETE` | `/api/convs/{sid}` | Delete a conversation |
| `GET` | `/api/usage` | Get current usage against the user's plan limit |
| `POST` | `/api/subscribe` | Change subscription plan (`free`, `pro`, `enterprise`) |
| `POST` | `/api/upload` | Upload a text/code/image file (max 10 MB) |
| `POST` | `/api/chat` | Send a message and stream back the AI response (SSE) |

### Subscription tiers

| Plan | Monthly message limit |
|---|---|
| `free` | 50 |
| `pro` | 500 |
| `enterprise` | Unlimited (effectively) |

---

## 🚀 Local Setup

### 1. Clone & navigate
```bash
cd nexusai
```

### 2. Configure environment variables
Create a `.env` file inside the `nexusai` folder:
```env
# Gemini API Key (Get it from Google AI Studio) — recommended primary provider
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Groq API Key (optional secondary provider)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Ollama fallback (optional, fully offline)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b
```

### 3. Install dependencies & run
**Windows (CMD / PowerShell):**
```powershell
venv\Scripts\python -m pip install -r requirements.txt
venv\Scripts\python main.py
```

**Unix / macOS:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Then open **http://localhost:8000**.

---

## ☁️ Deployment (Vercel)

The repo ships with a `vercel.json` pointing at `nexusai/main.py`:

```json
{
  "version": 2,
  "builds": [{ "src": "nexusai/main.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "nexusai/main.py" }]
}
```

1. Push the repository to GitHub.
2. Import it into [Vercel](https://vercel.com).
3. Add `GEMINI_API_KEY` (and any other keys you're using) under **Project Settings → Environment Variables**.
4. Deploy.

> Note: Vercel's serverless filesystem is ephemeral, so SQLite data (`nexus.db`) won't persist across deployments/cold starts in that environment. For durable multi-user persistence in production, swap in a hosted database (e.g. Postgres, Turso, or Supabase).

---

## 📁 Project Structure

```
karuna/
├── nexusai/
│   ├── main.py            # FastAPI app: routes, SSE chat, embedded HTML/CSS/JS UI
│   ├── database.py        # SQLite schema, auth, usage tracking, plan limits
│   ├── rendered.html       # Rendered reference copy of the UI
│   └── requirements.txt
├── requirements.txt         # Root requirements (mirrors nexusai/requirements.txt)
├── vercel.json              # Vercel serverless deployment config
└── .github/agents/          # Agent configuration
```

---

## 🗺️ Roadmap

- [ ] Swap SQLite for a hosted database for durable multi-user deployment
- [ ] Add streaming voice output (text-to-speech) to match voice input
- [ ] Per-conversation model switching (choose Gemini/Groq/Ollama per chat)
- [ ] Usage dashboard with historical charts

---

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

**Karunakaran A** — Final-year CSE student focused on cybersecurity, ethical hacking, and AI-powered application development.
[GitHub](https://github.com/karuna0733) · [LinkedIn](https://www.linkedin.com/in/karunakaran-a-88aaa82b9)
