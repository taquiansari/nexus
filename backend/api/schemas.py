"""
NEXUS API Schemas — Pydantic models for request/response validation.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum
import datetime


# ── Enums ──

class ExecutionStatus(str, Enum):
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    RECOVERY = "recovery"
    HITL_PAUSED = "hitl_paused"
    COMPLETED = "completed"
    ABORTED = "aborted"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EventType(str, Enum):
    PLAN_CREATED = "plan_created"
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    STEP_FAIL = "step_fail"
    HITL_REQUEST = "hitl_request"
    HITL_RESPONSE = "hitl_response"
    RECOVERY_START = "recovery_start"
    RECOVERY_COMPLETE = "recovery_complete"
    EXECUTION_COMPLETE = "execution_complete"
    EXECUTION_ABORTED = "execution_aborted"
    LOG = "log"


# ── Step Plan ──

class StepPlan(BaseModel):
    step_id: int
    action: str
    worker: str
    instruction: str
    expected_output: str
    risk_level: RiskLevel = RiskLevel.LOW
    depends_on: list[int] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    task_id: str
    original_intent: str
    steps: list[StepPlan]


# ── Worker Results ──

class WorkerResult(BaseModel):
    success: bool
    output: Optional[str] = None
    data: Optional[Any] = None
    artifacts: list[dict] = Field(default_factory=list)  # [{name, type, base64}]
    error: Optional[str] = None


# ── Critic Verdict ──

class CriticVerdict(BaseModel):
    step_id: int
    verdict: str  # "PASS" or "FAIL"
    confidence: float = 1.0
    reasoning: str = ""
    suggestions: list[str] = Field(default_factory=list)
    requires_hitl: bool = False
    hitl_question: Optional[str] = None
    hitl_options: list[str] = Field(default_factory=list)


# ── HITL ──

class HITLRequest(BaseModel):
    execution_id: str
    step_id: int
    question: str
    context: str
    options: list[str]


class HITLResponse(BaseModel):
    execution_id: str
    step_id: int
    selected_option: str


# ── Execution Events (WebSocket) ──

class ExecutionEvent(BaseModel):
    event_type: EventType
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    agent: str = ""
    step_id: Optional[int] = None
    message: str = ""
    data: Optional[Any] = None
    dag_state: Optional[dict] = None


# ── API Requests/Responses ──

class ExecuteRequest(BaseModel):
    task: str
    file_name: Optional[str] = None


class ExecuteResponse(BaseModel):
    execution_id: str
    status: str
    message: str


class ExecutionSummary(BaseModel):
    execution_id: str
    task: str
    status: str
    created_at: str
    duration_seconds: Optional[float] = None
    total_steps: int = 0


class ExecutionDetail(BaseModel):
    execution_id: str
    task: str
    status: str
    created_at: str
    duration_seconds: Optional[float] = None
    total_steps: int = 0
    events: list[dict] = Field(default_factory=list)
    plan: Optional[dict] = None
