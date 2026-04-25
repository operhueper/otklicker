# Accessibility audit — Phase 6 — 2026-04-25
Auditor: accessibility-auditor
Стандарт: WCAG 2.1 AA (с примечаниями по WCAG 2.2)
Тестовое окружение: Playwright (Chromium), localhost:3001, viewports 1280×720 + 375×812

## Findings

### CRITICAL (блокер запуска)

#### C-1. Белый текст на градиенте `--brand-gradient` уходит в жёлтую зону → 1.67:1
- **WCAG 1.4.3 Contrast (Minimum) — Level AA**
- Brand-gradient: `#FBBF24 → #F97316 → #EF4444 → #DB2777`. Контраст белого на каждой остановке:
  - `#FBBF24` (yellow) — **1.67:1** (FAIL для normal и large text)
  - `#F97316` (orange) — **2.80:1** (FAIL для normal, FAIL для large text 3:1 — на грани)
  - `#EF4444` (red) — **3.76:1** (PASS large text 3:1, FAIL normal 4.5:1)
  - `#DB2777` (pink) — **4.60:1** (PASS normal)
- Затрагивает (white text по всей градиентной длине, левая часть всегда жёлтая):
  1. `Nav` → кнопка "Запустить бота" (`btn-primary`)
  2. `Hero` → "Открыть @otklicker_bot" (`btn-primary`)
  3. `Pricing` → бренд-карта "Активный" — `background: var(--brand-gradient)`, белый текст для цены `790₽`, sub `за 3 недели`, label `Активный`, описаний features. **Полностью на градиенте — большая часть текста на жёлтом конце.**
  4. `FinalCTA` → весь блок `background: var(--brand-gradient)`, h2 + параграф + кнопка "Канал @otklicker" (полупрозрачная белая рамка) — низкий контраст
  5. `CookieBanner` → кнопка "Принять"
  6. `Features` → активный таб (`background: var(--brand-gradient)`, белый текст 14px)
  7. `HowItWorks` → активная карточка шага использует gradient для номера-кружка (текст белый — но крупный и жирный, всё равно проблема для номера на жёлтом)
- **Fix:**
  - Сместить градиент так, чтобы белый текст всегда оказывался на тёмной части (>= `#EF4444`): сменить background на `linear-gradient(135deg, #F97316 0%, #EF4444 50%, #DB2777 100%)` для текстовых поверхностей; или
  - Альтернативно покрыть текстовый блок overlay `rgba(0,0,0,0.18)` — повысит контраст без потери цвета бренда; или
  - Использовать тёмный текст (`color: #1C1917`) на жёлто-оранжевой части — но тогда теряется яркость; или
  - Вынести текст за пределы градиента (сейчас Pricing brand-card делает это правильно для бейджа сверху — `#1C1917` background)

#### C-2. Pricing brand-card — крупная цена `790` (white, 56px, 900) на gradient жёлтом
- **WCAG 1.4.3 — даже large text (3:1) не проходит на самой светлой остановке**
- На `#FBBF24` соотношение для крупного текста 1.67:1 — fail.
- **Fix:** см. C-1.

#### C-3. Отсутствие `prefers-reduced-motion` — нарушает 2.3.3 (AAA) и в spirit 2.2.2 (AA)
- **WCAG 2.3.3 Animation from Interactions — Level AAA** (рекомендация для 2.1 AA-сайтов с автозапуском)
- **WCAG 2.2.2 Pause, Stop, Hide — Level A** (для авто-обновляющегося контента)
- В CSS обнаружено **0 правил** `@media (prefers-reduced-motion: reduce)`. Активны:
  - **HeroChat** auto-cycle каждые 3 секунды (setTimeout): меняет вакансию, анимирует translateX(130%) + opacity. Невозможно остановить через системные настройки.
  - **SpeedSection** RAF-анимация прогресса гонки (запускается на IntersectionObserver, играет однократно — это лучше, но всё равно играет автоматически).
  - **HowItWorks** `.animate-slide-in-from-right` (Tailwind keyframe) при смене активной карточки.
  - **Features** `.animate-slide-in-features` при переключении табов.
  - 58 элементов с активным `transition`.
- **Fix (минимум):** добавить в `globals.css`:
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
  ```
  Дополнительно для HeroChat — отключить `setTimeout`-цикл, если `matchMedia('(prefers-reduced-motion: reduce)').matches`. Иначе движение JS-таймером не остановится CSS-правилом.

### HIGH

#### H-1. HeroChat счётчики `127 откликов / 95 пропущено` обновляются без `aria-live`
- **WCAG 4.1.3 Status Messages — Level AA**
- `<div>` со значениями инкрементируется каждые 3с (паузу можно поставить только через клик по кнопкам внутри, но скриnреадер не получит обновления).
- **Fix:** обернуть оба бэйджа в контейнер `<div aria-live="polite" aria-atomic="true">`. Также — auto-cycling само по себе нарушает 2.2.2; кнопки "Откликнуться/Пропустить" останавливают анимацию (paused state) — это частичный workaround, но скринридер не понимает, что это "управляющая" кнопка для анимации.

#### H-2. Hero counters пилюли «откликов / пропущено» — пограничный контраст
- **WCAG 1.4.3 — текст 12px (700)**
- `#15803D` на mixed `rgba(22,163,74,0.12)` over `#FAFAF9` = effective `rgb(223,240,228)` → **4.23:1** — пройдено по жёсткой границе 4.5:1? Нет, 4.23 < 4.5 → **FAIL для normal text 12px** (700 weight не делает его large — large = 18.66px+ или 14px+ bold; 12px bold не large).
- `#B91C1C` на `rgb(249,232,231)` → **5.46:1** PASS.
- **Fix:** затемнить зелёный до `#13633C` или поднять непрозрачность плашки.

#### H-3. Tablist `Features` — нет клавиатурной поддержки стрелок
- **WCAG 2.1.1 Keyboard — Level A** (минимум — Tab-доступ есть, отметим как нарушение паттерна WAI-ARIA Authoring Practices, не строгий fail Level A)
- Реальный fail — **2.4.7** (Focus Visible) проходит, но **WAI-ARIA Tabs Pattern** требует:
  - Стрелки Left/Right между табами
  - Home/End на крайние
  - Активация через Enter/Space
- Сейчас `role="tablist"` + `role="tab"` + `aria-selected` на месте, но handler на onClick — стрелки не работают. Скринридеры объявляют табы, но навигация только Tab по каждой.
- **Fix:** добавить onKeyDown handler на tablist с `e.key==='ArrowRight'/'ArrowLeft'/'Home'/'End'` для перемещения focus + setActive.

#### H-4. CookieBanner — нет `role="dialog"` и `aria-label`
- **WCAG 4.1.2 Name, Role, Value — Level A**
- Это нижний баннер, важный для согласия. Сейчас просто `<div>` без роли. Скринридер прочтёт текст внутри как обычный контент, но связь с двумя кнопками теряется.
- **Fix:** обернуть в `<div role="region" aria-label="Согласие на использование cookies">` или (если он модальный) `role="dialog" aria-modal="false" aria-labelledby="..."`. Так как баннер не блокирует страницу — `region` корректнее.

#### H-5. Footer — нет `<nav>` для блоков ссылок
- **WCAG 1.3.1 Info and Relationships — Level A**
- Колонки "Продукт / Поддержка / Компания" — это списки навигационных ссылок. Сейчас просто `<div>` с `<a>` подряд.
- **Fix:** обернуть каждую группу в `<nav aria-label="Продукт">` или единый `<nav aria-label="Подвал">` со списками `<ul><li>`.

### MEDIUM

#### M-1. Skip-to-content link отсутствует
- **WCAG 2.4.1 Bypass Blocks — Level A**
- Первый focusable элемент — логотип-ссылка `#top` (что де-факто = #main, но скринридер этого не знает). Нет `<a class="skip-link" href="#main">Перейти к содержимому</a>`.
- На сайте 5 ссылок в навигации + большой `Hero`; пользователь Tab-ом на FAQ дойдёт через 20 нажатий. Skip-link ускорит.
- **Fix:** добавить как первый элемент `<body>`:
  ```jsx
  <a href="#main-content" className="skip-link">Перейти к содержимому</a>
  ```
  c CSS, скрывающим до `:focus`.
- Также `<main id="main-content">` (сейчас `<main>` без id).

#### M-2. Heading hierarchy — на главной странице **нет h2 у `Hero`**, при этом h1 один; OK. Но...
- **WCAG 1.3.1**
- Декоративный/мокапный текст внутри `RealBotScreen` имеет жирные элементы вроде `Я первый бот автооткликов на HH.ru`, `Панель HH.ru` — без `<h*>`. Корректно, что не заголовки.
- TeaserStrip содержит крупные числа `×3 / x7 / 24/7` без semantic stat-структуры — это ОК как visual emphasis, но для скринридера может звучать "иксз больше приглашений" (ноль контекста). Желательно заменить `×` на буквенный знак или добавить `aria-label` на цифру.
- **Fix:** TeaserStrip числа — обернуть в `<dt>/<dd>` или дать `aria-label`: `<div aria-label="в три раза больше приглашений">×3</div>`.

#### M-3. Активный/неактивный таб — индикатор только цветом + бордером
- **WCAG 1.4.1 Use of Color — Level A** + **1.4.11 Non-text Contrast — AA**
- Активный = градиент (заливка). Неактивный = transparent + 1px `var(--line-dark)` (≈ rgba(254,243,199,0.12)) против тёмного фона. Контраст рамки **1.39:1** против фона — **FAIL 3:1 для UI components**.
- Хорошо, что `aria-selected` есть — скринридер прочтёт. Но для зрячего sighted-keyboard-пользователя без screenreader индикация неактивных табов слишком тонкая.
- **Fix:** усилить рамку неактивных до `var(--line-strong)` цвета в dark-режиме (например `rgba(254,243,199,0.35)`) или сделать неактивные с лёгкой `background: rgba(255,255,255,0.04)`.

#### M-4. Footer column-links — target size 22px высота
- **WCAG 2.5.8 Target Size (Minimum) — Level AA (новое в 2.2)**
- На /375 высота link-блоков "Политика конфиденциальности", "Cookies", "Оферта", "Политика данных бота" — **22px** (требуется 24px для WCAG 2.2 AA, либо inline exception). Footer — не inline-текст, поэтому исключение не работает.
- Также nav-bar mobile (`display:none` на <860, скрыт). На /375 проблема в footer.
- **Fix:** в footer колонках увеличить vertical gap до 12px (текущий 10px) или min-height каждой ссылки до 24px.

#### M-5. Inline english fragments без `lang="en"`
- **WCAG 3.1.2 Language of Parts — Level AA**
- Тексты в Hero/Features mockup: `Senior Product Designer`, `Senior Designer`, `Intermediate`, `Полная`, `Гибрид`. Часть мокапов вакансии HH — то есть это симулированный контент. Скринридер русским голосом прочтёт как русский — звучит коряво.
- **Severity LOW-MEDIUM:** мокап-демо, не основной контент.
- **Fix:** обернуть в `<span lang="en">Senior Product Designer</span>`. Не блокер, можно отложить.

#### M-6. Privacy/Cookies pages — нет Nav и Footer
- **WCAG 3.2.3 Consistent Navigation — Level AA**
- `/privacy` и `/cookies` рендерят только `<main>` с MD-контентом. Без шапки/подвала пользователь теряет основные навигационные ссылки. Только "← На главную".
- **Fix:** добавить `<Nav />` и `<Footer />` на legal-страницах.

### LOW

#### L-1. `<header>` отсутствует
- **WCAG 1.3.1**
- На главной `<nav>` стоит фиксированно сверху, но не обёрнута в `<header>`. Не строгое нарушение (nav сам по себе landmark), но семантически принято.
- **Fix:** обернуть `<Nav />` в `<header role="banner"><Nav/></header>` либо изменить в самом Nav.

#### L-2. `apple-icon.png` 404 в console
- **Не WCAG, но косвенно — page integrity**
- Manifest ссылается на /apple-icon.png; есть только icon.tsx. Не критично для a11y, но добавляет ошибку в DevTools.

#### L-3. Hero "Авторизация на HH..." — параграф объявлен `<div>`, не `<p>`
- **WCAG 1.3.1**
- Семантически — пояснение к CTA, должен быть `<p>`. Сейчас просто `<div>` с font-size 13.
- **Fix:** заменить `<div>` на `<p>`.

#### L-4. FAQ button — кружок-индикатор `<Plus/>/<Minus/>` без `aria-hidden`
- **WCAG 1.1.1 (информативный иконке)** — низкая severity
- Кружок чисто декоративный, текст вопроса слева полностью описывает контрол. Иконка lucide рендерит SVG без aria-hidden, и Playwright snapshot показывает `img` ноды.
- **Fix:** добавить `aria-hidden="true"` к иконкам внутри кнопки FAQ (и аналогично — `<Send>` внутри кнопок CTA, если их сопровождает текст).
- Заметим: lucide-react иконки в Hero/Features уже встречаются с `aria-hidden="true"` в JSX (вижу `<svg ... aria-hidden="true">` в коде HeroChat, Speed). Однако на `<Send/>` и `<Plus/>` от lucide-react этот атрибут не передаётся автоматически — нужно проверить и добавить.

#### L-5. HowItWorks использует `aria-pressed` (toggle pattern), а не `role="tab"` + `aria-selected`
- **WCAG 4.1.2 — корректно работает, но семантически это табы**
- Семантически HowItWorks — это табы (одна правая панель меняется в зависимости от активного шага). `aria-pressed` подходит для toggle-кнопок.
- **Fix (косметика):** переделать в `role="tablist"` + `role="tab"` + `role="tabpanel"` для консистентности с Features. Не блокер.

#### L-6. Кнопки "В чёрный список" / "Открыть на HH" в Hero phone mockup — это `<div>`, не интерактивные
- Декоративный мокап, корректно как `<div>`. Но визуально похоже на кнопку — потенциально путает пользователей. Не a11y-нарушение.

### POSITIVE

- `lang="ru"` на `<html>` — корректно.
- `<meta viewport>` без `user-scalable=no` или `maximum-scale` — pinch-zoom работает (1.4.4 Resize text).
- Один `<h1>` на главной, два h2 не подряд через h3 — иерархия чистая.
- `:focus-visible` глобальное правило с **видимым 2px solid orange outline + 3px offset** — отличная практика. Контраст ring 3.76:1 на белом — passes 1.4.11 (3:1).
- `nav role="navigation" aria-label="Основная навигация"`, `<main>`, `<footer>` — landmarks на месте.
- FAQ — корректные `aria-expanded`, `aria-controls`, и открытая панель имеет `role="region" aria-labelledby="faq-btn-${id}"`. Идеально.
- Features — корректный `role="tablist" aria-label="Функции бота"` + `role="tab" aria-selected` + `role="tabpanel" id={...} aria-labelledby`. ARIA structure правильный (только клавиатура/стрелки отсутствуют, см. H-3).
- Декоративные `.halo`, `.noise`, gradient-blob divs все имеют `aria-hidden="true"`. Очень хорошо.
- Инлайн-SVG иконки в HeroChat, Speed, RealBotScreen имеют `aria-hidden="true"`.
- Все внешние ссылки `target="_blank"` имеют `rel="noopener noreferrer"`.
- Корректно: `htmlFor`/`id` связки для FAQ; semantic `<button>` (не `<div role="button">`).
- ListItem-структуры (Pricing features, HowItWorks bullets) — реальные `<ul><li>`.

## Heading hierarchy

- **h1** (1 шт): "Откликается на свежие вакансии за вас."
- **h2** (5–6 шт):
  - "Четыре шага до первого отклика" (HowItWorks)
  - "Что делает бот внутри Telegram" (Features)
  - "Гонка длится 14 часов. Бот стартует через 10 минут." (Speed)
  - "Платите, пока ищете работу" (Pricing)
  - "Короткие ответы на частые вопросы" (FAQ)
  - "Свежая вакансия ждать не будет" (FinalCTA)
- **h3** (1 шт, ротируется по вкладкам): текущий headline активной фичи в Features ("Отклики уходят в первые минуты" / "...карточки..." / "...HR...")
- TeaserStrip и Footer column-titles **не имеют h-структуры** (decorative визуальный текст / визуальные labels) — корректно.
- /privacy, /cookies — h1 + h2/h3 из markdown — корректная иерархия.

## Контраст таблица

| Секция | Текст | Фон | Контраст | Pass (4.5:1 norm / 3:1 large) |
|---|---|---|---|---|
| Hero h1 | `#92400E` | `#FAFAF9` | 6.79 | PASS large |
| Hero лид (19px) | `#B45309` | `#FAFAF9` | 4.81 | PASS normal |
| Hero eyebrow (12px 600) | `#92400E` | `#FEF3C7` | 6.37 | PASS normal |
| Hero auth-note (13px) | `#B45309` | `#FAFAF9` | 4.81 | PASS normal |
| Hero counter green (12px 700) | `#15803D` | mixed `#DFF0E4` | **4.23** | **FAIL normal** |
| Hero counter red (12px 700) | `#B91C1C` | mixed `#F9E8E7` | 5.46 | PASS normal |
| Hero btn-primary (white) | `#FFF` | gradient @ `#FBBF24` end | **1.67** | **FAIL** |
| Hero btn-primary (white) | `#FFF` | gradient @ `#DB2777` end | 4.60 | PASS normal |
| Features h2 | `#FEF3C7` | `#1C1917` | 15.71 | PASS large |
| Features lead p (17px) | `#FBBF24` | `#1C1917` | 10.48 | PASS normal |
| Features tab inactive | `#FBBF24` | `#1C1917` (1.39 border) | 10.48 (text) | PASS text / **FAIL border 3:1** |
| Features tab active | `#FFF` | gradient | **1.67** на жёлтой части | **FAIL** |
| Features h3 (42px) | `#FEF3C7` | `#1C1917` | 15.71 | PASS large |
| Features `<li>` text (15px) | `#FEF3C7` | `#1C1917` | 15.71 | PASS normal |
| Speed status badge (12px 700) | `#92400E` | `#FEF3C7` | 6.37 | PASS normal |
| Speed stat value (38px 900) | `#92400E` | `#FEF3C7` | 6.37 | PASS large |
| Speed stat label (14px) | `#B45309` | `#FEF3C7` | 4.51 | PASS normal |
| Speed filters small (11px 700) | `#B45309` | `#FEF3C7` | 4.51 | PASS normal |
| Speed sleep label (16px) | rgba(120,113,108,0.7) | hatched + `#FFF` | 9.07 (best case) | PASS normal |
| Pricing free-card name (13px) | `#92400E` | `#FFF` | 7.09 | PASS normal |
| Pricing badge "37 ₽ в день" | `#FEF3C7` | `#1C1917` | 15.71 | PASS normal |
| Pricing brand-card all white text | `#FFF` | gradient (often yellow) | **1.67–4.60** | **FAIL** на жёлтой/оранжевой части |
| Pricing lead p (17px) | `#B45309` | `#FAFAF9` | 4.81 | PASS normal |
| FAQ question (17px 700) | `#92400E` | `#FFF` | 7.09 | PASS normal |
| FAQ answer (15px) | `#78350F` | `#FFF` | 9.07 | PASS normal |
| Footer link (14px) | `#B45309` | `#FAFAF9` | 4.81 | PASS normal |
| Footer copyright (12px) | `#B45309` | `#FAFAF9` | 4.81 | PASS normal |
| Cookie ghost btn (13px 600) | `#92400E` | `#FAFAF9` | 6.79 | PASS normal |
| Cookie brand btn (white) | `#FFF` | gradient | **1.67–4.60** | **FAIL** на жёлтой части |
| Teaser label (14px) | `#B45309` | `#FEF3C7` | 4.51 | PASS normal |
| FinalCTA p (18px) | `#FFF` | gradient | **1.67–4.60** | **FAIL** на жёлтой части |

## ARIA completeness

- [x] FAQ `aria-expanded` + `aria-controls` + связанный `role="region" aria-labelledby`
- [x] Features `role="tablist" aria-label="Функции бота"` + `role="tab" aria-selected aria-controls` + `role="tabpanel" id aria-labelledby`
- [x] HowItWorks `aria-pressed` (semantically toggle, not tab — приемлемо)
- [ ] CookieBanner `role="dialog"` или `role="region" aria-label="..."` — **отсутствует**
- [x] Декоративные halo / noise / gradient blobs — `aria-hidden="true"` везде
- [x] Иконки в кнопках с текстом (Send, ArrowRight) — рядом сопутствующий текст; lucide-react не добавляет автоматически `aria-hidden`, но скринридер игнорирует SVG без role/aria-label
- [x] `<nav role="navigation" aria-label="Основная навигация">`
- [x] `<main>`, `<footer>`
- [ ] `<header>` обёртка для Nav — отсутствует (LOW)
- [ ] `<nav>` внутри footer — отсутствует
- [ ] `aria-live` на HeroChat счётчиках — отсутствует
- [ ] Tabs клавиатурные стрелки — отсутствуют

## Reduced motion

- **FAIL:** ноль `@media (prefers-reduced-motion: reduce)` правил в CSS. Анимации играют независимо от системной настройки:
  - HeroChat: setTimeout-цикл 3000ms (carousel)
  - SpeedSection: requestAnimationFrame одноразовая авто-проигрыша при scroll-into-view
  - HowItWorks/Features: keyframe slide-in при смене tab
  - 58 elements с активным `transition`
- Hero auto-cycle также нарушает **WCAG 2.2.2 (Pause, Stop, Hide)** — больше 5 секунд автоматического движения требует механизм паузы. Кнопки "Откликнуться/Пропустить" останавливают цикл, но не самоочевидны как pause-control.

## Score

- **Контраст:** 6/10 — основные текстовые блоки на статичных фонах проходят, но ВСЕ `.btn-primary` и весь FinalCTA + Pricing brand-card + Cookie brand button + Features active tab имеют белый текст на градиенте, который провисает до 1.67:1 на жёлтой остановке. Это шесть мест по всему сайту — критично.
- **Клавиатура:** 8/10 — Tab-проход логичен, focus-visible виден везде, ARIA attrs корректные. Минусы: tabs без стрелок, skip-link отсутствует, footer column-links 22px высотой на mobile.
- **ARIA:** 8/10 — FAQ и Features образцовые, landmarks на месте; пропущены CookieBanner role, footer nav, aria-live на счётчиках.
- **Reduced motion:** 1/10 — полное игнорирование `prefers-reduced-motion`.

**Total: 5.75/10 — YELLOW (запуск возможен, но контраст на градиенте и reduced-motion должны быть закрыты до релиза)**

## Action items до публикации

### Блокирующие
- [ ] **C-1, C-2:** Сместить `--brand-gradient` для текстовых поверхностей так, чтобы белый текст не оказывался на `#FBBF24/#F97316`. Минимум — `linear-gradient(135deg, #F97316 0%, #EF4444 50%, #DB2777 100%)` для `.btn-primary`, Pricing brand-card, FinalCTA, Cookie "Принять", Features active tab. Декоративные градиенты (на h1 `.grad-text`, halo) трогать не обязательно — они не несут текст.
- [ ] **C-3:** Добавить глобальный `@media (prefers-reduced-motion: reduce)` блок в `globals.css` (см. сниппет в C-3). Дополнительно — в HeroChat обернуть auto-cycle setTimeout проверкой `matchMedia('(prefers-reduced-motion: reduce)').matches`.

### Highly recommended до релиза
- [ ] **H-1:** Hero счётчики обернуть в `<div aria-live="polite" aria-atomic="true">` или отказаться от инкремента счётчиков (статичные числа выглядят достоверно).
- [ ] **H-2:** Зелёная пилюля счётчика — затемнить текст до `#13633C` или сделать фон менее прозрачным (alpha 0.18 вместо 0.12) для контраста ≥ 4.5:1.
- [ ] **H-3:** Features tablist — добавить keyboard arrow handler (ArrowLeft/ArrowRight + Home/End).
- [ ] **H-4:** CookieBanner — `role="region" aria-label="Согласие на cookies"` (это persistent banner, не модалка).
- [ ] **H-5:** Footer колонки обернуть в `<nav aria-label="...">` со списками `<ul><li>`.

### Sprint-2 / Maintenance
- [ ] **M-1:** Добавить skip-to-content link перед `<Nav />`.
- [ ] **M-3:** Усилить рамку неактивных табов в Features (border ≥ 3:1 на тёмном фоне).
- [ ] **M-4:** Footer column-links на /375 — увеличить min-height до 24px (gap 12px).
- [ ] **M-6:** Добавить `<Nav/>` и `<Footer/>` на /privacy и /cookies (consistent navigation).
- [ ] **M-2:** TeaserStrip числа `×3 / x7` — `aria-label="в три раза больше приглашений"`.
- [ ] **M-5:** `lang="en"` на инлайн-фрагментах в мокапах вакансии (low priority).

### Nice-to-have
- [ ] **L-1:** Обернуть Nav в `<header>`.
- [ ] **L-2:** Добавить /apple-icon.png либо убрать ссылку из manifest (404 в console).
- [ ] **L-3:** Hero auth-note `<div>` → `<p>`.
- [ ] **L-4:** lucide-react иконки внутри кнопок с текстом — добавить `aria-hidden="true"` для гигиены.
- [ ] **L-5:** HowItWorks → `role="tablist"` (косметика).

## Methodology

- Tools: Playwright Chromium (1280×720 + 375×812), inline contrast calculator (WCAG 2.x relative luminance), accessibility tree snapshot.
- Scope: 5 routes (/, /privacy, /cookies, /offer, /bot-privacy).
- Manual: focus order traversal Tab-by-Tab, computed-style scrape, gradient-stop simulation для всех вариантов градиента.
- Не проводилось: реальный screenreader тест (VoiceOver/NVDA), тест 200%/400% zoom, Forced Colors mode. Рекомендуется до публичного запуска.
