"""Message relevance detector for chat monitoring.

Артём реагирует на любые интересные разговоры селлеров.
Не только на боли -- на вопросы, обсуждения, новости, жалобы.
Цель: быть активным участником чата, а не ботом-продавцом.

Two-level detection:
1. Keyword pattern match (fast, local)
2. Claude CLI semantic check (for borderline cases)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite
import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Categories -- what kind of conversation is this
# ---------------------------------------------------------------------------

CAT_QUESTION = "question"          # кто-то спрашивает совет
CAT_COMPLAINT = "complaint"        # жалуются на вб/озон/логистику
CAT_DISCUSSION = "discussion"      # обсуждают тему (реклама, трафик, карточки)
CAT_NEWS = "news_reaction"         # реагируют на новость
CAT_EXPERIENCE = "experience"      # делятся опытом
CAT_GENERAL = "general"            # общая релевантная тема для участия
CAT_IRRELEVANT = "irrelevant"

# ---------------------------------------------------------------------------
# Keyword patterns -- triggers for engagement
# ---------------------------------------------------------------------------

# Questions (someone asking for help/advice)
_QUESTION_PATTERNS = [
    r"(кто|у кого).{0,30}(пробовал|делал|сталкивался|есть опыт)",
    r"подскажите.{0,30}(как|где|что|почему|сколько)",
    r"(как|где|что).{0,20}(сделать|решить|настроить|убрать|поменять|загрузить)",
    r"(посоветуйте|подскажите|помогите|расскажите)",
    r"кто.{0,15}(знает|понимает|разбирается|может помочь)",
    r"а (вы|кто-нибудь|кто-то).{0,20}\?",
    r"(стоит ли|имеет смысл|есть смысл).{0,30}\?",
    r"как (у вас|у кого).{0,20}\?",
]

# Complaints (pain points people vent about)
_COMPLAINT_PATTERNS = [
    r"(задолбал|бесит|достал|надоел).{0,30}(вб|wb|озон|ozon|маркетплейс)",
    r"(выплаты|выплата).{0,20}(задерж|нет|не приш|где)",
    r"комисси.{0,20}(подняли|повысили|выросл|опять|снова)",
    r"(поддержка|саппорт).{0,20}(не отвечает|шаблон|бесполезн|игнор)",
    r"(приёмка|приемка).{0,20}(тормозит|стоит|неделю|долго|завис)",
    r"(карточка|карточки).{0,20}(упала|слетела|забанили|заблок)",
    r"(реклама|продвижение).{0,20}(не работает|сливает|бюджет|дорого|ноль)",
    r"(возвраты|возврат).{0,20}(много|процент|убыт|замучил)",
    r"(штраф|штрафы).{0,20}(вб|wb|озон|ozon|за что|опять)",
    r"(фото|фотки|изображения).{0,20}(не загруж|висят|старые|не обновл)",
]

# Discussions (active topics people engage with)
_DISCUSSION_PATTERNS = [
    r"(внешний|внешн).{0,15}(трафик|реклама|продвижение)",
    r"(посев|посевы).{0,15}(в каналах|телеграм|тг)",
    r"(рилс|reels|тикток|tiktok).{0,15}(для|товар|продвиж|работает)",
    r"(блогер|инфлюенсер).{0,15}(реклама|бартер|интеграц|работает)",
    r"(seo|сео).{0,15}(карточк|оптимиз|ключ|запрос)",
    r"(инфографика|rich.?контент).{0,10}(делаете|работает|влияет|конверс)",
    r"(конверси|ctr|клик).{0,15}(карточк|повыс|упал|как)",
    r"(fbs|fbo|dbs).{0,15}(лучше|выгоднее|перешёл|перешел|разница)",
    r"(юнит.?экономик|маржа|маржинальн).{0,15}(как|считать|какая|упала)",
    r"(дрр|drr|рекламный\s+расход).{0,15}(\d|процент|какой|норм)",
    r"(склейка|склейки).{0,10}(делаете|работает|есть смысл)",
    r"(самовыкуп|самовыкупы).{0,10}(ещё|работает|рискован|опасно)",
    r"(бренд|свой бренд).{0,15}(строить|развивать|зачем|смысл)",
    r"(телеграм|тг).{0,10}(канал|бот).{0,15}(для|покупател|база)",
    r"(мессенджер|месенджер).{0,10}(макс|max)\b",
    r"\bмакс\b.{0,15}(мессенджер|месенджер|приложение|бот|канал)",
]

# News reactions (people discussing marketplace news/changes)
_NEWS_PATTERNS = [
    r"(слышали|видели|читали).{0,20}(вб|wb|озон|ozon).{0,20}(теперь|будет|ввод)",
    r"(новые|новый).{0,10}(правила|тариф|условия|закон|требования)",
    r"(с\s+\d+\s+(апреля|мая|июня|марта)).{0,20}(вб|озон|комисс|тариф|правил)",
    r"(обновлени|изменени).{0,15}(лк|алгоритм|правил|условий)",
    r"(ркн|роскомнадзор|впн|vpn).{0,20}(блок|запрет|закон)",
]

# Experience sharing (people telling what worked/didn't work)
_EXPERIENCE_PATTERNS = [
    r"(попробовал|протестил|запустил|сделал).{0,20}(и\s+|—\s*|,\s*)(результат|итог|вот что|получил)",
    r"(у меня|мой опыт|расскажу).{0,20}(работает|не работает|получилось|не получилось)",
    r"(перешёл|перешел|переехал).{0,15}(на|с).{0,10}(fbs|fbo|озон|вб)",
    r"(поделюсь|делюсь).{0,15}(опытом|результат|цифр|статистик)",
]

# Broad question patterns (any question about seller topics)
_QUESTION_BROAD_PATTERNS = [
    r".{15,}\?$",                    # any message 15+ chars ending with ?
    r"(а\s+)?((как|что|где|почему|зачем|сколько|когда)\s+).{5,}\?",  # вопросительное слово + ?
    r"(кто-нибудь|кто-то|может кто|есть кто).{0,30}\?",
    r"(не знаете|не подскажете|не в курсе).{0,30}\?",
    r"(что думаете|что скажете|ваше мнение)",
]

# General seller chat (broad — lower priority, catches most marketplace talk)
_GENERAL_PATTERNS = [
    # WB/Ozon mentions in context
    r"(вб|wb|вайлдберриз|wildberries).{5,}",
    r"(озон|ozon).{5,}",
    # Money, payments, orders
    r"(выплат|оплат|выручк|оборот|доход|заработ).{3,}",
    r"\d+\s*(к|тыс|руб|₽).{0,15}(в день|в месяц|за неделю|за месяц|оборот|маржа)",
    # Logistics & operations
    r"(поставк|отгрузк|склад|палле|короб|упаковк).{3,}",
    r"(пвз|рц|сц|фулфилмент|fulfilment).{3,}",
    # Product & cards
    r"(карточк|артикул|sku|фото|видео|контент|инфографик).{3,}",
    r"(рейтинг|отзыв|звёзд|звезд).{0,20}(упал|вырос|как|мало|много|накрут)",
    # Advertising & promotion
    r"(реклам|бюджет|ставк|аукцион|cpm|cpc|ctr|автокампан).{3,}",
    r"(продвижен|трафик|показ|клик|конверси).{3,}",
    # Business general
    r"(конкурент|ниш|категори|рынок|сезон).{3,}",
    r"(товар|продукт|ассортимент|линейк).{0,15}(новый|запуск|добавил|вывод|закрыл)",
    # News & changes
    r"(новост|обновлен|измен|правил).{0,15}(вб|wb|озон|ozon|маркетплейс)",
    # Emotions (frustration/excitement about work)
    r"(задолбал|бесит|достал|надоел|устал|заебал).{3,}",
    r"(наконец|ура|круто|офигеть|ого|вау).{0,15}(заработал|пришл|получил|вырос|запустил)",
    # Pricing, unit economics
    r"(цен|ценообразован|скидк|акци|распродаж).{0,15}(вб|wb|озон|ozon|ставить|участвов|обязательн)",
]

# Skip these -- spam, ads, job posts
_EXCLUSION_PATTERNS = [
    r"(ищу\s+работу|ищу\s+сотрудник|вакансия|резюме)",
    r"(куплю|продам)\s+аккаунт",
    r"(кредит|займ).{0,15}(бизнес|продавц|для)",
    r"реклама\s+в\s+канал",
    r"(партнерка|партнёрка).{0,15}(казин|ставк|игр)",
    r"(вывод|обнал).{0,15}(денег|средств)",
    r"(спам|подписывайтесь на|переходите в)",
    r"(менеджер.{0,5}маркетплейс|готов.{0,10}вести.{0,10}аккаунт)",
]


@dataclass
class DetectionResult:
    relevant: bool
    category: str
    score: float
    reasoning: str
    matched_patterns: list[str] = field(default_factory=list)
    semantic_check_done: bool = False


class MessageDetector:
    """Detects messages worth engaging with."""

    def __init__(
        self,
        db_path: str,
        keyword_patterns_file: Optional[Path] = None,
        min_cooldown_minutes: int = 5,
        max_per_chat_per_day: int = 70,
        max_total_per_day: int = 200,
        claude_cli_path: str = "claude",
    ) -> None:
        self.db_path = db_path
        self.min_cooldown_minutes = min_cooldown_minutes
        self.max_per_chat_per_day = max_per_chat_per_day
        self.max_total_per_day = max_total_per_day
        self.claude_cli_path = claude_cli_path

        self._question_pats = _compile(_QUESTION_PATTERNS)
        self._question_broad_pats = _compile(_QUESTION_BROAD_PATTERNS)
        self._complaint_pats = _compile(_COMPLAINT_PATTERNS)
        self._discussion_pats = _compile(_DISCUSSION_PATTERNS)
        self._news_pats = _compile(_NEWS_PATTERNS)
        self._experience_pats = _compile(_EXPERIENCE_PATTERNS)
        self._general_pats = _compile(_GENERAL_PATTERNS)
        self._exclusion_pats = _compile(_EXCLUSION_PATTERNS)

        # Extra patterns from JSON file
        self._extra_pats: list[re.Pattern] = []
        if keyword_patterns_file and keyword_patterns_file.exists():
            try:
                data = json.loads(keyword_patterns_file.read_text(encoding="utf-8"))
                self._extra_pats = _compile(data.get("patterns", []))
                logger.info("detector.loaded_extra_patterns", count=len(self._extra_pats))
            except Exception as exc:
                logger.warning("detector.extra_patterns_failed", error=str(exc))

        # Semantic check rate limiter: max checks per hour
        self._semantic_check_timestamps: list[float] = []
        self._max_semantic_checks_per_hour = 40

    async def detect(
        self,
        chat_id: int,
        message_text: str,
        use_semantic_check: bool = True,
    ) -> DetectionResult:
        lower = message_text.lower()

        # Too short -- skip
        if len(message_text) < 10:
            return DetectionResult(False, CAT_IRRELEVANT, 0.0, "Too short")

        # Exclusion
        for p in self._exclusion_pats:
            if p.search(lower):
                return DetectionResult(False, CAT_IRRELEVANT, 0.0, "Spam/ads/jobs")

        # Rate limits
        if not await self._within_rate_limits(chat_id):
            return DetectionResult(False, CAT_IRRELEVANT, 0.0, "Rate limit")

        # Match by category (ordered by priority)
        result = self._match(lower)

        # Semantic fallback for unmatched messages (rate-limited)
        if not result.relevant and use_semantic_check:
            if self._can_do_semantic_check():
                result = await self._semantic_check(message_text, result)

        return result

    def _match(self, lower: str) -> DetectionResult:
        """Fast keyword matching across all categories."""

        # Questions -- highest value, someone needs help
        matched = [p.pattern[:40] for p in self._question_pats if p.search(lower)]
        if matched:
            return DetectionResult(True, CAT_QUESTION, 0.8, "Question", matched)

        # Complaints -- can empathize
        matched = [p.pattern[:40] for p in self._complaint_pats if p.search(lower)]
        if matched:
            return DetectionResult(True, CAT_COMPLAINT, 0.7, "Complaint", matched)

        # Experience sharing -- can engage
        matched = [p.pattern[:40] for p in self._experience_pats if p.search(lower)]
        if matched:
            return DetectionResult(True, CAT_EXPERIENCE, 0.65, "Experience", matched)

        # News -- can react
        matched = [p.pattern[:40] for p in self._news_pats if p.search(lower)]
        if matched:
            return DetectionResult(True, CAT_NEWS, 0.6, "News reaction", matched)

        # Discussion -- can participate
        matched = [p.pattern[:40] for p in self._discussion_pats if p.search(lower)]
        if matched:
            return DetectionResult(True, CAT_DISCUSSION, 0.55, "Discussion", matched)

        # Extra patterns from JSON (d2c, база покупателей, LTV, повторные)
        if self._extra_pats:
            matched = [p.pattern[:40] for p in self._extra_pats if p.search(lower)]
            if matched:
                return DetectionResult(True, CAT_DISCUSSION, 0.65, "Extra pattern", matched)

        # Broad questions and general patterns disabled — too many false positives that cause bans.
        # Only respond to specific questions, complaints, experience, news, discussions, extra.
        return DetectionResult(False, CAT_IRRELEVANT, 0.0, "No match")

    def _can_do_semantic_check(self) -> bool:
        """Rate limit semantic checks to max N per hour."""
        import time
        now = time.time()
        hour_ago = now - 3600
        self._semantic_check_timestamps = [
            t for t in self._semantic_check_timestamps if t > hour_ago
        ]
        if len(self._semantic_check_timestamps) >= self._max_semantic_checks_per_hour:
            logger.debug("detector.semantic_rate_limited",
                         count=len(self._semantic_check_timestamps))
            return False
        self._semantic_check_timestamps.append(now)
        return True

    async def _semantic_check(self, text: str, initial: DetectionResult) -> DetectionResult:
        """Claude CLI fallback for borderline messages."""
        try:
            from src.utils.claude_cli import generate

            prompt = f"""Сообщение из чата продавцов WB/Ozon:
"{text[:400]}"

Стоит ли на это ответить как обычному селлеру в чате?
Ответь ТОЛЬКО JSON без пояснений:
{{"relevant": true, "score": 0.7, "category": "question"}}

Категории: question, complaint, discussion, news_reaction, experience, general, irrelevant"""

            raw = await generate(
                system_prompt="Ты классификатор сообщений. Отвечай строго JSON, без текста вокруг.",
                user_prompt=prompt,
                claude_cli_path=self.claude_cli_path,
                timeout=30,
                model="haiku",
            )

            data = _extract_json(raw)
            if data is None:
                logger.warning("detector.semantic_parse_failed", raw_preview=raw[:200])
                return initial

            relevant = bool(data.get("relevant", False))
            score = float(data.get("score", 0.0))
            category = data.get("category", CAT_IRRELEVANT)

            result = DetectionResult(
                relevant=relevant and score >= 0.3,
                category=category if relevant else CAT_IRRELEVANT,
                score=score,
                reasoning="Semantic check",
                semantic_check_done=True,
            )
            logger.info(
                "detector.semantic_result",
                relevant=result.relevant,
                category=result.category,
                score=result.score,
            )
            return result

        except Exception as exc:
            logger.warning("detector.semantic_failed", error=str(exc))
            return initial

    async def _within_rate_limits(self, chat_id: int) -> bool:
        today = date.today().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            # Cooldown: check time since last sent message in this chat
            cursor = await db.execute(
                """SELECT sent_at FROM chat_opportunities
                   WHERE chat_id = ? AND status = 'sent'
                   ORDER BY sent_at DESC LIMIT 1""",
                (chat_id,),
            )
            row = await cursor.fetchone()
            if row and row[0]:
                try:
                    last_sent = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    elapsed_minutes = (now - last_sent).total_seconds() / 60
                    if elapsed_minutes < self.min_cooldown_minutes:
                        logger.info(
                            "detector.rate_limited",
                            reason="cooldown",
                            chat_id=chat_id,
                            elapsed=f"{elapsed_minutes:.1f}m",
                            cooldown=f"{self.min_cooldown_minutes}m",
                        )
                        return False
                except (ValueError, TypeError):
                    pass

            # Daily safety cap per chat
            cursor = await db.execute(
                "SELECT COUNT(*) FROM chat_opportunities WHERE chat_id = ? AND status = 'sent' AND date(sent_at) = ?",
                (chat_id, today),
            )
            row = await cursor.fetchone()
            chat_sent = row[0] if row else 0
            if chat_sent >= self.max_per_chat_per_day:
                logger.info(
                    "detector.rate_limited",
                    reason="per_chat_daily_cap",
                    chat_id=chat_id,
                    sent=chat_sent,
                    cap=self.max_per_chat_per_day,
                )
                return False

            # Daily safety cap total
            cursor = await db.execute(
                "SELECT COUNT(*) FROM chat_opportunities WHERE status = 'sent' AND date(sent_at) = ?",
                (today,),
            )
            row = await cursor.fetchone()
            total_sent = row[0] if row else 0
            if total_sent >= self.max_total_per_day:
                logger.info(
                    "detector.rate_limited",
                    reason="total_daily_cap",
                    sent=total_sent,
                    cap=self.max_total_per_day,
                )
                return False

        return True


def _extract_json(raw: str) -> dict | None:
    """Extract JSON from Claude CLI output (handles markdown wrapping)."""
    if not raw or not raw.strip():
        return None

    raw = raw.strip()

    # Try direct parse
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    # Try finding first JSON object
    match = re.search(r"\{[^{}]*\"relevant\"[^{}]*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _compile(patterns: list[str]) -> list[re.Pattern]:
    result = []
    for p in patterns:
        try:
            result.append(re.compile(p, re.IGNORECASE | re.UNICODE))
        except re.error as exc:
            logger.warning("detector.compile_error", pattern=p, error=str(exc))
    return result
