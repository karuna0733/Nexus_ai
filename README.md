# Nexus AI ◈ Modern Chat Assistant

Nexus AI is a sleek, modern, single-page chat assistant application built using **FastAPI** on the backend and a premium, responsive glassmorphic design on the frontend. It features seamless integration with **Google Gemini API**, **Groq Cloud**, and **Local Ollama** models.

---

## ⚡ Features

- **Gorgeous Dark/Glassmorphic UI**: Vibrant, responsive chat interface featuring smooth animations, hover effects, and auto-growing input textareas.
- **Ultra-Fast Streaming Responses**: Leverages Server-Sent Events (SSE) to stream AI responses in real-time.
- **Authentication & Persistence**: Built-in registration, login, session cookies (`nx_tok`), and chat history storage using an optimized local SQLite database (`nexus.db`).
- **Flexible AI Backends**:
  - **Gemini AI** (Recommended) for ultra-fast, high-quality responses.
  - **Groq Cloud** for high-speed Open Source models (Llama 3.1, etc.).
  - **Local Ollama** (fallback) for offline operation.
- **File Upload & Image Recognition**: Support for text, code, and image uploads (utilizing Gemini and Groq Vision capabilities).
- **Vercel Ready**: Preconfigured `vercel.json` for rapid hosting.

---

## 🛠️ Local Setup & Installation

### 1. Clone & Navigate
Ensure you are in the project root directory:
```bash
cd nexusai
```

### 2. Configure Environment Variables
Create a file named `.env` inside the `nexusai` folder and add your API keys:
```env
# Gemini API Key (Get it from Google AI Studio)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Groq API Key (Optional)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Ollama fallback (Optional)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b
```

### 3. Run the Server
Use the preconfigured virtual environment to launch the application:

* **Command Prompt (CMD)**:
  ```cmd
  venv\Scripts\python main.py
  ```
* **PowerShell**:
  ```powershell
  venv\Scripts\python main.py
  ```
* **Unix / macOS** (if migrating):
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  python main.py
  ```

Once started, open your browser and navigate to: **[http://localhost:8000](http://localhost:8000)**

---

## 🚀 Deployment

The project includes a `vercel.json` configuration file, ready for seamless deployment on [Vercel](https://vercel.com).
To deploy:
1. Push your repository to GitHub.
2. Link the repository to your Vercel account.
3. Add your `GEMINI_API_KEY` (and any other keys) in the **Environment Variables** section on Vercel settings.
4. Deploy!
