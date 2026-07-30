# DEZAFIRA — Ecossistema de Fábricas de Conteúdo

> **Automação de Conteúdo Digital com IA — 100% CPU, sem GPU**

Dezafira é um ecossistema integrado de fábricas de conteúdo digital — **Blogs, Livros, Cursos, Imagens** e **RAG Bíblico** — tudo orquestrado por agentes inteligentes com nomes brasileiros e monitorado pelo **Seu Pereira**, o analista de monetização.

---

## 🏗️ Arquitetura do Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                     FRONTEND (HTML + JS SPA)                      │
│   Dashboard  │  Pipeline  │  Blogs  │  Livros  │  Cursos        │
└──────────────────────────┬───────────────────────────────────────┘
                           │ API REST
┌──────────────────────────▼───────────────────────────────────────┐
│                     BACKEND (FastAPI) — 100+ endpoints            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                 🏭 Macro-Pipeline                            ││
│  │  Esteira única com 5 estágios animados + 9 agentes          ││
│  └──┬───────────┬───────────┬───────────┬───────────┬──────────┘│
│     ▼           ▼           ▼           ▼           ▼            │
│  🏗️Fundação  📋Arquitetura 📝Produção   🎨Refino    ✅Entrega   │
│  ──────────  ────────────  ──────────  ──────────  ──────────   │
│  Seu Hermes  Joaquim      Carlão       Tatiana     Seu Francisco │
│  Dona Célia               Dona Rosa    Seu Zé                   │
│                                                    Ricardo      │
│                                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │
│  │ 📝 Fábrica   │ │ 📗 Fábrica   │ │ 🎓 Fábrica   │              │
│  │ de Blogs     │ │ de Livros    │ │ de Cursos    │              │
│  │              │ │              │ │              │              │
│  │ BlogWriter   │ │ BookWriter   │ │ CourseWriter │              │
│  │ SEO Optimizer│ │ BookCover    │ │ Module Gen   │              │
│  │ Publisher    │ │ Chapter Gen  │ │ Quiz Gen     │              │
│  └──────────────┘ └──────────────┘ └──────────────┘              │
│                                                                   │
│  ┌──────────────┐ ┌──────────────┐                               │
│  │ 🎨 Fábrica   │ │ 👴 Seu       │                               │
│  │ de Imagens   │ │ Pereira      │                               │
│  │              │ │              │                               │
│  │ FLUX AI      │ │ 19 critérios │                               │
│  │ Pexels API   │ │ 6 categorias │                               │
│  └──────────────┘ └──────────────┘                               │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │              LLM Cascade (4 provedores)                      ││
│  │  NVIDIA NIM → OpenRouter → Gemini → DeepSeek (fallback)     ││
│  │  Database SQLite + SQLAlchemy ORM                            ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

---

## 🏭 A Fábrica de Blogs (Pipeline Principal)

### 🎯 Como Funciona

A macro-esteira cria um blog completo com **N artigos** (configurável) em **5 estágios sequenciais**:

```
🏗️ Fundação → 📋 Arquitetura → 📝 Produção → 🎨 Refino → ✅ Entrega
```

Cada artigo passa por todos os 5 estágios com qualidade e profundidade.

### 👥 Agentes da Pipeline

| Estágio | Agente | Responsabilidade |
|---------|--------|------------------|
| **🏗️ Fundação** | 👴 **Seu Hermes** | Orquestrador, decide temas e estratégia |
| | 👩‍🎨 **Dona Célia** | Designer, cria identidade visual do blog |
| **📋 Arquitetura** | 🔍 **Joaquim** | Pesquisador de keywords e tendências |
| **📝 Produção** | ✍️ **Carlão** | Redator, escreve artigos completos |
| | 🔎 **Dona Rosa** | Revisora, verifica similaridade e qualidade |
| **🎨 Refino** | 📸 **Tatiana** | Fotógrafa, busca imagens (Pexels/FLUX) |
| | 📅 **Seu Zé** | Agendador, programa publicação |
| | 🖼️ **Ricardo** | Especialista em imagens Pexels |
| **✅ Entrega** | 👴 **Seu Francisco** | Supervisor, confere produção e dá sinal verde |

### 📊 Seu Pereira — Analista de Monetização

Agente especialista que avalia se cada blog está no caminho certo para o **Google AdSense**:

- **19 critérios** em **6 categorias** (Conteúdo, Páginas, Design, Técnico, SEO, Autoridade)
- Pontuação automática com recomendações priorizadas
- Painel no Dashboard mostrando progresso e próximos passos
- Sistema de dependências entre critérios

---

## 🛠️ Tecnologias

| Camada | Tecnologias |
|--------|-------------|
| **Backend** | FastAPI (Python 3.11+), Uvicorn |
| **ORM** | SQLAlchemy + SQLite (dev) / PostgreSQL (prod) |
| **LLM Cascade** | NVIDIA NIM → OpenRouter → Gemini → DeepSeek |
| **Imagens** | FLUX.1 (Hugging Face) + Pexels API |
| **Frontend** | HTML + CSS + JavaScript SPA (vanilla) |
| **Infraestrutura** | Railway (Docker), CPU-only |

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
NVIDIA_API_KEY=nvapi-...              # Tenta primeiro
OPENROUTER_API_KEY=sk-or-...          # Fallback 2
GEMINI_API_KEY=AI...                  # Fallback 3
DEEPSEEK_API_KEY=sk-...               # Fallback 4 (nunca falha)

# ─── Imagens (recomendado pelo menos um) ───
HUGGINGFACE_TOKEN=hf_...              # FLUX.1 (geração AI)
PEXELS_API_KEY=...                    # Pexels (stock photos)

# ─── Opcional ───
DATABASE_URL=sqlite:///./dezafira.db  # Caminho do banco
```

---

## 📁 Estrutura do Projeto

```
dezafira/
├── SniperVideoEngine/
│   ├── server.py                  # API principal (100+ endpoints)
│   ├── modules/
│   │   ├── database.py            # SQLAlchemy ORM
│   │   ├── blog_writer.py         # Geração de artigos via LLM
│   │   ├── blog_pipeline.py       # Macro-esteira com 5 estágios
│   │   ├── blog_publisher.py      # Publicação em plataformas
│   │   ├── seu_pereira.py         # Analista de monetização
│   │   ├── seu_ze.py              # Agendador de produção
│   │   ├── ricardo.py             # Especialista em imagens
│   │   └── telegram_bot.py        # Bot Telegram (opcional)
│   ├── agents/
│   │   ├── book_factory.py        # Fábrica de Livros
│   │   ├── course_factory.py      # Fábrica de Cursos
│   │   ├── image_factory.py       # Fábrica de Imagens
│   │   └── llm.py                 # LLM compartilhado com cascade
│   ├── static/
│   │   ├── index.html             # UI Dashboard SPA
│   │   └── o-reino.html           # Blog viewer público
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
└── README.md
```

---

### 🔍 RAG Bíblico
Busca semântica inteligente nos artigos, livros e cursos usando **Sentence-Transformers** para embeddings e **LLM cascade** para respostas com citações.

```
Pergunta → Embeddings (all-MiniLM-L6-v2) → Cosine Similarity → Contexto → LLM → Resposta + Fontes
```

---

## 📋 API Endpoints (102 endpoints)

### Dashboard & Geral
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/factory/dashboard` | Dashboard consolidado |
| `GET` | `/api/v1/monetization/status` | Avaliação Seu Pereira |

### Fábrica de Blogs
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/v1/pipeline/run-blog-factory` | Iniciar macro-esteira |
| `GET` | `/api/v1/blog/{slug}/posts` | Listar artigos do blog |
| `GET` | `/api/v1/blog/{slug}/info` | Info do blog |
| `GET` | `/blog/{slug}` | Blog viewer público |
| `GET` | `/blog/{slug}/privacidade` | Política de Privacidade |
| `GET` | `/blog/{slug}/sobre` | Sobre Nós |
| `GET` | `/blog/{slug}/contato` | Contato |
| `GET` | `/robots.txt` | Robots.txt |
| `GET` | `/sitemap.xml` | Sitemap XML |
| `GET` | `/ads.txt` | Ads.txt |

### Fábrica de Livros
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/v1/books` | Listar livros |
| `POST` | `/api/v1/books/generate` | Gerar novo livro |

### Fábrica de Cursos
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/v1/courses` | Listar cursos |
| `POST` | `/api/v1/courses/generate` | Gerar novo curso |

### Imagens & Hermes
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/v1/images/generate-blog-image` | Gerar imagem para blog |
| `POST` | `/api/v1/hermes/chat` | Chat com Hermes |

---

## 🤖 Todos os Agentes

| Agente | Nome | Fábrica | Função |
|--------|------|---------|--------|
| **Hermes** | Seu Hermes | 🏭 Orquestrador | Comanda todas as fábricas |
| **Joaquim** | Joaquim | 🔍 Pesquisa | Pesquisa keywords e tendências |
| **Carlão** | Carlão | 📝 Blogs | Redator de artigos |
| **Dona Rosa** | Dona Rosa | 📝 Blogs | Revisora de conteúdo |
| **Dona Célia** | Dona Célia | 🎨 Design | Designer de identidade visual |
| **Tatiana** | Tatiana | 🎨 Imagens | Fotógrafa (busca imagens) |
| **Seu Zé** | Seu Zé | ⏰ Scheduler | Agendador de produção |
| **Ricardo** | Ricardo | 🖼️ Imagens | Especialista em imagens Pexels |
| **Seu Francisco** | Seu Francisco | ✅ Entrega | Supervisor de qualidade |
| **Seu Pereira** | Seu Pereira | 👴 Monetização | Analista de AdSense |
| **BlogWriter** | — | 📝 Blogs | Motor de geração de artigos |
| **BookWriterAgent** | — | 📗 Livros | Motor de geração de livros |
| **CourseWriterAgent** | — | 🎓 Cursos | Motor de geração de cursos |
| **ImageGeneratorAgent** | — | 🎨 Imagens | Motor de geração de imagens |

---

## 🗺️ Roadmap

### ✅ Implementado
- [x] Macro-esteira de Blogs com 5 estágios e 9 agentes
- [x] Conveyor belt UI animado na interface
- [x] Blog viewer público com espaços para anúncios
- [x] Fábrica de Livros (e-books completos)
- [x] Fábrica de Cursos (módulos, aulas, quizzes)
- [x] Fábrica de Imagens (FLUX + Pexels)
- [x] Seu Pereira — Analista de Monetização AdSense
- [x] LLM Cascade (4 provedores com fallback automático)
- [x] Páginas obrigatórias (Privacidade, Sobre, Contato)
- [x] Arquivos técnicos (robots.txt, sitemap.xml, ads.txt)
- [x] Dashboard SPA com métricas em tempo real

### 🔜 Próximos Passos
- [ ] **Deploy Railway** — Configurar domínio real e SSL
- [ ] Google Search Console — Verificação e monitoramento
- [ ] Indexação Google — Acompanhar artigos indexados
- [ ] Google AdSense — Solicitar aprovação
- [ ] Página de Vendas 1Convite — Mini App com checkout
- [ ] Fábrica de Blogs expandir — Mais nichos

---

*Dezafira — Ecossistema de Fábricas de Conteúdo v2.0*
