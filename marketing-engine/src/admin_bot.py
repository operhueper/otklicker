"""Admin bot for managing content queue.

Interactive Telegram bot for Artyom to review, approve/reject posts,
check queue status, and trigger generation/publishing manually.

Uses python-telegram-bot v21+ with polling (no webhooks needed).
Bot token: ADMIN_BOT_TOKEN (separate from channel bot).

Preview sends photo + caption so Artyom sees the image before approving.
Load pre-written posts from data/prewritten_posts.json into the queue.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Optional

import aiosqlite
import structlog
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from src.content.queue import ContentQueue, PostStatus

logger = structlog.get_logger(__name__)

# Telegram caption limit
_MAX_CAPTION = 1024


class AdminBot:
    """Interactive admin bot for content management."""

    def __init__(
        self,
        admin_bot_token: str,
        channel_bot_token: str,
        channel_id: str,
        admin_chat_id: int,
        db_path: str,
        data_dir: str,
        claude_cli_path: str = "claude",
    ) -> None:
        self.admin_bot_token = admin_bot_token
        self.channel_bot_token = channel_bot_token
        self.channel_id = channel_id
        self.admin_chat_id = admin_chat_id
        self.db_path = db_path
        self.data_dir = data_dir
        self.claude_cli_path = claude_cli_path

        self._images_dir = Path(data_dir) / "images"
        self._images_dir.mkdir(parents=True, exist_ok=True)

        self._app: Application | None = None

    def build(self) -> Application:
        """Build and configure the bot application."""
        self._app = (
            Application.builder()
            .token(self.admin_bot_token)
            .build()
        )

        # Commands
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("pending", self._cmd_pending))
        self._app.add_handler(CommandHandler("queue", self._cmd_queue))
        self._app.add_handler(CommandHandler("publish", self._cmd_publish))
        self._app.add_handler(CommandHandler("generate", self._cmd_generate))
        self._app.add_handler(CommandHandler("help", self._cmd_help))

        # Callback queries from inline buttons
        self._app.add_handler(CallbackQueryHandler(self._cb_preview, pattern=r"^preview:\d+$"))
        self._app.add_handler(CallbackQueryHandler(self._cb_approve, pattern=r"^approve:\d+$"))
        self._app.add_handler(CallbackQueryHandler(self._cb_reject, pattern=r"^reject:\d+$"))
        self._app.add_handler(CallbackQueryHandler(self._cb_pending_list, pattern=r"^pending_list$"))
        self._app.add_handler(CallbackQueryHandler(self._cb_publish_now, pattern=r"^publish_now:\d+$"))

        # Generate / load buttons
        self._app.add_handler(CallbackQueryHandler(self._cb_generate_menu, pattern=r"^generate_menu$"))
        self._app.add_handler(CallbackQueryHandler(self._cb_load_prewritten, pattern=r"^load_prewritten$"))
        self._app.add_handler(CallbackQueryHandler(self._cb_generate_new, pattern=r"^generate_new$"))

        # Chat response approval buttons
        self._app.add_handler(CallbackQueryHandler(self._cb_send_reply, pattern=r"^send_reply:\d+$"))
        self._app.add_handler(CallbackQueryHandler(self._cb_skip_reply, pattern=r"^skip_reply:\d+$"))

        # DM response approval buttons
        self._app.add_handler(CallbackQueryHandler(self._cb_send_dm, pattern=r"^send_dm:\d+$"))
        self._app.add_handler(CallbackQueryHandler(self._cb_skip_dm, pattern=r"^skip_dm:\d+$"))

        return self._app

    # Will be set from main.py
    userbot = None

    # ------------------------------------------------------------------
    # Access control
    # ------------------------------------------------------------------

    def _is_admin(self, update: Update) -> bool:
        """Only respond to admin user."""
        user_id = update.effective_user.id if update.effective_user else None
        return user_id == self.admin_chat_id

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_admin(update):
            return

        queue = ContentQueue(self.db_path)
        counts = await queue.count_by_status()

        pending = counts.get(PostStatus.PENDING_REVIEW.value, 0)
        approved = counts.get(PostStatus.APPROVED.value, 0)
        published = counts.get(PostStatus.PUBLISHED.value, 0)

        text = (
            "<b>Своя база -- Управление контентом</b>\n\n"
            f"На проверке: {pending}\n"
            f"Одобрено (ждут публикации): {approved}\n"
            f"Опубликовано: {published}\n\n"
            "Команды:\n"
            "/pending -- посты на проверке\n"
            "/queue -- статистика очереди\n"
            "/publish -- опубликовать следующий пост\n"
            "/generate -- сгенерировать посты\n"
            "/help -- справка"
        )

        keyboard = []
        if pending > 0:
            keyboard.append([InlineKeyboardButton("Посмотреть очередь", callback_data="pending_list")])
        keyboard.append([InlineKeyboardButton("Сгенерировать пост", callback_data="generate_menu")])

        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _cmd_pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_admin(update):
            return
        await self._send_pending_list(context.bot, update.effective_chat.id)

    async def _cmd_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_admin(update):
            return

        queue = ContentQueue(self.db_path)
        counts = await queue.count_by_status()

        lines = ["<b>Очередь постов</b>\n"]
        status_labels = {
            "draft": "Черновики",
            "pending_review": "На проверке",
            "approved": "Одобрено",
            "rejected": "Отклонено",
            "published": "Опубликовано",
        }
        total = 0
        for status, label in status_labels.items():
            count = counts.get(status, 0)
            total += count
            lines.append(f"{label}: {count}")

        lines.append(f"\nВсего: {total}")

        await update.message.reply_text("\n".join(lines), parse_mode="HTML")

    async def _cmd_publish(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_admin(update):
            return

        await update.message.reply_text("Публикую следующий одобренный пост...")

        try:
            from src.publisher.channel import ChannelPublisher

            queue = ContentQueue(self.db_path)
            publisher = ChannelPublisher(
                bot_token=self.channel_bot_token,
                channel_id=self.channel_id,
                data_dir=Path(self.data_dir),
                claude_cli_path=self.claude_cli_path,
            )

            result = await publisher.publish_next(queue)

            if result:
                await update.message.reply_text(
                    f"Пост опубликован\n\n"
                    f"ID: {result['id']}\n"
                    f"Тип: {result.get('type', '?')}"
                )
            else:
                await update.message.reply_text(
                    "Нет одобренных постов.\n"
                    "Проверь очередь /pending и одобри посты."
                )

        except Exception as exc:
            logger.error("admin_bot.publish_failed", error=str(exc))
            await update.message.reply_text(f"Ошибка публикации: {exc}")

    async def _cmd_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_admin(update):
            return

        available = self._count_available_prewritten()

        keyboard = [
            [InlineKeyboardButton(
                f"Загрузить готовый пост ({available} шт)",
                callback_data="load_prewritten",
            )],
            [InlineKeyboardButton(
                "Сгенерировать новый (Claude)",
                callback_data="generate_new",
            )],
        ]

        await update.message.reply_text(
            f"<b>Создать пост</b>\n\n"
            f"Готовых постов в очереди: {available}\n"
            f"Или сгенерировать новый через Claude (1-2 мин).",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_admin(update):
            return

        await update.message.reply_text(
            "<b>Команды</b>\n\n"
            "/pending -- посты на проверке (с кнопками)\n"
            "/queue -- статистика очереди\n"
            "/publish -- опубликовать следующий одобренный пост\n"
            "/generate -- сгенерировать новый пост\n"
            "/help -- эта справка\n\n"
            "<b>Автопостинг</b>\n"
            "Генерация: воскресенье 10:00\n"
            "Публикация: вт/чт/сб 10:00",
            parse_mode="HTML",
        )

    # ------------------------------------------------------------------
    # Callback query handlers
    # ------------------------------------------------------------------

    async def _cb_pending_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        if not self._is_admin(update):
            return

        # Delete previous message (may be text or photo)
        await _safe_delete(query.message)
        await self._send_pending_list(context.bot, update.effective_chat.id)

    async def _cb_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show post preview with image + approve/reject buttons."""
        query = update.callback_query
        await query.answer()

        if not self._is_admin(update):
            return

        post_id = int(query.data.split(":")[1])
        queue = ContentQueue(self.db_path)
        post = await queue.get_post(post_id)

        if not post:
            await query.message.edit_text("Пост не найден.")
            return

        # Get or generate image for this post
        image_path = await self._get_or_generate_image(post, queue)

        # Build caption (respecting Telegram 1024 limit)
        caption = _format_post_caption(post)

        keyboard = [
            [
                InlineKeyboardButton("Опубликовать сейчас", callback_data=f"publish_now:{post_id}"),
                InlineKeyboardButton("Одобрить", callback_data=f"approve:{post_id}"),
            ],
            [
                InlineKeyboardButton("Отклонить", callback_data=f"reject:{post_id}"),
                InlineKeyboardButton("Назад к списку", callback_data="pending_list"),
            ],
        ]
        markup = InlineKeyboardMarkup(keyboard)

        # Delete old message, send photo or text
        await _safe_delete(query.message)

        if image_path and image_path.exists():
            with open(image_path, "rb") as photo_file:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=markup,
                )
        else:
            # Fallback: text-only preview
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=_format_post_preview(post),
                parse_mode="HTML",
                reply_markup=markup,
            )

    async def _cb_approve(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer("Пост одобрен")

        if not self._is_admin(update):
            return

        post_id = int(query.data.split(":")[1])
        queue = ContentQueue(self.db_path)
        await queue.approve(post_id)

        logger.info("admin_bot.post_approved", post_id=post_id)

        keyboard = [[InlineKeyboardButton("К списку", callback_data="pending_list")]]

        await _safe_delete(query.message)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"Пост #{post_id} одобрен.\n"
                f"Будет опубликован в ближайший слот (вт/чт/сб 10:00)."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _cb_reject(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer("Пост отклонён")

        if not self._is_admin(update):
            return

        post_id = int(query.data.split(":")[1])
        queue = ContentQueue(self.db_path)
        await queue.reject(post_id, reason="Отклонён вручную")

        logger.info("admin_bot.post_rejected", post_id=post_id)

        keyboard = [[InlineKeyboardButton("К списку", callback_data="pending_list")]]

        await _safe_delete(query.message)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Пост #{post_id} отклонён.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # ------------------------------------------------------------------
    # Chat response approval
    # ------------------------------------------------------------------

    async def _cb_send_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Approve and send a chat response."""
        query = update.callback_query
        await query.answer("Отправляю...")

        if not self._is_admin(update):
            return

        opp_id = int(query.data.split(":")[1])

        if self.userbot:
            ok = await self.userbot.send_approved_response(opp_id)
            if ok:
                await query.message.edit_text(
                    query.message.text + "\n\nОтправлено",
                    parse_mode="HTML",
                )
            else:
                await query.message.edit_text(
                    query.message.text + "\n\nОшибка отправки (уже отправлено?)",
                    parse_mode="HTML",
                )
        else:
            await query.message.edit_text(
                query.message.text + "\n\nUserbot не подключен",
                parse_mode="HTML",
            )

    async def _cb_skip_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Skip a chat response."""
        query = update.callback_query
        await query.answer("Пропущено")

        if not self._is_admin(update):
            return

        opp_id = int(query.data.split(":")[1])

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE chat_opportunities SET status = 'skipped' WHERE id = ?",
                (opp_id,),
            )
            await db.commit()

        await query.message.edit_text(
            query.message.text + "\n\nПропущено",
            parse_mode="HTML",
        )

    # ------------------------------------------------------------------
    # DM response approval
    # ------------------------------------------------------------------

    async def _cb_send_dm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Approve and send a DM response (soft mode)."""
        query = update.callback_query
        await query.answer("Отправляю в ЛС...")

        if not self._is_admin(update):
            return

        opp_id = int(query.data.split(":")[1])

        if self.userbot:
            ok = await self.userbot.send_approved_dm(opp_id)
            if ok:
                await query.message.edit_text(
                    query.message.text + "\n\nОтправлено в ЛС",
                    parse_mode="HTML",
                )
            else:
                await query.message.edit_text(
                    query.message.text + "\n\nОшибка отправки",
                    parse_mode="HTML",
                )
        else:
            await query.message.edit_text(
                query.message.text + "\n\nUserbot не подключен",
                parse_mode="HTML",
            )

    async def _cb_skip_dm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Skip a DM response."""
        query = update.callback_query
        await query.answer("Пропущено")

        if not self._is_admin(update):
            return

        opp_id = int(query.data.split(":")[1])

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE chat_opportunities SET status = 'skipped' WHERE id = ?",
                (opp_id,),
            )
            await db.commit()

        await query.message.edit_text(
            query.message.text + "\n\nПропущено",
            parse_mode="HTML",
        )

    # ------------------------------------------------------------------
    # Generate menu & prewritten posts loader
    # ------------------------------------------------------------------

    async def _cb_generate_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show generate options: load from queue or generate via Claude."""
        query = update.callback_query
        await query.answer()

        if not self._is_admin(update):
            return

        # Count available prewritten posts
        available = self._count_available_prewritten()

        keyboard = [
            [InlineKeyboardButton(
                f"Загрузить готовый пост ({available} шт)",
                callback_data="load_prewritten",
            )],
            [InlineKeyboardButton(
                "Сгенерировать новый (Claude)",
                callback_data="generate_new",
            )],
        ]

        await _safe_delete(query.message)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "<b>Создать пост</b>\n\n"
                f"Готовых постов в очереди: {available}\n"
                "Или сгенерировать новый через Claude (1-2 мин)."
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _cb_load_prewritten(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Load next prewritten post from JSON into the queue with auto-image."""
        query = update.callback_query
        await query.answer("Загружаю пост...")

        if not self._is_admin(update):
            return

        post_data = self._get_next_prewritten()
        if not post_data:
            await _safe_delete(query.message)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Все готовые посты уже загружены. Используй генерацию через Claude.",
            )
            return

        queue = ContentQueue(self.db_path)
        post_id = await queue.add_post(
            post_type=post_data.get("type", "pain_solution"),
            title=post_data.get("title", ""),
            text=post_data.get("text", ""),
            cta=post_data.get("cta", ""),
        )

        # Auto-generate image
        post = await queue.get_post(post_id)
        image_path = await self._get_or_generate_image(post, queue)

        # Show preview with publish/approve buttons
        caption = _format_post_caption(post)

        keyboard = [
            [
                InlineKeyboardButton("Опубликовать сейчас", callback_data=f"publish_now:{post_id}"),
                InlineKeyboardButton("Одобрить (в очередь)", callback_data=f"approve:{post_id}"),
            ],
            [
                InlineKeyboardButton("Отклонить", callback_data=f"reject:{post_id}"),
                InlineKeyboardButton("Ещё пост", callback_data="generate_menu"),
            ],
        ]
        markup = InlineKeyboardMarkup(keyboard)

        await _safe_delete(query.message)

        if image_path and image_path.exists():
            with open(image_path, "rb") as photo_file:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=markup,
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=_format_post_preview(post),
                parse_mode="HTML",
                reply_markup=markup,
            )

    async def _cb_generate_new(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Generate a new post via Claude CLI with auto-image."""
        query = update.callback_query
        await query.answer("Генерирую... Подожди минуту.")

        if not self._is_admin(update):
            return

        await _safe_delete(query.message)
        status_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Генерирую пост через Claude... Это займёт около минуты.",
        )

        try:
            import random

            from src.content.generator import generate_post
            from src.content.prompts import ALL_POST_TYPES

            queue = ContentQueue(self.db_path)
            recent = await queue.get_recent_published(limit=5)
            recent_texts = [p["text"] for p in recent]

            recent_types = [p.get("type", "") for p in recent[:3]]
            available = [t for t in ALL_POST_TYPES if t not in recent_types] or ALL_POST_TYPES
            post_type = random.choice(available)

            post = await generate_post(
                post_type=post_type,
                recent_posts=recent_texts,
                claude_cli_path=self.claude_cli_path,
                data_dir=self.data_dir,
            )
            post_id = await queue.add_post(
                post_type=post.post_type,
                title=post.title,
                text=post.text,
                cta=post.cta,
            )

            # Auto-generate image
            db_post = await queue.get_post(post_id)
            image_path = await self._get_or_generate_image(db_post, queue)

            caption = _format_post_caption(db_post)

            keyboard = [
                [
                    InlineKeyboardButton("Опубликовать сейчас", callback_data=f"publish_now:{post_id}"),
                    InlineKeyboardButton("Одобрить (в очередь)", callback_data=f"approve:{post_id}"),
                ],
                [
                    InlineKeyboardButton("Отклонить", callback_data=f"reject:{post_id}"),
                    InlineKeyboardButton("Ещё пост", callback_data="generate_menu"),
                ],
            ]
            markup = InlineKeyboardMarkup(keyboard)

            await _safe_delete(status_msg)

            if image_path and image_path.exists():
                with open(image_path, "rb") as photo_file:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo_file,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=markup,
                    )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=_format_post_preview(db_post),
                    parse_mode="HTML",
                    reply_markup=markup,
                )

        except Exception as exc:
            logger.error("admin_bot.generate_failed", error=str(exc))
            await _safe_delete(status_msg)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Ошибка генерации: {exc}",
            )

    async def _cb_publish_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Approve and immediately publish a specific post."""
        query = update.callback_query
        await query.answer("Публикую...")

        if not self._is_admin(update):
            return

        post_id = int(query.data.split(":")[1])
        queue = ContentQueue(self.db_path)

        # Approve first
        await queue.approve(post_id)

        try:
            from src.publisher.channel import ChannelPublisher

            publisher = ChannelPublisher(
                bot_token=self.channel_bot_token,
                channel_id=self.channel_id,
                data_dir=Path(self.data_dir),
                claude_cli_path=self.claude_cli_path,
            )

            # Publish THIS specific post, not the oldest approved
            post = await queue.get_post(post_id)
            result = await publisher.publish_post(post, queue) if post else None

            await _safe_delete(query.message)

            if result:
                keyboard = [[InlineKeyboardButton("Ещё пост", callback_data="generate_menu")]]
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Пост #{post_id} опубликован в канал.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Ошибка: пост не найден в очереди.",
                )

        except Exception as exc:
            logger.error("admin_bot.publish_now_failed", error=str(exc))
            await _safe_delete(query.message)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Ошибка публикации: {exc}",
            )

    # ------------------------------------------------------------------
    # Prewritten posts helpers
    # ------------------------------------------------------------------

    def _get_prewritten_path(self) -> Path:
        return Path(self.data_dir) / "prewritten_posts.json"

    def _get_loaded_tracker_path(self) -> Path:
        return Path(self.data_dir) / "prewritten_loaded.json"

    def _get_loaded_nums(self) -> set[int]:
        """Get set of already-loaded post numbers."""
        tracker = self._get_loaded_tracker_path()
        if tracker.exists():
            try:
                return set(json.loads(tracker.read_text()))
            except (json.JSONDecodeError, TypeError):
                pass
        return set()

    def _mark_loaded(self, num: int) -> None:
        """Mark a prewritten post number as loaded."""
        loaded = self._get_loaded_nums()
        loaded.add(num)
        self._get_loaded_tracker_path().write_text(json.dumps(sorted(loaded)))

    def _count_available_prewritten(self) -> int:
        """Count prewritten posts not yet loaded."""
        path = self._get_prewritten_path()
        if not path.exists():
            return 0
        try:
            posts = json.loads(path.read_text())
            loaded = self._get_loaded_nums()
            return sum(1 for p in posts if p.get("num") not in loaded)
        except (json.JSONDecodeError, TypeError):
            return 0

    def _get_next_prewritten(self) -> Optional[dict]:
        """Get the next unloaded prewritten post."""
        path = self._get_prewritten_path()
        if not path.exists():
            return None
        try:
            posts = json.loads(path.read_text())
            loaded = self._get_loaded_nums()
            for post in posts:
                if post.get("num") not in loaded:
                    self._mark_loaded(post["num"])
                    return post
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _send_pending_list(self, bot, chat_id: int) -> None:
        """Send list of pending posts with preview buttons."""
        queue = ContentQueue(self.db_path)
        pending = await queue.get_pending()

        if not pending:
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "Нет постов на проверке.\n"
                    "Используй /generate для генерации новых."
                ),
                parse_mode="HTML",
            )
            return

        lines = [f"<b>На проверке: {len(pending)}</b>\n"]
        keyboard = []

        for post in pending[:10]:
            title = post.get("title") or post.get("text", "")[:50]
            post_type = post.get("type", "?")
            lines.append(f"#{post['id']} [{post_type}] {html.escape(title[:60])}")
            keyboard.append([
                InlineKeyboardButton(
                    f"#{post['id']}: {title[:30]}",
                    callback_data=f"preview:{post['id']}",
                )
            ])

        if len(pending) > 10:
            lines.append(f"\n... и ещё {len(pending) - 10}")

        await bot.send_message(
            chat_id=chat_id,
            text="\n".join(lines),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _get_or_generate_image(
        self, post: dict, queue: ContentQueue
    ) -> Optional[Path]:
        """Return existing image or generate one for this post."""
        # Check existing path
        if post.get("image_path"):
            existing = Path(post["image_path"])
            if existing.exists():
                return existing

        # Generate new image
        try:
            from src.publisher.image_gen import extract_accent_number, generate_post_image

            title = post.get("title", "")
            text = post.get("text", "")
            post_type = post.get("type", "")
            body = text[:120].split(".")[0] if text else None
            accent = extract_accent_number(title + " " + text)

            output = self._images_dir / f"post_{post['id']}.png"

            generate_post_image(
                headline=title or text[:80],
                post_type=post_type,
                body_text=body if not accent else None,
                accent_number=accent,
                output_path=output,
            )

            await queue.update_image_path(post["id"], str(output))
            return output

        except Exception as exc:
            logger.warning("admin_bot.image_gen_failed", post_id=post["id"], error=str(exc))
            return None

    async def send_notification(self, text: str, keyboard: list[list[InlineKeyboardButton]] | None = None) -> None:
        """Send a notification to admin (called from scheduler)."""
        if not self._app or not self._app.bot:
            logger.warning("admin_bot.not_running_for_notification")
            return

        markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await self._app.bot.send_message(
            chat_id=self.admin_chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=markup,
        )


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


async def _safe_delete(message) -> None:
    """Delete a message, ignoring errors (e.g. already deleted, too old)."""
    try:
        await message.delete()
    except Exception:
        pass


def _format_post_caption(post: dict) -> str:
    """Format post for Telegram photo caption (max 1024 chars)."""
    parts = [f"<b>Пост #{post['id']}</b>  [{post.get('type', '?')}]"]

    if post.get("title"):
        parts.append(f"\n<b>{html.escape(post['title'])}</b>")

    if post.get("text"):
        text = html.escape(post["text"])
        if len(text) > 750:
            text = text[:750] + "..."
        parts.append(f"\n{text}")

    if post.get("cta"):
        parts.append(f"\n{html.escape(post['cta'])}")

    result = "\n".join(parts)
    if len(result) > _MAX_CAPTION:
        result = result[: _MAX_CAPTION - 3] + "..."
    return result


def _format_post_preview(post: dict) -> str:
    """Format a post for text-only admin preview (fallback)."""
    parts = [f"<b>Пост #{post['id']}</b>"]
    parts.append(f"Тип: {post.get('type', '?')}")
    parts.append(f"Статус: {post.get('status', '?')}")
    parts.append(f"Создан: {post.get('created_at', '?')[:16]}")
    parts.append("")
    parts.append("--- Предпросмотр ---")
    parts.append("")

    if post.get("title"):
        parts.append(f"<b>{html.escape(post['title'])}</b>")
        parts.append("")

    if post.get("text"):
        text = post["text"]
        if len(text) > 3500:
            text = text[:3500] + "..."
        parts.append(html.escape(text))

    if post.get("cta"):
        parts.append("")
        parts.append(html.escape(post["cta"]))

    return "\n".join(parts)
