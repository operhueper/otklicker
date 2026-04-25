"""Response generator for chat monitoring.

Generates natural, humanized responses as Артём for detected opportunities.
Uses Claude CLI with conversation context.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

import structlog

from src.content.brand_voice import SYSTEM_PROMPT, validate_chat_response
from src.content.prompts import CHAT_RESPONSE_SYSTEM_PROMPT, get_chat_response_prompt
from src.utils.claude_cli import generate

logger = structlog.get_logger(__name__)

_MAX_CONTEXT_MESSAGES = 15


@dataclass
class ResponseResult:
    text: str
    confidence: float
    reasoning: str
    skip: bool
    raw_response: str = ""


async def generate_chat_response(
    conversation_context: list[dict],
    target_message: str,
    opportunity_category: str = "general",
    claude_cli_path: str = "claude",
    artem_original_message: str = "",
) -> ResponseResult:
    """Generate a natural chat response for a detected opportunity.

    Args:
        conversation_context: List of recent messages as dicts with
            'author' and 'text' keys. Most recent last.
        target_message: The specific message to respond to.
        opportunity_category: From detector (direct_mention, base_building, etc.).
        claude_cli_path: Path to claude CLI binary.
        artem_original_message: Артём's original message that was replied to
            (only for reply_to_artem category).

    Returns:
        ResponseResult with the generated text and metadata.
    """
    # Build context string from last N messages
    context_str = _format_context(conversation_context)

    # Inject learner context (trending topics, pains, mood from chats)
    learner_addon = ""
    try:
        from src.content.learner import get_context_prompt_addon
        addon = get_context_prompt_addon("data")
        if addon:
            learner_addon = f"\n\n{addon}"
    except Exception:
        pass

    user_prompt = get_chat_response_prompt(
        conversation_context=context_str + learner_addon,
        target_message=target_message,
        opportunity_category=opportunity_category,
        artem_original_message=artem_original_message,
    )

    try:
        raw = await generate(
            system_prompt=CHAT_RESPONSE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=512,
            claude_cli_path=claude_cli_path,
            model="sonnet",
        )

        result = _parse_response(raw)
        if result is None:
            logger.warning(
                "responder.parse_failed",
                raw_preview=raw[:200],
            )
            return ResponseResult(
                text="",
                confidence=0.0,
                reasoning="Failed to parse response",
                skip=True,
                raw_response=raw,
            )

        # Anti-AI validation: check if response sounds bot-like
        if result.text and not result.skip:
            validation = validate_chat_response(result.text)
            if validation.ai_score >= 3:
                logger.warning(
                    "responder.ai_detected",
                    ai_score=validation.ai_score,
                    issues=validation.issues,
                    text_preview=result.text[:100],
                )
                # Penalize confidence so it won't auto-send
                result.confidence = min(result.confidence, 0.4)
                result.reasoning = f"AI-detected (score {validation.ai_score}): {'; '.join(validation.issues[:3])}"
            elif validation.ai_score >= 1:
                logger.info(
                    "responder.ai_minor_tells",
                    ai_score=validation.ai_score,
                    issues=validation.issues,
                )

        logger.info(
            "responder.generated",
            confidence=result.confidence,
            skip=result.skip,
            category=opportunity_category,
        )

        return result

    except Exception as exc:
        logger.error(
            "responder.generation_failed",
            error=str(exc),
        )
        return ResponseResult(
            text="",
            confidence=0.0,
            reasoning=f"Generation error: {exc}",
            skip=True,
        )


def _format_context(messages: list[dict]) -> str:
    """Format recent messages into readable context string."""
    # Take last N messages
    recent = messages[-_MAX_CONTEXT_MESSAGES:]

    lines = []
    for msg in recent:
        author = msg.get("author", "Участник")
        text = msg.get("text", "").strip()
        if text:
            lines.append(f"{author}: {text}")

    return "\n".join(lines) if lines else "(нет контекста)"


def _parse_response(raw: str) -> Optional[ResponseResult]:
    """Parse Claude's JSON response into ResponseResult."""
    # Try direct parse
    data = None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        pass

    if data is None:
        # Try extracting from markdown
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

    if data is None:
        # Try first JSON object
        match = re.search(r"\{[^{}]*\"text\"[^{}]*\}", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

    if data is None:
        return None

    return ResponseResult(
        text=data.get("text", ""),
        confidence=float(data.get("confidence", 0.5)),
        reasoning=data.get("reasoning", ""),
        skip=bool(data.get("skip", False)),
        raw_response=raw,
    )
