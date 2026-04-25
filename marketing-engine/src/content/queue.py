"""Content queue manager backed by SQLite.

Manages post lifecycle: draft -> pending_review -> approved/rejected -> published.

Posts have a `source` ("ai" | "notion") and optional `external_id` pointing to
a Notion page. Notion-sourced posts take priority at publish time so imported
editorial content goes out before AI fallback drafts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import aiosqlite
import structlog

logger = structlog.get_logger(__name__)


class PostStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class PostSource(str, Enum):
    AI = "ai"
    NOTION = "notion"


class ContentQueue:
    """SQLite-backed content queue."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def add_post(
        self,
        post_type: str,
        title: str,
        text: str,
        cta: str = "",
        image_path: Optional[str] = None,
        status: PostStatus = PostStatus.PENDING_REVIEW,
        *,
        source: PostSource = PostSource.AI,
        external_id: Optional[str] = None,
        rubric: Optional[str] = None,
    ) -> int:
        """Insert a new post into the queue.

        Returns:
            New post ID.
        """
        now = _utcnow()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO posts
                    (type, title, text, cta, image_path, status, created_at,
                     source, external_id, rubric)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post_type, title, text, cta, image_path, status.value, now,
                    source.value, external_id, rubric,
                ),
            )
            await db.commit()
            post_id = cursor.lastrowid

        logger.info(
            "content_queue.post_added",
            post_id=post_id,
            post_type=post_type,
            source=source.value,
            status=status.value,
        )
        return post_id

    async def upsert_from_notion(
        self,
        *,
        external_id: str,
        post_type: str,
        title: str,
        text: str,
        rubric: Optional[str],
        cta: str = "",
        status: PostStatus = PostStatus.PENDING_REVIEW,
    ) -> int:
        """Insert OR refresh a Notion-sourced post.

        Idempotent: re-calling with the same `external_id` updates the
        existing row if status is still pending_review. After approval
        the row is locked to preserve the version the admin approved.
        """
        existing = await self.get_by_external_id(external_id)
        if existing is None:
            return await self.add_post(
                post_type=post_type,
                title=title, text=text, cta=cta,
                status=status,
                source=PostSource.NOTION,
                external_id=external_id,
                rubric=rubric,
            )
        # Lock after approval
        if existing["status"] in {PostStatus.APPROVED.value, PostStatus.PUBLISHED.value}:
            logger.info(
                "content_queue.notion_locked",
                post_id=existing["id"], external_id=external_id,
            )
            return existing["id"]

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE posts
                SET type = ?, title = ?, text = ?, cta = ?, rubric = ?
                WHERE id = ?
                """,
                (post_type, title, text, cta, rubric, existing["id"]),
            )
            await db.commit()
        logger.info(
            "content_queue.notion_refreshed",
            post_id=existing["id"], external_id=external_id,
        )
        return existing["id"]

    async def approve(self, post_id: int) -> None:
        """Move a post from pending_review to approved."""
        await self._update_status(post_id, PostStatus.APPROVED)

    async def reject(self, post_id: int, reason: str = "") -> None:
        """Move a post to rejected, optionally recording a reason."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE posts SET status = ?, rejection_reason = ? WHERE id = ?",
                (PostStatus.REJECTED.value, reason, post_id),
            )
            await db.commit()
        logger.info("content_queue.post_rejected", post_id=post_id, reason=reason)

    async def mark_published(
        self,
        post_id: int,
        telegram_message_id: Optional[int] = None,
        published_url: Optional[str] = None,
    ) -> None:
        """Mark a post as published."""
        now = _utcnow()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE posts
                SET status = ?, published_at = ?,
                    telegram_message_id = ?, published_url = ?
                WHERE id = ?
                """,
                (PostStatus.PUBLISHED.value, now, telegram_message_id, published_url, post_id),
            )
            await db.commit()
        logger.info(
            "content_queue.post_published",
            post_id=post_id,
            telegram_message_id=telegram_message_id,
            published_url=published_url,
        )

    async def update_image_path(self, post_id: int, image_path: str) -> None:
        """Update the image path for a post."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE posts SET image_path = ? WHERE id = ?",
                (image_path, post_id),
            )
            await db.commit()

    async def set_external_id(self, post_id: int, external_id: str) -> None:
        """Attach a Notion page_id to an existing post (used when an AI draft
        gets pushed to Notion after creation)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE posts SET external_id = ? WHERE id = ?",
                (external_id, post_id),
            )
            await db.commit()

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_next_approved(self) -> Optional[dict]:
        """Oldest approved post ready for publishing. Notion-sourced first."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM posts
                WHERE status = ?
                ORDER BY
                    CASE WHEN source = 'notion' THEN 0 ELSE 1 END,
                    created_at ASC
                LIMIT 1
                """,
                (PostStatus.APPROVED.value,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_pending(self) -> list[dict]:
        """Get all posts waiting for review."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM posts WHERE status = ? ORDER BY created_at DESC",
                (PostStatus.PENDING_REVIEW.value,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_post(self, post_id: int) -> Optional[dict]:
        """Get a single post by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM posts WHERE id = ?", (post_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_by_external_id(self, external_id: str) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM posts WHERE external_id = ? LIMIT 1",
                (external_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_recent_published(self, limit: int = 10) -> list[dict]:
        """Get recently published posts (for avoiding content repetition)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM posts
                WHERE status = ?
                ORDER BY published_at DESC
                LIMIT ?
                """,
                (PostStatus.PUBLISHED.value, limit),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def count_by_status(self) -> dict[str, int]:
        """Return count of posts grouped by status."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT status, COUNT(*) as cnt FROM posts GROUP BY status"
            )
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    async def clear_unpublished(self) -> int:
        """Delete every row that hasn't reached `published`. Returns deleted count.

        Used when the user asks to "reset the queue and regenerate".
        Preserves historical published posts for analytics.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM posts WHERE status != ?",
                (PostStatus.PUBLISHED.value,),
            )
            deleted = cursor.rowcount
            await db.commit()
        logger.info("content_queue.cleared", deleted=deleted)
        return deleted

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _update_status(self, post_id: int, status: PostStatus) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE posts SET status = ? WHERE id = ?",
                (status.value, post_id),
            )
            await db.commit()
        logger.info(
            "content_queue.status_updated",
            post_id=post_id,
            new_status=status.value,
        )


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()
