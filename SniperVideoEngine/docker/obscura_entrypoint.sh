#!/bin/sh
# ============================================================
# 🕵️ Obscura — entrypoint com proxy residencial condicional
#
# Lê OBSCURA_PROXY_URL da env do Railway e adiciona --proxy ao
# serve quando preenchida. Sem proxy, roda idêntico ao default.
# ============================================================
set -e

BIN=$(find /opt/obscura -type f -executable 2>/dev/null | head -1)
if [ -z "$BIN" ]; then
    echo "[entrypoint] ERRO: binario do Obscura nao encontrado em /opt/obscura" >&2
    exit 1
fi

PORT="${OBSCURA_PORT:-9222}"
WORKERS="${OBSCURA_WORKERS:-4}"

if [ -n "$OBSCURA_PROXY_URL" ]; then
    echo "[entrypoint] proxy residencial ativo"
    echo "[entrypoint] exec: $BIN serve --host 0.0.0.0 --port $PORT --workers $WORKERS --stealth --proxy <oculto>"
    exec "$BIN" serve --host 0.0.0.0 --port "$PORT" --workers "$WORKERS" --stealth --proxy "$OBSCURA_PROXY_URL"
else
    echo "[entrypoint] sem proxy (OBSCURA_PROXY_URL vazio)"
    exec "$BIN" serve --host 0.0.0.0 --port "$PORT" --workers "$WORKERS" --stealth
fi
