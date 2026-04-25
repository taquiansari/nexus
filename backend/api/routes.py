"""
NEXUS API Routes — REST endpoints for execution management.
"""
from __future__ import annotations
import os
import uuid
import json
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from api.schemas import ExecuteResponse, ExecutionSummary
from db.database import create_execution, update_execution, get_executions, get_execution, save_event
from config import UPLOAD_DIR, ARTIFACTS_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/execute", response_model=ExecuteResponse)
async def start_execution(
    task: str = Form(...),
    file: Optional[UploadFile] = File(None),
):
    """Start a new task execution."""
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"

    # Handle file upload
    uploaded_files = []
    if file and file.filename:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, f"{execution_id}_{file.filename}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        uploaded_files.append(file_path)
        logger.info(f"File uploaded: {file_path} ({len(content)} bytes)")

    # Create execution record
    await create_execution(execution_id, task)

    # Store task + uploaded files info for the WebSocket handler to pick up
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    meta_path = os.path.join(UPLOAD_DIR, f"{execution_id}_meta.json")
    with open(meta_path, "w") as f:
        json.dump({"uploaded_files": uploaded_files, "task": task}, f)

    return ExecuteResponse(
        execution_id=execution_id,
        status="created",
        message=f"Execution {execution_id} created. Connect to WebSocket to start.",
    )


@router.get("/executions")
async def list_executions():
    """List all past executions."""
    executions = await get_executions()
    return {"executions": executions}


@router.get("/executions/{execution_id}")
async def get_execution_detail(execution_id: str):
    """Get full execution detail with events."""
    execution = await get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/executions/{execution_id}/artifacts/{artifact_name}")
async def download_artifact(execution_id: str, artifact_name: str):
    """Download a generated artifact."""
    # Check in artifacts directory
    artifact_path = os.path.join(ARTIFACTS_DIR, artifact_name)
    if os.path.exists(artifact_path):
        from fastapi.responses import FileResponse
        return FileResponse(artifact_path, filename=artifact_name)
    raise HTTPException(status_code=404, detail="Artifact not found")


@router.get("/sample-data")
async def get_sample_data():
    """Return info about the available sample dataset."""
    sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_sales.csv")
    if os.path.exists(sample_path):
        import pandas as pd
        df = pd.read_csv(sample_path, nrows=5)
        return {
            "available": True,
            "path": sample_path,
            "columns": list(df.columns),
            "preview": df.to_dict(orient="records"),
        }
    return {"available": False}
