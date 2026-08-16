#!/usr/bin/env bash
#
# landing-via-cli.sh — Cria (e opcionalmente publica) uma landing page no
# DezafiraClube via a CLI API da v1.9: /api/cli/landing-pages
#
# Fluxo para o Hermes (ou qualquer agente) montar uma landing de oferta com
# PRODUTOS e POSTS REAIS do catálogo do Clube, sem abrir o builder visual.
#
# Requisitos: bash + curl + python3 (json).
#
# ─── Uso ─────────────────────────────────────────────────────────────────
#   CLUBE_URL=https://www.dezafira.com.br CLI_TOKEN=SEU_TOKEN \
#     ./landing-via-cli.sh \
#       --title "Guia Completo de Emagrecimento" \
#       --slug guia-completo-de-emagrecimento \
#       --product 42 \
#       --publish
#
# Flags:
#   --title  "..."   Título da landing (obrigatório)
#   --slug   slug    Slug/URL (opcional — derivado do título)
#   --product <id>   ID do produto para a oferta (opcional — usa o 1º do catálogo)
#   --posts  N       Quantos posts no bloco editorial (default 3, máx 6)
#   --publish        Publicar após criar (default: cria como draft)
#
# Saída: edit_url (admin) e public_url (/p/[slug]).
# ──────────────────────────────────────────────────────────────────────────

set -euo pipefail

BASE="${CLUBE_URL:-}"
TOKEN="${CLI_TOKEN:-}"
TITLE=""
SLUG=""
PRODUCT_ID=""
POSTS_N=3
PUBLISH=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title)   TITLE="$2";    shift 2 ;;
    --slug)    SLUG="$2";     shift 2 ;;
    --product) PRODUCT_ID="$2"; shift 2 ;;
    --posts)   POSTS_N="$2";  shift 2 ;;
    --publish) PUBLISH=1;     shift ;;
    --draft)   PUBLISH=0;     shift ;;
    *) echo "❌ Flag desconhecida: $1" >&2; exit 2 ;;
  esac
done

# ── Pré-checks ──────────────────────────────────────────────────────────
[[ -z "$BASE" ]]  && { echo "❌ Defina CLUBE_URL (ex: export CLUBE_URL=https://www.dezafira.com.br)" >&2; exit 2; }
[[ -z "$TOKEN" ]] && { echo "❌ Defina CLI_TOKEN (Admin → CLI & API → Regenerar Token)" >&2; exit 2; }
[[ -z "$TITLE" ]] && { echo "❌ Informe --title \"...\"" >&2; exit 2; }
command -v python3 >/dev/null || { echo "❌ Precisa de python3 para montar o JSON." >&2; exit 2; }

AUTH=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")
echo "🔑 Conectando em $BASE ..."

# ── 1. Buscar recursos reais (produtos + posts) ─────────────────────────
RESP=$(curl -fsS "${AUTH[@]}" "$BASE/api/cli/landing-pages/resources") || {
  echo "❌ Falha em GET /api/cli/landing-pages/resources (token inválido? URL errada?)" >&2; exit 1; }

# ── 2. Montar blocks com python3 (produto + posts reais) ────────────────
BLOCKS=$(PRODUCT_ID="${PRODUCT_ID:-}" POSTS_N="$POSTS_N" CLI_TITLE="$TITLE" python3 -c '
import json, os, sys

data = json.load(sys.stdin)
products = data.get("products") or []
posts = data.get("posts") or []

pid = os.environ.get("PRODUCT_ID", "")
prod = next((p for p in products if str(p.get("id")) == str(pid)), None) if pid else (products[0] if products else None)
if not prod:
    print("SEM_PRODUCTO", file=sys.stderr); sys.exit(1)

try:
    n = max(0, min(int(os.environ.get("POSTS_N", "3")), 6))
except ValueError:
    n = 3
sel_posts = posts[:n]

blocks = [
  {"id": "hero", "type": "hero", "properties": {
      "eyebrow": "Guia Completo",
      "title": os.environ["CLI_TITLE"],
      "subtitle": "Tudo o que você precisa saber, direto ao ponto.",
      "primaryText": "Quero este guia",
      "primaryHref": f"/product/{prod[\"slug\"]}",
      "secondaryText": "Ver o catálogo",
      "secondaryHref": "/products"}},
  {"id": "oferta", "type": "product-showcase", "properties": {
      "productId": prod.get("id"), "productSlug": prod.get("slug"),
      "name": prod.get("name"),
      "description": prod.get("description") or "Conteúdo completo e direto ao ponto.",
      "price": None,
      "buttonText": "Garantir acesso",
      "buttonHref": f"/product/{prod[\"slug\"]}"}},
  {"id": "conteudo", "type": "posts-grid", "properties": {
      "title": "Conteúdo relacionado", "subtitle": "Leia também",
      "posts": [{"id": p.get("id"), "title": p.get("title"), "slug": p.get("slug"),
                  "excerpt": p.get("excerpt", ""), "cover_image": p.get("cover_image", ""),
                  "href": f"/post/{p[\"slug\"]}"} for p in sel_posts]}},
  {"id": "faq", "type": "faq", "properties": {
      "title": "Perguntas frequentes",
      "items": [
        {"q": "Como recebo o acesso?", "a": "O acesso é liberado automaticamente após a compra, direto na sua área de membros."},
        {"q": "É vitalício?", "a": "Sim — quem compra avulso mantém o acesso definitivo."}]}},
  {"id": "cta", "type": "cta", "properties": {
      "subtitle": "Não perca a oportunidade",
      "buttonText": "Quero começar agora",
      "buttonHref": f"/product/{prod[\"slug\"]}"}},
]

print(json.dumps({"title": os.environ["CLI_TITLE"], "status": "draft", "blocks": blocks},
                 ensure_ascii=False))
' <<<"$RESP") || {
  if echo "$BLOCKS" | grep -q SEM_PRODUCTO; then
    echo "❌ Catálogo vazio — crie um produto no Clube antes." >&2
  else
    echo "❌ Falha ao montar a landing." >&2
  fi
  exit 1; }

# ── 3. Slug ─────────────────────────────────────────────────────────────
if [[ -n "$SLUG" ]]; then
  BODY=$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); d["slug"]=sys.argv[2]; print(json.dumps(d, ensure_ascii=False))' "$BLOCKS" "$SLUG")
else
  BODY="$BLOCKS"
fi

# ── 4. Criar (draft) ────────────────────────────────────────────────────
RESP=$(curl -fsS -X POST "${AUTH[@]}" -d "$BODY" "$BASE/api/cli/landing-pages") || {
  echo "❌ Falha ao criar a landing (400 = dados inválidos; 409 = slug em uso)." >&2
  exit 1; }

LID=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("id", ""))' <<<"$RESP")
LSLUG=$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("slug", ""))' <<<"$RESP")

echo ""
echo "✅ Landing criada (draft):"
echo "   🆔 ID:      $LID"
echo "   ✏️  Editor:  $BASE/admin/landing-pages/$LID"
echo "   🌐 Preview: $BASE/p/$LSLUG"

# ── 5. Publicar (opcional) ──────────────────────────────────────────────
if [[ "$PUBLISH" == "1" ]]; then
  curl -fsS -X PUT "${AUTH[@]}" -d '{"status":"published"}' "$BASE/api/cli/landing-pages/$LID" >/dev/null || {
    echo "❌ Falha ao publicar." >&2; exit 1; }
  echo "   🚀 Publicada em: $BASE/p/$LSLUG"
fi

echo ""
echo "💡 Guia completo: docs/integracao-adm-clube.md"
