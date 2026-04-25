"""Image generator for channel posts.

Generates 1080x1080 branded images for @otklicker, matching the brandbook
templates (see brandbook.pen: Post Images t1–t4).

Layout selection
----------------
Each `post_type` maps to exactly one template. Content signals
(numbers, quotes) no longer override the template. If you want a
"number" card, ask for `post_type="numbers"`; if you want a quote,
`post_type="hr_view"` (or legacy `personal_story`).

Templates
---------
- `number` (t1): Big accent number centered on the sunset gradient.
                 Kicker above, caption below. White logo chip top-left.
- `tip` (t2):    Cream card with gradient accent bar, bold title,
                 subtitle. Gradient logo chip bottom-left.
- `quote` (t3):  Sunset gradient frame around a cream inner card
                 carrying a quote and source attribution.
- `feature` (t4): Cream card with a gradient icon square at top,
                  "Новая фича" tag, feature name, description, and
                  a plain icon+wordmark row at the bottom.
- `update`:       Build-in-public variant of `tip` with a dark pill
                  kicker ("АПДЕЙТ · BUILD IN PUBLIC").

Typography
----------
Inter (500/700/800/900). Falls back to DejaVu/Arial if Inter is not
bundled under marketing-engine/data/fonts/.

Brand assets
------------
Real logo assets live in marketing-engine/data/brand/. Exported from
brandbook.pen. We paste them instead of redrawing synthetic chips.
"""

from __future__ import annotations

import re
import struct
from pathlib import Path
from typing import Iterable, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------

CANVAS_W = 1080
CANVAS_H = 1080

MARGIN = 80

# ---------------------------------------------------------------------------
# Brand palette (brandbook.pen, Закат-магента)
# ---------------------------------------------------------------------------

BG_CREAM = (255, 251, 240)       # #FFFBF0  — основной фон (tip/feature)
BG_PASTEL = (254, 243, 199)      # #FEF3C7  — пастельный фон (cards, quote inner)
BG_SAND = (255, 232, 176)        # #FFE8B0

TEXT_PRIMARY = (146, 64, 14)     # #92400E — основной текст на светлом (dark amber)
TEXT_SECONDARY = (180, 83, 9)    # #B45309 — вторичный текст
TEXT_ACCENT = (235, 63, 92)      # #EB3F5C — акцент "так нельзя"
TEXT_PINK = (219, 39, 119)       # #DB2777 — розовый для тегов
TEXT_AMBER = (255, 184, 0)       # #FFB800 — янтарь
TEXT_ON_GRADIENT = (255, 255, 255)        # белый на градиенте
TEXT_ON_GRADIENT_MUTED = (255, 245, 236)  # #FFF5EC
TEXT_WHITE = (255, 255, 255)

# Sunset gradient from brandbook (t1, t3, hero): amber → orange → red → pink
GRAD_SUNSET = (
    ((251, 191,  36), 0.00),    # #FBBF24
    ((249, 115,  22), 0.35),    # #F97316
    ((239,  68,  68), 0.70),    # #EF4444
    ((219,  39, 119), 1.00),    # #DB2777
)

# Warm 2-stop orange → pink (t2 logo chip, t4 icon, t2 accent bar)
GRAD_WARM = (
    ((249, 115,  22), 0.0),     # #F97316
    ((219,  39, 119), 1.0),     # #DB2777
)

BRAND_LABEL = "Откликер"
BRAND_HANDLE = "@otklicker_bot"

# Bundled font directory (prefer Inter when available)
FONTS_DIR = Path(__file__).resolve().parents[2] / "data" / "fonts"
BRAND_DIR = Path(__file__).resolve().parents[2] / "data" / "brand"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_post_image(
    headline: str,
    post_type: str = "",
    body_text: Optional[str] = None,
    accent_number: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """Generate a 1080x1080 branded post image.

    The template is chosen from `post_type`. `accent_number` is kept
    as a soft hint for the `number` template: if the chosen template
    is "number" and a number is provided, it is used verbatim.
    """
    from PIL import Image

    if output_path is None:
        import tempfile
        output_path = Path(tempfile.mktemp(suffix=".png"))

    body = (body_text or "").strip()
    headline = (headline or "").strip()

    layout = _choose_layout(post_type)

    if layout == "number":
        number = accent_number or _extract_primary_number(headline, body)
        if number:
            img = _render_number(headline, body, number, post_type=post_type)
        else:
            # Number card without a number is useless; fall back to tip.
            img = _render_tip(headline, body)

    elif layout == "quote":
        quote = _extract_quote(headline, body) or body or headline
        img = _render_quote(quote, headline, body)

    elif layout == "feature":
        img = _render_feature(headline, body)

    elif layout == "update":
        img = _render_update(headline, body)

    else:  # "tip" (default)
        img = _render_tip(headline, body)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", optimize=True)
    logger.info(
        "image_gen.saved",
        path=str(output_path),
        post_type=post_type,
        layout=layout,
    )
    return output_path


def extract_accent_number(text: str) -> Optional[str]:
    """Return a "punchy" figure (%, ×N, 75+, etc.) from `text`.

    Kept for back-compat. Prefer passing `post_type="numbers"` and
    letting the extractor find the number from the headline.
    """
    return _extract_primary_number("", text)


# ---------------------------------------------------------------------------
# Layout dispatcher — post_type drives the template. No sneaky overrides.
# ---------------------------------------------------------------------------


_TYPE_LAYOUT = {
    # откликер content types
    "numbers": "number",
    "hr_view": "quote",
    "build_in_public": "update",
    "resume_hack": "tip",
    "career_tip": "tip",
    "feature": "feature",
    # legacy / generic
    "data_numbers": "number",
    "personal_story": "quote",
    "case_study": "tip",
    "tips_howto": "tip",
    "hot_take": "tip",
    "news_reaction": "update",
    "behind_the_scenes": "update",
    "pain_solution": "tip",
    "compare": "tip",
    "case": "tip",
    "news": "update",
}


def _choose_layout(post_type: str) -> str:
    normalized = (post_type or "").strip().lower().replace(" ", "_").replace("/", "_")
    return _TYPE_LAYOUT.get(normalized, "tip")


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------


_NUMBER_PERCENT = re.compile(r"[+\-−]?\s?\d+(?:[.,]\d+)?\s?%")
_NUMBER_MULT = re.compile(r"[×x]\s?\d+")
_NUMBER_SUFFIX = re.compile(r"\d+(?:[.,]\d+)?\s?(?:К|M|B|млн|тыс)\+?", re.UNICODE)
_NUMBER_PLUS = re.compile(r"\d{2,}\+")
_NUMBER_BARE = re.compile(r"\b\d{2,4}\b")
# Single-digit numbers are only considered in the headline — the body often
# has them incidentally ("2-3 дня", "8 людей"), and they would crowd out
# a real headline figure.
_NUMBER_BARE_SHORT = re.compile(r"\b\d{1,4}\b")

_NUMBER_EXTRACTORS = (_NUMBER_PERCENT, _NUMBER_MULT, _NUMBER_SUFFIX, _NUMBER_PLUS, _NUMBER_BARE)

_BORING_NUMBERS = {"2024", "2025", "2026", "2027", "2028"}


def _extract_primary_number(headline: str, body: str) -> Optional[str]:
    """Return the most visually compelling number from headline or body.

    Rule: headline ALWAYS wins if it has any usable digit. Only fall
    through to the body if the headline has no digits at all. Inside
    each source, stronger visual formats (%, ×N, suffix, N+) outrank
    bare digits. Filters out calendar years.
    """
    # Pass 1: headline, strong extractors first, then any 1-4 digit number.
    if headline:
        for extractor in _NUMBER_EXTRACTORS:
            for match in extractor.finditer(headline):
                tok = match.group(0).replace(" ", "")
                if tok not in _BORING_NUMBERS:
                    return tok
        # fall-through: headline bare 1-digit
        for match in _NUMBER_BARE_SHORT.finditer(headline):
            tok = match.group(0)
            if tok not in _BORING_NUMBERS:
                return tok

    # Pass 2: body, but only for strong visual formats (not bare 1-digits).
    if body:
        for extractor in _NUMBER_EXTRACTORS:
            for match in extractor.finditer(body):
                tok = match.group(0).replace(" ", "")
                if tok not in _BORING_NUMBERS:
                    return tok
    return None


_QUOTE_REGEX = re.compile(r"[«\"]([^«»\"]{30,260})[»\"]")


def _extract_quote(headline: str, body: str) -> Optional[str]:
    """Return the longest substantial «…» (or '…') passage, if any."""
    candidates: list[str] = []
    for source in (body, headline):
        if not source:
            continue
        for match in _QUOTE_REGEX.finditer(source):
            q = match.group(1).strip()
            if 30 <= len(q) <= 260:
                candidates.append(q)
    if not candidates:
        return None
    candidates.sort(key=len, reverse=True)
    return candidates[0]


def _split_number_parts(token: str) -> tuple[str, str]:
    """Split '75%' into ('75', '%'); '×3' into ('×', '3'); '2400+' into ('2400', '+')."""
    m = re.match(r"^([×x+\-−]?)(\d+(?:[.,]\d+)?)([%KkКкМмkMB+]?)$", token)
    if not m:
        return token, ""
    prefix, digits, suffix = m.group(1), m.group(2), m.group(3)
    return prefix + digits, suffix


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def _render_number(headline: str, body: str, number: str, *, post_type: str):
    """t1 — huge number on sunset gradient. White chip top-left."""
    from PIL import ImageDraw

    img = _gradient_image(CANVAS_W, CANVAS_H, GRAD_SUNSET, rotation=135).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Top-left: real brand logo chip (white frosted pill with icon + text)
    _paste_logo_chip(img, x=MARGIN, y=MARGIN, style="white", height=76)

    # Kicker above the number
    kicker = _kicker_for_number(post_type, headline, body)
    if kicker:
        k_font = _load_font(30, weight="SemiBold", italic=True)
        draw.text((MARGIN, 260), kicker, font=k_font, fill=TEXT_ON_GRADIENT_MUTED)

    # The hero number
    core, suffix = _split_number_parts(number)
    display = core + suffix
    num_size = 460 if len(display) <= 2 else (380 if len(display) <= 3 else (300 if len(display) <= 5 else 220))
    num_font = _load_font(num_size, weight="Black")
    num_y = 320
    _draw_tracked(
        draw, display, (MARGIN, num_y), num_font,
        tracking=-num_size // 30, fill=TEXT_WHITE,
    )

    # Caption below the number (the original headline)
    caption_y = num_y + int(num_size * 0.90) + 32
    caption = _caption_line(headline)
    if caption:
        cap_font, cap_lines = _fit_wrap(
            draw, caption, CANVAS_W - MARGIN * 2,
            max_lines=3, sizes=(56, 48, 42, 38), weight="ExtraBold",
        )
        line_h = int(cap_font.size * 1.15)
        for i, line in enumerate(cap_lines):
            draw.text((MARGIN, caption_y + i * line_h), line, font=cap_font, fill=TEXT_ON_GRADIENT)
        caption_y += len(cap_lines) * line_h + 16

    # Italic tail (sub-caption)
    tail = _tail_line(post_type, headline, body)
    if tail and caption_y < CANVAS_H - 140:
        tail_font = _load_font(26, weight="SemiBold", italic=True)
        draw.text((MARGIN, caption_y), tail, font=tail_font, fill=TEXT_ON_GRADIENT_MUTED)

    # Bottom handle
    _draw_handle(draw, x=MARGIN, y=CANVAS_H - 70, fill=TEXT_ON_GRADIENT_MUTED)
    return img


def _render_tip(headline: str, body: str):
    """t2 — cream card with gradient accent bar + bold title + subtitle."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_CREAM)
    draw = ImageDraw.Draw(img)

    # Gradient accent bar top-left
    _paste_gradient_rect(
        img, x=MARGIN, y=160, w=288, h=18,
        stops=GRAD_WARM, rotation=90, radius=9,
    )

    # Headline
    title_width = CANVAS_W - MARGIN * 2
    title_font, title_lines = _fit_wrap(
        draw, headline, title_width,
        max_lines=5,
        sizes=(96, 84, 72, 64, 56, 48),
        weight="ExtraBold",
    )
    line_h = int(title_font.size * 1.12)
    title_y = 220
    for i, line in enumerate(title_lines):
        draw.text((MARGIN, title_y + i * line_h), line, font=title_font, fill=TEXT_PRIMARY)

    # Subtitle / body preview
    body_top = title_y + len(title_lines) * line_h + 40
    body_bottom = CANVAS_H - 220
    preview = _first_sentence(body, max_chars=220)
    if preview and body_top < body_bottom:
        max_lines = max(1, (body_bottom - body_top) // 50)
        body_font, body_lines = _fit_wrap(
            draw, preview, title_width,
            max_lines=min(5, max_lines),
            sizes=(36, 32, 28, 24),
            weight="Medium",
        )
        body_h = int(body_font.size * 1.35)
        for i, line in enumerate(body_lines):
            draw.text((MARGIN, body_top + i * body_h), line, font=body_font, fill=TEXT_SECONDARY)

    # Bottom-left: gradient brand chip + handle
    _paste_logo_chip(img, x=MARGIN, y=CANVAS_H - 176, style="gradient", height=72)
    handle_font = _load_font(22, weight="Medium")
    draw = ImageDraw.Draw(img)
    draw.text((MARGIN, CANVAS_H - 82), BRAND_HANDLE, font=handle_font, fill=TEXT_SECONDARY)
    return img


def _render_quote(quote: str, headline: str, body: str):
    """t3 — sunset frame around cream inner card with quote + source."""
    from PIL import Image, ImageDraw

    img = _gradient_image(CANVAS_W, CANVAS_H, GRAD_SUNSET, rotation=135).convert("RGB")

    pad = 16
    _rounded_fill(img, (pad, pad, CANVAS_W - pad, CANVAS_H - pad), radius=28, fill=BG_PASTEL)
    draw = ImageDraw.Draw(img)

    inner_l = pad + 56
    inner_r = CANVAS_W - pad - 56
    inner_w = inner_r - inner_l

    # Lay out quote text
    top_safe = pad + 220
    bottom_safe = CANVAS_H - pad - 220
    max_lines = max(2, (bottom_safe - top_safe) // 58)
    q_font, q_lines = _fit_wrap(
        draw, quote, inner_w,
        max_lines=min(9, max_lines),
        sizes=(58, 50, 44, 40, 36, 32),
        weight="Bold",
    )
    line_h = int(q_font.size * 1.28)
    block_h = line_h * len(q_lines)
    quote_y = top_safe + max(0, (bottom_safe - top_safe - block_h) // 2)

    # Opening curly quote mark
    q_mark_font = _load_font(180, weight="Black")
    draw.text((inner_l - 8, quote_y - 170), "“", font=q_mark_font, fill=(249, 115, 22))

    for i, line in enumerate(q_lines):
        draw.text((inner_l, quote_y + i * line_h), line, font=q_font, fill=TEXT_PRIMARY)

    # Source attribution (single line)
    src = _source_line(headline)
    if src:
        src_font = _load_font(24, weight="SemiBold")
        draw.text((inner_l, CANVAS_H - pad - 180), "— " + src, font=src_font, fill=TEXT_SECONDARY)

    # Brand chip bottom-left + handle
    _paste_logo_chip(img, x=inner_l, y=CANVAS_H - pad - 130, style="gradient", height=68)
    draw = ImageDraw.Draw(img)
    handle_font = _load_font(20, weight="Medium")
    draw.text((inner_l, CANVAS_H - pad - 56), BRAND_HANDLE, font=handle_font, fill=TEXT_SECONDARY)
    return img


def _render_feature(headline: str, body: str):
    """t4 — cream card with gradient icon square, tag, feature name, desc."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_CREAM)
    draw = ImageDraw.Draw(img)

    # Top: gradient icon square (using the brand mark png)
    icon_size = 132
    icon_path = BRAND_DIR / "logo_icon_gradient.png"
    if icon_path.exists():
        from PIL import Image as PILImage
        icon = PILImage.open(str(icon_path)).convert("RGBA")
        icon = icon.resize((icon_size, icon_size), PILImage.LANCZOS)
        img.paste(icon, (MARGIN, MARGIN + 56), icon)

    # "Новая фича" tag
    tag_font = _load_font(18, weight="Bold")
    draw.text((MARGIN, MARGIN + 56 + icon_size + 28), "Новая фича", font=tag_font, fill=TEXT_PINK)

    # Feature name
    name_y = MARGIN + 56 + icon_size + 28 + 40
    name_width = CANVAS_W - MARGIN * 2
    name_font, name_lines = _fit_wrap(
        draw, headline, name_width,
        max_lines=3,
        sizes=(72, 62, 52, 46),
        weight="ExtraBold",
    )
    line_h = int(name_font.size * 1.10)
    for i, line in enumerate(name_lines):
        draw.text((MARGIN, name_y + i * line_h), line, font=name_font, fill=TEXT_PRIMARY)

    # Description (first sentence of body)
    desc_top = name_y + len(name_lines) * line_h + 32
    desc_bottom = CANVAS_H - 180
    preview = _first_sentence(body, max_chars=240)
    if preview and desc_top < desc_bottom:
        max_lines = max(1, (desc_bottom - desc_top) // 44)
        d_font, d_lines = _fit_wrap(
            draw, preview, name_width,
            max_lines=min(5, max_lines),
            sizes=(30, 28, 26, 22),
            weight="Medium",
        )
        d_h = int(d_font.size * 1.4)
        for i, line in enumerate(d_lines):
            draw.text((MARGIN, desc_top + i * d_h), line, font=d_font, fill=TEXT_SECONDARY)

    # Bottom: plain icon + wordmark row (no chip), then handle
    _paste_logo_plain(img, x=MARGIN, y=CANVAS_H - 126, height=44)
    handle_font = _load_font(20, weight="Medium")
    draw = ImageDraw.Draw(img)
    draw.text((MARGIN, CANVAS_H - 72), BRAND_HANDLE, font=handle_font, fill=TEXT_SECONDARY)
    return img


def _render_update(headline: str, body: str):
    """Build-in-public update. Cream bg, dark pill kicker, bold title, preview."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_CREAM)
    draw = ImageDraw.Draw(img)

    # Thick sunset strip at the very top
    _paste_gradient_rect(img, 0, 0, CANVAS_W, 14, GRAD_SUNSET, rotation=90)

    # Dark pill kicker
    kicker_text = _update_kicker(headline)
    kicker_font = _load_font(18, weight="Bold")
    k_bbox = draw.textbbox((0, 0), kicker_text, font=kicker_font)
    k_w = k_bbox[2] - k_bbox[0]
    k_h = k_bbox[3] - k_bbox[1]
    kx, ky = MARGIN, 160
    pill_w = k_w + 36
    pill_h = k_h + 22
    _rounded_fill(img, (kx, ky, kx + pill_w, ky + pill_h), radius=pill_h // 2, fill=TEXT_PRIMARY)
    draw = ImageDraw.Draw(img)
    draw.text(
        (kx + 18, ky + (pill_h - k_h) // 2 - 3),
        kicker_text, font=kicker_font, fill=TEXT_AMBER,
    )

    # Headline
    title_y = ky + pill_h + 40
    title_font, title_lines = _fit_wrap(
        draw, headline, CANVAS_W - MARGIN * 2,
        max_lines=4,
        sizes=(92, 80, 68, 60, 52),
        weight="Black",
    )
    line_h = int(title_font.size * 1.05)
    for i, line in enumerate(title_lines):
        _draw_tracked(draw, line, (MARGIN, title_y + i * line_h), title_font, tracking=-2, fill=TEXT_PRIMARY)

    body_y = title_y + len(title_lines) * line_h + 40

    preview = _first_sentence(body, max_chars=220)
    if preview and body_y < CANVAS_H - 220:
        pv_font, pv_lines = _fit_wrap(
            draw, preview, CANVAS_W - MARGIN * 2,
            max_lines=max(1, (CANVAS_H - 220 - body_y) // 48),
            sizes=(34, 30, 26),
            weight="Medium",
        )
        pv_h = int(pv_font.size * 1.35)
        for i, line in enumerate(pv_lines):
            draw.text((MARGIN, body_y + i * pv_h), line, font=pv_font, fill=TEXT_SECONDARY)

    # Bottom: gradient brand chip + handle
    _paste_logo_chip(img, x=MARGIN, y=CANVAS_H - 160, style="gradient", height=68)
    handle_font = _load_font(22, weight="Medium")
    draw = ImageDraw.Draw(img)
    draw.text((MARGIN, CANVAS_H - 68), BRAND_HANDLE, font=handle_font, fill=TEXT_SECONDARY)
    return img


# ---------------------------------------------------------------------------
# Text helpers that turn post metadata into the small labels each layout needs
# ---------------------------------------------------------------------------


def _kicker_for_number(post_type: str, headline: str, body: str) -> Optional[str]:
    norm = (post_type or "").lower()
    if "numbers" in norm:
        return "в цифрах"
    if "resume" in norm:
        return "hh.ru"
    if "hr" in norm:
        return "по словам HR"
    words = _words(headline)
    if 2 <= len(words) <= 4:
        return " ".join(words).lower()
    return None


def _caption_line(headline: str) -> str:
    title = headline.strip()
    title = re.sub(r"^[«\"'“]?\s*", "", title)
    if len(title) > 72:
        m = re.split(r"[,:.–—]", title, maxsplit=1)
        title = m[0].strip()
    return title


def _tail_line(post_type: str, headline: str, body: str) -> Optional[str]:
    norm = (post_type or "").lower()
    if "numbers" in norm:
        return "медиана по рынку, 2026"
    if "resume" in norm:
        return "по данным ATS-мониторинга"
    return None


def _source_line(headline: str) -> str:
    title = headline.strip().strip("«»\"'")
    if len(title) > 80:
        title = title[:78] + "…"
    return title


def _update_kicker(headline: str) -> str:
    low = headline.lower()
    if "апдейт" in low or "обнов" in low:
        return "АПДЕЙТ · BUILD IN PUBLIC"
    if "запуск" in low or "релиз" in low:
        return "ЗАПУСК · BUILD IN PUBLIC"
    if "задерж" in low or "не готов" in low:
        return "ЧЕСТНО · BUILD IN PUBLIC"
    return "BUILD IN PUBLIC"


def _first_sentence(text: str, max_chars: int = 220) -> str:
    if not text:
        return ""
    text = text.strip()
    parts = re.split(r"(?<=[.!?…])\s+", text, maxsplit=1)
    first = parts[0].strip()
    if len(first) > max_chars:
        first = first[: max_chars - 1].rstrip() + "…"
    return first


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[\w]+", text, re.UNICODE) if len(w) > 2]


# ---------------------------------------------------------------------------
# Real-logo paste helpers (replace the old synthetic chip generator)
# ---------------------------------------------------------------------------


_LOGO_CACHE: dict[str, object] = {}


def _load_logo(filename: str):
    """Load a brand-asset PNG (cached, RGBA)."""
    from PIL import Image

    if filename in _LOGO_CACHE:
        return _LOGO_CACHE[filename]
    path = BRAND_DIR / filename
    if not path.exists():
        logger.warning("image_gen.logo_missing", path=str(path))
        return None
    img = Image.open(str(path)).convert("RGBA")
    _LOGO_CACHE[filename] = img
    return img


def _paste_logo_chip(base, x: int, y: int, *, style: str, height: int) -> None:
    """Paste a logo chip (icon + "Откликер") from brandbook assets.

    style="white":    semi-transparent white pill, brown text, red icon.
                      Meant for gradient backgrounds.
    style="gradient": orange→pink gradient pill, white text, white icon.
                      Meant for cream/pastel backgrounds.
    """
    from PIL import Image

    filename = "logo_chip_white.png" if style == "white" else "logo_chip_gradient.png"
    src = _load_logo(filename)
    if src is None:
        return

    ratio = height / src.height
    new_w = int(src.width * ratio)
    new_h = height
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    base.paste(resized, (x, y), resized)


def _paste_logo_plain(base, x: int, y: int, *, height: int) -> None:
    """Paste the plain horizontal logo (icon + 'Откликер') with no chip.

    Used at the bottom of feature cards (t4 style).
    """
    from PIL import Image

    src = _load_logo("logo_horizontal_large.png")
    if src is None:
        return

    ratio = height / src.height
    new_w = int(src.width * ratio)
    resized = src.resize((new_w, height), Image.LANCZOS)
    base.paste(resized, (x, y), resized)


def _draw_handle(draw, x: int, y: int, fill):
    font = _load_font(22, weight="Medium")
    draw.text((x, y), BRAND_HANDLE, font=font, fill=fill)


# ---------------------------------------------------------------------------
# Gradient and rounded-shape helpers
# ---------------------------------------------------------------------------


def _gradient_image(w: int, h: int, stops: Iterable, rotation: int = 135):
    from PIL import Image

    stops = tuple(stops)

    if rotation == 90:
        line_px = _precompute_line(stops, w)
        line_bytes = b"".join(struct.pack("BBB", *c) for c in line_px)
        buf = line_bytes * h
        return Image.frombytes("RGB", (w, h), buf)

    n = max(1, w + h - 1)
    line_px = _precompute_line(stops, n)
    long_buf = b"".join(struct.pack("BBB", *c) for c in line_px)
    rows = b"".join(long_buf[y * 3 : (y + w) * 3] for y in range(h))
    return Image.frombytes("RGB", (w, h), rows)


def _precompute_line(stops, n: int):
    stops = list(stops)
    positions = [s[1] for s in stops]
    colors = [s[0] for s in stops]
    last_idx = len(positions) - 1
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        if t <= positions[0]:
            out.append(colors[0])
            continue
        if t >= positions[-1]:
            out.append(colors[-1])
            continue
        for j in range(last_idx):
            p1, p2 = positions[j], positions[j + 1]
            if p1 <= t <= p2:
                span = p2 - p1
                a = (t - p1) / span if span > 0 else 0
                c1, c2 = colors[j], colors[j + 1]
                out.append((
                    int(c1[0] + (c2[0] - c1[0]) * a),
                    int(c1[1] + (c2[1] - c1[1]) * a),
                    int(c1[2] + (c2[2] - c1[2]) * a),
                ))
                break
    return out


def _paste_gradient_rect(base, x: int, y: int, w: int, h: int, stops, rotation=135, radius=0):
    from PIL import Image, ImageDraw

    rect = _gradient_image(w, h, stops, rotation=rotation)
    if radius > 0:
        rect = rect.convert("RGBA")
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, w - 1, h - 1], radius=radius, fill=255
        )
        base.paste(rect, (x, y), mask)
    else:
        base.paste(rect, (x, y))


def _rounded_fill(base, box: tuple[int, int, int, int], *, radius: int, fill):
    from PIL import Image, ImageDraw

    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=radius, fill=fill
    )
    base.paste(layer, (x1, y1), layer)


# ---------------------------------------------------------------------------
# Text layout helpers
# ---------------------------------------------------------------------------


def _fit_wrap(draw, text: str, max_width: int, *, max_lines: int, sizes, weight: str):
    text = text.strip()
    font = None
    lines: list[str] = [text]
    for size in sizes:
        font = _load_font(size, weight=weight)
        lines = _wrap_to_width(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    if font is None:
        font = _load_font(sizes[-1], weight=weight)
    trimmed = lines[: max_lines]
    if trimmed and len(lines) > max_lines:
        trimmed[-1] = _truncate_to_width(draw, trimmed[-1] + "…", font, max_width)
    return font, trimmed


def _wrap_to_width(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        trial = " ".join(current + [w]) if current else w
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
                current = [w]
            else:
                lines.append(w)
                current = []
    if current:
        lines.append(" ".join(current))
    return lines


def _truncate_to_width(draw, text: str, font, max_width: int) -> str:
    while text:
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return text
        text = text[:-2] + "…"
    return text


def _draw_tracked(draw, text: str, xy: tuple[int, int], font, *, tracking: int, fill):
    if tracking == 0:
        draw.text(xy, text, font=font, fill=fill)
        return
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), ch, font=font)
        x += (bbox[2] - bbox[0]) + tracking


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

_INTER_SUFFIX = {
    "Regular": "Regular",
    "Medium": "Medium",
    "SemiBold": "SemiBold",
    "Bold": "Bold",
    "ExtraBold": "ExtraBold",
    "Black": "Black",
}
_FALLBACK_BOLD = {"Bold", "ExtraBold", "SemiBold", "Black"}


def _load_font(size: int, *, weight: str = "Regular", italic: bool = False):
    from PIL import ImageFont

    suffix = _INTER_SUFFIX.get(weight, "Regular")
    if italic:
        suffix = suffix + "Italic" if suffix != "Regular" else "Italic"
    is_bold = weight in _FALLBACK_BOLD

    candidates: list[str] = [
        str(FONTS_DIR / f"Inter-{suffix}.ttf"),
        str(FONTS_DIR / f"Inter-{suffix}.otf"),
        f"/usr/share/fonts/truetype/inter/Inter-{suffix}.ttf",
        f"/usr/share/fonts/inter/Inter-{suffix}.ttf",
        f"/usr/local/share/fonts/Inter-{suffix}.ttf",
        str(Path.home() / ".fonts" / f"Inter-{suffix}.ttf"),
    ]

    if italic:
        non_italic = _INTER_SUFFIX.get(weight, "Regular")
        candidates += [
            str(FONTS_DIR / f"Inter-{non_italic}.ttf"),
            str(FONTS_DIR / f"Inter-{non_italic}.otf"),
        ]

    if weight == "Black":
        for fallback in ("ExtraBold", "Bold"):
            candidates += [str(FONTS_DIR / f"Inter-{fallback}.ttf")]

    if is_bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue

    return ImageFont.load_default()
