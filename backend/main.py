"""
NEXUS — AI Task Execution Agent
FastAPI application entry point.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from config import ALLOWED_ORIGINS, PORT, UPLOAD_DIR, ARTIFACTS_DIR
from db.database import init_db
from api.routes import router
from api.websocket import websocket_handler

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nexus")


# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🌀 NEXUS starting up...")
    await init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    logger.info("✅ Database initialized")
    logger.info(f"✅ Allowed origins: {ALLOWED_ORIGINS}")
    yield
    # Shutdown
    logger.info("🌀 NEXUS shutting down...")


# ── App ──
app = FastAPI(
    title="NEXUS — AI Task Execution Agent",
    description="Autonomous multi-step task execution engine with real-time streaming and human-in-the-loop.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST Routes ──
app.include_router(router, prefix="/api")


# ── Health Check ──
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nexus"}


# ── WebSocket ──
@app.websocket("/ws/{execution_id}")
async def ws_execution(websocket: WebSocket, execution_id: str):
    await websocket_handler(websocket, execution_id)


# ── Run ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
