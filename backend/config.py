"""
NEXUS Configuration — Environment variables and defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI LLM ──
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ── Server ──
PORT = int(os.getenv("PORT", 8000))
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# ── Execution Engine ──
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 2))
HITL_CONFIDENCE_THRESHOLD = float(os.getenv("HITL_CONFIDENCE_THRESHOLD", 0.6))
WORKER_TIMEOUT_SECONDS = int(os.getenv("WORKER_TIMEOUT_SECONDS", 60))

# ── Database ──
DATABASE_PATH = os.getenv("DATABASE_PATH", "nexus.db")

# ── File Storage ──
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/nexus_uploads")
ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "/tmp/nexus_artifacts")
