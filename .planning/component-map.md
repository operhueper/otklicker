# Карта компонентов Откликер лендинга | Phase 0.1

**Статус**: Разведка завершена. Исходная архитектура: inline Babel React UMD.
**Целевая архитектура**: Next.js 14 + TypeScript + Tailwind CSS.

---

## 1. Структура проекта

```
design_handoff_otklicker_landing/source/
├── index.html           # UMD bootstrap + script загрузка
├── app.jsx              # Root App, диспетчер секций, tweaks логика
├── styles.css           # CSS переменные + утилиты (grid, flex, btn, animation)
├── promo.md             # Маркетинг-материалы (не тащим)
├── tweaks-panel.jsx     # UI для дизайнер-твиков (НЕ тащим в Next)
└── components/
    ├── icons.jsx        # Icon объект, BrandMark, BrandLockup
    ├── telegram.jsx     # TelegramPhone (Telegram mockup)
    ├── real-bot.jsx     # RealBotScreen (реальный вид бота) + 5 экранов
    ├── hero.jsx         # Nav, Hero, HeroChat (живой чат-демо)
    ├── hero-swipe.jsx   # HeroSwipe (карточки свайпа, SAMPLE_JOBS)
    ├── sections.jsx     # HowItWorks, Features (с RealBotScreen)
    ├── more-sections.jsx # Pricing, PriceCard, FAQ, FinalCTA, Footer
    ├── speed.jsx        # SpeedSection (гонка 14 часов)
    └── speed.v1.jsx     # [DEPRECATED] — старая версия (НЕ тащить)

marketing-engine/       # Python Telegram marketing bot (отдельно)
├── src/
│   ├── main.py          # Основной loop
│   ├── admin_bot.py      # Admin интерфейс
│   └── config.py         # Конфиг
├── data/                # JSON с паттернами, чатами, голосом бренда
├── data/brand/          # PNG логотипы, иконки
└── pyproject.toml       # Deps
```

---

## 2. Полный список компонентов React

### 2.1 Global-шеринг через `Object.assign(window, {...})`

**КРИТИЧНО**: Все экспорты через `Object.assign(window, {...})` — это надо переписать на ES-модули!

| Файл | Компоненты | Тип | Глобал-шеринг |
|------|-----------|------|---------------|
| `tweaks-panel.jsx` | `useTweaks`, `TweaksPanel`, `TweakSection`, `TweakRow`, `TweakSlider`, `TweakToggle`, `TweakRadio`, `TweakSelect`, `TweakText`, `TweakNumber`, `TweakColor`, `TweakButton` | hooks + UI | ✅ YES (line 415) |
| `icons.jsx` | `Icon` (object), `BrandMark`, `BrandLockup` | components | ✅ YES (line 120) |
| `telegram.jsx` | `TelegramPhone` | component | ✅ YES (line 300) |
| `real-bot.jsx` | `RealBotScreen`, `ONBOARDING_SCREEN`, `MAIN_MENU_SCREEN`, `HH_AUTH_SCREEN`, `HH_PANEL_SCREEN`, `VACANCY_SCREEN` | component + data | ✅ YES (line 237) |
| `hero-swipe.jsx` | `HeroSwipe`, `JobCard`, `SAMPLE_JOBS` | component + data | ❌ NO |
| `hero.jsx` | `Nav`, `Hero`, `HeroChat`, `HERO_CHAT_JOBS` | components + data | ✅ YES (implicit, глобал-зависимость) |
| `sections.jsx` | `HowItWorks`, `Features` | components | ✅ YES (line 205) |
| `more-sections.jsx` | `Pricing`, `PriceCard`, `FAQ`, `FinalCTA`, `Footer` | components | ✅ YES (line 290) |
| `speed.jsx` | `SpeedSection`, `RaceTrack`, `Lane`, `TimeAxis`, `Playhead`, `StatTile`, `FiltersTile` | components | ❌ NO |

### 2.2 Полный реестр компонентов по файлам

#### `tweaks-panel.jsx` (432 строки)
**Назначение**: Реализация drag-floatable tweaks панели для дизайнеров. Сложная UX с ResizeObserver.

**Компоненты** (named exports через window):
- `useTweaks(defaults)` — hook: state + postMessage к родителю
- `TweaksPanel({ title, children })` — floating panel с dragging, resize-clamping
- `TweakSection`, `TweakRow` — layout helpers
- `TweakSlider`, `TweakToggle`, `TweakRadio`, `TweakSelect`, `TweakText`, `TweakNumber`, `TweakColor`, `TweakButton` — form controls

**useState/useEffect**:
- `useTweaks`: стейт values
- `TweaksPanel`: open, dragRef, offsetRef, ResizeObserver + mouse events
- `TweakRadio`: dragging, valueRef для closure

**Inline styles**: МНОГО (встроенная CSS-in-JS для панели, ~100 строк)

**Решение Phase 1**: НЕ ТАЩИТЬ в Next.js. Это dev-инструмент для дизайнера. На прод-сайт не нужна.

---

#### `icons.jsx` (121 строка)
**Назначение**: Lucide-style SVG иконки (inline) + брендовые компоненты.

**Компоненты**:
- `Icon` (object): MousePointerClick, Send, Check, X, Heart, Sparkles, MessageSquare, Layers, Zap, Clock, TrendingUp, Shield, ChevronDown, ChevronRight, ArrowRight, Telegram, Zap2, Plus, Minus, File, Users, Building, MapPin, Coins — всего ~22 иконки
- `BrandMark({ size, iconSize })` — gradient box с иконкой (wrapper для Icon.MousePointerClick)
- `BrandLockup({ size })` — logo + текст "Откликер · найди работу мечты"

**Inline styles**: МАЛО (flex, sizes via sizeMap)

**Аналоги lucide-react**:
- MousePointerClick → `Cursor` или кастомный
- Send → `Send`
- Check → `Check`
- X → `X`
- Heart → `Heart`
- Sparkles → `Sparkles`
- MessageSquare → `MessageSquare`
- Layers → `Layers`
- Zap → `Zap`
- Clock → `Clock`
- TrendingUp → `TrendingUp`
- Shield → `Shield`
- ChevronDown → `ChevronDown`
- ChevronRight → `ChevronRight`
- ArrowRight → `ArrowRight`
- Telegram → кастомный (есть в lucide, но style может отличаться)
- Zap2 → `Zap` (дублик с другим stroke)
- Plus → `Plus`
- Minus → `Minus`
- File → `File`
- Users → `Users`
- Building → `Building`
- MapPin → `MapPin`
- Coins → `Coins`

**Решение Phase 1**: Создать `site/components/Icons.tsx` с переписью на lucide-react. BrandMark, BrandLockup → `site/components/Brand.tsx`.

---

#### `telegram.jsx` (301 строка)
**Назначение**: Реалистичный Telegram UI mockup для демонстрации бота в hero.

**Компоненты**:
- `TelegramPhone({ peer, messages, replyKeyboard, width, height, dark, showInput })` — основной компонент (iPhone mockup)
- `ChatMessage({ msg, dark, ... })` — message bubble с поддержкой типов: text, options, vacancy, vacancy-rich, typing, stats, file

**Props**:
```javascript
messages: [
  { from: 'bot'|'me', type: 'text'|'options'|'vacancy'|'vacancy-rich'|'typing'|'stats'|'file', content, buttons }
]
```

**useState/useEffect**: ❌ NONE (pure render)

**Inline styles**: МНОГО (color palette для dark/light theme, bubble positioning, chat scroll)

**Где используется**:
- `hero.jsx` (не вижу прямого использования, но через глобал возможно)
- Потенциально для демо-чатов

**Решение Phase 1**: `site/components/TelegramPhone.tsx` + `site/lib/telegram-types.ts` для msg schema.

---

#### `real-bot.jsx` (238 строк)
**Назначение**: "Реальный" вид Telegram бота из скриншотов. Более структурированный чем TelegramPhone.

**Компоненты**:
- `RealBotScreen({ content, buttons, time, width, height, peer })` — основной компонент
- `KbdButton({ emoji, label, primary, accent, flex })` — кнопка reply keyboard

**Data (constants)**:
```javascript
const ONBOARDING_SCREEN = { content, buttons }
const MAIN_MENU_SCREEN = { content, buttons }
const HH_AUTH_SCREEN = { time, content, buttons }
const HH_PANEL_SCREEN = { content, buttons }
const VACANCY_SCREEN = { content, buttons }
```

**useState/useEffect**: ❌ NONE (pure render)

**Inline styles**: ОЧЕНЬ МНОГО (dark telegram theme #17212B, #182533, кнопки с градиентами, status bar, header)

**Где используется**:
- `sections.jsx`: HowItWorks.screens = [ONBOARDING_SCREEN, HH_AUTH_SCREEN, HH_PANEL_SCREEN, VACANCY_SCREEN]
- `sections.jsx`: Features.screen (MAIN_MENU_SCREEN, HH_PANEL_SCREEN, VACANCY_SCREEN)

**Решение Phase 1**: `site/components/RealBotScreen.tsx` + `site/lib/screens/bot-screens.ts` (data).

---

#### `hero-swipe.jsx` (~200+ строк)
**Назначение**: Swipe-стек вакансий (Tinder-like UI), demo animation.

**Компоненты**:
- `HeroSwipe()` — главный компонент (управляет стеком)
- `JobCard({ job, style })` — карточка вакансии

**Data**:
```javascript
const SAMPLE_JOBS = [
  { title, company, salary, location, match, tags, color, abbr },
  // 9 example jobs
]
```

**useState/useEffect**:
- stack (state)
- swipeDir (animation state)
- counter { liked, passed }
- setInterval для auto-swipe каждые 2800ms
- handleSwipe(dir) с setTimeout для animation

**Inline styles**: МНОГО (position: absolute, transform, transitions)

**Решение Phase 1**: `site/components/HeroSwipe.tsx` + `site/lib/data/sample-jobs.ts`.

---

#### `hero.jsx` (~550 строк)
**Назначение**: Nav + Hero + HeroChat комбо. Основной экран.

**Компоненты**:
- `Nav()` — fixed header, logo, nav links, CTA кнопка. Scrolled-state для backdrop filter.
- `Hero({ variant })` — основной hero section (левый текст + правый визуал)
- `HeroChat()` — live chat demo с вакансиями (alternative to HeroSwipe)

**Data**:
```javascript
const HERO_CHAT_JOBS = [
  { title, company, salary, location, schedule, experience, match, posted, duties, requirements },
  // 10 example jobs
]
```

**useState/useEffect**:
- Nav: scrolled state, scroll listener
- HeroChat: idx, sent, skipped, response, anim, paused, auto-cycle setTimeout каждые 3000ms

**Inline styles**: ОЧЕНЬ МНОГО (grid layout, responsive, hero halo decoration)

**Где используется**:
- app.jsx: `<Hero variant={t.heroVariant}/>`

**Решение Phase 1**: `site/components/Nav.tsx`, `site/components/Hero.tsx`, `site/components/HeroChat.tsx` + `site/lib/data/hero-jobs.ts`.

---

#### `sections.jsx` (~205 строк)
**Назначение**: HowItWorks + Features секции с tab-switching и RealBotScreen mockups.

**Компоненты**:
- `HowItWorks()` — 4 шага (резюме, подключение, фильтры, отклики), левый список + правый RealBotScreen
- `Features()` — 3 фичи с табами, левый текст + правый RealBotScreen

**useState/useEffect**:
- HowItWorks: active (шаг)
- Features: active (фича)

**Inline styles**: МНОГО (grid, tab buttons, transitions)

**Зависимости**: RealBotScreen, screen data (ONBOARDING_SCREEN и т.д.)

**Решение Phase 1**: `site/components/HowItWorks.tsx`, `site/components/Features.tsx`.

---

#### `more-sections.jsx` (~290 строк)
**Назначение**: Pricing + FAQ + FinalCTA + Footer.

**Компоненты**:
- `Pricing()` — grid из 2 PriceCard (free + premium)
- `PriceCard({ plan })` — карточка тарифа (brand/light/dark тон)
- `FAQ()` — accordion с 6 Q&A, open state
- `FinalCTA()` — big gradient block с текстом и двумя кнопками
- `Footer()` — logo + links + copyright

**Data**:
```javascript
const plans = [
  { name, price, unit, period, sub, features, cta, tone, badge? },
  // 2 plans
]
const FAQ.items = [
  { q, a },
  // 6 items
]
```

**useState/useEffect**:
- FAQ: open (active item index)

**Inline styles**: МНОГО (gradient backgrounds, button hover, grid)

**Решение Phase 1**: Отдельные компоненты в `site/components/` + `site/lib/data/pricing.ts`, `site/lib/data/faq.ts`.

---

#### `speed.jsx` (~450+ строк)
**Назначение**: Гонка 14 часов (bot vs manual). Сложная timeline с non-linear mapping.

**Компоненты**:
- `SpeedSection()` — главный контейнер (IntersectionObserver для auto-play)
- `RaceTrack({ minute, playheadPct })` — две lane + playhead + time axis
- `Lane({ kind, title, subtitle, minute, beats })` — одна дорожка (bot или manual)
- `TimeAxis({ minute, playheadPct })` — час-тики
- `Playhead({ playheadPct, minute })` — вертикальная линия
- `StatTile({ value, label })` — статистика внизу
- `FiltersTile()` — специальная плитка с фильтрами (incomplete в коде)

**Data**:
```javascript
const ZONES = [...]  // non-linear time mapping
const BOT_BEATS = [...]
const MANUAL_BEATS = [...]
const HOUR_TICKS = [...]
```

**useState/useEffect**:
- SpeedSection: progress (0..1), playing, hasAutoplayed, sectionRef, rafRef для requestAnimationFrame
- useEffect для IntersectionObserver
- useEffect для animation loop (RAF)

**Inline styles**: ОЧЕНЬ МНОГО (positioned elements, animations, non-linear transforms)

**Решение Phase 1**: `site/components/SpeedSection.tsx` + `site/lib/speed/time-zones.ts` для data.

---

#### `speed.v1.jsx`
**DEPRECATED** — старая версия. НЕ ТАЩИТЬ в Next.js.

---

### 2.3 app.jsx (55 строк)
**Назначение**: Root компонент. Диспетчер всех секций + tweaks логика.

**Компоненты**:
- `App()` — рендит Nav, Hero, SpeedSection, HowItWorks, Features, Pricing, FAQ, FinalCTA, Footer, TweaksPanel

**useState/useEffect**:
- t (tweaks): theme (light/dark), gradient (subtle/normal/intense), heroVariant (swipe/chat)
- setTweak callback
- useEffect для применения class-ов на body

**Решение Phase 1**: `site/app.tsx` (Next.js layout root).

---

## 3. Граф зависимостей компонентов

```
app.jsx
  ├─ Nav (из hero.jsx)
  ├─ Hero (из hero.jsx)
  │  ├─ BrandLockup (из icons.jsx)
  │  ├─ Icon.Telegram (из icons.jsx)
  │  ├─ HeroSwipe (из hero-swipe.jsx)
  │  │  └─ JobCard
  │  │     └─ Icon.* (Sparkles, Heart, X)
  │  └─ HeroChat (из hero.jsx)
  │     ├─ Icon.* (Heart, X)
  │     └─ RealBotScreen (из real-bot.jsx)
  │        └─ KbdButton
  ├─ SpeedSection (из speed.jsx)
  │  ├─ RaceTrack
  │  │  ├─ Lane (x2: bot + manual)
  │  │  ├─ TimeAxis
  │  │  └─ Playhead
  │  ├─ StatTile
  │  └─ FiltersTile
  ├─ HowItWorks (из sections.jsx)
  │  └─ RealBotScreen (x4 screens)
  │     └─ KbdButton
  ├─ Features (из sections.jsx)
  │  ├─ Icon.Check (из icons.jsx)
  │  └─ RealBotScreen (x3 screens)
  │     └─ KbdButton
  ├─ Pricing (из more-sections.jsx)
  │  └─ PriceCard
  │     └─ Icon.Check, Icon.Telegram
  ├─ FAQ (из more-sections.jsx)
  │  └─ Icon.Plus, Icon.Minus
  ├─ FinalCTA (из more-sections.jsx)
  │  └─ Icon.Telegram
  ├─ Footer (из more-sections.jsx)
  │  └─ BrandLockup
  └─ TweaksPanel (из tweaks-panel.jsx) [НЕ ТАЩИМ]
```

---

## 4. Data модули для Phase 1

Константы и массивы, которые должны быть отдельными файлами:

| Data | Текущее место | Новое место (Phase 1) | Объём |
|------|----------------|----------------------|--------|
| `HERO_CHAT_JOBS` | hero.jsx (114–315) | `site/lib/data/hero-jobs.ts` | 10 вакансий, ~150 строк |
| `SAMPLE_JOBS` | hero-swipe.jsx (5–15) | `site/lib/data/sample-jobs.ts` | 9 вакансий, ~15 строк |
| `HowItWorks.steps` | sections.jsx (8–28) | `site/lib/data/how-it-works.ts` | 4 шага, ~25 строк |
| `Features.features` | sections.jsx (102–126) | `site/lib/data/features.ts` | 3 фичи, ~30 строк |
| `ONBOARDING_SCREEN` | real-bot.jsx (147–161) | `site/lib/screens/bot-screens.ts` | 1 экран, ~15 строк |
| `MAIN_MENU_SCREEN` | real-bot.jsx (164–172) | `site/lib/screens/bot-screens.ts` | 1 экран, ~9 строк |
| `HH_AUTH_SCREEN` | real-bot.jsx (175–188) | `site/lib/screens/bot-screens.ts` | 1 экран, ~14 строк |
| `HH_PANEL_SCREEN` | real-bot.jsx (191–206) | `site/lib/screens/bot-screens.ts` | 1 экран, ~16 строк |
| `VACANCY_SCREEN` | real-bot.jsx (209–235) | `site/lib/screens/bot-screens.ts` | 1 экран, ~27 строк |
| Pricing plans | more-sections.jsx (8–43) | `site/lib/data/pricing.ts` | 2 плана, ~40 строк |
| FAQ items | more-sections.jsx (135–141) | `site/lib/data/faq.ts` | 6 Q&A, ~10 строк |
| `SpeedSection` zones | speed.jsx (40–56, 91–111) | `site/lib/speed/timeline.ts` | ZONES, BEATS, TICKS, ~70 строк |

---

## 5. CSS и inline-стили

### 5.1 CSS из styles.css (283 строки) — тащим в Tailwind/globals

- CSS переменные (--amber, --orange, --text-heading, etc.) → Tailwind config
- `.btn`, `.btn-primary`, `.btn-ghost`, `.btn-dark` → Tailwind utilities или `site/styles/buttons.css`
- `.container` → max-w + mx-auto (есть в Tailwind)
- `.eyebrow` → можно custom class или Tailwind
- `.grad-text` → CSS gradient → Tailwind gradient
- Animations (@keyframes slideInFromRight, swipeRight, swipeLeft, pulseRing, typingDots, floatY) → `globals.css` или `app.css`
- Dark theme (body.theme-dark) → перейти на Tailwind dark mode
- Gradient intensity (body.grad-*) → custom Tailwind config

### 5.2 Inline-стили по компонентам

**МНОГО inline в**:
- `tweaks-panel.jsx` — вся UI встроена в __TWEAKS_STYLE
- `telegram.jsx` — все bubble styles inline
- `real-bot.jsx` — все кнопки и layout inline
- `hero.jsx` — grid, hero halo, все sections
- `hero-swipe.jsx` — JobCard gradient, swipe transforms
- `sections.jsx` — tab buttons, grid layout
- `more-sections.jsx` — price cards, FAQ accordion
- `speed.jsx` — race track, lanes, playhead, timeline

**МАЛО inline в**:
- `icons.jsx` — только flex/sizing
- `app.jsx` — только body class management

**Стратегия Phase 1**:
1. Большие layout компоненты (Hero, Sections, etc.) — переписать на Tailwind classes
2. Анимации — перенести в `globals.css` (Tailwind @apply или custom CSS)
3. Dynamic styles (colors, transforms) — остаться inline или использовать CSS variables

---

## 6. Иконки lucide-react маппинг

| Текущая иконка (inline SVG) | lucide-react эквивалент | Примечание |
|-----|---------|-----------|
| Icon.MousePointerClick | Cursor или custom | Есть в lucide как Clickable |
| Icon.Send | Send | ✅ точно совпадает |
| Icon.Check | Check | ✅ точно совпадает |
| Icon.X | X | ✅ точно совпадает |
| Icon.Heart | Heart | ✅ точно совпадает |
| Icon.Sparkles | Sparkles | ✅ точно совпадает |
| Icon.MessageSquare | MessageSquare | ✅ точно совпадает |
| Icon.Layers | Layers | ✅ точно совпадает |
| Icon.Zap | Zap | ✅ точно совпадает |
| Icon.Clock | Clock | ✅ точно совпадает |
| Icon.TrendingUp | TrendingUp | ✅ точно совпадает |
| Icon.Shield | Shield | ✅ точно совпадает |
| Icon.ChevronDown | ChevronDown | ✅ точно совпадает |
| Icon.ChevronRight | ChevronRight | ✅ точно совпадает |
| Icon.ArrowRight | ArrowRight | ✅ точно совпадает |
| Icon.Telegram | Send или custom | lucide имеет Send, может потребоваться custom |
| Icon.Zap2 | Zap | Дублик, использовать Zap |
| Icon.Plus | Plus | ✅ точно совпадает |
| Icon.Minus | Minus | ✅ точно совпадает |
| Icon.File | File | ✅ точно совпадает |
| Icon.Users | Users | ✅ точно совпадает |
| Icon.Building | Building2 | ✅ совпадает (Building2 в lucide) |
| Icon.MapPin | MapPin | ✅ точно совпадает |
| Icon.Coins | Coins | ✅ точно совпадает |

---

## 7. Hooks и React API использование

### По компонентам

| Компонент | useState | useEffect | useRef | useCallback | Кол-во |
|-----------|----------|----------|--------|------------|--------|
| TweaksPanel | 2 | 2 | 2 | 1 | 7 |
| useTweaks | 1 | 0 | 0 | 1 | 2 |
| TweakRadio | 1 | 0 | 1 | 0 | 2 |
| Nav | 1 | 1 | 0 | 0 | 2 |
| Hero | 0 | 0 | 0 | 0 | 0 |
| HeroChat | 5 | 1 | 0 | 0 | 6 |
| HeroSwipe | 3 | 1 | 0 | 0 | 4 |
| HowItWorks | 1 | 0 | 0 | 0 | 1 |
| Features | 1 | 0 | 0 | 0 | 1 |
| FAQ | 1 | 0 | 0 | 0 | 1 |
| Pricing | 0 | 0 | 0 | 0 | 0 |
| SpeedSection | 3 | 2 | 3 | 0 | 8 |
| App | 1 | 1 | 0 | 0 | 2 |

**Итог**: Mostly simple state управление. Никаких Context, Redux, useReducer. Простой переход на Next.js без особых трудностей.

---

## 8. Маркетинг-движок (marketing-engine/)

**Статус**: Python Telegram бот (отдельный проект, не React).

**Структура**:
```
marketing-engine/
├── src/
│   ├── main.py           # Основной loop для мониторинга чатов
│   ├── admin_bot.py      # Admin интерфейс
│   └── config.py         # Конфиг (токены, чат-ID)
├── data/
│   ├── keyword_patterns.json       # Regex patterns для мониторинга
│   ├── seller_chats.json           # IDs чатов для отправки постов
│   ├── brand_voice_examples.json   # Примеры текстов в стиле бренда
│   ├── monitored_chats.json        # Чаты для мониторинга
│   └── brand/                      # PNG логотипы (4 варианта)
├── pyproject.toml        # deps: python-telegram-bot, httpx, etc.
└── .env                  # ADMIN_ID, BOT_TOKEN, etc.
```

**Назначение**: Мониторит выбранные Telegram чаты (LLM recruiter сообществ), генерирует посты в бренд-стиле и отправляет в админ-чаты.

**Для Phase 1**: Просто скопировать `marketing-engine/` в новый репо как-есть. Может использоваться для постинга о лендинге в соответствующих чатах.

---

## 9. План миграции по компонентам → Next.js структура

### Next.js целевая структура

```
site/
├── components/
│   ├── Nav.tsx
│   ├── Hero.tsx
│   ├── HeroChat.tsx
│   ├── HeroSwipe.tsx
│   ├── HowItWorks.tsx
│   ├── Features.tsx
│   ├── Pricing.tsx
│   ├── PriceCard.tsx
│   ├── FAQ.tsx
│   ├── FinalCTA.tsx
│   ├── Footer.tsx
│   ├── SpeedSection.tsx
│   ├── RealBotScreen.tsx
│   ├── TelegramPhone.tsx
│   ├── Brand.tsx (BrandMark, BrandLockup)
│   └── Icons.tsx (lucide-react wrapper или custom)
├── lib/
│   ├── data/
│   │   ├── hero-jobs.ts
│   │   ├── sample-jobs.ts
│   │   ├── how-it-works.ts
│   │   ├── features.ts
│   │   ├── pricing.ts
│   │   └── faq.ts
│   ├── screens/
│   │   └── bot-screens.ts (все 5 экранов)
│   ├── speed/
│   │   └── timeline.ts (zones, beats, ticks)
│   └── telegram-types.ts (message union types)
├── styles/
│   ├── globals.css (переменные + анимации)
│   └── buttons.css (утилиты кнопок, если не в Tailwind)
├── app.tsx (root layout)
└── page.tsx (главная страница, рендит все секции)
```

### Компонент-файл маппинг

| Исходный (UMD) | Phase 1 (Next.js TSX) | Тип | Депы |
|---|---|---|---|
| `icons.jsx` Icon object | `components/Icons.tsx` | Wrapper → lucide-react | lucide-react |
| `icons.jsx` BrandMark, BrandLockup | `components/Brand.tsx` | Компоненты | lucide-react |
| `telegram.jsx` TelegramPhone | `components/TelegramPhone.tsx` | Компонент | ❌ no |
| `real-bot.jsx` RealBotScreen, KbdButton | `components/RealBotScreen.tsx` | Компонент | ❌ no |
| `real-bot.jsx` screens data | `lib/screens/bot-screens.ts` | Type + const | ❌ no |
| `hero-swipe.jsx` HeroSwipe, JobCard | `components/HeroSwipe.tsx` | Компонент | ❌ no |
| `hero-swipe.jsx` SAMPLE_JOBS | `lib/data/sample-jobs.ts` | Const | ❌ no |
| `hero.jsx` Nav | `components/Nav.tsx` | Компонент | lucide-react (Icons) |
| `hero.jsx` Hero | `components/Hero.tsx` | Компонент | локальные |
| `hero.jsx` HeroChat | `components/HeroChat.tsx` | Компонент | локальные + RealBotScreen |
| `hero.jsx` HERO_CHAT_JOBS | `lib/data/hero-jobs.ts` | Const | ❌ no |
| `sections.jsx` HowItWorks | `components/HowItWorks.tsx` | Компонент | RealBotScreen |
| `sections.jsx` Features | `components/Features.tsx` | Компонент | RealBotScreen, Icons |
| `more-sections.jsx` Pricing | `components/Pricing.tsx` | Компонент | PriceCard, Icons |
| `more-sections.jsx` PriceCard | `components/PriceCard.tsx` | Компонент | Icons |
| `more-sections.jsx` FAQ | `components/FAQ.tsx` | Компонент | Icons |
| `more-sections.jsx` FinalCTA | `components/FinalCTA.tsx` | Компонент | Icons |
| `more-sections.jsx` Footer | `components/Footer.tsx` | Компонент | Brand |
| `more-sections.jsx` pricing, faq data | `lib/data/pricing.ts`, `lib/data/faq.ts` | Const | ❌ no |
| `speed.jsx` SpeedSection + helpers | `components/SpeedSection.tsx` | Компонент | ❌ no |
| `speed.jsx` timeline data | `lib/speed/timeline.ts` | Const + helpers | ❌ no |
| `app.jsx` App | `app.tsx` (layout) | Layout | локальные |
| ❌ `tweaks-panel.jsx` | ❌ НЕ ТАЩИМ | Dev-tool | ❌ |
| ❌ `speed.v1.jsx` | ❌ НЕ ТАЩИМ | Old | ❌ |

### CSS/Tailwind план

1. **globals.css**:
   - Tailwind directives (@tailwind base, components, utilities)
   - CSS переменные для brand colors (если используются в runtime)
   - @keyframes все анимации (slideInFromRight, swipeRight, pulseRing, typingDots, floatY)

2. **tailwind.config.ts**:
   - Extend colors с brand palette (amber, orange, red, pink + surfaces + text)
   - Extend spacing, borderRadius, shadows
   - Градиенты как custom utilities
   - Градиент-интенсивность как CSS переменные или variants

3. **Компоненты**: 
   - Переписать inline-стили на Tailwind classes (max w-screen, h-screen, grid, flex, etc.)
   - Dynamic styles (transforms, colors in animation) → оставить inline или CSS переменные

---

## 10. Вывод: План миграции по приоритетам

### Фаза 1a: Infrastructure (setup)
- [ ] Next.js 14 проект + TypeScript + Tailwind
- [ ] Tailwind config (colors, animations, spacing)
- [ ] globals.css + animations
- [ ] Icons.tsx (lucide-react wrapper)

### Фаза 1b: Core Components (без данных, чистые)
- [ ] Brand.tsx (BrandMark, BrandLockup)
- [ ] TelegramPhone.tsx
- [ ] RealBotScreen.tsx
- [ ] Spacing, Layout утилиты

### Фаза 1c: Data modules
- [ ] bot-screens.ts (5 экранов)
- [ ] hero-jobs.ts
- [ ] sample-jobs.ts
- [ ] how-it-works.ts
- [ ] features.ts
- [ ] pricing.ts
- [ ] faq.ts
- [ ] timeline.ts (speed section)

### Фаза 1d: Page Components (compose из core)
- [ ] HeroSwipe.tsx
- [ ] HeroChat.tsx
- [ ] HowItWorks.tsx
- [ ] Features.tsx
- [ ] Pricing.tsx + PriceCard.tsx
- [ ] FAQ.tsx
- [ ] SpeedSection.tsx

### Фаза 1e: Top-level
- [ ] Nav.tsx
- [ ] Hero.tsx
- [ ] FinalCTA.tsx
- [ ] Footer.tsx
- [ ] page.tsx (маршрут всех секций)

### Фаза 1f: Cleanup
- [ ] Удалить tweaks-panel из дизайна
- [ ] Удалить speed.v1.jsx упоминания
- [ ] Переписать все Object.assign(window, ...) на ES imports

### Фаза 2: Optimization + Deployment
- [ ] Image optimization (компоненты с Telegram mockups)
- [ ] Lazy loading для секций
- [ ] SEO + meta tags
- [ ] Vercel deploy

---

## 11. Checklist для разработчика Phase 1

- [ ] Все компоненты в отдельных файлах (`components/*.tsx`)
- [ ] Все данные в `lib/data/*.ts` и `lib/screens/*.ts`
- [ ] Все Tailwind classes (не inline styles где возможно)
- [ ] Все анимации в `globals.css`
- [ ] Lucide-react для всех иконок (не inline SVG)
- [ ] TypeScript interfaces для props
- [ ] No Object.assign(window, ...) в коде
- [ ] No dangerouslySetInnerHTML (except для bot-screen content)
- [ ] RealBotScreen content как type-safe union
- [ ] Auto-play animations через useEffect + IntersectionObserver (SpeedSection)
- [ ] Responsive grid (hero, sections) через Tailwind grid-cols-1 md:grid-cols-2
- [ ] Dark mode support (Tailwind dark: selector)

---

**Документ создан**: 2026-04-25
**Статус**: Ready for Phase 1 разработку
