# откликер — лендинг otklicker.ru

Telegram-бот [@otklicker_bot](https://t.me/otklicker_bot), который собирает резюме за 7-10 минут, авторизует в HH.ru без пароля и откликается на свежие вакансии за пользователя. Бот скорит вакансии по 5 факторам, генерирует персональные сопроводительные и отвечает HR прямо в Telegram.

## Запуск локально

```bash
cd site
npm install
npm run dev
# Открыть http://localhost:3000
```

Сборка статики:

```bash
cd site
npm run build
# Статика появится в site/out/
```

## Структура репозитория

```
site/             Next.js 14 App Router, TypeScript, Tailwind. Исходник лендинга.
promo/            Промо: персона Артёма, контент-план запуска, SEO.
legal/            Юридика сайта: SITE_PRIVACY_POLICY.md, COOKIE_POLICY.md.
deploy/           nginx-конфиг, deploy-скрипты, security-чеклист.
docs/             Продуктовая документация, runbook запуска, хэндоффы.
marketing-engine/ Python-движок для промо в HR-чатах (Telethon userbot + Claude CLI).
.planning/        Архитектурные документы, планы фаз, ревью-артефакты.
.github/          GitHub Actions workflows: CI (PR) и deploy (push в main).
```

## Запуск 5 мая 2026

Запускаемся ранним доступом по 300 человек/день, активация в 10:00 МСК. Цель ~3000 юзеров за первую волну.
Мастер-чеклист: [`docs/LAUNCH_RUNBOOK.md`](docs/LAUNCH_RUNBOOK.md).
Готовый контент: 7 постов канала в `marketing-engine/data/prewritten_posts.json`, статья VC.ru в `promo/content/articles/vc-launch-day.md`, контекст Артёма в `promo/artem/chats/launch-week-context.md`.

## Деплой

На каждый push в `main` GitHub Actions запускает сборку `site/` и rsync доставляет `out/` на сервер Hetzner (204.168.178.241) в `/var/www/otklicker.ru/`. Nginx раздаёт статику. SSL через Let's Encrypt + certbot.timer.

Ручной деплой: `ssh root@204.168.178.241 "ls /var/www/otklicker.ru/"`.

## Зависимости

- Node v22+, npm 10+
- Python 3.12 (только для marketing-engine на сервере)
- gh CLI для работы с GitHub Actions и PR
