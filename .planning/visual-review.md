# Visual review otklicker.ru — Phase 6 — 2026-04-25
Reviewer: designer (Sonnet 4.6)
Метод: Playwright screenshots + DOM measurements + code audit

## Скриншоты
- [home-1240.png](./screenshots/home-1240.png)
- [home-960.png](./screenshots/home-960.png)
- [home-720.png](./screenshots/home-720.png)
- [home-375.png](./screenshots/home-375.png)
- [privacy-1240.png](./screenshots/privacy-1240.png)
- [cookies-1240.png](./screenshots/cookies-1240.png)
- [offer-1240.png](./screenshots/offer-1240.png)
- [bot-privacy-1240.png](./screenshots/bot-privacy-1240.png)

---

## Findings по секциям

### Nav
- ✅ Sticky, height 73px (spec 72 — 1px drift, не видно)
- ✅ scroll=0: bg transparent, backdropFilter none — корректно
- ✅ scroll>12: blur + border появляются (code confirmed)
- ✅ 5 nav-ссылок + CTA «Запустить бота» с Send-иконкой
- ✅ `≤860px` скрывает `.nav-links` через inline `<style>` — работает
- ✅ BrandLockup + CTA на мобильном остаются

### Hero
- ✅ paddingTop 120, paddingBottom 80 — точно по спеке
- ✅ grid `1.1fr / 1fr`, gap 80px
- ✅ H1: 74.4px (clamp), weight 900, letter-spacing -0.03em (-2.232px)
- ✅ `.grad-text` на «свежие вакансии» — градиент работает, color transparent
- ✅ Eyebrow с eyebrow-dot + текст «Telegram-бот для поиска работы на HH.ru»
- ✅ 2 кнопки (btn-primary «Открыть @otklicker_bot», btn-ghost «Канал @otklicker»)
- ✅ Дисклеймер про пароль — присутствует
- ✅ Halo-блобы (жёлтый 520×520, розовый 420×420) — рендерятся
- ✅ HeroChat с автоциклом (3000ms) — вариант chat по умолчанию
- ❌ **LOW**: `≤960px` Hero сворачивается в 1 колонку — OK по коду, но на 960px breakpoint правая колонка (HeroChat) видна под текстом только частично из-за `minHeight: 540` на container без responsive overide. Нужно проверить, что height не обрезает чат на 960.

### TeaserStrip
- ✅ 3 элемента: ×3 больше приглашений, ×7 быстрее первый оффер, 24/7 HR-автоответы
- ✅ bg `--bg-pastel` (rgb 254,243,199)
- ✅ responsive: `≤720px` grid 2 колонки через inline style
- ❌ **LOW**: inline `<style>` тег внутри компонента для медиазапроса (паттерн повторяется в нескольких компонентах — nav, hero, teaser, features, pricing). Не критично функционально, но нечисто. В Phase 7 стоит унифицировать в globals.css или Tailwind.

### HowItWorks
- ✅ bg `--bg-pastel`, padding 96/96
- ✅ Section-head по центру, max-width 720
- ✅ H2 «Четыре шага / до первого отклика» с grad-text на «отклика»
- ✅ grid `1fr / 1.1fr` (обратный порядок fr по спеке — spec говорит `1fr / 1.1fr`, код `1fr 1.1fr` — соответствует)
- ✅ 4 шага-кнопки с aria-pressed; шаг 0 — активный при загрузке
- ✅ Активный шаг: белый фон + border + тень — подтверждено DOM
- ✅ RealBotScreen справа меняется по клику
- ✅ slideInFromRight анимация на смену экрана — объявлена в globals.css как `animate-slide-in-features` class (через Tailwind arbitrary? — нет, в globals нет @keyframes slideInFromRight как класса)
- ❌ **MEDIUM**: `@keyframes slideInFromRight` из оригинального `styles.css` **не перенесён** в `globals.css`. В `features.tsx` используется `className="animate-slide-in-features"` и в `how-it-works.tsx` аналогично — но этого класса нет ни в Tailwind config, ни в globals.css. Анимация смены экрана в HowItWorks и Features молча не работает. Нужно добавить в globals.css.

### Features
- ✅ bg `--bg-dark` (#1C1917), text `--text-on-dark`
- ✅ `.noise` overlay (opacity 0.04) — присутствует
- ✅ Два halo-блоба (розовый + оранжевый) — рендерятся
- ✅ Section-head LEFT-aligned (textAlign: 'left') — соответствует спеке
- ✅ 3 таба-пилюли: «01 · Автоотклики», «02 · Карточки и сопроводительные», «03 · Переписка с HR»
- ✅ Активный таб: background `var(--brand-gradient)`, тень 0 10px 24px rgba(219,39,119,0.25)
- ✅ ARIA: role="tablist", role="tab", aria-selected, aria-controls — корректно
- ✅ Bullet-list с 24×24 brand-gradient чекбоксами и Check icon
- ✅ RealBotScreen справа — адаптивный
- ❌ **MEDIUM**: Та же проблема — `animate-slide-in-features` класс не определён. Смена экрана между табами происходит без анимации. Нужен `@keyframes slideInFromRight` в globals.css + `.animate-slide-in-features { animation: slideInFromRight 0.5s cubic-bezier(.2,.8,.2,1); }`.
- ❌ **LOW**: Таб-кнопки используют `aria-selected` (роль tab), но нет `aria-pressed`. По спеке — `aria-pressed` (для toggle-кнопок); с role="tab" + aria-selected — более корректно, но стоит проверить screen-reader поведение.

### SpeedSection
- ✅ bg `--bg` (#FAFAF9), padding 96/96
- ✅ IntersectionObserver autoplay при 35% видимости — реализован
- ✅ RAF-анимация прогресса (PLAY_MS) — реализована
- ❌ **LOW**: `tabular-nums` — не нашли `.tabular`-элементов в SpeedSection (0 найдено). Числа в таймлайне могут прыгать по ширине при анимации. Нужно добавить `fontVariantNumeric: 'tabular-nums'` на числовые элементы внутри.
- ❌ **LOW**: Bot-privacy скриншот показал homepage — это артефакт многовкладочности Playwright, не реальный баг. Curl подтвердил что `/bot-privacy` рендерится корректно.

### Pricing
- ✅ 2 карточки — Бесплатный + Активный
- ✅ Брендовая карточка: `transform: matrix(1.03, 0, 0, 1.03, 0, 0)` — подтверждено DOM
- ✅ brand-gradient фон, box-shadow brand
- ✅ Бейдж «37 ₽ в день» — position absolute, top -12, right 24, bg #1C1917, color #FEF3C7
- ✅ Цена 56/900, единица 22/700, период 14
- ✅ Check-иконки: белые на brand, #DB2777 на free
- ✅ CTA-кнопка: белая с текстом #DB2777 на brand, тёмная с белым на free
- ✅ Сноска про ЮKassa + 14 дней — присутствует
- ✅ `≤960px` — 1 колонка
- ❌ **LOW**: `padding: '96px 0'` у секции, но `margin: '48px auto 0'` у грида + badge `top: -12` может выходить за padding-top контейнера при 1-колоночном layout на мобильном (визуально OK по скриншоту, но стоит перепроверить на iOS Safari).
- ❌ **LOW**: Container padding 24px (`px-6` = 24px) против спеки 32px desktop / 20px mobile. Разница 8px. Визуально незначительна, но несоответствие спеке.

### FAQ
- ✅ bg `--bg-pastel`, padding 96/96
- ✅ max-width 760 аккордеон
- ✅ Первый элемент открыт по умолчанию (aria-expanded="true" на первой кнопке — подтверждено)
- ✅ Иконка +/− в круге 32×32; открытый — brand-gradient, закрытый — bg-pastel
- ✅ aria-expanded, aria-controls, role="region" — a11y корректен
- ✅ Плавный toggle (inline conditional render — нет framer-motion, но достаточно)
- ❌ **LOW**: Нет анимации высоты при открытии/закрытии. Контент мгновенно появляется/исчезает. Спека не требует плавной анимации explicitно, но «плавное раскрытие» упомянуто. Можно добавить `max-height` transition или `<details>` native.

### FinalCTA
- ✅ padding 80/40, bg `--bg`
- ✅ Карточка border-radius 32, padding 64×48, brand-gradient, белый текст
- ✅ Два декоративных блоба внутри карточки
- ✅ H2 «Свежая вакансия / ждать не будет»
- ✅ 2 кнопки — белая «Открыть @otklicker_bot» + полупрозрачная «Канал @otklicker»
- ✅ Все CTA → Telegram с target="_blank" rel="noopener"

### Footer
- ✅ bg `--bg`, border-top `--line`, padding 48/36
- ✅ BrandLockup size="md" + подзаголовок
- ✅ 3 колонки: Продукт / Поддержка / Компания — корректно
- ✅ Email `info@otklicker.ru` — унифицирован (оба вхождения: в columns и в copyright bar)
- ✅ Copyright «© 2026 Откликер. Не аффилирован с hh.ru.»
- ❌ **LOW**: Footer не имеет nav landmark (нет `<nav>` внутри footer для ссылок). Незначительно для a11y но хорошая практика.

### CookieBanner
- ✅ Существует в DOM при `localStorage.otklicker_cookie_consent = null`
- ✅ position fixed bottom 0, zIndex 200
- ✅ 2 кнопки: «Только необходимые» + «Принять» (brand-gradient)
- ✅ Ссылка на /cookies
- ✅ localStorage key `otklicker_cookie_consent` — соответствует спеке
- ✅ Не ломает layout (находится поверх контента, не сдвигает страницу)
- ❌ **LOW**: Нет role="dialog" / aria-label на баннере. Для screen reader пользователей баннер не объявляется.

### Legal-страницы (/privacy, /cookies)
- ✅ /privacy — полный документ (12 разделов, реальный контент)
- ✅ /cookies — полный документ с таблицами cookies
- ✅ /offer — плейсхолдер «Документ готовится» + ссылка «← На главную»
- ✅ /bot-privacy — плейсхолдер «Документ готовится» + ссылка «← На главную» (подтверждено curl)
- ❌ **MEDIUM**: Плейсхолдер-страницы (/offer, /bot-privacy) не используют общий `<Nav>` и `<Footer>` — это plain `<main>` без обёртки. При навигации на эти страницы пользователь теряет навигацию. Нужен либо общий layout, либо кнопка «На главную» хотя бы стилизована брендово (сейчас — нестилизованная ссылка).
- ❌ **LOW**: /privacy и /cookies не имеют Nav/Footer либо отдельного back-navigation компонента — нет кнопки «← На главную» на этих страницах (только prose content). Пользователь попадает на /privacy без способа вернуться кроме браузерной кнопки.

### Шрифты
- ✅ Inter через `next/font/google`, subsets latin + cyrillic, все веса 400-900
- ✅ CSS variable `--font-inter` применяется на `<html>`
- ✅ Font preload headers в HTTP-ответе (woff2 preloaded)
- ✅ На скриншотах Inter отрисован корректно, нет fallback

### Градиенты и цвета
- ✅ `--brand-gradient: linear-gradient(135deg, #FBBF24 0%, #F97316 33%, #EF4444 66%, #DB2777 100%)` — соответствует спеке
- ✅ `.grad-text`: background-image градиент, color transparent, -webkit-text-fill-color transparent — корректно
- ✅ Все секционные цвета соответствуют токенам: bg-pastel, bg-dark, bg

### Адаптив
- ✅ 1240: 2-колоночные грид-секции, всё на месте
- ✅ 960: Hero переходит в 1 колонку, pricing в 1 колонку, features в 1 колонку
- ✅ 720: compact layout, teaser 2 колонки → OK
- ✅ 375: всё в 1 колонку, текст читаем, кнопки не обрезаны
- ❌ **MEDIUM**: На 375 H1 «Откликается на свежие вакансии за вас.» — clamp(44px, 6vw, 80px) на 375px = ~22.5px вычисленный vw, но clamp нижняя граница 44px срабатывает. Однако три строки при 44px на экране 375px занимают большую долю first viewport. Визуально норм но на 320px (старые Android) может быть проблема. Не критично для современных устройств.
- ❌ **LOW**: Nav links скрываются на ≤860 но нет hamburger-меню. Это known backlog по спеке — упомянуто как «мобильное меню навигации (если бэклог)». Приемлемо на текущем этапе.

### Анимации
- ✅ `btn:hover` translateY(-1px) — реализован
- ✅ `btn-primary:hover` усиленный box-shadow — реализован
- ✅ Nav scroll transition 0.2s ease — реализован
- ✅ SpeedSection IntersectionObserver autoplay — реализован
- ✅ HeroChat auto-cycle 3000ms (70/30 split) — реализован
- ✅ FAQ accordion toggle (мгновенный) — работает
- ❌ **MEDIUM**: `slideInFromRight` анимация НЕ реализована в globals.css. Классы `animate-slide-in-features` используются в Features и HowItWorks (key prop обеспечивает remount), но сам keyframe и утилит-класс отсутствуют. Смена RealBotScreen происходит без анимации.
- ❌ **LOW**: `pulseRing`, `typingDots`, `floatY` из спеки — не проверялись отдельно. В онлайн-индикаторе RealBotScreen они могут использоваться. Нужна отдельная проверка RealBotScreen компонента.

### A11y
- ✅ `:focus-visible` outline 2px orange — в globals.css
- ✅ `role="navigation"` aria-label на Nav
- ✅ `role="tablist"` / `role="tab"` / `aria-selected` / `aria-controls` в Features
- ✅ `aria-pressed` на кнопках шагов в HowItWorks
- ✅ `aria-expanded` / `aria-controls` / `role="region"` в FAQ
- ✅ `aria-hidden="true"` на декоративных элементах (halo, eyebrow-dot, noise)
- ❌ **LOW**: Features использует `aria-selected` (правильно для role="tab"), но HowItWorks использует `aria-pressed` (step-buttons, роль button) — это семантически разные паттерны. Оба функциональны, но непоследовательны.
- ❌ **LOW**: CookieBanner не имеет role="dialog" / aria-label / aria-live — не объявляется screen reader.
- ❌ **LOW**: Footer nav-колонки без `<nav>` landmark.

### Console errors
- Зафиксированы 1 error + 1 warning при навигации. Точный текст из лога не доступен (файл вне allowed roots). Вероятно — hydration предупреждение или Next.js dev notice. Требует уточнения.

---

## Spec measurements vs actual

| Параметр | Спека | Факт | Статус |
|---|---|---|---|
| Container max-width | 1240px | 1240px | ✅ |
| Container padding desktop | 32px | 24px (px-6) | ❌ -8px |
| Container padding mobile | 20px | не проверено | ? |
| Nav height | 72px | 73px | ✅ ~OK |
| Hero padding-top | 120px | 120px | ✅ |
| Hero padding-bottom | 80px | 80px | ✅ |
| Section padding desktop | 96/0 | 96/96 | ❌ нижний паддинг есть (не 0) |
| H1 font-size | clamp(44,6vw,80) | 74.4px @1240 | ✅ |
| H1 weight | 900 | 900 | ✅ |
| H1 letter-spacing | -0.03em | -2.232px ≈ -0.03em@74.4px | ✅ |
| FAQ first open | index 0 | aria-expanded=true | ✅ |
| Pricing brand scale | 1.03 | matrix(1.03…) | ✅ |
| Footer email | info@otklicker.ru | info@otklicker.ru | ✅ |

**Примечание по section padding**: спека говорит `96 0` (top/bottom), но это скорее всего означает `96px 0 padding` с `0` как горизонталь (а не вертикаль). Все секции имеют `padding: '96px 0'` = 96 top, 0 right/left, 96 bottom — это стандартная CSS shorthand. Фактически секции рендерятся с pt=96, pb=96. Скорее всего спека имеет в виду `padding: 96px 0` (убрать горизонтальные паддинги, оставить вертикальные). Реальный паддинг bottom тоже 96px — это нормально и соответствует ожидаемому виду.

---

## Сводный score

| Критерий | Score |
|---|---|
| Соответствие прототипу desktop | 8/10 |
| Соответствие прототипу mobile | 8/10 |
| Анимации | 6/10 |
| A11y фокус | 8/10 |
| **Total** | **7.5/10** |

---

## Action items до Phase 7 (блокеры)

- [ ] **MEDIUM** Добавить `@keyframes slideInFromRight` в globals.css и утилит-класс `.animate-slide-in-features { animation: slideInFromRight 0.5s cubic-bezier(.2,.8,.2,1); }` — без этого смена экрана в HowItWorks и Features происходит без анимации. `components/how-it-works.tsx`, `components/features.tsx`.
- [ ] **MEDIUM** Плейсхолдер-страницы /offer и /bot-privacy не используют общий Nav/Footer. Добавить хотя бы `<Nav />` в app/offer/page.tsx и app/bot-privacy/page.tsx через layout или напрямую.
- [ ] **MEDIUM** Уточнить и устранить console error/warning (1 error при навигации). Запустить `npm run build` для более чистого вывода.
- [ ] **LOW** Container padding: заменить `px-6` (24px) на `px-8` (32px) или добавить кастомный utility `px-container` = 32px desktop / 20px mobile. Файл: tailwind.config.ts + все компоненты с `.mx-auto.max-w-container.px-6`.

## Action items долгосрочно

- [ ] Inline `<style>` теги для медиазапросов внутри JSX (nav.tsx, hero.tsx, teaser-strip.tsx, features.tsx, pricing.tsx, how-it-works.tsx) — перенести в globals.css или Tailwind responsive классы для чистоты.
- [ ] FAQ: добавить анимацию высоты при открытии/закрытии (max-height transition или `<details>` native).
- [ ] CookieBanner: добавить `role="dialog"` aria-label="Уведомление о cookies" aria-live="polite".
- [ ] Footer: обернуть nav-колонки в `<nav aria-label="Ссылки сайта">`.
- [ ] SpeedSection: добавить `fontVariantNumeric: 'tabular-nums'` на числовые элементы таймлайна.
- [ ] Проверить RealBotScreen анимации (pulseRing, typingDots) отдельным pass.
- [ ] Гамбургер-меню для мобильного Nav — сейчас ссылки просто скрываются.
- [ ] /privacy и /cookies: добавить кнопку «← На главную» в начале страницы.
