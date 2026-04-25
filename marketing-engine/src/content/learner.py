"""Self-learning brand voice system.

Periodically reads messages from monitored chats, analyzes trends/pain points,
and updates brand_voice_context.json which is injected into prompts.

Runs as a scheduled job in the marketing engine.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# Context file that gets updated by learning and read by generator
CONTEXT_FILE = "brand_voice_context.json"

# Default context structure
DEFAULT_CONTEXT = {
    "last_updated": "",
    "top_pains": [],
    "trending_topics": [],
    "independence_ideas": [],
    "max_messenger_intel": [],
    "useful_numbers": [],
    "slang_new": [],
    "mood": "neutral",
    "sample_messages": [],
    "avoid_topics": [],
}


async def learn_from_chats(
    client,
    chat_ids: list[int],
    data_dir: str,
    claude_cli_path: str = "claude",
    messages_per_chat: int = 50,
) -> dict:
    """Read recent messages from chats and extract insights.

    Args:
        client: Connected Telethon client.
        chat_ids: List of chat IDs to read from.
        data_dir: Path to data directory for saving context.
        claude_cli_path: Path to Claude CLI for analysis.
        messages_per_chat: How many messages to read per chat.

    Returns:
        Updated context dict.
    """
    logger.info("learner.collecting", chats=len(chat_ids))

    # Collect messages
    all_messages = []
    for chat_id in chat_ids:
        try:
            async for msg in client.iter_messages(chat_id, limit=messages_per_chat):
                if msg.text and len(msg.text) > 15:
                    sender_name = ""
                    if msg.sender:
                        sender_name = getattr(msg.sender, "first_name", "") or ""
                    all_messages.append({
                        "chat_id": chat_id,
                        "from": sender_name,
                        "text": msg.text[:400],
                        "date": msg.date.isoformat(),
                    })
        except Exception as exc:
            logger.warning("learner.chat_read_failed", chat_id=chat_id, error=str(exc))

    if not all_messages:
        logger.warning("learner.no_messages")
        return _load_context(data_dir)

    logger.info("learner.collected", total_messages=len(all_messages))

    # Analyze with Claude CLI
    context = await _analyze_messages(all_messages, claude_cli_path)

    # Save updated context
    context["last_updated"] = datetime.now(timezone.utc).isoformat()
    _save_context(data_dir, context)

    logger.info("learner.updated", pains=len(context.get("top_pains", [])))
    return context


async def _analyze_messages(messages: list[dict], claude_cli_path: str) -> dict:
    """Use Claude CLI to analyze collected messages."""
    from src.utils.claude_cli import generate

    # Prepare message dump (truncated for prompt size)
    sample = messages[:150]  # limit to avoid huge prompts
    messages_text = "\n".join(
        f"[{m['from']}]: {m['text']}" for m in sample
    )

    prompt = f"""Проанализируй сообщения из чатов/каналов продавцов WB/Ozon и верни JSON.

СООБЩЕНИЯ:
{messages_text}

ФОКУС АНАЛИЗА:
- Особое внимание на темы: уход от зависимости от маркетплейсов, своя база покупателей, свои каналы продаж, внешний трафик, прямые продажи
- Если упоминается мессенджер Макс (Max), выпиши отдельно всё что о нём говорят
- Ищи интересные мысли, цифры, кейсы которые продавец мог бы использовать в разговоре

Верни строго JSON (без обёртки):
{{
  "top_pains": ["боль1", "боль2", ...],
  "trending_topics": ["тема1", "тема2", ...],
  "independence_ideas": ["мысли/кейсы про уход от зависимости от маркетплейсов и создание своей базы"],
  "max_messenger_intel": ["всё что упоминалось про мессенджер Макс, если ничего то пустой список"],
  "useful_numbers": ["конкретные цифры/кейсы которые можно ввернуть в разговор"],
  "slang_new": ["новое слово/выражение", ...],
  "mood": "одно слово: злой/раздражённый/нейтральный/оптимистичный",
  "sample_messages": ["5 самых характерных цитат из сообщений"],
  "avoid_topics": ["темы которые сейчас раздражают людей и лучше не трогать"]
}}

Максимум 7 пунктов в каждом списке. Пиши на русском."""

    try:
        raw = await generate(
            system_prompt="Ты аналитик. Возвращаешь только JSON.",
            user_prompt=prompt,
            claude_cli_path=claude_cli_path,
            timeout=120,
            model="haiku",
        )
        return _parse_json(raw)
    except Exception as exc:
        logger.error("learner.analysis_failed", error=str(exc))
        return DEFAULT_CONTEXT.copy()


def _parse_json(raw: str) -> dict:
    """Extract JSON from Claude response."""
    import re

    # Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # From code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Find first JSON object
    match = re.search(r"\{[^{}]*\"top_pains\"[^{}]*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return DEFAULT_CONTEXT.copy()


def get_context(data_dir: str) -> dict:
    """Load current brand voice context for prompt injection."""
    return _load_context(data_dir)


def get_context_prompt_addon(data_dir: str) -> Optional[str]:
    """Get context as a string to append to generation prompts."""
    ctx = _load_context(data_dir)
    if not ctx.get("top_pains"):
        return None

    parts = []

    if ctx.get("top_pains"):
        parts.append("АКТУАЛЬНЫЕ БОЛИ СЕЛЛЕРОВ:")
        for pain in ctx["top_pains"][:5]:
            parts.append(f"- {pain}")

    if ctx.get("trending_topics"):
        parts.append("\nТРЕНДОВЫЕ ТЕМЫ:")
        for topic in ctx["trending_topics"][:5]:
            parts.append(f"- {topic}")

    if ctx.get("mood"):
        parts.append(f"\nНАСТРОЕНИЕ В ЧАТАХ: {ctx['mood']}")

    if ctx.get("sample_messages"):
        parts.append("\nПРИМЕРЫ КАК ПИШУТ ЛЮДИ:")
        for msg in ctx["sample_messages"][:3]:
            parts.append(f'"{msg}"')

    if ctx.get("independence_ideas"):
        parts.append("\nМЫСЛИ ПРО СВОБОДУ ОТ МАРКЕТПЛЕЙСОВ (из чатов):")
        for idea in ctx["independence_ideas"][:5]:
            parts.append(f"- {idea}")

    if ctx.get("useful_numbers"):
        parts.append("\nЦИФРЫ И КЕЙСЫ (можно ввернуть в разговор):")
        for num in ctx["useful_numbers"][:5]:
            parts.append(f"- {num}")

    if ctx.get("max_messenger_intel"):
        parts.append("\nЧТО ГОВОРЯТ ПРО МЕССЕНДЖЕР МАКС:")
        for info in ctx["max_messenger_intel"][:5]:
            parts.append(f"- {info}")

    if ctx.get("avoid_topics"):
        parts.append("\nНЕ ТРОГАЙ ЭТИ ТЕМЫ:")
        for topic in ctx["avoid_topics"][:3]:
            parts.append(f"- {topic}")

    return "\n".join(parts)


def _load_context(data_dir: str) -> dict:
    path = Path(data_dir) / CONTEXT_FILE
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CONTEXT.copy()


def _save_context(data_dir: str, context: dict) -> None:
    path = Path(data_dir) / CONTEXT_FILE
    with open(path, "w") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)
    logger.info("learner.context_saved", path=str(path))
