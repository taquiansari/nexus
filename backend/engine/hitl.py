"""
NEXUS HITL Manager — Human-in-the-Loop pause/resume mechanism.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HITLManager:
    """
    Manages HITL pause/resume for execution runs.
    Uses asyncio Events to block the graph until a human responds.
    """

    def __init__(self):
        self._events: dict[str, asyncio.Event] = {}
        self._responses: dict[str, str] = {}

    def create_pause(self, execution_id: str):
        """Create a pause point for an execution."""
        self._events[execution_id] = asyncio.Event()
        logger.info(f"HITL: Pause created for execution {execution_id}")

    async def wait_for_response(self, execution_id: str, timeout: float = 300.0) -> Optional[str]:
        """
        Block until a human provides a response, or timeout.
        Returns the selected option string, or None on timeout.
        """
        event = self._events.get(execution_id)
        if not event:
            logger.error(f"HITL: No pause exists for {execution_id}")
            return None

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            response = self._responses.pop(execution_id, None)
            self._events.pop(execution_id, None)
            logger.info(f"HITL: Response received for {execution_id}: {response}")
            return response
        except asyncio.TimeoutError:
            logger.warning(f"HITL: Timeout waiting for response on {execution_id}")
            self._events.pop(execution_id, None)
            return None

    def submit_response(self, execution_id: str, response: str):
        """Submit a human response to resume execution."""
        self._responses[execution_id] = response
        event = self._events.get(execution_id)
        if event:
            event.set()
            logger.info(f"HITL: Response submitted for {execution_id}: {response}")
        else:
            logger.warning(f"HITL: No waiting event for {execution_id}")

    def is_waiting(self, execution_id: str) -> bool:
        """Check if an execution is waiting for HITL."""
        event = self._events.get(execution_id)
        return event is not None and not event.is_set()


# Singleton instance
hitl_manager = HITLManager()
