"""Content generator.

Uses Claude CLI to generate posts, validates them against brand voice rules,
and retries up to 3 times if validation fails.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

import structlog

from src.content.brand_voice import SYSTEM_PROMPT, validate_post
from src.content.prompts import get_post_prompt
from src.utils.claude_cli import generate

logger = structlog.get_logger(__name__)

_MAX_GENERATION_ATTEMPTS = 3


@dataclass
class GeneratedPost:
    title: str
    text: str
    cta: str
    post_type: str
    attempt: int  # which attempt produced this


async def generate_post(
    post_type: str,
    recent_posts: Optional[list[str]] = None,
    news_context: Optional[str] = None,
    extra_context: Optional[str] = None,
    claude_cli_path: str = "claude",
    data_dir: Optional[str] = None,
) -> GeneratedPost:
    """Generate a channel post via Claude CLI.

    Validates the post against brand voice rules. Retries up to
    _MAX_GENERATION_ATTEMPTS times if validation fails.

    Args:
        post_type: One of the POST_TYPE_* constants from prompts.py.
        recent_posts: List of recent post texts to avoid repetition.
        news_context: Optional news event to reference.
        extra_context: Any extra topic direction.
        claude_cli_path: Path to claude CLI binary.

    Returns:
        GeneratedPost dataclass.

    Raises:
        RuntimeError: If valid post cannot be generated after max attempts.
    """
    recent_summary = _summarise_recent_posts(recent_posts)

    # Inject fresh context from learner if available
    learner_context = ""
    if data_dir:
        try:
            from src.content.learner import get_context_prompt_addon
            addon = get_context_prompt_addon(data_dir)
            if addon:
                learner_context = addon
        except Exception:
            pass

    last_issues: list[str] = []

    for attempt in range(1, _MAX_GENERATION_ATTEMPTS + 1):
        logger.info(
            "content.generator.attempt",
            post_type=post_type,
            attempt=attempt,
        )

        retry_hint = ""
        if last_issues:
            retry_hint = (
                f"\n\nПРЕДЫДУЩАЯ ПОПЫТКА НЕ ПРОШЛА ВАЛИДАЦИЮ. Исправь:\n"
                + "\n".join(f"- {issue}" for issue in last_issues)
            )

        user_prompt = get_post_prompt(
            post_type=post_type,
            recent_posts_summary=recent_summary,
            news_context=news_context,
            extra_context=(extra_context or "") + retry_hint + ("\n\n" + learner_context if learner_context else ""),
        )

        raw = await generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            claude_cli_path=claude_cli_path,
            model="sonnet",
        )

        parsed = _parse_response(raw)
        if parsed is None:
            logger.warning(
                "content.generator.parse_failed",
                attempt=attempt,
                raw_preview=raw[:300],
            )
            last_issues = ["Ответ не удалось разобрать как JSON"]
            continue

        validation = validate_post(parsed["text"])
        logger.debug(
            "content.generator.validation",
            attempt=attempt,
            result=validation.summary(),
        )

        if validation.valid:
            return GeneratedPost(
                title=parsed.get("title", ""),
                text=parsed["text"],
                cta=parsed.get("cta", ""),
                post_type=post_type,
                attempt=attempt,
            )

        last_issues = validation.issues
        logger.warning(
            "content.generator.validation_failed",
            attempt=attempt,
            issues=validation.issues,
        )

    raise RuntimeError(
        f"Не удалось сгенерировать валидный пост типа '{post_type}' "
        f"за {_MAX_GENERATION_ATTEMPTS} попыток. "
        f"Последние ошибки: {last_issues}"
    )


def _parse_response(raw: str) -> Optional[dict]:
    """Extract JSON from Claude's response.

    Handles cases where Claude wraps JSON in markdown code blocks.
    """
    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first JSON object in the string
    match = re.search(r"\{[^{}]*\"text\"[^{}]*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _summarise_recent_posts(recent_posts: Optional[list[str]]) -> Optional[str]:
    """Create a short summary of recent posts for the prompt."""
    if not recent_posts:
        return None

    lines = []
    for i, post in enumerate(recent_posts[-5:], 1):  # last 5 only
        preview = post[:150].replace("\n", " ")
        lines.append(f"{i}. {preview}...")

    return "\n".join(lines)
