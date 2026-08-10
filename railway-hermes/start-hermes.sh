#!/bin/sh
set -e

# 1. Executa o seed de configuração caso esteja disponível
if [ -f /etc/cont-init.d/00-seed-config ]; then
  echo "[start-hermes] Rodando seed-config..."
  /etc/cont-init.d/00-seed-config || true
fi

# 2. Inicia o gateway em background na porta interna 8642
echo "[start-hermes] Iniciando Hermes Gateway na porta 8642..."
gateway run --host 0.0.0.0 --port 8642 &
GATEWAY_PID=$!

# 3. Inicia o dashboard oficial na porta $PORT do Railway (ou 9119 caso nula)
DASHBOARD_PORT="${PORT:-9119}"
echo "[start-hermes] Iniciando Hermes Dashboard na porta ${DASHBOARD_PORT}..."
hermes dashboard --host 0.0.0.0 --port "${DASHBOARD_PORT}" --no-open &
DASHBOARD_PID=$!

# 4. Monitoramento contínuo
echo "[start-hermes] Monitorando processos..."
while true; do
  if ! kill -0 $GATEWAY_PID 2>/dev/null; then
    echo "[start-hermes] Gateway morreu!"
    exit 1
  fi
  if ! kill -0 $DASHBOARD_PID 2>/dev/null; then
    echo "[start-hermes] Dashboard morreu!"
    exit 1
  fi
  sleep 5
done
