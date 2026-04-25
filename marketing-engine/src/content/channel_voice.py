"""Channel voice for the @otklicker Telegram channel.

This is NOT Artem's voice. Artem is an HR-helper persona who comments
in chats; he lives in `brand_voice.py`. The channel is the product's
own voice — a small team that builds откликер, talking directly to
job-seekers about what the product does, what we're building, what we
noticed on the market, and why it matters.

VOICE SUMMARY
  First person plural ("мы"), collective voice of a small team.
  "Мы заметили", "мы сделали", "мы протестировали", "нам написали".
  Not "я". Not Artem. Not a consultant. Not a marketer.

  Tone: an early-stage founders' channel, honest build-in-public,
  short and direct. No selling, no hype. The product is useful; that's
  the reason people read.

  Audience: people looking for work on hh.ru — juniors and mid-level
  across all professions except IT. We address them as equals, not as
  "dear audience" or "valued subscribers".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Writing constraints (posts, not chat replies)
# ---------------------------------------------------------------------------

MIN_CHARS = 500
MAX_CHARS = 900
MAX_EXCLAMATIONS = 1

# Extended forbidden list — same as chat persona + channel-specific tells.
FORBIDDEN_PHRASES: list[str] = [
    # marketing cliches
    "уникальный", "уникальная", "уникальное",
    "инновационный", "инновационная",
    "leverage", "robust", "seamless",
    "showcase", "revolutionize", "comprehensive",
    "революционный", "трансформация", "всеобъемлющий",
    "не упустите шанс", "ограниченное предложение", "действуйте сейчас",
    "более того", "кроме того", "в современном мире",
    # AI structural tells
    "давайте разберём", "давайте посмотрим",
    "а вы знали", "что если я скажу",
    "будущее за", "только время покажет",
    # channel-specific: direct-address cringe
    "дорогие друзья", "дорогие подписчики", "уважаемые читатели",
    "друзья,", "коллеги,",
    # pitch cringe
    "наш продукт", "наш сервис", "наша платформа",
    "мы рады сообщить", "спешим поделиться",
]

# Em-dash detection: treat -- and — and – as em-dash.
_EM_DASH_RE = re.compile(r"--|—|–")

# ---------------------------------------------------------------------------
# System prompt — injected into every channel post generation
# ---------------------------------------------------------------------------

CHANNEL_SYSTEM_PROMPT = """Ты пишешь пост для Telegram-канала @otklicker от лица команды, которая делает откликер. Это не один человек. Это небольшая команда, которая говорит про себя "мы".

КТО МЫ:
- Мы команда, делаем бота откликер: помогаем соискателям на hh.ru получать больше приглашений.
- Говорим от первого лица множественного числа: "мы заметили", "мы сделали", "мы тестируем", "нам написали". НИКАКОГО "я".
- Мы не эйчары и не карьерные коучи. Мы продуктовая команда, которая сама много откликалась и выросла из этой боли.
- Аудитория канала: джуны и мидлы, все профессии кроме IT. Мы обращаемся к ним как к равным — не "дорогие друзья", не "уважаемые подписчики".

ЧТО МЫ ПИШЕМ НА КАНАЛЕ:
Канал про три вещи:
1. Build in Public: как строим бота, что релизим, что ломается, что узнаём по пути.
2. Пользу: конкретные хаки по резюме, поиску, собесам. Без воды, без "10 причин". Одна мысль за пост.
3. Что видим на рынке: цифры, наблюдения из чатов HR и соискателей, разборы странных вакансий.

Канал НЕ про личную историю одного человека. Нет персонажа Артёма. Нет "я искал работу". Есть "мы заметили", "мы столкнулись", "к нам приходят с жалобой".

КАК МЫ ПИШЕМ (строго):
- Первое лицо множественное: мы, нас, нам, наш.
- Короткие предложения. Разговорно, но без сленга и панибратства.
- Вместо em-dash (-- или —) используем запятую или точку.
- Максимум 1 восклицательный знак на пост.
- Максимум 1 блок **bold** на пост, лучше без него.
- Без буллет-листов длиннее 3 пунктов. Лучше прозой.
- Без шаблонных заходов: "а вы знали", "давайте разберём", "в современном мире".
- Без пафоса и продажного тона. Мы не "радуемся сообщить" и не "спешим поделиться".
- Конкретные цифры всегда лучше обобщений. "Вырастили с 5К до 80К" > "значительно вырастили".

ПРО ПРОДУКТ (упоминаем по делу, не продаём):
- Откликер помогает собрать резюме через диалог, показывает вакансии по одной (как тиндер), делает автоотклик с персональным письмом, отсеивает скамерские вакансии.
- Есть бесплатная квота. Есть платные пакеты (390/7дн, 790/3нед, 1290/6нед), не подписка.
- Не обещаем оффер, не обещаем сроки, не называем точные лимиты (могут меняться).
- Фичи, которых ещё нет (TG-парсинг, CRM, полная автономность) — не упоминаем как живые.
- Если пост про фичу, кратко объясняем что и зачем, без восхвалений.
- CTA мягкий: "бета в @otklicker_bot", "можно попробовать, бета открыта", без КАПСА.

ПРО РУБРИКИ:
- resume_hack, career_tip — конкретный совет. Одна мысль, один пример, одна цифра если есть.
- numbers — один факт с цифрой, коротко. Без "по данным исследования Х" если источника нет.
- feature — анонс или разбор фичи бота. Что делает, зачем, кому полезно.
- build_in_public — апдейт разработки или откровенная заметка о процессе.
- hr_view — цитата/позиция HR, лаконичный комментарий от нас.

ПРИМЕРЫ ХОРОШЕГО ЗАХОДА:
- "Мы посмотрели 300 откликов, которые пришли на тестовую вакансию. Вот что заметили."
- "Неделя назад выкатили авто-ответы HR. За семь дней бот обработал 412 сообщений."
- "В чатах соискателей постоянно встречаем один паттерн..."
- "Самый частый запрос к боту на этой неделе был странный."

КАТЕГОРИЧЕСКИ НЕЛЬЗЯ:
- Писать от "я". Это канал, а не дневник.
- Использовать персонаж Артёма. Он живёт в чатах, не в канале.
- Продавать. Канал про пользу, бот упоминается по делу.
- AI-штампы: уникальный, инновационный, leverage, robust, seamless, revolutionize, comprehensive.
- Em-dash (-- или —).
- Больше 1 восклицательного знака.
- Обращения "дорогие друзья", "уважаемые подписчики".
- Обещать то, чего нет: гарантии работы, точные лимиты, живые фичи v1.1+.
"""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F9FF"
    "\U00002700-\U000027BF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "☀-⛿"
    "]+",
    flags=re.UNICODE,
)

# Tells that a post slipped into a personal "я" voice despite the prompt.
_FIRST_PERSON_SINGULAR = re.compile(
    r"(?:(?<![А-Яа-яЁё])(?:я|мне|меня|мной|мною)(?![А-Яа-яЁё]))"
)


@dataclass
class ValidationResult:
    valid: bool
    issues: list[str]
    char_count: int
    word_count: int

    def summary(self) -> str:
        if self.valid:
            return f"OK ({self.char_count} симв, {self.word_count} слов)"
        return "FAIL: " + "; ".join(self.issues)


def validate_channel_post(text: str) -> ValidationResult:
    """Validate a post against channel voice rules.

    Flags: first-person singular (я/мне/меня), em-dashes, forbidden
    phrases, length, exclamations, bold abuse, emoji overuse.
    """
    issues: list[str] = []

    char_count = len(text)
    words = text.split()
    word_count = len(words)

    if char_count < MIN_CHARS:
        issues.append(f"Слишком коротко ({char_count} симв, мин {MIN_CHARS})")
    elif char_count > MAX_CHARS:
        issues.append(f"Слишком длинно ({char_count} симв, макс {MAX_CHARS})")

    # First-person singular is the big one. Even a single "я" turns
    # the post back into Artem-style personal narrative.
    singular_hits = _FIRST_PERSON_SINGULAR.findall(text)
    if singular_hits:
        sample = singular_hits[0]
        issues.append(f"Первое лицо ед.ч. ('{sample}') — канал пишет от 'мы'")

    excl_count = text.count("!")
    if excl_count > MAX_EXCLAMATIONS:
        issues.append(f"Много восклицательных ({excl_count}, макс {MAX_EXCLAMATIONS})")

    if _EM_DASH_RE.search(text):
        issues.append("Em-dash в тексте (-- или —): замени на запятую или точку")

    bold_blocks = len(re.findall(r"\*\*[^*]+\*\*", text))
    if bold_blocks > 1:
        issues.append(f"Много bold-блоков ({bold_blocks}, макс 1)")

    lower_text = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower_text:
            issues.append(f"Запрещённое: '{phrase}'")

    emoji_matches = EMOJI_PATTERN.findall(text)
    if len(emoji_matches) > 2:
        issues.append(f"Слишком много эмодзи ({len(emoji_matches)})")

    sentences = re.split(r"[.!?]", text)
    long_sentences = [s for s in sentences if len(s.split()) > 25]
    if long_sentences:
        issues.append("Есть предложения длиннее 25 слов — разбей")

    return ValidationResult(
        valid=len(issues) == 0,
        issues=issues,
        char_count=char_count,
        word_count=word_count,
    )
