#!/bin/sh
# ============================================================
# 🌐 Chrome real (headless) — serviço CDP para o bridge Dezafira
#
# Sobe o Chrome real com remote debugging (CDP) no host 0.0.0.0
# (acessível pela rede privada do Railway) e proxy condicional
# via OBSCURA_PROXY_URL. O bridge prefere este motor para o
# Google (SERP/PAA reais) e usa o Obscura como fallback.
# ============================================================
set -e

CHROME="${CHROME_BIN:-/usr/bin/google-chrome}"
if [ ! -x "$CHROME" ]; then
    # tenta alternativas comuns (chromium, chrome-headless-shell)
    for c in /usr/bin/google-chrome-stable /usr/bin/chromium /usr/bin/chromium-browser /opt/google/chrome/chrome; do
        if [ -x "$c" ]; then CHROME="$c"; break; fi
    done
fi
if [ ! -x "$CHROME" ]; then
    echo "[entrypoint] ERRO: Chrome nao encontrado" >&2
    exit 1
fi

PORT="${OBSCURA_CHROME_PORT:-9223}"

BASE="--headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage"
BASE="$BASE --remote-debugging-port=$PORT --remote-debugging-address=0.0.0.0"
BASE="$BASE --user-data-dir=/tmp/chrome-profile"
BASE="$BASE --no-first-run --no-default-browser-check --disable-blink-features=AutomationControlled"

if [ -n "$OBSCURA_PROXY_URL" ]; then
    echo "[entrypoint] Chrome com proxy residencial ativo"
    exec "$CHROME" $BASE --proxy-server="$OBSCURA_PROXY_URL" about:blank
else
    echo "[entrypoint] Chrome sem proxy"
    exec "$CHROME" $BASE about:blank
fi
