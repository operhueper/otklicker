# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## О проекте

Лендинг otklicker.ru для Telegram-бота [@otklicker_bot](https://t.me/otklicker_bot). Бот помогает соискателям получать приглашения с HH.ru: собирает резюме за 7-10 минут, авторизует через одноразовый код HH, скорит вакансии, откликается и отвечает HR в Telegram.

Сам бот живёт на сервере (см. ниже). В этом репо — только лендинг + промо-материалы + локальное зеркало `marketing-engine/` (HR-промо userbot Артём).

## Запуск 5 мая 2026 (первая волна 500, дальше 300/день)

5 мая 2026 в 10:00 МСК открываем первую волну на 500 мест. Дальше ежедневная квота 300 пользователей. Цель ~3000 юзеров за первые 7-10 дней. До 5 мая waitlist выключен.

В текстах НИКОГДА: «попробуй прямо сейчас», «мгновенный доступ». Допустимо: «займи место», «ранний доступ», «открывается волнами».

Канал @otklicker ведёт founder, не Артём. У Артёма легенда HR-соискателя, не разработчика, голоса не путать.

Источник правды по очереди: задача в Notion «Очередь ранней волны (waitlist)». Мастер-документ запуска: `docs/LAUNCH_RUNBOOK.md`. Готовый контент: `marketing-engine/data/prewritten_posts.json`, `promo/content/articles/vc-launch-day.md`, `promo/artem/chats/launch-week-context.md`.

## Архитектура лендинга

Next.js 14 App Router + TypeScript strict + Tailwind, статическая сборка через `output: 'export'` (см. `site/next.config.mjs`). Главная — единая страница из секций, объявленная в `site/app/page.tsx`.

**Layout страницы (порядок секций):**
`Nav → Hero(variant="chat") → CoverLetter → HHvsOtklicker → Features → Pricing → FAQ → FinalCTA → Footer + CookieBanner`. Каждая секция — отдельный компонент в `site/components/*.tsx`.

**Контент-модель:** все тексты вынесены в `site/lib/data/*.ts` (faq, features, hero-jobs, pricing, sample-jobs, hh-vs-otklicker, nav). Типы — в `site/lib/types/*.ts`, реэкспорт через `site/lib/types/index.ts`. Чтобы поправить текст секции, ищи в `lib/data/`, не в компоненте.

**Эмуляция бота на лендинге:** «скриншоты» Telegram-бота не картинки, а HTML. Декларативные данные в `site/lib/screens/bot-screens.ts`, рендерит компонент `site/components/real-bot-screen.tsx`. Используется в Hero(chat), Features, CoverLetter.

**SEO/мета:** metadata в `site/app/layout.tsx` (общая) и `site/app/page.tsx` (главная + JSON-LD SoftwareApplication с реквизитами ИП). `robots.ts` и `sitemap.ts` рядом. OG-image генерируется через `site/app/opengraph-image.tsx` (`next/og`). Favicon-set через `app/icon.tsx` + `app/apple-icon.tsx`.

**Аналитика:** Yandex.Metrica подключается через `NEXT_PUBLIC_YANDEX_METRICA_ID` в `site/app/layout.tsx`. Если переменной нет, скрипт не рендерится (локальная разработка).

**Юридика:** `legal/SITE_PRIVACY_POLICY.md` и `legal/COOKIE_POLICY.md` рендерятся через `react-markdown` на `/privacy` и `/cookies`. `/offer` и `/bot-privacy` — placeholder-страницы (юридика бота ещё не написана).

**Стили:** Tailwind с кастомными токенами в `site/app/globals.css` и `tailwind.config.ts`. Большинство компонентов используют `style={{}}` inline + утилиты `mx-auto max-w-container px-6` + CSS-переменные `var(--brand-gradient)`, `var(--text-heading)`, `var(--bg-pastel)`, `var(--bg-dark)`. Это унаследовано из JSX-прототипа, миграция на чистый Tailwind в бэклоге.

## Деплой

Push в `main` → GitHub Actions (`.github/workflows/deploy.yml`) собирает `site/`, rsync статики `out/` в `/var/www/otklicker.ru/` на Hetzner CAX21 ARM (Helsinki, IP `204.168.178.241`). nginx раздаёт, Let's Encrypt (`certbot.timer`) обновляет SSL. ~2 минуты от push до live.

CI на PR: `.github/workflows/ci.yml`.

Доступ к серверу: `ssh root@204.168.178.241`. На сервере есть соседние проекты (fitcoach-bot, tg-automations и др.) — не трогать. Конфиг nginx: `/etc/nginx/sites-available/otklicker.ru`, исходник в репо `deploy/nginx/otklicker.ru.conf`.

## Структура каталогов

```
site/             Next.js 14 App Router, лендинг
  app/              маршруты (page, layout, privacy, cookies, offer, bot-privacy, sitemap, robots, opengraph-image)
  components/       секции лендинга и UI
  lib/data/         тексты секций (faq, features, pricing, hh-vs-otklicker, ...)
  lib/types/        TS-типы для контент-моделей
  lib/screens/      bot-screens.ts (HTML-эмуляция Telegram-бота)
promo/            Промо: персона Артёма, контент-план запуска, SEO
  artem/            persona.md, voice.md, chats/launch-week-context.md
  content/articles/ vc-launch-day.md и далее
  seo/              keywords.md, baseline-audit.md
legal/            Юридика сайта (SITE_PRIVACY_POLICY.md, COOKIE_POLICY.md)
deploy/           nginx-конфиг, deploy-скрипты, security-чеклист
docs/             PRODUCT_FACTS.md, ARTEM_CHATS.md, LAUNCH_RUNBOOK.md, HANDOFF_NEXT_SESSION.md, USER_TODO.md
marketing-engine/ Python userbot (Telethon + Claude CLI). Локально активная разработка, прод на сервере
.planning/        architecture.md, component-map.md, brand-tokens.md, PLAN.md, ревью-артефакты
brandbook.pen     Бренд-токены (читать ТОЛЬКО через mcp__pencil__*, не Read/Grep)
```

## Команды

```bash
cd site && npm run dev       # локальный сервер :3000
cd site && npm run build     # статическая сборка в site/out/
cd site && npm run lint      # ESLint (next lint), должен быть clean
cd site && npx tsc --noEmit  # проверка типов

gh pr view                   # посмотреть открытый PR
ssh root@204.168.178.241     # прод-сервер
```

Перед push в main: `tsc --noEmit` зелёный, `npm run build` зелёный, `npm run lint` без warning'ов на твои файлы.

## Чистка артефактов (важно)

При любом рефакторинге, миграции или переименовании сразу удалять старые версии. Не плодить параллельные папки и дубли документов в разных местах. Если файл переехал, старый сносим, не оставляем «на всякий случай». Бэкапы хранить вне репо (`~/Documents/otklicker-archive/`), не в коммитах.

## Источники правды

- Продукт, тарифы, фичи: `docs/PRODUCT_FACTS.md` (и серверный `data/product_knowledge.md`)
- Архитектура лендинга: `.planning/architecture.md`
- Дизайн-токены: `.planning/brand-tokens.md`
- Юридика сайта: `legal/SITE_PRIVACY_POLICY.md`, `legal/COOKIE_POLICY.md`
- Тарифы: `docs/PRODUCT_FACTS.md` §5 (Бесплатный 0 руб., Активный 790 руб. / 3 недели)

## Стек

Next.js 14 App Router, TypeScript strict, Tailwind CSS, `output: 'export'` (статика). Иконки `lucide-react`. Markdown через `react-markdown` + `remark-gfm`. Деплой: GH Actions rsync на Hetzner, nginx, Let's Encrypt.

## Правила голоса бренда

- Конкретные цифры вместо "много" / "значительно"
- Короткие предложения, максимум 3 строки в абзаце
- Один восклицательный знак на сообщение, не больше
- От лица команды ("мы сделали")

## Запрещено везде

- Em-dash как знак препинания (допустим только в технических комментариях кода). На сайте максимум 1–2 em-dash на весь лендинг, и то только в очень редких технических ситуациях. Это AI-клише, избегай.
- Маркетинговые штампы: "уникальный", "инновационный", "не упустите", leverage, robust, seamless
- Обращения "Дорогие друзья", "коллеги"
- Bold abuse
- "Найдём работу мечты за 3 дня" и конкретные обещания сроков без фактической основы
- "100 откликов" и большие числа. Наш лимит 15 откликов в день, и это НЕ лимит HH. Это наш потолок, чтобы человек физически вытянул ответы работодателей, собеседования и переписки. Больше 15 один соискатель просто не обработает в день. У HH ограничения нет.
- Эмодзи в текстах персоны Артёма
- Чтение `brandbook.pen` через Read/Grep. Только `mcp__pencil__*`.

## Безопасность

Никогда не коммитить `.env`, `*.session`, `*.session-journal`, `*.db` из marketing-engine/. Перед push: `find . -name ".env*" -not -path "*/node_modules/*" -not -path "./.git/*"` должно быть пусто (кроме `.env.example`).

Рискованные действия (DNS, SSH-конфиг сервера, force-push, удаление файлов, чужие проекты на сервере) — спросить пользователя.

## Бренд

- Название: **откликер** (lowercase в UI и текстах)
- Бот: @otklicker_bot
- Канал: @otklicker
- Email: info@otklicker.ru
- ИП Энбом К.И., ОГРНИП 324632700187012
