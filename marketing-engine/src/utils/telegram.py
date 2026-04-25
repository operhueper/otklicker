"""Telegram Bot API helpers.

Thin async wrappers around the Bot API for channel posting,
admin notifications, and stats retrieval.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import aiohttp
import structlog

logger = structlog.get_logger(__name__)

_API_BASE = "https://api.telegram.org/bot{token}/{method}"


_MAX_CAPTION = 1024


async def send_to_channel(
    bot_token: str,
    channel_id: str,
    text: str,
    image_path: Optional[Path | str] = None,
) -> dict:
    """Send a message (with optional image) to the Telegram channel.

    If image is provided but text exceeds Telegram's 1024-char caption limit,
    sends photo first (no caption), then text as a reply to the photo.

    Args:
        bot_token: Telegram bot token.
        channel_id: Channel username or numeric ID (e.g. @seller_base or -100...).
        text: Message text (HTML or Markdown).
        image_path: Optional path to a local image file.

    Returns:
        Telegram API response dict (of the text message).
    """
    async with aiohttp.ClientSession() as session:
        if image_path:
            if len(text) <= _MAX_CAPTION:
                return await _send_photo(session, bot_token, channel_id, text, image_path)
            # Text too long for caption: send photo without caption, then text as reply
            photo_resp = await _send_photo(session, bot_token, channel_id, "", image_path)
            photo_msg_id = photo_resp.get("result", {}).get("message_id")
            return await _send_message(
                session, bot_token, channel_id, text, reply_to=photo_msg_id,
            )
        return await _send_message(session, bot_token, channel_id, text)


async def send_to_admin(
    bot_token: str,
    admin_id: str | int,
    text: str,
    reply_markup: Optional[dict] = None,
) -> dict:
    """Send a notification message to the admin chat.

    Args:
        bot_token: Telegram bot token.
        admin_id: Admin's chat ID or username.
        text: Message text.
        reply_markup: Optional inline keyboard / reply keyboard dict.

    Returns:
        Telegram API response dict.
    """
    async with aiohttp.ClientSession() as session:
        payload: dict = {
            "chat_id": admin_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)

        return await _post(session, bot_token, "sendMessage", payload)


async def get_channel_stats(bot_token: str, channel_id: str) -> dict:
    """Get basic channel statistics via getChat.

    Returns:
        Dict with: chat_id, title, username, member_count (if available).
    """
    async with aiohttp.ClientSession() as session:
        chat = await _post(
            session, bot_token, "getChat", {"chat_id": channel_id}
        )
        result = chat.get("result", {})

        # getMemberCount for subscriber count
        count_resp = await _post(
            session,
            bot_token,
            "getChatMemberCount",
            {"chat_id": channel_id},
        )

        return {
            "chat_id": result.get("id"),
            "title": result.get("title"),
            "username": result.get("username"),
            "member_count": count_resp.get("result", 0),
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _send_message(
    session: aiohttp.ClientSession,
    bot_token: str,
    chat_id: str,
    text: str,
    reply_to: Optional[int] = None,
) -> dict:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    return await _post(session, bot_token, "sendMessage", payload)


async def _send_photo(
    session: aiohttp.ClientSession,
    bot_token: str,
    chat_id: str,
    caption: str,
    image_path: Path | str,
) -> dict:
    url = _API_BASE.format(token=bot_token, method="sendPhoto")

    with open(image_path, "rb") as f:
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        form.add_field("caption", caption)
        form.add_field("parse_mode", "HTML")
        form.add_field("photo", f, filename=Path(image_path).name, content_type="image/png")

        async with session.post(url, data=form) as resp:
            data = await resp.json()
            _check_response(data, "sendPhoto")
            return data


async def _post(
    session: aiohttp.ClientSession,
    bot_token: str,
    method: str,
    payload: dict,
) -> dict:
    url = _API_BASE.format(token=bot_token, method=method)
    async with session.post(url, json=payload) as resp:
        data = await resp.json()
        _check_response(data, method)
        return data


def _check_response(data: dict, method: str) -> None:
    if not data.get("ok"):
        error_code = data.get("error_code", "unknown")
        description = data.get("description", "no description")
        logger.error(
            "telegram.api.error",
            method=method,
            error_code=error_code,
            description=description,
        )
        raise RuntimeError(
            f"Telegram API error in {method}: [{error_code}] {description}"
        )
