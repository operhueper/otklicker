# Brand tokens for otklicker.ru

Источники:
- `design_handoff_otklicker_landing/source/styles.css` (хайфайдельный референс — приоритет при расхождениях).
- `brandbook.pen` (отрисованный брендбук, 6 разделов: Core Spec, TG Covers, Post Images, Bot Avatar, Bold Typography, Stickers).
- `design_handoff_otklicker_landing/README.md` секция «Design Tokens».

Брендбук как файл переменных не использует (`get_variables` возвращает пустой объект) — все значения хардкоднуты в нодах. Сверка делалась по фактическим `fill`/`fontSize`/`fontWeight` нод.

---

## Colors (final, для tailwind.config.ts)

### Бренд (акценты градиента)
| Token | Hex | Источник | Использование |
|---|---|---|---|
| `amber` | `#FBBF24` | styles.css + brandbook (совпадает) | Brand gradient stop 0% |
| `orange` | `#F97316` | styles.css + brandbook (совпадает) | Brand gradient stop 33% |
| `red` | `#EF4444` | styles.css + brandbook (совпадает) | Brand gradient stop 66% |
| `pink` | `#DB2777` | styles.css + brandbook (совпадает) | Brand gradient stop 100% |

### Поверхности
| Token | Hex | Источник | Использование |
|---|---|---|---|
| `bg` | `#FAFAF9` | styles.css + brandbook | Основной светлый фон |
| `bg-pastel` | `#FEF3C7` | styles.css + brandbook | Пастельные секции (HowItWorks, FAQ, карточки в брендбуке) |
| `bg-pastel-2` | `#FDE68A` | styles.css | Усиленный пастельный (декор) |
| `bg-cream` | `#FFFBF0` | brandbook (секция Bold Typography, стикеры) | Альтернативная светлая поверхность |
| `bg-dark` | `#1C1917` | styles.css + brandbook (avatar dark) | Тёмные секции (Features, тёмный аватар) |
| `bg-dark-2` | `#292524` | styles.css | Карточки на тёмном фоне |
| `card` | `#FFFFFF` | styles.css + brandbook | Базовые карточки |
| `card-dark` | `#292524` | styles.css | Карточки на тёмном фоне |

### Текст
| Token | Hex | Источник | Использование |
|---|---|---|---|
| `text` | `#78350F` | styles.css + brandbook | Основной body-текст |
| `text-heading` | `#92400E` | styles.css + brandbook | H1/H2/H3 |
| `text-sub` | `#B45309` | styles.css + brandbook | Подписи, eyebrow, secondary |
| `text-muted` | `#A8A29E` | styles.css | Hint, helper |
| `text-on-dark` | `#FEF3C7` | styles.css | Текст на тёмном фоне |
| `text-on-dark-sub` | `#FBBF24` | styles.css | Subtext на тёмном фоне |

### Линии
| Token | RGBA | Источник |
|---|---|---|
| `line` | `rgba(146, 64, 14, 0.12)` | styles.css |
| `line-strong` | `rgba(146, 64, 14, 0.22)` | styles.css |
| `line-dark` | `rgba(254, 243, 199, 0.12)` | styles.css |

### Дополнительные акценты из брендбука (раздел Bold Typography / Stickers)

Используются только в маркетинговых ассетах (TG-канал, посты, стикеры), **не уходят в Tailwind основного конфига**. Остаются как локальные значения в соответствующих ассетах:

- `#6D2B13` — тёмно-коричневый (заголовки в Bold Typography)
- `#8A3A10` — насыщенный коричневый (подзаголовки)
- `#FF6A2A`, `#E6227A`, `#EB3F5C` — альтернативные оранжево-розовые акценты в постах
- `#FFB800`, `#FFE8B0` — янтарные акценты в стикер-паке
- `#FDE68A` — обводка карточек

---

## Brand gradient

Базовый градиент (135°, 4 stops):

```css
--brand-gradient: linear-gradient(135deg, #FBBF24 0%, #F97316 33%, #EF4444 66%, #DB2777 100%);
```

Три пресета (через body-классы в styles.css строки 83–85):

| Preset | from | mid1 | mid2 | to |
|---|---|---|---|---|
| `subtle` | `#FCD34D` | `#FBBF24` | `#F59E0B` | `#F97316` |
| `normal` (default) | `#FBBF24` | `#F97316` | `#EF4444` | `#DB2777` |
| `intense` | `#FDE047` | `#F97316` | `#DC2626` | `#BE185D` |

В Tailwind зашить только `normal` через `backgroundImage.brand-gradient`. Пресеты `subtle` / `intense` — позже как утилитарные классы или CSS-переменные, **только если понадобятся вариации** (в текущем лендинге не используются вне tweaks-панели, которая в прод не идёт).

---

## Typography

### Family
- **Inter** (Google Fonts), weights `400 / 500 / 600 / 700 / 800 / 900`
- В Next.js — `next/font/google` с локальной поставкой (subset cyrillic+latin)
- Fallback: `-apple-system, BlinkMacSystemFont, sans-serif`
- Базовый размер `16px`, line-height `1.55`
- Заголовки: `letter-spacing: -0.02em` (h1: `-0.03em`)
- Числовые блоки (цены, счётчики): `font-variant-numeric: tabular-nums`
- Eyebrow: `uppercase`, `letter-spacing: 0.02–0.04em`, weight `600`

### Size scale (из styles.css `clamp` + брендбук)

| Token | Desktop | Mobile (≤720px) | Weight | Источник |
|---|---|---|---|---|
| `h1` | 80 | 44 | 800 | styles.css clamp(44, 8vw, 80) |
| `h2` | 52 | 32 | 800 | styles.css `.section-head h2` clamp(32, 4vw, 52) |
| `h3` | 44 | 30 | 800 | styles.css |
| `h-display` | 64 | — | 800–900 | brandbook (Bold Typo, Bot Avatar header) |
| `h-card` | 32 / 24 | — | 700–800 | brandbook (типо-сетка row1/row2) |
| `lead` | 19 | 17 | 500 | styles.css |
| `body` | 16 | 15 | 500 | styles.css + brandbook |
| `small` | 13–14 | 12–13 | 400–500 | styles.css |
| `caption` | 12 | 12 | 400 | brandbook (type row 4) |
| `eyebrow` | 12 | 12 | 600–700 | styles.css `.eyebrow` (uppercase) |

---

## Radii

| Token | px | Источник |
|---|---|---|
| `xs` | 8 | styles.css `--r-xs` |
| `sm` | 12 | styles.css `--r-sm` |
| `md` | 18 | styles.css `--r-md` |
| `lg` | 24 | styles.css `--r-lg` (используется в брендбуке для всех больших карточек) |
| `xl` | 32 | styles.css `--r-xl` |
| `pill` | 999 | styles.css (.btn, .eyebrow) |

В брендбуке также встречаются специфичные радиусы в карточках логотипа (14, 20, 22, 28, 36) — они должны выводиться из `lg` ± контекст, не нужно отдельных токенов.

---

## Shadows

| Token | Value | Источник |
|---|---|---|
| `sm` | `0 1px 2px rgba(120,53,15,.06), 0 2px 6px rgba(120,53,15,.04)` | styles.css `--shadow-sm` |
| `md` | `0 4px 14px rgba(120,53,15,.08), 0 12px 32px rgba(120,53,15,.06)` | styles.css `--shadow-md` |
| `lg` | `0 12px 40px rgba(120,53,15,.12), 0 30px 80px rgba(120,53,15,.08)` | styles.css `--shadow-lg` |
| `brand` | `0 20px 50px rgba(219,39,119,.22), 0 6px 18px rgba(249,115,22,.24)` | styles.css `--shadow-brand` |
| `brand-hover` | `0 24px 60px rgba(219,39,119,.30), 0 8px 22px rgba(249,115,22,.30)` | styles.css `.btn-primary:hover` |

Обратить внимание: цвет ru-теней замешан на `text-heading` (`#78350F` ≈ `rgba(120,53,15)`) — это намеренно, тёплая тень в палитре бренда.

---

## Spacing

Жёсткой 4-/8-pt шкалы нет. Фактически используется (по styles.css и брендбуку):

`4 · 6 · 8 · 10 · 12 · 14 · 16 · 18 · 20 · 22 · 24 · 28 · 32 · 36 · 40 · 48 · 56 · 60 · 64 · 80 · 96 · 120` px

В Tailwind дефолтная шкала покрывает большинство. Добавить только нестандартные кастомы при необходимости (`22 · 28 · 36 · 56 · 60 · 120`).

### Layout-константы
- Container `max-width: 1240px`, `padding-x: 32px` (desktop) / `20px` (mobile, ≤720px)
- Section padding: `96 0` (desktop) / `64 0` (mobile)

---

## Brandbook → export plan (для Phase 4)

Все нижние ID — стабильные node IDs из `brandbook.pen`. Использовать с `mcp__pencil__export_nodes(filePath=brandbook.pen, nodeIds=[...], format="png|svg", outputDir=...)`.

| Asset | Pencil node ID | Что это | Export size / format |
|---|---|---|---|
| **BrandMark (основной знак)** | `vYOy1` | Header-icon из шапки Core Spec, 88×88, gradient 135°, cursor inside | PNG 192×192 + 512×512, SVG (если получится через export) |
| **BrandMark (большой, основной)** | `cIcTM` | Из карточки «Основной знак», 100×100, with shadow | PNG 512×512, для favicon source |
| **BrandMark (icon-only, крупный)** | `xez6k` | Из карточки «Только иконка», 140×140, gradient 135° | PNG 1024×1024 (для og-image / app icon) |
| **BrandLockup (горизонтальный)** | `7Bui1` | Mark 96×96 + текст «Откликер» 48px/800 | SVG, PNG (transparent bg) |
| **BrandLockup (вертикальный, компактный)** | `GVKID` | Mark 68×68 + текст «Откликер» 22px/800 | SVG |
| **BrandLockup (полный, с подзаголовком)** | `pqERl` | Mark 100×100 + «Откликер» 32px + «Найди работу мечты» 14px | PNG 2x для marketing |
| **BrandLockup (моно, тёмный)** | `OG2G1` | Mark `#92400E` + текст | SVG (для печати/моно) |
| **BrandLockup (инверсия, на градиенте)** | `taG4b` | Mark белый + текст белый | PNG (сайдкейс — например, на тёмном email-баннере) |
| **Bot Avatar (основной)** | `U2B8J` | Круг 700×700 с градиентом 135°, cursor inside, glow | PNG 512×512 для @otklicker_bot |
| **Bot Avatar (пастельный)** | `uBEre` | Круг с заливкой `#FEF3C7`, cursor с градиентом | PNG 512×512 (резерв) |
| **Bot Avatar (тёмный)** | `wBKpu` | Круг `#1C1917`, cursor с градиентом | PNG 512×512 (для тёмных кампаний) |
| **Bot Avatar (светлый, обводка градиентом)** | `AAZou` | Круг белый, cursor с градиентом, обводка градиентом | PNG 512×512 (для встраивания в посты) |

### Ассеты, которые ещё могут понадобиться (опционально, после консультации с пользователем)

- **TG-обложки канала** (1280×640): `BRhwP` (заглавная, gradient), `GdC9E` (пастельная), `GOQe4` (анонс беты), `LhMPv` (минимал)
- **Post-templates** (1080×1080 или 1080×1920): фрейм `JwbTy` содержит готовые квадратные и вертикальные шаблоны (без отдельных стабильных ID на каждый — нужен повторный осмотр)
- **OG-image** для сайта (1200×630): отдельной готовой ноды в брендбуке нет — придётся либо сверстать в коде, либо сделать в Pencil отдельным шагом

---

## Расхождения брендбук ↔ styles.css

**Ключевые токены (палитра, поверхности, текст, тени, радиусы, типо-семейство): расхождений не обнаружено.** Брендбук и `styles.css` используют одни и те же hex-значения для всех 11 базовых цветов (`#FBBF24`, `#F97316`, `#EF4444`, `#DB2777`, `#FAFAF9`, `#FEF3C7`, `#1C1917`, `#78350F`, `#92400E`, `#B45309`, `#FFFFFF`).

**Дополнительные значения, которых нет в `styles.css`** (брендбук добавляет, лендинг не использует):
- `#FFFBF0` — кремовый фон в Bold Typography / Stickers секциях
- `#6D2B13`, `#8A3A10` — тёмно-коричневые для специальных постов
- `#FF6A2A`, `#E6227A`, `#EB3F5C` — альтернативные акценты в постах
- `#FFB800`, `#FFE8B0`, `#FDE68A` — янтарные обводки

Эти значения — **вне scope лендинга**. Они нужны только для маркетинг-ассетов (TG-каналы, стикеры) и не должны попадать в `tailwind.config.ts` основного сайта. Если позже понадобятся — отдельным конфигом `marketing-tokens.ts` или CSS-файлом.

**Типографика:** в брендбуке используются крупные размеры (180, 220 px в Bold Typography hero) — это локально для постов, не для лендинга. Шкала лендинга (`styles.css clamp` + table в README) — авторитетная.

**Шрифты Inter:** обе стороны используют один и тот же стек, weights 400–900.

**Итог:** для лендинга `styles.css` self-sufficient. Брендбук остаётся источником ассетов (логотипы, аватар) и маркетинг-стиля.

---

## Tailwind config snippet (preview)

```ts
// tailwind.config.ts — theme.extend
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Brand accents
        amber:  '#FBBF24',
        orange: '#F97316',
        red:    '#EF4444',
        pink:   '#DB2777',
        // Surfaces
        bg:           '#FAFAF9',
        'bg-pastel':  '#FEF3C7',
        'bg-pastel-2':'#FDE68A',
        'bg-dark':    '#1C1917',
        'bg-dark-2':  '#292524',
        card:         '#FFFFFF',
        'card-dark':  '#292524',
        // Text
        text:              '#78350F',
        'text-heading':    '#92400E',
        'text-sub':        '#B45309',
        'text-muted':      '#A8A29E',
        'text-on-dark':    '#FEF3C7',
        'text-on-dark-sub':'#FBBF24',
      },
      fontFamily: {
        sans: ['var(--font-inter)', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      fontSize: {
        // (можно оставить дефолтную шкалу Tailwind, либо задать кастомную)
        'h1': ['clamp(44px, 8vw, 80px)', { lineHeight: '1.05', letterSpacing: '-0.03em', fontWeight: '800' }],
        'h2': ['clamp(32px, 4vw, 52px)', { lineHeight: '1.05', letterSpacing: '-0.02em', fontWeight: '800' }],
        'h3': ['clamp(30px, 3.5vw, 44px)', { lineHeight: '1.1',  letterSpacing: '-0.02em', fontWeight: '800' }],
        'lead':   ['19px', { lineHeight: '1.55', fontWeight: '500' }],
        'body':   ['16px', { lineHeight: '1.55', fontWeight: '500' }],
      },
      borderRadius: {
        xs: '8px',
        sm: '12px',
        md: '18px',
        lg: '24px',
        xl: '32px',
        // pill: используем встроенный 'full' (= 9999px)
      },
      boxShadow: {
        sm: '0 1px 2px rgba(120,53,15,0.06), 0 2px 6px rgba(120,53,15,0.04)',
        md: '0 4px 14px rgba(120,53,15,0.08), 0 12px 32px rgba(120,53,15,0.06)',
        lg: '0 12px 40px rgba(120,53,15,0.12), 0 30px 80px rgba(120,53,15,0.08)',
        brand:       '0 20px 50px rgba(219,39,119,0.22), 0 6px 18px rgba(249,115,22,0.24)',
        'brand-hover':'0 24px 60px rgba(219,39,119,0.30), 0 8px 22px rgba(249,115,22,0.30)',
      },
      backgroundImage: {
        'brand-gradient':         'linear-gradient(135deg, #FBBF24 0%, #F97316 33%, #EF4444 66%, #DB2777 100%)',
        'brand-gradient-subtle':  'linear-gradient(135deg, #FCD34D 0%, #FBBF24 33%, #F59E0B 66%, #F97316 100%)',
        'brand-gradient-intense': 'linear-gradient(135deg, #FDE047 0%, #F97316 33%, #DC2626 66%, #BE185D 100%)',
      },
      borderColor: {
        line:       'rgba(146, 64, 14, 0.12)',
        'line-strong': 'rgba(146, 64, 14, 0.22)',
        'line-dark':  'rgba(254, 243, 199, 0.12)',
      },
      maxWidth: {
        container: '1240px',
      },
      spacing: {
        // дополнения к дефолтной шкале (если нужны)
        22: '5.5rem',   // 88px
        30: '7.5rem',   // 120px
      },
    },
  },
  plugins: [],
};

export default config;
```

### Глобальные CSS-переменные (для случаев, когда Tailwind utility не подходит)

```css
/* app/globals.css — дополнить, не заменять Tailwind */
:root {
  --brand-gradient: linear-gradient(135deg, #FBBF24 0%, #F97316 33%, #EF4444 66%, #DB2777 100%);
  --shadow-brand: 0 20px 50px rgba(219, 39, 119, 0.22), 0 6px 18px rgba(249, 115, 22, 0.24);
}
```

---

## Открытые вопросы / следующие шаги

1. **OG-image (1200×630).** Готовой ноды в брендбуке нет. Решение:
   - Вариант A: сделать отдельным шагом в Pencil поверх `BRhwP` (TG cover, 1280×640) — обрезать/адаптировать.
   - Вариант B: сверстать React-компонент `<OGImage>` через `next/og` на основе токенов из этого документа.
2. **Favicon.** Источник — `cIcTM` (BrandMark с тенью). Экспорт PNG 32/192/512 + ICO в Phase 4.
3. **Тема (dark mode).** На лендинге используется только в Features-секции (точечно). Полноценный toggle сайт-уровня — НЕ в этой Phase 0.1b. Если понадобится позже — переработать `tailwind.config.ts` с `darkMode: 'class'` и продублировать токены под `.theme-dark`.
4. **Иконки.** В прототипе нарисованы вручную в `icons.jsx`. План — заменить на `lucide-react` (мэппинг в `README.md` строки 320–331). Логотип-курсор остаётся отдельным SVG-ассетом (экспорт из брендбука).
5. **Cyrillic subset Inter.** При подключении через `next/font/google` явно указать `subsets: ['latin', 'cyrillic']`.
