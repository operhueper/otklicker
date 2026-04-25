"""Notion integration for the posts database.

Two-way sync with the Notion database "📝 Посты TG-канала"
(id `f1dbfb2d-7bfd-4a57-ae46-4d0823187b7e`).

What it does
------------
- fetch_scheduled(): pull posts marked "Запланирован" from Notion so
  the importer can queue them for admin review.
- mark_published(page_id, channel_url): flip the Notion status to
  "Опубликован" and record the published URL in Заметки.
- create_post(...): push an AI-generated or AI-drafted post INTO
  Notion as "Черновик". Everything we generate or queue is visible
  in the Notion board — no silent AI drafts.
- update_post(...): refresh title/text/status on an existing Notion
  page. Used when we regenerate the text and want Notion to reflect.

Notion fields we touch
----------------------
Название        — title
Текст поста     — rich_text
Рубрика         — select
Дата публикации — date
Статус          — status
Заметки         — rich_text (used for published URL breadcrumb)

Authentication
--------------
Uses a Notion internal integration token from env `NOTION_TOKEN`.
If unset, every method is a safe no-op that logs a warning. This
keeps local dev from crashing when the token isn't provisioned.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterable, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


_NOTION_API = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"

# Statuses (exact names in the DB)
STATUS_DRAFT = "Черновик"
STATUS_EDIT = "На редактуре"
STATUS_SCHEDULED = "Запланирован"
STATUS_PUBLISHED = "Опубликован"


@dataclass
class NotionPost:
    """A post as it lives in Notion."""
    page_id: str
    title: str
    text: str
    rubric: Optional[str] = None
    status: Optional[str] = None
    scheduled_date: Optional[date] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    last_edited: Optional[datetime] = None

    def is_placeholder_bot(self) -> bool:
        """True if text contains the legacy `@[ваш_бот]` placeholder."""
        return "@[ваш_бот]" in (self.text or "")


class NotionSource:
    """Client for the posts database.

    All methods are `async`. Network calls go through `httpx.AsyncClient`
    with a single shared instance for connection reuse. Call `close()`
    when done — or use `async with`.
    """

    def __init__(
        self,
        token: str,
        database_id: str,
        *,
        bot_placeholder_replacement: str = "@otklicker_bot",
        request_timeout: float = 15.0,
    ) -> None:
        self._token = (token or "").strip()
        self._database_id = database_id
        self._bot_repl = bot_placeholder_replacement
        self._timeout = request_timeout
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "NotionSource":
        self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Notion-Version": _NOTION_VERSION,
                    "Content-Type": "application/json",
                },
            )

    @property
    def enabled(self) -> bool:
        return bool(self._token)

    # ------------------------------------------------------------------
    # Read: query the database
    # ------------------------------------------------------------------

    async def fetch_all(self) -> list[NotionPost]:
        """Return every post in the database (paginated fetch)."""
        if not self.enabled:
            logger.warning("notion.disabled", op="fetch_all")
            return []
        return await self._query(filter_=None)

    async def fetch_by_status(self, status: str) -> list[NotionPost]:
        """Return posts whose Статус == `status`."""
        if not self.enabled:
            logger.warning("notion.disabled", op="fetch_by_status", status=status)
            return []
        return await self._query(filter_={
            "property": "Статус",
            "status": {"equals": status},
        })

    async def fetch_scheduled(self, for_date: Optional[date] = None) -> list[NotionPost]:
        """Return posts marked Запланирован with scheduled_date ≤ for_date.

        If `for_date` is None, returns all scheduled regardless of date.
        """
        all_scheduled = await self.fetch_by_status(STATUS_SCHEDULED)
        if for_date is None:
            return all_scheduled
        return [p for p in all_scheduled if p.scheduled_date is None or p.scheduled_date <= for_date]

    async def fetch_page(self, page_id: str) -> Optional[NotionPost]:
        """Fetch a single page by id."""
        if not self.enabled:
            return None
        self._ensure_client()
        assert self._client is not None
        r = await self._client.get(f"{_NOTION_API}/pages/{page_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        page = r.json()
        text = await self._fetch_page_text(page_id)
        return self._parse_page(page, text=text)

    # ------------------------------------------------------------------
    # Write: mark published / push a new draft / update
    # ------------------------------------------------------------------

    async def mark_published(
        self,
        page_id: str,
        channel_url: Optional[str] = None,
    ) -> bool:
        """Flip status to Опубликован and stash channel_url in Заметки.

        Returns True on success (or silent success when token missing).
        """
        if not self.enabled:
            logger.warning("notion.disabled", op="mark_published", page_id=page_id)
            return False

        props: dict[str, Any] = {
            "Статус": {"status": {"name": STATUS_PUBLISHED}},
        }
        if channel_url:
            # Append to existing notes if the field already has content —
            # this preserves the author's intent notes.
            existing = ""
            try:
                existing = await self._get_plain_text_field(page_id, "Заметки")
            except Exception as exc:  # non-fatal
                logger.warning("notion.read_notes_failed", page_id=page_id, error=str(exc))

            breadcrumb = f"published: {channel_url}"
            note_value = (
                breadcrumb
                if not existing
                else existing.rstrip() + "\n" + breadcrumb
            )
            props["Заметки"] = {"rich_text": _text_to_rich(note_value)}

        return await self._patch_page(page_id, props)

    async def create_post(
        self,
        *,
        title: str,
        text: str,
        rubric: Optional[str] = None,
        status: str = STATUS_DRAFT,
        notes: Optional[str] = None,
    ) -> Optional[str]:
        """Create a new page in the posts database.

        Returns the new page_id, or None if disabled/failed.
        """
        if not self.enabled:
            logger.warning("notion.disabled", op="create_post", title=title[:60])
            return None

        props = self._build_properties(
            title=title, text=text, rubric=rubric, status=status, notes=notes,
        )
        self._ensure_client()
        assert self._client is not None
        payload = {
            "parent": {"database_id": self._database_id},
            "properties": props,
        }
        r = await self._client.post(f"{_NOTION_API}/pages", json=payload)
        if r.status_code >= 300:
            logger.error(
                "notion.create_post_failed",
                status=r.status_code,
                body=r.text[:400],
            )
            return None
        page = r.json()
        logger.info(
            "notion.post_created",
            page_id=page.get("id"),
            title=title[:80],
        )
        return page.get("id")

    async def update_post(
        self,
        page_id: str,
        *,
        title: Optional[str] = None,
        text: Optional[str] = None,
        rubric: Optional[str] = None,
        status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False
        props = self._build_properties(
            title=title, text=text, rubric=rubric, status=status, notes=notes,
            include_only_set=True,
        )
        if not props:
            return True  # nothing to do
        return await self._patch_page(page_id, props)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _query(self, filter_: Optional[dict]) -> list[NotionPost]:
        self._ensure_client()
        assert self._client is not None
        results: list[dict] = []
        cursor: Optional[str] = None

        while True:
            payload: dict[str, Any] = {"page_size": 100}
            if filter_ is not None:
                payload["filter"] = filter_
            if cursor:
                payload["start_cursor"] = cursor
            r = await self._client.post(
                f"{_NOTION_API}/databases/{self._database_id}/query",
                json=payload,
            )
            if r.status_code >= 300:
                logger.error("notion.query_failed", status=r.status_code, body=r.text[:400])
                return []
            data = r.json()
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

        out: list[NotionPost] = []
        for page in results:
            page_id = page.get("id")
            if not page_id:
                continue
            text = await self._fetch_page_text(page_id)
            post = self._parse_page(page, text=text)
            if post is not None:
                out.append(post)
        return out

    async def _fetch_page_text(self, page_id: str) -> str:
        """Return concatenated plain text of the page blocks.

        Notion stores page bodies as blocks (paragraphs), not in a
        property. Title/short fields live in properties; the full
        content lives in blocks. We fetch all blocks and join text.
        """
        self._ensure_client()
        assert self._client is not None
        parts: list[str] = []
        cursor: Optional[str] = None

        while True:
            url = f"{_NOTION_API}/blocks/{page_id}/children"
            if cursor:
                url = f"{url}?start_cursor={cursor}&page_size=100"
            else:
                url = f"{url}?page_size=100"
            r = await self._client.get(url)
            if r.status_code >= 300:
                logger.warning(
                    "notion.fetch_blocks_failed",
                    page_id=page_id, status=r.status_code,
                )
                return ""
            data = r.json()
            for block in data.get("results", []):
                btype = block.get("type")
                if not btype:
                    continue
                body = block.get(btype, {})
                rich = body.get("rich_text", [])
                if rich:
                    text = "".join(r.get("plain_text", "") for r in rich)
                    if text:
                        parts.append(text)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

        full = "\n\n".join(parts)
        if self._bot_repl and "@[ваш_бот]" in full:
            full = full.replace("@[ваш_бот]", self._bot_repl)
        return full

    async def _get_plain_text_field(self, page_id: str, field_name: str) -> str:
        self._ensure_client()
        assert self._client is not None
        r = await self._client.get(f"{_NOTION_API}/pages/{page_id}")
        r.raise_for_status()
        page = r.json()
        prop = page.get("properties", {}).get(field_name, {})
        rich = prop.get("rich_text", [])
        return "".join(item.get("plain_text", "") for item in rich)

    async def _patch_page(self, page_id: str, properties: dict) -> bool:
        self._ensure_client()
        assert self._client is not None
        r = await self._client.patch(
            f"{_NOTION_API}/pages/{page_id}",
            json={"properties": properties},
        )
        if r.status_code >= 300:
            logger.error(
                "notion.patch_failed",
                page_id=page_id, status=r.status_code, body=r.text[:400],
            )
            return False
        return True

    def _parse_page(self, page: dict, *, text: str) -> Optional[NotionPost]:
        props = page.get("properties", {}) or {}
        title = _plain_title(props.get("Название"))
        rubric = _plain_select(props.get("Рубрика"))
        status = _plain_status(props.get("Статус"))
        sched = _plain_date(props.get("Дата публикации"))
        notes = _plain_rich_text(props.get("Заметки"))

        # If the page has NO body blocks but has a "Текст поста" property,
        # fall back to that. (The original schema had Текст поста as a
        # rich_text property; current DB has the body in blocks.)
        if not text:
            text = _plain_rich_text(props.get("Текст поста")) or ""

        if self._bot_repl and "@[ваш_бот]" in text:
            text = text.replace("@[ваш_бот]", self._bot_repl)

        try:
            last_edited = datetime.fromisoformat(
                (page.get("last_edited_time") or "").replace("Z", "+00:00")
            )
        except Exception:
            last_edited = None

        return NotionPost(
            page_id=page.get("id", ""),
            title=title,
            text=text,
            rubric=rubric,
            status=status,
            scheduled_date=sched,
            notes=notes,
            url=page.get("url"),
            last_edited=last_edited,
        )

    def _build_properties(
        self,
        *,
        title: Optional[str] = None,
        text: Optional[str] = None,
        rubric: Optional[str] = None,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        include_only_set: bool = False,
    ) -> dict[str, Any]:
        props: dict[str, Any] = {}
        if title is not None or not include_only_set:
            if title is not None:
                props["Название"] = {"title": _text_to_rich(title)}
        if text is not None or not include_only_set:
            if text is not None:
                # Stored in "Текст поста" property as well as we can't
                # reliably push multi-block content via this API in a
                # single call without racey retries. Property copy is
                # enough for the admin to see the text; blocks come later.
                props["Текст поста"] = {"rich_text": _text_to_rich(text)}
        if rubric is not None or not include_only_set:
            if rubric is not None:
                props["Рубрика"] = {"select": {"name": rubric}}
        if status is not None or not include_only_set:
            if status is not None:
                props["Статус"] = {"status": {"name": status}}
        if notes is not None or not include_only_set:
            if notes is not None:
                props["Заметки"] = {"rich_text": _text_to_rich(notes)}
        return props


# ----------------------------------------------------------------------
# Property parsers (module-level helpers — pure functions)
# ----------------------------------------------------------------------


def _plain_title(prop: Optional[dict]) -> str:
    if not prop:
        return ""
    return "".join(item.get("plain_text", "") for item in (prop.get("title") or []))


def _plain_rich_text(prop: Optional[dict]) -> str:
    if not prop:
        return ""
    return "".join(item.get("plain_text", "") for item in (prop.get("rich_text") or []))


def _plain_select(prop: Optional[dict]) -> Optional[str]:
    if not prop:
        return None
    sel = prop.get("select")
    if not sel:
        return None
    return sel.get("name")


def _plain_status(prop: Optional[dict]) -> Optional[str]:
    if not prop:
        return None
    st = prop.get("status")
    if not st:
        return None
    return st.get("name")


def _plain_date(prop: Optional[dict]) -> Optional[date]:
    if not prop:
        return None
    d = prop.get("date")
    if not d:
        return None
    raw = d.get("start")
    if not raw:
        return None
    try:
        # ISO date or datetime — take the date portion
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except Exception:
        try:
            return date.fromisoformat(raw[:10])
        except Exception:
            return None


def _text_to_rich(text: str, *, chunk_size: int = 1900) -> list[dict]:
    """Split long text into Notion rich_text blocks (Notion max 2000 chars per block)."""
    if not text:
        return []
    out: list[dict] = []
    remaining = text
    while remaining:
        chunk, remaining = remaining[:chunk_size], remaining[chunk_size:]
        out.append({
            "type": "text",
            "text": {"content": chunk},
            "plain_text": chunk,
        })
    return out
