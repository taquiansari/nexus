"""
NEXUS Text Transformer Worker — LLM-powered text operations.
"""
from __future__ import annotations
import logging
from workers.base_worker import BaseWorker, WorkerResult
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)


class TextTransformer(BaseWorker):
    name = "TextTransformer"

    async def _execute(
        self,
        instruction: str,
        context: dict,
        uploaded_files: list[str],
    ) -> WorkerResult:
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.3,
            max_tokens=4096,
        )

        # Build context from previous steps
        prev_context = context.get("accumulated_context", "")
        prev_data = context.get("previous_data")

        content_parts = [f"Task: {instruction}"]
        if prev_context:
            content_parts.append(f"\nContext from previous steps:\n{prev_context[:2000]}")
        if prev_data:
            data_str = str(prev_data)[:2000]
            content_parts.append(f"\nData to work with:\n{data_str}")

        messages = [
            SystemMessage(content=(
                "You are a text processing specialist. Follow the instruction precisely. "
                "Provide clear, well-structured output. Be concise but thorough."
            )),
            HumanMessage(content="\n".join(content_parts)),
        ]

        try:
            response = await llm.ainvoke(messages)
            result = response.content.strip()

            return WorkerResult(
                success=True,
                output=result,
                data=result,
            )
        except Exception as e:
            return WorkerResult(
                success=False,
                error=f"Text transformation failed: {str(e)}",
            )
