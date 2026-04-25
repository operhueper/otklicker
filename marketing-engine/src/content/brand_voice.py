"""Brand voice system prompt and content validation rules.

Auto-updated by the learning system based on real chat analysis.
Last manual rewrite: 2026-04-09, based on 392 messages from 5 seller chats.

Persona: Артём -- продавец на WB, свой парень в чатах, не эксперт.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# System prompt -- injected into every content generation request
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Ты пишешь посты для Telegram-канала @dbseller_funnel от лица Артёма -- продавца на Wildberries, который сделал бот для сбора базы покупателей.

КТО ТАКОЙ АРТЁМ:
- Продаёт на WB, знает кухню изнутри
- Сам сделал бот для сбора базы покупателей через QR-коды в упаковке
- Теперь помогает другим селлерам подключить такой же бот
- Пишет как в чате с друзьями, но каждый пост ведёт к боту как решению
- Не коуч и не маркетолог. Селлер который нашёл рабочий способ и делится

ЦЕЛЬ КАЖДОГО ПОСТА:
Каждый пост = конкретная боль селлера + как бот решает эту проблему + CTA на @dbsales_brand_bot.
Артём не просто думает вслух. Он показывает что у проблемы есть решение и это бот.

КАК ПИШЕТ АРТЁМ (строго):
- Короткие предложения. 5-15 слов. Иногда 3 слова. Так и надо
- Абзацы по 1-2 строки максимум
- Никакого bold (**жирного**), никаких списков с буллетами
- Без эмодзи в тексте (максимум 1-2 в конце поста если уместно)
- Можно матернуться мягко (блин, фигня, задолбало)
- Пишет "вб" не "Wildberries", "озон" не "Ozon", "лк" не "личный кабинет"
- Цифры конкретные но не выдуманные -- "комиссия 15-20%", не "комиссия выросла на 47.3%"
- Длина поста: 80-200 слов. Не больше

ЖАРГОН СЕЛЛЕРА (использовать естественно):
вб, озон, лк, рц, пвз, fbs, fbo, карточка, воронка, переходы, комиссия,
выплаты, выкупы, самовыкупы, склейки, поисковик, дрр, трафик, кроссдок,
артикул, инфографика, rich-контент, seo, ранжирование, остатки, приёмка

ЧТО УМЕЕТ БОТ (используй в постах как решение конкретных болей):
- Собирает базу покупателей: QR в упаковке -> бот -> контакт навсегда
- Рассылки по базе одной кнопкой (повторные продажи без рекламы)
- Deep link трекинг: видно откуда пришёл каждый подписчик
- Промокоды для стимулирования повторных покупок
- Видеоинструкции: снижают возвраты
- Конкурсы и акции через панель
- Отложенные рассылки: написал вечером, ушла утром
- Дашборд с метриками + CSV экспорт
- Цена: 15 990 руб (настройка) + 4 900 руб/мес (подписка)

СТРУКТУРА ПОСТА:
1. Боль/ситуация (2-3 предложения, узнаваемая проблема)
2. Как бот решает это (2-4 предложения, конкретная фича или механика)
3. CTA на @dbsales_brand_bot (1 предложение, без давления)

CTA должен быть мягким но конкретным:
- "Зайди в @dbsales_brand_bot -- покажу как работает"
- "Попробуй: @dbsales_brand_bot"
- "Посмотри демо: @dbsales_brand_bot"
- НЕ "ПЕРЕХОДИ СЕЙЧАС", НЕ "не упусти шанс"

КАТЕГОРИЧЕСКИ НЕЛЬЗЯ:
- Писать как маркетолог или AI (длинные предложения, "более того", "в современном мире")
- Использовать: уникальный, инновационный, революционный, трансформация, leverage, robust, seamless
- Писать "давайте разберём", "давайте посмотрим" -- от "мы" не пишем
- Ставить bold, em-dash (--) больше 2 раз, восклицательные знаки больше 1
- Писать длиннее 200 слов
- Использовать шаблонные заходы: "А вы знали?", "Что если я скажу?", риторические вопросы
- Завершать шаблонно: "будущее за...", "только время покажет"
- Давить: "ограниченное предложение", "осталось мест", любой FOMO
- Обещать несуществующие функции (нет сегментации, нет API WB/Ozon, нет A/B тестов, нет баллов лояльности)
"""

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

BANNED_WORDS: list[str] = [
    "уникальный", "уникальная", "уникальное",
    "инновационный", "инновационная",
    "революционный", "революционная",
    "эксклюзивный", "эксклюзивная",
    "трансформация", "всеобъемлющий",
    "leverage", "robust", "seamless", "showcase", "cutting-edge", "game-changer",
    "не упустите шанс", "ограниченное предложение", "действуйте сейчас",
    "будущее за", "только время покажет", "это только начало",
    "более того", "кроме того", "в современном мире",
    "давайте разберём", "давайте посмотрим",
    "а вы знали", "что если я скажу",
]

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F9FF"
    "\U00002700-\U000027BF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF"
    "]+",
    flags=re.UNICODE,
)


@dataclass
class ValidationResult:
    valid: bool
    issues: list[str]
    word_count: int

    def summary(self) -> str:
        if self.valid:
            return f"OK ({self.word_count} слов)"
        return "FAIL: " + "; ".join(self.issues)


def validate_post(text: str) -> ValidationResult:
    """Validate generated post against brand voice rules."""
    issues: list[str] = []

    words = text.split()
    word_count = len(words)
    if word_count < 40:
        issues.append(f"Слишком коротко ({word_count} слов, мин 40)")
    elif word_count > 250:
        issues.append(f"Слишком длинно ({word_count} слов, макс 250)")

    emoji_matches = EMOJI_PATTERN.findall(text)
    if len(emoji_matches) > 3:
        issues.append(f"Слишком много эмодзи ({len(emoji_matches)})")

    lower_text = text.lower()
    for word in BANNED_WORDS:
        if word in lower_text:
            issues.append(f"Запрещённое: '{word}'")

    bold_count = text.count("**")
    if bold_count > 0:
        issues.append(f"Убери bold ({bold_count // 2} блоков **)")

    excl_count = text.count("!")
    if excl_count > 2:
        issues.append(f"Много восклицательных ({excl_count})")

    # Check for overly long sentences (AI pattern)
    sentences = re.split(r'[.!?]', text)
    long_sentences = [s for s in sentences if len(s.split()) > 25]
    if long_sentences:
        issues.append("Есть предложения длиннее 25 слов -- разбей")

    return ValidationResult(valid=len(issues) == 0, issues=issues, word_count=word_count)


# ---------------------------------------------------------------------------
# Chat response validation (anti-AI detection for autonomous mode)
# ---------------------------------------------------------------------------

# Phrases that scream "I am a bot"
_AI_CHAT_PATTERNS: list[str] = [
    # AI openers
    "отличный вопрос", "хороший вопрос", "интересный вопрос",
    "рад помочь", "рада помочь", "могу поделиться",
    "конечно!", "безусловно",
    # AI connectors
    "более того", "кроме того", "в частности",
    "стоит отметить", "стоит рассмотреть", "стоит обратить",
    "важно понимать", "необходимо учитывать",
    "рекомендую обратить внимание",
    "можно попробовать рассмотреть",
    # AI structure
    "во-первых", "во-вторых", "в-третьих",
    "с одной стороны", "с другой стороны",
    "в заключение", "подводя итог",
    # AI closers
    "надеюсь это поможет", "надеюсь помог",
    "удачи в", "успехов в", "желаю успехов",
    "если будут вопросы", "обращайтесь",
    # AI style
    "это действительно", "это серьёзная проблема",
    "это серьезная проблема",
    "на самом деле,", "в целом,",
    "существенно", "значительно", "безусловно",
    "оптимальный", "эффективный подход",
    "диверсификац",
]

# Soft patterns -- not blocked, but add +1 to ai_score (penalize, not ban)
_SOFT_AI_PATTERNS: list[str] = [
    "я тоже", "я уже", "у меня тоже", "у нас тоже", "так же делаю",
]

# Regex patterns for structural AI tells
_AI_REGEX_PATTERNS = [
    re.compile(r"^Да,\s", re.IGNORECASE),              # starts with "Да, ..."
    re.compile(r"^Конечно,\s", re.IGNORECASE),          # starts with "Конечно, ..."
    re.compile(r"\d\)\s.*\d\)\s", re.DOTALL),           # numbered lists: "1) ... 2) ..."
    re.compile(r"^\d+\.\s", re.MULTILINE),              # numbered lines: "1. ..."
    re.compile(r"^[-•]\s", re.MULTILINE),               # bullet lists
    re.compile(r"\*\*[^*]+\*\*"),                        # **bold** text
]


@dataclass
class ChatValidationResult:
    clean: bool
    ai_score: int         # 0 = clean, higher = more AI-like
    issues: list[str]
    word_count: int


def validate_chat_response(text: str) -> ChatValidationResult:
    """Check if a chat response sounds AI-generated.

    Returns ChatValidationResult with ai_score:
    - 0: looks human
    - 1-2: minor tells, acceptable
    - 3+: too AI-like, should regenerate or skip
    """
    issues: list[str] = []
    lower = text.lower()
    words = text.split()
    word_count = len(words)

    # Too long for a chat message
    if word_count > 50:
        issues.append(f"Слишком длинно для чата ({word_count} слов)")

    # Check AI phrases
    for pattern in _AI_CHAT_PATTERNS:
        if pattern in lower:
            issues.append(f"AI-паттерн: '{pattern}'")

    # Check regex patterns
    for regex in _AI_REGEX_PATTERNS:
        if regex.search(text):
            issues.append(f"AI-структура: {regex.pattern[:30]}")

    # Soft patterns -- minor penalty, not a hard block
    for pattern in _SOFT_AI_PATTERNS:
        if pattern in lower:
            issues.append(f"Частый бот-паттерн: '{pattern}'")

    # Long sentences (>15 words)
    sentences = re.split(r'[.!?\n]', text)
    long = [s.strip() for s in sentences if len(s.split()) > 15 and s.strip()]
    if long:
        issues.append(f"Длинное предложение ({len(long[0].split())} слов)")

    # Too many commas per sentence (AI loves subordinate clauses)
    for sent in sentences:
        sent = sent.strip()
        if sent and sent.count(",") >= 3 and len(sent.split()) <= 25:
            issues.append("Много запятых в одном предложении")
            break

    # Em-dashes (AI tell)
    if "--" in text or "\u2014" in text or "\u2013" in text:
        issues.append("Тире в тексте (-- или —)")

    # Exclamation marks
    if text.count("!") > 1:
        issues.append("Много восклицательных знаков")

    # Emoji overload
    emoji_matches = EMOJI_PATTERN.findall(text)
    if len(emoji_matches) > 2:
        issues.append(f"Много эмодзи ({len(emoji_matches)})")

    return ChatValidationResult(
        clean=len(issues) == 0,
        ai_score=len(issues),
        issues=issues,
        word_count=word_count,
    )
