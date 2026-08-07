# DEZAFIRA — Fábricas de Conteúdo & Dezafira Adm

> **Versão:** 3.4.0  
> **Site público (DezafiraClube):** https://www.dezafira.com.br (SvelteKit + Railway)  
> **Admin (Dezafira Adm):** https://adm.dezafira.com.br (Next.js + Railway)  
> **API Backend:** https://dezafiraadm-production.up.railway.app (FastAPI)  
> **Database:** PostgreSQL (prod) / SQLite (dev)  
> **Última atualização:** 06/08/2026

---

## 📋 VISÃO GERAL

A Dezafira é um ecossistema de **fábricas de conteúdo digital** com IA — Blogs, Ebooks, Cursos e Marketing — orquestradas por agentes brasileiros e motor headless (Obscura/Chrome). O ecossistema tem **dois serviços**: o **DezafiraClube** (SvelteKit — site público, blog e área de membros) e o **Dezafira Adm** (FastAPI + Next.js — painel de fábricas). Pagamentos, **gamificação, combos e ranking** foram removidos do Adm (commits recentes).

### Estado Atual

| Métrica | Valor |
|---|---|
| **Canais de Blog** | 3 ativos (O Reino, Fenômenos Inexplicáveis, Emagrecimento Dores) |
| **Total de Artigos** | Ver dashboard (atualizado dinamicamente) |
| **Palavras Geradas** | ~199.000+ |
| **Artigos com Imagem** | 100% |
| **Score Monetização** | 88.7% (17/19) — ✅ Pronto AdSense |
| **Cursos Criados** | 2 (1 via pipeline automática) |
| **Trilhas de Aprendizado** | 1 (Trilha IA para Iniciantes) |
| **Fábricas Ativas** | Blog (5 fases) + Ebook (6 fases) + Curso (6 fases) + Marketing (6 fases) |
| **Agentes IA** | 21+ especializados |
| **LLM Cascade** | OpenRouter → Gemini → NVIDIA NIM → HuggingFace → DeepSeek |

### Blogs Ativos

| Blog | Nicho | Artigos | Imagens | Subdomínio |
|---|---|---|---|---|
| ✝ **O Reino** | Ensinamentos de Jesus | — | 100% | oreino |
| 🔮 **Fenômenos Inexplicáveis** | Teorias da Conspiração | — | 100% | fenomenosinexplicaveis |
| 🥗 **Emagrecimento Dores** | Emagrecimento | — | 100% | emagrecimentodores |

> *Artigos por blog atualizados dinamicamente no dashboard; os valores da tabela refletem os canais ativos em produção.*

---

## 🏗️ ARQUITETURA DO SISTEMA

```
┌──────────────────────────────────────────────────────────────────────┐
┌──────────────────────────────────────────────────────────────────────┐
│                 FRONTEND ADM — Next.js 14 (Railway)                 │
│        Landing │ Auth │ Painel │ Admin │ Fábricas │ Trilhas         │
│        https://adm.dezafira.com.br                                   │
│        ANEXA o painel legacy via <iframe> com token ?token=          │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ chamadas API diretas (fetch → backend)
┌──────────────────────────▼───────────────────────────────────────────┐
│              BACKEND — FastAPI (Railway) — 181 endpoints              │
│        https://dezafiraadm-production.up.railway.app (port 8080)     │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │         🔐 Auth & Admin (JWT + bcrypt + Google OAuth)           ││
│  │  Login │ Recovery │ Me │ Admin (require_admin)                  ││
│  └──────────────────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │       🏭 Fábricas / Pipelines (todas admin-gated)                ││
│  │  📝 Blog(5) │ 📗 Ebook(6) │ 🎓 Curso(6) │ 📢 Marketing(6)      ││
│  │  LiLi Reviewer · LLM Cascade(5) unificada · Modelos            ││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────┬───────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│              PostgreSQL (Railway) — 30+ tabelas                       │
│             Blog Channels/Posts/Sections │ Books │ Users              │
│             Sessions │ Courses │ LearningPaths │ Purchases           │
│             Ebook Accesses │ Marketing Campaigns │ SERP Runs         │
└──────────────────────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 AGENTES DO SISTEMA

### 👴 Seu Hermes — Orquestrador
**Arquivo:** `modules/blog_pipeline.py`  
**Responsabilidades:** Orquestra toda a macro-esteira da fábrica de blogs  
**Fases:** Fundação → Arquitetura → Produção → Refino → Entrega  
**Integração:** WebSocket hub para UI em tempo real  
**Checkpoint:** Salva estado no banco para retomada após falhas

### 📝 Carlão — Redator Chefe
**Arquivo:** `modules/blog_writer.py`  
**Responsabilidades:** Gera artigos completos usando LLM (Llama 3.3 via NVIDIA NIM)  
**Recursos:**
- Prompt otimizado por nicho (cristão, finanças, etc.)
- Geração de título, keywords, slug automático
- Controle de tom e estilo
- Tabelas, listas, citações bíblicas/financeiras
- Mínimo de 800 palavras por artigo

### 🎨 Seu Design — Diretor de Arte
**Arquivo:** `modules/brand_designer.py`  
**Responsabilidades:** Cria a identidade visual e o branding completo do blog (paleta de cores, tipografia, logos e favicons SVG sob medida) de forma totalmente dinâmica via LLM.  
**Recursos:**  
- Geração dinâmica de cores harmoniosas adaptadas ao nicho do blog (Light e Dark mode).  
- Recomendação de fontes do Google Fonts ideais para leitura e título.  
- Criação de logotipo e favicon SVG vetoriais exclusivos e dinâmicos para o nome do blog.

### 🌸 LiLi — Revisora de Qualidade
**Arquivo:** `modules/lili.py`  
**Responsabilidades:** Revisa artigos automaticamente após geração  
**Padrões detectados (25+):**
- `exclamacoes_em_massa` — 5+ exclamações seguidas
- `micro_biologia_gibberish` — seções sem sentido
- `html_garbage` — HTML mal formado com & $ # @
- `colon_quote_colon_garbage` — "Aerial: \"The:\"" (garbage LLM)
- `assistant_repetition` — vazamento de tokens de chat
- `backslash_dominated` — 3+ barras invertidas consecutivas
- `encoding_quebrado` — acentos quebrados
- `repeticao_massiva_sequencia` — 5 palavras repetidas 4+ vezes

**Correção automática:** Remove exclamacoes, traduz inglês, limpa encoding, remove tags vazias, limpa garbage text

**Score:** 0-100 (aprovado se ≥ 70 e sem issues "alta")

### 📸 Ricardo — Fotógrafo
**Arquivo:** `modules/ricardo.py`  
**Responsabilidades:** Gera imagem de destaque para cada artigo  
**Provedores (em ordem):** Pexels → Unsplash → Placeholder SVG  
**Fallback absoluto:** Placeholder SVG inline (data URI) — funciona 100%

### 👴 Seu Pereira — Analista de Monetização
**Arquivo:** `modules/seu_pereira.py`  
**Responsabilidades:** Avalia cada blog contra checklist de 19 critérios do Google AdSense  
**Categorias:**
- 📝 Conteúdo (5 critérios, peso 41)
- 📄 Páginas Obrigatórias (3 critérios, peso 22)
- 🎨 Design & UX (3 critérios, peso 18)
- 🔧 Técnico (5 critérios, peso 33)
- 🔍 Indexação & SEO (2 critérios, peso 13)
- 🏛️ Autoridade E-E-A-T (1 critério, peso 6)

**Score máximo:** 133 pontos  
**Status:** 🔴 < 20% | 🟠 20-50% | 🟡 50-80% | ✅ > 80%

### 📅 Seu Zé — Scheduler de Publicação
**Arquivo:** `modules/seu_ze.py`  
**Responsabilidades:** Publica 1 artigo/dia às 08:00 para cada blog ativo  
**Recursos:** Thread background com verificação a cada 60s, fila de artigos, notificação de estoque vazio

### 👴 Seu Francisco — Supervisor de Produção
**Arquivo:** `modules/seu_francisco.py`  
**Responsabilidades:** Confere estoque, autoriza novos artigos, relatório executivo  
**Regras:** Bloqueia se target atingido, bloqueia se >30% rejeitados

### 🔍 Joaquim — Pesquisador de Keywords
**Arquivo:** `modules/keyword_miner.py`  
**Responsabilidades:** Minerador de palavras-chave via Google Autocomplete + SERP Analysis  
**Recursos:** Expansão por prefixos/sufixos, People Also Ask, SERP Difficulty Analyzer, clustering

### 🎨 Dona Célia — Designer
**Arquivo:** `modules/brand_themes.py`  
**Responsabilidades:** Branding dinâmico por blog — logos SVG, favicons, cores, fontes  
**Temas disponíveis:** Cristão, Finanças, Saúde, Tecnologia, Geral

### 📸 Tatiana — Fotógrafa de Imagens
**Arquivo:** `modules/image_factory.py`  
**Responsabilidades:** Motor de geração de imagens (Pexels → Unsplash → Placeholder)

### 📝 Dona Rosa — Revisora Gramatical
**Arquivo:** `modules/blog_revisor.py`  
**Responsabilidades:** Revisão gramatical e estrutural de artigos

### 🏷️ Seu Silva — Agente de Afiliação Amazon
**Arquivo:** `modules/affiliate_agents.py`  
**Responsabilidades:** Gerencia tags de associado da Amazon e formata links de afiliados dinamicamente para produtos físicos do nicho.

### 🦐 Dona Benta — Agente de Afiliação Shopee
**Arquivo:** `modules/affiliate_agents.py`  
**Responsabilidades:** Cria links com assinaturas criptografadas (HMAC-SHA256) compatíveis com a API de afiliados da Shopee.

### 🤝 Seu Nogueira — Agente de Afiliação Mercado Livre
**Arquivo:** `modules/affiliate_agents.py`  
**Responsabilidades:** Orquestra a autenticação OAuth2 do Mercado Livre, realizando o refresh automático do access token no banco de dados.

### 📢 Fábrica de Marketing — 6 Agentes (Sabri Suby Framework)
**Arquivo:** `modules/marketing_pipeline.py`  
**Responsabilidades:** Esteira de 6 fases de Marketing Digital sequenciais (uma fase por chamada via `POST /api/v1/marketing/stage`), 100% integrada com Obscura (buscas reais do Google) e a cascata de LLMs gratuitos. Cada fase persiste o conteúdo no banco (`marketing_campaigns`) para restauração na UI.

| Fase | Agente | Papel |
|------|--------|-------|
| 1 | 👴 **Seu Tião** — O Caçador de Avatares | Usa Obscura (`get_google_suggestions`) para buscar buscas ativas no Google + LLM para criar o perfil completo do Dream Buyer (dores, medos ocultos, sonhos, objeções) |
| 2 | 🍰 **Dona Benta** — Iscas Digitais | Propõe 3 ideias de Iscas Digitais de Alto Valor (HVCO): e-books, checklists, mini-cursos com título, estrutura e justificativa |
| 3 | 📣 **Tonho da Propaganda** — Copywriter AIDA | Cria 3 variações de anúncios persuasivos (Atenção, Interesse, Desejo, Ação) para redes sociais |
| 4 | ✏️ **Zé do Traço** — Landing Page | Escreve a cópia e estrutura da Landing Page de captura (Hero, Problema, Solução, Prova Social, Garantia, CTA) |
| 5 | 💌 **Chica dos Correios** — E-mails / Nurturing | Escreve sequência de 4 e-mails (boas-vindas → objeção → oferta → urgência) com envio SMTP nativo (`MarketingPipeline.send_smtp_email`) |
| 6 | 🤝 **Seu Valdir** — Fechador da Oferta | Desenha a Oferta Irrecusável (Godfather Offer): garantia de risco zero, bônus, ancoragem de preço, escassez/urgência |

### 🌐 WordPress Publisher
**Arquivo:** `server.py` (endpoints) + `modules/mcp_client.py`  
**Responsabilidades:** Publicação nativa de artigos e páginas de vendas no WordPress via REST API (sem plugins) — usa `WP_URL`/`WP_USER`/`WP_APP_PASS`. O painel tem a página **🌐 WordPress** (teste de conexão, salvar credenciais, publicar artigo/página de vendas).

### 🖥️ MCP Servers Monitor
**Arquivo:** `modules/mcp_client.py`  
**Responsabilidades:** Telemetria de integridade dos servidores Model Context Protocol mapeados (memory, filesystem, brave_search, wordpress) — ping real e status exposto em `GET /api/v1/mcp/status` e no card do dashboard.

---

## 📡 ENDPOINTS DA API

> **Base:** `https://dezafiraadm-production.up.railway.app` · **181 endpoints no total** (admin-gated com `require_admin`).
> **Autenticação:** `Authorization: Bearer <JWT>`. Endpoints de **admin** (`/admin/*`, pipelines, ebooks, lili, search, monetization) exigem `require_admin` (401 sem token de admin).  
> **LLM Cascade:** fonte única em `agents/llm.py` — OpenRouter → Gemini → NVIDIA NIM → HuggingFace → DeepSeek (unificada em 08/2026; `_call_llm` do blog_writer virou delegador fino).

### 🏥 Health & Infra
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check do servidor |
| GET | `/healthz` | Healthcheck do Railway: **200** com motor OK ou dentro da graça · **503** quando o motor fica fora por mais que `OBSCURA_HEALTH_GRACE` (default 300s) — reinicia o backend |
| GET | `/api/v1/obscura/status` | 🕵️ Painel Obscura: status do motor, telemetria por agente (com `via_bridge`/`via_fallback`), retries, incidentes e grace — **admin** |
| GET | `/api/v1/obscura/grace` | Grace atual do healthcheck (`grace_s` + fonte `runtime`/`env`) — **admin** |
| PUT | `/api/v1/obscura/grace` | Aplica nova grace em runtime **e persiste no .env** (sem reiniciar o backend) — **admin** |
| GET | `/api/v1/obscura/proxy-check` | 🕵️ Healthcheck do proxy configurado: testa conectividade real (GET via proxy em api.ipify.org), mede latência + IP de saída — **admin** |
| GET | `/api/v1/obscura/serp-sources` | 🔀 Fontes SERP da rodada atual + histórico de rodadas (rotacao de buscadores) **incluindo as persistidas no banco** (`persisted_runs`, sobrevivem a restarts) — **admin** |
| POST | `/api/v1/obscura/serp-sources/reset` | Zera os contadores de fonte SERP (início de nova rodada da fábrica) — **admin** |
| GET | `/api/v1/version` | Versão da API |
| GET | `/api/v1/logs` | Logs recentes |
| GET | `/api/v1/account/balance` | Saldo da conta |
| GET | `/api/v1/trends` | Tendências globais |

### 🕵️ Monitoramento Obscura
| Recurso | Descrição |
|---------|-----------|
| **Card de graça configurável** | No painel 🕵️: select 0–900s + botão **Aplicar** → `PUT /api/v1/obscura/grace` (runtime + `.env`) |
| **Sinalizador bridge/fallback** | Barra por agente (⚡ azul = bridge CDP · 🟡 amarelo = fallback urllib) + resumo no dashboard |
| **Alertas de queda** | Watcher (task asyncio, `OBSCURA_ALERT_INTERVAL` default 30s) detecta motor fora além da graça e envia alerta **Telegram** (🔴 queda / 🟢 recuperação), 1 por incidente; histórico nos últimos 20 fica no painel |
| **E2E em 1 comando** | `bash .e2e_all.sh` — roda pytest + healthz E2E (200→503→200) + via counters + grace config, com relatório PASS/FAIL |
| **🔀 Rotação de buscadores** | Google bloqueado → fallback **round-robin** entre Bing (`obscura_bing`), DuckDuckGo (`obscura_ddg`, HTML + decode do redirect) e Ecosia (`obscura_ecosia`) — distribui carga e reduz rate-limit; fonte real de cada SERP registrada na telemetria |
| **🕵️ Healthcheck de proxy** | Card "Proxy residencial" no painel com botão **testar** → `GET /api/v1/obscura/proxy-check` (latência + IP de saída; SOCKS avisado como não-testável via urllib) |
| **🔀 Fontes SERP por rodada** | Seção no painel com barras por fonte (obscura/bing/ddg/ecosia/regex) + botão **🔄 Nova rodada** + histórico das últimas 20 rodadas; só conta como sucesso quando a SERP veio com URLs |
| **💾 Rodadas persistidas no banco** | Cada `reset_serp_sources()` (início de rodada) salva o snapshot em `obscura_serp_runs` (fontes + bloqueios) — o histórico **sobrevive a restarts/deploys** e é exposto como `persisted_runs` no endpoint serp-sources |
| **🚫 Bloqueios por fonte** | Telemetria `serp_blocks` (google/bing/ddg/ecosia) no relatório e no painel — mostra quantas vezes o Google devolveu `/sorry/` CAPTCHA e quantas o fallback salvou; proxy residencial deve zerar o bloqueio do Google |
| **🌐 Chrome real como serviço** | `docker/chrome/Dockerfile` sobe o Chrome real headless (CDP 9223) como serviço no Railway (Root Directory `docker/chrome`) — o bridge tenta **Chrome primeiro** (`OBSCURA_CHROME_HOST`/`OBSCURA_CHROME_PORT`), senão Obscura; cadeia prod = local (Chrome → Google → fallback rotativo). Chrome 136+ ignora `--remote-debugging-address=0.0.0.0` → entrypoint usa o **cdp_proxy.py** (proxy TCP unificado, substitui socat + health_server): Chrome no loopback `OBSCURA_CHROME_INNER_PORT` default 9224 + proxy expondo `0.0.0.0:9223 → 127.0.0.1:9224` reescrevendo Host (anti-DNS-rebinding) e respondendo 200 p/ qualquer caminho não-CDP |
| **🩺 Healthcheck nativo nos motores** | `HEALTHCHECK` nos `docker/obscura/Dockerfile` (curl em `:9222/json/version`) e `docker/chrome/Dockerfile` (wget em `:9223/json/version`) — o Railway só marca o serviço healthy quando o CDP responde de verdade |

### 📊 Dashboard / Fábrica (admin)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/factory/dashboard` | Dashboard completo (canais, artigos, métricas) — **admin** |
| GET | `/api/v1/factory/francisco` | Relatório do Seu Francisco |
| GET | `/api/v1/factory/ze-status` | Status do Seu Zé |
| GET | `/api/v1/factory/monitor-stats` | Estatísticas do monitor |
| GET | `/api/v1/factory/openmontage-status` | Status OpenMontage |
| POST | `/api/v1/factory/build-app` | Construir aplicativo |
| GET | `/api/v1/factory/{...}` | Extras do dashboard |

### 📝 API de Blogs (público de leitura)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/blog/{slug}/info` | Informações do blog |
| GET | `/api/v1/blog/{slug}/posts` | Lista de artigos do blog |
| GET | `/api/v1/blog/{slug}/posts/{post_id}` | Artigo específico |
| POST | `/api/v1/blog/{slug}/posts/{post_id}/update` | Atualizar artigo |
| POST | `/api/v1/blog/{slug}/posts/{post_id}/generate-image` | Gerar imagem do artigo |
| GET | `/api/v1/blog/{slug}/subdomain` | Obter subdomínio |
| POST | `/api/v1/blog/{slug}/subdomain` | Configurar subdomínio |
| POST | `/api/v1/blog/{slug}/generate-banner` | Gerar banner do blog |
| POST | `/api/v1/blog/{slug}/update-affiliate` | Atualizar config do Modo Afiliado |
| POST | `/api/v1/blog/{slug}/update-modes` | Atualizar modos de exibição |
| POST | `/api/v1/blog/generate-article` | Gerar artigo via LLM |
| POST | `/api/v1/blog/generate-article-hype` | Gerar artigo "hype" — **admin** |
| POST | `/api/v1/blog/generate-batch` | Gerar lote de artigos |
| POST | `/api/v1/blog/generate-missing-images` | Gerar imagens pendentes |
| POST | `/api/v1/blog/import-posts` | Importar artigos |
| DELETE | `/api/v1/blog/post/{post_id}` | Deletar artigo — **admin** |
| POST | `/api/v1/blog/post/{post_id}/regenerate` | Regenerar post — **admin** |
| POST | `/api/v1/blog/post/{post_id}/regenerate-image` | Regenerar imagem — **admin** |
| DELETE | `/api/v1/blog/channel/{channel_id}` | Deletar canal — **admin** |
| POST | `/api/v1/blogs/seed` | Popular blogs de teste |

### 🌸 LiLi — Revisão (admin)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/lili/review/{post_id}` | Revisar artigo — **admin** |
| GET | `/api/v1/lili/review-all` | Revisar todos os artigos — **admin** |
| POST | `/api/v1/lili/correct/{post_id}` | Corrigir artigo — **admin** |
| GET | `/api/v1/lili/ranking` | Ranking LiLi — **admin** |
| POST | `/api/v1/lili/regenerate-batch` | Regenerar lote — **admin** |
| GET | `/api/v1/lili/regenerate-jobs/{job_id}` | Status do job — **admin** |
| GET | `/api/v1/lili/regenerate-jobs` | Lista de jobs — **admin** |

### 💰 Monetização & Afiliados
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/monetization/status` | Status Seu Pereira (AdSense) — **admin** |
| GET | `/api/v1/affiliate/clicks` | Cliques consolidados |
| GET | `/go/{post_slug}/{provider}` | Cloaking/redirect de afiliados |

### 🎨 Imagens
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/images/generate-cover` | Gerar capa |
| POST | `/api/v1/images/generate-blog-image` | Gerar imagem de blog |
| POST | `/api/v1/images/generate-thumbnail` | Gerar thumbnail |

### 🔍 Pesquisa
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/search` | Busca global — **admin** |
| POST | `/api/v1/research/niche` | Pesquisar nicho |
| POST | `/api/v1/research/channel` | Analisar canal YouTube |
| GET | `/api/v1/research/trending` | Tendências do YouTube |
| GET | `/api/v1/research/youtube-rules` | Regras do YouTube |
| POST | `/api/v1/spy/discover` | Descobrir oportunidades |
| POST | `/api/v1/rag/ask` | Perguntar ao RAG |
| POST | `/api/v1/rag/index` | Indexar no RAG |

### 📚 Livros / Ebooks
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/books` | Listar livros |
| POST | `/api/v1/books/generate` | Gerar livro |
| POST | `/api/v1/books/seed` | Popular livros de teste |
| GET | `/api/v1/books/{book_id}` | Detalhes do livro |
| GET | `/api/v1/ebooks` | Listar ebooks — **admin** |
| GET | `/api/v1/ebooks/{book_id}` | Detalhes do ebook (header OU `?token=`) — **admin** |
| DELETE | `/api/v1/ebooks/{book_id}` | Deletar ebook — **admin** |
| GET | `/api/v1/ebooks/{book_id}/chapters` | Capítulos do ebook |
| GET | `/api/v1/my-ebooks` | Ebooks do usuário |

### 🎓 Cursos (público)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/courses` | Listar cursos |
| GET | `/api/v1/courses/{course_id}` | Detalhes do curso |
| POST | `/api/v1/courses/generate` | Gerar curso |
| POST | `/api/v1/courses/seed` | Seed de cursos |

### 🏗️ Pipelines (todas admin)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/pipeline/run-blog-factory` | Iniciar macro-esteira de blog |
| GET | `/api/v1/pipeline/blog-factory/status/{task_id}` | Status da macro-esteira |
| GET | `/api/v1/pipeline/blog-factory/history` | Histórico |
| GET | `/api/v1/pipeline/blog/history` | Histórico de pipelines |
| GET | `/api/v1/pipeline/run-blog` | Iniciar pipeline de blog |
| POST | `/api/v1/pipeline/suggest-blog-idea` | Sugerir ideia de blog |
| POST | `/api/v1/pipeline/run-ebook-factory` | Iniciar fábrica de ebooks |
| GET | `/api/v1/pipeline/ebook-factory/status/{task_id}` | Status fábrica de ebooks |
| GET | `/api/v1/pipeline/ebook-factory/history` | Histórico |
| POST | `/api/v1/pipeline/run-course-factory` | Iniciar fábrica de cursos |
| GET | `/api/v1/pipeline/course-factory/status/{task_id}` | Status fábrica de cursos |
| GET | `/api/v1/pipeline/course-factory/history` | Histórico |
| GET | `/api/v1/pipeline/macro-result/{task_id}` | Resultado da macro-esteira |
| GET | `/api/v1/pipeline/active-tasks` | Tarefas ativas |
| GET | `/api/v1/pipeline/{task_id}` | Status de pipeline específico |
| GET | `/api/v1/pipeline` | Listar pipelines |
| POST | `/api/v1/pipeline/{task_id}/pause` | Pausar |
| POST | `/api/v1/pipeline/{task_id}/resume` | Retomar |
| POST | `/api/v1/pipeline/{task_id}/stop` | Parar |
| POST | `/api/v1/pipeline/{task_id}/approve/{stage}` | Aprovar estágio |

### 📢 Marketing Digital (admin)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/marketing/start` | Inicia campanha de marketing (cria `campaign_id` + persiste no banco) — **admin** |
| POST | `/api/v1/marketing/stage` | Executa fase 1–6 da esteira (Seu Tião → Dona Benta → Tonho → Zé do Traço → Chica → Valdir) e persiste o conteúdo — **admin** |
| GET | `/api/v1/marketing/history` | Histórico das últimas 20 campanhas (restauração de estado na UI) — **admin** |
| POST | `/api/v1/marketing/send-test-email` | Teste SMTP rápido (assunto/corpo customizáveis) — **admin** |
| POST | `/api/v1/marketing/publish-wordpress` | Publica a página de vendas/landing do funil no WordPress — **admin** |

### 📤 Distribuição Social (admin)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/distribution/status` | Status de configuração das plataformas (Email/Resend, Pinterest, Instagram, TikTok, Twitter/X) + stats — **admin** |
| POST | `/api/v1/distribution/config` | Salva token/config de uma plataforma em `data/social_config.json` — **admin** |
| GET | `/api/v1/distribution/history` | Histórico das últimas 100 publicações distribuídas — **admin** |
| POST | `/api/v1/distribution/post` | Dispara publicação numa plataforma (email/pinterest/instagram/tiktok/twitter) — **admin** |
| POST | `/api/v1/distribution/post/{post_id}` | Distribui UM artigo específico do blog (imagem de destaque + link canônico) — botão "📤 Distribuir" do painel — **admin** |
| GET | `/api/v1/distribution/schedule` | Status do agendador automático (enabled/interval_hours/last_run) — **admin** |
| POST | `/api/v1/distribution/schedule` | Configura o agendador: `{enabled, interval_hours}` (1–168h) — **admin** |
| POST | `/api/v1/distribution/run-all` | Dispara distribuição manual imediata de artigos recentes de todos os canais ativos — **admin** |

### 🌐 WordPress (admin)
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/wordpress/test` | Testa a conexão REST com as credenciais fornecidas — **admin** |
| POST | `/api/v1/wordpress/save-settings` | Salva `WP_URL`/`WP_USER`/`WP_APP_PASS` no ambiente — **admin** |
| POST | `/api/v1/blog/post/{post_id}/publish-wordpress` | Publica um post aprovado no WordPress (upload de imagem + post) — **admin** |

### 🖥️ MCP (admin)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/mcp/status` | Status dos servidores MCP (memory, filesystem, brave_search, wordpress) — **admin** |

### 📦 Entregáveis & Checkout
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/deliverables` | Listar apps |
| POST | `/api/v1/deliverables/create` | Criar app |
| GET | `/api/v1/deliverables/{slug}` | Detalhes do app |
| POST | `/api/v1/deliverables/checkout` | Checkout |
| POST | `/api/v1/deliverables/webhooks/mercadopago` | Webhook Mercado Pago |
| POST | `/api/v1/deliverables/webhooks/stripe` | Webhook Stripe |
| POST | `/api/v1/checkout/create` | Criar checkout |
| POST | `/api/v1/checkout/confirm` | Confirmar checkout |
| GET | `/api/v1/transactions` | Listar transações |

### 📊 Analytics
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/analytics/metrics` | Métricas |
| GET | `/api/v1/analytics/channels` | Analytics por canal |

### 🧠 Hermes Chat & Canais
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/hermes/chat` | Conversar com Hermes |
| GET | `/api/v1/hermes/history` | Histórico do chat |
| POST | `/api/v1/hermes/clear` | Limpar histórico |
| POST | `/api/v1/hermes/analyze-video` | Analisar vídeo concorrente |
| GET | `/api/v1/channels` | Listar canais |
| POST | `/api/v1/channels` | Criar canal |
| DELETE | `/api/v1/channels/{channel_id}` | Deletar canal |
| POST | `/api/v1/channels/{channel_id}/login-stealth` | Login stealth |
| GET | `/api/v1/channels/{channel_id}/connection-status` | Status da conexão |
| POST | `/api/v1/channels/{channel_id}/submit-2fa` | Enviar 2FA |
| GET | `/api/v1/channels/{channel_id}/knowledge` | Memória do canal |
| POST | `/api/v1/channels/{channel_id}/knowledge` | Adicionar memória |

### 📈 Predictions
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/predictions` | Criar predição |
| GET | `/api/v1/predictions/{prediction_id}/result` | Resultado da predição |
| GET | `/api/v1/predictions/history` | Histórico |
| POST | `/api/v1/predictions/{prediction_id}/approve` | Aprovar |
| POST | `/api/v1/predictions/{prediction_id}/reject` | Rejeitar |

### 🌐 Frontend HTML (Blog Viewer)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Painel admin legacy (SPA) — exige token admin (`?token=` ou header) |
| GET | `/app/{slug}` | App do canal |
| GET | `/blog/{slug}` | Página inicial do blog |
| GET | `/blog/{slug}/sobre` | Página Sobre |
| GET | `/blog/{slug}/contato` | Página Contato |
| GET | `/blog/{slug}/privacidade` | Política de Privacidade |
| GET | `/blog/{slug}/termos` | Termos de Uso |
| GET | `/ebook/{slug}/venda` | Página de vendas do ebook |
| GET | `/ebook/{token}/reader` | Leitor do ebook |
| GET | `/api/v1/ebook-reader/{token}/chapter/{n}` | Capítulo do leitor |
| GET | `/oreino`, `/o-reino` | Redirects de blog |
| GET | `/go/{post_slug}/{provider}` | Redirect de afiliado |
| GET | `/sitemap.xml` | Sitemap XML |
| GET | `/robots.txt` | Robots.txt |
| GET | `/ads.txt` | Ads.txt |

---

## 🖥️ DEZAFIRA ADM — Frontend (Next.js)

### Visão Geral

O **Dezafira Adm** é o painel de administração focado **100% nas fábricas de conteúdo** (Blog, Ebook, Curso e Marketing). Pagamentos, gamificação, combos e ranking foram **removidos** — o ecossistema prioriza produção e distribuição de conteúdo.

> 💡 A **área de membros** (checkout, tokens de acesso, leitor de ebooks, cursos do assinante) vive no **DezafiraClube** (SvelteKit — `Blog_Inteligente_SEO_com_IA_-_v1.8/`), não neste frontend. O checkout do Clube usa **Asaas** (`src/lib/server/asaas.ts`); a integração **Polar foi removida**.

### Tech Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| Backend | FastAPI (integrado ao server.py existente) |
| Auth | JWT (HMAC-SHA256) + bcrypt + Google OAuth |
| Deploy Frontend | Railway (root `club-frontend`) |
| Deploy Backend | Railway (root `/`, port 8080) |

### Autenticação

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/login` | Login (email + senha) |
| POST | `/api/v1/auth/google` | Login/registro via Google OAuth |
| POST | `/api/v1/auth/forgot-password` | Enviar email de recuperação |
| POST | `/api/v1/auth/reset-password` | Redefinir senha com token |
| GET | `/api/v1/auth/me` | Dados do usuário logado |
| POST | `/api/v1/auth/logout` | Encerrar sessão |

> `POST /api/v1/auth/register` ainda existe no backend, mas a página de registro no frontend foi removida (stub redireciona para `/auth/login`).

**Auth Flow:**
- Senhas: bcrypt com salt (não passlib — compatibilidade com bcrypt 5.0)
- JWT: HMAC-SHA256, expiração configurável
- Google OAuth: id_token validado, user criado automaticamente
- Sessões: armazenadas no banco (`user_sessions`)
- Tokens de reset: SHA-256, expiração 1h

### Painel do Usuário (`/painel`)

Dashboard simples do usuário logado (dados de `/api/v1/auth/me` + listas de cursos e ebooks). **Sem gamificação/ranking** (removidos).

### Páginas (Next.js — `club-frontend/`)

| Página | Rota | Descrição |
|--------|------|-----------|
| Landing | `/` | Página inicial focada nas fábricas ("Dezafira Adm") |
| Login | `/auth/login` | Formulário de login |
| Painel | `/painel` | Dashboard do usuário (tabs: Visão Geral, Cursos, Ebooks) |
| Admin | `/admin` | Painel admin (stats, usuários, fábricas, trilhas, analytics, marketing) |
| Fábrica Blog | `/admin/fabrica-blog` | iframe do painel legacy → `/#blogs` |
| Fábrica Ebook | `/admin/fabrica-ebook` | iframe do painel legacy → `/#books` |
| Fábrica Curso | `/admin/fabrica-curso` | Pipeline nativa de cursos (Next.js) |
| Fábrica Marketing | `/admin/fabrica-blog#marketing` | Aba no admin → iframe do painel legacy → `/#marketing` (esteira de 6 fases) |
| Trilhas | `/admin/trilhas` | Gestão de learning paths |
| Analytics | `/admin/analytics` | Métricas reais (cursos/trilhas) |

**Features UI:**
- Dark mode (indigo/purple gradient theme)
- JWT armazenado em `localStorage` (`dz_token`)
- Rotas protegidas: `/painel` exige login; `/admin/*` exige `role === "admin"`
- As fábricas Blog/Ebook/Marketing são um **iframe** do painel legacy (`static/index.html`) com token passado via `?token=` + hash `#blogs`/`#books`/`#marketing`
- Auth flow em `lib/auth-context.tsx` (AuthProvider + useAuth) — usa `api.getMe()` para restaurar sessão
- API client em `lib/api.ts` injeta `Authorization: Bearer` em todas as chamadas


## 🗄️ DATABASE MODELS

### Blog Channels (`blog_channels`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (blg_xxxx) |
| name | VARCHAR(100) | Nome do blog |
| nicho | VARCHAR(100) | Nicho temático |
| lang | VARCHAR(10) | Idioma (PT) |
| platform | VARCHAR(50) | Plataforma (wordpress) |
| site_url | VARCHAR(500) | URL do site |
| subdomain | VARCHAR(100) | Subdomínio (ex: oreino) |
| status | VARCHAR(20) | active/inactive |
| frequency | VARCHAR(20) | Frequência (daily) |
| created_at | DateTime | Data de criação |
| is_affiliate | BOOLEAN | Ativação do Modo Afiliado |
| affiliate_providers | VARCHAR(500) | Provedores separados por vírgula |
| amazon_tag | VARCHAR(100) | Tag de associado da Amazon |
| amazon_key | VARCHAR(200) | Key API Amazon |
| amazon_secret | VARCHAR(200) | Secret API Amazon |
| shopee_app_id | VARCHAR(100) | App ID Shopee |
| shopee_app_secret | VARCHAR(200) | Secret Shopee |
| mercadolivre_client_id | VARCHAR(100) | Client ID ML |
| mercadolivre_client_secret | VARCHAR(200) | Client Secret ML |
| mercadolivre_access_token | VARCHAR(1000) | Access Token ML |
| mercadolivre_refresh_token | VARCHAR(1000) | Refresh Token ML |
| mercadolivre_token_expires | TIMESTAMP | Expiração Token ML |



### Blog Posts (`blog_posts`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (post_xxxx) |
| channel_id | VARCHAR(50) FK | Canal do blog |
| title | VARCHAR(500) | Título do artigo |
| author | VARCHAR(200) | Autor (default: Equipe Dezafira) |
| slug | VARCHAR(500) | Slug para URL |
| content | TEXT | HTML completo do artigo |
| excerpt | VARCHAR(1000) | Resumo |
| keywords | VARCHAR(1000) | Palavras-chave |
| featured_image_url | VARCHAR(1000) | URL da imagem de destaque |
| status | VARCHAR(30) | draft/published |
| word_count | INTEGER | Contagem de palavras |
| topic | VARCHAR(500) | Tópico |
| created_at | DateTime | Data de criação |
| published_at | DateTime | Data de publicação |

### Blog Sections (`blog_sections`)
Micro-nichos/seções dentro de um blog para organização temática.

### Blog Pipeline Runs (`blog_pipeline_runs`)
Registro de estado das execuções do pipeline (checkpoint para retomada).

### Affiliate Clicks (`affiliate_clicks`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PK | ID autoincremento |
| post_id | VARCHAR(50) FK | Post associado ao clique |
| provider | VARCHAR(50) | Provedor (amazon, shopee, mercadolivre) |
| product_name | VARCHAR(200) | Nome do produto |
| clicked_at | DateTime | Data/Hora do clique |


### Books & Courses
Modelos completos para Livros e Cursos com:
- Chapters, Formats, Modules, Lessons, Materials, Quizzes
- Suporte a preço, dificuldade, status de publicação

### Ebook Access (Área de Membro)
Sistema de tokens para acesso a ebooks comprados:
- Token SHA-256 único por combinacao ebook + email
- Validação a cada requisição
- Suporte a múltiplos ebooks por comprador

### Knowledge (Shared Memory)
Armazenamento de aprendizados por canal — estilo, SEO, preferências.

---

## 🎨 BRANDING DINÂMICO

Cada blog recebe identidade visual personalizada por nicho:

| Tema | Cor Primária | Logo SVG | Favicon | Fonte |
|------|------------|----------|---------|-------|
| ✝ **Cristão** | #d4a853 (dourado) | Cruz com brilho | ✝ SVG | Crimson Text |
| 💰 **Finanças** | #22c55e (verde) | Cifrão | 💰 SVG | Inter |
| 🌿 **Saúde** | #06b6d4 (ciano) | Cruz verde | 🌿 SVG | Nunito |
| ⚡ **Tecnologia** | #6366f1 (índigo) | Triângulo | ⚡ SVG | Space Grotesk |
| 🏠 **Geral** | #f59e0b (âmbar) | Casa | 🏠 SVG | Lora |

### Recursos Frontend
- Dark mode (toggle + `prefers-color-scheme` + localStorage)
- Hero section com artigo em destaque
- Scroll-fade animations (IntersectionObserver)
- Reading progress bar
- Newsletter inline nos artigos
- Cookie banner LGPD (Aceitar/Rejeitar)
- Tipografia fluida com `clamp()`
- Design responsivo
- Breadcrumb navegação
- Seção "Leia Também" com artigos relacionados
- Sitemap XML dinâmico
- Robots.txt + Ads.txt

---

## ⚙️ DEPENDÊNCIAS PRINCIPAIS

| Pacote | Versão | Uso |
|--------|--------|-----|
| FastAPI | 0.110.0 | Framework web |
| SQLAlchemy | 2.0.28 | ORM Database |
| psycopg2-binary | 2.9.9 | PostgreSQL driver |
| httpx | 0.27.0 | HTTP async client |
| websockets | 13.0+ | WebSocket tempo real |
| apscheduler | 3.10+ | Agendamento |
| pydantic | 2.6.4 | Validação de dados |
| python-jose[cryptography] | 3.3.0 | JWT tokens |
| passlib[bcrypt] | 1.7.4 | Senhas (backup) |
| bcrypt | 4.2+ | Hash de senhas (direto) |
| python-multipart | 0.0.9 | Form data parsing |
| redis | 5.0.1 | Cache, rate limiting |

---

## 📋 SEU PEREIRA — CHECKLIST DE MONETIZAÇÃO

### Score Atual: 88.7% 🟢 (17/19) — ✅ Pronto para solicitar o AdSense

### 📝 Conteúdo (5/5 ✅)
| Item | Peso | Status |
|------|------|--------|
| 20+ artigos publicados | 8 | ✅ Requisito cumprido (contagem dinâmica no dashboard) |
| 800+ palavras por artigo | 8 | ✅ Média ~2.238 |
| Imagens em todos os artigos | 5 | ✅ 100% |
| Conteúdo 100% original | 10 | ✅ Gerado por IA |
| Nicho permitido pelo AdSense | 10 | ✅ Religioso/FE |

### 📄 Páginas Obrigatórias (3/3 ✅)
| Item | Peso | Status |
|------|------|--------|
| Política de Privacidade | 10 | ✅ Servida pelo sistema |
| Página Sobre Nós | 6 | ✅ Servida pelo sistema |
| Página de Contato | 6 | ✅ Servida pelo sistema |

### 🎨 Design & UX (3/3 ✅)
| Item | Peso | Status |
|------|------|--------|
| Design responsivo | 7 | ✅ CSS moderno |
| Navegação limpa | 5 | ✅ Com categorias |
| Velocidade adequada | 6 | ✅ FastAPI + SSR |

### 🔧 Técnico (4/5 ✅)
| Item | Peso | Status |
|------|------|--------|
| Domínio próprio | 9 | ✅ dezafira.com.br |
| SSL/HTTPS | 8 | ✅ Railway auto |
| Google Search Console | 7 | ❌ Único pendente |
| robots.txt | 4 | ✅ Servido |
| ads.txt | 5 | ✅ Servido |

### 🔍 Indexação & SEO (1/2 ⚠️)
| Item | Peso | Status |
|------|------|--------|
| Google indexado | 8 | ⏳ Dependente do GSC |
| Sitemap XML | 5 | ✅ Gerado |

### 🏛️ Autoridade E-E-A-T (1/1 ✅)
| Item | Peso | Status |
|------|------|--------|
| Credibilidade | 6 | ✅ Página Sobre |

---

## 🚀 PRÓXIMOS PASSOS (PRIORIZADOS)

### 🔴 Imediatos (Deploy + Monetização)
1. **Deploy Railway** — 2 serviços (Python backend + Node frontend)
2. **Conectar Google Search Console** — Verificar domínio em search.google.com
3. **Solicitar indexação** dos artigos no Google
4. **Google Analytics** para métricas de tráfego
5. **Publicar artigos em massa** via Seu Zé

### 🟡 Curto Prazo (Qualidade)
1. **Criar 3º blog** (saúde/bem-estar ou tecnologia) com branding único
2. **Compressão de imagens** para melhorar PageSpeed
3. **Otimizar Core Web Vitals** (LCP, FID, CLS)
4. **Schema.org** Article + FAQ + Breadcrumb em JSON-LD
5. **Email de confirmação** (SMTP/Resend) para novos registros

### 🟢 Médio Prazo (Monetização Avançada)
1. **Aplicar para Google AdSense** quando score > 80%
2. **Implementar afiliados** (Amazon, Hotmart, Eduzz)
3. **Newsletter por e-mail** (capturar leads)
4. **Mais trilhas de aprendizado** (criar trilhas por nicho)
5. **Certificados de conclusão** para cursos

### 🔵 Longo Prazo (Escala)
1. **Automatizar criação de 10+ blogs** em nichos variados
2. **Implementar rede de blogs** (subdomínios wildcard)
3. **Dashboard avançado** com receita por blog
4. **SEO Analytics** integrado
5. **API pública** para parceiros

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Atual | Meta 30 dias | Meta 90 dias |
|---------|-------|-------------|--------------|
| Blogs ativos | 2 | 5 | 15 |
| Artigos totais | 89 | 300 | 1.500 |
| Cursos criados | 2 | 10 | 30 |
| Trilhas ativas | 1 | 3 | 10 |
| Score AdSense | 88.7% | 95% | 98% |
| Visitantes/mês | 0 | 1.000 | 50.000 |
| Receita/mês | R$ 34 | R$ 200 | R$ 5.000 |

---

## 🏗️ MACRO-ESTEIRA (Pipeline)

### Fase 1 — Fundação 🏗️
**Agentes:** Seu Hermes + Dona Célia  
**Peso:** 10%  
**Ações:** Cria blog no banco, define brand bible, identidade visual, cores, logo, favicon

### Fase 2 — Arquitetura 📋
**Agentes:** Joaquim + Obscura  
**Peso:** 15%  
**Ações:** Pesquisa keywords, mapeia seções e subnichos, gera pauta de 35 artigos

### Fase 3 — Produção 📝
**Agentes:** Carlão + LiLi + Ricardo  
**Peso:** 55%  
**Ações:** Gera artigos em lotes, revisa qualidade (LiLi), gera imagem (Ricardo)

### Fase 4 — Refino 🎨
**Agentes:** Tatiana + Ricardo + Seu Zé  
**Peso:** 15%  
**Ações:** Links internos, imagens pendentes, agendamento

### Fase 5 — Entrega ✅
**Agentes:** Seu Francisco  
**Peso:** 5%  
**Ações:** Confere estoque, valida qualidade, libera blog

---

## 📚 FÁBRICA DE EBOOKS (Nova)

### Visão Geral
Sistema completo de criação e venda de ebooks low-ticket (R$17-97) com pipeline de 6 fases, página de vendas e área de membro.

### Pipeline de 6 Fases

| Fase | Nome | Agentes | Descrição |
|------|------|---------|-----------|
| 1 | **Fundação** | Hermes + Dona Célia | Cria ebook no banco, gera título, branding |
| 2 | **Pesquisa de Dores** | Minerador de Dores + Obscura | Reddit, PAA, keywords, ranking de dores |
| 3 | **Criar Oferta** | Copywriter Infoprodutos | Mecanismo único, promessa, bônus, preço |
| 4 | **Produção** | Carlão + LiLi | Capítulo a capítulo com revisão de qualidade |
| 5 | **Refino** | Formatter | HTML formatado + página de vendas |
| 6 | **Entrega** | Seu Francisco | Produto criado, token de acesso gerado |

### Endpoints da Pipeline

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/pipeline/run-ebook-factory` | Inicia pipeline |
| GET | `/api/v1/pipeline/ebook-factory/status/{task_id}` | Polling de status |
| GET | `/api/v1/pipeline/ebook-factory/history` | Histórico de execuções |
| GET | `/api/v1/ebooks` | Lista todos os ebooks |
| GET | `/api/v1/ebooks/{book_id}` | Detalhes do ebook |
| DELETE | `/api/v1/ebooks/{book_id}` | Deleta ebook |

### Checkout e Área de Membro

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/checkout/create` | Cria sessão de checkout |
| POST | `/api/v1/checkout/confirm` | Confirma pagamento + gera token |
| GET | `/api/v1/my-ebooks?email=` | Lista ebooks por email |
| GET | `/ebook/{slug}/venda` | Página de vendas HTML |
| GET | `/ebook/{token}/reader` | **Leitor HTML (área de membro)** |
| GET | `/api/v1/ebook-reader/{token}/chapter/{n}` | API de capítulo |

### Fluxo de Compra

```
Página de Vendas → Checkout → Confirmação → Token Gerado → Leitor HTML
```

### Database Models

#### Books (`books`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (book_xxxx) |
| title | VARCHAR(500) | Título do ebook |
| niche | VARCHAR(100) | Nicho temático |
| style_id | VARCHAR(30) | Estilo visual |
| price_cents | INTEGER | Preço em centavos |
| sales_page_html | TEXT | HTML da página de vendas |
| sales_page_slug | VARCHAR(200) | Slug da página de vendas |
| status | VARCHAR(20) | draft/published |

#### Book Chapters (`book_chapters`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (bch_xxxx) |
| book_id | VARCHAR(50) FK | Ebook associado |
| chapter_number | INTEGER | Número do capítulo |
| title | VARCHAR(500) | Título do capítulo |
| content | TEXT | HTML do conteúdo |
| word_count | INTEGER | Contagem de palavras |

#### Products (`products`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (prod_xxxx) |
| book_id | VARCHAR(50) FK | Ebook associado |
| name | VARCHAR(200) | Nome do produto |
| price_cents | INTEGER | Preço em centavos |
| status | VARCHAR(20) | active/inactive |

#### Transactions (`transactions`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (txn_xxxx) |
| product_id | VARCHAR(50) FK | Produto associado |
| buyer_email | VARCHAR(200) | Email do comprador |
| buyer_name | VARCHAR(200) | Nome do comprador |
| amount_cents | INTEGER | Valor em centavos |
| status | VARCHAR(20) | pending/completed/refunded |
| payment_method | VARCHAR(20) | pix/credit_card/boleto |

#### Ebook Access (`ebook_access`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (eacc_xxxx) |
| token | VARCHAR(200) UK | Token SHA-256 de acesso |
| book_id | VARCHAR(50) FK | Ebook associado |
| transaction_id | VARCHAR(50) FK | Transação associada |
| buyer_email | VARCHAR(200) | Email do comprador |
| buyer_name | VARCHAR(200) | Nome do comprador |
| is_active | BOOLEAN | Token ativo |

### Leitor HTML

O leitor é uma página completa com:
- Header dourado com nome do comprador
- Sumário clicável
- Navegação anterior/próximo
- Tipografia Merriweather (conforto de leitura)
- Design responsivo mobile

### Geração de Token

```python
token = sha256(book_id + ":" + buyer_email + ":" + SECRET_KEY)[:48]
```

- Token é único por combinacao ebook + email
- Idempotente (não duplica)
- Validação a cada requisição

---

## 🎓 FÁBRICA DE CURSOS (Nova)

### Visão Geral
Pipeline automatizado de criação de cursos online com 6 fases e 5 agentes especializados. Gera cursos completos com módulos, aulas, materiais de apoio e quiz — prontos para venda na Dezafira Club.

### Pipeline de 6 Fases

| Fase | Nome | Agentes | Descrição |
|------|------|---------|-----------|
| 1 | **Fundação** | Professor + Pedagogo | Define tema, público-alvo, objetivos de aprendizagem, estrutura curricular |
| 2 | **Pesquisa** | Professor | Conteúdo técnico, referências, fontes, normatizações do nicho |
| 3 | **Estrutura** | Pedagogo | Módulos, aulas, sequência didática, mapas conceituais |
| 4 | **Produção** | Professor + Lili Cursos | Conteúdo das aulas (texto, exercícios, materiais) com revisão de qualidade |
| 5 | **Refino** | Quiz Master + Capa | Quiz por aula, avaliação final, capa visual do curso |
| 6 | **Entrega** | Capa | Thumbnails, pré-visualização, publicação na plataforma |

### Agentes Especializados

| Agente | Arquivo | Responsabilidades |
|--------|---------|-------------------|
| 🧑‍🏫 **Professor** | `modules/course_professor.py` | Conteúdo técnico, script de aulas, referências bibliográficas |
| 📐 **Pedagogo** | `modules/course_pedagogue.py` | Estrutura curricular, taxonomia de Bloom, sequência didática |
| 🌸 **Lili Cursos** | `modules/lili_cursos.py` | Revisão pedagógica e técnica (derivado da LiLi original) |
| ❓ **Quiz Master** | `modules/quiz_master.py` | Gera quiz por aula, avaliação final, gabarito, métricas |
| 🎨 **Capa** | `modules/course_cover.py` | Capa visual, thumbnails, identidade do curso |

### Endpoints da Pipeline

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/pipeline/run-course-factory` | Inicia pipeline de curso |
| GET | `/api/v1/pipeline/course-factory/status/{task_id}` | Polling de status |
| GET | `/api/v1/pipeline/course-factory/history` | Histórico de execuções |

### Endpoints Admin CRUD (Cursos)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/courses` | Listar todos os cursos |
| POST | `/api/v1/courses` | Criar curso |
| GET | `/api/v1/courses/{course_id}` | Detalhes do curso |
| PUT | `/api/v1/courses/{course_id}` | Atualizar curso |
| DELETE | `/api/v1/courses/{course_id}` | Deletar curso |
| POST | `/api/v1/courses/{course_id}/publish` | Publicar curso |
| POST | `/api/v1/courses/{course_id}/unpublish` | Despublicar curso |

### Endpoints Learning Paths

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/learning-paths` | Listar learning paths |
| POST | `/api/v1/learning-paths` | Criar learning path |
| GET | `/api/v1/learning-paths/{path_id}` | Detalhes do learning path |
| PUT | `/api/v1/learning-paths/{path_id}` | Atualizar learning path |
| DELETE | `/api/v1/learning-paths/{path_id}` | Deletar learning path |
| POST | `/api/v1/learning-paths/{path_id}/courses` | Adicionar curso ao path |
| DELETE | `/api/v1/learning-paths/{path_id}/courses/{course_id}` | Remover curso do path |

### Endpoints Analytics

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/courses/analytics/overview` | Métricas gerais de cursos |
| GET | `/api/v1/courses/{course_id}/analytics` | Métricas do curso específico |
| GET | `/api/v1/courses/{course_id}/enrollments` | Matrículas do curso |

### Estrutura do Curso

```
Course
├── CourseModule (1..N)
│   ├── CourseLesson (1..N)
│   │   ├── CourseMaterial (0..N)   — PDFs, links, anexos
│   │   └── CourseQuiz (0..1)       — Quiz da aula
│   └── ...
├── CourseQuiz (final)              — Avaliação final
└── CourseCover                     — Capa visual
```

### Database Tables (Novas)

#### CoursePipelineRun (`course_pipeline_runs`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (cpip_xxxx) |
| course_id | VARCHAR(50) FK | Curso associado |
| phase | INTEGER | Fase atual (1-6) |
| status | VARCHAR(20) | running/completed/failed |
| agent_log | JSONB | Log detalhado por agente |
| started_at | DateTime | Início da execução |
| completed_at | DateTime | Conclusão |

#### LearningPath (`learning_paths`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (lp_xxxx) |
| name | VARCHAR(200) | Nome do trilha |
| description | TEXT | Descrição |
| slug | VARCHAR(200) UK | Slug para URL |
| cover_url | VARCHAR(500) | URL da capa |
| status | VARCHAR(20) | active/inactive |
| created_at | DateTime | Criação |

#### LearningPathCourse (`learning_path_courses`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (lpc_xxxx) |
| path_id | VARCHAR(50) FK | Learning path |
| course_id | VARCHAR(50) FK | Curso |
| order_index | INTEGER | Ordem no path |

### Fluxo do Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Fase 1      │    │  Fase 2      │    │  Fase 3      │
│  Fundação    │───▶│  Pesquisa    │───▶│  Estrutura   │
│  Prof + Ped  │    │  Professor   │    │  Pedagogo    │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Fase 6      │    │  Fase 5      │    │  Fase 4      │
│  Entrega     │◀───│  Refino      │◀───│  Produção    │
│  Capa        │    │  Quiz + Capa │    │  Prof + Lili │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## 📢 FÁBRICA DE MARKETING (Nova)

### Visão Geral
Esteira de 6 fases de Marketing Digital baseada no **Sabri Suby Framework**, com 6 agentes brasileiros e execução **sequencial por fase** (`POST /api/v1/marketing/stage` com `stage` 1–6). Cada fase usa a **cascata de LLMs gratuitos** e a Fase 1 integra o **Obscura** para buscar buscas reais do Google. O conteúdo gerado persiste em `marketing_campaigns` — a UI restaura o estado a qualquer momento (sobrevive a restarts).

### Fluxo do Pipeline

```
1. Seu Tião (Avatar) → 2. Dona Benta (Iscas) → 3. Tonho (Anúncios AIDA)
→ 4. Zé do Traço (Landing Page) → 5. Chica (E-mails + SMTP) → 6. Seu Valdir (Oferta)
```

### Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/marketing/start` | Cria campanha + `campaign_id` |
| POST | `/api/v1/marketing/stage` | Executa fase 1–6 |
| GET | `/api/v1/marketing/history` | Histórico de campanhas (restauração UI) |
| POST | `/api/v1/marketing/send-test-email` | Teste SMTP |
| POST | `/api/v1/marketing/publish-wordpress` | Publica funil no WordPress |

### UI
- **Painel legacy** (`static/index.html`): nav **📢 Marketing Digital** com esteira visual de 6 fases, output por fase e histórico restaurado
- **Club admin** (Next.js): aba **Fábrica Marketing** (`/admin` → iframe `/#marketing`)
- **WordPress:** botão **🌐 Publicar no WP** no funil + página 🌐 WordPress com teste de conexão e credenciais

---

## 🔐 AUTENTICAÇÃO ADMIN & SEGURANÇA

### Controle de Acesso às Fábricas

Todas as fábricas (Blog, Ebook, Curso) são acessíveis apenas por usuários com `role="admin"`.

**Backend** — endpoints administrativos protegidos com `Depends(require_admin)`:

| Endpoint | Método | Uso |
|----------|--------|-----|
| `/api/v1/pipeline/run-blog-factory` | POST | Iniciar fábrica de blogs |
| `/api/v1/pipeline/blog-factory/history` | GET | Histórico |
| `/api/v1/pipeline/run-ebook-factory` | POST | Iniciar fábrica de ebooks |
| `/api/v1/pipeline/ebook-factory/history` | GET | Histórico |
| `/api/v1/pipeline/suggest-blog-idea` | POST | Sugerir ideia |
| `/api/v1/factory/dashboard` | GET | Dashboard |
| `/api/v1/blog/generate-article-hype` | POST | Gerar artigos hype |
| `/api/v1/blog/post/{post_id}` | DELETE | Deletar post |
| `/api/v1/blog/post/{post_id}/regenerate*` | POST | Regenerar post/imagem |
| `/api/v1/blog/channel/{channel_id}` | DELETE | Deletar canal |
| `/api/v1/lili/*` | GET/POST | Revisão e correção LiLi |
| `/api/v1/monetization/status` | GET | Status monetização |
| `/api/v1/search` | GET | Busca global |
| `/api/v1/ebooks` | GET | Lista ebooks |
| `/api/v1/ebooks/{book_id}` | GET/DELETE | Detalhe/delete (GET aceita `?token=`) |

**Painel admin legacy** (`GET /`) exige token admin via:
- Header `Authorization: Bearer <token>` 
- Ou query string `?token=<token>` (usado pelo iframe do frontend)

**Frontend Adm** — páginas `/admin/*` verificam `user.role === "admin"` antes de renderizar.

### Endpoints públicos (intencionalmente abertos)
- `/api/v1/blog/{slug}/posts` (GET)
- `/api/v1/blog/{slug}/info` (GET)

### Passagem de token ao painel legacy (iframe)
1. `api.getToken()` retorna o JWT armazenado no `localStorage`
2. Página Next.js monta URL: `https://backend/?token=<jwt>#blogs` (ou `#books`)
3. `static/index.html` lê o token da URL, guarda em `localStorage` e envia `Authorization` em todos os fetch
4. Backend valida o token (`_verify_jwt_token`) e o papel admin

### Dependências de autenticação (server.py)
```python
async def get_current_user(authorization: str = Header(None)): ...
async def get_optional_user(authorization: str = Header(None)): ...
async def require_admin(user=Depends(get_current_user)): ...
```

## 🔐 VARIÁVEIS DE AMBIENTE

```
# LLM Cascade (ordem real: OpenRouter → Gemini → NVIDIA NIM → HuggingFace → DeepSeek)
OPENROUTER_API_KEY=sk-or-...
GEMINI_API_KEY=AI...
NVIDIA_API_KEY=nvapi-...
HUGGINGFACE_TOKEN=hf_...
DEEPSEEK_API_KEY=sk-...

# Banco
DATABASE_URL=postgresql://...

# Auth
SECRET_KEY=sua-chave-secreta-aqui
GOOGLE_CLIENT_ID=...

# Imagens
PEXELS_API_KEY=...
UNSPLASH_ACCESS_KEY=...

# Obscura / Chrome (serviços Railway)
OBSCURA_ENABLED=true
OBSCURA_HOST=obscura.railway.internal
OBSCURA_PORT=9222
OBSCURA_CHROME_HOST=chrome.railway.internal
OBSCURA_CHROME_PORT=9223
OBSCURA_SERP_DELAY=1.5
OBSCURA_PROXY_URL=          # opcional — proxy residencial
OBSCURA_HEALTH_GRACE=300    # graça do healthcheck em segundos

# WordPress
WP_URL=https://seusite.com
WP_USER=admin
WP_APP_PASS=xxxx xxxx xxxx xxxx

# SMTP (Chica dos Correios / teste de e-mail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...
SMTP_SENDER=...
```

---

## 🐳 DEPLOY

### Backend (Railway)
**Root Directory:** `/` (raiz do repo `dezafira2.0`)  
**Builder:** Dockerfile  
**Dockerfile Path:** `/Dockerfile`  
**Healthcheck Path:** `/healthz` (200 com motor OK ou dentro da graça · 503 além de `OBSCURA_HEALTH_GRACE` — reinicia o backend)  
**Port:** 8080  
**Domínio:** `dezafiraadm-production.up.railway.app`  
**Envs:** `DATABASE_URL`, `AUTH_SECRET` (ou `SECRET_KEY`) ⚠️ **OBRIGATÓRIO desde 08/2026**: o backend **não sobe** sem ele (mínimo 16 chars; o fallback hardcoded foi removido por segurança) · chaves LLM, Redis, Obscura/Chrome, WP, SMTP

### Frontend Club (Railway)
**Root Directory:** `club-frontend`  
**Builder:** Dockerfile (auto-detectado)  
**Port:** 8080  
**Domínio:** `dezafira.com.br`  
**Envs:** `NEXT_PUBLIC_API_URL=https://dezafiraadm-production.up.railway.app`

### 🕵️ Obscura Engine (Railway — serviço dedicado)
**Root Directory:** `docker/obscura`  
**Builder:** Dockerfile padrão (Railpack detecta sozinho)  
**Porta interna:** 9222 (CDP)  
**DNS privado:** `obscura.railway.internal`  
**Envs:** `OBSCURA_WORKERS=4`, `OBSCURA_PROXY_URL=` (opcional)  
**Healthcheck:** `HEALTHCHECK` nativo (`curl :9222/json/version`)  
**Detalhes:** `docs/obscura_railway.md`

### 🌐 Chrome real (Railway — serviço dedicado)
**Root Directory:** `docker/chrome`  
**Builder:** Dockerfile padrão (Railpack detecta sozinho)  
**Porta interna:** 9223 (CDP via `cdp_proxy.py`)  
**DNS privado:** `chrome.railway.internal`  
**Envs:** `OBSCURA_CHROME_INNER_PORT=9224`  
**Healthcheck:** `HEALTHCHECK` nativo (`wget :9223/json/version`)  
**Por quê:** Chrome 136+ ignora `--remote-debugging-address=0.0.0.0` → entrypoint usa o **cdp_proxy.py** (proxy TCP unificado, substitui socat + health_server): Chrome no loopback 9224 + proxy expondo `0.0.0.0:9223 → 127.0.0.1:9224` reescrevendo Host e respondendo 200 p/ qualquer caminho não-CDP; o bridge conecta via **IP resolvido** (`_resolve_ip`) para contornar a proteção anti DNS-rebinding do Chrome 136+

### Banco de Dados (Railway PostgreSQL)
**Domínio:** `reseau.proxy.rlwy.net:26643`  
**Banco:** `railway`
**Redis:** já vinculado ao Railway

---

*Documentação gerada em 03/08/2026 — Dezafira Club v3.3*
