# ============================================================================
# DEZAFIRA ADM — Frontend (Next.js 14)
# Multi-stage build para Railway
# ============================================================================

# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app

# Bust Docker cache
ARG CACHEBUST=1

# Instalar dependencias
COPY package*.json ./
RUN npm ci

# Copiar codigo e buildar
# NEXT_PUBLIC_API_URL precisa existir DURANTE o build (Next.js inlina NEXT_PUBLIC_*)
ARG NEXT_PUBLIC_API_URL=https://dezafiraadm-production.up.railway.app
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
COPY . .
RUN rm -rf .next && npm run build


# Stage 2: Production
FROM node:20-alpine AS runner
WORKDIR /app

# Copiar build output
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

ENV NODE_ENV=production

CMD ["npm", "start"]
