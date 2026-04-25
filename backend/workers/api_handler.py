"""
NEXUS API Handler Worker — Makes HTTP requests to external APIs.
"""
from __future__ import annotations
import json
import logging
import httpx
from workers.base_worker import BaseWorker, WorkerResult
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

API_PLAN_PROMPT = """You are an API integration expert. Given an instruction, generate a JSON object describing the HTTP request to make.

RULES:
1. Output ONLY valid JSON, no markdown.
2. Structure:
{
  "method": "GET" or "POST",
  "url": "the full URL",
  "headers": {"key": "value"},
  "params": {"key": "value"},
  "body": {"key": "value"} or null,
  "description": "what this request does"
}
3. Use publicly accessible APIs when possible.
4. For safety, avoid any destructive operations."""


class APIHandler(BaseWorker):
    name = "APIHandler"

    async def _execute(
        self,
        instruction: str,
        context: dict,
        uploaded_files: list[str],
    ) -> WorkerResult:
        # Use LLM to plan the API request
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.0,
            max_tokens=1024,
        )

        messages = [
            {"role": "system", "content": API_PLAN_PROMPT},
            {"role": "user", "content": f"Instruction: {instruction}\n\nContext: {json.dumps(context.get('accumulated_context', ''))[:500]}"},
        ]

        response = await llm.ainvoke(messages)
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        try:
            request_plan = json.loads(raw)
        except json.JSONDecodeError:
            return WorkerResult(
                success=False,
                error=f"Failed to parse API request plan: {raw[:300]}"
            )

        # Execute the HTTP request with retry
        method = request_plan.get("method", "GET").upper()
        url = request_plan.get("url", "")
        headers = request_plan.get("headers", {})
        params = request_plan.get("params", {})
        body = request_plan.get("body")

        if not url:
            return WorkerResult(success=False, error="No URL specified in API plan")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    if method == "GET":
                        resp = await client.get(url, headers=headers, params=params)
                    elif method == "POST":
                        resp = await client.post(url, headers=headers, params=params, json=body)
                    else:
                        return WorkerResult(success=False, error=f"Unsupported method: {method}")

                    if resp.status_code == 429:
                        # Rate limited — backoff and retry
                        import asyncio
                        wait = 2 ** attempt
                        logger.warning(f"APIHandler: Rate limited, waiting {wait}s...")
                        await asyncio.sleep(wait)
                        continue

                    if resp.status_code >= 400:
                        return WorkerResult(
                            success=False,
                            error=f"HTTP {resp.status_code}: {resp.text[:500]}"
                        )

                    # Parse response
                    try:
                        data = resp.json()
                        output = json.dumps(data, indent=2)[:3000]
                    except Exception:
                        data = resp.text
                        output = data[:3000]

                    return WorkerResult(
                        success=True,
                        output=f"API request successful ({method} {url})\nResponse:\n{output}",
                        data=data,
                    )

            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                return WorkerResult(success=False, error=f"API request timed out after {max_retries} retries")
            except Exception as e:
                return WorkerResult(success=False, error=f"API request failed: {str(e)}")

        return WorkerResult(success=False, error="Max retries exceeded")
