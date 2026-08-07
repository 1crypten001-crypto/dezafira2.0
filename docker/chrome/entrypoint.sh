#!/bin/sh
# ============================================================
# 🌐 Chrome real (headless) — serviço CDP para o bridge Dezafira
#
# O Chrome moderno (136+) IGNORA --remote-debugging-address=0.0.0.0
# e binda o DevTools SÓ em 127.0.0.1 (o log mostra "DevTools
# listening on ws://127.0.0.1:9223"). Por isso este entrypoint:
#   1. roda o Chrome no LOOPBACK (porta interna, ex.: 9224)
#   2. o cdp_proxy.py expõe o CDP para a rede (0.0.0.0) reescrevendo o Host
#      para 127.0.0.1 (anti-DNS-rebinding) e responde 200 p/ qualquer caminho
#      não-CDP (healthcheck do Railway passa em qualquer porta).
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

# O backend SEMPRE sonda o CDP na porta fixa 9223 (default de
# OBSCURA_CHROME_HOST/OBSCURA_CHROME_PORT = chrome.railway.internal:9223).
# Por isso expomos a 9223 FIXA alEN de qualquer OBSCURA_CHROME_PORT/NOTA do
# Railway que esteja setada. Guardamos as portas extras antes de fixar a 9223.
RAILWAY_PORT="${PORT:-}"
EXTRA_PORT="${OBSCURA_CHROME_PORT:-}"
PORT="9223"
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

# Proxy TCP unificado (substitui o socat + health_server.py): responde 200
# para QUALQUER caminho que não seja do CDP (healthcheck do Railway passa em
# QUALQUER porta, seja $PORT, 9000, 80, 8080 ou 9223) e encaminha /json/* e
# /devtools/* para o CDP no loopback reescrevendo Host -> 127.0.0.1 (mata o
# anti-DNS-rebinding do Chrome para o backend usar *.railway.internal).
if command -v python3 >/dev/null 2>&1; then
    PORT="$RAILWAY_PORT" OBSCURA_INNER_PORT="$INNER_PORT" python3 /usr/local/bin/cdp_proxy.py &
    echo "[entrypoint] Proxy CDP/health Python ativo"
else
    echo "[entrypoint] ERRO: python3 nao encontrado — sem proxy/health" >&2
    exit 1
fi

# Auto-verificação: confirma que o CDP responde através do proxy na porta 9223
# (a mesma que o backend usa via rede privada chrome.railway.internal:9223).
i=0
while [ $i -lt 15 ]; do
    if wget -q -O /dev/null "http://127.0.0.1:9223/json/version" 2>/dev/null; then
        echo "[entrypoint] Healthcheck OK: http://127.0.0.1:9223/json/version responde via proxy"
        break
    fi
    i=$((i+1))
    sleep 1
done
if [ $i -ge 15 ]; then
    echo "[entrypoint] AVISO: /json/version nao respondeu via proxy em 15s" >&2
fi

# Mantém o container vivo (o shell é o PID 1)
wait
