# 🌐 Chrome real (headless) — Serviço CDP para o bridge Dezafira
#
# ⚠️ IMPORTANTE (Railway): este arquivo deve se chamar EXATAMENTE "Dockerfile"
# para o Railpack detectar automaticamente. No Railway, crie um serviço com:
#   Root Directory = /SniperVideoEngine/docker/chrome
# e o build usa este Dockerfile sem configuração extra.
#
# Sobe o Chrome real com remote debugging na porta 9223, acessível pela
# rede privada do Railway (0.0.0.0). O bridge PREFERE este motor para o
# Google (SERP/PAA reais — o Chrome desbloqueia o anti-bot que o headless
# Rust não consegue); o Obscura (9222) fica como fallback automático.
#
# Env vars no backend:
#   OBSCURA_CHROME_HOST=chrome.railway.internal
#   OBSCURA_CHROME_PORT=9223                     (default)
#   OBSCURA_PROXY_URL=...                        (opcional — residencial)

FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget gnupg ca-certificates fonts-liberation \
       libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 libgbm1 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Instala o Google Chrome estável (fingerprint TLS real)
RUN set -eux; \
    wget -q -O /tmp/chrome.deb \
      https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb; \
    apt-get update && apt-get install -y --no-install-recommends /tmp/chrome.deb; \
    rm -f /tmp/chrome.deb; \
    rm -rf /var/lib/apt/lists/*

# Entrypoint na mesma pasta do Dockerfile (contexto de build = esta pasta)
COPY entrypoint.sh /usr/local/bin/chrome_entrypoint.sh
RUN chmod +x /usr/local/bin/chrome_entrypoint.sh

# Porta do CDP (remote debugging)
EXPOSE 9223

# Healthcheck nativo: o Chrome expõe /json/version via HTTP (CDP).
# O Railway marca o serviço como healthy só quando o CDP responde —
# evita o bridge tentar o Chrome antes de o remote debugging estar de pé.
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:9223/json/version || exit 1

ENTRYPOINT ["/usr/local/bin/chrome_entrypoint.sh"]
