# откликер — памятка для Claude-сессий

## О проекте

Лендинг otklicker.ru для Telegram-бота [@otklicker_bot](https://t.me/otklicker_bot). Бот помогает соискателям получать приглашения с HH.ru: собирает резюме за 7-10 минут, авторизует через одноразовый код HH, скорит вакансии, откликается и отвечает HR в Telegram.

## Структура каталогов

```
site/            Next.js 14 App Router + TypeScript + Tailwind, static export
promo/           Промо-материалы (персона, посты, SEO)
legal/           Юридика (SITE_PRIVACY_POLICY.md, COOKIE_POLICY.md, placeholders)
deploy/          nginx-конфиг, GitHub Actions, security-чеклист
docs/            PRODUCT_FACTS.md, ARTEM_CHATS.md
marketing-engine/ Python userbot (Telethon + Claude CLI) — автономный проект
.planning/       architecture.md, component-map.md, brand-tokens.md, PLAN.md
```

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
- "100 откликов" и большие числа (лимит HH: 15 в день)
- Эмодзи в текстах персоны Артёма

## Безопасность

Никогда не коммитить `.env`, `*.session`, `*.session-journal`, `*.db` из marketing-engine/. Перед push: `find . -name ".env*" -not -path "*/node_modules/*"` должно быть пусто.

## Бренд

- Название: **откликер** (lowercase в UI и текстах)
- Бот: @otklicker_bot
- Канал: @otklicker
- Email: info@otklicker.ru
