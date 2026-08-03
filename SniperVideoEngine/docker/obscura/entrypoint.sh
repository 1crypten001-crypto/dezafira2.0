#!/bin/sh
# ============================================================
# 🕵️ Obscura — entrypoint com proxy residencial e socat
#
# O binário do Obscura binda o servidor CDP em 127.0.0.1 por default.
# Para permitir que a rede privada do Railway o acesse de fora, rodamos:
#   1. O Obscura no loopback (porta interna, default 9225)
#   2. socat mapeando a porta externa (9222) para a interna (9225)
# ============================================================
set -e

BIN=$(find /opt/obscura -type f -executable 2>/dev/null | head -1)
if [ -z "$BIN" ]; then
    echo "[entrypoint] ERRO: binario do Obscura nao encontrado em /opt/obscura" >&2
    exit 1
fi

PORT="${OBSCURA_PORT:-9222}"
INNER_PORT="${OBSCURA_INNER_PORT:-9225}"
WORKERS="${OBSCURA_WORKERS:-4}"

# Evita colisão se as portas configuradas forem iguais
if [ "$PORT" = "$INNER_PORT" ]; then
    INNER_PORT=$((INNER_PORT+1))
fi

if [ -n "$OBSCURA_PROXY_URL" ]; then
    echo "[entrypoint] Obscura com proxy residencial ativo"
    "$BIN" serve --host 127.0.0.1 --port "$INNER_PORT" --workers "$WORKERS" --stealth --proxy "$OBSCURA_PROXY_URL" &
else
    echo "[entrypoint] Obscura sem proxy"
    "$BIN" serve --host 127.0.0.1 --port "$INNER_PORT" --workers "$WORKERS" --stealth &
fi
OBSCURA_PID=$!

# Aguarda o CDP ficar ativo no loopback
i=0
while [ $i -lt 30 ]; do
    if curl -s -o /dev/null "http://127.0.0.1:${INNER_PORT}/json/version" 2>/dev/null; then
        echo "[entrypoint] CDP do Obscura ativo em 127.0.0.1:${INNER_PORT} (pid ${OBSCURA_PID})"
        break
    fi
    i=$((i+1))
    sleep 1
done
if [ $i -ge 30 ]; then
    echo "[entrypoint] ERRO: CDP do Obscura nao respondeu em 30s. Reiniciando." >&2
    exit 1
fi

# socat: expõe 0.0.0.0:PORT (rede privada do Railway) -> 127.0.0.1:INNER_PORT
echo "[entrypoint] Expondo :${PORT} (0.0.0.0) -> 127.0.0.1:${INNER_PORT} via socat"
exec socat TCP-LISTEN:${PORT},bind=0.0.0.0,reuseaddr,fork TCP:127.0.0.1:${INNER_PORT}
