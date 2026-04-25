# Deploy: otklicker.ru

Локальная инфра для деплоя статического лендинга `otklicker.ru` на Hetzner.

## Архитектура

```
git push main → GitHub Actions → npm ci + next build → rsync → nginx
                                                                 ↓
                                                       /var/www/otklicker.ru/
```

- **Build**: Next.js 14 static export, выход в `site/out/`.
- **Transport**: rsync поверх SSH с CI runner (ubuntu-latest) на сервер.
- **Serve**: nginx 1.24 на Hetzner CAX21 (Helsinki, ARM, Ubuntu 24.04).
- **TLS**: Let's Encrypt через `certbot --nginx`, автообновление через `certbot.timer`.
- **DNS**: Timeweb (на момент Phase 5a). A/AAAA переключатся на `204.168.178.241` в Phase 7.
- **Email**: `info@otklicker.ru` на Yandex 360 (MX переключим в Phase 7).

## Файлы

| Путь | Назначение |
|---|---|
| `deploy/nginx/otklicker.ru.conf` | nginx config: HTTP→HTTPS, www→apex, TLS, security headers, кеш, try_files для Next.js export |
| `deploy/scripts/setup-server.sh` | Идемпотентный скрипт первичной настройки сервера (apt, certbot, симлинк, проверка DNS) |
| `.github/workflows/deploy.yml` | Push в `main` → build → rsync → smoke-curl |
| `.github/workflows/ci.yml` | PR → tsc + lint + build (без деплоя) |

## Первичная настройка сервера (одноразово)

> Эту секцию выполняет владелец/Phase 5b. До этого момента CI будет fail на rsync, потому что публичный ключ ещё не на сервере.

1. SSH на сервер:

   ```bash
   ssh root@204.168.178.241
   ```

2. Склонировать репо во временное место (или скопировать только `deploy/`):

   ```bash
   git clone https://github.com/operhueper/otklicker.git /tmp/otklicker
   cd /tmp/otklicker
   ```

3. Запустить setup-скрипт:

   ```bash
   sudo bash deploy/scripts/setup-server.sh
   ```

   На этом этапе скрипт:
   - поставит `certbot`, `python3-certbot-nginx`, `rsync`,
   - создаст `/var/www/otklicker.ru/` и `/var/www/letsencrypt/`,
   - положит временную заглушку `index.html`,
   - подключит nginx config,
   - проверит DNS. Если DNS ещё указывает на старый Timeweb-хостинг,
     скрипт **выйдет до certbot** с подсказкой. Это ожидаемо до Phase 7.

4. (После переключения DNS, Phase 7) запустить скрипт повторно — он
   выпустит сертификат и включит `certbot.timer`.

5. После первого успешного `certbot renew --dry-run` раскомментить
   `add_header Strict-Transport-Security` в `otklicker.ru.conf`,
   закоммитить и задеплоить.

## SSH ключ для CI

Локально сгенерирован отдельный ключ (НЕ путать с `~/.ssh/otklicker_deploy` — тот для владельца):

- Приватный: `~/.ssh/otklicker_gh_actions` — пойдёт в GH Secret `DEPLOY_SSH_KEY`.
- Публичный: `~/.ssh/otklicker_gh_actions.pub` — на сервер в `/root/.ssh/authorized_keys`.

Добавить публичный ключ на сервер (одной строкой):

```bash
cat ~/.ssh/otklicker_gh_actions.pub | ssh root@204.168.178.241 \
    'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
```

## GitHub Secrets

Нужно добавить в `Settings → Secrets and variables → Actions` репо
`operhueper/otklicker`:

| Secret | Значение |
|---|---|
| `DEPLOY_SSH_KEY` | Полное содержимое `~/.ssh/otklicker_gh_actions` (включая `-----BEGIN OPENSSH PRIVATE KEY-----` и `-----END OPENSSH PRIVATE KEY-----`) |
| `DEPLOY_HOST` | `204.168.178.241` |
| `DEPLOY_USER` | `root` |
| `DEPLOY_PATH` | `/var/www/otklicker.ru/` (с trailing slash — критично для rsync) |

Через CLI:

```bash
gh secret set DEPLOY_SSH_KEY < ~/.ssh/otklicker_gh_actions
gh secret set DEPLOY_HOST -b "204.168.178.241"
gh secret set DEPLOY_USER -b "root"
gh secret set DEPLOY_PATH -b "/var/www/otklicker.ru/"
```

## Откат деплоя

Простой случай — найти прошлый рабочий коммит, сбилдить локально и
загрузить руками:

```bash
cd ~/projects/otklicker
git checkout <good-commit-sha>
cd site
npm ci
npm run build
rsync -avz --delete \
    -e "ssh -i ~/.ssh/otklicker_deploy" \
    out/ root@204.168.178.241:/var/www/otklicker.ru/
git checkout main
```

Альтернатива — `git revert <bad-commit>` и `git push`, CI задеплоит.

## Перевыпуск SSL

```bash
ssh root@204.168.178.241 'certbot renew --force-renewal && systemctl reload nginx'
```

## Проверки

После деплоя:

```bash
# С локалки, до DNS-переключения (по IP с Host-header):
curl -I -H "Host: otklicker.ru" http://204.168.178.241/

# После DNS-переключения и certbot:
curl -I https://otklicker.ru/
curl -I https://www.otklicker.ru/   # ожидается 301 на apex
```

SSL Labs (после Phase 7):

```
https://www.ssllabs.com/ssltest/analyze.html?d=otklicker.ru
```
