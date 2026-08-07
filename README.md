# DEZAFIRA — Ecossistema de Fábricas de Conteúdo

> **Automação de Conteúdo Digital com IA — 100% CPU, sem GPU**
>
> **Site público (DezafiraClube):** https://www.dezafira.com.br (SvelteKit + Railway)
> **Admin (Dezafira Adm):** https://adm.dezafira.com.br (Next.js + Railway)
> **Backend API:** https://dezafiraadm-production.up.railway.app (FastAPI)
> **Banco:** PostgreSQL (backend) + LibSQL (Clube)
>
> **Status atual:** Deploy completo · foco nas fábricas de conteúdo (Blog · Ebook · Curso · Marketing)

A Dezafira é um ecossistema de **fábricas de conteúdo digital** — **Blogs, Ebooks, Cursos e Marketing** — orquestradas por agentes inteligentes com nomes brasileiros (Seu Hermes, Carlão, LiLi, Dona Célia, Seu Pereira, etc.), com motor headless (Obscura/Chrome), distribuição social e publicação WordPress.

O ecossistema é dividido em **dois serviços**:

| Serviço | O que é | Stack | Onde |
|---|---|---|---|
| **DezafiraClube** | Site público, blog SEO e área de membros | SvelteKit 2 + Svelte 5 | `Blog_Inteligente_SEO_com_IA_-_v1.8/` |
| **Dezafira Adm** | Painel administrativo de fábricas + API | FastAPI + Next.js 14 | `server.py` + `modules/` + `club-frontend/` |

> ⚠️ Pagamentos, **gamificação, combos e ranking** foram removidos do Dezafira Adm (commits recentes) — o ecossistema prioriza produção e distribuição de conteúdo. A área de membros (checkout, tokens de acesso, leitor de ebooks) é responsabilidade do **DezafiraClube**, que processa pagamentos via **Asaas** (`src/lib/server/asaas.ts` — falta só configurar as credenciais). A integração **Polar foi removida**.

---

## 🏗️ Arquitetura Atual (Railway)

```
┌────────────────────────────── Railway ──────────────────────────────┐
│                                                                     │
│  Serviço 1: libsql-server                                           │
│  └─ Banco persistente (volume 5GB)                                  │
│                                                                     │
│  Serviço 2: DezafiraClube (SvelteKit)                               │
│  └─ www.dezafira.com.br + /admin + /members                         │
│                                                                     │
│  Serviço 3: DezafiraAdm API (FastAPI)                               │
│  └─ server.py + /api/v1/* + painel legado static/index.html         │
│                                                                     │
│  Serviço 4: DezafiraAdm Frontend (Next.js)                          │
│  └─ adm.dezafira.com.br (fábricas)                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✅ Status dos Serviços

| Serviço | URL | Status |
|---------|-----|--------|
| DezafiraClube | https://www.dezafira.com.br | ✅ |
| DezafiraAdm (API) | dezafiraadm-production.up.railway.app | ✅ |
| DezafiraAdm Frontend | adm.dezafira.com.br | ✅ |
| libsql-server | railway.internal:8080 | ✅ |

---

## 🖥️ Dezafira Adm — Frontend (Next.js)

### Visão Geral

O **Dezafira Adm** é o painel de administração focado **100% nas fábricas de conteúdo** (Blog, Ebook, Curso e Marketing). Login com JWT + bcrypt, gestão de cursos/trilhas/analytics/usuários, e as fábricas Blog/Ebook/Marketing embutidas via **iframe** do painel legado (`static/index.html`).

> 💡 A **área de membros** (checkout, tokens de acesso, leitor de ebooks, cursos do assinante) vive no **DezafiraClube** (SvelteKit), não neste frontend.

### Funcionalidades

| Feature | Descrição |
|---------|-----------|
| **Auth** | Email/senha + Google OAuth + recuperação de senha |
| **Fábricas** | Blog, Ebook, Curso e Marketing (4 pipelines completas) |
| **Admin** | Cursos CRUD, trilhas de aprendizagem, analytics, usuários e stats |
| **Painel** | Dashboard do usuário logado (`/painel` — dados de `/auth/me`, cursos e ebooks) |

### Frontend (Next.js 14)

```
club-frontend/
├── app/
│   ├── page.tsx                # Landing page (Dezafira Adm — foco nas fábricas)
│   ├── auth/login/page.tsx     # Login (register → redireciona p/ login)
│   ├── painel/page.tsx         # Dashboard do usuário (overview, cursos, ebooks)
│   ├── healthz/                # Healthcheck do frontend
│   └── admin/
│       ├── page.tsx            # Painel admin (stats, users, fábricas, trilhas, analytics, marketing)
│       ├── fabrica-blog/       # Fábrica de Blogs (iframe do painel → #blogs)
│       ├── fabrica-ebook/      # Fábrica de Ebooks (iframe do painel → #books)
│       ├── fabrica-curso/      # Fábrica de Cursos (pipeline nativa)
│       ├── trilhas/            # Learning paths
│       └── analytics/          # Métricas
├── lib/
│   ├── api.ts                  # Cliente API com todas as endpoints (injeta Bearer token)
│   └── auth-context.tsx        # React AuthProvider + useAuth (restaura sessão via /me)
├── Dockerfile                  # Build Railway
└── next.config.js
```

### API Endpoints (Dezafira Adm)

**Auth**
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/register` | Registro (email + senha) — endpoint existe, página removida |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/google` | Google OAuth |
| POST | `/api/v1/auth/forgot-password` | Recuperação de senha |
| POST | `/api/v1/auth/reset-password` | Redefinir senha |
| GET | `/api/v1/auth/me` | Dados do usuário logado |
| POST | `/api/v1/auth/logout` | Encerrar sessão |

> ❌ **Removidos:** `/api/v1/member/points|badges|streak|dashboard|courses|lessons/*`, `/api/v1/combos/*`, `/api/v1/ranking`, `/api/v1/admin/combos/*` — gamificação, combos e ranking saíram do Adm.

**Admin — Cursos / Trilhas / Analytics / Usuários** *(exigem `require_admin`)*
| Método | Rota | Descrição |
|--------|------|-----------|
| GET/POST | `/api/v1/admin/courses` | Listar/Criar cursos |
| GET/PUT/DELETE | `/api/v1/admin/courses/{course_id}` | Detalhes/Editar/Deletar |
| POST | `/api/v1/admin/courses/{course_id}/publish` | Publicar curso |
| POST | `/api/v1/admin/courses/{course_id}/unpublish` | Despublicar curso |
| GET/POST | `/api/v1/admin/learning-paths` | Listar/Criar trilhas |
| GET/PUT/DELETE | `/api/v1/admin/learning-paths/{path_id}` | Gestão de trilha |
| POST | `/api/v1/admin/learning-paths/{path_id}/courses` | Adicionar curso à trilha |
| DELETE | `/api/v1/admin/learning-paths/{path_id}/courses/{course_id}` | Remover curso da trilha |
| GET | `/api/v1/admin/analytics/overview` | Analytics overview |
| GET | `/api/v1/admin/analytics/courses` | Analytics de cursos |
| GET | `/api/v1/admin/users` | Listar usuários |
| GET | `/api/v1/admin/stats` | Estatísticas gerais |

**Learning Paths (público)**
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/learning-paths` | Listar trilhas |
| GET | `/api/v1/learning-paths/{slug}` | Detalhes da trilha |

**Pipelines de Fábrica** *(exigem `require_admin`)*
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/pipeline/run-course-factory` | Iniciar fábrica de cursos |
| GET | `/api/v1/pipeline/course-factory/status/{task_id}` | Status |
| GET | `/api/v1/pipeline/course-factory/history` | Histórico |
| POST | `/api/v1/pipeline/run-ebook-factory` | Iniciar fábrica de ebooks |
| GET | `/api/v1/pipeline/ebook-factory/status/{task_id}` | Status |
| POST | `/api/v1/pipeline/run-blog-factory` | Iniciar fábrica de blogs |
| GET | `/api/v1/pipeline/blog-factory/status/{task_id}` | Status |

**Distribuição Social** *(exigem `require_admin` — módulo `modules/distributor.py`)*
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/distribution/status` | Status de configuração das plataformas (Email/Pinterest/IG/TikTok/X) |
| POST | `/api/v1/distribution/config` | Salvar token/config de uma plataforma |
| GET | `/api/v1/distribution/history` | Histórico das últimas 100 publicações |
| POST | `/api/v1/distribution/post` | Disparar publicação numa plataforma |
| POST | `/api/v1/distribution/post/{post_id}` | Distribuir UM artigo específico do blog (botão "📤 Distribuir") |
| GET | `/api/v1/distribution/schedule` | Status do agendador automático de distribuição |
| POST | `/api/v1/distribution/schedule` | Configurar agendador automático (`enabled` + `interval_hours`) |
| POST | `/api/v1/distribution/run-all` | Distribuir manualmente artigos recentes de todos os canais |

---

## 📚 Fábrica de Ebooks (Nova)

### Pipeline de 6 Fases

```
🔍 Fundação → 🧠 Pesquisa → 📋 Oferta → 📝 Produção → 🎨 Refino → 🚀 Entrega
```

| Fase | Agentes | Descrição |
|------|---------|-----------|
| **Fundação** | Hermes + Dona Célia | Cria ebook no banco, gera título, branding |
| **Pesquisa** | Minerador de Dores + Obscura | Reddit, PAA, keywords, ranking de dores |
| **Oferta** | Copywriter Infoprodutos | Mecanismo único, promessa, bônus, preço |
| **Produção** | Carlão + LiLi | Capítulo a capítulo com revisão de qualidade |
| **Refino** | Formatter | HTML formatado + página de vendas |
| **Entrega** | Seu Francisco | Produto criado, token de acesso gerado |

### Checkout e Área de Membro

- **Página de Vendas**: HTML completo gerado por IA
- **Checkout**: Transação + confirmação manual
- **Token de Acesso**: SHA-256 único por comprador
- **Leitor HTML**: Área de membro com sumário + navegação

### Fluxo de Compra

```
Página de Vendas → Checkout → Confirmação → Token Gerado → Leitor HTML
```

---

## 🎓 Fábrica de Cursos

### Pipeline de 6 Fases

```
📋 Fundação → 🧠 Pesquisa → 📝 Roteiro → 🎬 Produção → 🎨 Refino → 🚀 Entrega
```

| Fase | Agentes | Descrição |
|------|---------|-----------|
| **Fundação** | Hermes + Dona Célia | Cria curso no banco, define tema, branding |
| **Pesquisa** | Minerador de Dores + Obscura | Análise de mercado, concorrentes, público-alvo |
| **Roteiro** | Roteirista | Estrutura módulos, aulas, objetivos de aprendizagem |
| **Produção** | Carlão + LiLi | Geração de conteúdo textual aula a aula |
| **Refino** | Formatter + Tatiana | Formatação HTML, assets visuais, slides |
| **Entrega** | Seu Francisco | Curso publicado, token de acesso gerado |

### Agentes Especializados

| Agente | Nome | Responsabilidade |
|--------|------|------------------|
| Orquestrador | **Seu Hermes** | Coordena pipeline e define estratégia |
| Roteirista | **Roteirista** | Cria estrutura de módulos e aulas |
| Redator | **Carlão** | Escreve conteúdo das aulas via LLM |
| Revisora | **LiLi** | Revisa qualidade e corrige erros |
| Entregador | **Seu Francisco** | Publica curso e gera tokens de acesso |

### Trilhas de Aprendizagem (Learning Paths)

Trilhas são sequências ordenadas de cursos que guiam o aluno de um tópico básico ao avançado:

- **Composição por ordem**: Cada trilha define a ordem dos cursos
- **Progressão automática**: Aluno avança ao completar curso anterior
- **Recomendação**: Sistema sugere trilhas com base no perfil e interesses
- **Certificado final**: Aluno recebe certificado ao completar toda a trilha

### Painel Admin para Cursos

- CRUD completo de cursos (criar, editar, arquivar)
- Gestão de módulos e aulas com drag-and-drop
- Upload e vinculação de materiais complementares (PDF, links)
- Dashboard com métricas: alunos inscritos, taxa de conclusão, avaliação média
- Publicação e agendamento de lançamentos

---

## 🛒 Funil de Vendas Integrado (Adm → Clube)

O ecossistema conecta a produção de conteúdo (fábricas) à **venda** no DezafiraClube:

```
Blog (CTA) → Landing de captura (lead magnet) → Newsletter/Resend (lead)
    → Curso/Ebook no catálogo do Clube → Checkout Asaas (order bump + esteira)
    → Player de curso (token de acesso) → Nurturing automático (4 e-mails)
```

### Ponte Adm → Clube

| Método | Rota | Onde | Descrição |
|--------|------|------|-----------|
| POST | `/api/v1/clube/import-product` | Adm (`require_admin`) | Encaminha produto das fábricas para o catálogo do Clube |
| POST | `/api/import/product` | Clube (`x-import-key`) | Cria produto no catálogo (link/manual; exige `external_link`) |
| POST | `/api/import/nurture` | Clube (`x-import-key`) | Envia e-mail de nurturing via Resend para assinantes ativos |

- **Chave compartilhada**: `CLUBE_IMPORT_KEY` (Adm) == `IMPORT_API_KEY` (Clube) — comparação timing-safe.
- **`CLUBE_PUBLIC_URL`** (Adm): URL pública do Clube usada pela ponte.

### Esteira de Produtos (upsell/downsell)

Produtos no Clube têm `upsell_product_id` e `downsell_product_id`. Após o pagamento, o comprador é redirecionado para `/checkout/obrigado/{id}`:

```
Compra confirmada → UPSELL (comprar?) → recusou → DOWNSEL (oferta menor) → recusou → Dashboard
```

- Ordem bump já existia no checkout; upsell/downsell foram adicionados (colunas novas + migração automática + campos no admin de produtos).
- **Asaas**: `src/lib/server/asaas.ts` (Clube) — *falta configurar as credenciais para liberar as vendas.*

### Player de Curso (entrega protegida)

- **Rota**: `GET /curso/{course_id}?token=...` (Adm, HTML noindex) — renderiza módulos e aulas completas com markdown.
- **Token de acesso**: HMAC-SHA256 com a chave compartilhada (`CLUBE_IMPORT_KEY`/`IMPORT_API_KEY`), TTL 30 dias. Gerado pelo Clube no momento da entrega (`decorateCourseLink` em `$lib/server/courseAccess.ts`) e anexado ao `external_link` do produto.
- Sem token válido → **403** (página de acesso restrito, fail-closed).
- `outputs/` e `static/` são servidos publicamente (montados no FastAPI) para capas/thumbnails geradas.

### Nurturing Automático (Fase 5 do MarketingPipeline)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/marketing/send-nurturing` | Dispara a régua de 4 e-mails imediatamente |
| POST | `/api/v1/marketing/nurture/schedule` | Agenda a sequência (e-mail 1 → amanhã; e-mail N → +N×day_gap dias) via APScheduler |
| POST | `/api/v1/marketing/nurture/cancel` | Cancela os jobs de nurturing de uma campanha |

- `parse_stage5_emails()` extrai os 4 e-mails do texto da Fase 5 (tolerante a variações).
- Cada passo chama `POST /api/import/nurture` no Clube (Resend → assinantes ativos em BCC).
- Jobs usam `misfire_grace_time` largo para sobreviver a reinícios do Railway.

### Captura de Leads

- **Newsletter do blog** (`modules/blog_viewer.py`): form POST em `/api/v1/newsletter/subscribe` (Adm) → encaminha ao Clube + backup local `data/newsletter_leads.jsonl`.
- **CTA configurável** por canal (`brand_config.cta`): card no fim dos artigos apontando para landing/produto.
- **Landing pages** do Clube: builder visual com bloco **newsletter** nativo (captura direto na lista do Clube, Resend).

---

## 🏭 A Fábrica de Blogs (Pipeline Principal)

### 🎯 Como Funciona

A macro-esteira cria um blog completo com **N artigos** (configurável) em **5 estágios sequenciais**:

```
🏗️ Fundação → 📋 Arquitetura → 📝 Produção → 🎨 Refino → ✅ Entrega
```

Cada artigo passa por todas as etapas obrigatórias:

1. **Artigo gerado** com instruções específicas do nicho via BlogWriter multiparte (8 chamadas LLM)
2. **Imagem de destaque** gerada IMEDIATAMENTE após o artigo (Pexels → SVG fallback)
3. **Revisão LiLi** automática com auto-correção de problemas comuns
4. **Pipeline bloqueia** se a imagem falhar — artigo é descartado

### 📊 Blogs em Produção

| Blog | Nicho | Subdomínio |
|------|-------|-----------|
| ✝️ **O Reino** | Ensinamentos de Jesus | oreino |
| 🔮 **Fenômenos Inexplicáveis** | Teorias da Conspiração | fenomenosinexplicaveis |
| 🥗 **Emagrecimento Dores** | Emagrecimento | emagrecimentodores |

> Contagem de artigos/imagens/score LiLi por blog é atualizada dinamicamente no dashboard (`/api/v1/factory/dashboard`).

### 👥 Agentes da Pipeline

| Estágio | Agente | Nome | Responsabilidade |
|---------|--------|------|------------------|
| **🏗️ Fundação** | Orquestrador | **Seu Hermes** | Decide temas e estratégia |
| | Designer | **Dona Célia** | Identidade visual do blog |
| **📋 Arquitetura** | Pesquisador | **Joaquim** | Keywords e tendências |
| **📝 Produção** | Redator | **Carlão** | Escreve artigos via 8 chamadas LLM |
| | Revisora | **Dona Rosa → LiLi** | Verifica similaridade e qualidade |
| **🎨 Refino** | Fotógrafa | **Tatiana** | Busca imagens Pexels |
| | Agendador | **Seu Zé** | Programa publicação |
| | Imagens | **Ricardo** | Gera imagens para artigos |
| **✅ Entrega** | Supervisor | **Seu Francisco** | Confere produção e dá sinal verde |
| **👴 Análise** | Monetização | **Seu Pereira** | 19 critérios Google AdSense |

---

## 🔧 Refino Técnico (Agosto 2026)

| Item | O que foi feito |
|------|-----------------|
| **Cascata LLM unificada** | `agents/llm.py` agora é a ÚNICA fonte da verdade: **OpenRouter → Gemini → NVIDIA NIM → HuggingFace → DeepSeek**. `blog_writer._call_llm` virou delegador fino (mesma assinatura, mantém `RuntimeError` em falha total para os fallbacks por seção); o `query_llm` só-NVIDIA do `server.py` foi removido (usa o `agents.llm`). ~500 linhas de duplicação eliminadas |
| **Bloco duplicado removido** | 14 endpoints duplicados (blogs/seed, books, courses, images, rag) em `server.py` — o segundo registro era inalcançável (a primeira rota vence no Starlette). −281 linhas de código morto |
| **Página de registro removida** | `auth/register/page.tsx` virou stub que redireciona para `/auth/login` |

---

## 📋 Seu Pereira — Analista de Monetização

Agente especialista que avalia se cada blog está no caminho certo para o **Google AdSense**:

- **19 critérios** em **6 categorias** (Conteúdo, Páginas, Design, Técnico, SEO, Autoridade)
- Pontuação automática com recomendações priorizadas (peso ALTA/MÉDIA/BAIXA)
- Painel no Dashboard mostrando progresso e próximos passos
- Sistema de dependências entre critérios

**Estado atual:** 88.7% (17/19 critérios) — atualizado dinamicamente no dashboard

---

## 🛠️ Tecnologias

| Camada | Tecnologias |
|--------|-------------|
| **Backend** | FastAPI (Python 3.11+), Uvicorn |
| **ORM** | SQLAlchemy + PostgreSQL (prod) / SQLite (dev) |
| **LLM Cascade** | OpenRouter → Gemini → NVIDIA NIM → HuggingFace → DeepSeek (unificada em `agents/llm.py`) |
| **Imagens** | Pexels API (primário) + SVG placeholder (fallback absoluto) |
| **Frontend Adm** | Next.js 14 (App Router) + Tailwind CSS + React |
| **Frontend Clube** | SvelteKit 2 + Svelte 5 (Runes) |
| **Auth** | JWT (HMAC-SHA256) + bcrypt + Google OAuth |
| **Frontend Blog** | HTML + CSS + JavaScript SPA (vanilla) |
| **Infraestrutura** | Railway (backend + frontends), CPU-only |

---

## 🚀 Como Rodar Localmente

### 1. Requisitos
- Python v3.11+

### 2. Setup Rápido
```bash
pip install -r requirements.txt
python server.py
```

### 3. Acessar UI
Abra **http://localhost:8000** no navegador

---

## 🔑 Variáveis de Ambiente (.env)

```bash
# ─── LLM Cascade (ordem real: OpenRouter → Gemini → NVIDIA → HuggingFace → DeepSeek) ───
OPENROUTER_API_KEY=sk-or-...          # Tenta primeiro (5 modelos gratuitos)
GEMINI_API_KEY=AI...                  # Fallback 2
NVIDIA_API_KEY=nvapi-...              # Fallback 3
HUGGINGFACE_TOKEN=hf_...              # Fallback 4
DEEPSEEK_API_KEY=sk-...               # Fallback 5

# ─── Imagens (recomendado) ───
PEXELS_API_KEY=...                    # Pexels (stock photos, gratuita)

# ─── Banco ───
DATABASE_URL=postgresql://...         # PostgreSQL (produção)

# ─── Auth (Dezafira Adm) — ⚠️ OBRIGATÓRIO ───
AUTH_SECRET=sua-chave-secreta-aqui    # JWT signing (>= 16 chars) — o servidor NÃO sobe sem isso (08/2026)
GOOGLE_CLIENT_ID=...                  # Google OAuth (opcional)

# ─── Ponte Adm → Clube (funil de vendas) ───
CLUBE_PUBLIC_URL=https://www.dezafira.com.br   # URL pública do Clube
CLUBE_IMPORT_KEY=chave-forte           # ⚠️ Mesma chave do IMPORT_API_KEY do Clube

# ─── No serviço DezafiraClube (SvelteKit) ───
IMPORT_API_KEY=chave-forte             # ⚠️ Mesma chave do CLUBE_IMPORT_KEY do Adm (ponte + player + nurturing)
BACKEND_URL=https://dezafiraadm-production.up.railway.app
```

---

## 📁 Estrutura do Projeto

```
dezafira/
├── server.py                  # API principal FastAPI (181 endpoints)
├── modules/
│   ├── database.py            # SQLAlchemy ORM (30+ tables)
│   ├── blog_writer.py         # Geração de artigos via LLM (delegador de agents/llm.py)
│   ├── blog_pipeline.py       # Macro-esteira com 5 estágios
│   ├── ebook_pipeline.py      # Pipeline de ebooks 6 fases
│   ├── course_pipeline.py     # Pipeline de cursos 6 fases
│   ├── marketing_pipeline.py  # Fábrica de Marketing 6 fases (Sabri Suby)
│   ├── blog_viewer.py         # Blog viewer público dinâmico
│   ├── blog_publisher.py      # Publicação de artigos
│   ├── blog_revisor.py        # Revisão gramatical
│   ├── brand_designer.py      # Identidade visual via LLM
│   ├── brand_themes.py        # Temas visuais por nicho
│   ├── image_factory.py       # Geração de imagens (Pexels + SVG)
│   ├── lili.py                # Revisora de qualidade auto-corretiva
│   ├── ricardo.py             # Gera imagem de destaque por artigo
│   ├── seu_pereira.py         # Analista de monetização
│   ├── seu_ze.py              # Agendador de produção
│   ├── seu_francisco.py       # Supervisor de produção
│   ├── keyword_miner.py       # Mineração de keywords
│   ├── seo_optimizer.py       # Otimização SEO
│   ├── affiliate_agents.py    # Afiliados Amazon/Shopee/Mercado Livre
│   ├── telegram_bot.py        # Bot do Telegram
│   ├── scheduler.py           # Agendador de tarefas
│   ├── deliverables.py        # Entregáveis/checkout
│   ├── distributor.py         # Distribuição social (Email/Pinterest/IG/TikTok/X)
│   ├── google_indexer.py      # Google Indexing API (OAuth 2.0)
│   ├── google_oauth_setup.py  # Setup OAuth da indexação
│   ├── mcp_client.py          # Telemetria MCP + WordPress REST
│   ├── document_parser.py     # Parsing de documentos
│   └── uploader.py            # Upload de assets
├── agents/
│   ├── llm.py                 # ⭐ ÚNICA cascata LLM (OpenRouter→Gemini→NVIDIA→HF→DeepSeek)
│   ├── book_factory.py        # Fábrica de livros (agentes)
│   ├── course_factory.py      # Fábrica de cursos
│   ├── course_professor.py    # Estrutura curricular (cursos)
│   ├── course_pedagogue.py    # Conteúdo didático
│   ├── course_reviewer.py     # Revisão de qualidade (cursos)
│   ├── course_quizmaster.py   # Quiz generation
│   ├── course_cover.py        # Capas/thumbnails de cursos
│   ├── image_factory.py       # Motor de imagens (Pexels → SVG)
│   └── rag_biblico.py         # RAG bíblico
├── services/
│   ├── obscura_bridge.py      # Bridge CDP (Chrome real + Obscura)
│   ├── obscura_client.py      # Cliente do motor headless
│   ├── obscura_health.py      # Healthcheck com grace configurável
│   ├── obscura_service.py     # Serviço/telemetria Obscura
│   ├── hyperframes_bridge.py  # Bridge HyperFrames
│   ├── open_montage_bridge.py # Bridge OpenMontage
│   ├── pwa_generator.py       # Geração de PWA
│   ├── spy_service.py         # Spy/descoberta de oportunidades
│   ├── voice_service.py       # Voz/TTS
│   └── memory_service.py      # Memória compartilhada
├── docker/
│   ├── cdp_proxy.py           # Proxy TCP unificado (substitui socat)
│   ├── chrome/                # Serviço Chrome real (CDP 9223)
│   └── obscura/               # Serviço Obscura (CDP 9222)
├── static/
│   └── index.html             # UI Dashboard SPA (blog/ebook admin) — exige token
├── pipeline/                   # Engine + orquestrador de pipelines
├── research/                   # Analisadores e spiders de pesquisa
├── docs/                       # Guias (Obscura, indexação Google)
├── tests/                      # Testes pytest
├── scripts/                    # Scripts utilitários
├── Blog_Inteligente_SEO_com_IA_-_v1.8/  # 🟢 DezafiraClube (SvelteKit) — site público + membros
├── club-frontend/             # 🟢 Dezafira Adm frontend (Next.js 14)
├── requirements.txt
├── Dockerfile
└── railway.toml
```

---

## 🗺️ Roadmap

### ✅ Implementado
- [x] Macro-esteira de Blogs com 5 estágios e 9 agentes
- [x] Conveyor belt UI animado na interface
- [x] Blog viewer público com páginas de sistema (privacidade, sobre, contato)
- [x] Temas visuais por nicho (brand_themes.py)
- [x] Instruções de redação específicas por nicho (finanças, cristão, tecnologia, saúde, casa)
- [x] LiLi — revisora automática com auto-correção de conteúdo e HTML
- [x] Imagem obrigatória em cada artigo (Pexels → SVG fallback)
- [x] Pipeline respeita artigos existentes (não gera duplicatas)
- [x] Tópicos dinâmicos gerados por LLM por nicho
- [x] Seu Pereira — Analista de Monetização (19 critérios)
- [x] **LLM Cascade unificada** — uma única cascata (OpenRouter→Gemini→NVIDIA→HF→DeepSeek) em `agents/llm.py`
- [x] Páginas obrigatórias (Privacidade, Sobre, Contato, robots.txt, sitemap.xml, ads.txt)
- [x] Dashboard SPA com métricas em tempo real
- [x] Deploy Railway com domínio próprio (dezafira.com.br)
- [x] Banco PostgreSQL em produção
- [x] **Fábrica de Ebooks** — Pipeline de 6 fases + Checkout + Área de Membro
- [x] **Dezafira Adm** — Frontend Next.js focado nas fábricas (gamificação/combos/ranking removidos)
- [x] **Fábrica de Cursos** — Pipeline de 6 fases + 5 agentes especializados + quizzes + capa
- [x] **Trilhas de Aprendizado** — learning paths com ordenação de cursos
- [x] **Admin Analytics** — métricas reais (usuários, cursos)
- [x] **Integração Fábrica de Blogs/Ebooks/Marketing no Adm** — páginas Next.js com iframe do painel
- [x] **Autenticação Admin** — endpoints das fábricas protegidos com `require_admin`
- [x] **Painel admin protegido** — `GET /` exige token admin (header ou query)
- [x] **🕵️ Obscura Engine** — motor headless dedicado no Railway (CDP 9222) com telemetria, alertas Telegram, grace configurável, healthcheck nativo
- [x] **🌐 Chrome real** — serviço dedicado no Railway (CDP 9223) via proxy TCP unificado (`cdp_proxy.py`) + conexão por IP (anti DNS-rebinding); `picked_engine` prioriza Chrome
- [x] **🔀 Rotação de buscadores** — Google bloqueado → fallback round-robin (Bing/DDG/Ecosia) com telemetria persistida no banco
- [x] **📢 Fábrica de Marketing** — esteira de 6 fases (Sabri Suby) com 6 agentes (Seu Tião, Dona Benta, Tonho, Zé do Traço, Chica, Seu Valdir) + SMTP nativo + histórico persistente
- [x] **🌐 WordPress** — publicação nativa via REST API (sem plugins)
- [x] **🖥️ MCP Servers** — telemetria de integridade (memory, filesystem, brave_search, wordpress) em `GET /api/v1/mcp/status`
- [x] **🛒 Funil de Vendas integrado** — ponte Adm→Clube (`/api/v1/clube/import-product` + `/api/import/product`), captura de leads (newsletter real + backup local), CTA configurável por blog, esteira upsell/downsell no checkout do Clube
- [x] **📬 Landing + Lead Magnet** — bloco newsletter nativo no builder de landing do Clube; landing pública `/p/guia-emagrecimento-gratis` capturando via `/api/newsletter` (Resend)
- [x] **🔒 Player de curso protegido** — `GET /curso/{id}?token=` com HMAC compartilhado (30 dias), entrega por link decorado no Clube, capa gerada via Pollinations/Gemini/Pexels
- [x] **⏰ Nurturing automático** — agendamento da régua de 4 e-mails via APScheduler (`/api/v1/marketing/nurture/schedule`) + disparo imediato (`send-nurturing`)

### 🔜 Próximos Passos
- [ ] Google Search Console — Verificação e monitoramento
- [ ] Indexação Google — Solicitar indexação dos artigos
- [ ] Google AdSense — Solicitar aprovação
- [ ] **Asaas** — configurar credenciais no Clube para liberar o checkout (pendência única para vendas reais)
- [ ] Proteção por token por compra (não por usuário) no player de curso
- [ ] Google Search Console — Verificação e monitoramento
- [ ] Redis — cache e rate limiting ativos em produção
- [ ] Real images nos blogs e club (substituir SVG placeholders)
- [ ] Proxy residencial (`OBSCURA_PROXY_URL`) — zerar bloqueios do Google e destravar PAA em escala
- [x] **Auth endurecida** — `AUTH_SECRET` obrigatório (≥16 chars, fallback hardcoded removido), assinatura JWT em tempo constante (`hmac.compare_digest`) e 12 endpoints de pipeline/factory/lili protegidos com `require_admin`

---

*Dezafira — Ecossistema de Fábricas de Conteúdo v3.4*
