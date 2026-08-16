#!/usr/bin/env bash
# ============================================================================
# DEZAFIRA — Setup automatizado do ecossistema no Railway (CLI v3)
# ----------------------------------------------------------------------------
# Cria: libsql-server (banco da DezafiraClube + volume) e a DezafiraClube
#       (SvelteKit). O backend FastAPI já existe em produção — o script
#       apenas detecta e segue.
#
# USO:
#   1) Instale o CLI:   bash <(curl -fsSL railway.com/install.sh)
#   2) Login:           railway login
#   3) Exporte os secrets abaixo (NUNCA cole valores reais no script):
#        export SQLD_AUTH_JWT_KEY="$(openssl rand -hex 32)"
#        export ADMIN_USERNAME="admin"
#        export ADMIN_PASSWORD="sua-senha-forte"
#        export BACKEND_URL="https://backend-production-92e1.up.railway.app"
#        export GEMINI_API_KEY="sua-chave"          # opcional
#   4) Rode:  bash scripts/setup_railway.sh
#
# VARIAVEIS OPCIONAIS:
#   RAILWAY_PROJECT_NAME      nome do projeto (default: dezafira)
#   AUTO_ADD_DOMAIN=1         adiciona www.dezafira.com.br ao serviço do clube
#   LIBSQL_BOTTOMLESS_ENDPOINT / _AWS_ACCESS_KEY_ID / _AWS_SECRET_ACCESS_KEY /
#   _AWS_DEFAULT_REGION       credenciais do bucket (ver libsql-server/.env.example)
#                             — se setadas, o backup bottomless é ativado
# ============================================================================
set -euo pipefail

# Diretório do script (robusto a cwd/PATH — não usar $0 relativo)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ------------------------------- Config -------------------------------------
REPO="${RAILWAY_REPO:-1crypten001-crypto/dezafira2.0}"
BRANCH="${RAILWAY_BRANCH:-main}"
PROJECT_NAME="${RAILWAY_PROJECT_NAME:-dezafira}"
LIBSQL_SERVICE="libsql-server"
CLUBE_SERVICE="dezafiraclube"
BACKEND_SERVICE="backend"
LIBSQL_MOUNT="/var/lib/sqld"
BUCKET_NAME="dezafira-libsql-backups"
BUCKET_REGION="${LIBSQL_BOTTOMLESS_AWS_DEFAULT_REGION:-sjc}"
SITE_URL="${SITE_URL:-https://www.dezafira.com.br}"

log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m    ✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m    ⚠ %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# --------------------------- Pre-checks --------------------------------------
command -v railway >/dev/null 2>&1 || die "CLI do Railway não encontrado. Instale: bash <(curl -fsSL railway.com/install.sh)"
railway whoami >/dev/null 2>&1 || die "Não logado. Rode: railway login"

# Secrets obrigatórios
[ -n "${SQLD_AUTH_JWT_KEY:-}" ] || die "Defina SQLD_AUTH_JWT_KEY (ex.: export SQLD_AUTH_JWT_KEY=\$(openssl rand -hex 32))"
[ -n "${ADMIN_USERNAME:-}" ] || die "Defina ADMIN_USERNAME"
[ -n "${ADMIN_PASSWORD:-}" ] || die "Defina ADMIN_PASSWORD"

# --------------------------- Projeto ----------------------------------------
log "Projeto '$PROJECT_NAME'"
if ! railway status --json >/dev/null 2>&1; then
  railway init --name "$PROJECT_NAME" --yes >/dev/null 2>&1 || {
    warn "Não consegui criar o projeto automaticamente. Rode 'railway init' manualmente e repita o script."
    exit 1
  }
  ok "projeto criado"
else
  ok "projeto já vinculado"
fi

# --------------------------- Serviços ----------------------------------------
create_service() { # $1=nome
  local name="$1"
  if railway service --json 2>/dev/null | grep -q "$name"; then
    ok "serviço '$name' já existe"
  else
    log "Criando serviço '$name' (do repo $REPO)"
    railway add --repo "$REPO" --branch "$BRANCH" --service "$name" --json >/dev/null 2>&1 \
      && ok "serviço '$name' criado" \
      || warn "Falha ao criar '$name'. Crie manualmente: Railway → New Service → Deploy from GitHub (repo $REPO)"
  fi
}

create_service "$LIBSQL_SERVICE"
create_service "$CLUBE_SERVICE"

# Backend: só detecta — NUNCA cria (evita backend duplicado em produção)
log "Verificando backend (produção)"
if railway service --json 2>/dev/null | grep -q "$BACKEND_SERVICE"; then
  ok "backend já existe no projeto"
else
  warn "backend '$BACKEND_SERVICE' não encontrado com esse nome — verifique no dashboard se o serviço de produção tem outro nome (ex.: backend-production-92e1). Não vou criá-lo."
fi

log "Root Directory (faça no dashboard)"
warn "libsql-server → Settings → Source → Root Directory: libsql-server"
warn "dezafiraclube  → Settings → Source → Root Directory: Versões do dezafiraClub/Blog_Inteligente_SEO_com_IA_-_v1.9"
warn "backend        → já configurado (produção)"

# --------------------------- Volume do libsql --------------------------------
log "Volume persistente em $LIBSQL_MOUNT (libsql)"
if railway volume list --service "$LIBSQL_SERVICE" --json 2>/dev/null | grep -q '"id"'; then
  ok "volume já existe"
else
  railway volume add --service "$LIBSQL_SERVICE" --mount-path "$LIBSQL_MOUNT" --json >/dev/null 2>&1 \
    && ok "volume criado em $LIBSQL_MOUNT" \
    || warn "Crie o volume no dashboard: Service libsql-server → Volumes → Add Volume → $LIBSQL_MOUNT"
fi

# --------------------------- Variáveis do libsql -----------------------------
log "Variáveis do serviço libsql-server"
railway variable set SQLD_HTTP_LISTEN_ADDR=0.0.0.0:8080 --service "$LIBSQL_SERVICE" --json >/dev/null 2>&1 || true
railway variable set SQLD_AUTH_JWT_KEY="$SQLD_AUTH_JWT_KEY" --service "$LIBSQL_SERVICE" --json >/dev/null 2>&1 \
  && ok "SQLD_AUTH_JWT_KEY definida" || warn "não foi possível definir SQLD_AUTH_JWT_KEY"

# --------------------------- Bucket (backup) ---------------------------------
if [ -n "${LIBSQL_BOTTOMLESS_ENDPOINT:-}" ] && [ -n "${LIBSQL_BOTTOMLESS_AWS_ACCESS_KEY_ID:-}" ] && [ -n "${LIBSQL_BOTTOMLESS_AWS_SECRET_ACCESS_KEY:-}" ]; then
  log "Ativando backup bottomless → Railway Bucket"
  railway variable set SQLD_ENABLE_BOTTOMLESS_REPLICATION=true --service "$LIBSQL_SERVICE" --json >/dev/null 2>&1 || true
  railway variable set LIBSQL_BOTTOMLESS_BUCKET="$BUCKET_NAME" --service "$LIBSQL_SERVICE" --json >/dev/null 2>&1 || true
  railway variable set LIBSQL_BOTTOMLESS_ENDPOINT="$LIBSQL_BOTTOMLESS_ENDPOINT" --service "$LIBSQL_SERVICE" --json >/dev/null 2>&1 || true
  railway variable set LIBSQL_BOTTOMLESS_AWS_ACCESS_KEY_ID="$LIBSQL_BOTTOMLESS_AWS_ACCESS_KEY_ID" --service "$LIBSQL_SERVICE" --json >/dev/null 2>&1 || true
  railway variable set LIBSQL_BOTTOMLESS_AWS_SECRET_ACCESS_KEY="$LIBSQL_BOTTOMLESS_AWS_SECRET_ACCESS_KEY" --service "$LIBSQL_SERVICE" --json >/dev/null 2>&1 || true
  railway variable set LIBSQL_BOTTOMLESS_AWS_DEFAULT_REGION="$BUCKET_REGION" --service "$LIBSQL_SERVICE" --json >/dev/null 2>&1 || true
  railway variable set "LIBSQL_BOTTOMLESS_DATABASE_ID=${LIBSQL_BOTTOMLESS_DATABASE_ID:-ns-dezafiraclube}" --service "$LIBSQL_SERVICE" --json >/dev/null 2>&1 || true
  ok "backup bottomless configurado (namespace ${LIBSQL_BOTTOMLESS_DATABASE_ID:-ns-dezafiraclube})"
else
  warn "Backup bottomless pulado. Para ativar:"
  warn "  railway bucket create $BUCKET_NAME --region $BUCKET_REGION --json"
  warn "  railway bucket credentials --bucket $BUCKET_NAME --json"
  warn "  export LIBSQL_BOTTOMLESS_ENDPOINT / _AWS_ACCESS_KEY_ID / _AWS_SECRET_ACCESS_KEY e rode de novo"
fi

# --------------------------- Token + DezafiraClube ---------------------------
log "Gerando token de acesso (validade 1 ano)"
TOKEN="$(SQLD_AUTH_JWT_KEY="$SQLD_AUTH_JWT_KEY" node "$SCRIPT_DIR/../libsql-server/rotate-token.mjs")" \
  || die "Falha ao gerar token (precisa de node >= 16)"
ok "token gerado"

log "Variáveis do serviço $CLUBE_SERVICE"
DATABASE_URL="http://$LIBSQL_SERVICE.railway.internal:8080"
railway variable set "DATABASE_URL=$DATABASE_URL" --service "$CLUBE_SERVICE" --json >/dev/null 2>&1 || true
railway variable set "DATABASE_AUTH_TOKEN=$TOKEN" --service "$CLUBE_SERVICE" --json >/dev/null 2>&1 || true
railway variable set "SITE_URL=$SITE_URL" --service "$CLUBE_SERVICE" --json >/dev/null 2>&1 || true
railway variable set "ORIGIN=$SITE_URL" --service "$CLUBE_SERVICE" --json >/dev/null 2>&1 || true
railway variable set "BACKEND_URL=${BACKEND_URL:-https://backend-production-92e1.up.railway.app}" --service "$CLUBE_SERVICE" --json >/dev/null 2>&1 || true
railway variable set "ADMIN_USERNAME=$ADMIN_USERNAME" --service "$CLUBE_SERVICE" --json >/dev/null 2>&1 || true
railway variable set "ADMIN_PASSWORD=$ADMIN_PASSWORD" --service "$CLUBE_SERVICE" --json >/dev/null 2>&1 || true
[ -n "${GEMINI_API_KEY:-}" ] && railway variable set "GEMINI_API_KEY=$GEMINI_API_KEY" --service "$CLUBE_SERVICE" --json >/dev/null 2>&1 || true
ok "variáveis do $CLUBE_SERVICE definidas (URL interna $DATABASE_URL)"

# --------------------------- Domínios ----------------------------------------
log "Domínios"
railway domain --service "$LIBSQL_SERVICE" >/dev/null 2>&1 || true
railway domain --service "$CLUBE_SERVICE" >/dev/null 2>&1 || true
if [ "${AUTO_ADD_DOMAIN:-0}" = "1" ]; then
  railway domain www.dezafira.com.br --service "$CLUBE_SERVICE" >/dev/null 2>&1 \
    && ok "www.dezafira.com.br adicionado ao $CLUBE_SERVICE" \
    || warn "Adicione www.dezafira.com.br no dashboard (após apontar o DNS CNAME)"
fi
ok "URLs *.up.railway.app geradas — veja no dashboard (Settings → Domains)"

# --------------------------- Deploy ------------------------------------------
log "Deploy (a partir do diretório correto de cada serviço)"
warn "Caminho principal: defina os Root Directories no dashboard e faça push no repo — o Railway deploya sozinho."
if [ -d "$SCRIPT_DIR/../libsql-server" ]; then
  (cd "$SCRIPT_DIR/../libsql-server" && railway up --service "$LIBSQL_SERVICE" --detach >/dev/null 2>&1) \
    && ok "deploy local do libsql disparado" \
    || warn "deploy local do libsql não disparou (serviço GitHub?) — use push + Root Directory"
fi
if [ -d "$SCRIPT_DIR/../Versões do dezafiraClub/Blog_Inteligente_SEO_com_IA_-_v1.9" ]; then
  (cd "$SCRIPT_DIR/../Versões do dezafiraClub/Blog_Inteligente_SEO_com_IA_-_v1.9" && railway up --service "$CLUBE_SERVICE" --detach >/dev/null 2>&1) \
    && ok "deploy local do clube disparado" \
    || warn "deploy local do clube não disparou (serviço GitHub?) — use push + Root Directory"
fi

# --------------------------- Migração ----------------------------------------
log "Migração do blog.db (rode quando o libsql estiver online)"
warn "O banco local tem o branding DezafiraClube. Para migrar use a URL PÚBLICA do libsql:"
warn "  railway domain list --service $LIBSQL_SERVICE   # pegue o *.up.railway.app"  warn "  cd \"Versões do dezafiraClub/Blog_Inteligente_SEO_com_IA_-_v1.9\""
  warn "  DATABASE_URL=https://<libsql>.up.railway.app DATABASE_AUTH_TOKEN='$TOKEN' npx tsx scripts/migrate-sqlite-to-turso.ts"

log "Monitoramento"
warn "Healthcheck: libsql usa /health (Dockerfile) e o clube usa /healthz (checa o banco)."
warn "DR/restore: ver docs/backup_restore_libsql.md — teste o restore antes de precisar."

log "Setup concluído! ✅"
