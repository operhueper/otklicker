# откликер — памятка для Claude-сессий

## О проекте

Лендинг otklicker.ru для Telegram-бота [@otklicker_bot](https://t.me/otklicker_bot). Бот помогает соискателям получать приглашения с HH.ru: собирает резюме за 7-10 минут, авторизует через одноразовый код HH, скорит вакансии, откликается и отвечает HR в Telegram.

## Запуск 5 мая 2026 (waitlist 300/день)

Запускаемся волнами по 300 человек/день, активация в 10:00 МСК. До 5 мая waitlist выключен. Цель ~3000 юзеров за первую волну.

В текстах НИКОГДА: «попробуй прямо сейчас», «мгновенный доступ». Допустимо: «займи место», «ранний доступ», «открывается волнами».

Канал @otklicker ведёт founder, не Артём. У Артёма легенда HR-соискателя, не разработчика, голоса не путать.

Источник правды по очереди: задача в Notion «Очередь ранней волны (waitlist)». Мастер-документ запуска: `docs/LAUNCH_RUNBOOK.md`. Готовый контент: `marketing-engine/data/prewritten_posts.json`, `promo/content/articles/vc-launch-day.md`, `promo/artem/chats/launch-week-context.md`.

## Структура каталогов

```
site/             Next.js 14 App Router + TypeScript + Tailwind, static export
promo/            Промо: персона Артёма, контент-план, SEO
  artem/            persona.md, voice.md, chats/launch-week-context.md
  content/articles/ vc-launch-day.md и далее
  seo/              keywords.md, baseline-audit.md
legal/            Юридика сайта (SITE_PRIVACY_POLICY.md, COOKIE_POLICY.md)
deploy/           nginx-конфиг, GitHub Actions, security-чеклист
docs/             PRODUCT_FACTS.md, ARTEM_CHATS.md, LAUNCH_RUNBOOK.md, HANDOFF_NEXT_SESSION.md, USER_TODO.md
marketing-engine/ Python userbot (Telethon + Claude CLI). Локально активная разработка, прод на сервере
.planning/        architecture.md, component-map.md, brand-tokens.md, PLAN.md
```

## Чистка артефактов (важно)

При любом рефакторинге, миграции или переименовании сразу удалять старые версии. Не плодить параллельные папки и дубли документов в разных местах. Если файл переехал, старый сносим, не оставляем «на всякий случай». Бэкапы хранить вне репо (`~/Documents/otklicker-archive/`), не в коммитах.

## Источники правды

- Продукт, тарифы, фичи: `docs/PRODUCT_FACTS.md` (и серверный `data/product_knowledge.md`)
- Архитектура лендинга: `.planning/architecture.md`
- Дизайн-токены: `.planning/brand-tokens.md`
- Юридика сайта: `legal/SITE_PRIVACY_POLICY.md`, `legal/COOKIE_POLICY.md`
- Тарифы: `docs/PRODUCT_FACTS.md` §5 (Бесплатный 0 руб., Активный 790 руб. / 3 недели)

## Команды

```bash
cd site && npm run dev       # локальный сервер :3000
cd site && npm run build     # статическая сборка в site/out/
cd site && npx tsc --noEmit  # проверка типов
gh pr view                   # посмотреть открытый PR
```

## Стек

Next.js 14 App Router, TypeScript strict, Tailwind CSS, `output: 'export'` (статика). Деплой: GH Actions rsync на Hetzner, nginx, Let's Encrypt.

## Правила голоса бренда

- Конкретные цифры вместо "много" / "значительно"
- Короткие предложения, максимум 3 строки в абзаце
- Один восклицательный знак на сообщение, не больше
- От лица команды ("мы сделали")

## Запрещено везде

- Em-dash как знак препинания (допустим только в технических комментариях кода)
- Маркетинговые штампы: "уникальный", "инновационный", "не упустите", leverage, robust, seamless
- Обращения "Дорогие друзья", "коллеги"
- Bold abuse
- "Найдём работу мечты за 3 дня" и конкретные обещания сроков без фактической основы
- "100 откликов" и большие числа. Наш лимит 15 откликов в день, и это НЕ лимит HH. Это наш потолок, чтобы человек физически вытянул ответы работодателей, собеседования и переписки. Больше 15 один соискатель просто не обработает в день. У HH ограничения нет.
- Эмодзи в текстах персоны Артёма

## Безопасность

Никогда не коммитить `.env`, `*.session`, `*.session-journal`, `*.db` из marketing-engine/. Перед push: `find . -name ".env*" -not -path "*/node_modules/*"` должно быть пусто.

## Бренд

- Название: **откликер** (lowercase в UI и текстах)
- Бот: @otklicker_bot
- Канал: @otklicker
- Email: info@otklicker.ru
