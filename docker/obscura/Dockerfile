# Obscura — Serviço headless browser (Rust)
#
# Railway: Root Directory = /docker/obscura

FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl ca-certificates socat xvfb dbus-x11 python3 \
        libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 \
        libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
        libxshmfence1 libx11-xcb1 libxcb-dri3-0 libxss1 libxtst6 \
        fonts-liberation libgtk-3-0 libxkbcommon0 libwayland-client0 \
        libdbus-1-3 libexpat1 libxfixes3 libxext6 libx11-6 \
    && rm -rf /var/lib/apt/lists/*

ARG OBSCURA_VERSION=latest

RUN set -eux; \
    if [ "$OBSCURA_VERSION" = "latest" ]; then \
        URL="https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-linux-stealth.tar.gz"; \
    else \
        URL="https://github.com/h4ckf0r0day/obscura/releases/download/${OBSCURA_VERSION}/obscura-x86_64-linux-stealth.tar.gz"; \
    fi; \
    curl -sL --retry 3 --retry-delay 2 --connect-timeout 10 -o /tmp/obscura.tar.gz "$URL" || \
      (echo "ERRO: Falha ao baixar Obscura" >&2 && exit 1); \
    tar -tzf /tmp/obscura.tar.gz > /dev/null || \
      (echo "ERRO: Arquivo invalido" >&2 && exit 1); \
    mkdir -p /opt/obscura; \
    tar xzf /tmp/obscura.tar.gz -C /opt/obscura; \
    find /opt/obscura -type f -exec chmod +x {} \;; \
    rm -f /tmp/obscura.tar.gz; \
    BIN=$(find /opt/obscura -type f -executable | head -1); \
    test -n "$BIN" || (echo "ERRO: Binario nao encontrado" >&2 && exit 1); \
    "$BIN" --version 2>&1 || true

COPY entrypoint.sh /usr/local/bin/obscura_entrypoint.sh
RUN chmod +x /usr/local/bin/obscura_entrypoint.sh

# Proxy TCP unificado (substitui socat): 200 p/ qualquer caminho não-CDP em
# TODAS as portas candidatas (healthcheck do Railway passa em qualquer porta)
# + encaminha /json/* e /devtools/* para o CDP reescrevendo Host->127.0.0.1.
COPY cdp_proxy.py /usr/local/bin/cdp_proxy.py
RUN chmod +x /usr/local/bin/cdp_proxy.py

# O Railway injeta $PORT A PARTIR do EXPOSE e usa ESSA porta no healthcheck
# (healthcheckPort/[variables] no toml são ignorados). Fixamos EXPOSE 9000
# (porta do proxy, 200 p/ qualquer caminho) — o CDP real (9222) segue
# exposto pelo proxy só para a rede privada do backend.
EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -s -o /dev/null http://localhost:9222/json/version || exit 1

ENTRYPOINT ["/usr/local/bin/obscura_entrypoint.sh"]
