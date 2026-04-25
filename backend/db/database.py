"""
NEXUS Database — Async SQLite setup and operations.
"""
import aiosqlite
import json
import datetime
from config import DATABASE_PATH


async def init_db():
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'planning',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                duration_seconds REAL,
                total_steps INTEGER DEFAULT 0,
                plan_json TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS execution_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                agent TEXT DEFAULT '',
                step_id INTEGER,
                message TEXT DEFAULT '',
                payload TEXT DEFAULT '{}',
                dag_state TEXT DEFAULT '{}',
                FOREIGN KEY (execution_id) REFERENCES executions(id)
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_execution 
            ON execution_events(execution_id)
        """)
        await db.commit()


async def create_execution(execution_id: str, task: str):
    """Insert a new execution record."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO executions (id, task, status, created_at) VALUES (?, ?, ?, ?)",
            (execution_id, task, "planning", datetime.datetime.now(datetime.timezone.utc).isoformat())
        )
        await db.commit()


async def update_execution(execution_id: str, **kwargs):
    """Update execution fields."""
    allowed = {"status", "completed_at", "duration_seconds", "total_steps", "plan_json"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [execution_id]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            f"UPDATE executions SET {set_clause} WHERE id = ?",
            values
        )
        await db.commit()


async def save_event(execution_id: str, event_type: str, agent: str = "",
                     step_id: int = None, message: str = "",
                     payload: dict = None, dag_state: dict = None):
    """Persist an execution event."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO execution_events 
               (execution_id, timestamp, event_type, agent, step_id, message, payload, dag_state)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                execution_id,
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
                event_type,
                agent,
                step_id,
                message,
                json.dumps(payload or {}),
                json.dumps(dag_state or {})
            )
        )
        await db.commit()


async def get_executions():
    """List all executions, most recent first."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM executions ORDER BY created_at DESC LIMIT 50"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_execution(execution_id: str):
    """Get full execution detail with events."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM executions WHERE id = ?", (execution_id,)
        )
        execution = await cursor.fetchone()
        if not execution:
            return None
        execution = dict(execution)

        cursor = await db.execute(
            "SELECT * FROM execution_events WHERE execution_id = ? ORDER BY id",
            (execution_id,)
        )
        events = await cursor.fetchall()
        execution["events"] = [dict(e) for e in events]
        return execution
