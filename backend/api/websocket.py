"""
NEXUS WebSocket Handler — Real-time bidirectional communication.

Streams execution events to clients and receives HITL responses.
"""
from __future__ import annotations
import os
import json
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from engine.state_machine import ExecutionEngine
from engine.hitl import hitl_manager
from db.database import update_execution, save_event, get_execution
from config import UPLOAD_DIR
import datetime

logger = logging.getLogger(__name__)

# Active WebSocket connections per execution
active_connections: dict[str, list[WebSocket]] = {}


async def websocket_handler(websocket: WebSocket, execution_id: str):
    """
    Handle a WebSocket connection for an execution.
    
    Flow:
    1. Client connects with execution_id
    2. Server starts (or reconnects to) the execution
    3. Server streams events in real-time
    4. Client can send HITL responses
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {execution_id}")

    # Register connection
    if execution_id not in active_connections:
        active_connections[execution_id] = []
    active_connections[execution_id].append(websocket)

    try:
        # Check if this is a replay (execution already completed)
        existing = await get_execution(execution_id)
        if existing and existing.get("status") in ("completed", "aborted"):
            # Send replay events
            for event in existing.get("events", []):
                payload = event.get("payload", "{}")
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except Exception:
                        payload = {}
                await websocket.send_json({
                    "event_type": event.get("event_type", "log"),
                    "timestamp": event.get("timestamp", ""),
                    "agent": event.get("agent", ""),
                    "step_id": event.get("step_id"),
                    "message": event.get("message", ""),
                    "data": payload.get("data"),
                    "dag_state": payload.get("dag_state"),
                })
                await asyncio.sleep(0.05)  # Small delay for replay effect
            return

        # Load execution metadata
        meta_path = os.path.join(UPLOAD_DIR, f"{execution_id}_meta.json")
        task = ""
        uploaded_files = []

        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
            task = meta.get("task", "")
            uploaded_files = meta.get("uploaded_files", [])
        elif existing:
            task = existing.get("task", "")

        if not task:
            await websocket.send_json({
                "event_type": "error",
                "message": "No task found for this execution.",
            })
            return

        # Create and run the execution engine
        engine = ExecutionEngine(execution_id, task, uploaded_files)

        # Event callback — broadcasts to all connected WebSockets
        async def broadcast_event(event: dict):
            # Save to database
            await save_event(
                execution_id=execution_id,
                event_type=event.get("event_type", "log"),
                agent=event.get("agent", ""),
                step_id=event.get("step_id"),
                message=event.get("message", ""),
                payload={"data": event.get("data"), "dag_state": event.get("dag_state")},
                dag_state=event.get("dag_state"),
            )

            # Broadcast to all connected clients
            disconnected = []
            for ws in active_connections.get(execution_id, []):
                try:
                    await ws.send_json(event)
                except Exception:
                    disconnected.append(ws)
            # Clean up disconnected
            for ws in disconnected:
                if ws in active_connections.get(execution_id, []):
                    active_connections[execution_id].remove(ws)

        engine.on_event(broadcast_event)

        # Run engine as a background task so we can listen for HITL inputs
        engine_task = asyncio.create_task(engine.run())

        # Listen for client messages (HITL responses)
        try:
            while not engine_task.done():
                try:
                    # Wait for client message with timeout
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=1.0,
                    )
                    # Parse HITL response
                    try:
                        data = json.loads(message)
                        if data.get("type") == "hitl_response":
                            selected = data.get("selected_option", "")
                            hitl_manager.submit_response(execution_id, selected)
                            logger.info(f"HITL response received: {selected}")
                    except json.JSONDecodeError:
                        pass
                except asyncio.TimeoutError:
                    continue
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected during execution: {execution_id}")
                    break
        except Exception as e:
            logger.error(f"WebSocket listener error: {e}")

        # Wait for engine to finish
        try:
            result = await asyncio.wait_for(engine_task, timeout=600)
        except asyncio.TimeoutError:
            result = {"status": "aborted"}

        # Update execution record
        status = result.get("status", "completed")
        plan = result.get("plan", {})
        total_steps = len(plan.get("steps", []))

        await update_execution(
            execution_id,
            status=status,
            completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            total_steps=total_steps,
            plan_json=json.dumps(plan),
        )

        # Clean up meta file
        if os.path.exists(meta_path):
            os.remove(meta_path)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {execution_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "event_type": "error",
                "message": f"Server error: {str(e)}",
            })
        except Exception:
            pass
    finally:
        # Cleanup
        if execution_id in active_connections:
            if websocket in active_connections[execution_id]:
                active_connections[execution_id].remove(websocket)
            if not active_connections[execution_id]:
                del active_connections[execution_id]
