"""
NEXUS Memory Layer — Accumulates context across execution steps.
"""
from __future__ import annotations
from typing import Any, Optional


class ExecutionMemory:
    """
    Short-term memory for a single execution run.
    Tracks step outputs, errors, and context for re-planning.
    """

    def __init__(self, task: str):
        self.task = task
        self.step_outputs: dict[int, Any] = {}
        self.step_errors: dict[int, list[str]] = {}
        self.accumulated_context: list[str] = []
        self.uploaded_file_info: Optional[dict] = None

    def record_output(self, step_id: int, output: Any):
        """Record successful step output."""
        self.step_outputs[step_id] = output
        summary = str(output)[:500] if output else "No output"
        self.accumulated_context.append(
            f"Step {step_id} completed successfully. Output summary: {summary}"
        )

    def record_error(self, step_id: int, error: str):
        """Record step error for recovery context."""
        if step_id not in self.step_errors:
            self.step_errors[step_id] = []
        self.step_errors[step_id].append(error)
        self.accumulated_context.append(
            f"Step {step_id} failed with error: {error}"
        )

    def set_file_info(self, file_info: dict):
        """Store uploaded file metadata."""
        self.uploaded_file_info = file_info

    def get_context_for_planning(self) -> str:
        """Get accumulated context for the Orchestrator."""
        parts = [f"Original task: {self.task}"]
        if self.uploaded_file_info:
            parts.append(f"Uploaded file: {self.uploaded_file_info}")
        if self.accumulated_context:
            parts.append("Execution history:")
            parts.extend(f"  - {c}" for c in self.accumulated_context)
        return "\n".join(parts)

    def get_context_for_recovery(self, step_id: int) -> str:
        """Get error context for re-planning a failed step."""
        errors = self.step_errors.get(step_id, [])
        parts = [
            f"Original task: {self.task}",
            f"Step {step_id} has failed {len(errors)} time(s).",
            f"Previous errors: {'; '.join(errors)}",
        ]
        if self.step_outputs:
            parts.append("Successfully completed steps:")
            for sid, out in self.step_outputs.items():
                parts.append(f"  Step {sid}: {str(out)[:200]}")
        return "\n".join(parts)

    def get_step_output(self, step_id: int) -> Any:
        """Retrieve a specific step's output."""
        return self.step_outputs.get(step_id)
