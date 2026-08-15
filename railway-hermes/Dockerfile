# ─────────────────────────────────────────────────────────────────────────────
# Hermes Agent (Nous Research) — serviço Railway
# Imagem OFICIAL publicada no Docker Hub (nousresearch/hermes-agent).
# O 00-seed-config (cont-init.d) gera /opt/data/.env + config.yaml a partir
# das variáveis do Railway ANTES do bootstrap s6 (roda antes de 01-hermes-setup).
# ─────────────────────────────────────────────────────────────────────────────
# v0.20.1 (v2026.8.13) — atualização 2026-08-15: tag pinada da release nova
# (estava em :latest resolvendo v0.20.0 de 03/ago). Trocar tag = novo build.
FROM nousresearch/hermes-agent:v2026.8.13

COPY --chmod=0755 00-seed-config /etc/cont-init.d/00-seed-config
COPY --chmod=0755 start-hermes.sh /start-hermes.sh

# Comando principal: script de inicialização do gateway + dashboard
CMD ["/start-hermes.sh"]
