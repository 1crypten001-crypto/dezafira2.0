#!/usr/bin/env bash
# ============================================================================
# DEZAFIRA — Restaura o banco do libsql-server a partir do bucket bottomless.
# ----------------------------------------------------------------------------
# O QUE FAZ:
#   1. Baixa a geração mais recente do bucket S3 (Railway Bucket)
#   2. Verifica a integridade (PRAGMA integrity_check — o bottomless-cli faz)
#   3. Faz backup do banco atual e o substitui pelo restaurado
#
# COMO USAR (o sqld DEVE estar parado):
#   Container temporário (recomendado — não dá pra ssh em serviço parado):
#     1) Railway → New Service → Docker Image: ghcr.io/tursodatabase/libsql-server:v0.24.32
#        (copie as variáveis LIBSQL_BOTTOMLESS_* do serviço de produção)
#     2) Suba este script e rode:
#        railway volume files upload ./restore.sh /restore.sh --service <servico-temp>
#        railway ssh --service <servico-temp>
#        bash /restore.sh
#     3) Envie o banco restaurado de volta para o volume de produção:
#        railway volume files upload /var/lib/sqld/iku.db /var/lib/sqld/iku.db --service libsql-server
#
# Detalhe: LIBSQL_BOTTOMLESS_DATABASE_ID (namespace) precisa ser IGUAL ao
# usado no backup — o padrão é "ns-default". Se o serviço usa outro valor,
# exporte antes:  export LIBSQL_BOTTOMLESS_DATABASE_ID=ns-dezafiraclube
# ============================================================================
set -euo pipefail

DB_PATH="${SQLD_DB_PATH:-/var/lib/sqld/iku.db}"
RESTORE_DIR="/tmp/libsql-restore"

[ -x /bin/bottomless-cli ] || { echo "✗ bottomless-cli não encontrado neste container"; exit 1; }

# Detecta sqld rodando sem depender de pgrep (imagem slim pode não ter procps)
for comm in /proc/[0-9]*/comm; do
  [ "$(cat "$comm" 2>/dev/null || true)" = "sqld" ] && {
    echo "⚠  O sqld está RODANDO. Para um restore seguro:"
    echo "   1) Railway → Service libsql-server → Deployments → pare/delete a instância atual"
    echo "   2) Rode este script num container temporário OU reinicie o serviço depois"
    exit 1
  }
done

rm -rf "$RESTORE_DIR" && mkdir -p "$RESTORE_DIR"
cd "$RESTORE_DIR"

echo "==> Restaurando a geração mais recente do bucket bottomless..."
/bin/bottomless-cli restore

RESTORED="$(find . -name data -type f | head -1)"
[ -n "$RESTORED" ] || { echo "✗ arquivo restaurado não encontrado"; exit 1; }
echo "==> Restaurado (e verificado) em: $RESTORED"

if [ -f "$DB_PATH" ]; then
  cp "$DB_PATH" "${DB_PATH}.pre-restore.bak"
  echo "==> Backup do banco atual: ${DB_PATH}.pre-restore.bak"
fi

install -m 0644 "$RESTORED" "$DB_PATH"

# ⚠️ CRÍTICO: remover WAL/SHM antigos — senão o SQLite tenta replay do WAL
# antigo contra o arquivo restaurado (corrupção). O restore do bottomless
# produz um arquivo único auto-contido (WAL já aplicado).
rm -f "$DB_PATH-wal" "$DB_PATH-shm" "$DB_PATH-wal2" "$DB_PATH-shm2"

echo "==> ✅ Banco restaurado em $DB_PATH (WAL/SHM antigos removidos)"
echo "==> Inicie o sqld (deploy/redeploy) — ele retoma a replicação bottomless."
