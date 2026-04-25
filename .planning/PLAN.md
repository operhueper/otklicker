# План реализации лендинга otklicker.ru

Дата: 2026-04-25
Цель: задеплоить https://otklicker.ru с SSL, CI/CD, SEO baseline на Hetzner CAX21 (204.168.178.241).

## Сводка

- Стек: Next.js 14 App Router + TypeScript strict + Tailwind, `output: 'export'`, nginx, Let's Encrypt, GitHub Actions deploy.
- Репо: `otklicker` (private), trunk-based в `main`, GH Actions деплоит на push.
- Фаз: 7 (Phase 0 закрыта артефактами в `.planning/`).
- Параллелизм: где безопасно, агенты запускаются одновременно. Внутри Phase 2 — все компоненты в параллель.
- Типичная длительность: ~8-10 часов чистого времени агентов от старта Phase 1 до зелёного Lighthouse в Phase 7.

## Контракт ответственности оркестратора

- Не делает сам то, что может сделать агент.
- Отчитывается по завершении каждой фазы (1-2 строки + ссылка на артефакт).
- При блокере вызывает `AskUserQuestion` с конкретными вариантами, не зависает молча.
- Перед risky действиями (DNS A/AAAA, перезагрузка nginx, certbot run, push в main, force push) подтверждает у пользователя.
- В конце каждой фазы коммитит атомарно: `feat:`, `fix:`, `chore:`, `docs:`, `ci:`.

## Граф зависимостей фаз (DAG)

```
Phase 1 (scaffold) ──┐
                     ├─→ Phase 2 (components) ──┐
                     ├─→ Phase 3 (legal) ───────┤
                     ├─→ Phase 4 (SEO+assets) ──┼─→ Phase 6 (review) ──→ Phase 7 (verify)
                     └─→ Phase 5 (deploy infra) ┘
```

Phase 3, 4, 5 стартуют сразу после Phase 1 — у них с Phase 2 общий только `app/layout.tsx`, который к этому моменту стабилен. Phase 6 ждёт всех. Phase 7 — финальная.

---

## Phase 1 — Скаффолд (Sonnet, ~30-40 мин)

### Задачи

| ID | Задача | Агент | Модель | Артефакт | Зависит от |
|----|--------|-------|--------|----------|------------|
| 1.1 | `gh repo create otklicker --private`. `git init`, базовые `.gitignore` (Node, Next, .DS_Store, `out/`, `.next/`, `*.log`, `.env*`), `README.md` (как локально запустить + структура), `CLAUDE.md` (правила голоса бренда + memo для будущих сессий) | executor | sonnet | новый репо на GH | — |
| 1.2 | `npx create-next-app@14 site --ts --tailwind --eslint --app --src-dir=false --import-alias '@/*'`. Затем настроить `next.config.mjs` (`output: 'export'`, `images.unoptimized: true`, `trailingSlash: true`). Подключить Inter в `app/layout.tsx` через `next/font/google` с `subsets: ['latin','cyrillic']`, weights `[400,500,600,700,800,900]`, `display: 'swap'`, `variable: '--font-inter'`. Установить `lucide-react`, `@tailwindcss/typography`, `clsx`, `tailwind-merge`, `react-markdown`, `rehype-raw` | executor | sonnet | `site/package.json`, `site/next.config.mjs`, `site/app/layout.tsx` | 1.1 |
| 1.3 | Создать структуру: `promo/{artem,content,seo,analytics}/`, `legal/`, `deploy/{nginx,scripts}/`, `docs/`, `.github/workflows/`. Скопировать (не переместить) `otklicker-promo/docs/PRODUCT_FACTS.md`, `docs/ARTEM_CHATS.md`, `docs/ARTEM_CHATS_VERIFIED.md` в `otklicker/docs/`. Скопировать `otklicker-promo/marketing-engine/` целиком в `otklicker/marketing-engine/` (не перемещать). Скопировать `.planning/` целиком в новый репо | executor | sonnet | папки + 4 .md + marketing-engine/ + .planning/ | 1.1 |
| 1.4 | Перенести `tailwind.config.ts` дословно из `architecture.md` §3 (готовый сниппет ~150 строк). Перенести `app/globals.css` дословно из `architecture.md` §4. Установить `@tailwindcss/typography` если не установлен в 1.2. Verify: `bg-brand-gradient` доступен, `:focus-visible` даёт orange outline | executor | sonnet | `site/tailwind.config.ts`, `site/app/globals.css` | 1.2 |
| 1.5 | Создать все типы из `architecture.md` §1 в `site/lib/types/{bot-screen,job,pricing,faq,feature,how-it-works,index}.ts`. Verify: `npx tsc --noEmit` без ошибок | executor | sonnet | `site/lib/types/*.ts` | 1.4 |

### Параллелизм

```
1.1 ─→ 1.2 ─┐
       1.3 ─┴─→ 1.4 ─→ 1.5
```

1.2 и 1.3 после 1.1 параллельно. 1.4 ждёт 1.2 (нужен `tailwind.config.ts` от create-next-app, перезаписывается). 1.5 ждёт 1.4 (типы используют типографические токены опосредованно — нет, они независимы; но логически правильно после конфига).

### Критерии приёмки Phase 1

- [ ] `gh repo view otklicker` показывает private репо
- [ ] `cd site && npm run build` собирается без ошибок (пустая страница из create-next-app — ОК)
- [ ] `cd site && npm run dev` стартует на :3000, страница открывается
- [ ] `site/tailwind.config.ts` содержит палитру и `bg-brand-gradient` (smoke: добавить временно `<div class="bg-brand-gradient h-20"/>` в `page.tsx`, проверить градиент в браузере, потом убрать)
- [ ] Inter подключён через `next/font/google` (Network tab показывает `inter-cyrillic-*.woff2`)
- [ ] `npx tsc --noEmit` зелёный
- [ ] В новом репо есть `marketing-engine/`, `docs/{PRODUCT_FACTS.md,ARTEM_CHATS.md,ARTEM_CHATS_VERIFIED.md}`, `promo/{artem,content,seo,analytics}/` (пустые), `.planning/`
- [ ] `git log --oneline` показывает чистые conventional-commits

### Промт для executor (1.1)

```
Создай GitHub-репо otklicker (приватный). Инициализируй git, добавь .gitignore (Node + Next.js + macOS), README.md с разделами «Запуск локально / Структура / Деплой», CLAUDE.md с правилами голоса бренда из docs/PRODUCT_FACTS.md §9. Сделай первый коммит chore: initial scaffold.
```

---

## Phase 2 — Миграция компонентов (Sonnet, параллельно, ~1.5-2 ч)

Каждая ветка параллельная. Источник — JSX-файлы прототипа в `design_handoff_otklicker_landing/source/components/`. Целевые — `site/components/*.tsx` и `site/lib/data/*.ts`. Перед стартом каждой ветки: `executor` читает `.planning/component-map.md`, `.planning/architecture.md` §1-§5, исходный JSX.

### Задачи

| ID | Задача | Агент | Модель | Артефакт | Зависит от |
|----|--------|-------|--------|----------|------------|
| 2.1 | `lib/data/*` + `lib/screens/bot-screens.ts`: HERO_CHAT_JOBS (10 шт из `hero.jsx:114-315`), SAMPLE_JOBS (9 шт из `hero-swipe.jsx:5-15`), HOW_IT_WORKS_STEPS (4 из `sections.jsx:8-28`), FEATURES (3 из `sections.jsx:102-126`), PRICING_PLANS (2 из `more-sections.jsx:8-43`, синк с `PRODUCT_FACTS.md` §5), FAQ_ITEMS (6 из `more-sections.jsx:135-141`), NAV_LINKS + FOOTER_LINKS, BOT_SCREENS (5 экранов из `real-bot.jsx:147-235`). 1:1 копия массивов, type-safe | executor | sonnet | `site/lib/data/*.ts`, `site/lib/screens/bot-screens.ts` | 1.5 |
| 2.2 | `lib/speed/timeline.ts`: ZONES, BOT_BEATS, MANUAL_BEATS, HOUR_TICKS из `speed.jsx:40-56,91-111` + helpers (`progressToMinute`, `minuteToPct`) | executor | sonnet | `site/lib/speed/timeline.ts` | 1.5 |
| 2.3 | `components/ui/`: `Button.tsx` (primary/ghost/dark, asChild для `<a>`), `Eyebrow.tsx`, `GradientText.tsx`, `SectionHead.tsx`, `HaloBlob.tsx`, `Noise.tsx`. На Tailwind, минимум inline. `lib/utils/cn.ts` (clsx + tailwind-merge) | executor | sonnet | `site/components/ui/*.tsx`, `site/lib/utils/cn.ts` | 1.5 |
| 2.4 | `components/Brand.tsx` (BrandMark, BrandLockup) с lucide `MousePointerClick`. Проверить — в прототипе пишется «Откликер» с заглавной (`icons.jsx:109`), но `CLAUDE.md` требует lowercase «откликер». **Использовать lowercase везде.** | executor | sonnet | `site/components/Brand.tsx` | 1.5 |
| 2.5 | `components/RealBotScreen.tsx`. Поддержка `dangerouslySetInnerHTML` для `content` (см. `architecture.md` §1.1 — допустимо), нормализация `KeyboardRow` (single button vs array из 2). Тёмная тема `#17212B/#182533/#FCD34D`. Использовать `boxShadow.phone` из tailwind | executor | sonnet | `site/components/RealBotScreen.tsx` | 2.3 |
| 2.6 | `components/Nav.tsx` из `hero.jsx:Nav` — sticky, blur при скролле, links из `NAV_LINKS`, CTA на `https://t.me/otklicker_bot` | executor | sonnet | `site/components/Nav.tsx` | 2.3, 2.4 |
| 2.7 | `components/Hero.tsx` + `components/HeroChat.tsx` из `hero.jsx`. Default variant — `chat` (architecture §9.11). HeroChat: `useState` для idx/sent/skipped/response/anim/paused, auto-cycle 3000ms через `setTimeout`. Использовать `useReducedMotion` (написать самому в `lib/utils/use-reduced-motion.ts`) для отключения цикла | executor | sonnet | `site/components/Hero.tsx`, `HeroChat.tsx`, `lib/utils/use-reduced-motion.ts` | 2.1, 2.3, 2.4, 2.5 |
| 2.8 | `components/HeroSwipe.tsx` из `hero-swipe.jsx`. Резервный вариант, готовый к включению через prop `<Hero variant="swipe" />`. SAMPLE_JOBS из 2.1 | executor | sonnet | `site/components/HeroSwipe.tsx` | 2.1, 2.3 |
| 2.9 | `components/HowItWorks.tsx` из `sections.jsx`. 4 шага слева, RealBotScreen справа. `useState` для active step | executor | sonnet | `site/components/HowItWorks.tsx` | 2.1, 2.5 |
| 2.10 | `components/Features.tsx` из `sections.jsx`. Тёмный фон, табы, RealBotScreen. `useState` для active feature | executor | sonnet | `site/components/Features.tsx` | 2.1, 2.5 |
| 2.11 | `components/SpeedSection.tsx` (~400 строк) из `speed.jsx`. IntersectionObserver для autoplay, RAF для анимации playhead. `useReducedMotion` отключает цикл (статичный финальный кадр). Подкомпоненты внутри файла: `RaceTrack`, `Lane`, `TimeAxis`, `Playhead`, `StatTile`, `FiltersTile` | executor | sonnet | `site/components/SpeedSection.tsx` | 2.2, 2.3 |
| 2.12 | `components/Pricing.tsx` + `components/PriceCard.tsx` из `more-sections.jsx`. Сетка 2 карточки. Текст синхронизировать с `PRODUCT_FACTS.md` §5 (Бесплатный, Активный 790 ₽ 3 недели). При расхождении с прототипом — приоритет `PRODUCT_FACTS.md` | executor | sonnet | `site/components/Pricing.tsx`, `PriceCard.tsx` | 2.1, 2.3 |
| 2.13 | `components/FAQ.tsx` из `more-sections.jsx`. Аккордеон, `useState` для open index, default `0`. ARIA-роли accordion | executor | sonnet | `site/components/FAQ.tsx` | 2.1, 2.3 |
| 2.14 | `components/FinalCTA.tsx` из `more-sections.jsx`. Большой gradient-блок, две кнопки: Telegram-бот и канал | executor | sonnet | `site/components/FinalCTA.tsx` | 2.3 |
| 2.15 | `components/Footer.tsx` из `more-sections.jsx`. Три колонки. Ссылки: `/privacy`, `/cookies`, `/offer`, `/bot-privacy` (последние две — placeholder в Phase 3). Email из `lib/data/nav.ts` — `info@otklicker.ru` (синк architecture §9.6) | executor | sonnet | `site/components/Footer.tsx` | 2.1, 2.4 |
| 2.16 | `components/CookieBanner.tsx`. `useState` + `useEffect` поверх `localStorage.otklicker.cookie-consent`. Текст: «Сайт использует cookies для аналитики и улучшения работы. Продолжая просмотр, вы соглашаетесь с [Политикой использования cookies](/cookies).» Кнопки: «Принять» (`'all'`), «Только необходимые» (`'essential'`). Ссылка ведёт на `/cookies` | executor | sonnet | `site/components/CookieBanner.tsx` | 2.3 |
| 2.17 | `components/MarkdownPage.tsx` — обёртка для legal-страниц через `react-markdown` + `rehype-raw` + Tailwind `prose-legal` (кастомный конфиг typography в tailwind.config). Ссылки absolute → `target="_blank" rel="noopener"` | executor | sonnet | `site/components/MarkdownPage.tsx` | 1.4 |
| 2.18 | Финальная сборка `app/page.tsx` — секционная композиция: `<Nav/>`, `<Hero/>`, `<SpeedSection/>`, `<HowItWorks/>`, `<Features/>`, `<Pricing/>`, `<FAQ/>`, `<FinalCTA/>`, `<Footer/>`. `<CookieBanner/>` монтируется в `app/layout.tsx`. Проверить визуально в `npm run dev` на 1240/960/720/375px | executor | sonnet | `site/app/page.tsx`, `app/layout.tsx` | 2.6-2.16 |

### Параллелизм

После 1.5 (типы готовы):
- Поток A (data): 2.1 → 2.2 параллельно
- Поток B (примитивы): 2.3 → 2.4 параллельно
- После 2.3+2.4: запускать 2.5, 2.6, 2.8, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 2.17 в параллель (10 веток)
- 2.7, 2.9, 2.10 ждут 2.5
- 2.18 ждёт всех

### Критерии приёмки Phase 2

- [ ] `npm run build` собирается без ошибок и warnings
- [ ] `npx tsc --noEmit` зелёный
- [ ] `npm run dev` → `http://localhost:3000/` показывает все 9 секций (Nav, Hero, Speed, HowItWorks, Features, Pricing, FAQ, FinalCTA, Footer)
- [ ] Cookie banner появляется при первом посещении, кнопка «Принять» сохраняет в `localStorage.otklicker.cookie-consent='all'`, reload — баннер скрыт
- [ ] CTA-кнопки в Hero и FinalCTA ведут на `https://t.me/otklicker_bot`
- [ ] HeroChat авто-циклит вакансии каждые 3с; при `prefers-reduced-motion: reduce` (DevTools → Rendering) — не циклит
- [ ] SpeedSection запускает анимацию при скролле; на reduced-motion — статичный финальный кадр
- [ ] FAQ раскрывается/сворачивается по клику, default open = item[0]
- [ ] Pricing: тексты совпадают с `docs/PRODUCT_FACTS.md` §5 (Бесплатный, Активный 790 ₽ за 3 недели)
- [ ] Footer ссылки `/privacy`, `/cookies`, `/offer`, `/bot-privacy` не 404 (хотя бы 200, контент будет в Phase 3)
- [ ] `git grep -n "Object.assign(window"` пусто (миграция на ES-модули)
- [ ] `git grep -nE "(--)\\s|—" site/components site/app | grep -vE "(comment|//|/\\*)"` пусто (em-dash запрещён в видимых текстах)

---

## Phase 3 — Юридические документы и legal-страницы (Sonnet + Opus, ~1 ч)

Стартует параллельно Phase 2 (зависимость только от 1.4 — globals.css для prose-стилей и `MarkdownPage.tsx` из 2.17).

Объём строго ограничен: пишем `SITE_PRIVACY_POLICY.md` и `COOKIE_POLICY.md`. Документы про бот (`/offer`, `/bot-privacy`) — placeholder.

Реквизиты оператора брать из `otklicker-promo/legal/PRIVACY_POLICY.md` (ИП Энбом Ксения Игоревна, ОГРНИП 324632700187012, ИНН 631609033320, адрес 443090 Самара, ул. Стара Загора 52-54). Контактный email: **`info@otklicker.ru`** (домен подключаем в Phase 5; в документе указать как заявленный канал связи).

### Задачи

| ID | Задача | Агент | Модель | Артефакт | Зависит от |
|----|--------|-------|--------|----------|------------|
| 3.1 | Написать `legal/COOKIE_POLICY.md` с нуля. Структура: §1 Цель, §2 Что такое cookies, §3 Какие cookies используем (essential — `otklicker.cookie-consent` 1 год, analytics — `_ym_uid`, `_ym_d`, `_ym_isad` Yandex.Metrica, грузятся только после согласия «Принять»), §4 Правовое основание (ст. 9 ФЗ-152), §5 Как отозвать согласие (очистка localStorage + повторный выбор в баннере), §6 Контакты оператора (ИП + `info@otklicker.ru`). Без em-dash | technical-writer | sonnet | `legal/COOKIE_POLICY.md` | — |
| 3.2 | Написать `legal/SITE_PRIVACY_POLICY.md` с нуля под бренд «откликер». **Только про посетителя сайта**, НЕ про пользователя бота. Минимальный набор: IP в логах nginx (хранение 30 дней), агрегированная Yandex.Metrica, cookies (отсылка на Cookie Policy). ФЗ-152 compliance. Подсмотреть структуру в `otklicker-promo/legal/PRIVACY_POLICY.md` (та же ИП, реквизиты реюзить дословно). Email для обращений: `info@otklicker.ru`. Без em-dash | legal-compliance-checker | opus | `legal/SITE_PRIVACY_POLICY.md` | — |
| 3.3 | `app/privacy/page.tsx` — `<MarkdownPage source={SITE_PRIVACY_POLICY}/>`. `app/cookies/page.tsx` — `<MarkdownPage source={COOKIE_POLICY}/>`. Markdown читается build-time через `lib/utils/markdown.ts` (`fs.readFileSync` относительно корня репо). Metadata title для каждой страницы | executor | sonnet | `site/app/privacy/page.tsx`, `site/app/cookies/page.tsx`, `site/lib/utils/markdown.ts` | 3.1, 3.2, 2.17 |
| 3.4 | `app/offer/page.tsx` и `app/bot-privacy/page.tsx` — placeholder. Текст: «Документ готовится. Если у вас есть вопросы — напишите в [@otklicker_bot](https://t.me/otklicker_bot).» Внизу — кнопка «На главную». Используют ту же типографику что и MarkdownPage (читаемая ширина 720px, Inter, заголовки h1/h2/h3, ссылки в брендовом цвете) | executor | sonnet | `site/app/offer/page.tsx`, `site/app/bot-privacy/page.tsx` | 2.17 |

### Критерии приёмки Phase 3

- [ ] `legal/SITE_PRIVACY_POLICY.md` >= 80 строк, упоминает ИП Энбом К.И. с реквизитами, ФЗ-152, IP nginx, Метрику; не упоминает бот, резюме, HH-токены
- [ ] `legal/COOKIE_POLICY.md` >= 50 строк, перечисляет 4 cookie с назначением и сроком
- [ ] `npm run build` → `out/privacy/index.html` и `out/cookies/index.html` существуют, содержат ключевые слова из MD
- [ ] `out/offer/index.html` и `out/bot-privacy/index.html` содержат «Документ готовится» и ссылку на `@otklicker_bot`
- [ ] `git grep -nE "—|--[^>]" legal/` пусто (em-dash запрещён) — `--` допустим только в HTML-комментах
- [ ] Все 4 страницы рендерятся в браузере, типографика наследует prose-стили, ссылки кликабельны

---

## Phase 4 — SEO и ассеты (Sonnet + Haiku + Opus, параллельно, ~45 мин)

Стартует параллельно Phase 2 (зависит от 1.4). Ассеты экспортируются из `brandbook.pen` через `mcp__pencil__*`.

### Задачи

| ID | Задача | Агент | Модель | Артефакт | Зависит от |
|----|--------|-------|--------|----------|------------|
| 4.1 | `site/lib/seo/metadata.ts` — `defaultMetadata` из `architecture.md` §8.6. `site/lib/seo/jsonld.ts` — JSON-LD `SoftwareApplication` с name «Откликер», applicationCategory `BusinessApplication`, offers (Бесплатный 0₽, Активный 790₽). Подключить `defaultMetadata` в `app/layout.tsx`, JSON-LD скриптом в `app/page.tsx`. Per-page metadata для `/privacy`, `/cookies`, `/offer`, `/bot-privacy` | seo-specialist | sonnet | `site/lib/seo/{metadata,jsonld}.ts`, обновлённый `app/layout.tsx` | 1.4 |
| 4.2 | `app/robots.ts` (Allow `*`, Sitemap `https://otklicker.ru/sitemap.xml`). `app/sitemap.ts` — три URL: `/`, `/privacy`, `/cookies` (placeholder'ы НЕ включаем — решение пользователя). lastModified = build time, priority 1.0/0.5/0.5. `app/manifest.ts` — name «откликер», theme `#FBBF24`, иконки 192/512 | seo-specialist | sonnet | `site/app/{robots,sitemap,manifest}.ts` | 1.4 |
| 4.3 | Экспорт ассетов из `brandbook.pen` через `mcp__pencil__open_document` + `mcp__pencil__export_nodes`. Node IDs из `brand-tokens.md`: `cIcTM` (BrandMark с тенью) → PNG 512×512 как favicon source; `xez6k` (BrandMark icon-only) → PNG 1024×1024; `7Bui1` (BrandLockup горизонтальный) → SVG; `U2B8J` (Bot Avatar основной) → PNG 512×512. Конвертация PNG → ICO (32px) + favicon-192.png + apple-touch-icon-180.png через ImageMagick или `sharp`. Положить в `site/public/` и `site/public/brand/` | executor | sonnet | `site/public/{favicon.ico,icon-192.png,icon-512.png,apple-touch-icon.png}`, `site/public/brand/*` | 1.3 |
| 4.4 | OG-image 1200×630. Стратегия: экспорт ноды `BRhwP` (TG cover 1280×640) через `mcp__pencil__export_nodes` PNG, обрезка до 1200×630 через `sharp`. Заголовок «откликает на свежие вакансии за вас» — если в ноде уже зашит, берём; если нет, накладываем через `sharp` composite. Положить в `site/public/og-image.png` | executor | sonnet | `site/public/og-image.png` | 1.3 |
| 4.5 | `promo/artem/persona.md` (HR-персона из `otklicker-promo/CLAUDE.md` секция «Персона Артёма»), `promo/artem/voice.md` (правила голоса бренда из `docs/PRODUCT_FACTS.md` §9), `promo/seo/keywords.md` (черновой список: «автоотклики hh», «telegram бот для поиска работы», «сопроводительное письмо ИИ», «hh без пароля», «бот для откликов hh» — 20-30 фраз с приоритетом по частотности и конкуренции). Это контент-артефакты, не код | writer | haiku | `promo/artem/{persona,voice}.md`, `promo/seo/keywords.md` | 1.3 |
| 4.6 | `promo/seo/baseline-audit.md` — тех. SEO-чеклист (canonical, robots, sitemap, OG, JSON-LD, semantic HTML headings, alt-тексты у RealBotScreen mockups, lang, hreflang ru, viewport) с отметкой «pass/fail» по факту реализации в 4.1-4.4 | seo-specialist | sonnet | `promo/seo/baseline-audit.md` | 4.1, 4.2, 4.3, 4.4 |

### Параллелизм

После 1.4: 4.1, 4.2, 4.3, 4.4, 4.5 запускаются одновременно. 4.6 ждёт 4.1-4.4.

### Критерии приёмки Phase 4

- [ ] `view-source:http://localhost:3000/` содержит `<script type="application/ld+json">` с SoftwareApplication
- [ ] `<title>` главной = «Откликер — Telegram-бот для поиска работы на HH.ru»
- [ ] `<meta property="og:image">` ведёт на `/og-image.png`, файл существует и валидный 1200×630
- [ ] `curl http://localhost:3000/sitemap.xml` (после `npm run build && npx serve out`) отдаёт XML с **3** URL (главная + privacy + cookies, без placeholder'ов)
- [ ] `curl http://localhost:3000/robots.txt` — Allow `*`, ссылка на sitemap
- [ ] `site/public/favicon.ico`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` существуют, не битые
- [ ] `promo/seo/baseline-audit.md` — все пункты `pass`

---

## Phase 5 — Деплой и инфраструктура (Sonnet + Opus, ~1 ч)

Стартует параллельно Phase 2 (зависит только от 1.1). Конечный шаг с DNS требует подтверждения пользователя.

### Задачи

| ID | Задача | Агент | Модель | Артефакт | Зависит от |
|----|--------|-------|--------|----------|------------|
| 5.1 | Сгенерировать SSH-ключ для CI: `ssh-keygen -t ed25519 -f ~/.ssh/otklicker_gh_actions -N "" -C "otklicker-gh-actions@$(date +%Y%m%d)"`. Public key добавить в `authorized_keys` сервера через `ssh-copy-id` или ручной echo. Private key добавить в GH Secrets как `DEPLOY_SSH_KEY` через `gh secret set`. Также: `DEPLOY_HOST=204.168.178.241`, `DEPLOY_USER=root`, `DEPLOY_PATH=/var/www/otklicker.ru/`. **Перед добавлением public key на сервер — `AskUserQuestion` подтверждение**, потому что это modification на production-сервере | devops-automator | sonnet | `~/.ssh/otklicker_gh_actions{,.pub}`, GH Secrets | 1.1 |
| 5.2 | Написать `deploy/nginx/otklicker.ru.conf` по спеке из `HANDOFF_PROMPT.md`: HTTP→HTTPS 301, www→apex 301, TLS 1.2+1.3, OCSP stapling, HSTS, минимальная CSP, gzip+brotli (если установлен), long-cache для `/_next/static/*` и `/static/*` (immutable 1 год), short-cache для HTML (max-age=300, must-revalidate), `/.well-known/acme-challenge/`, корень `/var/www/otklicker.ru/`, `try_files $uri $uri/ $uri.html =404` (важно для static export Next с trailingSlash) | devops-automator | sonnet | `deploy/nginx/otklicker.ru.conf` | 1.1 |
| 5.3 | `.github/workflows/deploy.yml` — на push в `main`: job `build` (Node 20, `npm ci` в `site/`, `npm run build` → `site/out/`), job `deploy` (rsync `site/out/` → `${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}` с `--delete`, использует `DEPLOY_SSH_KEY`). `.github/workflows/ci.yml` — на PR: lint + typecheck + build (без deploy). Concurrency group для отмены overlapping runs | devops-automator | sonnet | `.github/workflows/{deploy,ci}.yml` | 5.1 |
| 5.4 | SSH на сервер. Установить certbot: `apt-get update && apt-get install -y certbot python3-certbot-nginx`. Создать `/var/www/otklicker.ru/` с временной заглушкой `index.html` («сайт скоро откроется»). Положить nginx-конфиг в `/etc/nginx/sites-available/otklicker.ru`, симлинк в `sites-enabled/`. `nginx -t && systemctl reload nginx`. **Перед systemctl reload — `AskUserQuestion`**, потому что 80 порт уже отдаёт другие проекты | executor | sonnet | сервер настроен | 5.2 |
| 5.5 | **БЛОКЕР пользователя.** `AskUserQuestion`: «Готов поменять A/AAAA в Timeweb DNS на `204.168.178.241` (A) и текущий IPv6 сервера? MX и SPF не трогаем». После подтверждения — пользователь меняет в панели Timeweb (TTL 600s). Оркестратор ждёт. Проверка: `dig +short otklicker.ru @8.8.8.8` возвращает `204.168.178.241` | оркестратор | — | DNS пропагирован | 5.4 |
| 5.6 | На сервере: `certbot --nginx -d otklicker.ru -d www.otklicker.ru -m boviazgenaouakn@hotmail.com --agree-tos --non-interactive`. Проверить: `systemctl enable certbot.timer`, `certbot renew --dry-run` без ошибок | executor | sonnet | SSL активен | 5.5 |
| 5.7 | Аудит nginx-конфига: TLS-настройки (отключить TLS 1.0/1.1, оставить 1.2+1.3, безопасные cipher suites), HSTS preload-ready (`max-age=63072000; includeSubDomains; preload`), CSP (`default-src 'self'; script-src 'self' 'unsafe-inline' mc.yandex.ru; img-src 'self' data: mc.yandex.ru; style-src 'self' 'unsafe-inline'; connect-src 'self' mc.yandex.ru;`), X-Frame-Options DENY, Referrer-Policy strict-origin-when-cross-origin, Permissions-Policy (отключить camera, geolocation, microphone), отсутствие `server_tokens`. Аудит SSH (отключить пароли, только ключи). Проверка через `curl -I https://otklicker.ru` и `testssl.sh otklicker.ru`. Артефакт: `deploy/security-checklist.md` | security-engineer | opus | `deploy/security-checklist.md` | 5.6 |
| 5.8 | Yandex 360 для `info@otklicker.ru`: оркестратор проверяет в Yandex Connect готовность принимать почту (DNS-инструкции от Яндекса). **БЛОКЕР пользователя.** `AskUserQuestion`: «Готов поменять MX в Timeweb DNS на yandex (3 записи `mx.yandex.net` приоритеты 10/20/30) + добавить SPF/DKIM/DMARC?» **Только после подтверждения готовности Yandex Connect.** Не выполнять автоматом — это сломает рабочую почту, если Яндекс не настроен | оркестратор | — | MX переключены | 5.7 |

### Параллелизм

5.1, 5.2, 5.3 параллельно после 1.1. 5.4 ждёт 5.2. 5.5 ждёт 5.4 (блокер пользователя). 5.6 ждёт 5.5. 5.7 ждёт 5.6. 5.8 — отдельный risky шаг, можно отложить и не блокировать запуск сайта.

### Критерии приёмки Phase 5

- [ ] `gh secret list` показывает `DEPLOY_SSH_KEY`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PATH`
- [ ] Push временного коммита в `main` → GH Actions завершает оба job (build + deploy) зелёными
- [ ] `curl -I https://otklicker.ru` возвращает 200 + HSTS + CSP заголовки
- [ ] `curl -I http://otklicker.ru` возвращает 301 → https
- [ ] `curl -I https://www.otklicker.ru` возвращает 301 → apex
- [ ] `certbot renew --dry-run` без ошибок, `systemctl is-active certbot.timer` = `active`
- [ ] `testssl.sh otklicker.ru` — оценка A или A+, нет TLS 1.0/1.1
- [ ] `deploy/security-checklist.md` — все пункты `pass`
- [ ] (5.8 опционально) `dig +short MX otklicker.ru @8.8.8.8` показывает `mx.yandex.net.` записи
- [ ] (5.8 опционально) пробное письмо на `info@otklicker.ru` доставлено в Yandex 360 inbox

### Risky действия — требуют подтверждения

| Шаг | Что делает | Почему risky |
|---|---|---|
| 5.1 | Добавляет CI public key в `~/.ssh/authorized_keys` сервера | Меняет prod-сервер; если ключ скомпрометирован — root access |
| 5.4 | `systemctl reload nginx` | На сервере крутятся другие проекты (fitcoach, exercise-review, tg-automations) — broken config повалит всех |
| 5.5 | Смена A/AAAA Timeweb DNS | Если конфиг nginx неправильный, на час+ сайт не доступен |
| 5.6 | Запуск certbot | Перезаписывает nginx-конфиг (Let's Encrypt сам инжектит SSL-блок); надо проверить final config после |
| 5.8 | Смена MX на Yandex | Сломает рабочую почту, если Yandex Connect не готов принимать |

---

## Phase 6 — Ревью (Opus + Sonnet, последовательно, ~1 ч)

Все ревью прогоняются после того как Phase 2-5 закрыты. Если severity ≥ MEDIUM — итерация (executor чинит, ревьюер перепроверяет).

### Задачи

| ID | Задача | Агент | Модель | Артефакт | Зависит от |
|----|--------|-------|--------|----------|------------|
| 6.1 | Полный обзор кода: TS strict нарушения, dead code, читаемость, корректность миграции из прототипа, cn() вместо string concat, `useEffect` cleanup, отсутствие `any`. Severity: CRITICAL/HIGH/MEDIUM/LOW. Артефакт: `.planning/REVIEW.md` | code-reviewer | opus | `.planning/REVIEW.md` | Phase 2, 3, 4 |
| 6.2 | `npm run dev` локально, открыть в playwright. Сравнить визуально с прототипом (`design_handoff_otklicker_landing/index.html`) на 1240/960/720/375. Сделать скриншоты и diff. Cookie banner, hover state, focus-states, авто-цикл HeroChat | designer | sonnet | `.planning/visual-review.md` + screenshots | Phase 2, 3 |
| 6.3 | WCAG-проверка: контраст (text/text-heading на bg-pastel должен пройти AA для 16px+), навигация с клавиатуры (Tab по Nav, Hero CTA, Footer links), ARIA-метки на FAQ accordion, alt-тексты на mockups, focus-states видимы, cookie banner trapping (нет — но a11y-friendly). Lighthouse a11y >= 95 | accessibility-auditor | sonnet | `.planning/a11y-review.md` | Phase 2, 3 |
| 6.4 | Если в 6.1/6.2/6.3 есть severity ≥ MEDIUM — `executor` (sonnet) чинит, ревьюер перепроверяет (повтор соответствующего шага) | executor + ревьюер | sonnet | обновлённые артефакты | 6.1-6.3 |

### Критерии приёмки Phase 6

- [ ] `.planning/REVIEW.md` — нет CRITICAL/HIGH открытых пунктов
- [ ] `.planning/visual-review.md` — нет MEDIUM+ расхождений с прототипом
- [ ] `.planning/a11y-review.md` — Lighthouse a11y >= 95
- [ ] `npx tsc --noEmit` зелёный, `npm run lint` зелёный

---

## Phase 7 — Запуск и верификация (Sonnet, ~30 мин)

Финальная фаза. Все предыдущие закрыты, ревью passed.

### Задачи

| ID | Задача | Агент | Модель | Артефакт | Зависит от |
|----|--------|-------|--------|----------|------------|
| 7.1 | Push финальных коммитов в `main`. GH Actions деплоит. Проверить `gh run list --workflow=deploy.yml --limit 1` — статус success. На сервере: `ls /var/www/otklicker.ru/index.html`, `nginx -t`, `systemctl reload nginx` если нужно | executor | sonnet | сайт обновлён | Phase 5, 6 |
| 7.2 | Если DNS уже не пропагирован (Phase 5.5) — повторить `AskUserQuestion` по DNS. Дождаться: `dig +short otklicker.ru @8.8.8.8` и `dig +short otklicker.ru @1.1.1.1` оба возвращают `204.168.178.241`. Обычно 5-15 минут при TTL 600s | оркестратор | — | DNS resolves | 7.1 |
| 7.3 | Финальная верификация через playwright (`mcp__playwright__browser_*`): `https://otklicker.ru` открывается, SSL-замочек, все секции рендерятся, CTA ведут на `t.me/otklicker_bot` и `t.me/otklicker`, cookie banner появляется и сохраняет выбор, ссылка на `/cookies` ведёт на реальный текст, `/privacy` открывается, `/offer` и `/bot-privacy` показывают placeholder, `/robots.txt` валидный, `/sitemap.xml` валидный (3 URL), Lighthouse mobile + desktop ≥ 90 по всем 4 метрикам, OG-картинка отдаётся при шаринге в TG (отправить тестовую ссылку в @otklicker_bot или личку и проверить превью) | verifier | sonnet | `.planning/launch-verification.md` | 7.2 |
| 7.4 | Финальный отчёт пользователю: ссылка на репо, ссылка на сайт, прохождение всех 16 критериев приёмки (см. ниже), что осталось доделать (BOT_OFFER_AGREEMENT.md, BOT_PRIVACY_POLICY.md, Yandex.Metrica после получения ID, статьи блога) | оркестратор | — | финальное сообщение | 7.3 |

### Критерии приёмки Phase 7

- [ ] `.planning/launch-verification.md` — все пункты `pass`
- [ ] Lighthouse Performance/Accessibility/Best Practices/SEO ≥ 90 (mobile + desktop)
- [ ] Уведомление пользователю отправлено

---

## Чеклист критериев приёмки (16 пунктов из HANDOFF_PROMPT.md)

Финальное «готово» = всё ниже галочки:

1. [ ] `https://otklicker.ru` открывается с валидным SSL
2. [ ] www→apex редирект (301)
3. [ ] http→https редирект (301)
4. [ ] Все секции лендинга визуально совпадают с прототипом (designer-ревью passed, Phase 6.2)
5. [ ] CTA ведут на `https://t.me/otklicker_bot` и `https://t.me/otklicker`
6. [ ] Cookie banner функционирует, сохраняет выбор, ссылка на `/cookies` работает
7. [ ] `/privacy` и `/cookies` открываются с реальным контентом про «откликер» и реквизитами ИП Энбом К.И.
8. [ ] `/offer` и `/bot-privacy` открываются как placeholder с текстом «Документ готовится»
9. [ ] `robots.txt`, `sitemap.xml` валидны и доступны (sitemap включает только `/`, `/privacy`, `/cookies`)
10. [ ] OG-картинка корректно показывается при шаринге в Telegram
11. [ ] Lighthouse score ≥ 90 (Performance, Accessibility, Best Practices, SEO)
12. [ ] GH Actions деплой работает: `git push` → через 2-3 минуты сайт обновлён
13. [ ] TLS-сертификат автообновляется (`certbot renew --dry-run` без ошибок)
14. [ ] Все артефакты ревью (code, visual, a11y, security) собраны в `.planning/`
15. [ ] В новом репо `otklicker` есть `README.md` с инструкцией «как локально запустить», «как задеплоить», «структура»
16. [ ] В новом репо `otklicker` есть `CLAUDE.md` с памяткой для будущих сессий

---

## Глобальные риски и митигации

| Риск | Вероятность | Митигация |
|---|---|---|
| Bundle слишком толстый из-за inline JSX и lucide | средняя | `output: 'export'` минимизирует, Lighthouse в Phase 7 покажет; lucide tree-shakes по импорту |
| Брендбук не открылся / нет нужных нод | низкая | Phase 0.1b закрыла — node IDs зафиксированы в `brand-tokens.md`; fallback — кастомные SVG из прототипа |
| MX-переключение в Phase 5.8 сломает рабочую почту | средняя | Двойное подтверждение через `AskUserQuestion`; шаг опциональный для запуска сайта |
| Сервер: 4.1 ГБ свободной RAM из 7.5 | низкая | static export — Node на сервере не нужен, сборка идёт в GH Actions |
| ARM aarch64 совместимость нативных модулей | низкая | Node 20 LTS Hetzner CAX21 — официальная сборка; sharp работает на arm64 |
| Кто-то нажмёт «Тиндер» в Hero и удивится демо | низкая | в Hero и FinalCTA CTA ведут на `t.me/otklicker_bot` — реальный продукт; HeroSwipe не дефолтный variant |
| `legal/PRIVACY_POLICY.md` (старый) расходится с `PRODUCT_FACTS.md` | низкая (мы не публикуем старый) | новые документы пишутся с нуля под бренд «откликер»; реквизиты реюзим только в части ИП |
| Em-dash проскочит в текст | средняя | Phase 2 и Phase 6 имеют grep-чек в чек-листе |
| Certbot перезатрёт нашу nginx-конфигурацию | средняя | проверка config diff до и после; ручная правка после если нужно — security-engineer закрывает в 5.7 |
| Long-cache на `_next/static/*` после rebuild | низкая | hash в filename — иммутабельно; проверка `etag` |
| Yandex.Metrica подгружает скрипт до согласия | средняя | Метрика подключается в Phase будущей задачи; в текущем сборе Метрики нет, проблема не возникает |
| GH Actions не имеет access на серверный путь | низкая | Phase 5.1 проверяет SSH вручную перед добавлением workflow |

---

## Pull-request стратегия

- **Trunk-based в `main`.** Соло-разработка, GH Actions деплоит из `main`. Не делаем feature-branch + PR для каждой фазы.
- Атомарные коммиты внутри фазы, conventional-commits: `feat:`, `fix:`, `chore:`, `docs:`, `ci:`, `style:`.
- Один коммит = одна логическая единица (например, `feat(hero): add HeroChat component with auto-cycle`).
- Не пушить в `main` пока не закрыта фаза целиком — кроме case'ов где промежуточный пуш явно нужен (например, тестовый push в Phase 5.3 для проверки GH Actions).
- Перед каждым `git push` — `gitleaks` или ручной `git diff` на наличие токенов/ключей.

---

## Сводка решений (зафиксировано пользователем, не оспаривать)

| Вопрос | Решение |
|---|---|
| Имя GH-репо | `otklicker` (private) |
| Контактный email для legal | `info@otklicker.ru` (Yandex 360, подключение в Phase 5.8) |
| Какие legal-документы пишем сейчас | `SITE_PRIVACY_POLICY.md` + `COOKIE_POLICY.md` |
| `/offer` и `/bot-privacy` | placeholder-страницы |
| Cookie banner ссылается | на `/cookies` |
| Sitemap включает | `/`, `/privacy`, `/cookies` (без placeholder'ов) |
| Hero variant default | `chat` (swipe в коде, готов к включению) |
| Стек | Next.js 14 App Router + TS strict + Tailwind, static export |
| CI/CD | GH Actions, push в main → rsync на сервер |
| SSL | Let's Encrypt + certbot.timer |

---

## Указания исполнителю

- **Никаких пресуппозиций без подтверждения.** Risky действия (5.1, 5.4, 5.5, 5.8) требуют `AskUserQuestion` в момент действия.
- **Брендбук читать только через `mcp__pencil__*`**, не Read/Grep.
- **При расхождении прототипа и `PRODUCT_FACTS.md`** — приоритет `PRODUCT_FACTS.md`.
- **При расхождении прототипа и `CLAUDE.md` правил** (em-dash, lowercase «откликер») — приоритет `CLAUDE.md`.
- **Ссылаться на готовые сниппеты:** Tailwind config — `architecture.md` §3, globals.css — §4, типы — §1, дефолтная Metadata — §8.6, чек-лист Phase 1 — §10 (15 пунктов).
- **Не копировать старые `legal/PRIVACY_POLICY.md` и `OFFER_AGREEMENT.md`** в новый репо — они про «Свою базу», не про откликер.
- **`marketing-engine/`** копируется в новый репо как-есть, без модификаций (это автономный Python-проект).
- **Между фазами — короткий отчёт оркестратора** (1-2 строки + ссылка на артефакт). Не пересказ, а статус.

---

**Документ готов к запуску Phase 1.** Если пользователь подтверждает — оркестратор начинает с задачи 1.1.
