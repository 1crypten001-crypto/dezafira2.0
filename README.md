# DEZAFIRA — Ecossistema de Fábricas de Conteúdo

> **Automação de Conteúdo Digital com IA — 100% CPU, sem GPU**
> 
> **Produção:** https://dezafira.com.br
> 
> **Status atual:** 77 artigos publicados em 2 blogs, 100% com imagem, score LiLi médio 99.1/100

Dezafira é um ecossistema integrado de fábricas de conteúdo digital — **Blogs, Ebooks, Cursos, Imagens** — tudo orquestrado por agentes inteligentes com nomes brasileiros e monitorado pelo **Seu Pereira**, o analista de monetização.

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
│                                                    LiLi         │
│                                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │
│  │ 📝 Fábrica   │ │ 📗 Fábrica   │ │ 🎓 Fábrica   │              │
│  │ de Blogs     │ │ de Livros    │ │ de Cursos    │              │
│  │  2 blogs     │ │              │ │              │              │
│  │  77 artigos  │ │              │ │              │              │
│  └──────────────┘ └──────────────┘ └──────────────┘              │
│                                                                   │
│  ┌──────────────┐ ┌──────────────┐                               │
│  │ 🎨 Image     │ │ 👴 Seu       │                               │
│  │ Factory      │ │ Pereira      │                               │
│  │ Pexels + SVG │ │ 19 critérios │                               │
│  │ fallback     │ │ 6 categorias │                               │
│  └──────────────┘ └──────────────┘                               │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │              LLM Cascade (5 provedores)                      ││
│  │  OpenRouter → Gemini → NVIDIA → HuggingFace → DeepSeek       ││
│  │  Database PostgreSQL + SQLAlchemy ORM                         ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
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
| **LLM Cascade** | OpenRouter → Gemini → NVIDIA → HuggingFace → DeepSeek |
| **Imagens** | Pexels API (primário) + SVG placeholder (fallback absoluto) |
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
OPENROUTER_API_KEY=sk-or-...          # Tenta primeiro (gratuito)
GEMINI_API_KEY=AI...                  # Fallback 2 (gratuito)
NVIDIA_API_KEY=nvapi-...              # Fallback 3
HUGGINGFACE_TOKEN=hf_...              # Fallback 4 (gratuito)
DEEPSEEK_API_KEY=sk-...               # Fallback 5 (pago, nunca falha)

# ─── Imagens (recomendado) ───
PEXELS_API_KEY=...                    # Pexels (stock photos, gratuita)

# ─── Banco ───
DATABASE_URL=postgresql://...         # PostgreSQL (produção)
```

---

## 📁 Estrutura do Projeto

```
dezafira/
├── SniperVideoEngine/
│   ├── server.py                  # API principal (100+ endpoints)
│   ├── modules/
│   │   ├── database.py            # SQLAlchemy ORM
│   │   ├── blog_writer.py         # Geração de artigos via LLM multiparte
│   │   ├── blog_pipeline.py       # Macro-esteira com 5 estágios
│   │   ├── blog_viewer.py         # Blog viewer público dinâmico
│   │   ├── brand_themes.py        # Temas visuais por nicho
│   │   ├── image_factory.py       # Geração de imagens (Pexels + SVG)
│   │   ├── lili.py                # Revisora de qualidade auto-corretiva
│   │   ├── seu_pereira.py         # Analista de monetização
│   │   └── seu_ze.py              # Agendador de produção
│   ├── static/
│   │   └── index.html             # UI Dashboard SPA
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

### 🔜 Próximos Passos
- [ ] Google Search Console — Verificação e monitoramento
- [ ] Indexação Google — Solicitar indexação dos artigos
- [ ] Google AdSense — Solicitar aprovação
- [ ] Fábrica de Cursos — Integrar na UI principal
- [ ] Página de Vendas 1Convite — Mini App com checkout
- [ ] Blog to Podcast — Artigos → Áudio
- [ ] Email de confirmação com link de acesso (SMTP/Resend)

---

*Dezafira — Ecossistema de Fábricas de Conteúdo v2.2*
