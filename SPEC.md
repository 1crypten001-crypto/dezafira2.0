# DEZAFIRA — Fábrica de Blogs & Sistemas de Monetização

> **Versão:** 2.0.0  
> **Produção:** https://dezafira.com.br  
> **API:** https://backend-production-f90d.up.railway.app  
> **Database:** PostgreSQL (Railway)  
> **Última atualização:** 31/07/2026

---

## 📋 VISÃO GERAL

A Dezafira é uma plataforma SaaS de **criação e gestão automatizada de blogs** com IA.  
O sistema gera blogs completos do zero — com dezenas de artigos profundos, imagens de destaque, SEO técnico, branding profissional e preparação para monetização via Google AdSense.

### Estado Atual

| Métrica | Valor |
|---|---|
| **Canais de Blog** | 2 (O Reino + Vida Financeira) |
| **Total de Artigos** | 89 |
| **Palavras Geradas** | ~199.000+ |
| **Artigos com Imagem** | 100% |
| **Artigos Publicados** | Em andamento |
| **Score Monetização** | 88.7% (17/18) — ✅ Pronto AdSense |

### Blogs Ativos

| Blog | Nicho | Artigos | Imagens | Subdomínio |
|---|---|---|---|---|
| ✝ **O Reino** | Ensinamentos de Jesus | 41 | 100% | oreino |
| 💰 **Vida Financeira** | Finanças pessoais | 48 | 100% | vida-financeira |

---

## 🏗️ ARQUITETURA DO SISTEMA

```
┌─────────────────────────────────────────────┐
│                 FastAPI Server               │
│  ┌─────────────┐ ┌──────────┐ ┌───────────┐ │
│  │ REST API    │ │ WebSocket│ │ Static UI │ │
│  │ (80+ rotas) │ │ (hub)    │ │ index.html│ │
│  └──────┬──────┘ └──────────┘ └───────────┘ │
└─────────┼───────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────┐
│           PostgreSQL (Railway)               │
│  ┌──────────────┐ ┌───────────────┐         │
│  │ Blog Channels│ │ Blog Posts    │         │
│  │ Blog Sections│ │ Pipeline Runs │         │
│  │ Books        │ │ Courses       │         │
│  │ Knowledge    │ │ Subdomains    │         │
│  └──────────────┘ └───────────────┘         │
└─────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────┐
│         Macro Pipeline (Esteira)             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐  │
│  │Fundação│ │Arquitet│ │Produção│ │Refino│  │
│  │🏗️     │ │📋      │ │📝     │ │🎨   │  │
│  └────────┘ └────────┘ └────────┘ └──────┘  │
│             ┌────────┐                       │
│             │Entrega │                       │
│             │✅     │                       │
│             └────────┘                       │
└─────────────────────────────────────────────┘
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

### 🏥 Health
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check do servidor |

### 📊 Factory / Pipeline
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/factory/dashboard` | Dashboard completo (canais, artigos, métricas) |
| GET | `/api/v1/factory/monitor-stats` | Estatísticas do monitor |
| GET | `/api/v1/factory/francisco` | Relatório do Seu Francisco |
| GET | `/api/v1/factory/ze-status` | Status do Seu Zé |
| GET | `/api/v1/factory/openmontage-status` | Status OpenMontage |
| POST | `/api/v1/factory/build-app` | Construir aplicativo |
| POST | `/api/v1/pipeline/run-blog-factory` | Iniciar macro-esteira de blog |
| POST | `/api/v1/pipeline/run-blog` | Iniciar pipeline de blog |
| POST | `/api/v1/pipeline/run-sync` | Pipeline síncrono |
| GET | `/api/v1/pipeline/blog-factory/status/{task_id}` | Status da macro-esteira |
| GET | `/api/v1/pipeline/macro-result/{task_id}` | Resultado da macro-esteira |
| GET | `/api/v1/pipeline/blog/history` | Histórico de pipelines |
| GET | `/api/v1/pipeline/{task_id}` | Status de pipeline específico |

### 📝 Blog API
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/blog/{slug}/info` | Informações do blog |
| GET | `/api/v1/blog/{slug}/posts` | Lista de artigos do blog |
| GET | `/api/v1/blog/{slug}/posts/{post_id}` | Artigo específico |
| POST | `/api/v1/blog/{slug}/posts/{post_id}/update` | Atualizar artigo |
| POST | `/api/v1/blog/{slug}/posts/{post_id}/generate-image` | Gerar imagem para artigo |
| POST | `/api/v1/blog/generate-article` | Gerar artigo via LLM |
| POST | `/api/v1/blog/generate-batch` | Gerar lote de artigos |
| POST | `/api/v1/blog/generate-missing-images` | Gerar imagens pendentes |
| DELETE | `/api/v1/blog/post/{post_id}` | Deletar artigo |
| POST | `/api/v1/blog/import-posts` | Importar artigos |
| POST | `/api/v1/blog/{slug}/generate-banner` | Gerar banner do blog |
| GET | `/api/v1/blog/{slug}/subdomain` | Obter subdomínio |
| POST | `/api/v1/blog/{slug}/subdomain` | Configurar subdomínio |
| POST | `/api/v1/blogs/seed` | Popular blogs de teste |

### 🌸 LiLi — Revisão
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/lili/review/{post_id}` | Revisar artigo específico |
| GET | `/api/v1/lili/review-all` | Revisar todos os artigos |
| POST | `/api/v1/lili/correct/{post_id}` | Corrigir artigo automaticamente |

### 💰 Monetização
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/monetization/status` | Status do Seu Pereira (AdSense) |
| POST | `/api/v1/blog/{slug}/update-affiliate` | Atualiza configurações do Modo Afiliado |
| POST | `/api/v1/blog/{slug}/update-modes` | Alterna modos do blog (is_affiliate/is_discover) |
| GET | `/api/v1/affiliate/clicks` | Métricas consolidadas de cliques de afiliados |
| GET | `/go/{post_slug}/{provider}` | Cloaking de links e redirecionamento de afiliados |

### 🎨 Imagens
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/images/generate-blog-image` | Gerar imagem para blog |
| POST | `/api/v1/images/generate-cover` | Gerar capa |
| POST | `/api/v1/images/generate-thumbnail` | Gerar thumbnail |

### 🔍 Pesquisa
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/research/niche` | Pesquisar nicho |
| POST | `/api/v1/research/channel` | Analisar canal YouTube |
| GET | `/api/v1/research/trending` | Tendências do YouTube |
| GET | `/api/v1/research/youtube-rules` | Regras do YouTube |

### 📚 Livros
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/books` | Listar livros |
| POST | `/api/v1/books/generate` | Gerar livro |
| POST | `/api/v1/books/seed` | Popular livros de teste |
| GET | `/api/v1/books/{book_id}` | Detalhes do livro |

### 🎓 Cursos
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/courses` | Listar cursos |
| POST | `/api/v1/courses/generate` | Gerar curso |
| POST | `/api/v1/courses/seed` | Popular cursos de teste |
| GET | `/api/v1/courses/{course_id}` | Detalhes do curso |

### 🧠 Hermes Chat
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/hermes/chat` | Conversar com Hermes |
| POST | `/api/v1/hermes/analyze-video` | Analisar vídeo concorrente |
| POST | `/api/v1/hermes/clear` | Limpar histórico |
| GET | `/api/v1/hermes/history` | Histórico do chat |

### 📦 Entregáveis
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/deliverables` | Listar apps |
| POST | `/api/v1/deliverables/create` | Criar app |
| POST | `/api/v1/deliverables/checkout` | Checkout |
| GET | `/api/v1/deliverables/{slug}` | Detalhes do app |
| POST | `/api/v1/deliverables/webhooks/mercadopago` | Webhook Mercado Pago |
| POST | `/api/v1/deliverables/webhooks/stripe` | Webhook Stripe |

### 📊 Analytics
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/analytics/channels` | Analytics de canais |
| GET | `/api/v1/analytics/metrics` | Métricas de analytics |

### 🕵️ Spy / Trends
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/spy/discover` | Descobrir oportunidades |
| POST | `/api/v1/rag/ask` | Perguntar ao RAG |
| POST | `/api/v1/rag/index` | Indexar conteúdo no RAG |

### 🌐 Blog Frontend (HTML)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/blog/{slug}` | Página inicial do blog |
| GET | `/blog/{slug}/sobre` | Página Sobre |
| GET | `/blog/{slug}/contato` | Página Contato |
| GET | `/blog/{slug}/privacidade` | Política de Privacidade |
| GET | `/blog/{slug}/termos` | Termos de Uso |
| GET | `/sitemap.xml` | Sitemap XML (todos os artigos) |
| GET | `/robots.txt` | Robots.txt |
| GET | `/ads.txt` | Ads.txt |

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
| is_discover | BOOLEAN | Ativação do Modo Viral (Google Discover) |
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

### 🔴 Imediatos (Monetização)
1. **Conectar Google Search Console** (peso 7) — Verificar domínio em search.google.com
2. **Solicitar indexação** dos artigos no Google (peso 8)
3. **Implementar Google Analytics** para métricas de tráfego
4. **Criar mais conteúdo** para atingir 50+ artigos no O Reino
5. **Publicar artigos em massa** via Seu Zé

### 🟡 Curto Prazo (Qualidade)
1. **Criar 3º blog** (saúde/bem-estar ou tecnologia) com branding único
2. **Compressão de imagens** para melhorar PageSpeed
3. **Otimizar Core Web Vitals** (LCP, FID, CLS)
4. **Adicionar schema.org Article** + FAQ + Breadcrumb em JSON-LD
5. **Gerar backlinks** para autoridade de domínio

### 🟢 Médio Prazo (Monetização Avançada)
1. **Aplicar para Google AdSense** quando score > 80%
2. **Implementar afiliados** (Amazon, Hotmart, Eduzz)
3. **Criar produtos digitais** (Ebooks, Cursos) via sistema existente
4. **Newsletter por e-mail** (capturar leads)
5. **Anúncios nativos** (Taboola, Outbrain)

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
| Score AdSense | 88.7% | 95% | 98% |
| Visitantes/mês | 0 | 1.000 | 50.000 |
| Receita/mês | R$ 0 | R$ 200 | R$ 5.000 |

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

## 🔐 VARIÁVEIS DE AMBIENTE

```
DATABASE_URL=postgresql://...
NVIDIA_API_KEY=nvapi-...
PEXELS_API_KEY=...
UNSPLASH_ACCESS_KEY=...
TELEGRAM_BOT_TOKEN=...
```

---

## 🐳 DEPLOY (Railway)

**Root Directory:** `/SniperVideoEngine`  
**Builder:** Dockerfile  
**Dockerfile Path:** `/SniperVideoEngine/Dockerfile`  
**Healthcheck Path:** `/health`  
**Port:** 8080  
**Domínio:** dezafira.com.br (aponta para backend)

---

*Documentação gerada em 31/07/2026 — Dezafira Fábrica de Blogs™*
