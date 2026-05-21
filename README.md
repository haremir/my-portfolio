# Harun Emirhan Bostancı - Portfolio & AI Assistant

> **AI-powered personal operating system built entirely in Python.**
> Portfolio · Blog · Admin Dashboard · Telegram Ops · RAG Chatbot

A modern, full-stack personal portfolio and blog built entirely in Python using [Reflex](https://reflex.dev/). This project goes beyond a static site by integrating an AI-powered assistant (RAG), a comprehensive admin dashboard, and Telegram Ops for real-time visitor analytics.

## ✨ Features

- **Full-Stack Python**: Both frontend and backend are written purely in Python via Reflex.
- **AI Chat Assistant**: Embedded RAG chatbot powered by the Groq API (Llama-3) that can answer questions about my CV, projects, and skills.
- **Admin Dashboard**: Secure, UI-driven management for:
  - Blog posts, Portfolio Projects, and Case Studies.
  - Skills and Career History (Education & Experience).
  - AI Assistant parameters (System Prompt, Context, Temperature).
  - Visitor Chat Logs & Analytics.
- **Telegram Ops Integration**: A dedicated Telegram bot that alerts the admin about new interactions on the site, provides chat transcripts, and uses AI to summarize visitor intent.
- **Markdown & Code Highlighting**: Beautifully rendered blog posts and project case studies.
- **Responsive Design**: Fully optimized for desktop and mobile viewing with modern UI/UX principles.

## 🛠️ Tech Stack

- **Framework**: [Reflex](https://reflex.dev/) (React under the hood, written in Python)
- **Database**: SQLite with `SQLModel` & `SQLAlchemy`
- **AI / LLM**: [Groq API](https://groq.com/) (Llama-3 models)
- **Bot Integration**: `python-telegram-bot`
- **Package Manager**: [uv](https://github.com/astral-sh/uv)

## 🚀 Getting Started

### Prerequisites

- Python >= 3.12
- `uv` package manager installed
- A [Groq API Key](https://console.groq.com/keys)
- A Telegram Bot Token (from BotFather)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd my-portfolio
   ```

2. **Set up environment variables**
   Copy the example environment file and fill in your keys:
   ```bash
   cp .env.example .env
   ```
   *Make sure to configure `GROQ_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_ID`, and `ADMIN_PASSWORD`.*

3. **Install dependencies**
   ```bash
   uv sync
   ```

### Running the Application

To start both the Reflex web server and the Telegram bot concurrently, use the custom dev runner:

```bash
uv run site
```

This will launch:
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://0.0.0.0:8004`
- **Telegram Bot**: Polling in the background

### How it works

`uv run site` starts three concurrent processes:
- Reflex frontend (React/Python)  
- Reflex backend (FastAPI under the hood)
- Telegram bot (polling mode)

Graceful shutdown on Ctrl+C kills all child processes cleanly.

## 📁 Project Structure

- `harun_site/pages/` - Frontend pages (Home, About, Portfolio, Blog, Admin)
- `harun_site/state/` - Application state management and backend logic
- `harun_site/components/` - Reusable UI components (Navbar, Footer, Chat)
- `harun_site/telegram_bot/` - Telegram bot handlers and AI Ops logic
- `harun_site/utils/` - Helpers for Markdown parsing, LLM clients, and data management
- `data/` - JSON configuration for tags, skills, and chat memory
- `posts/` - Markdown files for blog posts
- `rxconfig.py` - Core Reflex configuration

## 🤝 License
This project is intended for personal portfolio usage.
