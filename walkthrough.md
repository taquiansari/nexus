# NEXUS — Build Walkthrough

## What Was Built

A full-stack **AI Task Execution Agent** — an autonomous system that takes a complex natural-language instruction, decomposes it into steps, executes them with specialist workers, self-heals on failure, supports human-in-the-loop breakpoints, and streams the entire process in real-time.

## Dashboard Preview

![NEXUS Dashboard](C:\Users\ASUS\.gemini\antigravity\brain\1f6f6eb1-b5af-4cb5-91c3-1de8403de715\dashboard_screenshot.png)

## Files Created

### Backend (FastAPI + Python) — 19 files

| File | Purpose |
|------|---------|
| [main.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/main.py) | FastAPI entry point with CORS, REST routes, WebSocket, health check |
| [config.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/config.py) | Environment variables (Groq key, origins, timeouts) |
| [requirements.txt](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/requirements.txt) | Python dependencies (unpinned for compatibility) |
| [agents/orchestrator.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/agents/orchestrator.py) | Planner — decomposes tasks into JSON step arrays via Groq LLM |
| [agents/critic.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/agents/critic.py) | Evaluator — checks worker outputs, triggers HITL on low confidence |
| [agents/memory.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/agents/memory.py) | Context accumulation across steps for re-planning |
| [workers/base_worker.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/workers/base_worker.py) | Abstract worker with timeout enforcement |
| [workers/data_processor.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/workers/data_processor.py) | LLM-generated pandas code execution for CSV operations |
| [workers/chart_generator.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/workers/chart_generator.py) | LLM-generated matplotlib chart creation |
| [workers/report_builder.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/workers/report_builder.py) | PDF report generation via fpdf2 |
| [workers/api_handler.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/workers/api_handler.py) | HTTP request worker with retry + backoff |
| [workers/text_transformer.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/workers/text_transformer.py) | LLM-driven text operations |
| [workers/web_researcher.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/workers/web_researcher.py) | DuckDuckGo search + scrape |
| [engine/state_machine.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/engine/state_machine.py) | Core execution engine — PLAN → EXECUTE → EVALUATE → RECOVER/HITL flow |
| [engine/state.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/engine/state.py) | TypedDict state schema |
| [engine/hitl.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/engine/hitl.py) | asyncio.Event-based pause/resume for human decisions |
| [api/routes.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/api/routes.py) | REST endpoints (execute, list, detail, artifacts) |
| [api/websocket.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/api/websocket.py) | WebSocket handler — event streaming + HITL response listener |
| [api/schemas.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/api/schemas.py) | Pydantic models for all data types |
| [db/database.py](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/db/database.py) | Async SQLite CRUD for executions + events |

### Frontend (Next.js 14) — 10 files

| File | Purpose |
|------|---------|
| [app/page.tsx](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/app/page.tsx) | Main dashboard — three-panel command center |
| [app/layout.tsx](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/app/layout.tsx) | Root layout with dark theme |
| [app/globals.css](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/app/globals.css) | Complete design system (500+ lines) |
| [app/history/page.tsx](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/app/history/page.tsx) | Execution history table |
| [components/TaskInput.tsx](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/components/TaskInput.tsx) | Task textarea + file upload + execute button |
| [components/ExecutionLog.tsx](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/components/ExecutionLog.tsx) | Real-time log stream with artifact download cards |
| [components/DagVisualizer.tsx](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/components/DagVisualizer.tsx) | React Flow live DAG with animated nodes |
| [components/HitlModal.tsx](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/components/HitlModal.tsx) | Human decision modal with spring animation |
| [components/ProgressBar.tsx](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/components/ProgressBar.tsx) | Step progress indicator |
| [hooks/useExecutionState.ts](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/hooks/useExecutionState.ts) | Zustand store for all execution state |
| [hooks/useWebSocket.ts](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/frontend/hooks/useWebSocket.ts) | WebSocket connection + event routing |

### Root & Deployment — 5 files

| File | Purpose |
|------|---------|
| [README.md](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/README.md) | Full documentation with setup + deployment |
| [.gitignore](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/.gitignore) | Python + Node.js + DB + temp files |
| [backend/Procfile](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/Procfile) | Railway process command |
| [backend/railway.json](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/railway.json) | Railway deploy config with health check |
| [backend/data/sample_sales.csv](file:///c:/Users/ASUS/Desktop/aitaskexecutionagent/backend/data/sample_sales.csv) | 524-row messy sales dataset for demo |

## Verification Results

| Check | Result |
|-------|--------|
| All Python imports | ✅ Pass |
| Backend server starts | ✅ `uvicorn` boots, health check returns `{"status":"healthy"}` |
| Frontend build | ✅ `next build` compiles successfully |
| Dashboard renders | ✅ Screenshot verified — three-panel layout, dark theme, glassmorphism |

## Remaining Steps for You

### 1. Create frontend env files

**`frontend/.env.local`** — create this file with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 2. Create backend .env with your Groq key

**`backend/.env`** — create this file with:
```
GROQ_API_KEY=gsk_your_actual_groq_key_here
GROQ_MODEL=llama-3.3-70b-versatile
ALLOWED_ORIGINS=http://localhost:3000
```

### 3. Test locally

```bash
# Terminal 1 — Backend
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open http://localhost:3000, enter the demo task, upload `backend/data/sample_sales.csv`, and click Execute.

### 4. Deploy

**Backend → Railway:**
- Root directory: `backend`
- Env vars: `GROQ_API_KEY`, `ALLOWED_ORIGINS=https://your-app.vercel.app`

**Frontend → Vercel:**
- Root directory: `frontend`
- Env vars: `NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app`, `NEXT_PUBLIC_WS_URL=wss://your-railway-url.up.railway.app`
