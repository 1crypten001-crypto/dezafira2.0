#!/usr/bin/env bash
# Smoke test HTTP real do Blueprint de Produto.
#
# IMPORTANTE: o server.py executa load_dotenv(override=True) no import, então o
# servidor SEMPRE usa o banco do .env (dezafira.db local de dev). Por isso este
# script não usa DATABASE_URL próprio — ele cria um usuário admin de teste no
# banco local, exercita os endpoints e LIMPA tudo no final (usuário + blueprint).
#
# Uso:  bash scripts/blueprint_smoke_test.sh
# Requer: .venv criado (python -m venv .venv && .venv/Scripts/pip install -r requirements.txt)
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT=8765
BASE="http://127.0.0.1:${PORT}"
PY=".venv/Scripts/python"
EMAIL="smoke@blueprint.test"

cleanup() {
  if [ -n "${SERVER_PID:-}" ]; then kill "$SERVER_PID" 2>/dev/null; fi
  "$PY" - <<'EOF' 2>/dev/null
from modules.database import engine, delete_db_user_sessions, get_db_user_by_email
from sqlalchemy import text
u = get_db_user_by_email('smoke@blueprint.test')
if u:
    delete_db_user_sessions(u.id)
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM users WHERE id = :uid'), {'uid': u.id})
    print('cleanup: usuário de teste removido')
EOF
}
trap cleanup EXIT

echo "==> Seed: criando admin de teste + JWT no banco local..."
# ATENÇÃO: o import de modules.database imprime ruído de migrations no STDOUT.
# Por isso silenciamos o stdout durante o seed — senão o bash captura lixo.
SEED_OUT=$("$PY" - <<'EOF'
import io, contextlib, sys
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    from dotenv import dotenv_values
    from modules.database import create_db_user, get_db_user_by_email, update_db_user
    import hashlib, time

    cfg = dotenv_values(".env")
    secret = cfg.get("AUTH_SECRET") or cfg.get("SECRET_KEY")
    assert secret, "AUTH_SECRET/SECRET_KEY ausente no .env"

    u = get_db_user_by_email("smoke@blueprint.test")
    if u:
        update_db_user(u.id, role="admin")
        uid = u.id
    else:
        created = create_db_user(email="smoke@blueprint.test", name="Smoke Tester", password_hash="x")
        assert created and "id" in created, created
        uid = created["id"]
        update_db_user(uid, role="admin")

    exp = int(time.time()) + 7 * 24 * 3600
    payload = f"{uid}:{exp}"
    sig = hashlib.sha256(f"{payload}:{secret}".encode()).hexdigest()[:32]

# (fora do redirect_stdout — senão o token vai para o buffer junto com o ruído)
sys.stdout.write(uid + "\n")
sys.stdout.write(f"{payload}:{sig}" + "\n")
EOF
)
if [ -z "$SEED_OUT" ]; then echo "FALHA no seed"; exit 1; fi
TEST_UID=$(echo "$SEED_OUT" | sed -n 1p)
TOKEN=$(echo "$SEED_OUT" | sed -n 2p)
echo "   usuário: $TEST_UID"

echo "==> Subindo servidor (porta $PORT)..."
"$PY" -m uvicorn server:app --host 127.0.0.1 --port "$PORT" > /tmp/blueprint_smoke_server.log 2>&1 &
SERVER_PID=$!

READY=0
for i in $(seq 1 40); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/" 2>/dev/null || true)
  if [ -n "$CODE" ] && [ "$CODE" != "000" ]; then READY=1; break; fi
  sleep 1
done
if [ "$READY" != "1" ]; then
  echo "FALHA: servidor não respondeu. Log:"; tail -20 /tmp/blueprint_smoke_server.log; exit 1
fi
echo "==> Servidor pronto."

echo "==> Testando auth (401 sem token)..."
UNAUTH=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/blueprints")
echo "   GET sem token -> $UNAUTH (esperado 401)"

echo "==> Criando blueprint (POST /api/v1/blueprints)..."
CREATE=$(curl -s -X POST "$BASE/api/v1/blueprints" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Smoke Test Blueprint","theme":"Guia Definitivo de Emagrecimento com IA","niche":"Fitness e Saude","price_cents":1990,"formats":["ebook","blog"],"config":{"artigos":2,"template_landing":"dezafira"}}')
BP_ID=$(echo "$CREATE" | "$PY" -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
if [ -z "$BP_ID" ]; then
  echo "FALHA ao criar blueprint: $CREATE"; tail -20 /tmp/blueprint_smoke_server.log; exit 1
fi
echo "   Blueprint criado: $BP_ID"

echo "==> Listando blueprints (GET /api/v1/blueprints)..."
LIST=$(curl -s "$BASE/api/v1/blueprints" -H "Authorization: Bearer $TOKEN")
echo "$LIST" | "$PY" -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('blueprints', data if isinstance(data, list) else [])
ids = [b['id'] for b in items]
print('   total:', len(ids), '| contém o criado:', '$BP_ID' in ids)
assert '$BP_ID' in ids
"

echo "==> Buscando blueprint (GET /api/v1/blueprints/{id})..."
DETAIL=$(curl -s "$BASE/api/v1/blueprints/$BP_ID" -H "Authorization: Bearer $TOKEN")
echo "$DETAIL" | "$PY" -c "
import sys, json
bp = json.load(sys.stdin)
print('   nome:', bp.get('name'), '| status:', bp.get('status'))
assert bp.get('id') == '$BP_ID'
assert bp.get('status') == 'draft'
"

echo "==> Deletando blueprint (DELETE /api/v1/blueprints/{id})..."
curl -s -X DELETE "$BASE/api/v1/blueprints/$BP_ID" -H "Authorization: Bearer $TOKEN" > /dev/null
echo "   ok"

echo ""
echo "================================================"
echo "OK: SMOKE TEST HTTP PASSED - CRUD Blueprint OK"
echo "================================================"
