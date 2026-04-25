# Phase 7 Runbook — DNS switchover + SSL + Yandex Mail

Дата: 2026-04-25  
Цель: переключить `otklicker.ru` с Timeweb-хостинга на Hetzner-сервер `204.168.178.241`, выпустить SSL через Let's Encrypt, подключить Yandex 360 для `info@otklicker.ru`.

## Текущее состояние

- Лендинг работает на сервере по IP, отдаётся nginx (HTTP-only bootstrap config)
- `https://otklicker.ru` пока не работает — DNS указывает на старый Timeweb-хостинг
- GH Actions деплой работает: push в main → rsync → live за 1-2 мин
- Certbot 2.9.0 установлен на сервере, готов к запуску
- Все блокеры из Phase 6 ревью закрыты (контраст CTA, reduced-motion, aria-live, manifest paths, timer cleanup)

## Два независимых трека

Можно делать параллельно. Я рекомендую начать с **Track A** (быстрее увидеть результат).

---

## Track A — DNS переключение + SSL (15-30 мин)

### Шаг A.1 — Поменять A/AAAA в Timeweb DNS (ручная)

Зайти в Timeweb-панель → DNS-записи `otklicker.ru` → редактировать:

| Запись | Старое значение | Новое значение | TTL |
|---|---|---|---|
| `A @` | `92.53.96.223` | **`204.168.178.241`** | 600 |
| `A www` | `92.53.96.223` | **`204.168.178.241`** | 600 |
| `AAAA @` | `2a03:6f00:1::5c35:60df` | **`2a01:4f9:c014:38bd::1`** | 600 |
| `AAAA www` | `2a03:6f00:1::5c35:60df` | **`2a01:4f9:c014:38bd::1`** | 600 |

**НЕ ТРОГАТЬ:**
- MX-записи (`mx1.timeweb.ru`, `mx2.timeweb.ru`) — пока оставить, в Track B заменим на Yandex
- SPF / TXT записи рабочей почты
- CNAME (если есть)

### Шаг A.2 — Дождаться пропагации DNS (5-15 мин)

Проверка с локальной машины:
```bash
dig +short otklicker.ru @8.8.8.8
dig +short otklicker.ru @1.1.1.1
dig +short otklicker.ru AAAA @8.8.8.8
```

Должно вернуть `204.168.178.241` и `2a01:4f9:c014:38bd::1`. Если возвращает старый IP — подождать ещё 5-10 минут.

### Шаг A.3 — Запустить certbot на сервере (агент или вручную)

После того как DNS зарезолвился на новый IP:

```bash
ssh root@204.168.178.241

# на сервере
certbot --nginx \
  -d otklicker.ru \
  -d www.otklicker.ru \
  -m info@otklicker.ru \
  --agree-tos \
  --non-interactive \
  --redirect
```

Certbot:
1. Поднимет http-01 challenge через nginx
2. Получит сертификат от Let's Encrypt
3. Авторазвернёт SSL в `/etc/nginx/sites-available/otklicker.ru` (наш http-only конфиг)
4. Добавит HTTP→HTTPS редирект (флаг `--redirect`)

### Шаг A.4 — Заменить http-only конфиг на полный production

Текущий конфиг на сервере — bootstrap (без security headers, без CSP, без кеширования).

```bash
# скопировать полный prod-конфиг с локальной машины
scp /Users/evgeniy/projects/otklicker/deploy/nginx/otklicker.ru.conf \
  root@204.168.178.241:/etc/nginx/sites-available/otklicker.ru.full

# на сервере: после certbot, файл sites-available/otklicker.ru уже модифицирован.
# Берём полный конфиг и применяем поверх (cert paths certbot подставит сам при следующем запуске)
ssh root@204.168.178.241 "
  cp /etc/nginx/sites-available/otklicker.ru /etc/nginx/sites-available/otklicker.ru.bak-$(date +%Y%m%d-%H%M%S)
  cp /etc/nginx/sites-available/otklicker.ru.full /etc/nginx/sites-available/otklicker.ru
  certbot install --nginx -d otklicker.ru -d www.otklicker.ru
  nginx -t && systemctl reload nginx
"
```

### Шаг A.5 — Включить HSTS

После того как `certbot renew --dry-run` зелёный — раскомментить HSTS строку в конфиге:

```nginx
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

```bash
ssh root@204.168.178.241 "
  sed -i 's|# add_header Strict-Transport|add_header Strict-Transport|' /etc/nginx/sites-available/otklicker.ru
  nginx -t && systemctl reload nginx
"
```

Не включать HSTS preload до того как сайт публично проверен (после этого откатить sub-domain HSTS невозможно ~2 года).

### Шаг A.6 — Проверка HTTPS

```bash
curl -fsSL https://otklicker.ru/ | head -20  # должно вернуть HTML
curl -fsSL https://otklicker.ru/robots.txt
curl -fsSL https://otklicker.ru/sitemap.xml
curl -I https://otklicker.ru/  # должно показать security headers, HSTS, server: nginx
curl -I http://otklicker.ru/  # должно вернуть 301 → https
curl -I https://www.otklicker.ru/  # должно вернуть 301 → https://otklicker.ru
```

### Шаг A.7 — `certbot renew --dry-run`

```bash
ssh root@204.168.178.241 "certbot renew --dry-run && systemctl status certbot.timer | head -5"
```

Если зелёный — auto-renew работает (раз в 12 часов проверка, обновление за 30 дней до истечения).

---

## Track B — ImprovMX форвард `info@otklicker.ru` → личный Gmail

Цель: входящие письма на `info@otklicker.ru` приходят в личный Gmail пользователя. Никакого webmail, никакого нового inbox — просто форвард.

### Шаг B.1 — Регистрация в ImprovMX (~2 мин)

1. Открыть **https://improvmx.com**
2. Sign up (или Login через Google — удобно если хочешь связать сразу с тем же Gmail)
3. После входа: «Add domain» → ввести `otklicker.ru`

ImprovMX покажет 2 MX-записи и SPF — их нужно прописать в Timeweb DNS (шаг B.2).

### Шаг B.2 — Добавить MX и SPF в Timeweb DNS

В Timeweb-панели → DNS-записи `otklicker.ru`:

**Удалить старые MX:**
| Запись | Старое значение | Действие |
|---|---|---|
| `MX @` | `mx1.timeweb.ru` priority 10 | удалить |
| `MX @` | `mx2.timeweb.ru` priority 20 | удалить |

**Добавить новые MX:**
| Запись | Имя | Значение | Priority | TTL |
|---|---|---|---|---|
| `MX` | `@` | `mx1.improvmx.com` | 10 | 3600 |
| `MX` | `@` | `mx2.improvmx.com` | 20 | 3600 |

**SPF (TXT):** если уже есть SPF на `@` (что-то вроде `v=spf1 include:spf.timeweb.ru ~all`) — заменить:

| Запись | Имя | Значение | TTL |
|---|---|---|---|
| `TXT` | `@` | `v=spf1 include:spf.improvmx.com ~all` | 3600 |

Если SPF не было — добавить ту же строку.

DKIM в free tier ImprovMX **не требуется** — они подписывают исходящие через свой домен. Это нормально для форварда (входящие проходят оригинальную DKIM-проверку через ImprovMX как relay).

### Шаг B.3 — Подождать пропагацию (5-15 мин)

Проверка:
```bash
dig +short otklicker.ru MX @8.8.8.8
```

Должно вернуть `mx1.improvmx.com.` и `mx2.improvmx.com.`. В ImprovMX-дашборде статус «Active» / зелёная галочка.

### Шаг B.4 — Настроить alias в ImprovMX

В ImprovMX dashboard → твой домен → «Aliases» → «Add alias»:

| Field | Value |
|---|---|
| Alias | `info` |
| Forward to | `твой-личный@gmail.com` |

Можно добавить catch-all: алиас `*` → твой Gmail (тогда `support@`, `hr@`, что угодно тоже придёт).

### Шаг B.5 — Тест

С другого ящика отправь письмо на `info@otklicker.ru`. Через 5-30 секунд должно прийти в твой личный Gmail (с пометкой "via improvmx" в заголовках, в Gmail UI просто появится).

Проверка через **https://www.mail-tester.com/**: отправляешь туда письмо, видишь spam-score. Должно быть 8-10/10 если MX и SPF настроены правильно.

### Шаг B.6 (опционально) — Отправлять КАК `info@otklicker.ru` из Gmail

ImprovMX free tier не даёт SMTP-relay для исходящих. Если хочешь писать ИЗ `info@otklicker.ru` (а не просто отвечать с обычного Gmail) — нужен внешний SMTP. Бесплатные варианты:

- **Brevo (бывший Sendinblue)** — 300 писем/день бесплатно. SMTP credentials → в Gmail "Settings → Accounts → Send mail as". Минут 15 настройки.
- **Mailjet free tier** — 200/день
- **SendGrid free tier** — 100/день

Эта настройка опциональна и не блокирует приёмку лендинга. Без неё ты просто отвечаешь с обычного Gmail-адреса. Для legal-уведомлений и certbot-renew достаточно входящих.

---

## После завершения Track A и Track B

### Финальный verifier (Phase 7.x)

Запустить `verifier`-агента или сделать вручную:

```bash
# 1. SSL valid
curl -I https://otklicker.ru/ 2>&1 | grep -i 'strict-transport\|server:'
echo | openssl s_client -connect otklicker.ru:443 -servername otklicker.ru 2>/dev/null | openssl x509 -noout -dates

# 2. www → apex redirect
curl -I https://www.otklicker.ru/ 2>&1 | grep -i location

# 3. http → https redirect
curl -I http://otklicker.ru/ 2>&1 | grep -i location

# 4. Все основные страницы
for path in / /privacy /cookies /offer /bot-privacy; do
  curl -fsI "https://otklicker.ru$path" | head -2
done

# 5. SEO assets
curl -fsSL https://otklicker.ru/robots.txt
curl -fsSL https://otklicker.ru/sitemap.xml
curl -fsI https://otklicker.ru/opengraph-image
curl -fsI https://otklicker.ru/icon

# 6. Lighthouse (через Chrome или web.dev)
# https://pagespeed.web.dev/?url=https%3A%2F%2Fotklicker.ru

# 7. SSL Labs
# https://www.ssllabs.com/ssltest/analyze.html?d=otklicker.ru

# 8. Mozilla Observatory
# https://observatory.mozilla.org/analyze/otklicker.ru
```

### Чеклист приёмки (16 пунктов из HANDOFF_PROMPT.md)

- [ ] `https://otklicker.ru` валидный SSL
- [ ] `www → apex` 301
- [ ] `http → https` 301
- [ ] Все секции лендинга визуально совпадают с прототипом
- [ ] CTA ведут на `https://t.me/otklicker_bot` и `https://t.me/otklicker`
- [ ] Cookie banner функционирует
- [ ] `/privacy`, `/cookies` с реальным контентом
- [ ] `/offer`, `/bot-privacy` placeholder
- [ ] `robots.txt`, `sitemap.xml` валидны
- [ ] OG-картинка показывается при шаринге в Telegram
- [ ] Lighthouse ≥ 90
- [ ] GH Actions деплой работает
- [ ] TLS auto-renew (`certbot renew --dry-run` зелёный)
- [ ] Все артефакты ревью в `.planning/`
- [ ] `README.md` с инструкцией
- [ ] `CLAUDE.md` для будущих сессий
