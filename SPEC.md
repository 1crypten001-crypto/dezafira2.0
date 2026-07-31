# SPEC.md — Dezafira Pipeline Specification

> **Versão:** 4.3
> **Data:** 2026-07-31
> **Status:** Fábrica de Blogs em produção com 89 artigos, 2 blogs, 100% imagens, Google Hype Engine, Split Hero UX, LiLi com score em cache + ranking + regeneração persistida
> **Produção:** https://dezafira.com.br

---

## 1. Visão Geral

Dezafira é um ecossistema de automação de conteúdo digital com foco atual na **Fábrica de Blogs** e **Seu Pereira** como analista de monetização.

| # | Fábrica | Motor | Status |
|---|---------|-------|--------|
| 1 | 📝 **Fábrica de Blogs** | Macro-esteira 5 estágios + LLM cascade | ✅ Produção (89 artigos) |
| 2 | 📗 **Fábrica de Livros** | BookWriterAgent (LLM) | ⏳ Em espera |
| 3 | 🎓 **Fábrica de Cursos** | CourseWriterAgent (LLM) | ⏳ Em espera |
| 4 | 🎨 **Fábrica de Imagens** | Pexels API + SVG fallback | ✅ Produção |
| — | 👴 **Seu Pereira** | Analista de Monetização AdSense | ✅ Ativo (88.7%) |

### Restrições de Infraestrutura
- **Plataforma:** Railway (Docker containers) / Local (Windows/Linux)
- **Hardware:** CPU only (sem GPU)
- **Banco:** PostgreSQL (produção) / SQLite (desenvolvimento)
- **LLM Cascade:** OpenRouter → Gemini → NVIDIA → HuggingFace → DeepSeek

---

## 2. Estado Atual da Fábrica de Blogs

### 2.1 Blogs em Produção

| Blog | Nicho | Artigos | C/Imagem | Publicados | Score LiLi | URL |
|------|-------|---------|----------|------------|------------|-----|
| ✝️ O Reino | Ensinamentos de Jesus | 41 | 41 (100%) | 39 | 55/100 | /blog/o-reino |
| 💰 Vida Financeira | Finanças, Investimentos | 48 | 48 (100%) | 37 | 81/100 | /blog/vida-financeira |
| **Total** | | **89** | **89 (100%)** | **76** | **~84/100** | |

### 2.2 Score LiLi — Cache no Banco

Desde v4.3 o score LiLi é **persistido no banco** (colunas `lili_score`, `lili_approved`, `lili_reviewed_at` em `blog_posts`), com migração idempotente no boot. O dashboard e o ranking leem do cache em vez de recalcular a cada request (2ª chamada ~4s vs ~40s).

### 2.3 Temas Visuais

Cada blog tem identidade visual própria via `brand_themes.py`:

| Nicho | Tema | Cores | Fonte |
|-------|------|-------|-------|
| Cristão | Dourado/tradição | `#d4a853`, `#1a1410`, `#8b2500` | Playfair Display |
| Finanças | Verde/prosperidade | `#059669`, `#022c22`, `#0d9488` | Inter |

### 2.4 Seu Pereira — Score Atual

**88.7% (17/18)** — Status: **✅ Pronto para solicitar o AdSense!** (118/133 pontos, avaliado em 31/07/2026).

**Pendente:** apenas 1 critério (Google Search Console / Indexação).

---

## 3. Macro-Esteira de Blogs

### 3.1 Fluxo Completo

```
Usuário define: Nome do Blog + Nicho + N artigos
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 🏗️ FUNDAÇÃO (Seu Hermes + Dona Célia)                          │
│ • Cria canal no banco (BlogChannel)                            │
│ • Verifica se blog já existe (evita duplicatas)                │
│ • Gera brand bible via LLM                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ 📋 ARQUITETURA (Joaquim)                                        │
│ • Pesquisa palavras-chave (Obscura ou fallback)                 │
│ • Identifica seções e micro-nichos                              │
│ • Busca "frutas baixas" (baixa concorrência)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ 📝 PRODUÇÃO (Carlão + LiLi)                                     │
│ • Gera tópicos dinâmicos ESPECÍFICOS do nicho via LLM          │
│ • Gera artigo completo via 8 chamadas LLM (multiparte)         │
│   - Planejamento → Introdução → 5 Seções → Conclusão           │
│ • Cada seção com instruções de redação específicas do nicho    │
│ • Gera imagem IMEDIATAMENTE após o artigo (obrigatório)        │
│ • LiLi revisa e auto-corrige o artigo                          │
│ • Se imagem falhar → artigo descartado + pipeline continua     │
│ • LOOP: repete para cada um dos N artigos                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ 🎨 REFINO (Tatiana + Seu Zé)                                    │
│ • Links internos entre artigos                                  │
│ • Seu Zé agenda publicação diária (1 artigo/dia às 08:00)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ ✅ ENTREGA (Seu Francisco)                                      │
│ • Seu Francisco confere a produção                              │
│ • LiLi faz revisão final de todos os artigos                   │
│ • Ricardo gera imagens pendentes (retry)                        │
│ • Relatório final: N artigos, ~X palavras                      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Pipeline — Correções Implementadas (Julho 2026)

| Problema | Causa Raiz | Correção |
|----------|-----------|----------|
| 108 artigos em vez de 30 | Pipeline não verificava artigos existentes | Contar artigos existentes no DB antes de gerar, ajustar target_articles |
| Garbage text (`Aerial: "The:"`) não detectado | LiLi sem padrão para dois-pontos após aspas | 2 novos BAD_PATTERNS: colon_quote_colon_garbage + repeat_word_colon_quote |
| Viés cristão no conteúdo de finanças | Prompt de seções com "inclua citações bíblicas" | Prompt neutro + instruções específicas por nicho |
| Artigos sem imagem | `import base64` faltando (placeholder SVG quebrava) | Adicionado `import base64` |
| Imagem não era obrigatória | try/except silencioso na geração de imagem | Imagem agora é obrigatória - falha deleta o artigo |
| HTML garbage não auto-corrigido | LiLi detectava mas não limpava | Adicionado passo 8: limpa & $ # @ \\ dentro de tags |

### 3.3 Modelo de Dados

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

class BlogSubdomain(Base):
    __tablename__ = "blog_subdomains"
    id, channel_id, subdomain
```

---

## 4. Seu Pereira — Analista de Monetização

**Arquivo:** `modules/seu_pereira.py`

### 4.1 Critérios de Avaliação (19 definidos / 18 avaliados — seo_indexed aguarda GSC)

| ID | Categoria | Critério | Peso | Status Atual |
|----|-----------|----------|------|-------------|
| content_articles_count | 📝 Conteúdo | 20+ artigos publicados | 8 | ✅ 89 artigos |
| content_word_count | 📝 Conteúdo | 800+ palavras por artigo | 8 | ✅ Média 2.238 |
| content_images | 📝 Conteúdo | Imagens em todos os artigos | 5 | ✅ 100% |
| content_originality | 📝 Conteúdo | Conteúdo 100% original | 10 | ✅ |
| content_niche_allowed | 📝 Conteúdo | Nicho permitido pelo AdSense | 10 | ✅ |
| pages_privacy | 📄 Páginas Obrig. | Política de Privacidade | 10 | ✅ |
| pages_about | 📄 Páginas Obrig. | Página Sobre Nós | 6 | ✅ |
| pages_contact | 📄 Páginas Obrig. | Página de Contato | 6 | ✅ |
| design_responsive | 🎨 Design & UX | Design responsivo | 7 | ✅ |
| design_navigation | 🎨 Design & UX | Navegação limpa | 5 | ✅ |
| design_speed | 🎨 Design & UX | Velocidade de carregamento | 6 | ✅ |
| tech_domain | 🔧 Técnico | Domínio próprio | 9 | ✅ dezafira.com.br |
| tech_ssl | 🔧 Técnico | SSL/HTTPS ativo | 8 | ✅ Railway |
| tech_search_console | 🔧 Técnico | Google Search Console | 7 | ❌ Único pendente |
| tech_robots_txt | 🔧 Técnico | robots.txt | 4 | ✅ |
| tech_ads_txt | 🔧 Técnico | ads.txt | 5 | ✅ |
| seo_indexed | 🔍 Indexação | Páginas indexadas | 8 | ⏳ Dependente do GSC |
| seo_sitemap | 🔍 Indexação | Sitemap XML | 5 | ✅ |
| authority_eeat | 🏛️ Autoridade | E-E-A-T | 6 | ✅ |

**Score atual:** 88.7% (17/18) — ✅ Pronto para solicitar o AdSense (118/133)

---

## 5. LLM Cascade

**Arquivo:** `modules/blog_writer.py` (função `_call_llm`)

### 5.1 Ordem de Tentativa

```
1. OpenRouter (Llama 3.3 70B) — gratuito, vários modelos
   → Se falhar (402 sem créditos, timeout, etc.)
2. Google Gemini (Gemini 2.0 Flash / 1.5 Pro) — gratuito
   → Se falhar
3. NVIDIA NIM (Llama 3.3 70B) — se chave real disponível
   → Se falhar
4. HuggingFace Inference API (Mixtral, Zephyr, Phi-3) — gratuito
   → Se falhar
5. DeepSeek (DeepSeek V3) — único pago, nunca falha
```

### 5.2 Geração de Artigos (Multiparte)

Cada artigo usa **8 chamadas LLM** separadas para qualidade máxima:

1. **Planejamento** — Outline com título, seções, keywords
2. **Introdução** — Gancho forte + contexto (~400-600 palavras)
3. **Seção 1-5** — Cada seção escrita separadamente
4. **Conclusão** — Reflexão + CTA (~300-500 palavras)

As instruções de redação são **específicas do nicho** detectado automaticamente (`_detect_niche`):

| Nicho | Instruções |
|-------|-----------|
| Finanças | Dados numéricos, comparações, fontes BR (IBGE, BC), regras práticas, passos acionáveis |
| Cristão | Referências bíblicas com versículos, tom pastoral, aplicação prática da fé |
| Saúde | Fontes científicas, recomendações de especialistas, dados OMS/MS |
| Tecnologia | Benchmarks, comparações, conceitos acessíveis, tendências |
| Casa | Passo a passo, custo-benefício, materiais acessíveis |

---

## 6. LiLi — Revisora de Qualidade

**Arquivo:** `modules/lili.py`

### 6.1 Padrões Detectados (15)

| Padrão | Severidade | Exemplo | Auto-corrige? |
|--------|-----------|---------|---------------|
| exclamacoes_em_massa | alta | `!!!!!!` | ✅ Remove |
| micro_biologia_gibberish | alta | "micro biologia" | ✅ Substitui |
| english_words | media | "everything", "someone" | ✅ Traduz |
| **html_garbage** | **alta** | **& $ # @ dentro de tags** | **✅ Remove (novo!)** |
| paragrafo_curto | media | `<p>Oi</p>` | ❌ |
| repeticao_frase | media | Frase duplicada | ❌ |
| encoding_quebrado | alta | \\u00ad | ✅ Corrige |
| colon_sequence_double | alta | `Aerial: "The: "` | ❌ |
| colon_quote_colon_garbage | alta | `Aerial: "The:"` | ❌ |
| repeat_word_colon_quote | alta | `Aerial\\: "The":` | ❌ |

### 6.2 Score

- Score = 100 - (15 × issues_alta + 5 × issues_media + 2 × issues_baixa)
- Aprovado se score >= 70 E nenhum issue de severidade 'alta'
- Score médio real: **~84/100** com os novos padrões estritos (pode variar conforme padrões aplicados)

### 6.3 Ferramentas de Qualidade (v4.3)

| Recurso | Endpoint | Descrição |
|---------|----------|-----------|
| Cache do score | — | `lili_score`/`lili_approved` persistidos no banco (dashboard cache-aware) |
| Ranking global | `GET /api/v1/lili/ranking` | Todos os artigos por score, filtros por blog/status, medalhas #1/#2/#3 |
| Score no painel | — | Badge `🌸 NN/100` por artigo + média por blog na UI Admin |
| Corrigir | `POST /api/v1/lili/correct/{id}` | Auto-correção via LiLi (texto + HTML) |
| Regenerar artigo | `POST /api/v1/blog/post/{id}/regenerate` | Recria do zero (texto + imagem + revisão), preserva status |
| Regenerar imagem | `POST /api/v1/blog/post/{id}/regenerate-image` | Apenas a imagem, mantém texto e score |
| Regenerar em lote | `POST /api/v1/lili/regenerate-batch` | Reprovação em massa (score < 70), **persistida em job** |
| Status do job | `GET /api/v1/lili/regenerate-jobs/{job_id}` | Progresso do lote (itens done/failed/processing) |

---

## 7. Páginas de Sistema

Todas servidas como endpoints FastAPI para qualquer blog:

| Rota | Descrição |
|------|-----------|
| `/blog/{slug}` | Blog viewer público com tema do nicho |
| `/blog/{slug}/privacidade` | Política de Privacidade com LGPD |
| `/blog/{slug}/sobre` | Sobre Nós com autoridade no nicho |
| `/blog/{slug}/contato` | Formulário de contato |
| `/robots.txt` | Permite Googlebot, bloqueia /api/ |
| `/sitemap.xml` | Dinâmico com todos os artigos |
| `/ads.txt` | Placeholder para Google AdSense |

---

## 8. Banco de Dados

**ORM:** SQLAlchemy com PostgreSQL (produção) / SQLite (desenvolvimento)

### Todos os Modelos

| Modelo | Tabela | Descrição | Registros |
|--------|--------|-----------|-----------|
| `BlogChannel` | `blog_channels` | Canais de blog | 2 |
| `BlogPost` | `blog_posts` | Artigos do blog | 89 |
| `BlogSection` | `blog_sections` | Seções/micro-nichos | ~12 |
| `BlogPipelineRun` | `blog_pipeline_runs` | Execuções da esteira | ~20 |
| `BlogSubdomain` | `blog_subdomains` | Subdomínios dos blogs | 2 |
| `RegenerationJob` | `regeneration_jobs` | Lotes de regeneração persistidos | 1 |
| `RegenerationJobItem` | `regeneration_job_items` | Itens (artigos) de cada lote | 1 |
| `Book` | `books` | Livros digitais | 0 |
| `Course` | `courses` | Cursos | 0 |
| `Channel` | `channels` | (Legado YouTube) | 0 |

---

## 9. Commits em Produção

```
e56fcc7  fix: abas dos blogs visíveis imediatamente na página Blogs & Pipeline
9a2b811  feat: persiste jobs de regeneração em lote no banco (resiliente a restarts)
db241aa  feat: botão regenerar imagem por artigo e regeneração em lote de reprovados
38c2ee4  feat: cache do score LiLi, botão regenerar e aba Qualidade com ranking
5ad948f  feat: score LiLi por artigo no painel por blog da UI Admin
c66620b  fix: dashboard 500 quebrava abas dos blogs na UI admin (migração + image_provider)
a27aff6  fix: corrige emojis corrompidos (mojibake cp850) na UI admin da esteira
57dd77d  fix: normaliza codificacao UTF-8, emojis e acentos de esteira
ec73d25  fix: implementa get_db_blog_pipeline_runs no database.py para resolver erro 500 do historico
115e6de  fix: corrige SyntaxError JS no postsList
0a6508f  feat: Google Hype Engine, esteira assíncrona com monitor de progresso na ADM
2b878b0  feat: Split Hero UX, imagens conceituais de branding geradas por IA por nicho
f8432b0  feat: Light Mode por padrão, Sumário (TOC) dinâmico e Caixa de Autor (E-E-A-T)
3977c2b  fix: LiLi auto-corrige html_garbage (& $ # @ dentro de tags)
0dd448b  fix: batch endpoint tambem exige imagem (mesma correcao do generate-single)
2b83ec7  fix: imagem obrigatoria em cada artigo — pipeline bloqueia se falhar
130b653  feat: instrucoes de redacao especificas por nicho no BlogWriter
5f477bc  fix: pipeline respeita artigos existentes, LiLi detecta garbage
f1a5e01  feat: topicos dinâmicos por nicho + LiLi revisando cada artigo
bab06f4  fix: Seu Pereira reconhece dominio real dezafira.com.br
04324ef  fix: move subdomain para tabela separada blog_subdomains
```

---

## 10. Roadmap

### ✅ Implementado v4.2
- [x] **Google Hype Engine**: Mineração de tendências reais via Google Autocomplete (`KeywordMiner`) para pautas dinâmicas.
- [x] **Esteira Assíncrona na ADM**: Monitoramento de progresso da esteira por etapas em tempo real na interface administrativa.
- [x] **Split Hero UX**: Layout moderno de duas colunas com imagens conceituais de branding exclusivas por nicho (geradas por IA).
- [x] **Modo Claro Mandatório**: Modo claro como padrão absoluto dos blogs para legibilidade.
- [x] **Sumário Dinâmico & Caixa de Autor**: Injeção automática de TOC nos posts e rodapé rico (E-E-A-T) com a biografia do redator por nicho.
- [x] Macro-esteira de Blogs com 5 estágios (conveyor belt UI)
- [x] 9 agentes com nomes brasileiros na pipeline
- [x] LiLi — revisora com auto-correção (conteúdo + HTML)
- [x] Imagem obrigatória em cada artigo (Pexels → SVG fallback)
- [x] Pipeline respeita artigos existentes (não gera duplicatas)
- [x] Instruções de redação específicas por nicho (5 nichos)
- [x] Tópicos dinâmicos gerados por LLM por nicho
- [x] Temas visuais por nicho (brand_themes.py)
- [x] Seu Pereira — 19 critérios de monetização (88.7% — ✅ Pronto para solicitar o AdSense)
- [x] LLM Cascade com 5 provedores
- [x] Blog viewer público com páginas de sistema
- [x] Dashboard SPA com métricas em tempo real
- [x] **Score LiLi em cache no banco** — leitura instantânea no dashboard e ranking
- [x] **Aba Qualidade com ranking global** — todos os artigos ordenados por score, filtros e medalhas
- [x] **Botão regenerar imagem** por artigo (mantém texto) no painel e na aba Qualidade
- [x] **Regeneração em lote persistida** — jobs no banco sobrevivem a restarts do Railway
- [x] **Abas dos blogs visíveis imediatamente** na página Blogs & Pipeline
- [x] Deploy Railway com PostgreSQL e domínio próprio
- [x] 89 artigos publicados, 100% com imagem

### 🔜 Próximo (prioridade)
- [ ] Google Search Console — Verificação de domínio
- [ ] Indexação Google — Solicitar indexação dos 89 artigos
- [ ] Google AdSense — Solicitar aprovação
- [ ] Fábrica de Livros e Cursos — Ativar produção
- [ ] Página de Vendas 1Convite — Mini App com checkout
- [ ] Blog to Podcast — Artigos → Áudio
- [ ] Expansão para mais nichos (saúde, tecnologia, casa)

---

*SPEC v4.3 — Ecossistema Dezafira — 2026-07-31*
