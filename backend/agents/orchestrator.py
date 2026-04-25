"""
NEXUS Orchestrator — The Planner agent that decomposes tasks into execution steps.
"""
from __future__ import annotations
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

PLANNING_SYSTEM_PROMPT = """You are NEXUS Orchestrator — an AI task planner. Your job is to decompose a complex user instruction into a sequence of concrete, executable steps.

You MUST respond with valid JSON only — no markdown, no explanation, just the JSON object.

Available workers:
- DataProcessor: Load CSVs, clean data, handle nulls, deduplicate, aggregate, compute statistics using pandas
- ChartGenerator: Create charts (bar, line, pie, scatter) from data using matplotlib  
- ReportBuilder: Compile text, tables, and charts into a PDF report
- APIHandler: Make HTTP GET/POST requests to external APIs
- TextTransformer: Summarize, extract entities, format text using LLM
- WebResearcher: Search the web and extract content from pages

Rules:
1. Each step must specify exactly ONE worker
2. Steps are executed SEQUENTIALLY in order
3. Mark risk_level as "high" for destructive actions (file deletion, external POST, email sending)
4. Mark risk_level as "medium" for operations with ambiguity (data cleaning decisions, schema inference)
5. Be specific in instructions — include column names, formats, and expected shapes when known
6. The expected_output should describe the type and shape of output expected

Respond with this JSON structure:
{
  "original_intent": "Brief summary of what the user wants",
  "steps": [
    {
      "step_id": 1,
      "action": "descriptive_action_name",
      "worker": "WorkerName",
      "instruction": "Detailed instruction for the worker",
      "expected_output": "Description of expected output",
      "risk_level": "low|medium|high",
      "depends_on": []
    }
  ]
}"""

RECOVERY_SYSTEM_PROMPT = """You are NEXUS Orchestrator in RECOVERY mode. A step in your execution plan has failed. 
You need to generate a REPLACEMENT step that achieves the same goal using a different approach.

You MUST respond with valid JSON only — a single step object.

Available workers:
- DataProcessor: Load CSVs, clean data, handle nulls, deduplicate, aggregate, compute statistics using pandas
- ChartGenerator: Create charts (bar, line, pie, scatter) from data using matplotlib
- ReportBuilder: Compile text, tables, and charts into a PDF report
- APIHandler: Make HTTP GET/POST requests to external APIs
- TextTransformer: Summarize, extract entities, format text using LLM
- WebResearcher: Search the web and extract content from pages

Respond with a single step JSON:
{
  "step_id": <same_step_id>,
  "action": "descriptive_action_name",
  "worker": "WorkerName",
  "instruction": "Modified instruction that avoids the previous error",
  "expected_output": "Description of expected output",
  "risk_level": "low|medium|high",
  "depends_on": []
}"""


def _get_llm():
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.1,
        max_tokens=4096,
    )


async def create_plan(task: str, context: str = "") -> dict:
    """
    Decompose a user task into an execution plan.
    Returns the parsed plan dict.
    """
    llm = _get_llm()

    user_content = f"User task: {task}"
    if context:
        user_content += f"\n\nAdditional context:\n{context}"

    messages = [
        SystemMessage(content=PLANNING_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    logger.info(f"Orchestrator: Creating plan for task: {task[:100]}...")
    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Orchestrator: Failed to parse plan JSON: {e}\nRaw: {raw[:500]}")
        # Fallback: create a simple single-step plan
        plan = {
            "original_intent": task,
            "steps": [
                {
                    "step_id": 1,
                    "action": "process_task",
                    "worker": "TextTransformer",
                    "instruction": task,
                    "expected_output": "Task result",
                    "risk_level": "low",
                    "depends_on": []
                }
            ]
        }

    logger.info(f"Orchestrator: Plan created with {len(plan.get('steps', []))} steps")
    return plan


async def create_recovery_step(failed_step: dict, error_context: str) -> dict:
    """
    Generate a replacement step for a failed step.
    Returns the new step dict.
    """
    llm = _get_llm()

    user_content = (
        f"Failed step:\n{json.dumps(failed_step, indent=2)}\n\n"
        f"Error context:\n{error_context}\n\n"
        f"Generate a replacement step that achieves the same goal using a different approach."
    )

    messages = [
        SystemMessage(content=RECOVERY_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    logger.info(f"Orchestrator: Creating recovery step for step {failed_step.get('step_id')}")
    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        step = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Orchestrator: Failed to parse recovery step: {e}")
        # Return modified original with simpler instruction
        step = dict(failed_step)
        step["instruction"] = (
            f"SIMPLIFIED RETRY: {failed_step['instruction']}. "
            f"Previous error: {error_context[:200]}. Try a simpler approach."
        )

    return step
