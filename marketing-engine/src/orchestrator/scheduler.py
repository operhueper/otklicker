"""APScheduler setup for automated marketing tasks.

Jobs:
- generate_weekly_content: Sunday 10:00 MSK -- generate 3 posts for the week
- publish_post: Tue/Thu/Sat 10:00 MSK -- publish next approved post
- collect_metrics: Daily 23:00 MSK -- collect channel metrics
- weekly_report: Monday 09:00 MSK -- send weekly report to admin
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = structlog.get_logger(__name__)

# Moscow timezone offset is UTC+3
_MSK_TZ = "Europe/Moscow"


class MarketingScheduler:
    """Wraps APScheduler with marketing job definitions."""

    def __init__(
        self,
        bot_token: str,
        channel_id: str,
        admin_chat_id: int | str,
        db_path: str,
        data_dir: str,
        claude_cli_path: str = "claude",
        admin_bot: object | None = None,
    ) -> None:
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.admin_chat_id = admin_chat_id
        self.db_path = db_path
        self.data_dir = data_dir
        self.claude_cli_path = claude_cli_path
        self.admin_bot = admin_bot  # AdminBot instance for notifications with buttons

        self.scheduler = AsyncIOScheduler(timezone=_MSK_TZ)
        # Set externally after UserBot is created (same pattern as admin_bot)
        self.userbot = None
        self._register_jobs()

    def _register_jobs(self) -> None:
        """Register all scheduled jobs."""
        # Generate 1 post the evening before each publish day (Mon/Wed/Fri 20:00 MSK)
        self.scheduler.add_job(
            self.job_generate_weekly_content,
            CronTrigger(day_of_week="mon,wed,fri", hour=20, minute=0, timezone=_MSK_TZ),
            id="generate_content",
            name="Generate one post",
            replace_existing=True,
        )

        # Publish post on Tue, Thu, Sat at 10:00 MSK
        self.scheduler.add_job(
            self.job_publish_post,
            CronTrigger(day_of_week="tue,thu,sat", hour=10, minute=0, timezone=_MSK_TZ),
            id="publish_post",
            name="Publish approved post",
            replace_existing=True,
        )

        # Collect metrics daily at 23:00 MSK
        self.scheduler.add_job(
            self.job_collect_metrics,
            CronTrigger(hour=23, minute=0, timezone=_MSK_TZ),
            id="collect_metrics",
            name="Collect daily metrics",
            replace_existing=True,
        )

        # Weekly report every Monday at 09:00 MSK
        self.scheduler.add_job(
            self.job_weekly_report,
            CronTrigger(day_of_week="mon", hour=9, minute=0, timezone=_MSK_TZ),
            id="weekly_report",
            name="Send weekly report to admin",
            replace_existing=True,
        )

        # Learn from chats every 12 hours (6:00 and 18:00 MSK)
        self.scheduler.add_job(
            self.job_learn_from_chats,
            CronTrigger(hour="6,18", minute=0, timezone=_MSK_TZ),
            id="learn_from_chats",
            name="Read chats and update brand voice context",
            replace_existing=True,
        )

        # Daily health report at 22:00 MSK
        self.scheduler.add_job(
            self.job_daily_health_report,
            CronTrigger(hour=22, minute=0, timezone=_MSK_TZ),
            id="daily_health",
            name="Daily health report to admin",
            replace_existing=True,
        )

        # Custdev daily report at 21:00 MSK
        self.scheduler.add_job(
            self.job_custdev_report,
            CronTrigger(hour=21, minute=0, timezone=_MSK_TZ),
            id="custdev_report",
            name="Custdev daily report to admin",
            replace_existing=True,
        )

        # Custdev probes: send 1 research question per day at 15:00 MSK
        self.scheduler.add_job(
            self.job_send_custdev_probes,
            CronTrigger(hour=15, minute=0, timezone=_MSK_TZ),
            id="custdev_probes",
            name="Send custdev probe to seller chat",
            replace_existing=True,
        )

        logger.info("scheduler.jobs_registered", job_count=8)

    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("scheduler.started")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown(wait=False)
        logger.info("scheduler.stopped")

    # ------------------------------------------------------------------
    # Job implementations
    # ------------------------------------------------------------------

    async def job_generate_weekly_content(self) -> None:
        """Generate 1 post and add to queue."""
        logger.info("scheduler.job.generate_content.start")

        try:
            from src.content.generator import generate_post
            from src.content.news_fetcher import fetch_marketplace_news
            from src.content.prompts import ALL_POST_TYPES
            from src.content.queue import ContentQueue

            queue = ContentQueue(self.db_path)

            # Fetch recent news for context
            news_items = await fetch_marketplace_news(max_items=5)
            news_context = _format_news_for_prompt(news_items)

            # Get recent posts to avoid repetition
            recent = await queue.get_recent_published(limit=5)
            recent_texts = [p["text"] for p in recent]

            # Pick post type that wasn't used recently
            post_type = _pick_post_type(recent)

            try:
                post = await generate_post(
                    post_type=post_type,
                    recent_posts=recent_texts,
                    news_context=news_context,
                    claude_cli_path=self.claude_cli_path,
                    data_dir=self.data_dir,
                )

                post_id = await queue.add_post(
                    post_type=post.post_type,
                    title=post.title,
                    text=post.text,
                    cta=post.cta,
                )

                logger.info(
                    "scheduler.job.post_generated",
                    post_id=post_id,
                    post_type=post_type,
                )

                await self._notify_admin(
                    f"Новый пост сгенерирован\n\n"
                    f"ID: {post_id}\n"
                    f"Тип: {post_type}\n"
                    f"Заголовок: {post.title[:60]}",
                    with_pending_button=True,
                )

            except Exception as exc:
                logger.error(
                    "scheduler.job.post_generation_failed",
                    post_type=post_type,
                    error=str(exc),
                )
                await self._notify_admin(f"Ошибка генерации поста ({post_type}): {exc}")

        except Exception as exc:
            logger.error(
                "scheduler.job.generate_content.failed",
                error=str(exc),
            )
            await self._notify_admin(f"ОШИБКА генерации контента: {exc}")

    async def job_publish_post(self) -> None:
        """Publish the next approved post to the channel."""
        logger.info("scheduler.job.publish_post.start")

        try:
            from pathlib import Path

            from src.content.queue import ContentQueue
            from src.publisher.channel import ChannelPublisher

            queue = ContentQueue(self.db_path)
            publisher = ChannelPublisher(
                bot_token=self.bot_token,
                channel_id=self.channel_id,
                data_dir=Path(self.data_dir),
                claude_cli_path=self.claude_cli_path,
            )

            result = await publisher.publish_next(queue)

            if result:
                logger.info(
                    "scheduler.job.post_published",
                    post_id=result["id"],
                )
                await self._notify_admin(
                    f"Пост опубликован\n\nID: {result['id']}\n"
                    f"Тип: {result.get('type')}\n"
                    f"Заголовок: {result.get('title', '')[:80]}"
                )
            else:
                logger.warning("scheduler.job.no_approved_posts")
                await self._notify_admin(
                    "Нет одобренных постов для публикации.\n"
                    "Проверь очередь и одобри посты.",
                    with_pending_button=True,
                )

        except Exception as exc:
            logger.error(
                "scheduler.job.publish_post.failed",
                error=str(exc),
            )
            await self._notify_admin(f"ОШИБКА публикации поста: {exc}")

    async def job_collect_metrics(self) -> None:
        """Collect daily channel metrics and store in DB."""
        logger.info("scheduler.job.collect_metrics.start")

        try:
            from src.utils.telegram import get_channel_stats

            stats = await get_channel_stats(self.bot_token, self.channel_id)
            today = datetime.now(timezone.utc).date().isoformat()
            now = datetime.now(timezone.utc).isoformat()

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO metrics
                        (date, channel_subs, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (today, stats.get("member_count", 0), now),
                )
                await db.commit()

            logger.info(
                "scheduler.job.metrics_collected",
                date=today,
                subs=stats.get("member_count", 0),
            )

        except Exception as exc:
            logger.error(
                "scheduler.job.collect_metrics.failed",
                error=str(exc),
            )

    async def job_weekly_report(self) -> None:
        """Generate and send weekly performance report to admin."""
        logger.info("scheduler.job.weekly_report.start")

        try:
            report = await _build_weekly_report(self.db_path)
            await self._notify_admin(report)
            logger.info("scheduler.job.weekly_report.sent")

        except Exception as exc:
            logger.error(
                "scheduler.job.weekly_report.failed",
                error=str(exc),
            )
            await self._notify_admin(f"ОШИБКА генерации отчёта: {exc}")

    async def job_learn_from_chats(self) -> None:
        """Read chats and update brand voice context."""
        logger.info("scheduler.job.learn.start")

        try:
            from telethon import TelegramClient

            from src.content.learner import learn_from_chats

            # Connect userbot temporarily for reading
            client = TelegramClient(
                str(Path(self.data_dir) / "userbot_session"),
                int(self._get_env("TELEGRAM_API_ID", "0")),
                self._get_env("TELEGRAM_API_HASH", ""),
            )
            await client.connect()

            if not await client.is_user_authorized():
                logger.warning("scheduler.job.learn.not_authorized")
                await client.disconnect()
                return

            # Get chat IDs + channel IDs + resolve usernames
            chat_ids = self._load_chat_ids()
            channel_ids = self._load_channel_ids()
            channel_usernames = self._load_channel_usernames()

            # Resolve usernames to IDs via Telethon
            for username in channel_usernames:
                try:
                    entity = await client.get_entity(username)
                    channel_ids.append(entity.id)
                    logger.info("scheduler.resolved_channel", username=username, id=entity.id)
                except Exception as exc:
                    logger.warning("scheduler.resolve_failed", username=username, error=str(exc))

            all_ids = chat_ids + channel_ids
            if not all_ids:
                # Fallback: read from all joined supergroups
                all_ids = await self._get_joined_chat_ids(client)

            if all_ids:
                context = await learn_from_chats(
                    client=client,
                    chat_ids=all_ids,
                    data_dir=self.data_dir,
                    claude_cli_path=self.claude_cli_path,
                )
                pains = context.get("top_pains", [])
                mood = context.get("mood", "?")
                logger.info("scheduler.job.learn.done", pains=len(pains), mood=mood)
            else:
                logger.warning("scheduler.job.learn.no_chats")

            await client.disconnect()

        except Exception as exc:
            logger.error("scheduler.job.learn.failed", error=str(exc))

    async def job_custdev_report(self) -> None:
        """Send evening custdev summary to admin at 21:00 MSK."""
        logger.info("scheduler.job.custdev_report.start")

        try:
            report = await _build_custdev_report(self.db_path)
            if report:
                await self._notify_admin(report)
                logger.info("scheduler.job.custdev_report.sent")
            else:
                logger.info("scheduler.job.custdev_report.no_data")
        except Exception as exc:
            logger.error("scheduler.job.custdev_report.failed", error=str(exc))

    async def job_daily_health_report(self) -> None:
        """Send daily health report with issues to admin at 22:00 MSK."""
        logger.info("scheduler.job.daily_health.start")

        try:
            report = await _build_daily_health_report(self.db_path)
            if report:
                await self._notify_admin(report)
                logger.info("scheduler.job.daily_health.sent")
            else:
                logger.info("scheduler.job.daily_health.no_issues")
        except Exception as exc:
            logger.error("scheduler.job.daily_health.failed", error=str(exc))

    async def job_send_custdev_probes(self) -> None:
        """Send 1 custdev research question to a seller chat at 15:00 MSK.

        Picks a chat not probed in the last 3 days, rotates topics to cover
        all product-validation angles (repeat sales, contacts, inserts, etc.).
        """
        logger.info("scheduler.job.custdev_probes.start")

        if not self.userbot:
            logger.warning("scheduler.job.custdev_probes.no_userbot")
            return

        try:
            import random

            chat_ids = self._load_chat_ids()
            if not chat_ids:
                logger.warning("scheduler.job.custdev_probes.no_chats")
                return

            # Find chats not probed in last 3 days
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """SELECT DISTINCT chat_id FROM custdev_probes
                       WHERE date(sent_at) >= date('now', '-3 days')"""
                )
                recently_probed = {row[0] for row in await cursor.fetchall()}

            available = [cid for cid in chat_ids if cid not in recently_probed]

            if not available:
                logger.info("scheduler.job.custdev_probes.all_chats_on_cooldown")
                await self._notify_admin("Кастдев: все чаты на кулдауне (3 дня). Пропуск.")
                return

            chat_id = random.choice(available)
            # Telethon needs -100 prefix for supergroups
            raw_chat_id = int(f"-100{chat_id}") if chat_id > 0 else chat_id

            sent = await self.userbot.send_custdev_probe(
                chat_id=chat_id,
                raw_chat_id=raw_chat_id,
            )

            if sent:
                logger.info("scheduler.job.custdev_probes.done", chat_id=chat_id)
            else:
                logger.info("scheduler.job.custdev_probes.skipped", chat_id=chat_id)

        except Exception as exc:
            logger.error("scheduler.job.custdev_probes.failed", error=str(exc))
            await self._notify_admin(f"ОШИБКА кастдев-пробы: {exc}")

    def _load_chat_ids(self) -> list[int]:
        """Load chat IDs from data/monitored_chats.json."""
        import json
        path = Path(self.data_dir) / "monitored_chats.json"
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                return [int(cid) for cid in data.get("chat_ids", [])]
            except Exception:
                pass
        return []

    def _load_channel_ids(self) -> list[int]:
        """Load channel IDs for learner from data/monitored_chats.json."""
        import json
        path = Path(self.data_dir) / "monitored_chats.json"
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                return [int(cid) for cid in data.get("channel_ids", [])]
            except Exception:
                pass
        return []

    def _load_channel_usernames(self) -> list[str]:
        """Load channel usernames for learner from data/monitored_chats.json."""
        import json
        path = Path(self.data_dir) / "monitored_chats.json"
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                return data.get("channel_usernames", [])
            except Exception:
                pass
        return []

    async def _get_joined_chat_ids(self, client) -> list[int]:
        """Get IDs of all joined supergroups (discussion chats)."""
        ids = []
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if hasattr(entity, "megagroup") and entity.megagroup:
                ids.append(entity.id)
        return ids

    @staticmethod
    def _get_env(key: str, default: str = "") -> str:
        import os
        return os.getenv(key) or default

    async def _notify_admin(self, text: str, with_pending_button: bool = False) -> None:
        """Send notification to admin chat via admin bot (with optional buttons)."""
        try:
            keyboard = None
            if with_pending_button and self.admin_bot:
                from telegram import InlineKeyboardButton
                keyboard = [[InlineKeyboardButton("Посмотреть очередь", callback_data="pending_list")]]

            if self.admin_bot:
                await self.admin_bot.send_notification(text, keyboard=keyboard)
            else:
                from src.utils.telegram import send_to_admin
                await send_to_admin(
                    bot_token=self.bot_token,
                    admin_id=self.admin_chat_id,
                    text=text,
                )
        except Exception as exc:
            logger.error("scheduler.admin_notify_failed", error=str(exc))


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------


async def _build_custdev_report(db_path: str) -> str | None:
    """Build custdev daily report with questions asked and responses received."""
    import json

    async with aiosqlite.connect(db_path) as db:
        # Today's probes
        cursor = await db.execute(
            """SELECT id, chat_name, question_topic, question_text,
                      responses_count, responses_json
               FROM custdev_probes
               WHERE date(sent_at) = date('now')
               ORDER BY sent_at""",
        )
        probes = await cursor.fetchall()

        if not probes:
            return None

        # All-time stats
        cursor = await db.execute(
            "SELECT COUNT(*), SUM(responses_count) FROM custdev_probes"
        )
        row = await cursor.fetchone()
        total_probes = row[0] if row else 0
        total_responses = row[1] if row else 0

    lines = ["<b>Кастдев-отчёт за сегодня</b>\n"]

    for probe_id, chat_name, topic, question, resp_count, resp_json in probes:
        lines.append(f"<b>#{probe_id}</b> [{topic}] в {chat_name}")
        lines.append(f"<i>{question[:200]}</i>")

        if resp_count and resp_count > 0:
            responses = json.loads(resp_json) if resp_json else []
            lines.append(f"Ответов: {resp_count}")
            for r in responses[:5]:
                author = r.get("author", "?")
                text = r.get("text", "")[:150]
                lines.append(f"  {author}: {text}")
        else:
            lines.append("Ответов пока нет")

        lines.append("")

    lines.append(f"<b>Итого за всё время:</b> {total_probes} вопросов, {total_responses or 0} ответов")

    return "\n".join(lines)


async def _build_daily_health_report(db_path: str) -> str | None:
    """Build daily health report. Returns None if no issues found."""
    issues: list[str] = []

    async with aiosqlite.connect(db_path) as db:
        # Chat activity stats
        cursor = await db.execute(
            """SELECT chat_id, COUNT(*) as cnt
               FROM chat_opportunities
               WHERE status = 'sent' AND date(sent_at) = date('now')
               GROUP BY chat_id ORDER BY cnt DESC""",
        )
        chat_stats = await cursor.fetchall()
        total_sent = sum(r[1] for r in chat_stats)

        # Chats near or at limit (70)
        for chat_id, cnt in chat_stats:
            if cnt >= 60:
                issues.append(f"Чат {chat_id}: {cnt}/70 сообщений (лимит скоро)")

        # Skipped due to low confidence
        cursor = await db.execute(
            """SELECT COUNT(*) FROM chat_opportunities
               WHERE date(detected_at) = date('now')
               AND status IN ('skipped', 'pending')
               AND confidence < 0.5""",
        )
        row = await cursor.fetchone()
        low_conf = row[0] if row else 0
        if low_conf > 10:
            issues.append(f"Пропущено {low_conf} сообщений (низкая уверенность)")

        # Pending (not approved) messages
        cursor = await db.execute(
            """SELECT COUNT(*) FROM chat_opportunities
               WHERE status = 'pending'
               AND date(detected_at) = date('now')""",
        )
        row = await cursor.fetchone()
        pending = row[0] if row else 0
        if pending > 5:
            issues.append(f"{pending} сообщений ждут одобрения")

    # Build report
    header = f"<b>Дневной отчёт Артёма</b>\n\nОтправлено сегодня: {total_sent}"
    if chat_stats:
        top = ", ".join(f"{cid}({cnt})" for cid, cnt in chat_stats[:3])
        header += f"\nТоп чаты: {top}"

    if issues:
        body = "\n\n<b>Проблемы:</b>\n" + "\n".join(f"-- {i}" for i in issues)
        return header + body

    return header + "\n\nПроблем нет"


async def _build_weekly_report(db_path: str) -> str:
    """Build a weekly performance report string."""
    async with aiosqlite.connect(db_path) as db:
        # Posts published this week
        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM posts
            WHERE status = 'published'
            AND date(published_at) >= date('now', '-7 days')
            """
        )
        row = await cursor.fetchone()
        posts_published = row[0] if row else 0

        # Responses sent this week
        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM chat_opportunities
            WHERE status = 'sent'
            AND date(sent_at) >= date('now', '-7 days')
            """
        )
        row = await cursor.fetchone()
        responses_sent = row[0] if row else 0

        # Pending posts
        cursor = await db.execute(
            "SELECT COUNT(*) FROM posts WHERE status = 'pending_review'"
        )
        row = await cursor.fetchone()
        pending = row[0] if row else 0

        # Latest subscriber count
        cursor = await db.execute(
            "SELECT channel_subs FROM metrics ORDER BY date DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        subs = row[0] if row else 0

    now = datetime.now(timezone.utc)
    week_str = f"{now.strftime('%d.%m')} отчёт"

    return (
        f"Еженедельный отчёт ({week_str})\n\n"
        f"Подписчики канала: {subs:,}\n"
        f"Постов опубликовано (7 дней): {posts_published}\n"
        f"Ответов в чатах (7 дней): {responses_sent}\n"
        f"Постов на проверке: {pending}\n\n"
        f"Используй /pending для проверки очереди"
    )


def _pick_post_type(recent_posts: list[dict]) -> str:
    """Pick a post type that wasn't used in the last few posts."""
    import random

    from src.content.prompts import ALL_POST_TYPES

    recent_types = [p.get("type", "") for p in recent_posts[:3]]
    available = [t for t in ALL_POST_TYPES if t not in recent_types]

    if not available:
        available = ALL_POST_TYPES

    return random.choice(available)


def _format_news_for_prompt(news_items: list) -> Optional[str]:
    """Format news items for inclusion in content generation prompt."""
    if not news_items:
        return None

    lines = []
    for item in news_items[:3]:
        lines.append(f"- {item.title}: {item.summary[:100]}")

    return "\n".join(lines)
