"""News fetcher for WB/Ozon marketplace news.

Fetches from RSS feeds and returns structured news items.
Used to provide fresh context for content generation.
"""

from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import aiohttp
import structlog

logger = structlog.get_logger(__name__)

# RSS feed sources for marketplace news
RSS_SOURCES = [
    {
        "name": "oborot.ru",
        "url": "https://oborot.ru/news/rss.xml",
        "category": "marketplace",
    },
    {
        "name": "vc.ru/marketplace",
        "url": "https://vc.ru/rss/marketplace",
        "category": "marketplace",
    },
    {
        "name": "retail.ru",
        "url": "https://www.retail.ru/rss/news.rss",
        "category": "retail",
    },
]

# Telegram channels to monitor (channel usernames for context)
TELEGRAM_CHANNEL_SOURCES = [
    "@wb_official",
    "@ozon_news",
    "@marketplace_news_ru",
]

# Keywords to filter relevant news
RELEVANCE_KEYWORDS = [
    "wildberries",
    "wb",
    "ozon",
    "маркетплейс",
    "продавец",
    "селлер",
    "комиссия",
    "выплата",
    "тариф",
    "хранение",
    "логистика",
    "возврат",
    "рейтинг",
    "алгоритм",
    "поиск",
    "реклама wb",
    "реклама ozon",
    "штраф",
    "блокировка",
]

_FETCH_TIMEOUT = 15  # seconds per feed


@dataclass
class NewsItem:
    title: str
    summary: str
    source: str
    url: str
    date: datetime
    relevance_score: float  # 0.0 - 1.0


async def fetch_marketplace_news(
    max_items: int = 20,
    min_relevance: float = 0.3,
) -> list[NewsItem]:
    """Fetch recent marketplace news from all configured RSS sources.

    Args:
        max_items: Maximum number of items to return.
        min_relevance: Minimum relevance score to include an item.

    Returns:
        List of NewsItem sorted by date descending.
    """
    tasks = [_fetch_rss(source) for source in RSS_SOURCES]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items: list[NewsItem] = []
    for source, result in zip(RSS_SOURCES, results):
        if isinstance(result, Exception):
            logger.warning(
                "news_fetcher.rss.failed",
                source=source["name"],
                error=str(result),
            )
            continue
        all_items.extend(result)

    # Filter by relevance
    relevant = [
        item for item in all_items if item.relevance_score >= min_relevance
    ]

    # Sort by date descending
    relevant.sort(key=lambda x: x.date, reverse=True)

    logger.info(
        "news_fetcher.done",
        total_fetched=len(all_items),
        relevant=len(relevant),
        returned=min(len(relevant), max_items),
    )

    return relevant[:max_items]


async def _fetch_rss(source: dict) -> list[NewsItem]:
    """Fetch and parse a single RSS feed."""
    timeout = aiohttp.ClientTimeout(total=_FETCH_TIMEOUT)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MarketingBot/1.0)",
    }

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(source["url"]) as resp:
            if resp.status != 200:
                raise RuntimeError(
                    f"HTTP {resp.status} from {source['url']}"
                )
            content = await resp.text()

    return _parse_rss(content, source["name"])


def _parse_rss(xml_content: str, source_name: str) -> list[NewsItem]:
    """Parse RSS XML into NewsItem list."""
    items: list[NewsItem] = []

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        logger.warning("news_fetcher.xml_parse_error", source=source_name, error=str(exc))
        return items

    # Handle both RSS 2.0 and Atom
    channel = root.find("channel")
    if channel is None:
        # Try Atom
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
    else:
        entries = channel.findall("item")

    for entry in entries:
        item = _parse_entry(entry, source_name)
        if item:
            items.append(item)

    return items


def _parse_entry(entry: ET.Element, source_name: str) -> Optional[NewsItem]:
    """Parse a single RSS item/entry element."""
    def get_text(tag: str) -> str:
        el = entry.find(tag)
        return (el.text or "").strip() if el is not None else ""

    title = get_text("title")
    if not title:
        return None

    summary = get_text("description") or get_text("summary") or ""
    # Strip HTML tags from summary
    summary = re.sub(r"<[^>]+>", "", summary).strip()
    summary = summary[:500]  # Limit length

    url = get_text("link") or ""
    date_str = get_text("pubDate") or get_text("published") or ""

    # Parse date
    date = _parse_date(date_str)

    relevance = _calculate_relevance(title + " " + summary)

    return NewsItem(
        title=title,
        summary=summary,
        source=source_name,
        url=url,
        date=date,
        relevance_score=relevance,
    )


def _parse_date(date_str: str) -> datetime:
    """Parse various date formats, fall back to now."""
    if not date_str:
        return datetime.now(timezone.utc)

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return datetime.now(timezone.utc)


def _calculate_relevance(text: str) -> float:
    """Calculate relevance score based on keyword matches."""
    lower = text.lower()
    matches = sum(1 for kw in RELEVANCE_KEYWORDS if kw in lower)
    # Normalize: 3+ keywords = 1.0
    return min(matches / 3.0, 1.0)

