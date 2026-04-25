# Security audit — otklicker.ru — 2026-04-25 (Phase 5c)

Аудитор: security-engineer (Opus 4.7)
Скоуп: production nginx config, HTTP-only bootstrap config, GH Actions workflows, SSH-конфиг сервера, network exposure, live HTTP-headers
Версия: до certbot (HTTPS ещё не активирован, DNS otklicker.ru → 92.53.96.223 Timeweb, целевой сервер 204.168.178.241)
Метод: read-only inspection статичных конфигов + read-only SSH к серверу (sshd_config, ufw, ss, iptables, docker ps, nginx -T)

## Severity scale
- **CRITICAL** — exploit или массовая утечка секретов (немедленно)
- **HIGH** — серьёзная уязвимость, нужно фиксить до публичного запуска
- **MEDIUM** — best practice violation, фиксить в течение недели
- **LOW** — hardening, nice-to-have
- **INFO** — observation, не уязвимость

---

## Findings

### CRITICAL

#### C-1. Postgres-инстансы соседних ботов выставлены в публичный интернет
- **Где:** сервер 204.168.178.241, докер-проксирует наружу `0.0.0.0:5432`, `0.0.0.0:5434`, `0.0.0.0:5435`, `0.0.0.0:5436`, `0.0.0.0:5437` (контейнеры `hh-bot-postgres-1`, `dream-job-bot-db-1`, `lifepilot-bot-db-1`, `voicebridge-ai-db-1` и др.)
- **Почему плохо:** UFW настроен корректно (`22/80/443` only), но Docker через `iptables -t nat DOCKER` chain делает DNAT в обход UFW INPUT — это известный footgun docker+ufw. Любой в интернете может коннектиться к Postgres и брутить пароль. Утечка БД любого из этих ботов = инцидент. Для otklicker это reputational risk (общий хост).
- **Исправление:** в `docker-compose.yml` каждого затронутого бота сменить `ports: ["5432:5432"]` на `ports: ["127.0.0.1:5432:5432"]` (бинд только на loopback). Альтернатива — пакет `ufw-docker` или правило `DOCKER-USER` chain дропающее извне всё кроме whitelist.
- **Не блокирует Phase 7 для otklicker лендинга**, но критично для ext-окружения.

#### C-2. Дополнительные docker-сервисы наружу на 8080/8081/8082/8085/8443/3100
- **Где:** lifepilot-bot (8080, 8443), hh-bot (8081), dream-job-bot-dashboard (8082), voicebridge-ai-bot (8085), dream-job-bot-proxy (3100)
- **Почему плохо:** admin-панели и нестандартные сервисы без TLS и без auth-прокси. Аналогично C-1 — bypass UFW через docker DNAT.
- **Исправление:** все админ-сервисы — за nginx-reverse-proxy на 443 с basic-auth/oauth-proxy и bind на `127.0.0.1` в compose. Если сервис нужен публично — обернуть в TLS и rate-limit.

### HIGH

#### H-1. SSH разрешает root-логин по паролю по дефолту (sshd_config)
- **Где:** `/etc/ssh/sshd_config`: все ключевые директивы закомменчены, действуют дефолты:
  - `PermitRootLogin` дефолт = `prohibit-password` в OpenSSH ≥ 7.0 (это OK), но **явно не задано**
  - `PasswordAuthentication` дефолт = `yes` — **разрешает пароль**
  - `MaxAuthTries` дефолт = `6` — слишком мягко
  - `ChallengeResponseAuth`/`KbdInteractiveAuth` не выключены — путь для пароль-через-PAM
  - `UsePAM yes` подтверждает что PAM пускает пароль
- **Почему плохо:** на сервер с public IP постоянно стучатся боты. Дефолт `PermitRootLogin prohibit-password` спасает только от пароля под root, но любой другой пользователь (если когда-либо появится) сможет логиниться по паролю. И автоматический lock после 6 попыток — слабая защита, fail2ban нет.
- **Исправление:** в `/etc/ssh/sshd_config.d/00-hardening.conf`:
  ```
  PermitRootLogin prohibit-password
  PasswordAuthentication no
  KbdInteractiveAuth no
  PubkeyAuthentication yes
  MaxAuthTries 3
  ClientAliveInterval 300
  ClientAliveCountMax 2
  X11Forwarding no
  PermitEmptyPasswords no
  ```
  затем `sshd -t && systemctl reload ssh`.

#### H-2. fail2ban не установлен
- **Где:** `systemctl status fail2ban` пусто, пакет отсутствует
- **Почему плохо:** SSH:22 publicly accessible + дефолт `MaxAuthTries 6` + UFW не блочит брутфорс. Любой ботнет может неделями подбирать.
- **Исправление:** `apt-get install -y fail2ban`, в `/etc/fail2ban/jail.local`:
  ```
  [sshd]
  enabled = true
  maxretry = 3
  findtime = 10m
  bantime = 1h
  ```
  Опционально добавить jail для nginx-`limit-req` после деплоя лендинга.

#### H-3. Системный nginx.conf разрешает TLS 1.0 / 1.1 на http-уровне
- **Где:** `/etc/nginx/nginx.conf` строка `ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;` (см. вывод `nginx -T`)
- **Почему плохо:** наш `otklicker.ru.conf:81` переопределяет на `TLSv1.2 TLSv1.3` — **для otklicker.ru это ОК**. Но любой другой vhost на этом сервере, не задавший явно `ssl_protocols`, унаследует TLS 1.0/1.1 — POODLE/BEAST/уязвимые шифры. Это влияет на репутацию shared host.
- **Исправление:** в `/etc/nginx/nginx.conf` поправить http-блок: `ssl_protocols TLSv1.2 TLSv1.3;` и `ssl_prefer_server_ciphers off;` (последнее для совр. лучших практик с CHACHA20). Это не сломает otklicker.ru.conf.

### MEDIUM

#### M-1. CSP содержит `script-src 'unsafe-inline'`
- **Где:** `otklicker.ru.conf:102` и продублировано в `:198`
- **Почему плохо:** `'unsafe-inline'` сводит XSS-защиту почти к нулю. Любая stored/reflected XSS немедленно эксплуатируема. Yandex.Metrica — реальная причина (она требует inline-snippet) но решается nonce-ом или хешем.
- **Исправление (для Phase 4 когда Метрика будет добавлена):** перейти на `script-src 'self' 'nonce-$request_id' https://mc.yandex.ru;` и встраивать снипет с `nonce`. Альтернатива: вынести Метрику в отдельный JS-файл и отдавать с `'self'`. Пока Метрики нет — можно убрать `'unsafe-inline'` уже сейчас.

#### M-2. CSP содержит `style-src 'unsafe-inline'`
- **Где:** `otklicker.ru.conf:102, :198`
- **Почему плохо:** менее опасно чем у скриптов, но позволяет CSS-injection (data exfiltration через `background:url(...)`).
- **Исправление:** Next.js export использует Tailwind который генерирует статичный CSS — inline-стили не нужны. После убедиться (открыть out/index.html, поискать `style=`), убрать `'unsafe-inline'` из `style-src`.

#### M-3. `frame-src https://mc.yandex.ru` вместо `frame-src 'none'` пока Метрика не подключена
- **Где:** `otklicker.ru.conf:102, :198`
- **Почему плохо:** Phase 4 только планирует Метрику. Пока её нет, расширенная директива даёт лишний attack-surface (clickjacking-iframe из mc.yandex.ru теоретически возможен).
- **Исправление:** до Phase 4 заменить на `frame-src 'none'`. После добавления — вернуть.

#### M-4. `connect-src 'self' https://mc.yandex.ru` без HTTPS-API эндпоинта
- **Где:** `otklicker.ru.conf:102, :198`
- **Почему плохо:** статический лендинг сейчас не делает fetch/XHR. Можно сузить.
- **Исправление:** до подключения Метрики — `connect-src 'self'`. После — `'self' https://mc.yandex.ru`.

#### M-5. CSP дублируется в server-блоке и в location `/`
- **Где:** `otklicker.ru.conf:102` (server-уровень) и `:198` (location /)
- **Почему плохо:** не уязвимость, но source of drift — обновишь в одном месте, забудешь в другом, защита частично сломается. Уже видно: `add_header` в location `/` перекрывает наследование, поэтому пришлось дублировать. Это ожидаемое поведение nginx, но требует строгой синхронизации.
- **Исправление:** вынести security-headers в отдельный файл `/etc/nginx/snippets/security-headers.conf` и подключать через `include` в обоих местах. Source of truth один.

#### M-6. `setup-server.sh` запускает `apt-get update && apt-get install` без проверки целостности
- **Где:** `setup-server.sh:55-57`
- **Почему плохо:** не уязвимость в обычной модели угроз (apt подписан), но скрипт не проверяет наличие сети, не пинит версии. Если в будущем добавится — лучше зафиксировать минорные версии для предсказуемости.
- **Исправление:** приемлемо как есть. Для усиления — добавить `apt-get install --no-install-recommends`.

#### M-7. Setup-скрипт пытается перезапустить nginx с возможным сломанным конфигом
- **Где:** `setup-server.sh:106-120` — комментарий явно говорит «может упасть на первом проходе»
- **Почему плохо:** это известный edge-case (см. otklicker.ru.conf где listen 443 ssl без сертификата → nginx -t падает). Скрипт правильно его обходит через двойной `nginx -t`. Но комментарий «временно закомментируйте listen 443» — это manual step, нарушает идемпотентность.
- **Исправление:** на первом проходе деплоить `otklicker.ru.http-only.conf`, после certbot успеха — заменять на полный. Это уже подразумевается в задумке (Phase 7), просто закодифицировать в скрипте: добавить флаг `--bootstrap` который ставит http-only конфиг.

### LOW

#### L-1. ssh_config: `ClientAliveInterval`/`ClientAliveCountMax` на дефолтах
- **Где:** sshd_config — обе закомменчены (ClientAliveInterval 0 = disabled)
- **Почему плохо:** зависшие сессии висят бесконечно, пожирают слот, могут быть hijacked после краша клиента.
- **Исправление:** см. H-1 — добавить `ClientAliveInterval 300`, `ClientAliveCountMax 2`.

#### L-2. SSH на стандартном порту 22
- **Почему плохо:** не уязвимость, но привлекает scan-трафик и шум в логах. Меняется одной строкой и резко снижает 99% брутфорса.
- **Исправление:** опционально — `Port 2202` (нестандартный, но не «секретный»), параллельно с fail2ban (см. H-2). Не критично если fail2ban стоит.

#### L-3. `gzip on` без `gzip_disable` для старых браузеров и без `gzip_static`
- **Где:** `otklicker.ru.conf:109-127`
- **Почему плохо:** не безопасность напрямую, но BREACH-attack на gzip+TLS существует. Для лендинга без cookies/CSRF-token в HTML — irrelevant, но если в будущем появятся приватные данные, подумать.
- **Исправление:** ничего не делать пока на лендинге нет приватных response-данных. Если добавится session-cookie или CSRF в HTML — выключить gzip для этого роута.

#### L-4. `actions/checkout@v4` без `persist-credentials: false`
- **Где:** `.github/workflows/deploy.yml:18`, `ci.yml:15`
- **Почему плохо:** GITHUB_TOKEN остаётся в `.git/config` после checkout, любой last step может его забрать. В нашем deploy.yml — мы запускаем rsync через свой ключ, не нуждаемся в GITHUB_TOKEN после checkout.
- **Исправление:** добавить `with: persist-credentials: false` в шаги checkout (обоих workflow).

#### L-5. deploy.yml не имеет `permissions:` блока
- **Где:** `.github/workflows/deploy.yml`
- **Почему плохо:** GitHub дефолт = `write-all` если не задано. Workflow получает больше прав чем нужно.
- **Исправление:** в начале job добавить:
  ```yaml
  permissions:
    contents: read
  ```
  Аналогично в ci.yml.

#### L-6. `StrictHostKeyChecking=accept-new` после `ssh-keyscan`
- **Где:** `deploy.yml:48, :53`
- **Почему плохо:** мы делаем `ssh-keyscan -H` и сохраняем в `known_hosts`, после чего `accept-new` уже не нужен — лучше `yes` для строгой проверки. Сейчас если кто-то перехватит keyscan (TOFU race), accept-new примет.
- **Исправление:** заменить `accept-new` на `yes` в `-o StrictHostKeyChecking=yes`. Идеально — пинить host-key через GitHub Secret и подкладывать его до rsync, не через keyscan.

#### L-7. `setup-server.sh` не делает backup существующего nginx-конфига
- **Где:** `setup-server.sh:94-95` — `cp` без backup
- **Почему плохо:** если в `/etc/nginx/sites-available/otklicker.ru` была кастомизация, `cp` её затрёт. Идемпотентность нарушена в edge-case.
- **Исправление:** `cp -f "${NGINX_AVAILABLE}" "${NGINX_AVAILABLE}.bak.$(date +%s)" 2>/dev/null || true` перед копированием.

#### L-8. `ssl_session_timeout 1d` — длинноват
- **Где:** `otklicker.ru.conf:85`
- **Почему плохо:** Mozilla рекомендует 1 час (`1h`). В случае компрометации сессия живёт максимум час, не сутки.
- **Исправление:** `ssl_session_timeout 1h;`

#### L-9. Нет `Cross-Origin-*` headers
- **Где:** `otklicker.ru.conf` security-headers блок
- **Почему плохо:** `Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Embedder-Policy: require-corp`, `Cross-Origin-Resource-Policy: same-site` — defense-in-depth против Spectre-class и cross-origin leaks. Не критично для статического лендинга.
- **Исправление:** опционально — добавить `add_header Cross-Origin-Opener-Policy "same-origin" always;` и `add_header Cross-Origin-Resource-Policy "same-origin" always;`. COEP пропустить (он ломает встраивание Метрики).

### INFO

#### I-1. server_tokens off корректно поставлен в обоих vhost-блоках
- `otklicker.ru.conf:47, :69, :224`, `http-only.conf:16` — версия nginx не утекает в Server-header (внутренний curl показал просто `Server: nginx`). OK.

#### I-2. Защита от `/.git`, `/.env` etc. через `location ~ /\.(?!well-known)` корректна
- `otklicker.ru.conf:211-215`, `http-only.conf:53-57` — защищает скрытые файлы, но пропускает `.well-known/`. OK.

#### I-3. ACME-challenge route правильно изолирован
- `otklicker.ru.conf:51-55, :140-144`, `http-only.conf:22-26` — `^~` префикс не редиректит на HTTPS, корректно. OK.

#### I-4. `gzip_proxied any` + `gzip_vary on`
- `otklicker.ru.conf:111, :110` — корректно для CDN-кэширования. OK.

#### I-5. UFW активен и корректно настроен (для INPUT chain)
- Открыты только 22/80/443. **Но** см. C-1, C-2 — Docker bypass.

#### I-6. `concurrency: deploy-production` с `cancel-in-progress: false`
- `deploy.yml:8-10` — корректно: не отменяет уже идущий деплой, что предотвращает race и corrupted rsync.

#### I-7. `pull_request_target` НЕ используется
- ci.yml использует `pull_request` (безопасно для запуска кода из PR с pinned permissions). OK.

#### I-8. Secrets не печатаются в логах workflow
- deploy.yml: `secrets.DEPLOY_SSH_KEY` идёт в файл через `>`, не в `echo`. GitHub автоматически маскирует значения секретов в выводе. OK.

#### I-9. Bootstrap-конфиг минималистичен и не открывает странных путей
- `otklicker.ru.http-only.conf` — `/`, `/.well-known/acme-challenge/`, deny `/\..*`. Никаких `/admin`, `/api`, `/.git`. OK.

#### I-10. authorized_keys содержит 3 ключа с понятными comment-полями
- `evgeniy@jinru.vip`, `github-actions-deploy`, `otklicker-gh-actions@20260425` — все идентифицируются. Старых/анонимных нет. OK. Рекомендация: удалить `github-actions-deploy` если он от старого репо и не используется (сейчас используется `otklicker-gh-actions@20260425`).

#### I-11. CSP включает `base-uri 'self'`, `object-src 'none'`, `form-action 'self'`
- `otklicker.ru.conf:102, :198` — лучшие практики выполнены. OK.

#### I-12. OCSP stapling включён с резолверами Cloudflare/Google
- `otklicker.ru.conf:89-92` — OK. Не утекает приватный DNS-провайдер пользователя.

#### I-13. HSTS правильно закомменчен с инструкцией
- `otklicker.ru.conf:95-96` — есть явный TODO «активировать после успешного renew --dry-run». Корректный подход (не ставить HSTS пока цепочка нестабильна — иначе невозможно откатить).

---

## Сводный score
- **TLS / nginx (production-config):** 8/10 — TLS 1.2/1.3, сильные шифры, OCSP stapling, security-headers покрыты. Минусы: CSP unsafe-inline, дубликат CSP, session_timeout 1d, нет COOP/CORP.
- **Bootstrap http-only:** 9/10 — минималистичен, защищён, корректный ACME-роут.
- **SSH:** 4/10 — sshd_config на дефолтах, fail2ban нет, MaxAuthTries 6, password-auth теоретически возможен через PAM.
- **GH Actions:** 7/10 — secrets корректно, concurrency корректно, но нет permissions-блока, persist-credentials по дефолту, accept-new вместо yes.
- **Network exposure:** 3/10 — UFW корректен, но Docker bypassит UFW и выставляет 5 Postgres-инстансов и 6 admin-сервисов соседних ботов в публик. Это **не для otklicker напрямую**, но это shared host.
- **Setup-script:** 7/10 — set -euo pipefail, идемпотентность есть, нет backup конфига, edge-case с nginx -t.
- **Live HTTP-headers (бутстрап):** 8/10 — `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, server_tokens off. Headers будут расширены на HTTPS-стадии.

**Total readiness for otklicker.ru landing production:** 7/10 — **yellow**.

Лендинг сам по себе готов к публику (после certbot и фиксов M-1..M-3 и L-1..L-9). Блокеры по соседним сервисам (C-1, C-2, H-1, H-2) не относятся к otklicker напрямую, но создают reputation-risk если Postgres-инстанс соседнего бота скомпрометируется.

---

## Action items для Phase 7 (после certbot, перед публичным запуском)
- [ ] Включить HSTS после успешного `certbot renew --dry-run` (`otklicker.ru.conf:96` — раскомментировать)
- [ ] Заменить bootstrap-конфиг на полный production-конфиг
- [ ] Установить fail2ban (H-2)
- [ ] Закодифицировать SSH hardening через `/etc/ssh/sshd_config.d/00-hardening.conf` (H-1)
- [ ] Поправить `/etc/nginx/nginx.conf` — убрать TLSv1/TLSv1.1 на http-уровне (H-3)
- [ ] Убрать `'unsafe-inline'` из `script-src` и `style-src` пока Метрика не подключена (M-1, M-2)
- [ ] Сузить `frame-src` и `connect-src` до `'none'`/`'self'` пока Метрика не подключена (M-3, M-4)
- [ ] Вынести security-headers в `/etc/nginx/snippets/security-headers.conf` и подключить через include (M-5)
- [ ] `ssl_session_timeout 1h;` (L-8)
- [ ] Добавить `permissions: contents: read` в оба workflow (L-5)
- [ ] Добавить `with: persist-credentials: false` в actions/checkout (L-4)
- [ ] Заменить `StrictHostKeyChecking=accept-new` на `yes` в deploy.yml (L-6)

## Action items долгосрочные (после публичного запуска)
- [ ] **Высокий приоритет:** забиндить все Postgres-контейнеры на `127.0.0.1` (C-1) — отдельная задача по соседним ботам
- [ ] **Высокий приоритет:** скрыть admin-сервисы за TLS+auth-proxy или забиндить на 127.0.0.1 (C-2)
- [ ] testssl.sh + Mozilla Observatory — внешний аудит после certbot и активации HSTS
- [ ] Settle на nonce-based CSP когда добавится Yandex.Metrica (Phase 4)
- [ ] Регулярный `apt-get upgrade` (auto через unattended-upgrades, проверить установку)
- [ ] Logrotate для `/var/log/nginx/otklicker.ru.access.log` и `error.log` (по умолчанию ставится с пакетом nginx — проверить `/etc/logrotate.d/nginx`)
- [ ] Backup-стратегия для `/etc/letsencrypt/`, `/etc/nginx/sites-available/`, `/var/www/otklicker.ru/` — еженедельный rsync на отдельный хранитель
- [ ] Удалить старый ключ `github-actions-deploy` из authorized_keys если не используется (I-10)
- [ ] Опционально: SSH на нестандартный порт (L-2) после установки fail2ban
- [ ] Добавить `Cross-Origin-Opener-Policy` и `Cross-Origin-Resource-Policy` (L-9)
