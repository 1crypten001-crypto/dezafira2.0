#!/usr/bin/env bash
# E2E do /healthz: 200 (motor de pé) → derruba motor → 503 → religa motor → 200
# Notas:
#  - server.py carrega .env com override=True → env do shell perde. Trocamos a
#    linha OBSCURA_ENABLED no proprio .env e restauramos via trap (crash-proof:
#    restaura pelo valor original capturado, nao por backup que pode estar velho).
#  - No Git Bash, $! e PID do MSYS (nao serve para taskkill). O kill do server usa
#    o PID real do Windows resolvido via netstat (mesma tecnica do motor).
cd "$(dirname "$0")"

export OBSCURA_HEALTH_GRACE=0

ORIG_OBSCURA=$(grep '^OBSCURA_ENABLED=' .env | head -1)
restore_env() {
  if [ -n "$ORIG_OBSCURA" ]; then
    sed -i "s|^OBSCURA_ENABLED=.*|$ORIG_OBSCURA|" .env 2>/dev/null || true
  else
    sed -i '/^OBSCURA_ENABLED=/d' .env 2>/dev/null || true
  fi
}
trap restore_env EXIT
sed -i 's/^OBSCURA_ENABLED=.*/OBSCURA_ENABLED=true/' .env
echo "== .env temporario: $(grep '^OBSCURA_ENABLED=' .env) (original: ${ORIG_OBSCURA:-<ausente>}) =="

WIN_PIDS_8000() { netstat -ano 2>/dev/null | grep ':8000' | grep LISTENING | awk '{print $NF}' | sort -u; }
WIN_PIDS_9222() { netstat -ano 2>/dev/null | grep ':9222' | grep LISTENING | awk '{print $NF}' | sort -u; }

KILL_PIDS() {
  for pid in $1; do taskkill //F //PID "$pid" >/dev/null 2>&1 || true; done
}

ENGINE_ONLINE() {
  timeout 10 python -c "import asyncio; from services.obscura_bridge import get_obscura_status; s=asyncio.run(get_obscura_status()); print('true' if s.get('online') else 'false')" 2>/dev/null | tail -1
}

START_ENGINE() {
  nohup ./.obscura-bin/obscura.exe serve --port 9222 --workers 4 --stealth > .obscura-bin/server.log 2>&1 </dev/null &
}

WAIT_ENGINE() {
  for i in $(seq 1 20); do
    if [ "$(ENGINE_ONLINE)" = "true" ]; then echo "motor online (iter $i)"; return 0; fi
    sleep 2
  done
  echo "!! motor NAO respondeu pelo bridge"; return 1
}

echo "== pre-flight: garante motor saudavel + limpa servidores orfaos na 8000 =="
# Sobe o uvicorn novo apenas se a 8000 estiver livre (server velho de run anterior
# ficava orfao porque o kill usava PID do MSYS; agora matamos o PID real do Windows).
KILL_PIDS "$(WIN_PIDS_8000)"
sleep 1
if [ "$(ENGINE_ONLINE)" != "true" ]; then
  echo "motor fora ou meio-morto — limpando 9222 e subindo limpo"
  KILL_PIDS "$(WIN_PIDS_9222)"
  sleep 2
  START_ENGINE
  WAIT_ENGINE || exit 1
fi

echo "== boot server (uvicorn :8000) =="
nohup python -m uvicorn server:app --port 8000 > .server_test.log 2>&1 </dev/null &
SRV_PID=$!

# espera o server responder (ate 40s)
for i in $(seq 1 40); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://127.0.0.1:8000/healthz 2>/dev/null)
  if [ "$CODE" != "000" ]; then break; fi
  sleep 1
done
echo "server pronto (HTTP $CODE) — pid $SRV_PID"

echo "== 1) Motor de pé → espera 200 =="
curl -s -o /tmp/hz1.json -w "HTTP %{http_code}\n" --max-time 8 http://127.0.0.1:8000/healthz
head -c 300 /tmp/hz1.json; echo

ENGINE_PID=$(WIN_PIDS_9222 | head -1)
echo "== matando o motor (PID $ENGINE_PID) =="
KILL_PIDS "$ENGINE_PID"
sleep 3

echo "== 2) Motor derrubado (grace=0) → espera 503 =="
curl -s -o /tmp/hz2.json -w "HTTP %{http_code}\n" --max-time 8 http://127.0.0.1:8000/healthz
head -c 500 /tmp/hz2.json; echo

echo "== religando o motor =="
START_ENGINE
WAIT_ENGINE || exit 1

echo "== 3) Motor de volta → espera 200 =="
curl -s -o /tmp/hz3.json -w "HTTP %{http_code}\n" --max-time 8 http://127.0.0.1:8000/healthz
head -c 300 /tmp/hz3.json; echo

echo "== parando o server de teste (PID real via netstat) =="
KILL_PIDS "$(WIN_PIDS_8000)"
kill "$SRV_PID" 2>/dev/null || true
echo DONE
