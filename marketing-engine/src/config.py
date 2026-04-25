"""Configuration loader for marketing-engine.

Reads settings from environment variables / .env file.
All sensitive values must be in .env, never hardcoded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (marketing-engine directory)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


@dataclass
class Config:
    # Telegram Bot API (для публикации в канал)
    telegram_bot_token: str = field(default_factory=lambda: os.environ["TELEGRAM_BOT_TOKEN"])

    # Admin bot (интерактивное управление очередью)
    admin_bot_token: str = field(default_factory=lambda: os.environ["ADMIN_BOT_TOKEN"])

    # Telethon userbot (для мониторинга чатов, опционально)
    telegram_api_id: int = field(
        default_factory=lambda: int(os.getenv("TELEGRAM_API_ID") or "0")
    )
    telegram_api_hash: str = field(default_factory=lambda: os.getenv("TELEGRAM_API_HASH") or "")
    telegram_phone: str = field(default_factory=lambda: os.getenv("TELEGRAM_PHONE") or "")

    # Channel / admin
    channel_id: str = field(
        default_factory=lambda: os.getenv("CHANNEL_ID", "@seller_base")
    )
    admin_chat_id: int = field(default_factory=lambda: int(os.environ["ADMIN_CHAT_ID"]))

    # Claude CLI
    claude_cli_path: str = field(
        default_factory=lambda: os.getenv("CLAUDE_CLI_PATH", "claude")
    )

    # Paths
    data_dir: Path = field(
        default_factory=lambda: Path(os.getenv("DATA_DIR", "./data")).resolve()
    )
    db_path: Path = field(
        default_factory=lambda: Path(os.getenv("DB_PATH", "./data/marketing.db")).resolve()
    )

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """Load and validate configuration from environment."""
    return Config()
