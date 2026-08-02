# 🕵️ Obscura — Serviço exclusivo do motor headless (Rust, ~30MB RAM)
#
# ⚠️ IMPORTANTE (Railway): este arquivo deve se chamar EXATAMENTE "Dockerfile"
# para o Railpack detectar automaticamente. No Railway, crie um serviço com:
#   Root Directory = /SniperVideoEngine/docker/obscura
# e o build usa este Dockerfile sem configuração extra.
#
# Usa uma base com shell (debian slim) para o entrypoint conseguir ler
# OBSCURA_PROXY_URL e adicionar --proxy condicionalmente — a imagem
# oficial é distroless (sem shell), então aqui baixamos o MESMO binário
# das releases (mesmo fluxo do start_obscura_local.bat).
#
# O backend Python alcança este serviço pela rede privada do Railway:
#   http://obscura.railway.internal:9222
#
# Env vars suportadas:
#   OBSCURA_PORT       (default 9222)
#   OBSCURA_WORKERS    (default 4)
#   OBSCURA_PROXY_URL  (opcional — residencial: http://user:pass@host:port)

FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates tar \
    && rm -rf /var/lib/apt/lists/*

# Baixa o binário stealth (TLS impersonation) das releases oficiais
ARG OBSCURA_VERSION=latest
RUN set -eux; \
    URL="https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-linux-stealth.tar.gz"; \
    curl -sL -o /tmp/obscura.tar.gz "$URL"; \
    mkdir -p /opt/obscura; \
    tar xzf /tmp/obscura.tar.gz -C /opt/obscura; \
    find /opt/obscura -type f -exec chmod +x {} \;; \
    rm -f /tmp/obscura.tar.gz

# Entrypoint na mesma pasta do Dockerfile (contexto de build = esta pasta)
COPY entrypoint.sh /usr/local/bin/obscura_entrypoint.sh
RUN chmod +x /usr/local/bin/obscura_entrypoint.sh

# Porta do servidor CDP (WebSocket)
EXPOSE 9222

# Healthcheck nativo: o motor expõe /json/version via HTTP (CDP).
# O Railway marca o serviço como healthy só quando o CDP responde —
# evita o backend tentar usar o Obscura antes de ele estar de pé.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:9222/json/version >/dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/obscura_entrypoint.sh"]
