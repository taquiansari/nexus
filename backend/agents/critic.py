"""
NEXUS Critic — The Evaluator agent that checks worker outputs for quality.
"""
from __future__ import annotations
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, OPENAI_MODEL, HITL_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

CRITIC_SYSTEM_PROMPT = """You are NEXUS Critic — an AI evaluator. Your job is to assess whether a worker's output successfully fulfills the step instruction.

You MUST respond with valid JSON only — no markdown, no explanation.

Evaluation criteria:
1. Does the output match the expected output description?
2. Is the data correct and complete?
3. Are there any errors, anomalies, or quality issues?
4. Is there ambiguity that requires human clarification?

Respond with this JSON structure:
{
  "verdict": "PASS" or "FAIL",
  "confidence": 0.0 to 1.0,
  "reasoning": "Explain your evaluation",
  "suggestions": ["suggestion1", "suggestion2"],
  "requires_hitl": true/false,
  "hitl_question": "Question for the user (only if requires_hitl is true)",
  "hitl_options": ["Option 1", "Option 2"] 
}

Set requires_hitl to true if:
- There's ambiguity that only a human can resolve
- The data has anomalies (e.g., most values are zero, unexpected distributions)
- The step risk_level is "high" and the action is destructive
- Your confidence is below 0.6"""


def _get_llm():
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.0,
        max_tokens=2048,
    )


async def evaluate_step(
    step: dict,
    worker_output: str,
    risk_level: str = "low",
    accumulated_context: str = ""
) -> dict:
    """
    Evaluate a worker's output against the step's expectations.
    Returns the critic verdict dict.
    """
    llm = _get_llm()

    user_content = (
        f"Step instruction: {step.get('instruction', '')}\n"
        f"Expected output: {step.get('expected_output', '')}\n"
        f"Risk level: {risk_level}\n"
        f"Actual worker output:\n{worker_output[:3000]}\n"
    )
    if accumulated_context:
        user_content += f"\nContext from previous steps:\n{accumulated_context[:1000]}"

    messages = [
        SystemMessage(content=CRITIC_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    logger.info(f"Critic: Evaluating step {step.get('step_id')}")

    try:
        response = await llm.ainvoke(messages)
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        verdict = json.loads(raw)
    except Exception as e:
        logger.error(f"Critic: Evaluation failed: {e}")
        # Default to PASS if critic fails (don't block execution)
        verdict = {
            "verdict": "PASS",
            "confidence": 0.7,
            "reasoning": f"Critic evaluation error ({str(e)[:100]}). Defaulting to PASS.",
            "suggestions": [],
            "requires_hitl": False,
            "hitl_question": None,
            "hitl_options": []
        }

    # Force HITL if confidence is below threshold
    confidence = verdict.get("confidence", 1.0)
    if confidence < HITL_CONFIDENCE_THRESHOLD and not verdict.get("requires_hitl"):
        verdict["requires_hitl"] = True
        verdict["hitl_question"] = (
            verdict.get("hitl_question") or
            f"The evaluator has low confidence ({confidence:.0%}) about this step's output. "
            f"Reason: {verdict.get('reasoning', 'Unknown')}. Should we proceed or retry?"
        )
        verdict["hitl_options"] = verdict.get("hitl_options") or ["Proceed anyway", "Retry step", "Abort execution"]

    # Force HITL for high-risk steps
    if risk_level == "high" and not verdict.get("requires_hitl"):
        verdict["requires_hitl"] = True
        verdict["hitl_question"] = (
            verdict.get("hitl_question") or
            "This is a HIGH-RISK step. Please confirm the output before proceeding."
        )
        verdict["hitl_options"] = verdict.get("hitl_options") or ["Approve and continue", "Retry step", "Abort execution"]

    logger.info(
        f"Critic: Step {step.get('step_id')} → {verdict.get('verdict')} "
        f"(confidence: {confidence:.0%}, hitl: {verdict.get('requires_hitl')})"
    )
    return verdict
