"""Structured logging setup with optional Telegram alerts for critical errors.

Uses structlog for consistent JSON/console output.
Critical-level log entries are forwarded to the admin Telegram chat.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Optional

import structlog

_bot_token: Optional[str] = None
_admin_chat_id: Optional[str] = None
_log_file: Optional[Path] = None


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    bot_token: Optional[str] = None,
    admin_chat_id: Optional[str] = None,
) -> None:
    """Configure structlog and standard logging.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file.
        bot_token: Telegram bot token for critical alert forwarding.
        admin_chat_id: Admin chat ID to receive critical alerts.
    """
    global _bot_token, _admin_chat_id, _log_file

    _bot_token = bot_token
    _admin_chat_id = admin_chat_id
    _log_file = log_file

    level = getattr(logging, log_level.upper(), logging.INFO)

    # Standard library logging handlers
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        handlers=handlers,
        format="%(message)s",
    )

    # Structlog processors chain
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer() if sys.stdout.isatty() else structlog.processors.JSONRenderer(),
        ],
    )

    for handler in handlers:
        handler.setFormatter(formatter)

    # Install critical alert hook
    _install_critical_hook()


def _install_critical_hook() -> None:
    """Patch structlog to forward CRITICAL events to Telegram."""

    original_critical = structlog.stdlib.BoundLogger.critical

    async def _send_alert(message: str) -> None:
        if not _bot_token or not _admin_chat_id:
            return
        try:
            from src.utils.telegram import send_to_admin  # lazy import

            await send_to_admin(
                _bot_token,
                _admin_chat_id,
                f"CRITICAL ERROR\n\n{message[:3000]}",
            )
        except Exception:
            pass  # Never let alert failure kill the app

    def patched_critical(self: Any, event: str, *args: Any, **kwargs: Any) -> Any:
        result = original_critical(self, event, *args, **kwargs)
        # Fire-and-forget in running event loop if available
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_send_alert(event))
        except RuntimeError:
            pass  # No running loop; skip Telegram alert
        return result

    structlog.stdlib.BoundLogger.critical = patched_critical  # type: ignore[method-assign]


def get_logger(name: str) -> Any:
    """Get a structlog logger by name."""
    return structlog.get_logger(name)
