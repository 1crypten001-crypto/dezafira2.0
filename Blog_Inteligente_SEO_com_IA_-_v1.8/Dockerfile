# ============================================================================
# DEZAFIRACLUBE — SvelteKit (adapter-node) — Dockerfile para Railway
# Build multi-stage: node deps → build → runtime enxuto
#
# NOTA: usa node:20-slim (Debian/glibc) e NÃO Alpine — better-sqlite3 é um
# módulo nativo que só tem prebuild para glibc; no Alpine (musl) o npm ci
# falharia por falta de toolchain (python3/make/g++).
# ============================================================================

# Stage 1: Dependências + Build
FROM node:20-slim AS builder
WORKDIR /app

# Copia manifests e instala (inclui devDeps para o build)
COPY package.json package-lock.json ./
RUN npm ci --include=dev

# Copia o source e builda
COPY . .
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Runtime
FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production

# Só o que o adapter-node precisa para rodar
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules

# Banco local (fallback p/ dev; em produção use DATABASE_URL do Turso)
# blog.db versionado no repo — copiado para o runtime
COPY blog.db ./blog.db

EXPOSE 3000

# adapter-node lê a $PORT do Railway automaticamente (PORT)
CMD ["node", "build/index.js"]
