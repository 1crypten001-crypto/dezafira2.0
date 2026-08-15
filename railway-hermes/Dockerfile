# ─────────────────────────────────────────────────────────────────────────────
# Hermes Agent (Nous Research) — serviço Railway
# Imagem OFICIAL publicada no Docker Hub (nousresearch/hermes-agent).
# O 00-seed-config (cont-init.d) gera /opt/data/.env + config.yaml a partir
# das variáveis do Railway ANTES do bootstrap s6 (roda antes de 01-hermes-setup).
# ─────────────────────────────────────────────────────────────────────────────
# v0.20.1 (v2026.8.13) — atualização em 2026-08-15: touch para invalidar cache
# e puxar imagem `latest` nova (v0.20.0 → v0.20.1, ~1.444 commits de fix).
FROM nousresearch/hermes-agent:latest

COPY --chmod=0755 00-seed-config /etc/cont-init.d/00-seed-config
COPY --chmod=0755 start-hermes.sh /start-hermes.sh

# Comando principal: script de inicialização do gateway + dashboard
CMD ["/start-hermes.sh"]
