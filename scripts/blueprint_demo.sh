#!/usr/bin/env bash
# ============================================================================
# 🎯 Blueprint — Demonstração / E2E via API (sandbox)
#
# Fluxo: criar receita → rodar motor → aguardar revisão → (opcional) publicar
#
# Uso:
#   API=http://localhost:8000 TOKEN=<seu-jwt-admin> \
#     ./scripts/blueprint_demo.sh "Guia de IA para Iniciantes" "Tecnologia & IA"
#
# Para publicar de verdade no Clube, adicione: PUBLISH=1
# (exige CLUBE_IMPORT_KEY + CLI_TOKEN no .env do Adm e IMPORT_API_KEY no Clube)
# ============================================================================
set -euo pipefail

API="${API:-http://localhost:8000}"
TOKEN="${TOKEN:?Defina TOKEN (JWT admin) no ambiente}"
THEME="${1:?Uso: blueprint_demo.sh \"Tema do Produto\" \"Nicho\"}"
NICHE="${2:-Tecnologia & IA}"
PUBLISH="${PUBLISH:-0}"
POLL_INTERVAL="${POLL_INTERVAL:-5}"

auth=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")

echo "🎯 Blueprint: $THEME ($NICHE)"

# 1. Criar receita
BP=$(curl -s -X POST "$API/api/v1/blueprints" "${auth[@]}" -d "{
  \"name\": \"$THEME\",
  \"theme\": \"$THEME\",
  \"niche\": \"$NICHE\",
  \"price_cents\": 1990,
  \"formats\": [\"ebook\", \"blog\"],
  \"config\": {\"artigos\": 2, \"template_landing\": \"dezafira\"}
}")
BP_ID=$(echo "$BP" | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "📦 Blueprint criado: $BP_ID"

# 2. Disparar o motor
curl -s -X POST "$API/api/v1/blueprints/$BP_ID/run" "${auth[@]}" >/dev/null
echo "⚡ Motor iniciado — aguardando revisão (polling ${POLL_INTERVAL}s)..."

# 3. Polling até review/published/failed
while true; do
  STATE=$(curl -s "$API/api/v1/blueprints/$BP_ID" "${auth[@]}")
  STATUS=$(echo "$STATE" | python -c "import sys,json;print(json.load(sys.stdin).get('status'))")
  STAGE=$(echo "$STATE" | python -c "import sys,json;print(json.load(sys.stdin).get('stage') or '')")
  echo "   status=$STATUS · estágio=$STAGE"
  case "$STATUS" in
    review) echo "👀 Em revisão — abra /admin/blueprint/$BP_ID para revisar os assets."; break ;;
    failed) echo "❌ Falhou:"; echo "$STATE" | python -c "import sys,json;print(json.load(sys.stdin).get('error'))"; exit 1 ;;
    published) echo "✅ Já publicado."; break ;;
    *) sleep "$POLL_INTERVAL" ;;
  esac
done

# 4. Publicar (opcional)
if [ "$PUBLISH" = "1" ]; then
  echo "🚀 Publicando no Clube..."
  RES=$(curl -s -X POST "$API/api/v1/blueprints/$BP_ID/publish" "${auth[@]}")
  echo "$RES" | python -c "import sys,json; d=json.load(sys.stdin); print('status:', d.get('status')); [print(f\"   {k}: {v.get('status')} — {v.get('detail','')[:80]}\") for k,v in (d.get('publish_log') or {}).items()]"
fi

echo "🔗 UI: http://localhost:3000/admin/blueprint/$BP_ID"
