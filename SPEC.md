# SPEC.md — Dezafira Pipeline Specification

> **Versão:** 4.0
> **Data:** 2026-07-30
> **Status:** Ecossistema de 4 Fábricas + Analista de Monetização

---

## 1. Visão Geral

Dezafira é um ecossistema de automação de conteúdo digital com **4 fábricas integradas** e **Seu Pereira** como analista de monetização.

| # | Fábrica | Motor | Status |
|---|---------|-------|--------|
| 1 | 📝 **Fábrica de Blogs** | Macro-esteira 5 estágios + LLM cascade | ✅ Produção |
| 2 | 📗 **Fábrica de Livros** | BookWriterAgent (LLM) | ✅ Produção |
| 3 | 🎓 **Fábrica de Cursos** | CourseWriterAgent (LLM) | ✅ Produção |
| 4 | 🎨 **Fábrica de Imagens** | FLUX.1 (HF) + Pexels API | ✅ Produção |
| — | 🔍 **RAG Bíblico** | Sentence-Transformers + LLM cascade | ✅ Beta |
| — | 👴 **Seu Pereira** | Analista de Monetização AdSense | ✅ Beta |

### Restrições de Infraestrutura
- **Plataforma:** Railway (Docker containers) / Local (Windows/Linux)
- **Hardware:** CPU only (sem GPU)
- **Banco:** SQLite (dev) / PostgreSQL (production)
- **LLM Cascade:** NVIDIA NIM → OpenRouter → Gemini → DeepSeek

---

## 2. Arquitetura

```
┌────────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Browser)                           │
│         UI Dashboard SPA + Blog Viewer + Pipeline Animado          │
└────────────────────────────┬───────────────────────────────────────┘
                             │ HTTP REST API
┌────────────────────────────▼───────────────────────────────────────┐
│                        SERVER (FastAPI)                             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  🏭 Macro-Pipeline (blog_pipeline.py)                        │  │
│  │  5 estágios: Fundação → Arquitetura → Produção → Refino →   │  │
│  │  → Entrega. Produção em massa de N artigos por blog.        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ 📝 Blog  │ │ 📗 Book  │ │ 🎓 Course │ │ 🎨 Image │              │
│  │ Factory  │ │ Factory  │ │ Factory   │ │ Factory  │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
│                                                                     │
│  ┌──────────────┐ ┌─────────────────────────────────────────────┐  │
│  │ 👴 Seu       │ │  LLM Cascade                                │  │
│  │  Pereira     │ │  NVIDIA NIM → OpenRouter → Gemini → DeepSeek│  │
│  │  19 critérios│ │  Fallback automático em cada chamada        │  │
│  └──────────────┘ └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Macro-Esteira de Blogs

### 3.1 Fluxo Completo

```
Usuário define: Nome do Blog + Nicho + N artigos
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 🏗️ FUNDAÇÃO (Hermes + Dona Célia)                              │
│ • Cria canal no banco (BlogChannel)                            │
│ • Define identidade visual e tom de voz                        │
│ • Gera N topics únicos para os artigos                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ 📋 ARQUITETURA (Joaquim)                                        │
│ • Pesquisa palavras-chave para cada topic                       │
│ • Analisa concorrência e tendências                             │
│ • Gera estrutura de SEO para cada artigo                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ 📝 PRODUÇÃO (Carlão + Dona Rosa)                                │
│ • Gera artigo completo via LLM cascade (1100-1500 palavras)     │
│ • Título, slug, conteúdo HTML, excerpt, keywords                │
│ • Revisão de similaridade e qualidade                           │
│ • LOOP: repete para cada um dos N artigos                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ 🎨 REFINO (Tatiana + Seu Zé + Ricardo)                          │
│ • Tatiana busca imagens no Pexels para cada artigo              │
│ • Ricardo gera/refina imagens se necessário                     │
│ • Seu Zé programa agendamento de publicação                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ ✅ ENTREGA (Seu Francisco)                                      │
│ • Verifica qualidade: todos os artigos têm imagem?             │
│ • Conferência final da produção                                │
│ • Sinal verde: blog completo com N artigos                     │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Arquitetura do Pipeline

**Arquivo:** `modules/blog_pipeline.py`
**Classe:** `BlogPipeline`
**WebSocket:** comunicação em tempo real com UI

```python
class BlogPipeline:
    async def run_macro(self):
        # 5 fases, N artigos cada
        await self._phase_fundacao()     # 1x por blog
        await self._phase_arquitetura()  # N vezes (1 por artigo)
        await self._phase_producao()     # N vezes
        await self._phase_refino()       # N vezes
        await self._phase_entrega()      # 1x no final
```

### 3.3 UI (Conveyor Belt)

- **5 estágios visuais** com animação de esteira
- Conectores que acendem quando o estágio é concluído
- Barra de progresso global (artigos concluídos / total)
- Log em tempo real via WebSocket
- Histórico de pipelines executadas

### 3.4 Modelo de Dados

```python
class BlogChannel(Base):
    __tablename__ = "blog_channels"
    id, name, nicho, lang, platform, site_url, banner_url, status, frequency

class BlogPost(Base):
    __tablename__ = "blog_posts"
    id, channel_id, title, slug, content, excerpt, keywords,
    featured_image_url, status, word_count, topic, created_at, published_at

class BlogSection(Base):
    __tablename__ = "blog_sections"
    id, channel_id, name, slug, keywords, target_articles

class BlogPipelineRun(Base):
    __tablename__ = "blog_pipeline_runs"
    id, channel_id, phase, status, total_articles_target,
    articles_generated, current_round, pipeline_data
```

---

## 4. Seu Pereira — Analista de Monetização

**Arquivo:** `modules/seu_pereira.py`
**Classe:** `SeuPereira`

### 4.1 Critérios de Avaliação (19)

| ID | Categoria | Critério | Peso | Depende |
|----|-----------|----------|------|---------|
| content_articles_count | 📝 Conteúdo | 20+ artigos publicados | 8 | — |
| content_word_count | 📝 Conteúdo | 800+ palavras por artigo | 8 | — |
| content_images | 📝 Conteúdo | Imagens em todos os artigos | 5 | — |
| content_originality | 📝 Conteúdo | Conteúdo 100% original | 10 | articles_count |
| content_niche_allowed | 📝 Conteúdo | Nicho permitido pelo AdSense | 10 | — |
| pages_privacy | 📄 Páginas Obrig. | Política de Privacidade (LGPD) | 10 | — |
| pages_about | 📄 Páginas Obrig. | Página Sobre Nós | 6 | — |
| pages_contact | 📄 Páginas Obrig. | Página de Contato | 6 | — |
| design_responsive | 🎨 Design & UX | Design responsivo (mobile) | 7 | — |
| design_navigation | 🎨 Design & UX | Navegação limpa e funcional | 5 | — |
| design_speed | 🎨 Design & UX | Velocidade de carregamento | 6 | — |
| tech_domain | 🔧 Técnico | Domínio próprio configurado | 9 | — |
| tech_ssl | 🔧 Técnico | SSL/HTTPS ativo | 8 | domain |
| tech_search_console | 🔧 Técnico | Google Search Console | 7 | domain |
| tech_robots_txt | 🔧 Técnico | robots.txt configurado | 4 | domain |
| tech_ads_txt | 🔧 Técnico | ads.txt configurado | 5 | domain |
| seo_indexed | 🔍 Indexação | Páginas indexadas no Google | 8 | search_console, articles |
| seo_sitemap | 🔍 Indexação | Sitemap XML configurado | 5 | domain |
| authority_eeat | 🏛️ Autoridade | Credibilidade E-E-A-T | 6 | about |

**Score máximo:** 133 pontos

### 4.2 Status

| Pontuação | Status | Label |
|-----------|--------|-------|
| ≥ 80% | ✅ ready | Pronto para solicitar o AdSense |
| ≥ 50% | 🟡 almost | Quase lá! Faltam requisitos prioritários |
| ≥ 20% | 🟠 progress | Em progresso |
| < 20% | 🔴 starting | Precisa de muito trabalho |

---

## 5. LLM Cascade

**Arquivo:** `agents/llm.py`

### 5.1 Ordem de Tentativa

```
1. NVIDIA NIM (Llama 3.3 70B) — query_llm()
   → Se falhar (timeout, erro de API, etc.)
2. OpenRouter (Llama 3.3 via API)
   → Se falhar
3. Google Gemini (Gemini 1.5 Pro/Flash)
   → Se falhar
4. DeepSeek (DeepSeek V3)
   → Único pago, nunca falha
```

### 5.2 Configuração

```python
LLM_CASCADE = [
    {"provider": "nvidia",    "model": "meta/llama-3.3-70b-instruct",   "api_key": "NVIDIA_API_KEY"},
    {"provider": "openrouter","model": "meta-llama/llama-3.3-70b-instruct","api_key": "OPENROUTER_API_KEY"},
    {"provider": "gemini",    "model": "gemini-1.5-pro",               "api_key": "GEMINI_API_KEY"},
    {"provider": "deepseek",  "model": "deepseek-chat",                "api_key": "DEEPSEEK_API_KEY"},
]
```

---

## 6. Fábrica de Livros 📗

### 6.1 Fluxo
```
Tema → BookWriterAgent → Capítulos com conteúdo → Capa (FLUX/Pexels) → Livro salvo
```

### 6.2 Modelos
```python
class Book(Base):
    id, title, subtitle, author, description, cover_url, topic,
    keywords, status, total_chapters, total_words, price_cents

class BookChapter(Base):
    id, book_id, chapter_number, title, content, word_count
```

---

## 7. Fábrica de Cursos 🎓

### 7.1 Fluxo
```
Tema → CourseWriterAgent → Módulos → Aulas + Quizzes → Curso salvo
```

### 7.2 Modelos
```python
class Course(Base):
    id, title, subtitle, description, cover_url, topic, keywords,
    status, total_modules, total_lessons, difficulty, price_cents

class CourseModule(Base): ...
class CourseLesson(Base): ...
class CourseQuiz(Base): ...
```

---

## 8. Fábrica de Imagens 🎨

### 8.1 Fluxo
```
Descrição → FLUX.1 (Hugging Face) → Imagem Gerada
         → Pexels API (fallback) → URL da imagem stock
```

### 8.2 Funções
- `generate_blog_image(topic)` → Imagem para artigo
- `generate_cover(title, topic)` → Capa de livro
- `generate_course_thumbnail(title, topic)` → Thumbnail de curso

---

## 9. Páginas de Sistema

Todas servidas como endpoints FastAPI para qualquer blog:

| Rota | Descrição |
|------|-----------|
| `/blog/{slug}/privacidade` | Política de Privacidade com LGPD |
| `/blog/{slug}/sobre` | Sobre Nós com autoridade no nicho |
| `/blog/{slug}/contato` | Formulário de contato |
| `/robots.txt` | Permite Googlebot, bloqueia /api/ |
| `/sitemap.xml` | Dinâmico com todos os artigos |
| `/ads.txt` | Placeholder para Google AdSense |

---

## 10. Banco de Dados

**ORM:** SQLAlchemy com fallback resiliente:
1. Tenta SQLite no caminho do projeto
2. Se falhar (Windows path), fallback para `:memory:`

### Todos os Modelos

| Modelo | Tabela | Descrição |
|--------|--------|-----------|
| `BlogChannel` | `blog_channels` | Canais de blog |
| `BlogPost` | `blog_posts` | Artigos do blog |
| `BlogSection` | `blog_sections` | Seções/micro-nichos |
| `BlogPipelineRun` | `blog_pipeline_runs` | Execuções da esteira |
| `Book` | `books` | Livros digitais |
| `BookChapter` | `book_chapters` | Capítulos dos livros |
| `Course` | `courses` | Cursos |
| `CourseModule` | `course_modules` | Módulos dos cursos |
| `CourseLesson` | `course_lessons` | Aulas |
| `Channel` | `channels` | (Legado) |
| `Prediction` | `predictions` | (Legado) |
| `DeliverableApp` | `deliverable_apps` | Mini Apps |

---

## 11. API Endpoints Completos

### 11.1 Health & Geral
| Método | Rota |
|--------|------|
| `GET` | `/health` |
| `GET` | `/api/v1/factory/dashboard` |
| `GET` | `/api/v1/logs` |

### 11.2 Monetização (Seu Pereira)
| Método | Rota |
|--------|------|
| `GET` | `/api/v1/monetization/status` |

### 11.3 Pipeline
| Método | Rota |
|--------|------|
| `POST` | `/api/v1/pipeline/run-blog-factory` |
| `GET` | `/api/v1/pipeline/blog-factory/history` |
| `POST` | `/api/v1/pipeline/generate-images` |

### 11.4 Blog
| Método | Rota |
|--------|------|
| `GET` | `/api/v1/blog/{slug}/info` |
| `GET` | `/api/v1/blog/{slug}/posts` |
| `GET` | `/api/v1/blog/{slug}/post/{post_id}` |
| `GET` | `/blog/{slug}` |
| `GET` | `/blog/{slug}/privacidade` |
| `GET` | `/blog/{slug}/sobre` |
| `GET` | `/blog/{slug}/contato` |
| `GET` | `/robots.txt` |
| `GET` | `/sitemap.xml` |
| `GET` | `/ads.txt` |

### 11.5 Books & Courses
| Método | Rota |
|--------|------|
| `GET` | `/api/v1/books` |
| `GET` | `/api/v1/books/{id}` |
| `POST` | `/api/v1/books/generate` |
| `GET` | `/api/v1/courses` |
| `GET` | `/api/v1/courses/{id}` |
| `POST` | `/api/v1/courses/generate` |

### 11.6 Images & Hermes
| Método | Rota |
|--------|------|
| `POST` | `/api/v1/images/generate-blog-image` |
| `POST` | `/api/v1/images/generate-cover` |
| `POST` | `/api/v1/hermes/chat` |
| `GET` | `/api/v1/hermes/history` |

---

## 12. Variáveis de Ambiente

```bash
# ─── LLM Cascade (pelo menos 1) ───
NVIDIA_API_KEY=
OPENROUTER_API_KEY=
GEMINI_API_KEY=
DEEPSEEK_API_KEY=

# ─── Imagens (pelo menos 1) ───
HUGGINGFACE_TOKEN=
PEXELS_API_KEY=

# ─── Banco ───
DATABASE_URL=sqlite:///./dezafira.db

# ─── Deploy ───
SITE_URL=https://dezafira.com.br
```

---

## 13. Agentes do Sistema

| Nome | Nome Real | Arquivo | Função |
|------|-----------|---------|--------|
| Hermes | Seu Hermes | server.py | Orquestrador |
| Joaquim | Joaquim | blog_pipeline.py | Pesquisador |
| Carlão | Carlão | blog_writer.py | Redator |
| Dona Rosa | Dona Rosa | blog_pipeline.py | Revisora |
| Dona Célia | Dona Célia | blog_pipeline.py | Designer |
| Tatiana | Tatiana | blog_pipeline.py | Fotógrafa |
| Seu Zé | Seu Zé | seu_ze.py | Agendador |
| Ricardo | Ricardo | ricardo.py | Especialista Imagens |
| Seu Francisco | Seu Francisco | blog_pipeline.py | Supervisor |
| Seu Pereira | Seu Pereira | seu_pereira.py | Monetização |

---

## 14. Roadmap

### ✅ Implementado v2.0
- [x] Macro-esteira de Blogs com 5 estágios (conveyor belt UI)
- [x] 9 agentes com nomes brasileiros na pipeline
- [x] Seu Pereira — 19 critérios de monetização
- [x] LLM Cascade com 4 provedores
- [x] Blog viewer público com páginas de sistema
- [x] Fábrica de Livros (completa)
- [x] Fábrica de Cursos (módulos + aulas + quizzes)
- [x] Fábrica de Imagens (FLUX + Pexels)
- [x] Dashboard SPA com métricas em tempo real
- [x] Sistema de dependências entre critérios

### 🔜 Planejado
- [ ] Deploy Railway com domínio real
- [ ] Google Search Console integrado
- [ ] Solicitação Google AdSense
- [ ] Página de Vendas 1Convite
- [ ] Blog to Podcast (artigos → áudio)
- [ ] Expansão para múltiplos nichos

---

*SPEC v4.0 — Ecossistema Dezafira — 2026-07-30*
