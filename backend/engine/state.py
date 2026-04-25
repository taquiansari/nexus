"""
NEXUS State — LangGraph state definition for the execution engine.
"""
from __future__ import annotations
from typing import TypedDict, Optional, Any
import operator
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """The full state that flows through the LangGraph execution graph."""

    # ── Core ──
    task: str
    execution_id: str

    # ── Plan ──
    plan: Optional[dict]
    current_step_index: int
    total_steps: int

    # ── Execution ──
    step_results: list[dict]
    status: str      # planning | executing | evaluating | recovery | hitl_paused | completed | aborted

    # ── Recovery ──
    error_context: Optional[str]
    retry_count: int

    # ── HITL ──
    hitl_request: Optional[dict]
    hitl_response: Optional[str]
    waiting_for_hitl: bool

    # ── Files ──
    uploaded_files: list[str]

    # ── Events (accumulated for WebSocket broadcast) ──
    events: list[dict]
