"""Telethon userbot -- autonomous chat participant.

Connects as Артём, monitors seller chats, generates responses.

Modes:
- Replies to Артём → auto-send after 30-120 sec delay
- Keyword-detected opportunities → auto-send after 30-120 sec delay
- DMs: bot questions / spam → admin approval before sending
- Cooldown: min 5 min between messages in the same chat

Notifications to admin: info-only (Артём ответил в чат X). No approval buttons.
Ban detection: loud alert if Artём gets kicked/banned from a channel.
"""

from __future__ import annotations

import asyncio
import random
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite
import structlog
from telethon import TelegramClient, events
from telethon.tl.types import Message

from src.chat_monitor.detector import DetectionResult, MessageDetector
from src.chat_monitor.responder import ResponseResult, generate_chat_response

logger = structlog.get_logger(__name__)

_BUFFER_SIZE = 50
_MIN_CONFIDENCE = 0.5
_AUTO_SEND_CONFIDENCE = 0.8  # >= 80% → auto-send, lower → admin approval
_REPLY_DELAY_MIN = 30    # seconds
_REPLY_DELAY_MAX = 120   # seconds
_MAX_REPLIES_PER_CHAIN = 2  # max replies in one conversation thread before stopping
_REPLY_COOLDOWN_MINUTES = 5  # min 5 min between any messages in the same chat


class UserBot:
    """Autonomous chat participant. Sends responses automatically, notifies admin after the fact."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        db_path: str,
        bot_token: str,
        admin_chat_id: int | str,
        monitored_chat_ids: list[int],
        session_path: Optional[Path] = None,
        claude_cli_path: str = "claude",
    ) -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.db_path = db_path
        self.bot_token = bot_token
        self.admin_chat_id = admin_chat_id
        self.monitored_chat_ids = set(monitored_chat_ids)
        self.claude_cli_path = claude_cli_path

        session_file = str(session_path or Path(db_path).parent / "userbot_session")
        self.client = TelegramClient(session_file, api_id, api_hash)

        self.detector = MessageDetector(
            db_path=db_path,
            keyword_patterns_file=Path(db_path).parent / "data" / "keyword_patterns.json",
            claude_cli_path=claude_cli_path,
        )

        self._message_buffer: dict[int, deque] = {}
        # Track Артём's sent message IDs per chat (for reply detection)
        self._my_message_ids: dict[int, set[int]] = {}
        # Track reply chains: chat_id -> count of consecutive Артём replies
        self._reply_chain_count: dict[int, int] = {}
        # Track last reply time per chat for cooldown
        self._last_reply_time: dict[int, float] = {}
        # Cache own user ID
        self._me_id: int | None = None
        # Will be set by main.py after admin_bot is built
        self.admin_bot = None
        # custdev probe tracking: chat_id -> {msg_id -> probe_id}
        self._custdev_probe_ids: dict[int, dict[int, int]] = {}

    async def start(self) -> None:
        """Connect and start listening. Does NOT block -- returns after setup."""
        await self.client.connect()
        if not await self.client.is_user_authorized():
            logger.error("userbot.not_authorized")
            return

        # If no specific chats, discover from joined supergroups
        if not self.monitored_chat_ids:
            async for dialog in self.client.iter_dialogs():
                entity = dialog.entity
                if hasattr(entity, "megagroup") and entity.megagroup:
                    self.monitored_chat_ids.add(entity.id)
            logger.info("userbot.auto_discovered", count=len(self.monitored_chat_ids))

        # Cache own user ID
        me = await self.client.get_me()
        self._me_id = me.id

        # Listen to incoming messages (other people)
        self.client.add_event_handler(
            self._on_message,
            events.NewMessage(incoming=True),
        )

        # Listen to OWN outgoing messages to track sent message IDs
        self.client.add_event_handler(
            self._on_own_message,
            events.NewMessage(outgoing=True),
        )

        # Proactive ban/kick detection — fires immediately when Telegram sends the update
        self.client.add_event_handler(
            self._on_chat_action,
            events.ChatAction(),
        )

        logger.info(
            "userbot.started",
            monitored_chats=list(self.monitored_chat_ids),
        )

        # Keep connection alive without blocking
        # Telethon will process updates via the shared asyncio loop
        while self.client.is_connected():
            await asyncio.sleep(1)

    async def stop(self) -> None:
        await self.client.disconnect()
        logger.info("userbot.stopped")

    async def send_approved_response(self, opportunity_id: int) -> bool:
        """Send an approved response to the chat. Called from admin bot."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM chat_opportunities WHERE id = ? AND status = 'pending'",
                (opportunity_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return False

            opp = dict(row)

        try:
            # Try with -100 prefix for supergroups
            send_chat_id = int(opp["chat_id"])
            if send_chat_id > 0:
                send_chat_id = int(f"-100{send_chat_id}")

            try:
                await self.client.send_message(
                    send_chat_id,
                    opp["response_text"],
                    reply_to=opp["message_id"],
                )
            except Exception as send_exc:
                await self._handle_send_error(send_exc, int(opp["chat_id"]))
                return False

            # Mark as sent
            now = datetime.now(timezone.utc).isoformat()
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE chat_opportunities SET status = 'sent', sent_at = ? WHERE id = ?",
                    (now, opportunity_id),
                )
                await db.commit()

            logger.info("userbot.response_sent", opportunity_id=opportunity_id)
            return True

        except Exception as exc:
            logger.error("userbot.send_failed", opportunity_id=opportunity_id, error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _on_own_message(self, event: events.NewMessage.Event) -> None:
        """Track Артём's own messages for reply detection."""
        message: Message = event.message
        raw_chat_id = event.chat_id
        chat_id = int(str(raw_chat_id).replace("-100", "")) if raw_chat_id < 0 else raw_chat_id

        if chat_id not in self._my_message_ids:
            self._my_message_ids[chat_id] = set()
        self._my_message_ids[chat_id].add(message.id)

        # Keep set size reasonable
        if len(self._my_message_ids[chat_id]) > 500:
            oldest = sorted(self._my_message_ids[chat_id])[:250]
            self._my_message_ids[chat_id] -= set(oldest)

        # Also buffer own messages for context
        msg_dict = {
            "author": "Артём",
            "text": message.text or "",
            "message_id": message.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._buffer_message(chat_id, msg_dict)

    async def _on_message(self, event: events.NewMessage.Event) -> None:
        message: Message = event.message
        raw_chat_id = event.chat_id

        if not message.text or len(message.text) < 3:
            return

        if message.sender_id == self._me_id:
            return

        # --- Private messages (DMs) ---
        if event.is_private:
            logger.info(
                "userbot.dm_received",
                sender_id=message.sender_id,
                text_preview=message.text[:60],
            )
            sender_id = message.sender_id
            msg_dict = {
                "author": _get_sender_name(event),
                "text": message.text,
                "message_id": message.id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._buffer_message(sender_id, msg_dict)
            asyncio.create_task(self._process_dm(message, event))
            return

        # --- Group messages ---
        # Normalize chat ID (Telethon uses -100XXXX for supergroups)
        chat_id = int(str(raw_chat_id).replace("-100", "")) if raw_chat_id < 0 else raw_chat_id

        # Only respond in monitored chats
        if chat_id not in self.monitored_chat_ids and raw_chat_id not in self.monitored_chat_ids:
            return

        if len(message.text) < 10:
            return

        logger.info("userbot.msg_received", chat_id=chat_id, text_preview=message.text[:60])

        msg_dict = {
            "author": _get_sender_name(event),
            "text": message.text,
            "message_id": message.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._buffer_message(chat_id, msg_dict)

        # Check if this is a reply to Артём's message
        is_reply = await self._is_reply_to_me(chat_id, message)

        if is_reply:
            asyncio.create_task(
                self._process_reply(chat_id, message, msg_dict, raw_chat_id=raw_chat_id)
            )
        else:
            # New topic from someone else → reset reply chain for this chat
            self._reply_chain_count[chat_id] = 0
            asyncio.create_task(
                self._process_message(chat_id, message, msg_dict, raw_chat_id=raw_chat_id)
            )

    # ------------------------------------------------------------------
    # DM handling
    # ------------------------------------------------------------------

    async def _process_dm(self, message: Message, event) -> None:
        """Route private messages: product questions → soft response, spam → admin approval."""
        text = message.text
        sender_id = message.sender_id
        author = _get_sender_name(event)

        # Check if we have prior conversation with this person
        has_history = len(self._message_buffer.get(sender_id, [])) > 1

        if _is_bot_question(text):
            # Generate a soft suggested response and send for approval
            logger.info("userbot.dm_bot_question", sender_id=sender_id, author=author)
            asyncio.create_task(
                self._respond_dm_soft(message, sender_id, author)
            )
            return

        if has_history:
            # Person we've talked to before — never auto-respond with sales pitch.
            # Just notify admin so Artem can respond personally and appropriately.
            logger.info("userbot.dm_from_contact", sender_id=sender_id, author=author)
            info = (
                f"<b>Сообщение в ЛС (знакомый контакт)</b>\n"
                f"От: {author} (ID: {sender_id})\n\n"
                f"<i>{text[:500]}</i>\n\n"
                f"<i>Есть история переписки -- ответь сам, по-человечески</i>"
            )
            await self._notify_admin_info(info)
            return

        if _is_spam_dm(text):
            # Only cold spam from strangers — still send for approval, not auto-send
            logger.info("userbot.dm_spam_detected", sender_id=sender_id, author=author)
            asyncio.create_task(
                self._respond_spam_with_approval(message, sender_id, author)
            )
            return

        # Other DMs — ignore silently
        logger.debug("userbot.dm_ignored", sender_id=sender_id)

    async def _respond_spam_with_approval(
        self, message: Message, sender_id: int, author: str
    ) -> None:
        """Generate a spam response and send for admin approval (NOT auto-send)."""
        try:
            from src.content.prompts import DM_SPAM_SALES_PROMPT, get_dm_spam_prompt

            context = list(self._message_buffer.get(sender_id, []))
            context_str = "\n".join(
                f"{m.get('author','?')}: {m.get('text','')}" for m in context[-10:]
            )

            user_prompt = get_dm_spam_prompt(
                spam_message=message.text,
                conversation_context=context_str,
            )

            from src.utils.claude_cli import generate
            raw = await generate(
                system_prompt=DM_SPAM_SALES_PROMPT,
                user_prompt=user_prompt,
                max_tokens=512,
                claude_cli_path=self.claude_cli_path,
                model="sonnet",
            )

            # Parse response — expect plain text or JSON with "text" field
            response_text = raw.strip()
            if response_text.startswith("{"):
                import json
                try:
                    data = json.loads(response_text)
                    response_text = data.get("text", response_text)
                except (json.JSONDecodeError, ValueError):
                    # Extract from markdown if needed
                    import re
                    m = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', response_text)
                    if m:
                        response_text = m.group(1).replace('\\"', '"').replace("\\n", "\n")

            if not response_text or len(response_text) < 5:
                return

            # Save to DB as pending
            opportunity_id = await self._save_dm_opportunity(
                sender_id=sender_id,
                author=author,
                message=message,
                response_text=response_text,
            )

            # Send for admin approval instead of auto-sending
            info = (
                f"<b>Спам в ЛС #{opportunity_id}</b>\n"
                f"От: {author} (ID: {sender_id})\n\n"
                f"Спам: <i>{message.text[:200]}</i>\n\n"
                f"Предложенный ответ:\n{response_text[:300]}"
            )

            if self.admin_bot:
                from telegram import InlineKeyboardButton
                keyboard = [
                    [
                        InlineKeyboardButton("Отправить", callback_data=f"send_dm:{opportunity_id}"),
                        InlineKeyboardButton("Пропустить", callback_data=f"skip_dm:{opportunity_id}"),
                    ]
                ]
                try:
                    await self.admin_bot.send_notification(info, keyboard=keyboard)
                except Exception as exc:
                    logger.error("userbot.dm_spam_admin_failed", error=str(exc))
            else:
                from src.utils.telegram import send_to_admin
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {"text": "Отправить", "callback_data": f"send_dm:{opportunity_id}"},
                            {"text": "Пропустить", "callback_data": f"skip_dm:{opportunity_id}"},
                        ]
                    ]
                }
                try:
                    await send_to_admin(
                        bot_token=self.bot_token,
                        admin_id=self.admin_chat_id,
                        text=info,
                        reply_markup=reply_markup,
                    )
                except Exception as exc:
                    logger.error("userbot.dm_spam_admin_failed", error=str(exc))

            logger.info(
                "userbot.dm_spam_pending",
                sender_id=sender_id,
                author=author,
                opportunity_id=opportunity_id,
            )

        except Exception as exc:
            logger.error("userbot.dm_spam_response_failed", error=str(exc))

    async def _respond_dm_soft(
        self, message: Message, sender_id: int, author: str
    ) -> None:
        """Generate a soft, non-pushy response for DM product questions and send for admin approval."""
        try:
            from src.content.prompts import DM_SOFT_RESPONSE_PROMPT, get_dm_soft_response_prompt

            context = list(self._message_buffer.get(sender_id, []))
            context_str = "\n".join(
                f"{m.get('author','?')}: {m.get('text','')}" for m in context[-10:]
            )

            user_prompt = get_dm_soft_response_prompt(
                dm_message=message.text,
                conversation_context=context_str,
            )

            from src.utils.claude_cli import generate

            raw = await generate(
                system_prompt=DM_SOFT_RESPONSE_PROMPT,
                user_prompt=user_prompt,
                max_tokens=512,
                claude_cli_path=self.claude_cli_path,
                model="sonnet",
            )

            response_text = raw.strip()
            if response_text.startswith("{"):
                import json
                try:
                    data = json.loads(response_text)
                    response_text = data.get("text", response_text)
                except (json.JSONDecodeError, ValueError):
                    import re
                    m = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', response_text)
                    if m:
                        response_text = m.group(1).replace('\\"', '"').replace("\\n", "\n")

            if not response_text or len(response_text) < 5:
                # Fallback to plain notification
                info = (
                    f"<b>Вопрос о боте (ЛС)</b>\n"
                    f"От: {author} (ID: {sender_id})\n\n"
                    f"<i>{message.text[:500]}</i>"
                )
                await self._notify_admin_info(info)
                return

            # Save to DB as pending DM response
            opportunity_id = await self._save_dm_opportunity(
                sender_id=sender_id,
                author=author,
                message=message,
                response_text=response_text,
            )

            # Send to admin with approval buttons
            info = (
                f"<b>Вопрос в ЛС #{opportunity_id}</b>\n"
                f"От: {author} (ID: {sender_id})\n\n"
                f"<i>{message.text[:300]}</i>\n\n"
                f"Предложенный ответ:\n"
                f"{response_text[:400]}\n\n"
                f"<i>Мягкий режим -- без впаривания</i>"
            )

            if self.admin_bot:
                from telegram import InlineKeyboardButton
                keyboard = [
                    [
                        InlineKeyboardButton("Отправить", callback_data=f"send_dm:{opportunity_id}"),
                        InlineKeyboardButton("Пропустить", callback_data=f"skip_dm:{opportunity_id}"),
                    ]
                ]
                try:
                    await self.admin_bot.send_notification(info, keyboard=keyboard)
                except Exception as exc:
                    logger.error("userbot.dm_soft_admin_failed", error=str(exc))
            else:
                from src.utils.telegram import send_to_admin
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {"text": "Отправить", "callback_data": f"send_dm:{opportunity_id}"},
                            {"text": "Пропустить", "callback_data": f"skip_dm:{opportunity_id}"},
                        ]
                    ]
                }
                try:
                    await send_to_admin(
                        bot_token=self.bot_token,
                        admin_id=self.admin_chat_id,
                        text=info,
                        reply_markup=reply_markup,
                    )
                except Exception as exc:
                    logger.error("userbot.dm_soft_admin_failed", error=str(exc))

            logger.info(
                "userbot.dm_soft_generated",
                sender_id=sender_id,
                author=author,
                opportunity_id=opportunity_id,
            )

        except Exception as exc:
            logger.error("userbot.dm_soft_failed", error=str(exc))
            # Fallback: plain notification
            info = (
                f"<b>Вопрос о боте (ЛС)</b>\n"
                f"От: {author} (ID: {sender_id})\n\n"
                f"<i>{message.text[:500]}</i>"
            )
            await self._notify_admin_info(info)

    async def _save_dm_opportunity(
        self,
        sender_id: int,
        author: str,
        message: Message,
        response_text: str,
    ) -> int:
        """Save a DM opportunity to the database."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO chat_opportunities
                    (chat_id, chat_name, message_id, message_text, author,
                     detected_at, response_text, confidence, category, status, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sender_id, f"ЛС {author}", message.id, message.text,
                    author, now, response_text, 0.8, "dm_bot_question",
                    "pending", None,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def send_approved_dm(self, opportunity_id: int) -> bool:
        """Send an approved DM response. Called from admin bot."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM chat_opportunities WHERE id = ? AND status = 'pending'",
                (opportunity_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return False

            opp = dict(row)

        try:
            sender_id = int(opp["chat_id"])

            # Delay 3-8 seconds (DM should feel natural)
            delay = random.randint(3, 8)
            await asyncio.sleep(delay)

            await self.client.send_message(sender_id, opp["response_text"])

            now = datetime.now(timezone.utc).isoformat()
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE chat_opportunities SET status = 'sent', sent_at = ? WHERE id = ?",
                    (now, opportunity_id),
                )
                await db.commit()

            logger.info("userbot.dm_sent", opportunity_id=opportunity_id, sender_id=sender_id)
            return True

        except Exception as exc:
            logger.error("userbot.dm_send_failed", opportunity_id=opportunity_id, error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Group reply handling
    # ------------------------------------------------------------------

    async def _is_reply_to_me(self, chat_id: int, message: Message) -> bool:
        """Check if this message is a reply to one of Артём's messages."""
        if not message.reply_to:
            return False

        reply_to_id = message.reply_to.reply_to_msg_id
        if not reply_to_id:
            return False

        # Fast check: is the replied-to message in our tracked set?
        my_ids = self._my_message_ids.get(chat_id, set())
        if reply_to_id in my_ids:
            return True

        # Fallback: fetch the message and check sender
        try:
            replied_msg = await self.client.get_messages(
                message.chat_id, ids=reply_to_id
            )
            if replied_msg and replied_msg.sender_id == self._me_id:
                # Cache for future lookups
                my_ids.add(reply_to_id)
                return True
        except Exception as exc:
            logger.debug("userbot.reply_check_failed", error=str(exc))

        return False

    async def _get_replied_text(self, message: Message) -> str:
        """Get the text of the message being replied to."""
        if not message.reply_to or not message.reply_to.reply_to_msg_id:
            return ""
        try:
            replied_msg = await self.client.get_messages(
                message.chat_id, ids=message.reply_to.reply_to_msg_id
            )
            return (replied_msg.text or "") if replied_msg else ""
        except Exception:
            return ""

    async def _process_reply(
        self, chat_id: int, message: Message, msg_dict: dict, raw_chat_id: int = 0
    ) -> None:
        """Process a reply to Артём -- auto-send after 30-120 sec delay."""
        try:
            # Record custdev response if this is a reply to a probe (always, regardless of other filters)
            await self._maybe_record_custdev_response(chat_id, message, msg_dict)

            # --- Pre-filters (FREE, no Claude call) ---

            # 1. Conversation ender → don't reply
            if _is_conversation_ender(message.text):
                self._reply_chain_count[chat_id] = 0  # reset chain
                logger.info("userbot.reply_skip_ender", text=message.text[:40])
                return

            # 2. Reply chain limit → stop engaging after N replies in a row
            chain = self._reply_chain_count.get(chat_id, 0)
            if chain >= _MAX_REPLIES_PER_CHAIN:
                logger.info(
                    "userbot.reply_skip_chain_limit",
                    chat_id=chat_id,
                    chain=chain,
                )
                return

            # 3. Cooldown → don't reply too fast in the same chat
            import time
            now = time.time()
            last = self._last_reply_time.get(chat_id, 0)
            if (now - last) < _REPLY_COOLDOWN_MINUTES * 60:
                elapsed = (now - last) / 60
                logger.info(
                    "userbot.reply_skip_cooldown",
                    chat_id=chat_id,
                    elapsed_min=f"{elapsed:.1f}",
                )
                return

            logger.info(
                "userbot.reply_to_artem",
                chat_id=chat_id,
                author=msg_dict["author"],
                text_preview=message.text[:60],
            )

            # Get the original message Артём sent
            artem_original = await self._get_replied_text(message)

            # Build context
            context = list(self._message_buffer.get(chat_id, []))

            response = await generate_chat_response(
                conversation_context=context[:-1],
                target_message=message.text,
                opportunity_category="reply_to_artem",
                claude_cli_path=self.claude_cli_path,
                artem_original_message=artem_original,
            )

            if response.skip:
                self._reply_chain_count[chat_id] = 0
                logger.info("userbot.reply_skip", reason="model said skip")
                return

            if response.confidence < _MIN_CONFIDENCE:
                logger.info("userbot.reply_skip_low_conf", confidence=response.confidence)
                return

            if _contains_product_mention(response.text):
                logger.warning("userbot.reply_blocked_product", text=response.text[:100])
                return

            # Random delay 30-120 seconds (human-like)
            delay = random.randint(_REPLY_DELAY_MIN, _REPLY_DELAY_MAX)
            logger.info("userbot.reply_delayed", delay=delay, chat_id=chat_id)
            await asyncio.sleep(delay)

            # Auto-send (no admin approval)
            send_chat_id = raw_chat_id if raw_chat_id else (
                int(f"-100{chat_id}") if chat_id > 0 else chat_id
            )

            try:
                sent_msg = await self.client.send_message(
                    send_chat_id,
                    response.text,
                    reply_to=message.id,
                )
            except Exception as send_exc:
                await self._handle_send_error(send_exc, chat_id)
                return

            # Track the sent message and update chain counter
            if chat_id not in self._my_message_ids:
                self._my_message_ids[chat_id] = set()
            self._my_message_ids[chat_id].add(sent_msg.id)
            self._reply_chain_count[chat_id] = chain + 1
            self._last_reply_time[chat_id] = time.time()

            # Save to DB as already sent
            opportunity_id = await self._save_opportunity(
                chat_id=chat_id,
                message=message,
                detection=DetectionResult(
                    relevant=True, category="reply_to_artem",
                    score=response.confidence, reasoning="Reply to Артём",
                ),
                response=response,
                status="sent",
            )

            logger.info(
                "userbot.reply_auto_sent",
                opportunity_id=opportunity_id,
                chat_id=chat_id,
                delay=delay,
                chain=chain + 1,
            )

            # Notify admin (info only)
            chat_name = await self._get_chat_name(chat_id)
            author = _get_sender_name_from_message(message)
            info_text = (
                f"<b>Авто-ответ #{opportunity_id}</b> (реплай)\n"
                f"Чат: {chat_name}\n"
                f"От: {author}\n\n"
                f"<i>{message.text[:200]}</i>\n\n"
                f"Ответ Артёма:\n"
                f"{response.text}\n\n"
                f"[delay: {delay}s / {response.confidence:.0%} / chain: {chain + 1}/{_MAX_REPLIES_PER_CHAIN}]"
            )
            await self._notify_admin_info(info_text)

        except Exception as exc:
            logger.error("userbot.reply_error", chat_id=chat_id, error=str(exc))

    async def _notify_admin_info(self, text: str) -> None:
        """Send info notification to admin (no approval buttons)."""
        try:
            if self.admin_bot:
                await self.admin_bot.send_notification(text)
            else:
                from src.utils.telegram import send_to_admin
                await send_to_admin(
                    bot_token=self.bot_token,
                    admin_id=self.admin_chat_id,
                    text=text,
                )
        except Exception as exc:
            logger.error("userbot.admin_info_failed", error=str(exc))

    async def _on_chat_action(self, event: events.ChatAction.Event) -> None:
        """Proactive ban/kick detection. Fires the moment Telegram delivers the update."""
        try:
            # Only care about kicks/bans where the affected user is us
            if not (event.user_kicked or event.user_left):
                return

            if self._me_id is None or event.user_id != self._me_id:
                return

            raw_chat_id = event.chat_id
            chat_id = int(str(raw_chat_id).replace("-100", "")) if raw_chat_id < 0 else raw_chat_id

            # Not a chat we monitored — still alert, just in case
            was_monitored = chat_id in self.monitored_chat_ids
            self.monitored_chat_ids.discard(chat_id)

            action = "КИКНУЛИ" if event.user_kicked else "ПОКИНУЛ / ЗАБЛОКИРОВАН"
            chat_name = await self._get_chat_name(chat_id)

            logger.critical(
                "userbot.BAN_DETECTED_PROACTIVE",
                chat_id=chat_id,
                chat_name=chat_name,
                action=action,
                was_monitored=was_monitored,
            )

            alert = (
                f"🚨🚨🚨 <b>БАН / КИК — ОБНАРУЖЕН СРАЗУ!</b> 🚨🚨🚨\n\n"
                f"‼️ Артёма <b>{action}</b> из чата!\n\n"
                f"<b>Чат:</b> {chat_name} (ID: {chat_id})\n"
                f"<b>Мониторился:</b> {'да' if was_monitored else 'нет'}\n\n"
                f"Чат автоматически убран из мониторинга!\n"
                f"‼️ Проверь вручную прямо сейчас!"
            )

            for i in range(3):
                await self._notify_admin_info(alert)
                if i < 2:
                    await asyncio.sleep(2)

        except Exception as exc:
            logger.error("userbot.chat_action_handler_failed", error=str(exc))

    async def _handle_send_error(self, exc: Exception, chat_id: int) -> None:
        """Detect bans/kicks and send loud alert to admin."""
        from telethon.errors import (
            ChatWriteForbiddenError,
            ChannelPrivateError,
            ForbiddenError,
            UserBannedInChannelError,
        )

        exc_name = type(exc).__name__
        chat_name = await self._get_chat_name(chat_id)

        ban_errors = (
            ChatWriteForbiddenError,
            ChannelPrivateError,
            UserBannedInChannelError,
        )

        if isinstance(exc, ban_errors):
            # Remove from monitored chats immediately so we stop trying
            self.monitored_chat_ids.discard(chat_id)
            logger.critical("userbot.BANNED", chat_id=chat_id, chat_name=chat_name, error=exc_name,
                            remaining_chats=len(self.monitored_chat_ids))

            # LOUD ALERT — Артём забанен/кикнут
            alert = (
                f"🚨🚨🚨 <b>БАН / КИК — НЕЛЬЗЯ ПИСАТЬ!</b> 🚨🚨🚨\n\n"
                f"‼️‼️ Артём заблокирован в чате!\n\n"
                f"<b>Чат:</b> {chat_name} (ID: {chat_id})\n"
                f"<b>Ошибка:</b> {exc_name}\n"
                f"<b>Детали:</b> {str(exc)[:200]}\n\n"
                f"Чат автоматически убран из мониторинга!\n"
                f"‼️ Проверь вручную прямо сейчас!"
            )
            # Send alert 3 times with pauses to make it impossible to miss
            for i in range(3):
                await self._notify_admin_info(alert)
                if i < 2:
                    await asyncio.sleep(2)
        elif isinstance(exc, ForbiddenError):
            alert = (
                f"🚨 <b>ДОСТУП ЗАПРЕЩЁН</b>\n\n"
                f"Чат: {chat_name} (ID: {chat_id})\n"
                f"Ошибка: {exc_name}: {str(exc)[:200]}\n\n"
                f"Возможно, ограничение на отправку сообщений."
            )
            logger.error("userbot.forbidden", chat_id=chat_id, error=str(exc))
            await self._notify_admin_info(alert)
        elif "slowmode" in str(exc).lower() or "SLOWMODE_WAIT" in str(exc):
            # Slowmode — не критично, просто лог
            logger.warning("userbot.slowmode", chat_id=chat_id, error=str(exc))
        else:
            # Unknown send error — log and notify
            logger.error("userbot.send_failed", chat_id=chat_id, error=str(exc))
            alert = (
                f"<b>Ошибка отправки</b>\n"
                f"Чат: {chat_name} (ID: {chat_id})\n"
                f"Ошибка: {exc_name}: {str(exc)[:200]}"
            )
            await self._notify_admin_info(alert)

    async def _process_message(
        self, chat_id: int, message: Message, msg_dict: dict, raw_chat_id: int = 0
    ) -> None:
        """Process keyword-detected message.

        Confidence >= 80% → auto-send after delay.
        Confidence 50-80% → save as pending, send to admin for approval.
        Confidence < 50% → skip.
        """
        try:
            result = await self.detector.detect(
                chat_id=chat_id,
                message_text=message.text,
                use_semantic_check=True,
            )

            if not result.relevant:
                return

            logger.info(
                "userbot.relevant",
                chat_id=chat_id,
                category=result.category,
                score=result.score,
            )

            # Generate response
            context = list(self._message_buffer.get(chat_id, []))
            response = await generate_chat_response(
                conversation_context=context[:-1],
                target_message=message.text,
                opportunity_category=result.category,
                claude_cli_path=self.claude_cli_path,
            )

            if response.skip:
                logger.info("userbot.skip", reason="model said skip")
                return

            if response.confidence < _MIN_CONFIDENCE:
                logger.info("userbot.skip_low_conf", confidence=response.confidence)
                return

            # Safety: no product mentions
            if _contains_product_mention(response.text):
                logger.warning("userbot.blocked_product", text=response.text[:100])
                return

            if response.confidence >= _AUTO_SEND_CONFIDENCE:
                # High confidence → auto-send
                await self._auto_send_message(
                    chat_id=chat_id,
                    message=message,
                    detection=result,
                    response=response,
                    raw_chat_id=raw_chat_id,
                )
            else:
                # Medium confidence (50-80%) → silent drop, save to DB for stats
                await self._save_opportunity(
                    chat_id=chat_id,
                    message=message,
                    detection=result,
                    response=response,
                    status="dropped",
                )
                logger.info(
                    "userbot.dropped_low_conf",
                    chat_id=chat_id,
                    confidence=response.confidence,
                    category=result.category,
                )

        except Exception as exc:
            logger.error("userbot.error", chat_id=chat_id, error=str(exc))

    async def _auto_send_message(
        self,
        chat_id: int,
        message: Message,
        detection: DetectionResult,
        response: ResponseResult,
        raw_chat_id: int = 0,
    ) -> None:
        """Auto-send a high-confidence response after a human-like delay."""
        delay = random.randint(_REPLY_DELAY_MIN, _REPLY_DELAY_MAX)
        logger.info("userbot.auto_delayed", delay=delay, chat_id=chat_id)
        await asyncio.sleep(delay)

        send_chat_id = raw_chat_id if raw_chat_id else (
            int(f"-100{chat_id}") if chat_id > 0 else chat_id
        )

        try:
            sent_msg = await self.client.send_message(
                send_chat_id,
                response.text,
                reply_to=message.id,
            )
        except Exception as send_exc:
            await self._handle_send_error(send_exc, chat_id)
            return

        # Track the sent message
        if chat_id not in self._my_message_ids:
            self._my_message_ids[chat_id] = set()
        self._my_message_ids[chat_id].add(sent_msg.id)

        # Save to DB as already sent
        opportunity_id = await self._save_opportunity(
            chat_id=chat_id,
            message=message,
            detection=detection,
            response=response,
            status="sent",
        )

        logger.info(
            "userbot.auto_sent",
            opportunity_id=opportunity_id,
            chat_id=chat_id,
            category=detection.category,
            confidence=response.confidence,
            delay=delay,
        )

        # Notify admin (info only, no buttons)
        chat_name = await self._get_chat_name(chat_id)
        author = _get_sender_name_from_message(message)
        info_text = (
            f"<b>Авто-ответ #{opportunity_id}</b>\n"
            f"Чат: {chat_name}\n"
            f"От: {author}\n\n"
            f"<i>{message.text[:200]}</i>\n\n"
            f"Ответ Артёма:\n"
            f"{response.text}\n\n"
            f"[{detection.category} / {response.confidence:.0%} / delay: {delay}s]"
        )
        await self._notify_admin_info(info_text)

    async def _save_opportunity(
        self,
        chat_id: int,
        message: Message,
        detection: DetectionResult,
        response: ResponseResult,
        status: str = "pending",
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        chat_name = await self._get_chat_name(chat_id)
        sent_at = now if status == "sent" else None

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO chat_opportunities
                    (chat_id, chat_name, message_id, message_text, author,
                     detected_at, response_text, confidence, category, status, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chat_id, chat_name, message.id, message.text,
                    _get_sender_name_from_message(message),
                    now, response.text, response.confidence, detection.category,
                    status, sent_at,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def _send_to_admin(
        self,
        opportunity_id: int,
        chat_id: int,
        message: Message,
        detection: DetectionResult,
        response: ResponseResult,
    ) -> None:
        """Send approval request to admin bot."""
        chat_name = await self._get_chat_name(chat_id)
        author = _get_sender_name_from_message(message)

        text = (
            f"<b>Ответ #{opportunity_id}</b>\n"
            f"Чат: {chat_name}\n"
            f"От: {author}\n\n"
            f"<i>{message.text[:300]}</i>\n\n"
            f"Ответ Артёма:\n"
            f"{response.text}\n\n"
            f"[{detection.category} / {response.confidence:.0%}]"
        )

        if self.admin_bot:
            from telegram import InlineKeyboardButton
            keyboard = [
                [
                    InlineKeyboardButton("Отправить", callback_data=f"send_reply:{opportunity_id}"),
                    InlineKeyboardButton("Пропустить", callback_data=f"skip_reply:{opportunity_id}"),
                ]
            ]
            try:
                await self.admin_bot.send_notification(text, keyboard=keyboard)
            except Exception as exc:
                logger.error("userbot.admin_notify_failed", error=str(exc))
        else:
            # Fallback: raw API
            from src.utils.telegram import send_to_admin
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "Отправить", "callback_data": f"send_reply:{opportunity_id}"},
                        {"text": "Пропустить", "callback_data": f"skip_reply:{opportunity_id}"},
                    ]
                ]
            }
            try:
                await send_to_admin(
                    bot_token=self.bot_token,
                    admin_id=self.admin_chat_id,
                    text=text,
                    reply_markup=reply_markup,
                )
            except Exception as exc:
                logger.error("userbot.admin_notify_failed", error=str(exc))

    def _buffer_message(self, chat_id: int, msg_dict: dict) -> None:
        if chat_id not in self._message_buffer:
            self._message_buffer[chat_id] = deque(maxlen=_BUFFER_SIZE)
        self._message_buffer[chat_id].append(msg_dict)

    async def send_custdev_probe(
        self,
        chat_id: int,
        raw_chat_id: int | None = None,
        chat_name: str = "",
        topic: str | None = None,
    ) -> bool:
        """Send a custdev research question to a chat.

        Returns True if sent, False if skipped (cooldown, no topic, error).
        Called by the scheduler job or admin bot commands.
        """
        import json
        import random

        from src.content.prompts import (
            CUSTDEV_QUESTIONS,
            CUSTDEV_SYSTEM_PROMPT,
            CUSTDEV_TOPICS,
            get_custdev_probe_prompt,
        )
        from src.utils.claude_cli import generate

        # Cooldown: don't probe same chat more than once in 3 days
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT COUNT(*) FROM custdev_probes
                   WHERE chat_id = ? AND date(sent_at) >= date('now', '-3 days')""",
                (chat_id,),
            )
            row = await cursor.fetchone()
            if row and row[0] > 0:
                logger.info("custdev.skip_cooldown", chat_id=chat_id)
                return False

        # Pick topic not recently used in this chat (last 30 days)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT question_topic FROM custdev_probes
                   WHERE chat_id = ? AND date(sent_at) >= date('now', '-30 days')""",
                (chat_id,),
            )
            rows = await cursor.fetchall()
        used_topics = {r[0] for r in rows}

        if topic is None:
            # Product-validation topics first (most useful for PMF research)
            priority = [
                "repeat_sales", "customer_contacts", "inserts_packaging",
                "marketplace_dependency", "external_traffic",
            ]
            available = [t for t in priority if t not in used_topics]
            if not available:
                available = [t for t in CUSTDEV_TOPICS if t not in used_topics]
            if not available:
                available = CUSTDEV_TOPICS  # full rotation reset
            topic = random.choice(available)

        variants = CUSTDEV_QUESTIONS.get(topic, [])
        if not variants:
            logger.warning("custdev.no_variants", topic=topic)
            return False

        # Build recent chat context from message buffer
        context_messages = list(self._message_buffer.get(chat_id, []))
        chat_context = "\n".join(
            f"{m.get('author', '?')}: {m.get('text', '')[:100]}"
            for m in context_messages[-10:]
        )

        # Recent probes summary for de-duplication
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT question_text FROM custdev_probes WHERE chat_id = ? ORDER BY sent_at DESC LIMIT 5",
                (chat_id,),
            )
            rows = await cursor.fetchall()
        recent_probes_summary = "\n".join(r[0] for r in rows) if rows else ""

        base_question = random.choice(variants)
        user_prompt = get_custdev_probe_prompt(
            base_question=base_question,
            chat_context=chat_context,
            recent_probes_summary=recent_probes_summary,
        )

        try:
            raw = await generate(
                system_prompt=CUSTDEV_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=200,
                claude_cli_path=self.claude_cli_path,
                model="haiku",
            )
        except Exception as exc:
            logger.error("custdev.generation_failed", chat_id=chat_id, error=str(exc))
            return False

        question_text = raw.strip()
        if not question_text or len(question_text) < 10:
            logger.warning("custdev.empty_response", chat_id=chat_id)
            return False

        # Safety: no product mentions
        if _contains_product_mention(question_text):
            logger.warning("custdev.blocked_product", text=question_text[:100])
            return False

        # Human-like delay before sending
        delay = random.randint(30, 120)
        logger.info("custdev.delayed", delay=delay, chat_id=chat_id, topic=topic)
        await asyncio.sleep(delay)

        # Compute raw_chat_id for Telethon if not provided
        if raw_chat_id is None:
            raw_chat_id = int(f"-100{chat_id}") if chat_id > 0 else chat_id

        try:
            sent_msg = await self.client.send_message(raw_chat_id, question_text)
        except Exception as exc:
            await self._handle_send_error(exc, chat_id)
            return False

        # Track as Артём's own message (so replies are caught by _process_reply)
        if chat_id not in self._my_message_ids:
            self._my_message_ids[chat_id] = set()
        self._my_message_ids[chat_id].add(sent_msg.id)

        # Save to DB
        now = datetime.now(timezone.utc).isoformat()
        if not chat_name:
            chat_name = await self._get_chat_name(chat_id)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO custdev_probes
                   (chat_id, chat_name, question_topic, question_text, message_id, sent_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (chat_id, chat_name, topic, question_text, sent_msg.id, now),
            )
            probe_id = cursor.lastrowid
            await db.commit()

        # Cache probe ID for response tracking during current session
        if chat_id not in self._custdev_probe_ids:
            self._custdev_probe_ids[chat_id] = {}
        self._custdev_probe_ids[chat_id][sent_msg.id] = probe_id

        logger.info(
            "custdev.probe_sent",
            chat_id=chat_id,
            topic=topic,
            probe_id=probe_id,
            message_id=sent_msg.id,
        )

        await self._notify_admin_info(
            f"<b>Кастдев #{probe_id}</b>\n"
            f"Чат: {chat_name}\n"
            f"Тема: {topic}\n\n"
            f"<i>{question_text}</i>"
        )
        return True

    async def _maybe_record_custdev_response(
        self, chat_id: int, message: Message, msg_dict: dict
    ) -> None:
        """If this message is a reply to a custdev probe, record the response."""
        if not message.reply_to or not message.reply_to.reply_to_msg_id:
            return

        replied_id = message.reply_to.reply_to_msg_id

        # Check in-memory cache first (fast path)
        probe_id = self._custdev_probe_ids.get(chat_id, {}).get(replied_id)

        if probe_id is None:
            # DB lookup — handles restarts where cache is empty
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id FROM custdev_probes WHERE chat_id = ? AND message_id = ?",
                    (chat_id, replied_id),
                )
                row = await cursor.fetchone()
                probe_id = row[0] if row else None

        if probe_id:
            await self._record_custdev_response(
                probe_id=probe_id,
                author=msg_dict.get("author", "?"),
                text=msg_dict.get("text", ""),
            )

    async def _record_custdev_response(self, probe_id: int, author: str, text: str) -> None:
        """Append a response to a custdev probe record."""
        import json
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT responses_count, responses_json FROM custdev_probes WHERE id = ?",
                    (probe_id,),
                )
                row = await cursor.fetchone()
                if not row:
                    return

                count = (row[0] or 0) + 1
                responses = json.loads(row[1] or "[]")
                responses.append({"author": author, "text": text[:300]})

                await db.execute(
                    "UPDATE custdev_probes SET responses_count = ?, responses_json = ? WHERE id = ?",
                    (count, json.dumps(responses, ensure_ascii=False), probe_id),
                )
                await db.commit()

            logger.info("custdev.response_recorded", probe_id=probe_id, author=author, total=count)
        except Exception as exc:
            logger.error("custdev.record_failed", probe_id=probe_id, error=str(exc))

    async def _get_chat_name(self, chat_id: int) -> str:
        try:
            entity = await self.client.get_entity(chat_id)
            return getattr(entity, "title", None) or str(chat_id)
        except Exception:
            return str(chat_id)


import re as _re

# Short messages that signal "end of conversation" — no need to reply
_ENDER_EXACT = {
    "ок", "ok", "окей", "ладно", "лады", "хорошо",
    "да", "ага", "угу", "ну да", "да да",
    "согласен", "согласна", "соглас",
    "спасибо", "спс", "благодарю", "спасибки", "пасиб",
    "понял", "понятно", "понял спасибо", "ясно",
    "точно", "верно", "именно", "факт",
    "класс", "круто", "супер", "огонь", "топ", "кайф",
    "+", "++", "+++", "👍", "🤝", "🙏", "😂", "😅",
    "хах", "хаха", "ахах", "лол", ")))","хех",
    "ну ок", "ну ладно", "ну понятно",
    # Extended: common short replies that don't need a response
    "ну да точно", "это да", "да уж", "ну", "не не",
    "логично", "жиза", "жизненно", "в точку",
    "буду иметь в виду", "учту", "запомню",
    "сенк", "сенкс", "thx", "thanks", "спасибо большое",
    "ну хорошо", "ок спасибо", "ок понял", "ок спс",
    "да я понял", "я понял", "я понял спасибо",
    "ну понятно", "короче да", "ну логично",
    "интересно", "хм", "хмм",
}

_ENDER_PATTERNS = _re.compile(
    r"^("
    r"спасиб\w*|благодар\w*|"          # спасибо/благодарю
    r"соглас\w*|"                       # согласен/а
    r"поня[тл]\w*|"                     # понял/понятно
    r"(ну\s+)?(ок|окей|ладно|хорошо)|"  # ок/ладно
    r"да\s*(да)*|ага|угу|"              # да/ага
    r"точно|верно|именно|факт|"         # подтверждения
    r"круто|класс|супер|огонь|топ|"     # одобрения
    r"ха+х?а*\)?|лол|[)]{2,}|"         # смех
    r"[👍🤝🙏😂😅🔥❤️]+\s*|"             # эмодзи
    r"(ну\s+)?(логично|жиза|жизненно|в точку)|"  # согласие
    r"(ок|ну|да)\s+спасиб\w*|"         # ок спасибо
    r"(ок|ну|да)\s+поня[тл]\w*|"       # ок понял
    r"буду\s+(иметь\s+в\s+виду|знать)|учту|запомню|"  # принял к сведению
    r"я\s+поня[тл]\w*"                 # я понял
    r")[\s!.)*]*$",
    _re.IGNORECASE | _re.UNICODE,
)


def _is_conversation_ender(text: str) -> bool:
    """Check if a message is a conversation-ending acknowledgment."""
    clean = text.strip().lower()

    # Short-to-medium messages — likely just a reaction or acknowledgment
    if len(clean) <= 50:
        if clean in _ENDER_EXACT:
            return True
        if _ENDER_PATTERNS.match(clean):
            return True

    return False


def _is_bot_question(text: str) -> bool:
    """Check if DM is asking about our bot/product."""
    lower = text.lower()
    bot_keywords = [
        "своя база", "свою базу", "своей базы",
        "ваш бот", "твой бот", "этот бот",
        "dbsales", "dbseller",
        "как работает бот", "что умеет бот",
        "сколько стоит", "какая цена", "тариф",
        "подключить", "попробовать", "демо",
        "qr код", "qr-код", "куар",
        "база покупателей", "базу покупателей",
        "рассылк", "повторные продаж",
    ]
    return any(kw in lower for kw in bot_keywords)


def _is_spam_dm(text: str) -> bool:
    """Check if DM looks like spam/unsolicited sales."""
    lower = text.lower()
    spam_signals = [
        "предлагаю", "предлагаем", "наши услуги", "наша компания",
        "продвижение", "раскрутк", "накрутк", "реклам",
        "менеджер маркетплейс", "ведение аккаунт", "ведение магазин",
        "дизайн карточ", "инфографик", "фото товар",
        "seo карточ", "оптимизац", "аналитик",
        "выведем в топ", "поднимем продаж", "увеличим",
        "бесплатн", "скидк", "акци", "специальное предложение",
        "пишите в лс", "напишите мне", "свяжитесь",
        "заработ", "доход", "пассивн", "инвестиц",
        "канал", "подписывайтесь", "переходите",
        "сотрудничеств", "партнёрств", "партнерств",
        "могу помочь", "готов помочь", "хотите",
        "нужен менеджер", "нужен дизайнер",
        "фулфилмент", "логист", "склад",
        "wildberries", "вайлдберриз",
        "самовыкуп", "отзыв",
    ]
    # Spam if 2+ signals or message is long (>200 chars) with any signal
    matches = sum(1 for s in spam_signals if s in lower)
    if matches >= 2:
        return True
    if matches >= 1 and len(text) > 200:
        return True
    # Links in first message
    if "http" in lower or "t.me/" in lower or "wa.me/" in lower:
        return True
    return False


def _contains_product_mention(text: str) -> bool:
    lower = text.lower()
    blocked = ["своя база", "dbsales", "dbseller", "@db", "наш бот", "наш сервис", "наш продукт"]
    return any(b in lower for b in blocked)


def _get_sender_name(event: events.NewMessage.Event) -> str:
    sender = event.sender
    if sender is None:
        return "Неизвестный"
    name_parts = [
        getattr(sender, "first_name", "") or "",
        getattr(sender, "last_name", "") or "",
    ]
    name = " ".join(p for p in name_parts if p).strip()
    return name or getattr(sender, "username", None) or str(getattr(sender, "id", "?"))


def _get_sender_name_from_message(message: Message) -> str:
    if hasattr(message, "sender") and message.sender:
        sender = message.sender
        name_parts = [
            getattr(sender, "first_name", "") or "",
            getattr(sender, "last_name", "") or "",
        ]
        name = " ".join(p for p in name_parts if p).strip()
        return name or getattr(sender, "username", None) or "Участник"
    return "Участник"
