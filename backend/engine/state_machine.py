"""
NEXUS State Machine — The core execution engine built on LangGraph.

This is a cyclic state graph that orchestrates the full lifecycle:
  PLAN → EXECUTE → EVALUATE → (NEXT | RECOVER | HITL | COMPLETE)
"""
from __future__ import annotations
import asyncio
import datetime
import json
import logging
import pandas as pd
from typing import Any, Optional

from agents.orchestrator import create_plan, create_recovery_step
from agents.critic import evaluate_step
from agents.memory import ExecutionMemory
from engine.hitl import hitl_manager
from config import MAX_RETRIES

logger = logging.getLogger(__name__)

# ── Worker Registry ──
from workers.data_processor import DataProcessor
from workers.chart_generator import ChartGenerator
from workers.report_builder import ReportBuilder
from workers.api_handler import APIHandler
from workers.text_transformer import TextTransformer
from workers.web_researcher import WebResearcher

WORKERS = {
    "DataProcessor": DataProcessor(),
    "ChartGenerator": ChartGenerator(),
    "ReportBuilder": ReportBuilder(),
    "APIHandler": APIHandler(),
    "TextTransformer": TextTransformer(),
    "WebResearcher": WebResearcher(),
}


def _make_event(event_type: str, message: str, agent: str = "",
                step_id: int = None, data: Any = None, dag_state: dict = None) -> dict:
    """Create a standardized event dict."""
    return {
        "event_type": event_type,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "agent": agent,
        "step_id": step_id,
        "message": message,
        "data": data,
        "dag_state": dag_state,
    }


def _build_dag_state(plan: dict, current_step: int, step_results: list) -> dict:
    """Build the DAG visualization state."""
    if not plan or "steps" not in plan:
        return {}

    nodes = {}
    for step in plan["steps"]:
        sid = step["step_id"]
        # Determine node status
        result = next((r for r in step_results if r.get("step_id") == sid), None)
        if result:
            status = "passed" if result.get("success") else "failed"
        elif sid == current_step:
            status = "running"
        elif sid < current_step:
            status = "passed"
        else:
            status = "pending"

        nodes[str(sid)] = {
            "id": str(sid),
            "label": step.get("action", f"Step {sid}"),
            "worker": step.get("worker", ""),
            "status": status,
            "instruction": step.get("instruction", "")[:100],
        }

    edges = []
    for step in plan["steps"]:
        for dep in step.get("depends_on", []):
            edges.append({"source": str(dep), "target": str(step["step_id"])})
        # Also add sequential edges
        if step["step_id"] > 1 and not step.get("depends_on"):
            edges.append({"source": str(step["step_id"] - 1), "target": str(step["step_id"])})

    return {"nodes": nodes, "edges": edges}


class ExecutionEngine:
    """
    Runs the full execution lifecycle for a single task.
    Emits events that get pushed to clients via WebSocket.
    """

    def __init__(self, execution_id: str, task: str, uploaded_files: list[str] = None):
        self.execution_id = execution_id
        self.task = task
        self.uploaded_files = uploaded_files or []
        self.memory = ExecutionMemory(task)
        self.events: list[dict] = []
        self.plan: dict = {}
        self.step_results: list[dict] = []
        self.status = "planning"
        self._event_callback = None

    def on_event(self, callback):
        """Register callback for real-time event streaming."""
        self._event_callback = callback

    async def _emit(self, event: dict):
        """Emit an event to the callback and store it."""
        self.events.append(event)
        if self._event_callback:
            try:
                await self._event_callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    async def run(self) -> dict:
        """Execute the full lifecycle. Returns final state."""
        try:
            # ── PHASE 1: PLANNING ──
            self.status = "planning"
            await self._emit(_make_event(
                "log", "🧠 Orchestrator: Analyzing task and creating execution plan...",
                agent="orchestrator"
            ))

            file_context = ""
            if self.uploaded_files:
                file_context = f"Uploaded files: {', '.join(self.uploaded_files)}"
                # Try to read CSV info for planning
                for fpath in self.uploaded_files:
                    if fpath.endswith(".csv"):
                        try:
                            df = pd.read_csv(fpath, nrows=5)
                            file_context += f"\nCSV preview ({fpath}):\n"
                            file_context += f"Columns: {list(df.columns)}\n"
                            file_context += f"Shape: {df.shape}\n"
                            file_context += df.head().to_string()
                            self.memory.set_file_info({
                                "path": fpath,
                                "columns": list(df.columns),
                                "shape": list(df.shape),
                            })
                        except Exception:
                            pass

            self.plan = await create_plan(self.task, file_context)
            steps = self.plan.get("steps", [])
            total_steps = len(steps)

            dag_state = _build_dag_state(self.plan, 0, [])
            await self._emit(_make_event(
                "plan_created",
                f"📋 Plan created with {total_steps} steps",
                agent="orchestrator",
                data=self.plan,
                dag_state=dag_state,
            ))

            for step in steps:
                await self._emit(_make_event(
                    "log",
                    f"   Step {step['step_id']}: [{step['worker']}] {step['instruction'][:80]}...",
                    agent="orchestrator",
                    step_id=step["step_id"],
                ))

            # ── PHASE 2: EXECUTE EACH STEP ──
            for step_index, step in enumerate(steps):
                step_id = step["step_id"]
                worker_name = step.get("worker", "TextTransformer")
                instruction = step.get("instruction", "")
                risk_level = step.get("risk_level", "low")

                self.status = "executing"
                dag_state = _build_dag_state(self.plan, step_id, self.step_results)

                await self._emit(_make_event(
                    "step_start",
                    f"⚡ Worker [{worker_name}]: Executing Step {step_id}...",
                    agent=worker_name,
                    step_id=step_id,
                    dag_state=dag_state,
                ))

                # Build context for this step
                worker_context = {
                    "accumulated_context": self.memory.get_context_for_planning(),
                }

                # Pass data from dependencies
                depends_on = step.get("depends_on", [])
                if depends_on:
                    for dep_id in depends_on:
                        dep_result = next((r for r in self.step_results if r.get("step_id") == dep_id), None)
                        if dep_result and dep_result.get("data") is not None:
                            worker_context["previous_data"] = dep_result["data"]
                            # For charts, also pass chart data separately
                            if dep_result.get("artifacts"):
                                for art in dep_result["artifacts"]:
                                    if art.get("type", "").startswith("image/"):
                                        worker_context["chart_data"] = art.get("base64")
                elif step_index > 0:
                    # Default: pass previous step's data
                    prev = self.step_results[-1] if self.step_results else None
                    if prev and prev.get("data") is not None:
                        worker_context["previous_data"] = prev["data"]
                        if prev.get("artifacts"):
                            for art in prev["artifacts"]:
                                if art.get("type", "").startswith("image/"):
                                    worker_context["chart_data"] = art.get("base64")

                # Execute worker
                worker = WORKERS.get(worker_name)
                if not worker:
                    await self._emit(_make_event(
                        "step_fail",
                        f"❌ Unknown worker: {worker_name}",
                        agent="engine",
                        step_id=step_id,
                    ))
                    self.step_results.append({
                        "step_id": step_id,
                        "success": False,
                        "error": f"Unknown worker: {worker_name}",
                    })
                    continue

                result = await worker.execute(instruction, worker_context, self.uploaded_files)

                # ── PHASE 3: EVALUATE ──
                self.status = "evaluating"

                if result.success:
                    # Run critic evaluation
                    verdict = await evaluate_step(
                        step, result.output,
                        risk_level=risk_level,
                        accumulated_context=self.memory.get_context_for_planning(),
                    )

                    # Check if HITL is needed
                    if verdict.get("requires_hitl", False):
                        self.status = "hitl_paused"
                        hitl_question = verdict.get("hitl_question", "Please review this step's output.")
                        hitl_options = verdict.get("hitl_options", ["Approve and continue", "Retry step", "Abort execution"])

                        await self._emit(_make_event(
                            "hitl_request",
                            f"⚠️ HITL: {hitl_question}",
                            agent="critic",
                            step_id=step_id,
                            data={
                                "question": hitl_question,
                                "options": hitl_options,
                                "context": verdict.get("reasoning", ""),
                                "step_output": result.output[:1000],
                            },
                        ))

                        # Wait for human response
                        hitl_manager.create_pause(self.execution_id)
                        human_response = await hitl_manager.wait_for_response(self.execution_id, timeout=300)

                        if human_response is None or human_response.lower() in ["abort execution", "abort"]:
                            self.status = "aborted"
                            await self._emit(_make_event(
                                "execution_aborted",
                                "🛑 Execution aborted by user or timeout.",
                                agent="user",
                            ))
                            return self._final_state()

                        await self._emit(_make_event(
                            "hitl_response",
                            f"👤 User selected: {human_response}",
                            agent="user",
                            step_id=step_id,
                        ))

                        if "retry" in human_response.lower():
                            # Retry this step
                            self.memory.record_error(step_id, "User requested retry")
                            # Re-run current step (decrement index to re-process)
                            continue

                    # Step passed
                    self.memory.record_output(step_id, result.output)
                    step_record = {
                        "step_id": step_id,
                        "success": True,
                        "output": result.output,
                        "data": result.data,
                        "artifacts": result.artifacts,
                    }
                    self.step_results.append(step_record)

                    dag_state = _build_dag_state(self.plan, step_id + 1, self.step_results)
                    await self._emit(_make_event(
                        "step_complete",
                        f"✅ Step {step_id} PASSED — {result.output[:150]}",
                        agent=worker_name,
                        step_id=step_id,
                        data={"artifacts": result.artifacts},
                        dag_state=dag_state,
                    ))

                else:
                    # Step failed — attempt recovery
                    self.status = "recovery"
                    self.memory.record_error(step_id, result.error or "Unknown error")

                    await self._emit(_make_event(
                        "step_fail",
                        f"❌ Step {step_id} FAILED — {result.error or result.output}",
                        agent=worker_name,
                        step_id=step_id,
                    ))

                    # Recovery loop
                    recovered = False
                    for retry in range(MAX_RETRIES):
                        await self._emit(_make_event(
                            "recovery_start",
                            f"🔄 Recovery attempt {retry + 1}/{MAX_RETRIES} for Step {step_id}...",
                            agent="orchestrator",
                            step_id=step_id,
                        ))

                        # Ask orchestrator for a recovery step
                        recovery_context = self.memory.get_context_for_recovery(step_id)
                        new_step = await create_recovery_step(step, recovery_context)

                        new_instruction = new_step.get("instruction", instruction)
                        new_worker_name = new_step.get("worker", worker_name)
                        new_worker = WORKERS.get(new_worker_name, worker)

                        await self._emit(_make_event(
                            "log",
                            f"   New approach: [{new_worker_name}] {new_instruction[:80]}...",
                            agent="orchestrator",
                            step_id=step_id,
                        ))

                        retry_result = await new_worker.execute(
                            new_instruction, worker_context, self.uploaded_files
                        )

                        if retry_result.success:
                            self.memory.record_output(step_id, retry_result.output)
                            step_record = {
                                "step_id": step_id,
                                "success": True,
                                "output": retry_result.output,
                                "data": retry_result.data,
                                "artifacts": retry_result.artifacts,
                                "recovered": True,
                            }
                            self.step_results.append(step_record)

                            dag_state = _build_dag_state(self.plan, step_id + 1, self.step_results)
                            await self._emit(_make_event(
                                "recovery_complete",
                                f"✅ Step {step_id} RECOVERED — {retry_result.output[:150]}",
                                agent=new_worker_name,
                                step_id=step_id,
                                data={"artifacts": retry_result.artifacts},
                                dag_state=dag_state,
                            ))
                            recovered = True
                            break
                        else:
                            self.memory.record_error(step_id, retry_result.error or "Retry failed")
                            await self._emit(_make_event(
                                "log",
                                f"   ❌ Recovery attempt {retry + 1} failed: {retry_result.error[:100]}",
                                agent="orchestrator",
                                step_id=step_id,
                            ))

                    if not recovered:
                        # Max retries exhausted — record failure and continue
                        self.step_results.append({
                            "step_id": step_id,
                            "success": False,
                            "output": result.output,
                            "error": result.error,
                        })
                        dag_state = _build_dag_state(self.plan, step_id + 1, self.step_results)
                        await self._emit(_make_event(
                            "log",
                            f"⚠️ Step {step_id} could not be recovered after {MAX_RETRIES} attempts. Continuing...",
                            agent="engine",
                            step_id=step_id,
                            dag_state=dag_state,
                        ))

            # ── PHASE 4: COMPLETE ──
            self.status = "completed"
            total_passed = sum(1 for r in self.step_results if r.get("success"))
            total_failed = sum(1 for r in self.step_results if not r.get("success"))
            recovered = sum(1 for r in self.step_results if r.get("recovered"))

            # Collect all artifacts
            all_artifacts = []
            for r in self.step_results:
                if r.get("artifacts"):
                    all_artifacts.extend(r["artifacts"])

            dag_state = _build_dag_state(self.plan, total_steps + 1, self.step_results)
            await self._emit(_make_event(
                "execution_complete",
                (
                    f"🎉 Execution complete! "
                    f"{total_passed}/{total_steps} steps passed, "
                    f"{total_failed} failed, {recovered} recovered."
                ),
                agent="engine",
                data={"artifacts": all_artifacts},
                dag_state=dag_state,
            ))

            return self._final_state()

        except Exception as e:
            self.status = "aborted"
            logger.error(f"Execution engine error: {e}", exc_info=True)
            await self._emit(_make_event(
                "execution_aborted",
                f"💥 Execution failed with error: {str(e)}",
                agent="engine",
            ))
            return self._final_state()

    def _final_state(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "task": self.task,
            "status": self.status,
            "plan": self.plan,
            "step_results": self.step_results,
            "events": self.events,
        }
