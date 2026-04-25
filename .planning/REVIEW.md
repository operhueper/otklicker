# Code review otklicker.ru — Phase 6 — 2026-04-25

Reviewer: code-reviewer (Opus)
Скоуп: `/Users/evgeniy/projects/otklicker/site/`

## Severity

- CRITICAL: exploit / broken build / missing data
- HIGH: bugs, broken UX, a11y blocker
- MEDIUM: anti-patterns, maintainability
- LOW: style, refactor
- POSITIVE: что сделано хорошо

## Findings

### CRITICAL

(None.)

### HIGH

**H-1: Manifest icons referenced with wrong paths** — `site/public/manifest.json:6-7`
`manifest.json` объявляет иконки `/icon.png` и `/apple-icon.png`, но static export отдаёт их по `/icon` и `/apple-icon` (без расширения). Браузер запросит `/icon.png` из манифеста и получит 404 — нет PWA-иконки, нет Android home-screen.
Fix: исправить пути в manifest на `/icon` и `/apple-icon`, либо удалить manifest.json и оставить Next-managed metadata.

**H-2: Nested setTimeout cleanup is dead code in `HeroChat`** — `components/hero-chat.tsx:29-51`
Внутри `useEffect` зарегистрирован setTimeout (`t`), из его callback ещё один setTimeout (`t2`) с `return () => clearTimeout(t2)` — это return value колбэка, не cleanup React. То же с `t3` на 45-46. Только outermost `return () => clearTimeout(t)` на 50 реально срабатывает на unmount. При unmount во время 450ms или 900ms окна вложенные таймеры всё ещё стрельнут setSent/setSkipped/setIdx/setResponse на размонтированном компоненте.
То же с `act()` на 63-75 (там return-ы вообще выкинуты — это не хук).
Fix: накопить timer IDs в `useRef<number[]>([])`, push при каждом setTimeout, clear all в cleanup эффекта.

**H-3: `handleSwipe` setTimeout in `HeroSwipe` is also uncleaned** — `components/hero-swipe.tsx:68-82`
`handleSwipe()` обычная функция, не useEffect. `return () => clearTimeout(t)` на 81 — discarded return value. При swipe + unmount в течение 380ms — setStack/setSwipeDir/setCounter на unmounted node.
Fix: трекать активный таймер в `useRef<number | null>(null)`, очищать в unmount-эффекте.

**H-4: ESLint suppressions misplaced — warnings still fire** — `components/hero-swipe.tsx:60` и `components/speed.tsx:41`
`eslint-disable-next-line react-hooks/exhaustive-deps` стоит ПЕРЕД вызовом `useEffect(`. Next-ESLint репортит предупреждение на строке закрытия dependency array (66 в hero-swipe, 61 в speed.tsx). Verified `npx next lint` всё ещё показывает warnings.
Fix: переместить comment на строку перед `}, [...])`, либо обернуть disable/enable блоком, либо рефакторить чтобы deps были корректными.

### MEDIUM

**M-1: `dangerouslySetInnerHTML` with template-string interpolation in `HeroChat`** — `components/hero-chat.tsx:37-38, 60-61, 214`
`response.text` строится template literals с `job.company`. Сейчас `job.company` из статичного `HERO_CHAT_JOBS` — безопасно. Но паттерн фрагилен: любой будущий путь, где `job.company` приходит от user/HH input — XSS.
Fix: рендерить JSX напрямую `<><b>{job.company}</b></>` вместо `dangerouslySetInnerHTML`. То же с `BOT_SCREENS` в `lib/screens/bot-screens.ts` — модельировать как `ReactNode[]`, исключить `dangerouslySetInnerHTML` в `RealBotScreen` (строка 117) полностью.

**M-2: Bogus literal in `PricingPlan.id` type** — `lib/types/pricing.ts:6`
`id: 'free' | 'active' | string` коллапсирует в `string` — литералы дают ноль IDE assistance. Либо `id: string`, либо `id: 'free' | 'active'`.

**M-3: `Lane.kind` typed as `string` instead of literal union** — `components/speed.tsx:165`
Принимает `kind: string`, передаются только `'bot'` и `'manual'`. Заменить на `kind: 'bot' | 'manual'`.

**M-4: Unused dependencies bloating install / lockfile** — `package.json`
- `rehype-raw` — нигде не импортируется (хорошая новость: legal-страницы XSS-safe by default, raw HTML экранируется react-markdown)
- `tailwind-merge` — нигде не импортируется
- `clsx` — нигде не импортируется
Fix: `npm uninstall rehype-raw tailwind-merge clsx`.

**M-5: `setInterval` recreated every cycle in `HeroSwipe`** — `components/hero-swipe.tsx:61-66`
Эффект зависит от `stack`, поэтому interval уничтожается и пересоздаётся каждый раз когда `stack` меняется (каждые `cycleMs`). Effectively setTimeout-цепочка. Функционально корректно, семантически вводит в заблуждение.
Fix: использовать `setTimeout` или ref-stable handler.

**M-6: Composite key with full-stack identity defeats reconciliation** — `components/hero-swipe.tsx:107`
`key={`${job.title}-${i}-${stack[0].title}`}` включает `stack[0].title` — каждый цикл top-card title меняется, все 3 карточки ремонтируются.
Fix: `key={job.title}` (titles уникальны в SAMPLE_JOBS).

**M-7: BeatMarker uses index keys for static array** — `components/speed.tsx:225`
`key={i}` по `BOT_BEATS`/`MANUAL_BEATS`. Массивы immutable — поведение OK, но `key={beat.t}` лучше выражает intent.

**M-8: `_playheadPct` parameter passed to `TimeAxis` but never read** — `components/speed.tsx:158, 292-293`
Передаётся `playheadPct`, в `TimeAxis` деструктурируется как `_playheadPct` с eslint-disable. Dead code.
Fix: убрать `playheadPct` из `TimeAxisProps` и call site.

**M-9: Inline styles everywhere instead of using configured Tailwind tokens** — multiple files
Tailwind config объявляет `text-h1`, `text-h2`, цветовые токены, `max-w-container` — но большинство компонентов хардкодят через inline `style={{ ... }}`. Дизайн-токены дублируются (Tailwind config + CSS-переменные в globals.css). Унаследовано из прототипа. Не блокирует Phase 7. Долгосрочно — мигрировать.

**M-10: `BrandLockup` tagline "найди работу мечты" is invented** — `components/brand.tsx:52`
Per CLAUDE.md: «Слоган: нет фиксированного — не использовать придуманные». Этот tagline подразумевает гарантированный outcome ("работа мечты"), конфликтует с правилом «обещания функций которых нет в боте».
Fix: убрать tagline или заменить на нейтральное «Telegram-бот · HH.ru».

### LOW

**L-1: `dangerouslySetInnerHTML` для JSON-LD — стандартный idiom** — `app/page.tsx:74-76`
Безопасно (constant). Просто следить если jsonLd когда-нибудь станет user-derived.

**L-2: Buttons missing explicit `type="button"`** — multiple files
В `cookie-banner.tsx`, `hero-chat.tsx`, `hero-swipe.tsx`, `features.tsx`, `faq.tsx`, `how-it-works.tsx`, `speed.tsx` нет `type="button"`. Default `submit` внутри form, ни одна не в form — поведение OK, но best practice.

**L-3: Dead font assets** — `app/fonts/`
`GeistMonoVF.woff` и `GeistVF.woff` в репо. layout использует `next/font/google` Inter; Geist не импортируется.
Fix: удалить папку.

**L-4: Dead CSS class `.prose-legal`** — `app/globals.css:178-188`
Legal-страницы используют `prose prose-stone`, никогда `.prose-legal`.
Fix: либо подключить `<article className="prose prose-legal">`, либо удалить правило.

**L-5: Mixed quote-style — single in TS, double in JSX**
TS canonical, OK.

**L-6: `id="teaser-grid"` selector in `<style>` tag** — `components/teaser-strip.tsx:10, 24`
Inline `<style>` с глобальным `id` загрязняет namespace.
Fix: class selector + scoped CSS module, либо Tailwind responsive utilities.

**L-7: `<a href="#">` semantic — fixed in TS, just note**
JSX-прототип имел три placeholder `href="#"` (О нас, Политика данных, Оферта). TS корректно заменил на `/privacy`, `/cookies`, `/offer`, `/bot-privacy`. Migration улучшила source.

**L-8: `react-strict-mode` + auto-cycle effects double-invoke in dev**
`reactStrictMode: true` в `next.config.mjs` триггерит double-mount в dev. Вместе с H-2/H-3 (timer cleanup) — warnings или jumpy initial state в dev mode но не в prod build. Фикс H-2/H-3 решает оба.

**L-9: Decimal pixel sizes in `RealBotScreen` and `HeroChat`** — `lib/screens/bot-screens.ts`, `components/hero-chat.tsx`
`fontSize: 13.5`, `12.5`, `11.5`. Браузеры рендерят OK, half-pixel необычно. Унаследовано из прототипа.

### POSITIVE

- **Migration fidelity high.** Spot-check HowItWorks, Features, Pricing, FAQ, FinalCTA, Footer, Hero, HeroChat, RealBotScreen vs `design_handoff_otklicker_landing/source/components/*.jsx` — content 1:1, structure preserved.
- **Spec compliance с `docs/PRODUCT_FACTS.md` exact.** Pricing 0/постоянно и 790/3 недели + бейдж «37 ₽ в день» правильно (`lib/data/pricing.ts:9, 26-29`). FAQ statements (14-day refund, +48h guarantee, OAuth, Playwright, mobile proxy, 9-21 window, 15-per-day limit) — всё совпадает.
- **Brand voice clean.** Searched for forbidden words (уникальный, инновационный, не упустите, leverage, robust, seamless, showcase, revolutionize, "работа за 3 дня", "100 откликов", `hi@otklicker.app`) и `--` как пунктуация. Ноль hits. Footer корректно `info@otklicker.ru`.
- **No `any`, no `console.*`, no TODO/FIXME/HACK, no hardcoded secrets.** TypeScript strict mode; `tsc --noEmit` clean.
- **rehype-raw NOT wired up** — legal-страницы рендерят markdown через react-markdown + remark-gfm только. Raw HTML в .md экранируется по умолчанию. Legal-страницы XSS-safe.
- **A11y baseline solid.** `aria-hidden="true"` на декоративных SVG/halo. `role="navigation"`/`aria-label` на Nav. `role="tablist"`/`role="tab"`/`role="tabpanel"`/`aria-selected`/`aria-controls`/`aria-labelledby` в Features. `aria-pressed` в HowItWorks. `aria-expanded`/`aria-controls` в FAQ. Buttons HeroSwipe с `aria-label`. Focus ring через `:focus-visible` в `globals.css:75-79`.
- **JSON-LD `SoftwareApplication`** на homepage с двумя Offer'ами совпадающими с реальной ценой.
- **`output: 'export'` works** — `out/` содержит полный static HTML, CSS, JS, dynamically-generated PNG (icon, apple-icon, opengraph-image), корректные robots.txt и sitemap.xml.
- **Lucide icons tree-shaken cleanly** — ~7 иконок (Send, ArrowRight, Check, Plus, Minus, MousePointerClick), grep по "lucide" в vendor chunks пуст. First-load JS ~107 KB разумно.
- **`metadata` exports proper.** На каждой странице title/description/canonical/robots. `/offer` и `/bot-privacy` корректно `robots: { index: false, follow: false }` + Disallow в `robots.ts`.
- **TS strict ловит баги в compile time.** Типы в `lib/types/*.ts` segmented (один концепт на файл с barrel index.ts).
- **Next 14 App Router conventions correct.** Server components by default; `'use client'` precisely где нужны state/effects (Nav, HeroChat, HeroSwipe, HowItWorks, Features, Pricing, FAQ, CookieBanner, SpeedSection). FinalCTA, Footer, Hero, TeaserStrip, RealBotScreen, BrandLockup — server components, good split.
- **CookieBanner gracefully degrades** при заблокированном localStorage (try/catch вокруг getItem/setItem).
- **Speed timeline logic** в `lib/speed/timeline.ts` — `pct()` и `progressToMinute()` хорошо bounded с edge-case clamping. Зональная математика sums to 1.0.
- **Footer email fix preserved** — JSX-прототип имел `href="mailto:hi@otklicker.app"` с label `info@otklicker.ru` (mismatch). TS-версия корректно рендерит оба как `info@otklicker.ru`.

## Score

- Migration fidelity: **9/10**
- TS strictness: **8/10**
- React/Next conventions: **6/10** (timer cleanup bugs, ineffective ESLint suppressions)
- Performance: **9/10**
- Brand voice: **10/10**
- **Total: 8.4/10 — yellow**

## Action items до публичного запуска (Phase 7)

- [ ] **H-1**: Fix `manifest.json` icon paths (`/icon.png` → `/icon`) или удалить manifest.json
- [ ] **H-2**: Track + cleanup nested setTimeouts в HeroChat
- [ ] **H-3**: Same для HeroSwipe.handleSwipe — useRef timer
- [ ] **H-4**: Поправить две `react-hooks/exhaustive-deps` ESLint warnings
- [ ] **M-1**: Заменить dangerouslySetInnerHTML в HeroChat toast на JSX
- [ ] **M-4**: `npm uninstall rehype-raw tailwind-merge clsx`
- [ ] **L-3**: Удалить `app/fonts/Geist*.woff`
- [ ] Verify after fix: `npm run build && npx next lint` zero warnings

## Action items долгосрочно

- [ ] **M-2/M-3**: Tighten literal unions
- [ ] **M-6**: Stable id для HeroSwipe key
- [ ] **M-9**: Migrate inline `style={{...}}` на Tailwind classes
- [ ] **M-10**: Reconsider "найди работу мечты" tagline в BrandLockup
- [ ] **L-2**: Add `type="button"` to all interactive buttons
- [ ] **L-4**: Wire `.prose-legal` или удалить
- [ ] **L-6**: Replace `id="teaser-grid"` global ID на class-scoped responsive utilities
- [ ] Convert BOT_SCREENS content из HTML strings в ReactNode trees
- [ ] Add basic Playwright smoke test (homepage loads, all sections render, all CTAs link to t.me/otklicker_bot или t.me/otklicker, manifest icon resolves 200 OK)
