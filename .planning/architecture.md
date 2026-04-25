# Архитектура лендинга Откликер | Phase 0.2

**Статус:** Финальный архитектурный документ для Phase 1 (executor скелетон).
**Стек:** Next.js 14 App Router · TypeScript strict · Tailwind CSS · static export.
**Автор:** Architect, Phase 0.2 (2026-04-25).
**Цель документа:** дать executor готовые сигнатуры типов, структуру файлов, копируемый Tailwind config и явный чеклист, чтобы Phase 1 закрылась без архитектурных решений в рантайме.

Источники: `.planning/component-map.md`, `.planning/brand-tokens.md`, `design_handoff_otklicker_landing/source/styles.css`, `design_handoff_otklicker_landing/source/components/*.jsx`, `docs/PRODUCT_FACTS.md`, `legal/PRIVACY_POLICY.md`, `legal/OFFER_AGREEMENT.md`.

---

## 1. TypeScript типы

Все типы лежат в `site/lib/types/` (по доменам). Импорт через barrel `site/lib/types/index.ts`.

### 1.1 `site/lib/types/bot-screen.ts`

Описывает данные `RealBotScreen` (real-bot.jsx:147–235). Сейчас `content` — HTML-строка через `dangerouslySetInnerHTML`; в Phase 1 оставляем тот же контракт (легально внутри замкнутого мокапа), но типизируем явно.

```ts
// Идентификаторы пяти готовых сценариев из real-bot.jsx
export type BotScreenId =
  | 'onboarding'
  | 'main-menu'
  | 'hh-auth'
  | 'hh-panel'
  | 'vacancy';

// Кнопка reply-клавиатуры
export interface KeyboardButton {
  emoji?: string;
  label: string;
  primary?: boolean;
  accent?: 'green' | 'red';
  /** Есть в исходнике как twoCol/pairLabel — в данных не используется, оставлен на будущее */
}

// Ряд клавиатуры: либо одиночная кнопка, либо горизонтальная пара
export type KeyboardRow = KeyboardButton | KeyboardButton[];

// Шапка чата (опциональный override дефолта "Откликер · бот")
export interface ChatHeader {
  name: string;
  subtitle: string;
}

// Один экран бота — то, что принимает RealBotScreen
export interface BotScreen {
  /**
   * HTML-разметка контента бабла. Допускается, потому что:
   *   1) данные статические, лежат в нашем репо;
   *   2) обернутый Telegram-стиль (цветные ссылки, <b>) проще набрать как HTML, чем городить компонент.
   * Если в Phase 2 захочется убрать dangerouslySetInnerHTML — мигрировать на массив сегментов.
   */
  content: string;
  buttons: KeyboardRow[];
  /** Время в шапке бабла "06:32" */
  time?: string;
  header?: Partial<ChatHeader>;
}

// Карта всех пяти экранов
export type BotScreenMap = Record<BotScreenId, BotScreen>;

// (Резерв на будущее — если решим вынести HeroChat в общий движок.)
// Структурный BotMessage используется только в HeroChat, где сообщения программно
// конструируются из JobCard. В Phase 1 HeroChat остаётся со своим локальным шейпом —
// смотри ниже type HeroChatMessage.
export interface BotMessage {
  role: 'bot' | 'user' | 'system';
  type: 'text' | 'options' | 'vacancy' | 'vacancy-rich' | 'typing' | 'stats' | 'file' | 'toast';
  content?: string;          // HTML или plain
  buttons?: KeyboardButton[];
  /** Для type='vacancy-rich' — структурная карточка вакансии */
  job?: JobCard;
  /** Для type='toast' (response-bubble в HeroChat) */
  tone?: 'apply' | 'skip';
}
```

### 1.2 `site/lib/types/job.ts`

Карточка вакансии. Один тип покрывает оба варианта — структурный (HeroChat, `HERO_CHAT_JOBS`) и облегчённый (HeroSwipe, `SAMPLE_JOBS`). Поля swipe-only помечены `?`.

```ts
export interface JobCard {
  // Общее (есть и в HERO_CHAT_JOBS, и в SAMPLE_JOBS)
  title: string;
  company: string;
  salary: string;
  location: string;
  match: number; // 0..100

  // Только HERO_CHAT_JOBS (chat-вариант)
  schedule?: string;
  experience?: string;
  posted?: string;
  duties?: string[];
  requirements?: string[];

  // Только SAMPLE_JOBS (swipe-вариант)
  tags?: string[];
  /** CSS background-image для шапки карточки — например, 'linear-gradient(135deg, #FBBF24, #F97316)' */
  color?: string;
  /** Аббревиатура для логотипа-плашки */
  abbr?: string;
}
```

### 1.3 `site/lib/types/pricing.ts`

Синхронизировано с `docs/PRODUCT_FACTS.md` §5. На сегодня в продакшен-копии плана два — Бесплатный и Активный (790 ₽ / 3 недели). Tone'а `dark` сейчас не используется, но оставлен в union, потому что в more-sections.jsx:72 ветка `isDark` уже зашита.

```ts
export type PricingTone = 'light' | 'brand' | 'dark';

export interface PricingPlan {
  /** Уникальный slug — используется в data-атрибутах и аналитике */
  id: 'free' | 'active' | string;
  /** Заголовок карточки ("Бесплатный", "Активный") */
  name: string;
  /** Цена как строка — "0", "790" — потому что отображается с разбивкой число/валюта */
  price: string;
  /** Валюта/символ ("₽") */
  unit: string;
  /** Период оплаты ("постоянно", "за 3 недели") */
  period: string;
  /** Подпись под названием ("Чтобы попробовать", "Для активного поиска") */
  sub: string;
  /** Опциональный бейдж в правом верхнем углу ("37 ₽ в день") */
  badge?: string;
  /** Список фич — ровно та, что в more-sections.jsx, синхронизирована с PRODUCT_FACTS §5 */
  features: string[];
  /** Текст CTA-кнопки ("Попробовать", "Оформить пакет") */
  cta: string;
  /** Куда ведёт CTA — пока всегда t.me/otklicker_bot */
  href: string;
  /** Тон карточки */
  tone: PricingTone;
}
```

### 1.4 `site/lib/types/faq.ts`

```ts
export interface FAQItem {
  /** Slug — для anchor-ссылок и аналитики (faq#kak-bot-otkliki) */
  id: string;
  q: string;
  a: string;
}
```

### 1.5 `site/lib/types/feature.ts`

```ts
import type { BotScreenId } from './bot-screen';

export type FeatureId = 'auto' | 'cards' | 'menu';

export interface Feature {
  id: FeatureId;
  /** Текст таб-пилюли ("01 · Автоотклики") */
  label: string;
  /** Заголовок H3 правой колонки */
  headline: string;
  /** Лид-параграф */
  lead: string;
  /** Буллеты с круглыми чекбоксами */
  bullets: string[];
  /** Какой экран бота показывается справа */
  screen: BotScreenId;
}
```

### 1.6 `site/lib/types/how-it-works.ts`

```ts
import type { BotScreenId } from './bot-screen';

export interface HowItWorksStep {
  /** Двузначный номер: "01" .. "04" */
  number: string;
  title: string;
  description: string;
  screen: BotScreenId;
}
```

### 1.7 `site/lib/types/index.ts` (barrel)

```ts
export * from './bot-screen';
export * from './job';
export * from './pricing';
export * from './faq';
export * from './feature';
export * from './how-it-works';
```

### 1.8 Пропсы компонентов

Все компоненты — function components с явным `interface Props`. Размещаем рядом с компонентом, не в `lib/types`.

```ts
// components/Nav.tsx
export interface NavProps {
  /** Override links (по умолчанию из NAV_LINKS константы внутри компонента) */
  links?: ReadonlyArray<{ href: string; label: string }>;
}

// components/Hero.tsx
export type HeroVariant = 'chat' | 'swipe';
export interface HeroProps {
  variant?: HeroVariant; // default 'chat' (решение Phase 0.2 — chat по умолчанию, swipe в резерве)
}

// components/HeroChat.tsx
export interface HeroChatProps {
  /** Список вакансий — по умолчанию HERO_CHAT_JOBS */
  jobs?: JobCard[];
  /** Стартовое значение счётчика "откликов" — по умолчанию 127 */
  initialSent?: number;
  /** Стартовое значение счётчика "пропущено" — по умолчанию 94 */
  initialSkipped?: number;
  /** Интервал автоцикла, мс. По умолчанию 3000 */
  cycleMs?: number;
}

// components/HeroSwipe.tsx
export interface HeroSwipeProps {
  jobs?: JobCard[];
  cycleMs?: number; // default 2800
}

// components/HowItWorks.tsx
export interface HowItWorksProps {
  steps?: HowItWorksStep[]; // default из lib/data/how-it-works
}

// components/Features.tsx
export interface FeaturesProps {
  features?: Feature[]; // default из lib/data/features
}

// components/Pricing.tsx
export interface PricingProps {
  plans?: PricingPlan[]; // default из lib/data/pricing
}

// components/PriceCard.tsx
export interface PriceCardProps {
  plan: PricingPlan;
}

// components/FAQ.tsx
export interface FAQProps {
  items?: FAQItem[];          // default из lib/data/faq
  defaultOpen?: number | null; // default 0
}

// components/Footer.tsx
export interface FooterProps { /* нет настроек, всё — статика */ }

// components/CookieBanner.tsx
export interface CookieBannerProps {
  /** Ключ в localStorage */
  storageKey?: string; // default 'otklicker.cookie-consent'
  /** Куда ведёт ссылка "подробнее" */
  policyHref?: string; // default '/cookies'
}

// components/SpeedSection.tsx
export interface SpeedSectionProps { /* нет настроек, тайминг внутри */ }

// components/RealBotScreen.tsx
export interface RealBotScreenProps {
  content: string;
  buttons: KeyboardRow[];
  time?: string;
  width?: number;  // default 360
  height?: number; // default 620
  header?: Partial<ChatHeader>;
}
```

---

## 2. Структура файлов внутри `site/`

```
site/
├── app/                                 # Next.js App Router
│   ├── layout.tsx                       # <html lang="ru">, Inter, body, CookieBanner-mount
│   ├── page.tsx                         # главная "/" — собирает все секции
│   ├── globals.css                      # Tailwind base + CSS-переменные + утилиты
│   ├── robots.ts                        # /robots.txt — статический generator
│   ├── sitemap.ts                       # /sitemap.xml — все страницы
│   ├── manifest.ts                      # /manifest.webmanifest (PWA-light)
│   ├── icon.tsx                         # favicon source (gradient mark, ImageResponse)
│   ├── apple-icon.tsx                   # apple-touch-icon
│   ├── opengraph-image.png              # 1200×630 статика (экспорт из брендбука, не runtime)
│   ├── twitter-image.png                # та же что и og (или копия)
│   ├── privacy/
│   │   └── page.tsx                     # рендерит legal/SITE_PRIVACY_POLICY.md через react-markdown
│   ├── cookies/
│   │   └── page.tsx                     # рендерит legal/COOKIE_POLICY.md
│   ├── offer/
│   │   └── page.tsx                     # placeholder ("Документ готовится")
│   ├── bot-privacy/
│   │   └── page.tsx                     # placeholder (политика для @otklicker_bot)
│   └── not-found.tsx                    # 404
├── components/                          # React-компоненты
│   ├── Nav.tsx                          # Sticky навигация с blur при скролле
│   ├── Hero.tsx                         # Двухколоночный hero
│   ├── HeroChat.tsx                     # Авто-цикл живого чата
│   ├── HeroSwipe.tsx                    # Стек swipe-карточек (резерв, не в default-варианте)
│   ├── HowItWorks.tsx                   # 4 шага + RealBotScreen
│   ├── Features.tsx                     # Тёмная секция, табы + RealBotScreen
│   ├── Pricing.tsx                      # Сетка двух тарифов
│   ├── PriceCard.tsx                    # Одна карточка тарифа
│   ├── FAQ.tsx                          # Аккордеон, 6 пунктов
│   ├── FinalCTA.tsx                     # Большой gradient-блок в конце
│   ├── Footer.tsx                       # Футер с тремя колонками ссылок
│   ├── SpeedSection.tsx                 # Race 14 часов (большой компонент, ~400 строк)
│   ├── RealBotScreen.tsx                # Telegram-mockup (dark theme)
│   ├── Brand.tsx                        # BrandMark + BrandLockup
│   ├── CookieBanner.tsx                 # Нижний баннер согласия с куки
│   ├── MarkdownPage.tsx                 # Обёртка для legal-страниц (react-markdown + prose)
│   └── ui/                              # Низкоуровневые примитивы
│       ├── Button.tsx                   # primary/ghost/dark варианты, asChild для <a>
│       ├── Eyebrow.tsx                  # .eyebrow с дотом — pill-плашка
│       ├── HaloBlob.tsx                 # Декоративный blur-блоб (position absolute)
│       ├── Noise.tsx                    # SVG-турбуленция overlay для тёмных секций
│       ├── GradientText.tsx             # <span> с background-clip: text
│       └── SectionHead.tsx              # eyebrow + h2 + p (центральный или левый align)
├── lib/
│   ├── data/                            # Контентные массивы
│   │   ├── hero-jobs.ts                 # HERO_CHAT_JOBS — 10 вакансий
│   │   ├── sample-jobs.ts               # SAMPLE_JOBS — 9 swipe-карточек
│   │   ├── how-it-works.ts              # HOW_IT_WORKS_STEPS — 4 шага
│   │   ├── features.ts                  # FEATURES — 3 фичи
│   │   ├── pricing.ts                   # PRICING_PLANS — 2 плана (синк с PRODUCT_FACTS §5)
│   │   ├── faq.ts                       # FAQ_ITEMS — 6 Q&A
│   │   └── nav.ts                       # NAV_LINKS, FOOTER_LINKS
│   ├── screens/
│   │   └── bot-screens.ts               # BOT_SCREENS: Record<BotScreenId, BotScreen>
│   ├── speed/
│   │   └── timeline.ts                  # ZONES, BOT_BEATS, MANUAL_BEATS, HOUR_TICKS, helpers
│   ├── types/                           # см. секцию 1
│   │   ├── bot-screen.ts
│   │   ├── job.ts
│   │   ├── pricing.ts
│   │   ├── faq.ts
│   │   ├── feature.ts
│   │   ├── how-it-works.ts
│   │   └── index.ts
│   ├── seo/
│   │   ├── metadata.ts                  # дефолтный Metadata + helpers (canonical, og)
│   │   └── jsonld.ts                    # SoftwareApplication-объект
│   └── utils/
│       ├── cn.ts                        # clsx + tailwind-merge wrapper
│       └── markdown.ts                  # readMarkdownFile() из legal/* при build-time
├── styles/
│   └── globals.css                      # перенесён из app/ если хочется отдельной папки
│                                        # (решение Phase 0.2: оставить в app/globals.css)
├── public/
│   ├── og-image.png                     # 1200×630
│   ├── favicon.ico                      # на случай если App Router-icon не сработает
│   ├── apple-touch-icon.png             # 180×180
│   ├── icon-192.png                     # PWA
│   ├── icon-512.png                     # PWA
│   └── brand/                           # экспорт из brandbook.pen (vYOy1, cIcTM, …)
│       ├── mark.svg
│       ├── mark-512.png
│       └── lockup-horizontal.svg
├── tailwind.config.ts                   # см. секцию 3
├── postcss.config.js                    # autoprefixer + tailwindcss
├── next.config.mjs                      # output: 'export', images.unoptimized: true
├── tsconfig.json                        # strict, paths { '@/*': './*' }
├── package.json
└── README.md                            # как поднять / задеплоить
```

**Один файл = одна строка зачем (для верхнего уровня):**

- `app/layout.tsx` — корневой шаблон, грузит Inter, монтирует CookieBanner, задаёт `<html lang="ru">`.
- `app/page.tsx` — главная страница, секционная композиция.
- `app/globals.css` — Tailwind directives + CSS-переменные + 6 keyframes + utility-классы.
- `app/robots.ts` — отдаёт корневой robots.txt при `output: 'export'`.
- `app/sitemap.ts` — генерация sitemap.xml на этапе сборки.
- `app/manifest.ts` — PWA manifest (имя, иконки, theme-color).
- `app/icon.tsx` — динамический favicon через `next/og` (с фолбэком в `public/favicon.ico`).
- `app/privacy/page.tsx` — политика конфиденциальности сайта.
- `app/cookies/page.tsx` — политика cookie.
- `app/offer/page.tsx` — оферта (заглушка до готовности текста).
- `app/bot-privacy/page.tsx` — политика бота (заглушка).
- `tailwind.config.ts` — дизайн-токены проекта.
- `next.config.mjs` — `output: 'export'` для статической раздачи.

---

## 3. Tailwind config (финал)

Готов к копированию. Замечания после кода — обязательно прочитать.

```ts
// site/tailwind.config.ts
import type { Config } from 'tailwindcss';
import typography from '@tailwindcss/typography';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    // Override default screens (dropping sm:640 / md:768 / lg:1024 — не используется в дизайне)
    screens: {
      sm: '720px',  // мобильный плотный паддинг
      md: '960px',  // двухколоночные сетки → одноколоночные
      lg: '1240px', // контейнер
    },
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
        'bg-cream':   '#FFFBF0',
        'bg-dark':    '#1C1917',
        'bg-dark-2':  '#292524',
        card:         '#FFFFFF',
        'card-dark':  '#292524',
        // Text
        text:                 '#78350F',
        'text-heading':       '#92400E',
        'text-sub':           '#B45309',
        'text-muted':         '#A8A29E',
        'text-on-dark':       '#FEF3C7',
        'text-on-dark-sub':   '#FBBF24',
        // Lines (как именованные colors, чтобы доступны через border-line)
        line:                 'rgba(146, 64, 14, 0.12)',
        'line-strong':        'rgba(146, 64, 14, 0.22)',
        'line-dark':          'rgba(254, 243, 199, 0.12)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      fontSize: {
        // Кастомные кегли с line-height и letter-spacing — точное соответствие styles.css
        h1:    ['clamp(44px, 6vw, 80px)', { lineHeight: '1.02', letterSpacing: '-0.03em', fontWeight: '900' }],
        h2:    ['clamp(32px, 4vw, 52px)', { lineHeight: '1.05', letterSpacing: '-0.02em', fontWeight: '800' }],
        h3:    ['clamp(30px, 3.4vw, 44px)', { lineHeight: '1.10', letterSpacing: '-0.02em', fontWeight: '800' }],
        lead:  ['19px', { lineHeight: '1.55', fontWeight: '500' }],
        body:  ['16px', { lineHeight: '1.55', fontWeight: '500' }],
        small: ['13px', { lineHeight: '1.5',  fontWeight: '500' }],
        eyebrow: ['12px', { lineHeight: '1', letterSpacing: '0.02em', fontWeight: '600' }],
      },
      borderRadius: {
        xs:   '8px',
        sm:   '12px',
        md:   '18px',
        lg:   '24px',
        xl:   '32px',
        // pill: используем встроенный 'full' (= 9999px), отдельный токен не нужен
      },
      boxShadow: {
        sm:           '0 1px 2px rgba(120,53,15,0.06), 0 2px 6px rgba(120,53,15,0.04)',
        md:           '0 4px 14px rgba(120,53,15,0.08), 0 12px 32px rgba(120,53,15,0.06)',
        lg:           '0 12px 40px rgba(120,53,15,0.12), 0 30px 80px rgba(120,53,15,0.08)',
        brand:        '0 20px 50px rgba(219,39,119,0.22), 0 6px 18px rgba(249,115,22,0.24)',
        'brand-hover':'0 24px 60px rgba(219,39,119,0.30), 0 8px 22px rgba(249,115,22,0.30)',
        // Для mockup-телефона (real-bot.jsx:23)
        phone:        '0 30px 80px rgba(28,25,23,0.25), 0 10px 24px rgba(28,25,23,0.12), inset 0 0 0 1px rgba(255,255,255,0.06)',
      },
      backgroundImage: {
        // Только normal — subtle/intense пресеты были в tweaks-panel, в прод не идут
        'brand-gradient': 'linear-gradient(135deg, #FBBF24 0%, #F97316 33%, #EF4444 66%, #DB2777 100%)',
      },
      keyframes: {
        'slide-in-from-right': {
          '0%':   { transform: 'translateX(120%) rotate(8deg)', opacity: '0' },
          '60%':  { opacity: '1' },
          '100%': { transform: 'translateX(0) rotate(0deg)', opacity: '1' },
        },
        'swipe-right': {
          '0%':   { transform: 'translate(0, 0) rotate(0deg)',          opacity: '1' },
          '100%': { transform: 'translate(120%, -30px) rotate(18deg)',  opacity: '0' },
        },
        'swipe-left': {
          '0%':   { transform: 'translate(0, 0) rotate(0deg)',           opacity: '1' },
          '100%': { transform: 'translate(-120%, -30px) rotate(-18deg)', opacity: '0' },
        },
        'pulse-ring': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(219, 39, 119, 0.5)' },
          '50%':      { boxShadow: '0 0 0 14px rgba(219, 39, 119, 0)' },
        },
        'typing-dots': {
          '0%, 60%, 100%': { transform: 'translateY(0)',     opacity: '0.3' },
          '30%':           { transform: 'translateY(-4px)',  opacity: '1' },
        },
        'float-y': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
      },
      animation: {
        'slide-in-from-right': 'slide-in-from-right 0.5s cubic-bezier(.2,.8,.2,1)',
        'slide-in-features':   'slide-in-from-right 0.6s cubic-bezier(.2,.8,.2,1)',
        'swipe-right':         'swipe-right 0.45s cubic-bezier(.2,.8,.2,1) forwards',
        'swipe-left':          'swipe-left 0.45s cubic-bezier(.2,.8,.2,1) forwards',
        'pulse-ring':          'pulse-ring 2.5s infinite',
        'typing-dots':         'typing-dots 1.2s infinite',
        'float-y':             'float-y 4s ease-in-out infinite',
      },
      maxWidth: {
        container: '1240px',
        prose:     '760px',  // legal-страницы и FAQ контент-ширина
        narrow:    '720px',  // section-head
        cards:     '880px',  // pricing-grid
      },
      spacing: {
        // Дополнения к дефолтной шкале
        18: '4.5rem',  // 72px — высота Nav
        22: '5.5rem',  // 88px
        26: '6.5rem',  // 104px
        30: '7.5rem',  // 120px — section padding desktop
      },
      transitionTimingFunction: {
        smooth: 'cubic-bezier(.2,.8,.2,1)', // тот же easing что в keyframes
      },
    },
  },
  plugins: [
    typography, // markdown rendering для /privacy, /cookies, /offer
  ],
};

export default config;
```

**Замечания:**
1. `screens` мы переопределяем (не extend) — стандартные брейкпоинты Tailwind не используются дизайном, иначе `md:` начнёт срабатывать в 768px вместо 960px и поломает сетки.
2. `colors.line` / `line-strong` / `line-dark` дают доступ через `border-line`, `border-line-strong` — Tailwind 3+ умеет такой ключ.
3. `boxShadow.phone` добавлен сверх brand-tokens.md — он нужен для `RealBotScreen` (real-bot.jsx:23) и встречается дважды в исходнике.
4. `backgroundImage.brand-gradient` — единственный пресет (subtle/intense выкинуты вместе с tweaks-panel).
5. `darkMode` не выставляется — Features-секция на тёмном фоне работает через явные классы (`bg-bg-dark`, `text-text-on-dark`), а не через `dark:` variant. Если в Phase 2 захотим toggle — переключим на `darkMode: 'class'`.

---

## 4. globals.css (финал)

Содержимое `site/app/globals.css`. Каждая секция прокомментирована.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* ============================================================
 * CSS-переменные (для inline-стилей, которые остаются в РИДЕ)
 * Дублируют Tailwind-токены — нужны там, где Tailwind не вписывается:
 *   - dynamic background-image в JobCard (job.color)
 *   - inline halo-blob colors из data
 *   - старый код, импортирующий var(--brand-gradient)
 * ============================================================ */
:root {
  --amber:  #FBBF24;
  --orange: #F97316;
  --red:    #EF4444;
  --pink:   #DB2777;

  --bg:           #FAFAF9;
  --bg-pastel:    #FEF3C7;
  --bg-pastel-2:  #FDE68A;
  --bg-dark:      #1C1917;

  --text:           #78350F;
  --text-heading:   #92400E;
  --text-sub:       #B45309;
  --text-on-dark:   #FEF3C7;
  --text-on-dark-sub: #FBBF24;

  --line:        rgba(146, 64, 14, 0.12);
  --line-strong: rgba(146, 64, 14, 0.22);
  --line-dark:   rgba(254, 243, 199, 0.12);

  --brand-gradient: linear-gradient(135deg, #FBBF24 0%, #F97316 33%, #EF4444 66%, #DB2777 100%);

  --shadow-sm:    0 1px 2px rgba(120, 53, 15, 0.06), 0 2px 6px rgba(120, 53, 15, 0.04);
  --shadow-md:    0 4px 14px rgba(120, 53, 15, 0.08), 0 12px 32px rgba(120, 53, 15, 0.06);
  --shadow-lg:    0 12px 40px rgba(120, 53, 15, 0.12), 0 30px 80px rgba(120, 53, 15, 0.08);
  --shadow-brand: 0 20px 50px rgba(219, 39, 119, 0.22), 0 6px 18px rgba(249, 115, 22, 0.24);
  --shadow-phone: 0 30px 80px rgba(28, 25, 23, 0.25), 0 10px 24px rgba(28, 25, 23, 0.12), inset 0 0 0 1px rgba(255, 255, 255, 0.06);
}

/* ============================================================
 * @layer base — дефолты HTML-элементов
 * ============================================================ */
@layer base {
  * { box-sizing: border-box; }

  html, body {
    margin: 0;
    padding: 0;
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-inter), -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 16px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
    scroll-behavior: smooth;
  }

  body { overflow-x: hidden; }

  button {
    font-family: inherit;
    cursor: pointer;
    border: none;
    background: none;
    color: inherit;
  }

  a { color: inherit; text-decoration: none; }

  /* Глобальный focus ring — обязательный для a11y, не убирать.
     Apply через :focus-visible, чтобы мышь не показывала рамку. */
  :focus-visible {
    outline: 2px solid var(--orange);
    outline-offset: 3px;
    border-radius: 4px;
  }

  /* Скрыть скроллбар внутри телефона-мокапа */
  .phone-scroll::-webkit-scrollbar { display: none; }
  .phone-scroll { scrollbar-width: none; }
}

/* ============================================================
 * @layer components — повторяющиеся паттерны через @apply
 * Решение: utility-классы, а не отдельные React-компоненты, для:
 *   - .btn-primary / .btn-ghost / .btn-dark — потому что их зовут
 *     и из <a>, и из <button>, и из <Link>, проще единый класс.
 *   - .grad-text — однострочное применение в JSX внутри <h1>.
 *   - .eyebrow / .eyebrow-dot — встречаются в каждой секции.
 * ============================================================ */
@layer components {
  .btn {
    @apply inline-flex items-center gap-[10px] rounded-full font-bold whitespace-nowrap;
    @apply transition-[transform,box-shadow,background] duration-150;
    padding: 14px 22px;
    font-size: 15px;
  }
  .btn:hover  { transform: translateY(-1px); }
  .btn:active { transform: translateY(0); }

  .btn-primary {
    background: var(--brand-gradient);
    color: #fff;
    box-shadow: var(--shadow-brand);
  }
  .btn-primary:hover {
    box-shadow: 0 24px 60px rgba(219, 39, 119, 0.3),
                0 8px 22px rgba(249, 115, 22, 0.3);
  }

  .btn-ghost {
    @apply bg-transparent;
    color: var(--text-heading);
    border: 1px solid var(--line-strong);
  }
  .btn-ghost:hover { background: rgba(146, 64, 14, 0.05); }

  .btn-dark {
    background: #1C1917;
    color: #fff;
  }
  .btn-dark:hover { background: #000; }

  .grad-text {
    background: var(--brand-gradient);
    -webkit-background-clip: text;
            background-clip: text;
    color: transparent;
    -webkit-text-fill-color: transparent;
  }

  .eyebrow {
    @apply inline-flex items-center gap-2 rounded-full uppercase;
    padding: 6px 14px;
    background: var(--bg-pastel);
    color: var(--text-heading);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.02em;
    border: 1px solid var(--line);
  }

  .eyebrow-dot {
    @apply rounded-full;
    width: 6px;
    height: 6px;
    background: var(--brand-gradient);
  }

  /* Декоративный halo-блоб — используется в Hero и Features */
  .halo {
    @apply absolute pointer-events-none rounded-full;
    filter: blur(80px);
    opacity: 0.35;
    z-index: 0;
  }

  /* SVG-noise-overlay для тёмной секции Features */
  .noise {
    @apply absolute inset-0 pointer-events-none;
    opacity: 0.04;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  }

  /* tabular-nums для счётчиков */
  .tabular {
    font-variant-numeric: tabular-nums;
  }
}

/* ============================================================
 * Markdown-страницы (privacy, cookies, offer)
 * Используется через <article className="prose-legal">
 * Поверх @tailwindcss/typography .prose, с нашими токенами.
 * ============================================================ */
.prose-legal {
  --tw-prose-body:    var(--text);
  --tw-prose-headings: var(--text-heading);
  --tw-prose-links:   var(--text-heading);
  --tw-prose-bold:    var(--text-heading);
  --tw-prose-hr:      var(--line);
  --tw-prose-quotes:  var(--text-sub);
  --tw-prose-code:    var(--text-heading);
  --tw-prose-counters: var(--text-sub);
  --tw-prose-bullets: var(--text-sub);
}
```

**Решение по утилитарным классам.** Используем `@layer components` + `@apply`, а не голые CSS-правила — преимущество: PurgeCSS не выбросит, и Tailwind-токены доступны единообразно. Исключение — `.grad-text`, `.halo`, `.noise`: там нужны property вне Tailwind (background-clip, blur(80px), data:URL), оставляем как чистый CSS.

---

## 5. Inline-стили из прототипа → Tailwind

Жёсткое правило для executor'а:

> **Inline `style={...}` допустим только в двух случаях:**
> 1. Значение динамическое — зависит от React state, props или вычисляется на лету (`transform: translateX(${anim}%)`, `style={{ background: job.color }}`).
> 2. Значение использует CSS-переменную, которой нет в Tailwind config (`background: 'var(--brand-gradient)'` — теперь покрыто `bg-brand-gradient`, поэтому уже не нужно).
>
> **Во всех остальных случаях — Tailwind classes.**

Маппинг по компонентам:

| Что в прототипе | Куда мигрирует |
|---|---|
| `style={{ display: 'flex', gap: 12, ... }}` | `className="flex gap-3 ..."` |
| `style={{ borderRadius: 24, padding: 32 }}` | `className="rounded-lg p-8"` (rounded-lg = 24px) |
| `style={{ background: 'var(--brand-gradient)' }}` | `className="bg-brand-gradient"` |
| `style={{ color: 'var(--text-heading)' }}` | `className="text-text-heading"` |
| `style={{ fontSize: 'clamp(44px, 6vw, 80px)' }}` | `className="text-h1"` (наш custom kegль) |
| `style={{ animation: 'slideInFromRight 0.5s ...' }}` | `className="animate-slide-in-from-right"` |
| `style={{ background: '#1C1917' }}` | `className="bg-bg-dark"` (если совпадает с токеном) или inline (если нет) |
| `style={{ position: 'absolute', top: -120, right: -120 }}` | `className="absolute -top-30 -right-30"` (или inline для нестандартных значений) |
| `style={{ transform: anim ? 'translateX(130%) ...' : 'none' }}` | inline остаётся (динамический) |
| `style={{ background: job.color }}` (JobCard) | inline остаётся (data-driven) |
| Halo-блоб с `width: 520, height: 520, background: '#FBBF24', top: -120, right: -120` | компонент `<HaloBlob>` с props `size`, `color`, `placement` или класс `.halo` + inline width/height/colors |
| Noise-overlay (SVG-турбуленция) | класс `.noise` (см. globals.css) |
| Анимации `slideInFromRight` итд | через `@keyframes` в Tailwind config + `animate-*` |
| `dangerouslySetInnerHTML` в RealBotScreen content | оставляем — данные статические, в нашем репо |

**Halo и Noise — компоненты или классы.** Решение: используем класс `.halo` для общих свойств (position, blur, pointer-events) и inline для динамики (width, height, color, координаты). Это короче, чем отдельный компонент `<HaloBlob>` ради 4 случаев использования.

```tsx
// Пример из Hero.tsx
<div className="halo" style={{ width: 520, height: 520, background: '#FBBF24', top: -120, right: -120 }} />
```

Если в Phase 2 halo понадобится больше пяти раз — рефакторим в `<HaloBlob>`.

---

## 6. Стратегия данных

Все массивы — отдельные `.ts`-модули с явным экспортом и типизацией.

### 6.1 `lib/data/hero-jobs.ts`

```ts
import type { JobCard } from '@/lib/types';

export const HERO_CHAT_JOBS: JobCard[] = [
  {
    title: 'Руководитель отдела продаж',
    company: 'Торговая компания',
    salary: 'от 170 000 ₽',
    location: 'Удалённо',
    schedule: 'Полная · 5/2 · 8 часов',
    experience: '1–3 года',
    match: 92,
    posted: 'Сегодня, 12 мин назад',
    duties: [
      'Управление командой менеджеров продаж',
      'Контроль выполнения плана и качества сделок',
      'Ежедневная отчётность собственнику',
    ],
    requirements: [
      'Опыт управления отделом продаж от 2 лет',
      'Уверенный пользователь CRM (amoCRM/Bitrix24)',
      'Системность, ориентация на результат',
    ],
  },
  // ... остальные 9 — копировать 1:1 из hero.jsx:114–315
];
```

### 6.2 `lib/data/sample-jobs.ts`

```ts
import type { JobCard } from '@/lib/types';

export const SAMPLE_JOBS: JobCard[] = [
  {
    title: 'Senior Product Designer',
    company: 'Yandex Eats',
    salary: 'от 320 000 ₽',
    location: 'Москва · Remote',
    match: 92,
    tags: ['Figma', 'Research', 'B2C'],
    color: 'linear-gradient(135deg, #FBBF24, #F97316)',
    abbr: 'YE',
  },
  // ... остальные 8 из hero-swipe.jsx:5–14
];
```

### 6.3 `lib/data/pricing.ts`

**Источник истины:** `docs/PRODUCT_FACTS.md` §5. Если в боте поменяли цены — обновить здесь и пере-собрать.

```ts
import type { PricingPlan } from '@/lib/types';

export const PRICING_PLANS: PricingPlan[] = [
  {
    id: 'free',
    name: 'Бесплатный',
    price: '0',
    unit: '₽',
    period: 'постоянно',
    sub: 'Чтобы попробовать',
    features: [
      '1 резюме (полный цикл)',
      '5 автооткликов с персональным письмом',
      '10 карточек в день',
      'Только режим «С подтверждением»',
      'Лог последних 5 откликов',
    ],
    cta: 'Попробовать',
    href: 'https://t.me/otklicker_bot',
    tone: 'light',
  },
  {
    id: 'active',
    name: 'Активный',
    price: '790',
    unit: '₽',
    period: 'за 3 недели',
    sub: 'Для активного поиска',
    badge: '37 ₽ в день',
    features: [
      'Безлимит резюме и версий',
      'До 15 откликов в день — лимит HH',
      'Безлимит карточек',
      'Оба режима: «С подтверждением» и «Автопилот»',
      'Персональные сопроводительные',
      'Автоответы HR',
      'Полная история откликов',
    ],
    cta: 'Оформить пакет',
    href: 'https://t.me/otklicker_bot',
    tone: 'brand',
  },
];
```

### 6.4 `lib/data/faq.ts`

```ts
import type { FAQItem } from '@/lib/types';

export const FAQ_ITEMS: FAQItem[] = [
  { id: 'ban',     q: 'Не забанит ли HH мой аккаунт?', a: '...' },
  { id: 'access',  q: 'Как вы получаете доступ к моему HH?', a: '...' },
  { id: 'cover',   q: 'Кто пишет сопроводительное?', a: '...' },
  { id: 'hr',      q: 'Что если HR напишет?', a: '...' },
  { id: 'refund',  q: 'Можно ли вернуть деньги?', a: '...' },
  { id: 'limits',  q: 'Что бот не делает?', a: '...' },
];
// Полные тексты — копировать 1:1 из more-sections.jsx:135–141
```

### 6.5 `lib/data/how-it-works.ts`

```ts
import type { HowItWorksStep } from '@/lib/types';

export const HOW_IT_WORKS_STEPS: HowItWorksStep[] = [
  { number: '01', title: 'Резюме за 7–10 минут',     description: '...', screen: 'onboarding' },
  { number: '02', title: 'Подключение HH',           description: '...', screen: 'hh-auth' },
  { number: '03', title: 'Фильтры и режим',          description: '...', screen: 'hh-panel' },
  { number: '04', title: 'Отклики и переписка с HR', description: '...', screen: 'vacancy' },
];
```

### 6.6 `lib/data/features.ts`

```ts
import type { Feature } from '@/lib/types';

export const FEATURES: Feature[] = [
  {
    id: 'auto',
    label: '01 · Автоотклики',
    headline: 'Отклики уходят в первые минуты',
    lead: '...',
    bullets: [
      'Два режима: «С подтверждением» и «Автопилот» (порог 75%)',
      'Лимит до 15 откликов в день — это лимит HH',
      'Мгновенная пауза одной кнопкой',
    ],
    screen: 'hh-panel',
  },
  { id: 'cards', label: '02 · Карточки и сопроводительные', /* ... */ screen: 'vacancy' },
  { id: 'menu',  label: '03 · Переписка с HR',              /* ... */ screen: 'main-menu' },
];
```

### 6.7 `lib/screens/bot-screens.ts`

```ts
import type { BotScreenMap } from '@/lib/types';

export const BOT_SCREENS: BotScreenMap = {
  onboarding: {
    content: `<span>Я первый бот автооткликов на <span style="color:#3390EC">HH.ru</span></span>
<br/><br/>
— Отправили 50 откликов — ни одного ответа?<br/>
...`,
    buttons: [
      { emoji: '📜', label: 'Оферта' },
      { emoji: '🔒', label: 'Конфиденциальность' },
      { emoji: '✅', label: 'Принимаю условия — начать', primary: true },
    ],
  },
  'main-menu': { /* ... */ },
  'hh-auth':   { /* ... */ },
  'hh-panel':  { /* ... */ },
  vacancy:     { /* ... */ },
};
```

### 6.8 `lib/data/nav.ts`

```ts
export const NAV_LINKS = [
  { href: '#how',      label: 'Как работает' },
  { href: '#features', label: 'Фичи' },
  { href: '#pricing',  label: 'Тарифы' },
  { href: '#faq',      label: 'FAQ' },
] as const;

export const FOOTER_LINKS = {
  product: [
    { href: '#how', label: 'Как работает' },
    { href: '#features', label: 'Фичи' },
    { href: '#pricing', label: 'Тарифы' },
  ],
  support: [
    { href: '#faq', label: 'FAQ' },
    { href: 'mailto:info@otklicker.ru', label: 'info@otklicker.ru' },
    { href: 'https://t.me/otklicker_support', label: 'Telegram-поддержка' },
  ],
  company: [
    { href: '/privacy', label: 'Политика данных' },
    { href: '/offer',   label: 'Оферта' },
    { href: '/cookies', label: 'Cookie' },
  ],
} as const;
```

---

## 7. App Router routes

| Route | Файл | Контент | Metadata | Sitemap | Canonical |
|---|---|---|---|---|---|
| `/` | `app/page.tsx` | Все секции главной + JSON-LD | title: "Откликер — Telegram-бот для автооткликов на HH.ru", description: лид из hero (~155 chars), og: 1200×630 статика | да, priority 1.0 | `https://otklicker.ru/` |
| `/privacy` | `app/privacy/page.tsx` | `<MarkdownPage>` рендерит `legal/PRIVACY_POLICY.md` (или новый `legal/SITE_PRIVACY_POLICY.md` — см. §9 Open вопросы) | title: "Политика конфиденциальности — Откликер", description: 1-я строка MD, og: дефолт сайта, robots: index | да, priority 0.3 | `https://otklicker.ru/privacy` |
| `/cookies` | `app/cookies/page.tsx` | `<MarkdownPage>` рендерит `legal/COOKIE_POLICY.md` (новый файл — см. §9) | title: "Политика cookie — Откликер" | да, priority 0.3 | `https://otklicker.ru/cookies` |
| `/offer` | `app/offer/page.tsx` | placeholder. До готовности окончательного текста рендерим `legal/OFFER_AGREEMENT.md` если он валиден, или плашку "Документ готовится" | title: "Оферта — Откликер" | да, priority 0.3 | `https://otklicker.ru/offer` |
| `/bot-privacy` | `app/bot-privacy/page.tsx` | placeholder для политики бота @otklicker_bot (отдельный документ от сайта) | title: "Политика бота @otklicker_bot — Откликер" | да, priority 0.2 | `https://otklicker.ru/bot-privacy` |
| `/robots.txt` | `app/robots.ts` | `User-agent: *\nAllow: /\nSitemap: https://otklicker.ru/sitemap.xml` | — | — | — |
| `/sitemap.xml` | `app/sitemap.ts` | URLs всех страниц | — | — | — |
| `/manifest.webmanifest` | `app/manifest.ts` | PWA-light: name, icons (192/512), theme_color #F97316 | — | — | — |
| `/icon.png` | `app/icon.tsx` | Динамическая 32×32 favicon с gradient mark | — | — | — |
| `/apple-icon.png` | `app/apple-icon.tsx` | 180×180 apple-touch-icon | — | — | — |

**Решение по 404.** `app/not-found.tsx` — простая страница с "Страница не найдена" и ссылкой на главную. Не в sitemap.

**Решение по `/offer` и `/bot-privacy`.** Оба — placeholders в Phase 1. `/offer` пытается рендерить `legal/OFFER_AGREEMENT.md` (он есть, 325 строк); если в нём шаблонные `{{переменные}}`, рендерим заглушку. `/bot-privacy` — отдельный документ, на момент Phase 0.2 файла нет, делаем плейсхолдер «Политика @otklicker_bot готовится».

---

## 8. SEO baseline

**Что architect фиксирует, реализует Phase 4.**

### 8.1 HTML lang

```tsx
// app/layout.tsx
<html lang="ru" className={inter.variable}>
```

### 8.2 Inter via next/font/google

```tsx
// app/layout.tsx
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500', '600', '700', '800', '900'],
  display: 'swap',
  variable: '--font-inter',
});
```

### 8.3 JSON-LD на главной

```ts
// lib/seo/jsonld.ts
export const SOFTWARE_APPLICATION_LD = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Откликер',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Telegram',
  description: 'Telegram-бот для автооткликов на HH.ru. Резюме за 7–10 минут, отклики в первые минуты, ответы HR в Telegram.',
  url: 'https://otklicker.ru/',
  inLanguage: 'ru-RU',
  offers: [
    {
      '@type': 'Offer',
      name: 'Бесплатный',
      price: '0',
      priceCurrency: 'RUB',
      availability: 'https://schema.org/InStock',
    },
    {
      '@type': 'Offer',
      name: 'Активный',
      price: '790',
      priceCurrency: 'RUB',
      availability: 'https://schema.org/InStock',
      priceSpecification: {
        '@type': 'UnitPriceSpecification',
        price: '790',
        priceCurrency: 'RUB',
        billingDuration: 'P21D', // ISO 8601 — 21 день
        unitText: 'package',
      },
    },
  ],
  publisher: {
    '@type': 'Organization',
    name: 'Откликер',
    url: 'https://otklicker.ru/',
  },
} as const;
```

Вставляется в `app/page.tsx` как `<script type="application/ld+json">{JSON.stringify(SOFTWARE_APPLICATION_LD)}</script>`.

### 8.4 OG-image — статика

Решение: статика 1200×630 PNG в `public/og-image.png`. Источник — экспорт из `brandbook.pen` (`BRhwP` — TG cover 1280×640) с обрезкой/доводкой в графическом редакторе. Динамический `next/og` через `app/opengraph-image.tsx` не используем — статика проще, кешируется CDN, не требует runtime.

### 8.5 Twitter card

`twitter:card = summary_large_image`, `twitter:image = /og-image.png`, `twitter:title`, `twitter:description` — те же что и og.

### 8.6 Дефолтная Metadata

```ts
// lib/seo/metadata.ts
import type { Metadata } from 'next';

export const defaultMetadata: Metadata = {
  metadataBase: new URL('https://otklicker.ru'),
  title: {
    default: 'Откликер — Telegram-бот для поиска работы на HH.ru',
    template: '%s — Откликер',
  },
  description:
    'Бот следит за лентой HH и отправляет отклик в первые минуты после публикации. Резюме за 7–10 минут, отклики и переписка с HR — в одном Telegram.',
  applicationName: 'Откликер',
  keywords: ['HH.ru', 'отклики', 'Telegram-бот', 'поиск работы', 'AI-резюме'],
  openGraph: {
    type: 'website',
    locale: 'ru_RU',
    siteName: 'Откликер',
    title: 'Откликер — Telegram-бот для поиска работы на HH.ru',
    description: '...',
    url: 'https://otklicker.ru/',
    images: [{ url: '/og-image.png', width: 1200, height: 630, alt: 'Откликер' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Откликер — Telegram-бот для поиска работы на HH.ru',
    description: '...',
    images: ['/og-image.png'],
  },
  alternates: { canonical: '/' },
  robots: { index: true, follow: true },
};
```

### 8.7 Sitemap

`app/sitemap.ts` отдаёт массив `[{ url: 'https://otklicker.ru/', lastModified: new Date(), priority: 1.0 }, …]` с пятью URL: `/`, `/privacy`, `/cookies`, `/offer`, `/bot-privacy`.

---

## 9. Open вопросы / риски

1. **Финальный текст OG-image.** Решение в Phase 4 — взять `BRhwP` из `brandbook.pen`, экспортировать через `mcp__pencil__export_nodes`, обрезать до 1200×630, наложить заголовок «Откликается на свежие вакансии за вас». Сейчас фактического файла нет — Phase 1 кладёт plaсeholder.

2. **Мобильный логотип.** `BrandLockup size="sm"` (icons.jsx:103) уже скрывает подзаголовок, для мобильного отдельная версия не нужна. Если в будущем понадобится укоротить до иконки — добавим вариант `size="xs"` без текста.

3. **Cookie-consent state.** Решение: `useState` + `useEffect` для чтения `localStorage.getItem('otklicker.cookie-consent')` на mount. Без сервиса аналитики (метрика подключается по согласию). Storage key в Props компонента (`storageKey?: string`). Не Cookie API — баннер ничего не сохраняет в фактические cookies.

4. **AAAA-запись на IPv6.** Не блокирующий вопрос для Phase 1 (статика на любом hosting). Если хостинг (Vercel / Netlify / s3) даёт dual-stack — берём бесплатно. Решение DNS — отдельная задача в Phase 5 (deploy).

5. **Файл `legal/SITE_PRIVACY_POLICY.md`.** В репо сейчас `legal/PRIVACY_POLICY.md` (250 строк). Не очевидно, эта политика — для бота или для сайта. **Action для Phase 1:** проверить и при необходимости разделить на `legal/SITE_PRIVACY_POLICY.md` (для лендинга) и `legal/BOT_PRIVACY_POLICY.md` (для @otklicker_bot). Документ `legal/COOKIE_POLICY.md` сейчас отсутствует — нужен новый. До его готовности `/cookies` рендерит плашку «Документ готовится».

6. **Email рассинхрон.** В `more-sections.jsx:271`: `mailto:hi@otklicker.app`, label `info@otklicker.ru`. **Решение:** в `lib/data/nav.ts` сразу прописать `info@otklicker.ru` и href, и label.

7. **Telegram-иконка в lucide-react.** В пакете `lucide-react` есть `Send` и `Telegram` (последняя — нет точного аналога, но `Send` визуально похожа). Решение: в Phase 1 используем `Send` из lucide для CTA. Если визуально не подойдёт — возьмём кастомный SVG из текущего `icons.jsx:53–55` и положим как `components/ui/IconTelegram.tsx`.

8. **Дублирующая `Zap2`.** В `icons.jsx:56` это копия `Zap` с другим stroke. Не используется в дизайне — выбрасываем при миграции.

9. **MousePointerClick.** В lucide-react есть `MousePointerClick` (точное имя). Если в текущей версии пакета нет — берём кастомный SVG из `icons.jsx:6–10`.

10. **Static export и server actions.** `output: 'export'` запрещает server actions, dynamic route handlers и middleware. На Phase 1 это ок (форм нет, всё в Telegram). Если в Phase 6 понадобится форма (например, web-to-lead) — переедем на гибридный mode.

11. **Variant Hero по умолчанию.** В прототипе `tweaks-panel.jsx` позволяла переключать `chat` ↔ `swipe`. Phase 0.2 фиксирует **default `chat`** (он визуально богаче и нативнее под Telegram-нарратив). `swipe` остаётся в коде как `<HeroSwipe />`, готовый к включению через prop.

12. **legal/PRIVACY_POLICY.md vs PRODUCT_FACTS.md синк.** Если политика говорит «храним пароль 30 дней», а PRODUCT_FACTS говорит «не храним пароль» — будет противоречие. **Action:** при подключении MD-файла на `/privacy` executor должен прочитать его и сравнить с PRODUCT_FACTS §7. Если расходится — флагнуть в issue, не публиковать.

13. **react-markdown и SVG/HTML.** Если в legal-MD есть `<table>` или `<details>` — `react-markdown` их рендерит, но требует `rehype-raw`. Решение: подключить `rehype-raw` в `<MarkdownPage>` сразу, чтобы не возвращаться.

14. **Анимация в HeroChat при `prefers-reduced-motion`.** Сейчас auto-cycle жмёт каждые 3 секунды. Для a11y — обернуть в `useReducedMotion()` (свой хук, читает media query), при `reduce` — отключить auto-cycle (показывать первую вакансию статически). **Action:** добавить в чеклист Phase 1.

---

## 10. Чеклист для Phase 1 (executor скелетон)

15 actionable пунктов. Каждый — верифицируемый «готово / не готово».

1. **Поднять Next.js 14 в `site/`.** `npx create-next-app@14 site --ts --tailwind --eslint --app --src-dir=false --import-alias '@/*'`. Verify: `cd site && npm run build` зелёный.

2. **Скопировать `tailwind.config.ts` из §3.** Установить `@tailwindcss/typography`. Verify: `npm run build` без ошибок темы; класс `bg-brand-gradient` доступен в JSX и применяется в браузере.

3. **Создать `app/globals.css` из §4.** Verify: `body` имеет нужный fallback fontstack; `:focus-visible` показывает orange outline на `<a>`.

4. **Подключить Inter через `next/font/google`** в `app/layout.tsx` с переменной `--font-inter`, subsets `['latin', 'cyrillic']`, weights `[400, 500, 600, 700, 800, 900]`, `display: 'swap'`. Verify: dev-tools в Network показывает `inter-cyrillic-*.woff2` загрузки; `getComputedStyle(body).fontFamily` начинается с `Inter`.

5. **Создать все типы из §1.** `lib/types/{bot-screen,job,pricing,faq,feature,how-it-works,index}.ts`. Verify: `tsc --noEmit` без ошибок; импорт `import type { JobCard } from '@/lib/types'` работает.

6. **Создать data-модули из §6.** `lib/data/*.ts` + `lib/screens/bot-screens.ts`. Скопировать массивы 1:1 из `.jsx`-источников. Verify: длины массивов совпадают (HERO_CHAT_JOBS = 10, SAMPLE_JOBS = 9, FAQ_ITEMS = 6, PRICING_PLANS = 2, BOT_SCREENS keys = 5).

7. **Реализовать `components/ui/`** (Button, Eyebrow, GradientText, SectionHead). Verify: storybook не нужен, делаем визуальный smoke на `app/page.tsx` черновом.

8. **Реализовать `components/Brand.tsx`** (BrandMark + BrandLockup) с импортом lucide-react `MousePointerClick`. Verify: `<BrandLockup size="sm">` в Nav рендерится 36×36 mark + текст «откликер» (lowercase per CLAUDE.md, **проверить** — в исходнике `icons.jsx:109` написано «Откликер» с заглавной).

9. **Реализовать `components/RealBotScreen.tsx`** с поддержкой `dangerouslySetInnerHTML` для `content` и нормализацией `KeyboardRow` (single button vs array). Verify: рендер `BOT_SCREENS.onboarding` визуально совпадает с прототипом по скриншоту.

10. **Реализовать секционные компоненты** (Nav, Hero, HeroChat, HeroSwipe, HowItWorks, Features, Pricing, PriceCard, FAQ, FinalCTA, Footer). Inline-стили — только динамические, остальное Tailwind. Verify: `npm run dev`, открыть `/`, скроллить — все секции видны, layout совпадает с прототипом на 1240/960/720px.

11. **Реализовать `components/SpeedSection.tsx`** (большой, ~400 строк) с IntersectionObserver и RAF. Использовать `useReducedMotion()` для отключения auto-play. Verify: при первом скролле в секцию запускается анимация playhead; при `prefers-reduced-motion: reduce` — статичный финальный кадр.

12. **Реализовать `components/CookieBanner.tsx`** с `useState` + `useEffect` поверх `localStorage`. Verify: первое посещение → баннер виден; «Принять» → `localStorage.otklicker.cookie-consent = 'accepted'`, баннер исчезает; reload → баннер не появляется.

13. **Создать routes** `/privacy`, `/cookies`, `/offer`, `/bot-privacy` с `<MarkdownPage>` или плашкой-плейсхолдером. Подключить `react-markdown` + `rehype-raw` + Tailwind `prose-legal`. Verify: `/privacy` рендерит markdown с правильными цветами заголовков (text-heading); ссылки в тексте open in new tab если absolute, иначе same tab.

14. **Создать `app/sitemap.ts`, `app/robots.ts`, `app/manifest.ts`, `app/icon.tsx`, `lib/seo/{metadata,jsonld}.ts`.** Подключить `defaultMetadata` в `app/layout.tsx`. Вставить JSON-LD на `/`. Verify: `curl http://localhost:3000/sitemap.xml` отдаёт XML с 5 URL; `view-source:/` содержит `<script type="application/ld+json">`.

15. **Настроить `next.config.mjs`** с `output: 'export'`, `images.unoptimized: true`, `trailingSlash: true` (для статики на S3-like хостингах). Запустить `npm run build` — должна сгенериться `out/` с готовыми HTML. Verify: `out/index.html` существует и содержит full hero copy; `out/privacy/index.html` — рендер MD; `out/sitemap.xml` валидный.

---

## Сводка по решениям

| Вопрос | Решение | Где зафиксировано |
|---|---|---|
| CSS framework | Tailwind, не CSS Modules | §3 |
| Anim engine | Tailwind keyframes + `useState`/`useEffect` | §3, §10.11 |
| Icon lib | `lucide-react` + 1–2 кастомных SVG (Telegram, MousePointerClick fallback) | §9.7, §9.9 |
| Hero variant default | `chat` | §9.11 |
| OG-image | статика 1200×630 в `public/` | §8.4 |
| Dark mode toggle | не делаем | §3 (комм), §9 |
| Cookie-consent storage | `localStorage`, не cookie API | §9.3 |
| Subtle/intense gradient presets | не тащим | §3 (комм) |
| Tweaks-panel | не тащим | §10 |
| speed.v1.jsx | не тащим | (вне scope) |
| Inline `style={...}` | только динамика | §5 |
| Output | `export` (статика) | §10.15 |

---

**Документ готов для Phase 1.** Объём ~830 строк, типы typesafe, Tailwind config копируемый, чеклист actionable.

---
