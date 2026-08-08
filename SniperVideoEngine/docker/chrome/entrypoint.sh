#!/bin/sh
# ============================================================
# 🌐 Chrome real (headless) — serviço CDP para o bridge Dezafira
#
# O Chrome moderno (136+) IGNORA --remote-debugging-address=0.0.0.0
# e binda o DevTools SÓ em 127.0.0.1 (o log mostra "DevTools
# listening on ws://127.0.0.1:9223"). Por isso este entrypoint:
#   1. roda o Chrome no LOOPBACK (porta interna, ex.: 9224)
#   2. expõe a porta externa via socat (0.0.0.0:PORT -> 127.0.0.1:INNER_PORT)
# Assim a rede privada do Railway alcança o Chrome de verdade.
# Proxy condicional via OBSCURA_PROXY_URL.
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
INNER_PORT="${OBSCURA_CHROME_INNER_PORT:-9224}"

# Guarda contra colisão: se PORT == INNER_PORT o socat nao consegue bindar
# (EADDRINUSE) e o container morre. Nunca deixe os dois iguais.
if [ "$PORT" = "$INNER_PORT" ]; then
    echo "[entrypoint] AVISO: OBSCURA_CHROME_PORT == OBSCURA_CHROME_INNER_PORT (${PORT}) — ajustando INNER_PORT para $((INNER_PORT+1))" >&2
    INNER_PORT=$((INNER_PORT+1))
fi

BASE="--headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage"
# Chrome no loopback — o DevTools sempre binda em 127.0.0.1 no Chrome 136+
BASE="$BASE --remote-debugging-port=$INNER_PORT --remote-debugging-address=127.0.0.1"
BASE="$BASE --user-data-dir=/tmp/chrome-profile"
BASE="$BASE --no-first-run --no-default-browser-check --disable-blink-features=AutomationControlled"

if [ -n "$OBSCURA_PROXY_URL" ]; then
    echo "[entrypoint] Chrome com proxy residencial ativo"
    "$CHROME" $BASE --proxy-server="$OBSCURA_PROXY_URL" about:blank &
else
    echo "[entrypoint] Chrome sem proxy"
    "$CHROME" $BASE about:blank &
fi
CHROME_PID=$!

# Espera o CDP do Chrome ficar pronto (loopback)
i=0
while [ $i -lt 30 ]; do
    if wget -q -O /dev/null "http://127.0.0.1:${INNER_PORT}/json/version" 2>/dev/null; then
        echo "[entrypoint] CDP do Chrome ativo em 127.0.0.1:${INNER_PORT} (pid ${CHROME_PID})"
        break
    fi
    i=$((i+1))
    sleep 1
done
if [ $i -ge 30 ]; then
    # Chrome morto → sair com erro para o Railway reiniciar o container
    # (senão o socat ficaria como 'forwarder oco' e o serviço não se auto-cura)
    echo "[entrypoint] ERRO: CDP do Chrome nao respondeu em 30s — Chrome pode ter morrido. Reiniciando." >&2
    exit 1
fi

# socat: expõe 0.0.0.0:PORT (rede privada do Railway) -> 127.0.0.1:INNER_PORT
echo "[entrypoint] Expondo :${PORT} (0.0.0.0) -> 127.0.0.1:${INNER_PORT} via socat"
exec socat TCP-LISTEN:${PORT},bind=0.0.0.0,reuseaddr,fork TCP:127.0.0.1:${INNER_PORT}
