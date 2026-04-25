# Что осталось сделать тебе руками — otklicker.ru

> Сайт live на https://otklicker.ru. Всё критичное закрыто. Ниже — действия, которые могу сделать только ты, с разной срочностью.

---

## Срочно (в течение суток)

### 1. Проверить почту info@otklicker.ru

MX-записи ещё пропагируются — Google уже видит новый SPF, но MX от ImprovMX могут идти 3-24 часа.

**Через 6-24 часа:**
1. Отправь себе тест: с другого ящика напиши на `info@otklicker.ru`
2. Через 30 секунд проверь свой Gmail
3. Если пришло — всё работает

**Если через 24 часа письмо не пришло:**
- Зайди в ImprovMX dashboard (https://improvmx.com/dashboard) — статус домена должен быть зелёный «Active»
- Зайди в Timeweb DNS-панель — проверь что MX записи именно `mx1.improvmx.com` (10) и `mx2.improvmx.com` (20), без `mx*.timeweb.ru`
- Проверь SPF: TXT на `@` должен быть `v=spf1 include:spf.improvmx.com ~all`
- Если всё OK — подожди ещё 12 часов, MX TTL у Timeweb могут быть до 86400

---

## В ближайшую неделю

### 2. Yandex.Metrica

Без счётчика ты не видишь ни одного посетителя.

1. Зайди на https://metrika.yandex.ru/list
2. «Добавить счётчик» → ввести `otklicker.ru` → название «Откликер лендинг»
3. Согласие на обработку данных, Webvisor включить
4. Получишь **Номер счётчика** (8-значное число)
5. Скинь его в новый чат с Claude — он вставит код на сайт и обновит CSP

### 3. Submit sitemap в поисковики

Чтобы появиться в Yandex и Google:

**Yandex.Webmaster:**
1. https://webmaster.yandex.ru → «Добавить сайт»
2. Подтвердить владение через DNS (TXT-запись) — добавь в Timeweb
3. После подтверждения: «Файлы Sitemap» → ввести `https://otklicker.ru/sitemap.xml`

**Google Search Console:**
1. https://search.google.com/search-console
2. «Добавить ресурс» → «URL-prefix» → `https://otklicker.ru/`
3. Подтвердить владение (HTML-файл, DNS, или meta-тег — выбери удобное)
4. «Файлы Sitemap» → ввести `sitemap.xml`

### 4. Проверить визуал в реальных браузерах

С твоего реального устройства (не моего скриншота playwright):

1. Открой https://otklicker.ru на десктопе и мобильном
2. Прогони все секции, кликни все CTA — все ведут в Telegram?
3. Cookie banner снизу? Кликни «Принять» — исчезает? Перезагрузи страницу — не появляется снова?
4. Проверь /privacy и /cookies — текст читабельный, не сломан?
5. Шарни ссылку на otklicker.ru в свой Telegram — превью с лого + заголовок появляется?

Если что-то не так — скриншот в новый чат с Claude.

---

## Когда будут свободные руки

### 5. Документы про бот (важно для соответствия закону)

Сейчас на сайте /offer и /bot-privacy — **placeholder-страницы** «Документ готовится». Это нормально для лендинга-визитки, но если кто-то реально оформит платёж и попросит оферту — у тебя её нет.

**Что сделать:**
1. **Договор-оферта** на платные услуги бота (`legal/BOT_OFFER_AGREEMENT.md`):
   - Описывает что включено в платный пакет (790 ₽ / 3 недели)
   - Условия возврата (14 дней, +48ч SLA если бот не прислал ни одной вакансии)
   - ЮKassa, чеки 54-ФЗ
   - Реквизиты ИП Энбом К.И. (уже есть в site privacy)
   - Можно либо нанять юриста (~5-15к ₽), либо в новой Claude-сессии сделать через `legal-compliance-checker` агент на Opus
   
2. **Политика обработки данных пользователей бота** (`legal/BOT_PRIVACY_POLICY.md`):
   - Что собирает бот: резюме, токены HH, переписка с HR
   - Где хранится, кому передаётся (HH.ru, ЮKassa)
   - Право на удаление
   - Также можно через legal-compliance-checker

После создания этих двух документов — Claude обновит /offer и /bot-privacy на реальный контент, добавит в sitemap, уберёт noindex.

### 6. SMTP relay для отправки КАК info@otklicker.ru (опционально)

Сейчас ты получаешь письма на info@ в Gmail, но отвечать можешь только с обычного gmail-адреса. Если важно отвечать с info@ (например для деловых контактов):

1. Регистрация на https://www.brevo.com (бывший Sendinblue) — free tier 300 писем/день
2. Получить SMTP credentials (server: smtp-relay.brevo.com, login, key)
3. Gmail → Настройки → Аккаунты и импорт → «Отправлять письма как» → добавить `info@otklicker.ru`:
   - SMTP сервер: `smtp-relay.brevo.com`
   - Порт: 587
   - Логин и пароль: из Brevo
4. Подтвердить адрес через тест-письмо
5. Теперь в Gmail можно выбирать «From: info@otklicker.ru» при ответе

### 7. HSTS preload submission (после 2-3 недель работы)

Сейчас в HSTS заголовке стоит `preload`, но в публичный hstspreload-список ты не подал.

После 2-3 недель уверенной работы HTTPS без проблем:
1. https://hstspreload.org/?domain=otklicker.ru
2. Проверка пройдёт, нажми Submit
3. Через 4-12 недель otklicker.ru попадёт в встроенный список Chrome/Firefox/Safari — браузеры будут принудительно использовать HTTPS даже до первого визита

**ВНИМАНИЕ:** после попадания в preload-список откатить HTTPS будет очень сложно (~2 года). Делай только когда уверен что сайт навсегда на HTTPS.

---

## Возможно (по желанию)

### 8. SSH hardening сервера

Сейчас на сервере `204.168.178.241`:
- `PasswordAuthentication=yes` (можно зайти паролем — security audit отметил как HIGH)
- `MaxAuthTries=6` (стандарт)
- fail2ban не установлен

Если хочешь закрыть: скажи новой Claude-сессии «сделай SSH hardening по deploy/security-checklist.md H-1/H-2». Это стандартный набор: password=no, fail2ban установить, MaxAuthTries=3.

**Риск:** если ты входишь по паролю где-то — сломается. Перед этим убедись что у тебя SSH ключ работает.

### 9. Соседние боты с публичным Postgres (security CRITICAL)

Security audit нашёл что **соседние** боты на сервере (не наш) имеют Postgres на `0.0.0.0:5432-5437` через Docker bypass UFW. Это shared-host risk: хотя otklicker лендинг сам по себе изолирован, если соседний бот будет взломан через Postgres — могут пойти дальше по серверу.

Это не блокер для лендинга, но рекомендую:
1. Зайди на сервер: `ssh root@204.168.178.241`
2. `ss -tlnp | grep -E ":543[2-7]"` — посмотри что слушает
3. В docker-compose-файлах соответствующих ботов изменить `5432:5432` на `127.0.0.1:5432:5432`

Это отдельная задача, не про лендинг.

---

## Промт для следующего чата с Claude

Скопируй и вставь в новый чат:

```
Привет. Я продолжаю работу над лендингом otklicker.ru.

Прочти полностью файл /Users/evgeniy/projects/otklicker/docs/HANDOFF_NEXT_SESSION.md
— там полный контекст: что сделано, что в backlog, как работать.

Также прочти /Users/evgeniy/projects/otklicker/CLAUDE.md
— правила голоса бренда.

После этого спроси меня, чем сегодня занимаемся.
```

Этот же промт можно скинуть прямо ссылкой на эти файлы в репо:
- https://github.com/operhueper/otklicker/blob/main/docs/HANDOFF_NEXT_SESSION.md
- https://github.com/operhueper/otklicker/blob/main/CLAUDE.md

---

## Ссылки (важные)

- 🌐 https://otklicker.ru
- 📦 https://github.com/operhueper/otklicker
- 🤖 https://t.me/otklicker_bot
- 📺 https://t.me/otklicker
- 🛠️ ImprovMX: https://improvmx.com/dashboard
- 📊 Метрика (когда подключишь): https://metrika.yandex.ru
- 🔍 Yandex.Webmaster: https://webmaster.yandex.ru
- 🔍 Google Search Console: https://search.google.com/search-console
- 📜 Hetzner: https://console.hetzner.cloud (если нужно проверить сервер)
- 📨 Timeweb DNS-панель: https://timeweb.com (домен `otklicker.ru` → DNS-записи)
