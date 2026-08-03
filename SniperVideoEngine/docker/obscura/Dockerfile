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
#
# ──────────────────────────────────────────────────────────────────────────────
# VERSIONAMENTO:
#   OBSCURA_VERSION pina a versão do binário para builds reproduzíveis.
#   Para atualizar: ajuste o ARG OBSCURA_VERSION abaixo e faça redeploy.
#   Verifique as releases em: https://github.com/h4ckf0r0day/obscura/releases
# ──────────────────────────────────────────────────────────────────────────────

FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates tar socat \
    && rm -rf /var/lib/apt/lists/*

# Pina a versão do binário stealth (TLS impersonation) para builds reproduzíveis.
# "latest" pode quebrar silenciosamente se uma nova release for incompatível.
# Para atualizar: troque o valor de OBSCURA_VERSION abaixo.
ARG OBSCURA_VERSION=latest

RUN set -eux; \
    if [ "$OBSCURA_VERSION" = "latest" ]; then \
        URL="https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-linux-stealth.tar.gz"; \
    else \
        URL="https://github.com/h4ckf0r0day/obscura/releases/download/${OBSCURA_VERSION}/obscura-x86_64-linux-stealth.tar.gz"; \
    fi; \
    echo "[Dockerfile] Baixando Obscura de: $URL"; \
    curl -sL --retry 3 --retry-delay 2 --connect-timeout 10 -o /tmp/obscura.tar.gz "$URL" || \
      (echo "ERRO: Falha ao baixar Obscura ${OBSCURA_VERSION}" >&2 && exit 1); \
    # Valida com tar -tzf (list-only): falha se o arquivo for HTML/404 em vez de tar.gz
    tar -tzf /tmp/obscura.tar.gz > /dev/null || \
      (echo "ERRO: Arquivo baixado nao e um tar.gz valido (possivel 404 ou redirect)" >&2 && exit 1); \
    mkdir -p /opt/obscura; \
    tar xzf /tmp/obscura.tar.gz -C /opt/obscura; \
    find /opt/obscura -type f -exec chmod +x {} \;; \
    rm -f /tmp/obscura.tar.gz; \
    BIN=$(find /opt/obscura -type f -executable | head -1); \
    test -n "$BIN" || (echo "ERRO: Binario do Obscura nao encontrado apos extracao" >&2 && exit 1); \
    echo "[Dockerfile] Obscura instalado em: $BIN"; \
    "$BIN" --version 2>&1 || echo "[Dockerfile] --version nao suportado (ok)"

# Entrypoint na mesma pasta do Dockerfile (contexto de build = esta pasta)
COPY entrypoint.sh /usr/local/bin/obscura_entrypoint.sh
RUN chmod +x /usr/local/bin/obscura_entrypoint.sh

# Porta do servidor CDP (WebSocket)
EXPOSE 9222

# Healthcheck nativo: o motor expõe /json/version via HTTP (CDP).
# O Railway marca o serviço como healthy só quando o CDP responde —
# evita o backend tentar usar o Obscura antes de ele estar de pé.
# start-period=25s: tempo para o binário inicializar e abrir o servidor CDP.
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD curl -fsS http://localhost:9222/json/version > /dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/obscura_entrypoint.sh"]
