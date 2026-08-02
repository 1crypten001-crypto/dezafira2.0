# DEZAFIRA — Fábrica de Blogs & Dezafira Club

> **Versão:** 3.2.0  
> **Produção (Frontend + Admin):** https://dezafira.com.br (Railway)  
> **API Backend:** https://backend-production-f90d.up.railway.app  
> **Database:** PostgreSQL + Redis (Railway)  
> **Última atualização:** 01/08/2026

---

## 📋 VISÃO GERAL

A Dezafira é um ecossistema de **fábricas de conteúdo digital** com IA — Blogs, Ebooks, Cursos e uma área de membros completa com gamificação (**Dezafira Club**).

### Estado Atual

| Métrica | Valor |
|---|---|
| **Canais de Blog** | 2 (O Reino + Vida Financeira) |
| **Total de Artigos** | 89 |
| **Palavras Geradas** | ~199.000+ |
| **Artigos com Imagem** | 100% |
| **Score Monetização** | 88.7% (17/18) — ✅ Pronto AdSense |
| **Cursos Criados** | 2 (1 via pipeline automática) |
| **Trilhas de Aprendizado** | 1 (Trilha IA para Iniciantes) |
| **Fábricas Ativas** | Blog (5 fases) + Ebook (6 fases) + Curso (6 fases) |
| **Agentes IA** | 15+ especializados |
| **LLM Cascade** | Gemini → OpenRouter → GitHub → Groq → Anthropic |

### Blogs Ativos

| Blog | Nicho | Artigos | Imagens | Subdomínio |
|---|---|---|---|---|
| ✝ **O Reino** | Ensinamentos de Jesus | 41 | 100% | oreino |
| 💰 **Vida Financeira** | Finanças pessoais | 48 | 100% | vida-financeira |

---

## 🏗️ ARQUITETURA DO SISTEMA

```
┌──────────────────────────────────────────────────────────────────────┐
│                 FRONTEND CLUB — Next.js 14 (Railway)                 │
│        Landing │ Auth │ Painel │ Admin │ Fábricas │ Combos           │
│        https://dezafira.com.br (dezafira.railway.internal)           │
│        ANEXA o painel legacy via <iframe> com token ?token=           │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ chamadas API diretas (fetch → backend)
┌──────────────────────────▼───────────────────────────────────────────┐
│              BACKEND — FastAPI (Railway) — 167 endpoints              │
│        https://backend-production-f90d.up.railway.app (port 8080)     │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │       🔐 Auth & Member System (JWT + bcrypt + Google OAuth)      ││
│  │  Register │ Login │ Recovery │ Points │ Badges │ Streak │ Rank   ││
│  │  Course Tracks │ Combos │ Ebooks │ Admin (require_admin)         ││
│  └──────────────────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │       🏭 Fábricas / Pipelines (todas admin-gated)                ││
│  │  📝 Blog Factory(5 fases) │ 📗 Ebook Factory(6) │ 🎓 Curso(6)    ││
│  │  LiLi Reviewer · LlM Cascade(5) · Redis · Modelos               ││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────┬───────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│              PostgreSQL (Railway) — 30+ tabelas                       │
│             Blog Channels/Posts/Sections │ Books │ Users              │
│             Sessions │ Points │ Badges │ Streaks │ Courses            │
│             LearningPaths │ Combos │ Purchases │ Ebook Accesses      │
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

---

## 📡 ENDPOINTS DA API

> **Base:** `https://backend-production-f90d.up.railway.app` · **167 endpoints no total.**
> **Autenticação:** `Authorization: Bearer <JWT>`. Endpoints de **admin** (`/admin/*`, pipelines, ebooks, lili, search, monetization) exigem `require_admin` (401 sem token de admin).

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
| **🌐 Chrome real como serviço** | `Dockerfile.chrome` sobe o Chrome real headless (CDP 9223) como serviço no Railway — o bridge tenta **Chrome primeiro** (`OBSCURA_CHROME_HOST`/`OBSCURA_CHROME_PORT`), senão Obscura; cadeia prod = local (Chrome → Google → fallback rotativo) |
| **🩺 Healthcheck nativo nos motores** | `HEALTHCHECK` nos `Dockerfile.obscura` (curl em `:9222/json/version`) e `Dockerfile.chrome` (wget em `:9223/json/version`) — o Railway só marca o serviço healthy quando o CDP responde de verdade |

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

## 🏠 DEZAFIRA CLUB — Área de Membro

### Visão Geral
Área de membros completa com autenticação, gamificação, cursos e combos. Frontend Next.js separado, backend integrado no FastAPI existente.

### Tech Stack
| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js 14.2.35 (App Router) + Tailwind CSS |
| Backend | FastAPI (integrado ao server.py existente) |
| Auth | JWT (HMAC-SHA256) + bcrypt + Google OAuth |
| Deploy Frontend | Railway (root `/SniperVideoEngine/club-frontend`) |
| Deploy Backend | Railway (root `/SniperVideoEngine`, port 8080) |

### Autenticação

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/register` | Registro (email + senha) |
| POST | `/api/v1/auth/login` | Login (email + senha) |
| POST | `/api/v1/auth/google` | Login/registro via Google OAuth |
| POST | `/api/v1/auth/forgot-password` | Enviar email de recuperação |
| POST | `/api/v1/auth/reset-password` | Redefinir senha com token |
| GET | `/api/v1/auth/me` | Dados do usuário logado |
| POST | `/api/v1/auth/logout` | Encerrar sessão |

**Auth Flow:**
- Senhas: bcrypt com salt (não passlib — compatibilidade com bcrypt 5.0)
- JWT: HMAC-SHA256, expiração configurável
- Google OAuth: id_token validado, user criado automaticamente
- Sessões: armazenadas no banco (user_sessions)
- Tokens de reset: SHA-256, expiração 1h

### Área de Membro (Dashboard)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/member/dashboard` | Resumo do membro (pontos, badges, cursos) |
| GET | `/api/v1/member/points` | Histórico de pontos |
| GET | `/api/v1/member/badges` | Badges conquistadas |
| GET | `/api/v1/member/streak` | Sequência diária |
| GET | `/api/v1/member/courses` | Cursos matriculados |
| POST | `/api/v1/member/courses/{course_id}/enroll` | Matricular-se no curso |
| POST | `/api/v1/member/lessons/{lesson_id}/complete` | Marcar aula como concluída |
| GET | `/api/v1/ranking` | Ranking global |
| GET | `/api/v1/ebooks/{book_id}/chapters` | Capítulos do ebook |

### Gamificação

| Ação | Pontos |
|------|--------|
| Login diário | +10 |
| Completar aula | +25 |
| Completar módulo | +50 |
| Completar curso | +200 |
| Comprar ebook | +30 |
| Indicar amigo | +100 |

**Badges:**
- 🎯 Primeiro Passo — Primeira aula completada
- 🔥 Em Chamas — 7 dias consecutivos
- 📚 Leitor — 3 ebooks comprados
- 🎓 Formado — 1 curso completo
- 🏆 Mestre — 1000 pontos totais

**Ranking Global:**
- Top 10 do mês
- Top 10 geral

### Combos (Ebook + Curso)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/combos` | Listar combos disponíveis |
| GET | `/api/v1/combos/{slug}` | Detalhes do combo |
| POST | `/api/v1/combos/{id}/purchase` | Iniciar compra do combo |
| POST | `/api/v1/combos/{id}/confirm` | Confirmar pagamento |
| POST | `/api/v1/admin/combos` | Criar combo (admin) |
| DELETE | `/api/v1/admin/combos/{id}` | Deletar combo (admin) |

**Desconto:** 30% ao comprar ebook + curso juntos

### Admin Panel

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/admin/users` | Listar todos os usuários — **admin** |
| GET | `/api/v1/admin/stats` | Estatísticas gerais — **admin** |
| GET | `/api/v1/ranking` | Ranking global |

#### Admin — Cursos (CRUD)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/admin/courses` | Listar cursos — **admin** |
| POST | `/api/v1/admin/courses` | Criar curso — **admin** |
| GET | `/api/v1/admin/courses/{course_id}` | Detalhes — **admin** |
| PUT | `/api/v1/admin/courses/{course_id}` | Atualizar — **admin** |
| DELETE | `/api/v1/admin/courses/{course_id}` | Deletar — **admin** |
| POST | `/api/v1/admin/courses/{course_id}/publish` | Publicar — **admin** |
| POST | `/api/v1/admin/courses/{course_id}/unpublish` | Despublicar — **admin** |

#### Admin — Learning Paths
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/admin/learning-paths` | Listar trilhas — **admin** |
| POST | `/api/v1/admin/learning-paths` | Criar trilha — **admin** |
| GET | `/api/v1/admin/learning-paths/{path_id}` | Detalhes — **admin** |
| PUT | `/api/v1/admin/learning-paths/{path_id}` | Atualizar — **admin** |
| DELETE | `/api/v1/admin/learning-paths/{path_id}` | Deletar — **admin** |
| POST | `/api/v1/admin/learning-paths/{path_id}/courses` | Adicionar curso — **admin** |
| DELETE | `/api/v1/admin/learning-paths/{path_id}/courses/{course_id}` | Remover curso — **admin** |

#### Admin — Analytics
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/admin/analytics/overview` | Resumo analítico — **admin** |
| GET | `/api/v1/admin/analytics/courses` | Analytics de cursos — **admin** |

#### Trilhas Públicas
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/learning-paths` | Listar trilhas públicas |
| GET | `/api/v1/learning-paths/{slug}` | Detalhes da trilha

### Database Tables (Novas)

#### Users (`users`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único (usr_xxxx) |
| email | VARCHAR(200) UK | Email do usuário |
| name | VARCHAR(200) | Nome completo |
| password_hash | VARCHAR(200) | Hash bcrypt da senha |
| google_id | VARCHAR(100) | ID do Google OAuth |
| avatar_url | VARCHAR(500) | URL do avatar |
| role | VARCHAR(20) | user/admin |
| created_at | DateTime | Data de criação |
| last_login | DateTime | Último login |

#### User Sessions (`user_sessions`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID da sessão |
| user_id | VARCHAR(50) FK | Usuário associado |
| token | VARCHAR(500) UK | JWT token |
| created_at | DateTime | Criação |
| expires_at | DateTime | Expiração |

#### Password Resets (`password_resets`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único |
| user_id | VARCHAR(50) FK | Usuário associado |
| token | VARCHAR(200) UK | Token de reset |
| expires_at | DateTime | Expiração (1h) |
| used | BOOLEAN | Já utilizado |

#### User Points (`user_points`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único |
| user_id | VARCHAR(50) FK | Usuário associado |
| points | INTEGER | Pontos ganhos |
| action | VARCHAR(50) | Ação realizada |
| reference_id | VARCHAR(50) | ID referência |
| created_at | DateTime | Data |

#### User Badges (`user_badges`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único |
| user_id | VARCHAR(50) FK | Usuário associado |
| badge_name | VARCHAR(100) | Nome da badge |
| badge_icon | VARCHAR(50) | Emoji/ícone |
| earned_at | DateTime | Conquistada em |

#### User Streaks (`user_streaks`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único |
| user_id | VARCHAR(50) FK | Usuário associado |
| streak_count | INTEGER | Dias consecutivos |
| last_active_date | DATE | Último dia ativo |

#### Course Tracks (`course_tracks`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único |
| user_id | VARCHAR(50) FK | Usuário |
| course_id | VARCHAR(50) FK | Curso |
| enrolled_at | DateTime | Matrícula |
| completed_at | DateTime | Conclusão |
| progress_pct | INTEGER | Progresso 0-100 |

#### Lesson Progress (`lesson_progress`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único |
| track_id | VARCHAR(50) FK | Course track |
| lesson_id | VARCHAR(50) FK | Aula |
| completed | BOOLEAN | Concluída |
| completed_at | DateTime | Conclusão |

#### Combos (`combos`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único |
| name | VARCHAR(200) | Nome do combo |
| slug | VARCHAR(200) UK | Slug para URL |
| description | TEXT | Descrição |
| book_id | VARCHAR(50) FK | Ebook incluso |
| course_id | VARCHAR(50) FK | Curso incluso |
| original_price_cents | INTEGER | Preço original |
| combo_price_cents | INTEGER | Preço com desconto |
| discount_pct | INTEGER | Percentual desconto |
| status | VARCHAR(20) | active/inactive |
| created_at | DateTime | Criação |

#### Combo Purchases (`combo_purchases`)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | VARCHAR(50) PK | ID único |
| combo_id | VARCHAR(50) FK | Combo comprado |
| user_id | VARCHAR(50) FK | Comprador |
| amount_cents | INTEGER | Valor pago |
| status | VARCHAR(20) | pending/completed |
| created_at | DateTime | Compra |

### Frontend (Next.js — `club-frontend/`)

| Página | Rota | Descrição |
|--------|------|-----------|
| Landing | `/` | Página inicial com hero, combos, ranking |
| Login | `/auth/login` | Formulário de login |
| Registro | `/auth/register` | Formulário de registro |
| Painel | `/painel` | Área do membro (tabs: Visão Geral, Cursos, Ebooks, Ranking) |
| Admin | `/admin` | Painel admin (Stats, Fábricas, Usuários, Combos, Trilhas, Analytics) |
| Fábrica Blog | `/admin/fabrica-blog` | iframe do painel legacy → `/#blogs` |
| Fábrica Ebook | `/admin/fabrica-ebook` | iframe do painel legacy → `/#books` |
| Fábrica Curso | `/admin/fabrica-curso` | Pipeline nativa de cursos (Next.js) |
| Trilhas | `/admin/trilhas` | Gestão de learning paths |
| Analytics | `/admin/analytics` | Métricas reais |

**Features UI:**
- Dark mode (indigo/purple gradient theme)
- JWT armazenado em `localStorage` (`dz_token`)
- Rotas protegidas: `/painel` exige login; `/admin/*` exige `role === "admin"` (redireciona para `/painel` caso contrário)
- As fábricas Blog/Ebook são um **iframe** do painel legacy (`static/index.html`) com token passado via `?token=` + hash `#blogs`/`#books`
- Auth flow em `lib/auth-context.tsx` (AuthProvider + useAuth) — usa `api.getMe()` para restaurar sessão
- API client em `lib/api.ts` injeta `Authorization: Bearer` em todas as chamadas

---

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

### Score Atual: 88.7% 🟢 (17/18) — ✅ Pronto para solicitar o AdSense

### 📝 Conteúdo (5/5 ✅)
| Item | Peso | Status |
|------|------|--------|
| 20+ artigos publicados | 8 | ✅ 89 artigos |
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

**Frontend Club** — páginas `/admin/*` verificam `user.role === "admin"` antes de renderizar.

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
# LLM Cascade
GEMINI_API_KEY=AI...
OPENROUTER_API_KEY=sk-or-...
GITHUB_TOKEN=...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...

# Banco
DATABASE_URL=postgresql://...

# Auth
SECRET_KEY=sua-chave-secreta-aqui
GOOGLE_CLIENT_ID=...

# Imagens
PEXELS_API_KEY=...
UNSPLASH_ACCESS_KEY=...
```

---

## 🐳 DEPLOY

### Backend (Railway)
**Root Directory:** `/SniperVideoEngine`  
**Builder:** Dockerfile  
**Dockerfile Path:** `/SniperVideoEngine/Dockerfile`  
**Healthcheck Path:** `/health` (timeout 120s)  
**Port:** 8080  
**Domínio:** `backend-production-f90d.up.railway.app`  
**Envs:** `DATABASE_URL`, `SECRET_KEY`, chaves LLM, Redis

### Frontend Club (Railway)
**Root Directory:** `/SniperVideoEngine/club-frontend`  
**Builder:** Dockerfile (auto-detectado)  
**Port:** 8080  
**Domínio:** `dezafira.com.br`  
**Envs:** `NEXT_PUBLIC_API_URL=https://backend-production-f90d.up.railway.app`

### Banco de Dados (Railway PostgreSQL)
**Domínio:** `reseau.proxy.rlwy.net:26643`  
**Banco:** `railway`
**Redis:** já vinculado ao Railway

---

*Documentação gerada em 01/08/2026 — Dezafira Club v3.2*
