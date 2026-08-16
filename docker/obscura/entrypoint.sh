#!/bin/sh
# ============================================================
# Obscura — entrypoint com socat
#
# O binário do Obscura IGNORA --host 0.0.0.0 e binda o CDP SÓ em
# 127.0.0.1 (mesmo comportamento do Chrome 136+). Por isso:
#   1. roda o Obscura no LOOPBACK (porta interna, default 9225)
#   2. o cdp_proxy.py expõe o CDP para a rede (0.0.0.0) reescrevendo o Host
#      para 127.0.0.1 (anti-DNS-rebinding) e responde 200 p/ qualquer caminho
#      não-CDP (healthcheck do Railway passa em qualquer porta).
# Assim a rede privada do Railway alcança o CDP de verdade.
# ============================================================
set -e

BIN=$(find /opt/obscura -type f -executable 2>/dev/null | head -1)
if [ -z "$BIN" ]; then
    echo "[entrypoint] ERRO: binario do Obscura nao encontrado em /opt/obscura" >&2
    exit 1
fi

# $PORT é injetado pelo Railway (dinâmico). O backend SEMPRE sonda o CDP na
# porta fixa 9222 (OBSCURA_PORT default). Guardamos as portas extras e fixamos
# a 9222 para garantir que ela seja exposta, mesmo que OBSCURA_PORT env esteja
# setado com outro valor no serviço.
RAILWAY_PORT="${PORT:-}"
EXTRA_PORT="${OBSCURA_PORT:-}"
PORT="9222"
INNER_PORT="${OBSCURA_INNER_PORT:-9225}"
WORKERS="${OBSCURA_WORKERS:-4}"

if [ "$PORT" = "$INNER_PORT" ]; then
    INNER_PORT=$((INNER_PORT+1))
fi

echo "[entrypoint] Binario: $BIN"
echo "[entrypoint] Porta CDP: $PORT | interna: $INNER_PORT | workers: $WORKERS | railway PORT: ${RAILWAY_PORT:-<vazio>}"

# Inicia Xvfb (display virtual p/ Chromium embutido).
# Resiliencia: limpa locks residuais (restart pode deixar /tmp/.X99-lock) e,
# se o display :99 falhar, cai para :100 em vez de derrubar o container
# (bug observado 15/08: "Server is already active for display 99" → CDP nunca
# subiu → healthcheck falhou → deploy FAILED).
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null || true
echo "[entrypoint] Iniciando Xvfb..."
Xvfb :99 -screen 0 1280x720x24 -ac +extension GLX +render -noreset >/tmp/xvfb.log 2>&1 &
XVFB_PID=$!
sleep 1
if ! kill -0 "$XVFB_PID" 2>/dev/null; then
    echo "[entrypoint] Xvfb :99 falhou ao iniciar; tentando :100" >&2
    cat /tmp/xvfb.log >&2
    rm -f /tmp/.X100-lock /tmp/.X11-unix/X100 2>/dev/null || true
    Xvfb :100 -screen 0 1280x720x24 -ac +extension GLX +render -noreset >/tmp/xvfb.log 2>&1 &
    XVFB_PID=$!
    sleep 1
    export DISPLAY=:100
else
    export DISPLAY=:99
fi
echo "[entrypoint] Xvfb PID: $XVFB_PID DISPLAY=$DISPLAY"

# Inicia o Obscura no loopback (porta interna)
LOGFILE=/tmp/obscura.log
echo "[entrypoint] Iniciando Obscura em 127.0.0.1:${INNER_PORT}..."
"$BIN" serve --host 127.0.0.1 --port "$INNER_PORT" --workers "$WORKERS" --stealth > "$LOGFILE" 2>&1 &
BIN_PID=$!
echo "[entrypoint] Obscura PID: $BIN_PID (log em $LOGFILE)"

# Aguarda o CDP ficar ativo no loopback (60s)
i=0
while [ $i -lt 60 ]; do
    if curl -s -o /dev/null "http://127.0.0.1:${INNER_PORT}/json/version" 2>/dev/null; then
        echo "[entrypoint] CDP do Obscura ativo em 127.0.0.1:${INNER_PORT} (pid ${BIN_PID})"
        break
    fi
    if [ $((i % 10)) -eq 0 ] && [ $i -gt 0 ]; then
        echo "[entrypoint] Aguardando CDP... ${i}s / 60s"
        tail -5 "$LOGFILE" 2>/dev/null || true
    fi
    i=$((i+1))
    sleep 1
done

if [ $i -ge 60 ]; then
    echo "[entrypoint] ERRO: CDP do Obscura nao respondeu em 60s." >&2
    echo "=== LOG ===" >&2
    cat "$LOGFILE" 2>/dev/null || true
    echo "=== FIM ===" >&2
    ldd "$BIN" 2>&1 | grep "not found" || echo "libs OK"
    exit 1
fi

# Proxy TCP unificado (substitui o socat + health_server.py): responde 200
# para QUALQUER caminho que não seja do CDP (healthcheck do Railway passa em
# QUALQUER porta, seja $PORT, 9000, 80, 8080 ou 9222) e encaminha /json/* e
# /devtools/* para o CDP no loopback reescrevendo Host -> 127.0.0.1 (mata o
# anti-DNS-rebinding do motor para o backend usar *.railway.internal).
if command -v python3 >/dev/null 2>&1; then
    PORT="$RAILWAY_PORT" OBSCURA_INNER_PORT="$INNER_PORT" python3 /usr/local/bin/cdp_proxy.py &
    echo "[entrypoint] Proxy CDP/health Python ativo"
else
    echo "[entrypoint] ERRO: python3 nao encontrado — sem proxy/health" >&2
    exit 1
fi

# Auto-verificação: confirma que o CDP responde através do proxy na porta 9222
# (a mesma que o backend usa via rede privada obscura.railway.internal:9222).
i=0
while [ $i -lt 15 ]; do
    if curl -s -o /dev/null "http://127.0.0.1:9222/json/version" 2>/dev/null; then
        echo "[entrypoint] Healthcheck OK: http://127.0.0.1:9222/json/version responde via proxy"
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
