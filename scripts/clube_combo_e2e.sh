#!/usr/bin/env bash
# E2E do Combo/Pacote nativo no DezafiraClube
#
# Fluxo real validado:
#   1. Sobe o Clube local (SvelteKit dev, DB isolado .e2e_clube.db)
#   2. Importa 2 produtos (itens) + 1 pacote (bundle_items) via /api/import/product
#   3. Confere bundle_items persistidos no banco
#   4. Simula compra: product_purchases 'pending' + webhook Asaas PAYMENT_CONFIRMED
#   5. Verifica: compra → completed e itens do pacote DESBLOQUEADOS (completed)
#   6. Página pública /product/{slug} do pacote responde 200 (vitrine do combo)
#   7. Cleanup total (server + banco)
#
# Uso: bash scripts/clube_combo_e2e.sh
# Requer node (usa o portátil em .tools/node se existir).

set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLUBE="$ROOT/Versões do dezafiraClub/Blog_Inteligente_SEO_com_IA_-_v1.9"
DB="$CLUBE/.e2e_clube.db"
PORT=5173
IMPORT_KEY="e2e-import-key-123"
WEBHOOK_SECRET="e2e-webhook-secret-456"
PASS=0
FAIL=0

# ── Node portátil (se disponível) ───────────────────────────────────────────
# Prefere a versão que casa com os módulos nativos do Clube (better-sqlite3
# é compilado contra o Node 22 — NODE_MODULE_VERSION 127).
if [ -z "${NODE_DIR:-}" ] && [ -x "$ROOT/.tools/node/node-v22.23.2-win-x64/node.exe" ]; then
  NODE_DIR="$ROOT/.tools/node/node-v22.23.2-win-x64"
elif [ -z "${NODE_DIR:-}" ] && [ -x "$ROOT/.tools/node/node.exe" ]; then
  NODE_DIR="$ROOT/.tools/node"
fi
if [ -n "${NODE_DIR:-}" ] && [ -x "$NODE_DIR/node.exe" ]; then
  export PATH="$NODE_DIR:$PATH"
fi
if ! command -v node >/dev/null 2>&1; then
  echo "✗ node não disponível. Baixe o portátil para .tools/node ou instale o Node."
  exit 2
fi
NODE_BIN="$(command -v node)"
echo "✓ node: $NODE_BIN ($(node -v))"

ok()   { echo "  ✓ $1"; PASS=$((PASS+1)); }
bad()  { echo "  ✗ $1"; FAIL=$((FAIL+1)); }

# ── Cleanup inicial ──────────────────────────────────────────────────────────
cleanup() {
  if [ -n "${SERVER_PID:-}" ]; then kill "$SERVER_PID" 2>/dev/null; fi
  sleep 2  # libera o lock do banco no Windows antes de remover
  for i in 1 2 3; do rm -f "$DB" "$DB-wal" "$DB-shm" 2>/dev/null && break; sleep 1; done
}
trap cleanup EXIT
cleanup

export E2E_DB="$DB"

# ── Sobe o Clube ─────────────────────────────────────────────────────────────
echo "==> Subindo o Clube (porta $PORT, DB isolado)..."
cd "$CLUBE" || { echo "✗ Clube não encontrado"; exit 1; }
DATABASE_PATH="$DB" IMPORT_API_KEY="$IMPORT_KEY" ASAAS_WEBHOOK_SECRET="$WEBHOOK_SECRET" \
  "$NODE_BIN" node_modules/vite/bin/vite.js dev --port "$PORT" --strictPort > /tmp/clube_e2e.log 2>&1 &
SERVER_PID=$!

for i in $(seq 1 60); do
  if curl -s -o /dev/null "http://localhost:$PORT"; then break; fi
  sleep 1
done
if ! curl -s -o /dev/null "http://localhost:$PORT"; then
  echo "✗ Clube não subiu. Log:"; tail -15 /tmp/clube_e2e.log
  exit 1
fi
echo "✓ Clube no ar"

# ── Seed: usuário (via better-sqlite3 do próprio Clube) ─────────────────────
echo "==> Seed do usuário e2e..."
node - <<'EOF' || { echo "✗ seed falhou"; exit 1; }
const Database = require('better-sqlite3');
const db = new Database(process.env.E2E_DB);
try {
  db.prepare("INSERT OR IGNORE INTO users (username, password, role) VALUES ('e2e@combo.test', 'x', 'member')").run();
  const u = db.prepare("SELECT id FROM users WHERE username='e2e@combo.test'").get();
  console.log("USER_ID=" + u.id);
} finally { db.close(); }
EOF
USER_ID=$(node - <<'EOF'
const Database = require('better-sqlite3');
const db = new Database(process.env.E2E_DB);
try { console.log(db.prepare("SELECT id FROM users WHERE username='e2e@combo.test'").get().id); } finally { db.close(); }
EOF
)
[ -n "$USER_ID" ] && ok "usuário criado (id $USER_ID)" || bad "usuário não criado"

# ── Import dos produtos + pacote ─────────────────────────────────────────────
echo "==> Import via /api/import/product..."
import_p() { # $1=name $2=price $3=bundle_json(opcional)
  local payload="{\"name\":\"$1\",\"price_cents\":$2,\"resource_type\":\"link\",\"external_link\":\"/checkout\"${3:+,$3}}"
  curl -s -X POST "http://localhost:$PORT/api/import/product" \
    -H "Content-Type: application/json" -H "x-import-key: $IMPORT_KEY" \
    -d "$payload"
}

R_A=$(import_p "Item A E2E" 1000)
ID_A=$(echo "$R_A" | node -pe "JSON.parse(require('fs').readFileSync(0)).product_id")
[ -n "$ID_A" ] && ok "Item A importado (id $ID_A)" || bad "Item A falhou: $R_A"

R_B=$(import_p "Item B E2E" 500)
ID_B=$(echo "$R_B" | node -pe "JSON.parse(require('fs').readFileSync(0)).product_id")
[ -n "$ID_B" ] && ok "Item B importado (id $ID_B)" || bad "Item B falhou: $R_B"

R_C=$(import_p "Pacote Completo E2E" 1200 "\"bundle_items\":[$ID_A,$ID_B]")
ID_C=$(echo "$R_C" | node -pe "JSON.parse(require('fs').readFileSync(0)).product_id")
[ -n "$ID_C" ] && ok "Pacote importado (id $ID_C)" || bad "Pacote falhou: $R_C"

# Validação do pacote no banco
ITEMS_DB=$(node - <<EOF
const Database = require('better-sqlite3');
const db = new Database(process.env.E2E_DB);
try { console.log(db.prepare('SELECT bundle_items FROM products WHERE id=?').get($ID_C).bundle_items); } finally { db.close(); }
EOF
)
echo "$ITEMS_DB" | grep -q "$ID_A" && echo "$ITEMS_DB" | grep -q "$ID_B" \
  && ok "bundle_items persistidos: $ITEMS_DB" || bad "bundle_items ausentes: $ITEMS_DB"

# Bundle inválido (item que não existe) → 400
R_BAD=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:$PORT/api/import/product" \
  -H "Content-Type: application/json" -H "x-import-key: $IMPORT_KEY" \
  -d '{"name":"Bad","price_cents":100,"resource_type":"link","external_link":"/checkout","bundle_items":[999999,999998]}')
[ "$R_BAD" = "400" ] && ok "bundle com item inexistente → 400" || bad "esperava 400, veio $R_BAD"

# ── Simula compra do pacote + webhook Asaas ─────────────────────────────────
echo "==> Simulando compra + webhook Asaas..."
node - <<EOF || { echo "✗ seed compra falhou"; exit 1; }
const Database = require('better-sqlite3');
const db = new Database(process.env.E2E_DB);
try {
  db.prepare("INSERT INTO product_purchases (user_id, product_id, product_name_snapshot, price_cents, asaas_payment_id, status) VALUES (?, ?, 'Pacote Completo E2E', 1200, 'e2e_asaas_fake', 'pending')").run($USER_ID, $ID_C);
} finally { db.close(); }
EOF
ok "compra do pacote criada (pending)"

curl -s -X POST "http://localhost:$PORT/api/webhook/asaas" \
  -H "Content-Type: application/json" -H "asaas-access-token: $WEBHOOK_SECRET" \
  -d '{"event":"PAYMENT_CONFIRMED","payment":{"id":"e2e_asaas_fake","subscription":null}}' > /dev/null

# Verifica status + desbloqueio
RESULT=$(node - <<EOF
const Database = require('better-sqlite3');
const db = new Database(process.env.E2E_DB);
try {
  const bundle = db.prepare("SELECT status FROM product_purchases WHERE asaas_payment_id='e2e_asaas_fake'").get();
  const items = db.prepare("SELECT product_id, status FROM product_purchases WHERE user_id=? AND product_id IN (?, ?) AND status='completed'").all($USER_ID, $ID_A, $ID_B);
  console.log(JSON.stringify({ bundle: bundle && bundle.status, unlocked: items.map(i => i.product_id).sort() }));
} finally { db.close(); }
EOF
)
CHECK=$(echo "$RESULT" | node -e "
const r = JSON.parse(require('fs').readFileSync(0));
const okBundle = r.bundle === 'completed';
const items = (r.unlocked || []).map(Number);
const okItems = items.includes($ID_A) && items.includes($ID_B);
console.log(okBundle && okItems ? 'PASS' : 'FAIL');
")
if [ "$CHECK" = "PASS" ]; then
  ok "compra → completed + itens $ID_A/$ID_B desbloqueados: $RESULT"
else
  bad "desbloqueio incompleto: $RESULT"
fi

# ── Página pública do pacote ────────────────────────────────────────────────
echo "==> Página pública /product/{slug}..."
SLUG=$(node - <<EOF
const Database = require('better-sqlite3');
const db = new Database(process.env.E2E_DB);
try { console.log(db.prepare('SELECT slug FROM products WHERE id=?').get($ID_C).slug); } finally { db.close(); }
EOF
)
CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/product/$SLUG")
[ "$CODE" = "200" ] && ok "/product/$SLUG → 200 (vitrine do combo)" || bad "/product/$SLUG → $CODE"

# ── Resumo ───────────────────────────────────────────────────────────────────
echo ""
echo "================================================"
if [ "$FAIL" = "0" ]; then
  echo "OK: E2E COMBO/PACOTE PASSED ($PASS checks)"
else
  echo "FALHOU: $FAIL checks falharam ($PASS passaram)"
fi
echo "================================================"
exit $([ "$FAIL" = "0" ] && echo 0 || echo 1)
