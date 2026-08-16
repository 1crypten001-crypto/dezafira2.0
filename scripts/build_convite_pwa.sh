#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# build_convite_pwa.sh — Pipeline de build do PWA 1Convite
#
#   npm install  →  vite build  →  copia o bundle para web/1convite/dist/
#
# Depois do build, o middleware de Host-routing do server.py serve o SPA
# estático na raiz do domínio dedicado (1convite.com.br) — fallback para o
# PWA gerado dinamicamente enquanto não houver dist/.
#
# Uso:
#   bash scripts/build_convite_pwa.sh
#
# Requer: Node.js >= 20 (npm).
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/web/1convite/frontend"
DIST_SRC="$SRC/dist"
DIST_DEST="$ROOT/web/1convite/dist"

if ! command -v node >/dev/null 2>&1; then
  echo "❌ Node.js não encontrado no PATH. Instale Node >= 20 (https://nodejs.org) e tente de novo."
  echo "   Alternativa portátil: baixe o zip do Node para Windows/Linux e use o binário direto."
  exit 1
fi

NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$NODE_MAJOR" -lt 20 ]; then
  echo "❌ Node muito antigo ($(node -v)). O 1Convite exige Node >= 20."
  exit 1
fi

echo "── [1/4] npm install (web/1convite/frontend) ──"
cd "$SRC"
npm install --no-audit --no-fund

echo "── [2/4] vite build ──"
npm run build

if [ ! -f "$DIST_SRC/index.html" ]; then
  echo "❌ Build terminou sem gerar dist/index.html"
  exit 1
fi

echo "── [3/4] copiando dist/ → web/1convite/dist ──"
rm -rf "$DIST_DEST"
cp -r "$DIST_SRC" "$DIST_DEST"

echo "── [4/4] verificação ──"
if [ -f "$DIST_DEST/index.html" ]; then
  echo "✅ Bundle pronto em web/1convite/dist/ ($(du -sh "$DIST_DEST" | cut -f1))"
  echo "   O domínio 1convite.com.br agora serve o SPA na raiz (reinicie o server.py p/ limpar o cache de 30s)."
else
  echo "❌ Falha na cópia do bundle"
  exit 1
fi
