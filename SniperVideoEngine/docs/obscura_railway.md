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
2. No campo **Root Directory**, aponte para `SniperVideoEngine/docker/obscura`
   (a pasta contém um `Dockerfile` com nome padrão que o Railpack detecta
   automaticamente — sem precisar de configuração extra)
3. Railway expõe a porta **9222** (EXPOSE no Dockerfile)
4. Workers: env `OBSCURA_WORKERS` (default 4 = scraping de dores em paralelo)
5. **Proxy residencial (opcional):** env `OBSCURA_PROXY_URL` no serviço — o
   entrypoint (`docker/obscura/entrypoint.sh`) adiciona `--proxy`
   automaticamente quando preenchida

> **Por que este Dockerfile baixa o binário das releases?** A imagem oficial
> `h4ckf0r0day/obscura` é **distroless** (sem shell), impossível de montar o
> `--proxy` condicional. Este Dockerfile usa `debian:bookworm-slim` + o mesmo
> binário stealth das releases (mesmo fluxo do `start_obscura_local.bat`) para
> o entrypoint conseguir ler `OBSCURA_PROXY_URL` e montar os args.

### Healthcheck

O Obscura **não tem endpoint `/health` nativo**. Como o protocolo CDP expõe o
endpoint HTTP `/json/version`, o `docker/obscura/Dockerfile` já traz um
**`HEALTHCHECK` nativo** (`curl -fsS http://localhost:9222/json/version`) — o
Railway só marca o serviço como **healthy** quando o CDP responde de verdade,
evitando o backend tentar usar o Obscura antes de ele estar de pé. O
`docker/chrome/Dockerfile` faz o mesmo via `wget` em
`http://localhost:9223/json/version`.

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
```

## 1.5) Chrome real como serviço (desbloqueia o Google de vez)

O Chrome real (fingerprint TLS genuíno) desbloqueia o Google SERP/PAA que o
headless Rust não consegue (o Google devolve `/sorry/` CAPTCHA). No Railway
isso é um **terceiro serviço**:

1. Crie um serviço apontando o **Root Directory** para
   `SniperVideoEngine/docker/chrome` (contém `Dockerfile` padrão que o
   Railpack detecta sozinho)
2. Railway expõe a porta **9223** (EXPOSE no Dockerfile)

> ⚠️ **Chrome moderno (136+) ignora `--remote-debugging-address=0.0.0.0`** e
> binda o DevTools só em `127.0.0.1` (o log mostra `DevTools listening on
> ws://127.0.0.1:9223`). Por isso o entrypoint usa **socat**: o Chrome roda no
> loopback (porta interna `OBSCURA_CHROME_INNER_PORT`, default 9224) e o socat
> expõe `0.0.0.0:9223 → 127.0.0.1:9224` — a rede privada do Railway alcança o
> Chrome de verdade, e o healthcheck (`wget :9223/json/version`) passa pelo
> socat.
3. No **backend**, configure:
   ```
   OBSCURA_CHROME_HOST=chrome.railway.internal
   OBSCURA_CHROME_PORT=9223
   OBSCURA_PROXY_URL=            # opcional — proxy residencial
   ```

O bridge (`_pick_bridge_host_port`) tenta **Chrome primeiro** (host/porta do
Chrome) e, não havendo, cai no **Obscura** (OBSCURA_HOST/OBSCURA_PORT). Assim
em produção a cadeia fica igual à local: **Chrome → Google → fallback**
rotativo (Bing/DDG/Ecosia).

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
  automaticamente pelo `create_all` em `modules/database.py`); tabela
  `obscura_serp_runs` guarda o snapshot de fontes/bloqueios SERP de cada rodada
  da fábrica — o histórico **sobrevive a restarts e deploys** (exposto como
  `persisted_runs` em `GET /api/v1/obscura/serp-sources`)

## Notas

- A imagem é **distroless** (sem shell, sem package manager) — debug via
  `RUST_LOG` e CDP, não via `docker exec`
- A flag `--stealth` usa a variante do binário com wreq/BoringSSL (TLS
  impersonation); sem ela o transporte padrão (rustls) não falseia o TLS do
  Chrome — importante para YouTube/Google sem página de consentimento
- Releases Linux miram Ubuntu 22.04 (glibc 2.35+)
- Se o motor estiver offline, tudo continua funcionando via fallback urllib —
  a diferença é que o painel mostra 🔴 Offline e as chamadas caem no fallback
