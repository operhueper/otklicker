#!/usr/bin/env bash
# =============================================================================
# setup-server.sh -- первичная настройка nginx + certbot для otklicker.ru
# =============================================================================
#
# Запускать на сервере (Hetzner CAX21, Ubuntu 24.04, ARM):
#   sudo bash deploy/scripts/setup-server.sh
#
# или зайти как root и выполнить:
#   bash deploy/scripts/setup-server.sh
#
# Скрипт идемпотентный -- можно запускать повторно. Не падает на уже
# выполненных шагах. Если DNS не переключён, certbot не запустится --
# скрипт выйдет с подсказкой.
#
# =============================================================================

set -euo pipefail

DOMAIN="otklicker.ru"
DOMAIN_WWW="www.otklicker.ru"
EMAIL="info@otklicker.ru"
SERVER_IP="204.168.178.241"

WEB_ROOT="/var/www/${DOMAIN}"
ACME_ROOT="/var/www/letsencrypt"

NGINX_AVAILABLE="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"

# Расположение скрипта -> репо -> nginx-конфиг.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
NGINX_CONF_SRC="${REPO_ROOT}/deploy/nginx/${DOMAIN}.conf"

log()  { printf "\033[1;34m[setup]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m  %s\n" "$*" >&2; }
err()  { printf "\033[1;31m[err]\033[0m   %s\n" "$*" >&2; }

# ---- 1. Проверка что мы под root --------------------------------------------
if [[ "$(id -u)" -ne 0 ]]; then
    err "Запускать под root. Используйте: sudo bash $0"
    exit 1
fi

# ---- 2. Проверка что nginx-конфиг существует --------------------------------
if [[ ! -f "${NGINX_CONF_SRC}" ]]; then
    err "Не найден nginx-конфиг: ${NGINX_CONF_SRC}"
    err "Убедитесь что репо склонировано целиком."
    exit 1
fi

# ---- 3. apt update + установка пакетов --------------------------------------
log "Установка certbot, python3-certbot-nginx, rsync"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq certbot python3-certbot-nginx rsync

# ---- 4. Создание каталогов --------------------------------------------------
log "Создание ${WEB_ROOT} и ${ACME_ROOT}"
mkdir -p "${WEB_ROOT}" "${ACME_ROOT}"
chown -R www-data:www-data "${WEB_ROOT}" "${ACME_ROOT}"
chmod 755 "${WEB_ROOT}" "${ACME_ROOT}"

# ---- 5. Заглушка index.html (если каталог пустой) ---------------------------
if [[ ! -f "${WEB_ROOT}/index.html" ]]; then
    log "Кладу временную заглушку в ${WEB_ROOT}/index.html"
    cat > "${WEB_ROOT}/index.html" <<'EOF'
<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>otklicker.ru</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       max-width: 640px; margin: 4rem auto; padding: 0 1rem; color: #1a1a1a; }
h1 { font-size: 1.5rem; }
p { line-height: 1.6; }
</style>
</head>
<body>
<h1>otklicker.ru</h1>
<p>Скоро здесь будет лендинг откликера. Бот уже работает: @otklicker_bot</p>
</body>
</html>
EOF
    chown www-data:www-data "${WEB_ROOT}/index.html"
else
    log "Контент в ${WEB_ROOT} уже есть -- пропускаю заглушку"
fi

# ---- 6. Копирование nginx-конфига -------------------------------------------
log "Копирую ${NGINX_CONF_SRC} -> ${NGINX_AVAILABLE}"
cp "${NGINX_CONF_SRC}" "${NGINX_AVAILABLE}"

# ---- 7. Симлинк в sites-enabled ---------------------------------------------
if [[ -L "${NGINX_ENABLED}" || -f "${NGINX_ENABLED}" ]]; then
    log "Симлинк ${NGINX_ENABLED} уже существует -- обновляю"
    ln -sf "${NGINX_AVAILABLE}" "${NGINX_ENABLED}"
else
    log "Создаю симлинк ${NGINX_ENABLED}"
    ln -s "${NGINX_AVAILABLE}" "${NGINX_ENABLED}"
fi

# ---- 8. nginx -t + reload ---------------------------------------------------
log "Проверка nginx-конфига"
if ! nginx -t; then
    err "nginx -t упал. Не перезагружаю nginx, чтобы не сломать другие сайты."
    err "Скорее всего certbot ещё не выпустил сертификат, и в HTTPS-блоке"
    err "не подключены ssl_certificate. Это ожидаемо при первом запуске --"
    err "временно закомментируйте listen 443 блоки и попробуйте ещё раз,"
    err "или продолжайте: certbot ниже сам активирует SSL и перезагрузит."
    # На первом проходе fail возможен, но certbot --nginx поднимет всё сам.
fi

log "Reload nginx (если упал nginx -t -- пропускаю reload)"
if nginx -t 2>/dev/null; then
    systemctl reload nginx
fi

# ---- 9. Проверка DNS перед certbot ------------------------------------------
log "Проверяю что DNS ${DOMAIN} указывает на ${SERVER_IP}"
DNS_RESOLVED="$(dig +short "${DOMAIN}" @8.8.8.8 | tail -n1 || true)"

if [[ "${DNS_RESOLVED}" != "${SERVER_IP}" ]]; then
    warn "DNS ${DOMAIN} -> '${DNS_RESOLVED}', ожидается '${SERVER_IP}'"
    warn "Сначала переключите A/AAAA записи на ${SERVER_IP} в Timeweb DNS,"
    warn "дождитесь пропагации (обычно 5-30 минут) и запустите скрипт повторно."
    warn "Сейчас выхожу до certbot. Заглушка по HTTP уже работает."
    exit 0
fi

log "DNS ок, ${DOMAIN} -> ${DNS_RESOLVED}"

# ---- 10. certbot ------------------------------------------------------------
# Проверяем что сертификат ещё не выпущен (идемпотентность).
if [[ -d "/etc/letsencrypt/live/${DOMAIN}" ]]; then
    log "Сертификат /etc/letsencrypt/live/${DOMAIN} уже существует -- пропускаю выпуск"
else
    log "Запускаю certbot --nginx для ${DOMAIN}, ${DOMAIN_WWW}"
    certbot --nginx \
        -d "${DOMAIN}" -d "${DOMAIN_WWW}" \
        -m "${EMAIL}" \
        --agree-tos --non-interactive --redirect \
        --no-eff-email
fi

# ---- 11. certbot.timer ------------------------------------------------------
log "Включаю certbot.timer для автообновления"
systemctl enable certbot.timer
systemctl start  certbot.timer

# ---- 12. renew --dry-run ----------------------------------------------------
log "Проверка автообновления (renew --dry-run)"
if certbot renew --dry-run; then
    log "renew --dry-run OK -- HSTS можно активировать в nginx-конфиге"
else
    warn "renew --dry-run завершился с ошибкой. Проверьте логи certbot."
fi

# ---- Готово -----------------------------------------------------------------
log "Готово."
log "Проверьте вручную:"
log "  curl -I https://${DOMAIN}/"
log "  curl -I https://${DOMAIN_WWW}/   # должен быть 301 на apex"
log "После успешного renew --dry-run раскомментите add_header Strict-Transport-Security в nginx-конфиге."
