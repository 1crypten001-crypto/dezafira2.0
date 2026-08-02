# DEZAFIRA — Ecossistema de Fábricas de Conteúdo & Dezafira Club

> **Automação de Conteúdo Digital com IA — 100% CPU, sem GPU**
> 
> **Produção:** https://dezafira.com.br
> **Club:** https://dezafira.com.br (Next.js + Railway)
> 
> **Status atual:** 89 artigos publicados em 2 blogs, 100% com imagem, score LiLi médio 99.1/100

Dezafira é um ecossistema integrado de fábricas de conteúdo digital — **Blogs, Ebooks, Cursos** — tudo orquestrado por agentes inteligentes com nomes brasileiros, monitorado pelo **Seu Pereira**, e uma área de membros completa com gamificação: **Dezafira Club**.

---

## 🏗️ Arquitetura do Sistema

```
┌──────────────────────────────────────────────────────────────────────┐
│                 FRONTEND — Dezafira Club (Next.js 14)                │
│  Landing │ Auth │ Dashboard │ Admin Panel │ Combos │ Ranking         │
│  dezafira.com.br (Railway)                                            │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ chamadas diretas (fetch → FastAPI + Bearer)
┌──────────────────────────▼───────────────────────────────────────────┐
│                 BACKEND (FastAPI) — 167 endpoints                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │              🔐 Auth & Member System                             ││
│  │  Register │ Login │ Google OAuth │ Password Recovery │ JWT      ││
│  │  Points │ Badges │ Streak │ Ranking │ Course Tracks │ Combos    ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │              🏭 Factories (Pipelines)                            ││
│  │  📝 Blog Factory (5 phases)  │  📗 Ebook Factory (6 phases)    ││
│  │  🎓 Course Factory (6 phases) │  📸 Image Factory (Pexels+SVG)   ││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │              LLM Cascade (5 provedores)                          ││
│  │  Gemini → OpenRouter → GitHub → Groq → Anthropic                 ││
│  │  Database PostgreSQL + SQLAlchemy ORM + Redis                    ││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

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

## 🏠 Dezafira Club — Área de Membro

### Visão Geral
Área de membros completa com autenticação, gamificação, cursos e combos. Frontend Next.js 14 (Railway), backend integrado no FastAPI existente.

### Funcionalidades

| Feature | Descrição |
|---------|-----------|
| **Auth** | Email/senha + Google OAuth + Recuperação de senha |
| **Gamificação** | Pontos por ações, badges, streak diário, ranking global |
| **Cursos** | Estrutura Course > Track > Module > Lesson com progresso |
| **Combos** | Bundle ebook + curso com 30% desconto |
| **Admin** | Stats, gestão de usuários, CRUD de combos |

### Frontend (Next.js 14)

```
club-frontend/
├── app/
│   ├── page.tsx                # Landing page (hero, combos, ranking)
│   ├── auth/login/page.tsx    # Login
│   ├── auth/register/page.tsx # Registro
│   ├── painel/page.tsx        # Dashboard do membro (overview, cursos, ebooks, ranking)
│   └── admin/
│       ├── page.tsx           # Painel admin (stats, users, combos)
│       ├── fabrica-blog/      # Fábrica de Blogs (iframe do painel → #blogs)
│       ├── fabrica-ebook/     # Fábrica de Ebooks (iframe do painel → #books)
│       ├── fabrica-curso/     # Fábrica de Cursos (pipeline nativa)
│       ├── trilhas/           # Learning paths
│       └── analytics/         # Métricas
├── lib/
│   ├── api.ts                # Cliente API com todas as endpoints (injeta Bearer token)
│   └── auth-context.tsx      # React AuthProvider + useAuth (restaura sessão via /me)
├── public/images/            # Imagens placeholder
├── Dockerfile                # Build Railway
└── next.config.js
```

### API Endpoints (Novas)

**Auth**
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/register` | Registro (email + senha) |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/google` | Google OAuth |
| POST | `/api/v1/auth/forgot-password` | Recuperação de senha |
| POST | `/api/v1/auth/reset-password` | Redefinir senha |
| GET | `/api/v1/auth/me` | Dados do usuário logado |
| POST | `/api/v1/auth/logout` | Encerrar sessão |

**Member**
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/member/dashboard` | Dashboard do membro |
| GET | `/api/v1/member/points` | Pontos |
| GET | `/api/v1/member/badges` | Badges |
| GET | `/api/v1/member/streak` | Streak |
| GET | `/api/v1/member/courses` | Cursos matriculados |
| POST | `/api/v1/member/courses/{id}/enroll` | Matricular-se |
| POST | `/api/v1/member/lessons/{id}/complete` | Completar aula |

**Combos**
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/combos` | Listar combos |
| GET | `/api/v1/combos/{slug}` | Detalhes do combo |
| POST | `/api/v1/combos/{id}/purchase` | Iniciar compra |
| POST | `/api/v1/combos/{id}/confirm` | Confirmar pagamento |

**Social**
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/ranking` | Ranking global |

**Admin — Cursos / Trilhas / Analytics** *(exigem `require_admin`)*
| Método | Rota | Descrição |
|--------|------|-----------|
| GET/POST | `/api/v1/admin/courses` | Listar/Criar cursos |
| GET/PUT/DELETE | `/api/v1/admin/courses/{id}` | Detalhes/Editar/Deletar |
| POST | `/api/v1/admin/courses/{id}/publish` | Publicar curso |
| POST | `/api/v1/admin/courses/{id}/unpublish` | Despublicar curso |
| GET/POST | `/api/v1/admin/learning-paths` | Listar/Criar trilhas |
| GET/PUT/DELETE | `/api/v1/admin/learning-paths/{id}` | Gestão de trilha |
| POST | `/api/v1/admin/learning-paths/{id}/courses` | Adicionar curso à trilha |
| DELETE | `/api/v1/admin/learning-paths/{id}/courses/{cid}` | Remover curso da trilha |
| GET | `/api/v1/admin/analytics/overview` | Analytics overview |
| GET | `/api/v1/admin/analytics/courses` | Analytics de cursos |
| GET | `/api/v1/admin/users` | Listar usuários |
| GET | `/api/v1/admin/stats` | Estatísticas gerais |
| POST | `/api/v1/admin/combos` | Criar combo |
| DELETE | `/api/v1/admin/combos/{id}` | Deletar combo |

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
- Dashboard com métricas: alunos inscritos, taxa de conclusão, avalição média
- Publicação e agendamento de lançamentos

### API Endpoints (Cursos)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/v1/courses` | Listar cursos (público) |
| GET | `/api/v1/courses/{id}` | Detalhes do curso (público) |
| GET | `/api/v1/learning-paths` | Listar trilhas (público) |
| GET | `/api/v1/learning-paths/{slug}` | Detalhes da trilha (público) |
| POST | `/api/v1/member/courses/{id}/enroll` | Inscrever-se (membro) |

**CRUD (admin)** — sob `/api/v1/admin/courses/*`
- `GET/POST` `/api/v1/admin/courses`, `GET/PUT/DELETE` `/api/v1/admin/courses/{id}`

> O CRUD administrativo completo vive em `/api/v1/admin/courses/*` (listado na seção *API Endpoints - Admin*).

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

| Blog | Nicho | Artigos | Imagens | Publicados | Score LiLi |
|------|-------|---------|---------|------------|------------|
| ✝️ **O Reino** | Ensinamentos de Jesus | 37 | 37 (100%) | 37 | 98.9/100 |
| 💰 **Vida Financeira** | Finanças, Investimentos | 40 | 40 (100%) | 30 | 99.2/100 |
| **Total** | | **77** | **77 (100%)** | **67** | **99.1/100** |

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

### 🔧 Últimas Correções (Julho 2026)

| Correção | O que resolveu |
|----------|---------------|
| **Import base64** no image_factory.py | Placeholder SVG quebrava silenciosamente → artigos sem imagem |
| **Imagem obrigatória** no generate-article | Se imagem falha, artigo é deletado + erro retornado |
| **Pipeline bloqueante** em _phase_producao | Se imagem falha, article_result["success"] = False + continue |
| **LiLi auto-corrige html_garbage** | Remove & $ # @ \\ dentro de tags HTML automaticamente |
| **Pipeline respeita artigos existentes** | Conta artigos no DB antes de gerar, ajusta target_articles |
| **Instruções de redação por nicho** | 5 nichos (finanças, cristão, saúde, tecnologia, casa) com prompts específicos |
| **Tópicos dinâmicos** | Gera tópicos variados via LLM por nicho (não mais fixo "Jesus") |

---

## 📋 Seu Pereira — Analista de Monetização

Agente especialista que avalia se cada blog está no caminho certo para o **Google AdSense**:

- **19 critérios** em **6 categorias** (Conteúdo, Páginas, Design, Técnico, SEO, Autoridade)
- Pontuação automática com recomendações priorizadas (peso ALTA/MÉDIA/BAIXA)
- Painel no Dashboard mostrando progresso e próximos passos
- Sistema de dependências entre critérios

**Estado atual:** 68.4% (13/19 critérios atendidos)

---

## 🛠️ Tecnologias

| Camada | Tecnologias |
|--------|-------------|
| **Backend** | FastAPI (Python 3.11+), Uvicorn |
| **ORM** | SQLAlchemy + PostgreSQL (prod) / SQLite (dev) |
| **LLM Cascade** | Gemini → OpenRouter → GitHub → Groq → Anthropic |
| **Imagens** | Pexels API (primário) + SVG placeholder (fallback absoluto) |
| **Frontend Club** | Next.js 14 (App Router) + Tailwind CSS + React |
| **Auth** | JWT (HMAC-SHA256) + bcrypt + Google OAuth |
| **Frontend Blog** | HTML + CSS + JavaScript SPA (vanilla) |
| **Cache** | Redis (sessões, filas, cache de respostas) |
| **Infraestrutura** | Railway (backend + frontend), CPU-only |

---

## 🚀 Como Rodar Localmente

### 1. Requisitos
- Python v3.11+

### 2. Setup Rápido
```bash
cd SniperVideoEngine
pip install -r requirements.txt
python server.py
```

### 3. Acessar UI
Abra **http://localhost:8000** no navegador

---

## 🔑 Variáveis de Ambiente (.env)

```bash
# ─── LLM Cascade (pelo menos 1 obrigatório) ───
GEMINI_API_KEY=AI...                  # Tenta primeiro (gratuito)
OPENROUTER_API_KEY=sk-or-...          # Fallback 2 (gratuito)
GITHUB_TOKEN=...                      # Fallback 3
GROQ_API_KEY=gsk_...                  # Fallback 4
ANTHROPIC_API_KEY=sk-ant-...          # Fallback 5

# ─── Imagens (recomendado) ───
PEXELS_API_KEY=...                    # Pexels (stock photos, gratuita)

# ─── Banco ───
DATABASE_URL=postgresql://...         # PostgreSQL (produção)

# ─── Auth (Dezafira Club) ───
SECRET_KEY=sua-chave-secreta-aqui     # JWT signing
GOOGLE_CLIENT_ID=...                  # Google OAuth (opcional)
```

---

## 📁 Estrutura do Projeto

```
dezafira/
├── SniperVideoEngine/
│   ├── server.py                  # API principal (167 endpoints)
│   ├── modules/
│   │   ├── database.py            # SQLAlchemy ORM (30+ tables)
│   │   ├── blog_writer.py         # Geração de artigos via LLM
│   │   ├── blog_pipeline.py       # Macro-esteira com 5 estágios
│   │   ├── ebook_pipeline.py      # Pipeline de ebooks 6 fases
│   │   ├── course_pipeline.py     # Pipeline de cursos 6 fases
│   │   ├── blog_viewer.py         # Blog viewer público dinâmico
│   │   ├── blog_publisher.py      # Publicação de artigos
│   │   ├── blog_revisor.py        # Revisão gramatical
│   │   ├── brand_designer.py      # Identidade visual via LLM
│   │   ├── brand_themes.py        # Temas visuais por nicho
│   │   ├── image_factory.py       # Geração de imagens (Pexels + SVG)
│   │   ├── lili.py                # Revisora de qualidade auto-corretiva
│   │   ├── seu_pereira.py         # Analista de monetização
│   │   ├── seu_ze.py              # Agendador de produção
│   │   ├── seu_francisco.py       # Supervisor de produção
│   │   ├── seu_ricardo.py         # (ver agents/) — só consolida uploads
│   │   ├── keyword_miner.py       # Mineração de keywords
│   │   ├── seo_optimizer.py       # Otimização SEO
│   │   ├── telegram_bot.py        # Bot do Telegram
│   │   ├── scheduler.py           # Agendador de tarefas
│   │   ├── deliverables.py        # Entregáveis/checkout
│   │   ├── image_factory.py       # Geração de capas/thumbnails
│   │   └── uploader.py            # Upload de assets
│   ├── agents/
│   │   ├── course_professor.py    # Estrutura curricular (cursos)
│   │   ├── course_pedagogue.py    # Conteúdo didático
│   │   ├── course_reviewer.py     # Revisão de qualidade (cursos)
│   │   ├── course_quizmaster.py   # Quiz generation
│   │   └── course_cover.py        # Capas/thumbnails de cursos
│   ├── static/
│   │   └── index.html             # UI Dashboard SPA (blog/ebook admin) — exige token
│   ├── club-frontend/             # Next.js 14 frontend
│   │   ├── app/
│   │   │   ├── page.tsx           # Landing page
│   │   │   ├── auth/              # Login/Register
│   │   │   ├── painel/            # Member dashboard
│   │   │   └── admin/             # Admin panel
│   │   │       ├── fabrica-blog/  # Fábrica de Blogs (iframe do painel)
│   │   │       ├── fabrica-ebook/ # Fábrica de Ebooks (iframe do painel)
│   │   │       ├── fabrica-curso/ # Fábrica de Cursos (nativo)
│   │   │       ├── trilhas/       # Learning paths
│   │   │       └── analytics/     # Métricas
│   │   ├── lib/
│   │   │   ├── api.ts             # API client (injeta Bearer)
│   │   │   └── auth-context.tsx   # Auth provider
│   │   ├── Dockerfile             # Container build
│   │   └── next.config.js
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
├── README.md
└── SPEC.md
```

---

## 📋 Commits em Produção

```
3977c2b fix: LiLi auto-corrige html_garbage (& $ # @ dentro de tags)
0dd448b fix: batch endpoint tambem exige imagem
2b83ec7 fix: imagem obrigatoria em cada artigo — pipeline bloqueia se falhar
130b653 feat: instrucoes de redacao especificas por nicho no BlogWriter
5f477bc fix: pipeline respeita artigos existentes, LiLi detecta garbage
f1a5e01 feat: topicos dinâmicos por nicho + LiLi revisando cada artigo
bab06f4 fix: Seu Pereira reconhece dominio real dezafira.com.br
```

---

## 🗺️ Roadmap

### ✅ Implementado
- [x] Macro-esteira de Blogs com 5 estágios e 9 agentes
- [x] Conveyor belt UI animado na interface
- [x] Blog viewer público com páginas de sistema (privacidade, sobre, contato)
- [x] Temas visuais por nicho (brand_themes.py)
- [x] Instruções de redação específicas por nicho (finanças, cristão, saúde, tecnologia, casa)
- [x] LiLi — revisora automática com auto-correção de conteúdo e HTML
- [x] Imagem obrigatória em cada artigo (Pexels → SVG fallback)
- [x] Pipeline respeita artigos existentes (não gera duplicatas)
- [x] Tópicos dinâmicos gerados por LLM por nicho
- [x] Seu Pereira — Analista de Monetização (19 critérios)
- [x] LLM Cascade (5 provedores com fallback automático)
- [x] Páginas obrigatórias (Privacidade, Sobre, Contato, robots.txt, sitemap.xml, ads.txt)
- [x] Dashboard SPA com métricas em tempo real
- [x] Deploy Railway com domínio próprio (dezafira.com.br)
- [x] Banco PostgreSQL em produção
- [x] **Fábrica de Ebooks** — Pipeline de 6 fases + Checkout + Área de Membro
- [x] **Dezafira Club** — Auth, Gamificação, Cursos, Combos (Next.js 14 + FastAPI)
- [x] **Fábrica de Cursos** — Pipeline de 6 fases + 5 agentes especializados + quizzes + capa
- [x] **Trilhas de Aprendizado** — learning paths com ordenação de cursos
- [x] **Admin Analytics** — métricas reais (usuários, cursos, receita)
- [x] **Integração Fábrica de Blogs/Ebooks no Club** — páginas Next.js com iframe do painel
- [x] **Autenticação Admin** — endpoints das fábricas protegidos com `require_admin`
- [x] **Painel admin protegido** — `GET /` exige token admin (header ou query)

### 🔜 Próximos Passos
- [ ] Google Search Console — Verificação e monitoramento
- [ ] Indexação Google — Solicitar indexação dos artigos
- [ ] Google AdSense — Solicitar aprovação
- [ ] Email de confirmação com link de acesso (SMTP/Resend)
- [ ] Redis — cache e rate limiting ativos em produção
- [ ] Real images nos blogs e club (substituir SVG placeholders)

---

*Dezafira — Ecossistema de Fábricas de Conteúdo v3.2*
