# 🕵️ Obscura — Serviço exclusivo + monitoramento

Como subir o motor headless Obscura como **serviço dedicado** no Railway e
conectar o backend Dezafira a ele via Private Networking.

## O que este serviço entrega

- Motor headless em Rust (~30MB RAM) que renderiza JS real, com modo stealth
  (anti-fingerprint + bloqueio de rastreadores)
- Servidor CDP (WebSocket) na porta **9222**
- O backend (`services/obscura_client.py`) fala com ele via bridge CDP; se o
  motor estiver offline, cai em **fallback urllib** — as pipelines nunca quebram
- Toda chamada é registrada na telemetria (página 🕵️ Obscura + tabela `obscura_logs`)

## 1) Subir o serviço no Railway

1. No **mesmo projeto Railway** do backend, crie um **segundo serviço**
2. Aponte o **Dockerfile** para `SniperVideoEngine/Dockerfile.obscura`
   (ou use a imagem direto: `h4ckf0r0day/obscura`)
3. Railway expõe a porta **9222** (EXPOSE no Dockerfile)
4. Workers: ajuste o `--workers` no Dockerfile conforme o plano
   (4 workers = scraping de dores em paralelo)

### Healthcheck

O Obscura **não tem endpoint `/health` nativo**. Como o protocolo CDP expõe o
endpoint HTTP `/json` (lista de sessões/targets), configure o healthcheck do
Railway apontando para a **porta 9222** no caminho `/json`. É o mesmo endpoint
que o `ObscuraBridge.get_status()` usa para saber se o motor está vivo.

## 2) Conectar o backend (Private Networking)

No Railway, dentro do mesmo projeto, o backend alcança o serviço pelo DNS
interno **sem expor porta pública**:

```
OBSCURA_HOST=obscura.railway.internal
OBSCURA_PORT=9222
OBSCURA_ENABLED=true
```

O `ObscuraBridge` (`services/obscura_bridge.py`) já lê `OBSCURA_HOST` /
`OBSCURA_PORT`, e `get_obscura_status()` faz o ping CDP no `/json`.

### Variáveis opcionais (produção)

```
# Rotação de buscadores: quando o Google bloqueia, o fallback alterna
# round-robin entre Bing, DuckDuckGo e Ecosia (distribui carga e reduz
# rate-limit). Delay entre SERPs para não estourar os buscadores:
OBSCURA_SERP_DELAY=1.5

# Proxy residencial (destrava Google SERP/PAA de vez). Preencha no Railway
# e o motor sobe com a flag --proxy. Formato http://user:pass@host:port
# ou socks5://user:pass@host:port:
OBSCURA_PROXY_URL=

# Porta do Chrome real (CDP) — somente uso local (dev). Em produção o
# bridge usa o motor Obscura via OBSCURA_HOST/OBSCURA_PORT:
OBSCURA_CHROME_PORT=9223
```

> **Produção (Railway):** o Chrome real é local-only (start_chrome_local.bat).
> No Railway o backend usa o motor Obscura via Private Networking — o bridge
> tenta o Chrome (9223) primeiro e, não havendo, cai no Obscura (9222)
> automaticamente. Se usar proxy residencial, configure `OBSCURA_PROXY_URL`
> nas env vars do serviço Obscura (a flag `--proxy` é passada no start).

## 3) Rodando local (desenvolvimento)

Sem Docker, use o binário das releases do repo `h4ckf0r0day/obscura`:

```bash
# Linux x86_64 (variante -stealth inclui TLS impersonation / wreq-BoringSSL):
curl -L -o obscura.tar.gz \
  https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-x86_64-linux-stealth.tar.gz
tar xzf obscura.tar.gz
./obscura serve --port 9222 --workers 4 --stealth
```

Ou com Docker:

```bash
docker run -d --name obscura -p 127.0.0.1:9222:9222 \
  h4ckf0r0day/obscura serve --port 9222 --workers 4 --stealth
```

Depois rode o backend com `OBSCURA_ENABLED=true` (é o default do cliente).

## 4) Monitoramento (página exclusiva)

- **Endpoint admin:** `GET /api/v1/obscura/status` (protegido por `require_admin`)
- **Página no painel:** nav **🕵️ Obscura** — status online/offline, alvos CDP,
  chamadas por agente, taxa de sucesso, latência média e últimas 100 chamadas
- **Card no Dashboard:** status compacto com as 5 últimas chamadas
- **Banco:** tabela `obscura_logs` guarda o histórico persistido (criada
  automaticamente pelo `create_all` em `modules/database.py`)

## Notas

- A imagem é **distroless** (sem shell, sem package manager) — debug via
  `RUST_LOG` e CDP, não via `docker exec`
- A flag `--stealth` usa a variante do binário com wreq/BoringSSL (TLS
  impersonation); sem ela o transporte padrão (rustls) não falseia o TLS do
  Chrome — importante para YouTube/Google sem página de consentimento
- Releases Linux miram Ubuntu 22.04 (glibc 2.35+)
- Se o motor estiver offline, tudo continua funcionando via fallback urllib —
  a diferença é que o painel mostra 🔴 Offline e as chamadas caem no fallback
