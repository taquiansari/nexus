# 🌀 NEXUS — AI Task Execution Agent

> **Autonomous multi-step task execution engine with real-time streaming, self-healing recovery, and human-in-the-loop breakpoints.**

![Architecture](https://img.shields.io/badge/Architecture-State_Machine-6366f1)
![LLM](https://img.shields.io/badge/LLM-Groq_Llama_3.3-06b6d4)
![Frontend](https://img.shields.io/badge/Frontend-Next.js_14-000000)
![Backend](https://img.shields.io/badge/Backend-FastAPI-10b981)

---

## 🚀 What is NEXUS?

NEXUS transforms complex natural-language instructions into orchestrated, multi-step workflows. It doesn't just plan — it **executes, evaluates, self-heals, and asks for help when it's stuck**.

### Key Features

- **🧠 Intelligent Planning**: Decomposes complex tasks into executable steps using Groq LLM
- **⚡ Specialist Workers**: 6 dedicated workers (Data Processing, Chart Generation, Report Building, API Handling, Text Transformation, Web Research)
- **🔍 Critic Evaluation**: Every step is evaluated for quality — bad outputs trigger automatic recovery
- **🔄 Self-Healing Recovery**: Failed steps are re-planned with alternative approaches (up to 2 retries)
- **👤 Human-in-the-Loop**: Agent pauses for ambiguous/high-risk decisions and asks the user
- **📊 Live DAG Visualization**: Interactive execution graph that lights up in real-time
- **📝 Real-time Execution Logs**: WebSocket-powered streaming with color-coded entries
- **📥 Downloadable Artifacts**: Generated charts and PDF reports available for download
- **📜 Execution History**: Browse and replay past executions

---

## 🏗️ Architecture

```
Frontend (Vercel)          Backend (Railway)
┌─────────────────┐       ┌──────────────────────────┐
│   Next.js 14    │──REST──│     FastAPI Server        │
│                 │       │                            │
│  ┌─DAG Viewer─┐ │       │  ┌─Orchestrator─────────┐ │
│  │  React Flow │ │◄─WSS─│  │  (Groq LLM Planner)  │ │
│  └────────────┘ │       │  └──────────────────────┘ │
│                 │       │                            │
│  ┌─Exec Log──┐  │       │  ┌─Workers──────────────┐ │
│  │  Stream    │  │       │  │ DataProcessor        │ │
│  └───────────┘  │       │  │ ChartGenerator       │ │
│                 │       │  │ ReportBuilder         │ │
│  ┌─HITL─────┐  │       │  │ APIHandler            │ │
│  │  Modal   │───│─WSS──│  │ TextTransformer       │ │
│  └──────────┘   │       │  │ WebResearcher         │ │
└─────────────────┘       │  └──────────────────────┘ │
                          │                            │
                          │  ┌─Critic────────────────┐ │
                          │  │  (Quality Evaluator)   │ │
                          │  └──────────────────────┘ │
                          │                            │
                          │  SQLite │ Groq API          │
                          └──────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| LLM | Groq (Llama 3.3 70B) | Fast inference, free tier |
| Backend | FastAPI + Python | Async-native, WebSocket support |
| Frontend | Next.js 14 + TypeScript | React ecosystem, App Router |
| DAG Viz | React Flow | Purpose-built interactive graphs |
| State Mgmt | Zustand | Lightweight, no boilerplate |
| Animations | Framer Motion | Spring physics animations |
| Real-time | WebSockets | Bidirectional (streaming + HITL) |
| Database | SQLite (aiosqlite) | Zero-config, portable |
| PDF Gen | fpdf2 | No system dependencies |
| Deployment | Vercel + Railway | Free tier, easy setup |

---

## 📦 Setup & Installation

### Prerequisites

- **Python 3.11+** — [python.org](https://python.org)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **Groq API Key** — Free at [console.groq.com](https://console.groq.com)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/nexus-agent.git
cd nexus-agent
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Generate sample data
python data/generate_sample.py

# Start the server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local if using a different backend URL

# Start dev server
npm run dev
```

### 4. Open the dashboard

Navigate to **http://localhost:3000** 🎉

---

## 🎯 Demo Scenario

### "Messy CSV → Financial Report"

1. Open the dashboard
2. Enter this task:
   > "I have a CSV file of raw sales transactions for 2025. The data is messy — there are missing values, inconsistent date formats, and duplicate entries. Clean the data, calculate monthly revenue trends, identify the best-performing product category, generate a bar chart, and create a PDF report."
3. Upload the sample CSV (`backend/data/sample_sales.csv`)
4. Click **Execute Task**
5. Watch the agent plan, execute, evaluate, and deliver!

### What you'll see:

- 🧠 Orchestrator decomposes into 4-5 steps
- ⚡ DataProcessor cleans and analyzes the CSV
- 📊 ChartGenerator creates a revenue bar chart
- 📄 ReportBuilder compiles a PDF report
- ⚠️ HITL may trigger for data cleaning decisions
- 🔄 Recovery if a step fails
- 📥 Download the generated chart and report

---

## 🚀 Deployment

### Backend → Railway

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select the repository and set **Root Directory** to `backend`
4. Add environment variables:
   - `GROQ_API_KEY=your_key`
   - `ALLOWED_ORIGINS=https://your-app.vercel.app`
5. Railway auto-deploys. Copy the generated URL.

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → New Project → Import from GitHub
2. Set **Root Directory** to `frontend`
3. Add environment variables:
   - `NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app`
   - `NEXT_PUBLIC_WS_URL=wss://your-railway-url.up.railway.app`
4. Deploy!

---

## 📁 Project Structure

```
aitaskexecutionagent/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Environment config
│   ├── agents/               # Orchestrator, Critic, Memory
│   ├── workers/              # 6 specialist workers
│   ├── engine/               # State machine, HITL manager
│   ├── api/                  # REST routes, WebSocket handler
│   ├── db/                   # SQLite database layer
│   └── data/                 # Sample CSV dataset
│
├── frontend/
│   ├── app/                  # Next.js pages (dashboard, history)
│   ├── components/           # React components
│   ├── hooks/                # Zustand store, WebSocket hook
│   └── styles/               # CSS design system
│
├── .gitignore
└── README.md
```

---

## 🧪 Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Cyclic state machine** over linear chains | Recovery loops require cycling back from EVALUATE to EXECUTE — impossible with linear pipelines |
| **WebSockets** over SSE | Bidirectional: server streams events AND client sends HITL decisions |
| **Groq** over OpenAI | 10x faster inference at free tier — critical for real-time UX |
| **fpdf2** over WeasyPrint | No system-level dependencies — deploys cleanly on Railway |
| **SQLite** over Postgres | Zero-config, ships in the container — perfect for demos |
| **Zustand** over Redux | 80% less boilerplate for the same state management capability |

---

## 📝 License

MIT
