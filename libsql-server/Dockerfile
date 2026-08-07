# ============================================================================
# DEZAFIRA — libsql-server (SQLite na nuvem, mesmo motor do Turso)
# Serviço de banco da DezafiraClube dentro do próprio Railway.
# ============================================================================
# Versão pinada (reproduzível). Atualize testando antes: troque a tag e redeploye.
FROM ghcr.io/tursodatabase/libsql-server:v0.24.32

# O sqld escuta em 8080 por padrão (mesmo valor da imagem). Manter explícito
# para o Railway detectar a porta correta via EXPOSE (não depende de $PORT).
ENV SQLD_HTTP_LISTEN_ADDR=0.0.0.0:8080

# Dados persistentes (monte um Volume do Railway AQUI — é o SQLD_DB_PATH padrão)
VOLUME /var/lib/sqld

# Apenas HTTP: o @libsql/client conecta via http:// (ou ws://). Sem gRPC —
# porta extra poderia confundir a detecção automática de porta do Railway.
EXPOSE 8080

# Healthcheck real sem curl (a imagem slim não tem): bash /dev/tcp no /health.
# O Railway também faz healthcheck via railway.toml (healthcheckPath=/health).
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD bash -c 'exec 3<>/dev/tcp/127.0.0.1/8080 && { printf "GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n" >&3; head -n1 <&3 | grep -q " 200 "; }'
