"""
NEXUS Base Worker — Abstract interface for all specialist workers.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional
import asyncio
import logging
from config import WORKER_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class WorkerResult:
    """Standardized result from any worker."""

    def __init__(
        self,
        success: bool,
        output: str = "",
        data: Any = None,
        artifacts: list[dict] = None,
        error: str = None,
    ):
        self.success = success
        self.output = output
        self.data = data
        self.artifacts = artifacts or []
        self.error = error

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "data": self.data,
            "artifacts": self.artifacts,
            "error": self.error,
        }


class BaseWorker(ABC):
    """Abstract base class for all workers."""

    name: str = "BaseWorker"

    @abstractmethod
    async def _execute(
        self,
        instruction: str,
        context: dict,
        uploaded_files: list[str],
    ) -> WorkerResult:
        """Execute the step. Subclasses implement this."""
        ...

    async def execute(
        self,
        instruction: str,
        context: dict = None,
        uploaded_files: list[str] = None,
    ) -> WorkerResult:
        """Execute with timeout protection."""
        context = context or {}
        uploaded_files = uploaded_files or []

        logger.info(f"{self.name}: Executing — {instruction[:100]}...")

        try:
            result = await asyncio.wait_for(
                self._execute(instruction, context, uploaded_files),
                timeout=WORKER_TIMEOUT_SECONDS,
            )
            if result.success:
                logger.info(f"{self.name}: Success — {result.output[:100]}")
            else:
                logger.warning(f"{self.name}: Failed — {result.error}")
            return result

        except asyncio.TimeoutError:
            error = f"{self.name} timed out after {WORKER_TIMEOUT_SECONDS}s"
            logger.error(error)
            return WorkerResult(success=False, error=error)

        except Exception as e:
            error = f"{self.name} unexpected error: {str(e)}"
            logger.error(error, exc_info=True)
            return WorkerResult(success=False, error=error)
