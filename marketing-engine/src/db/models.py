"""Database schema definitions and initialization.

Tables:
- posts: content queue
- chat_opportunities: detected chat engagement opportunities
- metrics: daily channel/campaign metrics
- settings: key-value store for app config
"""

from __future__ import annotations

import aiosqlite
import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# DDL statements
# ---------------------------------------------------------------------------

_CREATE_POSTS = """
CREATE TABLE IF NOT EXISTS posts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    type                TEXT NOT NULL,
    title               TEXT NOT NULL DEFAULT '',
    text                TEXT NOT NULL,
    cta                 TEXT NOT NULL DEFAULT '',
    image_path          TEXT,
    status              TEXT NOT NULL DEFAULT 'draft',
    rejection_reason    TEXT,
    telegram_message_id INTEGER,
    created_at          TEXT NOT NULL,
    published_at        TEXT,
    views               INTEGER DEFAULT 0,
    forwards            INTEGER DEFAULT 0
);
"""

_CREATE_CHAT_OPPORTUNITIES = """
CREATE TABLE IF NOT EXISTS chat_opportunities (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER NOT NULL,
    chat_name       TEXT NOT NULL DEFAULT '',
    message_id      INTEGER,
    message_text    TEXT NOT NULL,
    author          TEXT NOT NULL DEFAULT '',
    detected_at     TEXT NOT NULL,
    response_text   TEXT,
    confidence      REAL DEFAULT 0.0,
    category        TEXT NOT NULL DEFAULT 'general',
    status          TEXT NOT NULL DEFAULT 'pending',
    sent_at         TEXT
);
"""

_CREATE_METRICS = """
CREATE TABLE IF NOT EXISTS metrics (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    date                TEXT NOT NULL UNIQUE,
    channel_subs        INTEGER DEFAULT 0,
    new_leads           INTEGER DEFAULT 0,
    posts_published     INTEGER DEFAULT 0,
    responses_sent      INTEGER DEFAULT 0,
    channel_views       INTEGER DEFAULT 0,
    created_at          TEXT NOT NULL
);
"""

_CREATE_CUSTDEV_PROBES = """
CREATE TABLE IF NOT EXISTS custdev_probes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER NOT NULL,
    chat_name       TEXT NOT NULL DEFAULT '',
    question_topic  TEXT NOT NULL,
    question_text   TEXT NOT NULL,
    message_id      INTEGER,
    sent_at         TEXT NOT NULL,
    responses_count INTEGER DEFAULT 0,
    responses_json  TEXT DEFAULT '[]',
    status          TEXT NOT NULL DEFAULT 'sent'
);
"""

_CREATE_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);
"""

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);",
    "CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_opportunities_status ON chat_opportunities(status);",
    "CREATE INDEX IF NOT EXISTS idx_opportunities_chat ON chat_opportunities(chat_id, detected_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(date DESC);",
    "CREATE INDEX IF NOT EXISTS idx_custdev_chat ON custdev_probes(chat_id, sent_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_custdev_status ON custdev_probes(status);",
]

_DEFAULT_SETTINGS = [
    ("max_responses_per_chat_per_day", "2"),
    ("max_responses_total_per_day", "10"),
    ("content_generation_day", "sunday"),
    ("publish_days", "tuesday,thursday,saturday"),
    ("publish_hour", "10"),
    ("last_sync_at", ""),
]


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


async def init_db(db_path: str) -> None:
    """Create all tables, indexes, and seed default settings.

    Safe to call multiple times (uses CREATE IF NOT EXISTS).

    Args:
        db_path: Absolute path to SQLite database file.
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

        for ddl in [_CREATE_POSTS, _CREATE_CHAT_OPPORTUNITIES, _CREATE_METRICS, _CREATE_CUSTDEV_PROBES, _CREATE_SETTINGS]:
            await db.execute(ddl)

        for idx in _INDEXES:
            await db.execute(idx)

        # Seed default settings (ignore if already exist)
        for key, value in _DEFAULT_SETTINGS:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )

        await db.commit()

    logger.info("db.initialized", db_path=db_path)


async def get_setting(db_path: str, key: str, default: str = "") -> str:
    """Read a setting value by key."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else default


async def set_setting(db_path: str, key: str, value: str) -> None:
    """Write or update a setting value."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()
