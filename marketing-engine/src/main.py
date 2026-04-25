"""Entry point for the marketing engine.

Starts:
1. Database initialization
2. Structured logging
3. Admin bot (polling for commands/callbacks)
4. APScheduler (content generation + publishing jobs)
5. Telethon userbot (if Telegram API credentials configured)

Usage:
    cd marketing-engine
    python -m src.main
"""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


async def main() -> None:
    """Main async entry point."""
    # Load configuration
    try:
        from src.config import load_config
        config = load_config()
    except (KeyError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        print("Copy .env.example to .env and fill in the values.", file=sys.stderr)
        sys.exit(1)

    # Configure logging
    from src.utils.logger import configure_logging
    configure_logging(
        log_level="INFO",
        log_file=config.data_dir / "logs" / "marketing.log",
        bot_token=config.admin_bot_token,
        admin_chat_id=config.admin_chat_id,
    )

    logger.info("marketing_engine.starting")

    # Initialize database
    from src.db.models import init_db
    await init_db(str(config.db_path))

    # Build admin bot
    from src.admin_bot import AdminBot
    admin_bot = AdminBot(
        admin_bot_token=config.admin_bot_token,
        channel_bot_token=config.telegram_bot_token,
        channel_id=config.channel_id,
        admin_chat_id=config.admin_chat_id,
        db_path=str(config.db_path),
        data_dir=str(config.data_dir),
        claude_cli_path=config.claude_cli_path,
    )
    app = admin_bot.build()

    # Start scheduler (passes admin_bot for notifications with buttons)
    from src.orchestrator.scheduler import MarketingScheduler
    scheduler = MarketingScheduler(
        bot_token=config.telegram_bot_token,
        channel_id=config.channel_id,
        admin_chat_id=config.admin_chat_id,
        db_path=str(config.db_path),
        data_dir=str(config.data_dir),
        claude_cli_path=config.claude_cli_path,
        admin_bot=admin_bot,
    )
    scheduler.start()

    # Start userbot (optional -- only if Telethon credentials are set)
    userbot = None
    userbot_task = None

    try:
        userbot = _init_userbot(config)
        if userbot:
            # Wire userbot <-> admin_bot for approval flow
            userbot.admin_bot = admin_bot
            admin_bot.userbot = userbot
            userbot_task = asyncio.create_task(userbot.start())
            logger.info("marketing_engine.userbot_started")
    except Exception as exc:
        logger.warning(
            "marketing_engine.userbot_skipped",
            reason=str(exc),
        )

    # Initialize and start the admin bot polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    logger.info("marketing_engine.running", components=["admin_bot", "scheduler"])

    # Set up graceful shutdown
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_signal() -> None:
        logger.info("marketing_engine.shutdown_requested")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal)

    # Wait until stopped
    await stop_event.wait()

    logger.info("marketing_engine.stopping")

    # Graceful shutdown
    await app.updater.stop()
    await app.stop()
    await app.shutdown()

    scheduler.stop()

    if userbot:
        await userbot.stop()

    if userbot_task:
        userbot_task.cancel()
        try:
            await userbot_task
        except (asyncio.CancelledError, Exception):
            pass

    logger.info("marketing_engine.stopped")


def _init_userbot(config) -> object | None:
    """Try to initialize the Telethon userbot.

    Returns None if credentials are not configured or Telethon unavailable.
    """
    if not config.telegram_api_id or not config.telegram_api_hash or not config.telegram_phone:
        logger.info("marketing_engine.userbot_disabled", reason="Missing Telethon credentials")
        return None

    try:
        from src.chat_monitor.userbot import UserBot

        # Load monitored chat IDs from settings
        monitored_chats = _load_monitored_chats(config.data_dir)

        return UserBot(
            api_id=config.telegram_api_id,
            api_hash=config.telegram_api_hash,
            phone=config.telegram_phone,
            db_path=str(config.db_path),
            bot_token=config.telegram_bot_token,
            admin_chat_id=config.admin_chat_id,
            monitored_chat_ids=monitored_chats,
            session_path=config.data_dir / "userbot_session",
            claude_cli_path=config.claude_cli_path,
        )

    except Exception as exc:
        logger.warning("marketing_engine.userbot_init_failed", error=str(exc))
        return None


def _load_monitored_chats(data_dir: Path) -> list[int]:
    """Load monitored chat IDs from data/monitored_chats.json."""
    import json

    chats_file = data_dir / "monitored_chats.json"
    if not chats_file.exists():
        logger.info(
            "marketing_engine.no_monitored_chats",
            hint="Create data/monitored_chats.json with a list of chat IDs",
        )
        return []

    try:
        with open(chats_file) as f:
            data = json.load(f)
        chat_ids = [int(cid) for cid in data.get("chat_ids", [])]
        logger.info("marketing_engine.monitored_chats_loaded", count=len(chat_ids))
        return chat_ids
    except Exception as exc:
        logger.error("marketing_engine.monitored_chats_load_failed", error=str(exc))
        return []


if __name__ == "__main__":
    asyncio.run(main())
