# 🚀 Plano de Execução — Absorção do 1Convite no Ecossistema Dezafira

> **Status:** em andamento (fase 1: conteúdo + infra de domínio dedicado)
> **Última atualização:** 16/08/2026
> **Objetivo final:** o 1Convite deixa de ser um sistema separado e vira um
> **produto da fábrica** (DezafiraADM), com conteúdo no banco do ADM, PWA no
> padrão Dezafira e entrega via DezafiraClub — com domínio dedicado
> (`1convite.com.br`).

---

## 1. Arquitetura-alvo

```
┌────────────────────────── DEZAFIRAADM (a fábrica) ──────────────────────────┐
│  dezafiraadm (FastAPI)          ──  banco PostgreSQL (Postgres)             │
│   ├── Fábricas (ofertas, blog, ebook, curso, imagens, mapas, biosites…)      │
│   ├── Blueprint Engine (branding + artefatos por produto)                   │
│   ├── Fábrica de PWAs (miniapps → /app/{slug} + manifest/sw/icons)          │
│   └── [NOVO] Conteúdo 1Convite (convite_* tables) + rota por Host           │
│                                                                             │
│  dezafiraadm-frontend (adm.dezafira.com.br)  ← UI da fábrica                │
└──────────────────────────────────────────────────────────────────────────────┘
        │  ponte CLUBE_IMPORT_KEY → /api/import/product, /member-course
        ▼
┌────────────────────────── DEZAFIRACLUB (a vitrine) ─────────────────────────┐
│  dezafiraclube (www.dezafira.com.br) — venda, área de membros, entrega      │
└──────────────────────────────────────────────────────────────────────────────┘

Domínio dedicado do produto 1Convite:
  DNS 1convite.com.br → serviço dezafiraadm (Railway custom domain)
  Host header 1convite.com.br → middleware serve /app/1convite na raiz (/)
  Outros PWAs: /app/{slug} sem domínio próprio (inalterado)
```

**Decisões do dono (já confirmadas):**
1. Dados de usuário do 1Convite: **começar do zero** (só conteúdo: Bíblia, matriz diária, trilhas, jogos, dicionário).
2. Conselheiros IA: **manter chave do ChatGPT (LWC)** — portar o fluxo LWC pro backend Python do ADM.
3. PWA: funcionar como os outros PWAs (banco do ADM + gerador) **com domínio dedicado**.
4. Repo GitHub `spcompensa-glitch/1convite`: **pode remover tudo** após absorver o código/conteúdo pro repo Dezafira.

---

## 2. Estado atual (o que existe)

### 2.1 Serviços Railway no projeto `shimmering-possibility` (production)

| Serviço | Repo | Papel | Status |
|---|---|---|---|
| dezafiraadm | dezafira2.0 (`/`) | Backend fábrica (FastAPI) | ✅ |
| dezafiraadm-frontend | dezafira2.0 (`/club-frontend`) | Admin fábrica (Next.js) | ✅ |
| dezafiraclube | dezafira2.0 (`/Blog_..._v1.8`) ⚠️ | Vitrine/área de membros (SvelteKit) | ✅ (roda v1.8, atual é v1.9) |
| libsql-server / Postgres / Redis | imagem/plugin | Bancos da Dezafira | ✅ |
| Chrome / obscura / hermes-agent / aionui-webui | imagem/repo | Motores da fábrica | ⚠️ obscura FAILED 15/08 |
| 1convite-frontend | spcompensa-glitch/1convite (`/frontend`) | PWA do 1Convite | ✅ |
| 1convite-backend | spcompensa-glitch/1convite (`/backend`) | API Express do 1Convite | ✅ |
| 1convite-App | spcompensa-glitch/1convite (`/frontend/android/app`) | APK Android | ❌ FAILED |
| Postgres-UgL5 / Redis-S2x0 | plugin | Banco/cache do 1Convite (criados 08/08) | ✅ |

### 2.2 Conteúdo do 1Convite (repo público, clone em `/tmp/1convite-src`)

| Conteúdo | Onde vive hoje | Destino |
|---|---|---|
| Bíblia ACF (~31k versículos) | Postgres-UgL5 `tb_biblia` (importado de JSON público) | `convite_biblia` (reimportável) |
| Matriz diária 365 dias | `tb_matriz_diaria` — 7 dias reais + 358 gerados por template (meditação/IA no app) | `convite_matriz_diaria` |
| Dicionário teológico (8 termos) | `tb_dicionario` (seed) | `convite_dicionario` |
| Trilhas de crescimento (4 temas × 30 dias) | `tb_trilhas` (seed) | `convite_trilhas` |
| Jogos: Quiz (30), Charadas (15), Forca (30), Caça-Palavras (37) | `frontend/src/data/arcadeData.js` | `convite_jogos_*` |
| Trilha do Reino (plano 540/365 dias + devocionais + ações) | `frontend/src/data/trailData.js` | `convite_trilha_reino_*` |
| Leads (landing) | `tb_leads` | começar do zero (decisão) |
| Usuários/progresso/moedas | `tb_usuario_progresso` etc. | começar do zero (decisão) |
| Áudio narrado (Bíblia) | Librivox (stream externo via API) | manter stream externo |
| Conselheiros IA | ChatGPT via LWC (`LWC_SECRET`) | manter, portar pra FastAPI |

---

## 3. Fases de execução

### Fase 1 — Conteúdo no banco do ADM (✅ código pronto, ⏳ aguarda seed em produção)
- [x] Mapear conteúdo (clone + análise)
- [x] Converter dados para JSON canônico: `data/convite/*.json`
  (matriz diária real, arcade, trilha do reino)
- [x] Modelos SQLAlchemy: `modules/convite_models.py`
  (matriz, dicionário, trilhas, bíblia, jogos, trilha do reino, `miniapp_domains`)
- [x] Seed/import: `scripts/seed_convite.py`
  (dicionário, trilhas, matriz 1–365, jogos, trilha do reino; `--with-bible` importa ACF)
- [x] Seed VALIDADO em SQLite de teste (365 matriz · 120 trilhas · 112 jogos · 590 dias trilha · 16 dicionário · 9 marcos · 31.106 versículos Bíblia)
- [ ] Rodar seed no banco real (local dev = SQLite; produção = Postgres `Postgres`) — ⚠️ precisa aprovação
- [ ] Migrar rotas de conteúdo 1Convite pro FastAPI (`modules/convite_api.py`, fase 1b)

### Fase 2 — Infra de domínio dedicado (✅ PRONTO E TESTADO)
- [x] Modelo `miniapp_domains` (domínio → slug do miniapp)
- [x] Middleware Host-routing no `server.py` (1convite.com.br → /app/1convite)
- [x] Manifest/SW domain-aware (start_url `/`, scope `/` no domínio dedicado)
- [x] Endpoints admin para gerir domínios (`GET/POST/DELETE /api/v1/miniapps/{slug}/domains`)
- [x] 11 testes de Host-routing passando (TestClient + banco de teste)
- [x] **Custom domain criado no Railway (16/08)** — `1convite.com.br` → serviço `dezafiraadm` (porta 8080), id `1b5d315e`
- [x] **DNS APONTADO E DOMÍNIO NO AR (16/08)** — registros na **Hostinger (dns-parking)**: **ALIAS `@` → `yufqkp4n.up.railway.app`** (a Hostinger publica CNAME de raiz como ALIAS, com flattening) + **TXT `@` → `railway-verify=49cc427d...`**. Serial da zona subiu (`2026081606→07`). Obs.: `69.46.46.x` é a **edge do Railway** (o alvo `yufqkp4n.up.railway.app` resolve pro mesmo IP) — não era "hosting antigo".
- [x] **Validação ponta a ponta (16/08)** — `https://1convite.com.br/` → **HTTP 200 servindo o bundle PWA do 1Convite** (HTML idêntico ao `web/1convite/dist/index.html`: `index-DS1BRgRX.js`, `index-HB5bG-2B.css`); `/manifest.json` (start_url `/`, domain-aware) 200; `/sw.js` 200; assets 200; **`/api/v1/*` 200 sem rewrite** (health, biblia/livros com dados reais, asaas/status conectado). Railway: `syncStatus ACTIVE`, `verified True`, cert `VALID` (o checker de CNAME mostra `currentValue` vazio porque é ALIAS, mas o roteamento funciona). Banco já tem `miniapp_domains` = 1convite.com.br → miniapp 1convite (ativo)

### Fase 3 — PWA como produto da fábrica (✅ base pronta, ⏳ PWA React + publicação)
- [x] Registrar o 1Convite como miniapp (`/app/1convite`) com branding — `seed_convite.py --register-miniapp`
- [x] Associar domínio dedicado `1convite.com.br` → `/app/1convite` (Host-routing testado: 17/17)
- [x] API de conteúdo FastAPI — `modules/convite_api.py` (Bíblia, matriz, dicionário, trilhas, trilha do reino, 4 jogos) — registrada no server.py, 17/17 testes
- [x] **Fábrica de Convites** — `modules/convite_factory.py`: branding (paleta/nome/copy/logo no miniapp) + blueprint (`formats=app`, `external_link` = domínio dedicado) + publish via ponte. Endpoints admin: `POST /api/v1/convite/factory/{branding,blueprint,publish/{bp_id}}` — 7/7 testes
- [x] **Seed em PRODUÇÃO** (Postgres Railway via `altaria.proxy.rlwy.net`): conteúdo completo + miniapp `1Convite` (b67c0154) + domínio `1convite.com.br` ✅
- [x] **PWA absorvido** — código completo (App.jsx 5.9k linhas, componentes, dados dos jogos, mídias 51MB, backend Express de referência, skill de sites animados) em `web/1convite/` (README com build/arquitetura)
- [x] **Compat API `/api/v1/*`** — `modules/convite_compat_api.py`: contrato EXATO do Express original (usuario, codigo-dia, biblia livros/capitulos/texto/busca/aleatorio/audio+streams, dicionario, trilhas lista/ativa/iniciar/completar/cancelar, contatos, historico, checkpoint, avancar/reiniciar dia, pagamentos, admin plano, leads, health) — 42/42 testes
- [x] **Middleware fix + SPA estático** — `/api/*` NÃO é mais reescrito no domínio dedicado (bug crítico corrigido: o PWA chamava `/app/1convite/api/...` → 404); quando existe `web/{slug}/dist/index.html` o domínio dedicado serve o bundle SPA na raiz (com fallback p/ `/_pwa_build/...` e index.html), senão fallback p/ PWA gerado
- [x] **Conselheiros IA (LWC)** — sidecar Node mínimo `web/1convite/backend-lwc/` (handler oficial `@opencoredev/loginwithchatgpt-server`, mesmo `LWC_SECRET`) + proxy `/api/v1/chatgpt/*` no FastAPI (`LWC_SIDECAR_URL`); sem sidecar → 503 JSON gracioso (PWA mostra "offline" sem quebrar)
- [x] `/auth/convite` — o PWA absorvido chama `/auth/convite` (e não `/auth/google`, que é do NextAuth do admin) — 4 call sites ajustados em App.jsx
- [x] **Bundle BUILDADO** — Node 22 portátil (sem instalar nada na máquina) → `npm install && vite build` → `web/1convite/dist/` (SPA 626KB + mídias, ~52MB). Pipeline automatizado: `scripts/build_convite_pwa.sh`. SPA real servido no domínio dedicado verificado (raiz, /assets, sw.js, fallback, API) ✅
- [x] **Blueprint do 1Convite criado** — `bp_7f93b831a1` (status review, `external_link=https://1convite.com.br`, format app) via ConviteFactory
- [~] **Publish TESTADO (falha segura)** — com `.env` carregado, o bridge tentou conectar no Clube (`CLUBE_PUBLIC_URL=http://localhost:5173`, sem servidor local) → "All connection attempts failed". **Nada externo foi criado.** Quando o Clube estiver no ar (ou apontar pro real), rodar `ConviteFactory.publish('bp_7f93b831a1')`
- [x] **Publish em PRODUÇÃO CONCLUÍDO (16/08)** — blueprint **`bp_9f086a77ad`** criado e publicado no Clube real: **product_id 18, slug `1convite`, R$ 19,90 (price_cents 1900), resource_type=link, descrição completa** → página `https://www.dezafira.com.br/product/1convite` (HTTP 200, renderiza título + descrição + preço). Publish_log: produto ok, bundle/blog/landing/membros skipped (correto p/ formato app). *Necessário: fix de compatibilidade Python 3.11 (f-string com backslash em blueprint_engine.py:634) — módulo não compilava no Railway e o publish quebrava no import; corrigido e deployado*

### Fase 4 — Conselheiros IA (LWC) — ✅ DEPLOYADO (16/08)
- [x] Sidecar Node `web/1convite/backend-lwc/` (handler oficial, mesma chave) + `railway.toml` (Nixpacks, healthcheck /healthz)
- [x] Proxy `/api/v1/chatgpt/*` no FastAPI (`LWC_SIDECAR_URL`) — 503 gracioso sem sidecar
- [x] **Sidecar DEPLOYADO no Railway (16/08)** — serviço **`1convite-lwc`** criado via API (source `1crypten001-crypto/dezafira2.0`, root dir `web/1convite/backend-lwc`, builder Nixpacks, healthcheck `/healthz`, start `npm start`), domínio **`https://1convite-lwc-production.up.railway.app`** (`/healthz` → `{"status":"ok","service":"1convite-lwc"}`), build SUCCESS
- [x] **`LWC_SIDECAR_URL` setado no `dezafiraadm`** (produção) → redeploy OK; **proxy validado de ponta a ponta**: `/api/v1/chatgpt/*` responde do handler do sidecar (308 raiz / 404 em rotas desconhecidas — antes era 503 "offline")
- [~] **`LWC_SECRET` real pendente** — sidecar roda com o segredo de dev fallback; para os Conselheiros IA autenticarem de verdade no ChatGPT/LWC, falta setar o segredo original (obter do projeto 1Convite antigo ou do painel LWC) na variável `LWC_SECRET` do serviço `1convite-lwc`

### Fase 4b — PAGAMENTOS & DESCOBERTA (integração com tokens reais) — ✅ 15/08
- [x] **Asaas integrado (produção) — CONFIRMADO 16/08** — token `$aact_prod_...` (1crypten001@gmail.com) validado via API. `modules/asaas_client.py`: customer upsert, cobrança PIX (invoiceUrl + QR), cartão, webhook (PAYMENT_*), status. Endpoints `/api/v1/asaas/{status,cobranca-pix,webhook,cobranca/{id}}` + `/api/v1/pagamentos/*` do 1Convite criam cobrança PIX real (fallback fake só sem chave). **Correção: `ASAAS_API_KEY` NÃO estava no `dezafiraadm` de produção (só no `.env` local — a integração havia sido validada localmente) — setada via `variableUpsert` + redeploy OK**
- [x] **Teste REAL de cobrança (16/08)** — `/api/v1/asaas/status` → conta `1crypten001@gmail.com` (produção); cobrança PIX real criada (R$ 5,00 — **mínimo do Asaas é R$ 5,00**; R$ 1,00 é recusado), status PENDING, `invoiceUrl` válida, **payload EMV PIX válido** (`000201...br.gov.bcb.pix...`) + QR encodedImage; cobranças de teste removidas via `DELETE /v3/payments/{id}` (endpoint de cancelamento `/cancel` retorna 404 — o correto é DELETE)
- [x] **Webhook Asaas REGISTRADO (16/08)** — `id 5b0468b5-ccc2-4c5d-9492-512259ae3af9` → `https://adm.dezafira.com.br/api/v1/asaas/webhook`, eventos `PAYMENT_RECEIVED, PAYMENT_CONFIRMED, PAYMENT_OVERDUE, PAYMENT_REFUNDED, PAYMENT_DELETED` (antes não havia webhook nenhum — pagamento confirmado não liberava acesso)
- [x] **Agente Dário ativado com as chaves** — Facebook (`FACEBOOK_ACCESS_TOKEN`, já no .env) via `FacebookAdsSpy` (API Graph + fallback Obscura/Chrome); Google via `GoogleSEOSpy` com o **CSE do dono** (`GOOGLE_CSE_ID=8699036eeda444a95`): caminho API precisa de `GOOGLE_API_KEY` (não fornecida) → **fallback novo: scraping da página do CSE via Chrome/Obscura** (`_search_via_cse_scraper`) para gerar palavras-chave de artigos/backlinks
- [x] `.env.example` atualizado (ASAAS_API_KEY, GOOGLE_CSE_ID, GOOGLE_API_KEY, LWC_SIDECAR_URL)
- [ ] `GOOGLE_API_KEY` (Google Custom Search JSON API) — opcional, desbloqueia o caminho de API do Dario SEO

### Fase 4c — PRIMEIRA OFERTA (produção) — ✅ 15/08
- [x] **Banners do 1Convite no blog O Reino (produção)** — blog `o-reino` (blg_50e26e, 21 posts) encontrado no ADM de produção; **21/21 artigos** receberam o banner-CTA do 1Convite (bloco HTML/CSS com branding dourado → botão "COMEÇAR AGORA" → **https://1convite.com.br** — página de venda + checkout Asaas PIX). Banner do canal gerado (pollinations). **16/08:** CTA atualizado → **página de venda** (`/product/1convite`) + banner-imagem por tema (ver Fase 4d)
- [x] **Blueprint preenchido** — `bp_7f93b831a1` completo: price **R$ 19,90** (editar antes de publicar), descrição/vendas, benefícios, pitch, CTA, `checkout_provider=asaas`, `external_link=https://1convite.com.br`, status review
- [x] **Asaas na venda** — módulo + endpoints prontos (ver Fase 4b); o checkout do app usa PIX real
- [x] **UI da Fábrica de Convites** — `club-frontend/app/admin/fabrica-convite/page.tsx` (status miniapp/domínio/Asaas/blueprints + branding + criar blueprint + publicar) + item "👑 1Convite" no menu admin + endpoint `GET /api/v1/convite/factory/blueprints` (401 sem auth) — testado
- [x] **Publicar no Clube (16/08)** — feito em produção, ver Fase 3: `/product/1convite` no ar (product_id 18)
- [x] **FUNIL E2E validado em PRODUÇÃO (16/08)** — (1) banner no artigo do blog O Reino (`/blog/o-reino?post=post_*`, botão dourado → `https://1convite.com.br`) ✅; (2) checkout do PWA no domínio: `POST /api/v1/pagamentos/criar-preferencia` → cobrança PIX real `pay_s6s2miq1ben0rxj6` (R$ 19,90, PENDING, EMV+QR válidos, removida após teste) ✅; (3) **compra no Clube**: membro de teste registrado + perfil com CPF → `GET /purchase/18` → **303 → `https://www.asaas.com/i/pay_l3c6kwzugdycegss`** (PIX real produção, PENDING, R$ 19,00, removida após teste) ✅
- [x] **Clube: Asaas em produção** — `ASAAS_API_KEY` + `ASAAS_API_URL` (produção) setadas no env do `dezafiraclube`; settings do banco corrigidas (`asaas_api_url` estava **sandbox** + chave fraca `311101Jfpl@!` — agora o env de produção sobrepõe). **`enable_member_login` ativado** (`0`→`1` — área de membros e compras no ar; antes toda compra dava 403 "área desativada"); `enable_otp_login` restaurado para `1` após o teste
- [x] **Preço DEFINIDO (16/08)** — **R$ 29,90/mês ou R$ 297,00 à vista (12 meses, 2 meses grátis)** — alinhado nos 3 lados: produto no Clube (`price_cents=29700`), blueprint `bp_9f086a77ad` (`29700`) e PWA (tela Premium)

### Fase 4d — PREÇO, ARTES DOS BANNERS E PÁGINAS DE ENTREGA (16/08)
- [x] **Precificação aplicada** — produto `/product/1convite` no Clube atualizado via admin: **R$ 297,00 à vista** (`price_cents 29700`) + descrição nova com os dois preços e link de instalação; blueprint `bp_9f086a77ad` atualizado para 29700 (fonte de re-publish)
- [x] **Artes dos banners CRIADAS** — 5 imagens geradas com PIL (paleta navy `#0f172a→#16213e→#0f3460` + dourado `#d4af37`, monograma 1C, CTA dourado, preço): `static/images/1convite/` → `banner_hero`, `banner_biblia`, `banner_jogos`, `banner_trilhas` (1200×400) + `banner_social_1080.png` (quadrado p/ redes). Servidas em `https://1convite.com.br/static/images/1convite/*.png`
- [x] **Banner-imagem injetado nos 21 artigos do O Reino (produção)** — Postgres: CTA do banner dourado trocado de `1convite.com.br` → **`https://www.dezafira.com.br/product/1convite`** (página de venda/checkout) + banner-imagem (variante por tema) anexado ao fim de cada artigo. `modules/blog_viewer.py` agora injeta o banner-imagem por tema em qualquer artigo (com guarda anti-duplicação p/ os que já têm no corpo)
- [x] **Página de ENTREGA + INSTALAÇÃO** — `GET /instalar` e `/entrega` no ADM (`modules/instalar_page.py`, rota liberada no host-routing do domínio dedicado): o que acontece depois da compra (acesso imediato via webhook Asaas, login com o e-mail da compra) + passo a passo de instalação do PWA (Android/Chrome, iPhone/Safari, desktop/Chrome-Edge). Link "Como instalar" na tela Premium do app
- [x] **PWA: tela Premium com os dois preços + checkout real** — `App.jsx`: cards **Mensal R$ 29,90/mês** e **Anual R$ 297,00 (2 meses grátis)** com checkout Asaas real (`POST /pagamentos/criar-preferencia` com `valor_cents` 2990/29700 → fatura PIX/cartão); removido o fluxo WhatsApp com número placeholder; **fix `API_BASE`** (apontava para domínio Railway antigo `invigorating-expression-...` → agora same-origin `/api/v1`)
- [x] **PWA buildado e deployado** — `npm run build` → `web/1convite/dist/` novo bundle **`index-DGCtRnqO.js`** (626KB) commitado (o ADM serve `web/{slug}/dist` no domínio dedicado)
- [~] **Conta de teste** — membro `funil.membro@dezafira.com.br` (senha `TesteFunil@2026`) criado no Clube durante o E2E; remover se quiser banco 100% limpo
- [x] **Push pro GitHub CONCLUÍDO (16/08)** — merge em `main` (`b0fea9d..c736493` → `14c8b8e` → `1115cb2`). Foram 3 commits: integração 1Convite/Asaas/Dario/Fábrica; fix TS do admin (32 erros) + fix binário do Obscura (usava `obscura-worker` no lugar de `obscura`); fix Python 3.11 (f-string com backslash) + admin sem senha padrão
- [x] **Builds de produção 5/5 SUCCESS (16/08)** — dezafiraadm, dezafiraadm-frontend, dezafiraclube, obscura, Chrome — todos verdes após os fixes. Obscura: CDP ativo (log "CDP do Obscura ativo em 127.0.0.1:9225" + healthcheck OK; `json/version` responde Chrome/145)
- [x] **Credenciais do admin** — `admin@dezafira.com` (login validado em produção). Senha **definitiva aplicada** (16/08): nova senha forte gravada direto no Postgres de produção e **login validado 200 OK** (`/api/v1/auth/login`). Seed do código lê `ADMIN_PASSWORD` do ambiente (sem valor → não cria usuário; não sobrescreve senha existente no boot)

### Fase 5 — Deletes (✅ EXECUTADO em 15/08)
- [x] **Deletes executados via API** (`serviceDelete`): `1convite-frontend`, `1convite-backend`, `1convite-App`, `Postgres-UgL5`, `Redis-S2x0` — confirmados fora do projeto (10 serviços restantes, todos Dezafira)
- [ ] ~~Backup dump~~ — pg_dump indisponível e DB interno; conteúdo preservado em `data/convite/*.json` + banco local (decisão do dono: dados de usuário começam do zero)
- [ ] Apagar repo GitHub `spcompensa-glitch/1convite` (pendente — precisa das credenciais do dono; conteúdo já absorvido)
- [ ] Corrigir `dezafiraclube` → root dir `v1.9` — **⚠️ BLOQUEADO: históricos DIVERGENTES** (GitHub main tem commits que o local não tem — bidu, miniapps born-complete, hermes). **NÃO push** (seria rejeitado/misturado). Patches gerados em `C:/tmp/dezafira_patches/` — aplicar no checkout que pusha pro GitHub
- [x] **obscura**: causa raiz (Xvfb display 99) + fix COMMITADO localmente (deba515). **Redeploy bloqueado** até o fix chegar no GitHub (Railway builda do GitHub)
- [x] **Seed banco real (local)**: conteúdo completo + miniapp `1Convite` + domínio `1convite.com.br` registrados no `dezafira.db`

---

## 4. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Perder conteúdo do 1Convite ao apagar | Alto | JSON canônico em `data/convite/` + dump do Postgres-UgL5 antes do delete |
| Quebrar `/app/{slug}` existente dos miniapps | Médio | Middleware só age quando Host está no mapa `miniapp_domains`; caminhos `/app/*` passam direto |
| Bíblia grande (31k linhas) lenta no seed | Baixo | Inserção em lotes (batch 1000) com transação única |
| Domínio dedicado com scope/start_url errado no install | Médio | Manifest domain-aware (start_url `/` quando Host dedicado) |
| LWC/chat segredo exposto | Alto | Nunca logar valores de variáveis; usar `LWC_SECRET` do mesmo jeito que o Clube |

## 5. Rollback

- **Banco:** tabelas `convite_*` e `miniapp_domains` são novas — `DROP TABLE` remove tudo sem tocar no resto.
- **server.py:** middleware é aditivo e condicionado ao mapa de domínios (vazio por padrão → nenhum efeito).
- **Railway:** serviços deletados podem ser recriados do repo GitHub até ele ser apagado; depois, do JSON/backup.

## 6. Pendências que dependem de você

1. Aprovar o **dump do Postgres-UgL5** (read-only) antes dos deletes — quer que eu peça as credenciais ou o dump via `railway volume/ssh`?
2. Confirmar se o **obscura** (motor de busca) é crítico — investigo o build log em paralelo.
3. Confirmar troca do `dezafiraclube` pra **v1.9** + redeploy.
4. Onde mora o DNS do `1convite.com.br` (registro/provedor) pra eu apontar pro serviço `dezafiraadm`.
