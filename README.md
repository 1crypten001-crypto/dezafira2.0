# DEZAFIRA — Ecossistema de Fábricas de Conteúdo

> **Repositório Oficial:** https://github.com/1crypten001-crypto/dezafira2.0/
>
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
| **DezafiraClube** | Site público, blog SEO, área de membros, landing pages e comunidade (**v1.9**) | SvelteKit 2 + Svelte 5 | `Versões do dezafiraClub/Blog_Inteligente_SEO_com_IA_-_v1.9/` |
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
| **Fábricas** | Blog, Ebook, Curso, Marketing e Bio Sites (5 pipelines completas) |
| **Admin** | Cursos CRUD, trilhas de aprendizagem, analytics, usuários e stats |
| **Painel** | Dashboard do usuário logado (`/painel` — dados de `/auth/me`, cursos e ebooks) |
| **Chat Hermes** | O chat do admin (`/chat`) redireciona para o **AionUi WebUI** (`HERMES_WEBUI_PUBLIC_URL`) **só se o WebUI estiver no ar**; caso contrário serve a página embutida do backend (14/08/2026). O Hermes (Nous Agent) dispara fábricas pela API com service key — **Chainlit removido** (12/08/2026) |

### Frontend (Next.js 14)

```
club-frontend/
├── app/
│   ├── page.tsx                # Landing page (Dezafira Adm — foco nas fábricas)
│   ├── auth/login/page.tsx     # Login (register → redireciona p/ login)
│   ├── painel/page.tsx         # Dashboard do usuário (overview, cursos, ebooks)
│   ├── healthz/                # Healthcheck do frontend
│   └── admin/
│       ├── page.tsx            # Painel admin (Widescreen 3-Col, status do sistema, atividade recente)
│       ├── canais/             # Hub de Canais (lista de canais e criação via formulário integrado)
│       ├── fabrica-blog/       # Fábrica de Blogs (nativa com 3 abas, pipeline IA e envio ao Club)
│       ├── fabrica-ebook/      # Fábrica de Ebooks (nativa com 6 fases e envio ao Club)
│       ├── fabrica-curso/      # Fábrica de Cursos (nativa por abas e publicação)
│       ├── fabrica-vsl/        # Fábrica de VSLs (nativa com aba geradora IA de 5 passos e A/B/C metrics)
│       ├── fabrica-biosites/   # Fábrica de Bio Sites (nativa com mockup de preview mobile)
│       ├── fabrica-mapas/      # Fábrica de Mapas (nativa com visualizador JSON e envio ao Club)
│       ├── fabrica-miniapp/    # Fábrica de MiniApps (nativa com log de agentes ao vivo e preview PWA)
│       ├── trilhas/            # Learning paths
│       └── analytics/          # Métricas e gerenciamento de usuários
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

**Fábrica de Bio Sites**
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/biosites/create` | Geração de Bio Site via pipeline de IA |
| GET | `/api/v1/biosites` | Listar todos os Bio Sites cadastrados |
| GET | `/api/v1/biosites/{bio_id}` | Detalhes de um Bio Site específico |
| PUT | `/api/v1/biosites/{bio_id}` | Atualizar informações, cores e links do Bio Site |
| DELETE | `/api/v1/biosites/{bio_id}` | Deletar Bio Site |
| GET | `/bio/{slug}` | Serve HTML final do Bio Site (público / preview) |


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

### Landing Pages via CLI (v1.9)

O **Seu Hermes** (fábrica de Marketing) publica landings de oferta completas **direto via API** do Clube, sem builder no Adm:

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/cli/landing-pages/schema` | Contratos dos blocos (hero, product-showcase, posts-grid, pricing, faq, cta, testemunhos…) |
| GET | `/api/cli/landing-pages/resources` | Produtos e posts reais do catálogo do Clube |
| POST | `/api/cli/landing-pages` | Cria/publica landing em `/p/{slug}` |
| PUT/DELETE | `/api/cli/landing-pages/{slug}` | Atualiza/remove landing |

- Auth: `Authorization: Bearer <token>` — token gerado em `admin/cli` do Clube (hash + expiração na v1.9; **regenerar no pós-deploy**).
- Exemplo pronto: `Versões do dezafiraClub/Blog_Inteligente_SEO_com_IA_-_v1.9/scripts/landing-via-cli.sh`
- Guia completo: `Versões do dezafiraClub/Blog_Inteligente_SEO_com_IA_-_v1.9/docs/integracao-adm-clube.md`

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

## 🎯 Blueprint de Produto (NOVO — substitui a Fábrica de Produtos)

**Receita de produto:** tema + nicho + preço → a IA gera **tudo** (produto no catálogo, blog + banners, landing page, funil bump/upsell/downsell, área de membros) e a **ponte** publica no DezafiraClube. A UI fica em `/admin/blueprint` (o antigo `fabrica-produtos` redireciona para lá).

**Estágios do motor** (`modules/blueprint_engine.py`): `fundacao` (LLM) → `conteudo` (pipelines existentes) → `assets` (**Agnes AI** → cascata, com super prompt) → `landing` (blocos do Clube via `modules/landing_templates.py`) → `funil` (bump/upsell/downsell) → `revisao` → `publicacao` (ponte).

**Revisão visual de imagens** (`components/AssetSlot.tsx`): miniatura → clique abre a imagem em **tamanho real com dimensões (W×H)** + provedor; **super prompt copiável** ao lado; botões 🔄 **Regenerar** (nova seed), 📤 **Upload** (sua imagem substitui a gerada — nunca é sobrescrita pelo motor) e 🖌️ **Capa Agnes** (capa editorial do Agnes Studio com seletor de estilo — alternativa à imagem por prompt).

**🎨 Brand kit** (por blueprint, persistido em `config.brand_kit`): cores (fundo/destaque/texto) + fontes customizadas — as capas Agnes Studio usam automaticamente. Form na página de detalhe + `PATCH /api/v1/blueprints/{id}`. Aceita **dois formatos**: canônico `{colors: {bg, bg2, accent, text, muted}, font, font_sans}` e plano `{primary_color, accent_color, logo_text}` (normalizado no motor `agnes_studio._make_design`/`landing_templates._kit_colors` e na UI da página de detalhe).

**Capa Agnes automática**: o estágio `assets` gera o slot **`product_image_agnes`** (capa editorial do produto) automaticamente ao lado da imagem por prompt — regenerar/rodar de novo mantém o estilo.

**Publicação** (etapa 6, log por etapa em `publish_log`): filhos upsell/downsell **primeiro** → produto principal (com `youtube_video_url`, `category`, bump e ids da esteira) → `sync-blog` generalizado (posts + banners) → landing via CLI (`Bearer CLI_TOKEN`) → área de membros (`member-course`).

| Método | Rota (Adm, `require_admin`) | Descrição |
|--------|------|-----------|
| POST | `/api/v1/blueprints` | Criar receita (draft) |
| GET | `/api/v1/blueprints` · `/{id}` | Listar / estado completo |
| POST | `/api/v1/blueprints/{id}/run` | Disparar o motor (0–5) |
| POST | `/api/v1/blueprints/{id}/assets/regenerate` | Regenerar slot (`{slot}`) |
| PATCH | `/api/v1/blueprints/{id}` | Atualizar `config` (merge — ex: brand kit) |
| POST | `/api/v1/blueprints/{id}/assets/agnes-cover` | Capa editorial Agnes Studio (`{slot, style_id}`) |
| POST | `/api/v1/blueprints/{id}/assets/upload` | Upload `{slot, data_url}` |
| POST | `/api/v1/blueprints/{id}/publish` | Publicar no Clube (ponte) |
| DELETE | `/api/v1/blueprints/{id}` | Remover |

> 📖 Guia completo: `docs/blueprint_guia.md` · Demo/E2E: `scripts/blueprint_demo.sh` · Env: `CLUBE_PUBLIC_URL`, `CLUBE_IMPORT_KEY`, `BACKEND_URL`, `CLI_TOKEN`, `AGNES_API_KEY`.

---

## 🎨 Agnes Studio (capas com design editorial — HTML → PNG)

`modules/agnes_studio.py` compõe capas com **design real** (tipografia + autor + créditos + identidade do canal) e renderiza HTML → PNG via **Obscura** (`ObscuraBridge.screenshot`, CDP `Page.captureScreenshot` com `clip` explícito para dimensões exatas), com **fallback local Pillow** para nunca falhar:

- **Capa de curso** 16:9 (1280×720) · **Capa de ebook** livro (1200×1600) · **Imagem de artigo** (1200×630) · **Capa de produto** quadrada (1024×1024, usada no Blueprint)
- 5 estilos determinísticos (`moderno`, `elegante`, `tech`, `minimal`, `dark-gold`); o **design é persistido** no produto (`cover_design`) para que regenerações mantenham a identidade visual
- Salva `{slug}_{uuid}.png` em `outputs/agnes/` e retorna `{cover_url, design}` — a **galeria** (`/api/v1/agnes/gallery`) lista e `use-cover` aplica qualquer versão
- Endpoints: `POST /api/v1/courses/{id}/agnes-cover` · `POST /api/v1/ebooks/{id}/agnes-cover` · `POST /api/v1/blog/post/{id}/agnes-cover` — todos aceitam `{style_id}` e `{brand_kit}` no body (todos `require_admin`)
- **Seletor de estilo na UI**: componente `AgnesCoverButton` (estilo + gerar + preview) nas fábricas de curso/ebook/blog
- **Brand kit global**: componente `BrandKitEditor` (cores + fontes em `localStorage`) nas 3 fábricas — o `AgnesCoverButton` envia o brand kit junto e as capas saem já com a identidade
- **Brand kit na landing**: `modules/landing_templates.py` injeta as cores/fontes do `config.brand_kit` nos blocos publicados (hero, oferta, prova, FAQ, CTA) — landing nasce com a identidade visual
- **Templates de landing variados**: `dezafira` (padrão) · `dark-sales` (escuro, urgência, `compareAtPrice`, badge "Últimas vagas") · `clean-soft` (claro, minimalista, `posts-grid`) — seletor na página de detalhe do Blueprint (`config.template_landing`)
- **Comparador de variantes**: `POST /api/v1/blueprints/{id}/assets/agnes-variants` (gera 5 estilos do slot) e `POST .../agnes-apply-variant` (aplica um deles) — modal lado a lado no `AssetSlot` (`{variant, index}`) com dimensões

## 🎬 Agnes Video (image-to-video — `agnes-video-v2.0`)

A assinatura Agnes inclui **vídeo** além de imagens (`modules/agnes_video.py`, API `https://apihub.agnes-ai.com/v1/videos`):

- **`POST /api/v1/agnes/video`** `{prompt, image, wait}` — `image` aceita URL pública **ou base64/data URL**; `wait=true` faz polling síncrono, baixa o MP4 para `outputs/vsl/` e devolve `local_url`; `wait=false` (padrão) devolve a task para polling via GET
- **`GET /api/v1/agnes/video/{task_id}`** — status da task (a URL final vem em `metadata.url`)
- Vídeo real validado: **5s · h264 1088×832 · 24fps · áudio AAC** — demo da marca Dezafira em `outputs/agnes/dezafira_demo.html` (imagem com fundo Agnes + tipografia CDP e o vídeo gerado a partir dela)
- **No Blueprint** (`config.video.enabled`): o motor gera um **slot `promo_video`** automático por produto — usa a capa (Agnes Studio local → base64, ou remota → URL) como frame inicial, gera o clipe e salva em `outputs/vsl/bp_*_promo.mp4`; o `AssetSlot` renderiza `<video>` (slot marcado `video: true`). Obs.: a API da Agnes retorna **`503 video_queue_full`** quando a fila está cheia — o motor trata como fallback gracioso (`generated: false` sem quebrar o run) e a regeneração do slot pode ser re-tentada depois
- **URLs locais nos slots**: o `AssetSlot` resolve URLs `/outputs/...` contra o `apiBase` do backend (imagens e vídeo) — sem isso o `<video>`/`<img>` quebrava no admin (:3000 não serve /outputs)
- **Na fábrica de VSL**: botão **"🎬 Gerar vídeo IA (Agnes)"** ao lado do render TTS — `POST /api/v1/vsl/{id}/render-agnes-video` (task assíncrona) + `GET /api/v1/vsl/{id}/agnes-video` (polling; ao concluir baixa o MP4 e atualiza `video_url` da VSL, que o player do Clube passa a rodar)
- Scripts: `scripts/agnes_brand_demo.py` (fundo Agnes + tipografia/copy com o branding Dezafira → PNG) e `scripts/agnes_video_demo.py` (imagem → vídeo → MP4)
- **Histórico e diff de assets**: cada regeneração/upload/capa/variante empilha a versão anterior em `assets.slots[].history` (máx. 8); `POST .../assets/restore` restaura uma versão (a atual volta pro histórico) e o `AssetSlot` compara lado a lado (antes × atual)
- **Combo/pacote nativo (fase 2)**: `funil.bundle` no blueprint (desconto %, incluir upsell/downsell) → o motor publica um produto **Pacote** com `bundle_items` (ids dos incluídos) e a landing promove o combo (slug `{slug}-pacote`, **preço riscado** `compareAtPrice` = soma dos itens + CTA dedicado "Quero o pacote completo"); no Clube, a compra do bundle desbloqueia todos os itens (`unlockBundleForUser` nos webhooks Asaas/Stripe), a página do produto lista o conteúdo e o **pós-compra oferece o pacote** (`checkout/obrigado`: reverse lookup `findBundleForProduct` → estágio "Pacote completo" antes do upsell)
- **Fábrica de VSL no blueprint**: `config.vsl.enabled` → o motor gera **script completo + headlines A/B/C** (novo `modules/vsl_factory.py`, LLM + fallback determinístico) com thumbnail da capa do produto; `content.vsl` alimenta o bloco de vídeo da landing e o `youtube_video_url` do produto
- **VSL com TTS e vídeo**: novo `modules/vsl_video.py` — roteiro → **cenas editoriais** (HTML→PNG via Chrome, fallback Pillow) + **narração pt-BR** (`edge-tts`, sem chave) → **MP4** (ffmpeg estático via `imageio-ffmpeg`). `POST /api/v1/vsl/{id}/render-video` + botão 🎬 na fábrica de VSL (player + cenas). Validado: vídeo real 1280×720 h264+aac, 15s
- **Player de VSL na landing**: o Clube **já tem** o `VslPlayer` (bloco `vsl`: vídeo MP4, autoplay mudo, progress bar de neuromarketing, **headlines A/B/C por visitante** e **analytics de retenção** → `POST /api/v1/vsl/analytics`). A geração de landing agora **emite o bloco `vsl`** com `vslId`/`src`/`thumbnail`/`headline_a..c` quando o blueprint tem VSL com MP4 (fallback: iframe do YouTube via `config.youtube_video_url`). A URL do ADM usada pelo player é configurável: `PUBLIC_ADM_API_URL` no `.env` do Clube (default produção)
- **Galeria visual**: página `/admin/agnes` — grid com zoom (dimensões/tamanho), botões **Aplicar** (via `/use-cover`) e 🗑 **remover** (`DELETE /api/v1/agnes/gallery/{filename}`)
- **CI com Chrome**: `.github/workflows/ci.yml` — `pytest` (banco temporário, isolado) + teste CDP real de render com Chrome headless (inclui o teste de render sem falhar quando o Chrome não está disponível)
- **Validação do render real**: `scripts/agnes_studio_render_check.py` sobe um Chrome headless local e valida HTML→PNG de ponta a ponta (validado: capa 1280×720 exata via CDP); também coberto por teste na suíte (`tests/test_agnes_studio_render_cdp.py`, pula sem Chrome)

> ⚠️ Requer `pillow` (no `requirements.txt`). Com `OBSCURA_ENABLED=false` (padrão local) as capas saem pelo fallback Pillow; com o Chrome/Obscura no ar, saem pelo render HTML real (tipografia/fontes).

---

## 🧪 Testes (isolados do banco real)

`tests/conftest.py` define `DATABASE_URL` para um **SQLite temporário** (`tests/.pytest_state/`, gitignored) ANTES de qualquer import — nenhum teste toca/polui o `dezafira.db` real (validado: 0 registros residuais). Requer `server.py` com `load_dotenv(override=False)` (variáveis de ambiente do usuário têm prioridade sobre `.env`).

```bash
.venv/Scripts/python -m pytest tests/ -q --timeout=120 --ignore=tests/test_hermes_pipeline.py
```

E2E do combo/pacote no Clube (sobe o SvelteKit com DB isolado, importa itens +
pacote via HTTP, simula o webhook Asaas e confere o desbloqueio):

```bash
bash scripts/clube_combo_e2e.sh
```

> O shell não tem `node` no PATH — use o Node portátil do projeto
> (`.tools/node/node-v22.23.2-win-x64/`, gitignored):
> `export PATH="$(pwd)/.tools/node/node-v22.23.2-win-x64:$PATH"`
> (o E2E já faz isso sozinho). O v22 é o que casa com o `better-sqlite3` do Clube.

> `test_hermes_pipeline` e `test_obscura_telemetry_sources` chamam LLM/SERP reais — rodam só com chaves configuradas (ambientais).

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
| **Cascata LLM unificada** | `agents/llm.py` agora é a ÚNICA fonte da verdade: **Agnes AI (agnes-2.5-flash, IA OFICIAL) → OpenRouter → Gemini → NVIDIA NIM → HuggingFace → DeepSeek**. `blog_writer._call_llm` virou delegador fino (mesma assinatura, mantém `RuntimeError` em falha total para os fallbacks por seção); o `query_llm` só-NVIDIA do `server.py` foi removido (usa o `agents.llm`). ~500 linhas de duplicação eliminadas |
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
│   ├── image_factory.py       # Geração de imagens (Agnes → Gemini → FLUX → Pexels → SVG)
│   ├── agnes_studio.py        # 🎨 Capas com design real (HTML → PNG via Obscura/Pillow)
│   ├── blueprint_engine.py    # Motor do Blueprint de Produto (6 estágios + publicação)
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
├── Versões do dezafiraClub/
│   └── Blog_Inteligente_SEO_com_IA_-_v1.9/  # 🟢 DezafiraClube (SvelteKit) — site público + membros (v1.8 preservado como backup)
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
- [x] **🎯 Blueprint de Produto** — receita tema+nicho gera produto, blog/banners, landing, funil e área de membros com revisão de imagens (super prompt + upload + zoom) e publicação via ponte; **Agnes AI** = IA oficial de imagens (provedor #0) — `docs/blueprint_guia.md`

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
