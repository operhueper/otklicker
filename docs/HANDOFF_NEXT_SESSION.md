# Хэндофф для следующей Claude-сессии — otklicker.ru

> **Скопируй этот файл целиком в новый чат с Claude Code.** Это вводный контекст: что сделано, что в работе, что в бэклоге, как продолжать.

---

## Кто ты

Ты продолжаешь работу над лендингом **otklicker.ru** — сайтом для Telegram-бота `@otklicker_bot` (автоотклики на HH.ru). Запущен в production 25 апреля 2026 предыдущей сессией. Twoя задача — закрыть бэклог (a11y/code MEDIUM, контент про бот, аналитика) и помогать пользователю с эволюцией продукта.

## Стек одной строкой

Next.js 14 App Router + TypeScript strict + Tailwind, static export → nginx на Hetzner CAX21 ARM (Helsinki), Let's Encrypt SSL, GH Actions push→deploy, ImprovMX→Gmail для info@otklicker.ru.

## Где живёт код

- Локальный репо: `/Users/evgeniy/projects/otklicker/`
- GitHub: https://github.com/operhueper/otklicker (private)
- Production: https://otklicker.ru
- Старый рабочий проект (только промо/marketing-engine): `/Users/evgeniy/projects/otklicker-promo/`

## Сервер

- IP: `204.168.178.241` (IPv6 `2a01:4f9:c014:38bd::1`)
- SSH: `ssh root@204.168.178.241` (стандартный ключ пользователя работает)
- Локация: Helsinki (hel1), Hetzner CAX21, ARM aarch64, Ubuntu 24.04
- Что стоит: nginx 1.24, certbot 2.9.0, GH Actions deploy user (через ключ `~/.ssh/otklicker_gh_actions`)
- Лендинг: `/var/www/otklicker.ru/` (наполняется rsync'ом из CI)
- Конфиг: `/etc/nginx/sites-available/otklicker.ru` (и `.full` бэкап, исходник в репо `deploy/nginx/otklicker.ru.conf`)
- На сервере есть ещё проекты (`fitcoach-bot`, `exercise-review`, `tg-automations`, `containerd`, `tg-bots`) — **НЕ ТРОГАТЬ**, не наш лендинг

## Что уже готово (не трогать без необходимости)

- ✅ Все 9 секций лендинга мигрированы из JSX-прототипа в `site/components/*.tsx`
- ✅ 5 экранов бота в `site/lib/screens/bot-screens.ts`
- ✅ Тарифы (`site/lib/data/pricing.ts`) синхронизированы с `docs/PRODUCT_FACTS.md`
- ✅ Site Privacy Policy (`legal/SITE_PRIVACY_POLICY.md` → `/privacy`)
- ✅ Cookie Policy (`legal/COOKIE_POLICY.md` → `/cookies`)
- ✅ Placeholder /offer и /bot-privacy (ждут содержимого)
- ✅ SEO: metadata, robots.txt, sitemap.xml (3 URL: /, /privacy, /cookies), JSON-LD SoftwareApplication
- ✅ OG-image 1200×630 через `next/og`, favicon-set
- ✅ HTTPS, HSTS 2y preload, security headers, ужесточённый CSP (без Yandex.Metrica)
- ✅ certbot auto-renew (certbot.timer active)
- ✅ GH Actions: push в main → ~2 мин live
- ✅ ImprovMX MX/SPF в Timeweb DNS (info@otklicker.ru → личный Gmail пользователя)

## Источники правды

| Что | Где |
|---|---|
| Продуктовая фактура (тарифы, фичи) | `docs/PRODUCT_FACTS.md` |
| Голос бренда, запреты | `CLAUDE.md` в корне репо |
| Архитектура (TS-типы, токены) | `.planning/architecture.md` |
| Карта компонентов прототипа | `.planning/component-map.md` |
| Бренд-токены | `.planning/brand-tokens.md` |
| План по фазам (исторический) | `.planning/PLAN.md` |
| Code review | `.planning/REVIEW.md` |
| Visual review | `.planning/visual-review.md` |
| A11y review | `.planning/a11y-review.md` |
| Security audit | `deploy/security-checklist.md` |
| Phase 7 runbook | `.planning/PHASE7_RUNBOOK.md` |
| Скриншоты на 4 брейкпоинтах | `.planning/screenshots/` |
| Реквизиты ИП в legal-документах | ИП Энбом К.И., ОГРНИП 324632700187012 |

## Обязательные правила (НЕ нарушать)

1. **Голос бренда** (`CLAUDE.md`): без em-dash как пунктуация, без «уникальный», «инновационный», «не упустите», «leverage», «robust», «seamless», без эмодзи в текстах персоны, без «работа за 3 дня», без «100 откликов» (лимит HH = 15)
2. **Бренд «откликер» строго lowercase** в текстах (только в начале предложения с заглавной)
3. **Конкретные цифры** вместо «много» / «значительно»
4. **Reverify before claim done**: `npm run build` зелёный, `npx tsc --noEmit` чистый, `npx next lint` без warnings
5. **НЕ копировать** `.env*` или `.session*` файлы из marketing-engine в коммиты
6. **Brandbook.pen — только через `mcp__pencil__*`**, никогда Read/Grep
7. **Атомарные conventional commits** (`feat:`, `fix:`, `chore:`, `docs:`, `ci:`, `style:`)
8. **Рискованные действия — спросить у пользователя**: DNS, SSH-конфиг сервера, force-push, удаление файлов, чужие проекты на сервере
9. **Email унифицирован** на `info@otklicker.ru` (НЕ `hi@otklicker.app`)

## Окружение и инструменты

- Node 22.14, npm 10.9.2 (локально)
- gh CLI авторизован под `operhueper`
- GH Secrets уже настроены: `DEPLOY_SSH_KEY`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PATH`
- MCP: pencil (для brandbook.pen), playwright (для дизайн/a11y проверок), hetzner (для server CRUD при необходимости)

## Bekлог приоритезированный

### Wave A — Высокий приоритет (закрыть в ближайшую неделю)

**A11y MEDIUM:**
- Skip-to-content link в Nav (для screen-reader)
- `role="region"` + `aria-label` на CookieBanner
- Footer link columns обернуть в семантический `<nav>` + `<ul><li>`
- Keyboard arrow navigation для tablist в Features (стрелки ←→ переключают табы)

**Brand voice:**
- M-10: tagline «найди работу мечты» в `components/brand.tsx:52` (BrandLockup) нарушает правило «не использовать придуманные слоганы». Заменить на нейтральный «Telegram-бот · HH.ru» или убрать совсем (согласовать с пользователем)

**Code MEDIUM:**
- M-1: заменить `dangerouslySetInnerHTML` в `components/hero-chat.tsx` на JSX (`<><b>{job.company}</b></>`)
- M-2: `lib/types/pricing.ts:6` — `id: 'free' | 'active' | string` → убрать `| string`
- M-3: `components/speed.tsx:165` — `kind: string` → `'bot' | 'manual'`

### Wave B — Средний приоритет

**Yandex.Metrica интеграция:**
1. Получить counter ID от пользователя
2. Подключить через `next/script` в `app/layout.tsx` (стратегия `afterInteractive`)
3. Учесть согласие через `localStorage.otklicker_cookie_consent === 'all'`
4. Открыть CSP обратно: добавить `mc.yandex.ru` в `script-src`, `connect-src`, `img-src`, `frame-src` в `deploy/nginx/otklicker.ru.conf`
5. Обновить Cookie Policy если нужно
6. Submit sitemap в Yandex.Webmaster + Google Search Console

**Документы про бот** (когда пользователь готов):
- `legal/BOT_OFFER_AGREEMENT.md` — договор-оферта на платные услуги бота. Обращайся к юристу или используй legal-compliance-checker (Opus). Реквизиты: ИП Энбом К.И., ОГРНИП 324632700187012
- `legal/BOT_PRIVACY_POLICY.md` — политика обработки данных пользователей бота (резюме, токены HH, переписка с HR). Это сложный документ, требует понимания того, что бот делает (см. `docs/PRODUCT_FACTS.md`)
- После создания: заменить placeholder в `app/offer/page.tsx` и `app/bot-privacy/page.tsx` на рендер MD (как сделано в `/privacy` и `/cookies`)
- Добавить /offer и /bot-privacy в `app/sitemap.ts` (раньше исключены из-за placeholder-статуса)
- Убрать noindex с этих страниц в их `metadata`

### Wave C — Долгосрочный backlog

**Code LOW/MEDIUM:**
- Inline styles → Tailwind classes (M-9 в REVIEW.md): большинство компонентов используют inline `style={{}}` вместо Tailwind classes. Унаследовано из прототипа. Долгая миграция, низкий приоритет.
- Convert `BOT_SCREENS` (`lib/screens/bot-screens.ts`) с HTML strings на ReactNode trees, чтобы убрать `dangerouslySetInnerHTML` в `RealBotScreen`
- Tighten composite key in HeroSwipe (M-6)
- Add `type="button"` всем кнопкам (L-2)
- L-4: `.prose-legal` неиспользуемый класс в globals.css — либо подключить, либо убрать
- L-6: `id="teaser-grid"` global ID в `components/teaser-strip.tsx` — заменить на class-scoped
- Базовый Playwright smoke-тест (homepage, все CTA, manifest icons 200)

**Server hardening (security audit findings — отдельно от сайта):**
- H-1 (security-checklist.md): SSH `PasswordAuthentication=no`, `MaxAuthTries=3`, `ClientAliveInterval=300` через `/etc/ssh/sshd_config.d/00-hardening.conf`
- H-2: `apt-get install fail2ban`
- C-1/C-2: соседние боты на сервере имеют публичный Postgres на 0.0.0.0:5432-5437 (Docker bypass UFW). Не наш проект, но shared-host risk. Согласовать с пользователем.

**SEO дальше:**
- HSTS preload submission на https://hstspreload.org/?domain=otklicker.ru (после 2-3 недель работы HSTS без проблем)
- Расширить ключевые слова в `promo/seo/keywords.md`
- Контент-план для блога: `promo/seo/content-plan.md`
- Первая статья vc.ru / Habr про откликер

**Маркетинг (HR-персона Артём):**
- `marketing-engine/` уже на сервере, работает в HR-чатах
- Если понадобится менять промпты — делать в `marketing-engine/src/content/prompts.py` на сервере, не в локальном репо
- Список HR-чатов: `data/hr_chats.json`

## Как работать

### Делегирование агентам

Прошлая сессия использовала OMC. Доступны:
- `executor` (Sonnet) — implementation
- `executor` с `model=opus` — сложная архитектура
- `code-reviewer` (Opus) — review
- `architect` (Opus) — system design
- `legal-compliance-checker` (Opus) — для bot privacy policy
- `Technical Writer` (Sonnet) — для bot offer
- `accessibility-auditor` (Sonnet) — a11y проверки
- `designer` (Sonnet) — visual review через playwright
- `security-engineer` (Opus) — server/infra audits

Делегируй когда задача multi-step. Простые правки в 1 файле — делай сам.

### Деплой

```bash
git push origin main  # → GH Actions → ~2 мин live
```

Откат:
```bash
git revert <sha>
git push origin main
```

### Локальная разработка

```bash
cd /Users/evgeniy/projects/otklicker/site
npm run dev       # http://localhost:3000
npm run build     # static export в out/
npx tsc --noEmit  # проверка типов
npx next lint     # ESLint (должен быть clean)
```

### Server access

```bash
ssh root@204.168.178.241
# конфиг nginx: /etc/nginx/sites-available/otklicker.ru
# логи: /var/log/nginx/otklicker.ru.{access,error}.log
# certbot: certbot renew --dry-run
```

## Стартовая инструкция

1. Прочти этот файл целиком
2. Прочти `CLAUDE.md` (правила голоса бренда)
3. Спроси пользователя что делаем сегодня. Возможные варианты:
   - Wave A item (a11y MEDIUM, brand voice tagline, code MEDIUM)
   - Подключение Yandex.Metrica (если ID получен)
   - Bot Offer / Bot Privacy Policy (если пользователь готов делать)
   - Контент для блога (статьи)
   - Что-то новое, не из бэклога
4. Если задача big — делегируй executor агенту с подробным промптом
5. После — `npm run build`, push, проверка production через curl

Удачи. Сайт уже live, никаких героических усилий — методично закрывай бэклог.
