"""Channel publisher.

Takes an approved post from the queue and publishes it to the Telegram
channel. Optionally:
- generates a branded image for the post
- marks the Notion page Опубликован + writes the channel URL back
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import structlog

from src.content.notion_source import NotionSource
from src.content.queue import ContentQueue, PostStatus
from src.utils.telegram import send_to_channel

logger = structlog.get_logger(__name__)


class ChannelPublisher:
    """Publishes approved posts to the Telegram channel."""

    def __init__(
        self,
        bot_token: str,
        channel_id: str,
        data_dir: Path,
        generate_images: bool = True,
        claude_cli_path: str = "claude",
        notion_source: Optional[NotionSource] = None,
    ) -> None:
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.data_dir = data_dir
        self.generate_images = generate_images
        self.claude_cli_path = claude_cli_path
        self.notion_source = notion_source
        self._images_dir = data_dir / "images"
        self._images_dir.mkdir(parents=True, exist_ok=True)

    async def publish_next(self, queue: ContentQueue) -> Optional[dict]:
        """Fetch the next approved post and publish it.

        Returns:
            The published post dict, or None if nothing was available.
        """
        post = await queue.get_next_approved()
        if not post:
            logger.info("channel_publisher.no_approved_posts")
            return None

        return await self.publish_post(post, queue)

    async def publish_post(self, post: dict, queue: ContentQueue) -> dict:
        """Publish a specific post dict.

        Args:
            post: Post dict from the database.
            queue: ContentQueue instance for status updates.

        Returns:
            Updated post dict.
        """
        post_id = post["id"]
        logger.info(
            "channel_publisher.publishing",
            post_id=post_id,
            post_type=post.get("type"),
        )

        # Build message text
        text = _format_message(post)

        # Determine image path
        image_path: Optional[Path] = None
        if post.get("image_path") and Path(post["image_path"]).exists():
            image_path = Path(post["image_path"])
        elif self.generate_images:
            image_path = await self._generate_image(post, queue)

        try:
            response = await send_to_channel(
                bot_token=self.bot_token,
                channel_id=self.channel_id,
                text=text,
                image_path=image_path,
            )

            telegram_message_id = (
                response.get("result", {}).get("message_id")
            )

            published_url = _build_channel_url(self.channel_id, telegram_message_id)
            await queue.mark_published(
                post_id,
                telegram_message_id=telegram_message_id,
                published_url=published_url,
            )

            # Propagate to Notion if this post came from there (or was
            # pushed there after AI generation — either way the page id
            # is in external_id).
            external_id = post.get("external_id")
            if external_id and self.notion_source and self.notion_source.enabled:
                ok = await self.notion_source.mark_published(
                    page_id=external_id,
                    channel_url=published_url,
                )
                if not ok:
                    logger.warning(
                        "channel_publisher.notion_mark_failed",
                        post_id=post_id, external_id=external_id,
                    )

            logger.info(
                "channel_publisher.published",
                post_id=post_id,
                telegram_message_id=telegram_message_id,
                published_url=published_url,
            )

            return {
                **post,
                "status": PostStatus.PUBLISHED.value,
                "telegram_message_id": telegram_message_id,
                "published_url": published_url,
            }

        except Exception as exc:
            logger.error(
                "channel_publisher.publish_failed",
                post_id=post_id,
                error=str(exc),
            )
            raise

    async def _generate_image(
        self, post: dict, queue: ContentQueue
    ) -> Optional[Path]:
        """Generate a branded image for the post."""
        output_path = self._images_dir / f"post_{post['id']}.png"
        title = post.get("title", "")
        text = post.get("text", "")
        post_type = post.get("type", "")

        try:
            from src.publisher.image_gen import generate_post_image

            generate_post_image(
                headline=title or text[:80],
                post_type=post_type,
                body_text=text,
                output_path=output_path,
            )
            await queue.update_image_path(post["id"], str(output_path))
            return output_path
        except Exception as exc:
            logger.warning("channel_publisher.image_gen_failed", post_id=post["id"], error=str(exc))
            return None


def _build_channel_url(channel_id: str, message_id: Optional[int]) -> Optional[str]:
    """Compose a `https://t.me/<channel>/<msg>` URL.

    Accepts both `@channel_name` and numeric IDs (`-100...`). Returns None
    if we can't build a public URL (e.g. numeric private id without alias).
    """
    if not message_id:
        return None
    cid = (channel_id or "").strip()
    if cid.startswith("@"):
        return f"https://t.me/{cid[1:]}/{message_id}"
    # Numeric -100xxxxxxxxxx form — needs `c/<short>/<msg>` for private
    if cid.startswith("-100"):
        short = cid[4:]
        return f"https://t.me/c/{short}/{message_id}"
    return None


def _format_message(post: dict) -> str:
    """Format post for Telegram message.

    Combines title and text, appends CTA as separate line.
    Uses HTML parse mode.
    """
    parts = []

    if post.get("title"):
        parts.append(f"<b>{post['title']}</b>")
        parts.append("")  # blank line

    if post.get("text"):
        parts.append(post["text"])

    if post.get("cta"):
        parts.append("")  # blank line
        parts.append(post["cta"])

    return "\n".join(parts)


