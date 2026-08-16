# 🎯 Blueprint de Produto — Plano de Implementação

> **Objetivo:** criar no DezafiraAdm uma página **Blueprint** que substitui a atual *Fábrica de Produtos*: a partir de **tema + nicho + preço**, a IA gera AUTOMATICAMENTE todos os artefatos de um produto, o usuário revisa visualmente cada imagem (super prompt + upload + zoom) e a **ponte** publica tudo no DezafiraClube com status por etapa.
>
> **Status:** ✅ **IMPLEMENTADO (F1–F6)** — F2, F3, F4, F5 e F6 concluídos com testes (88 passando). Guia de uso: `docs/blueprint_guia.md` · Demo/E2E: `scripts/blueprint_demo.sh`
> Combo/Pacote nativo → **fase 2** · Landing: blocos prontos do Clube + registry extensível · IA oficial de imagens: **Agnes AI** (provedor #0)

---

## 1. Conceito

**Blueprint = receita de produto.** Uma entidade que orquestra a geração de:

| Artefato | Onde vive | Como nasce |
|---|---|---|
| 📦 Produto (catálogo) | Clube (`products`) | Ponte `/api/import/product` |
| 📝 Blog + artigos | Clube (`posts`, `post_products`) | Ponte `/api/import/sync-blog` (generalizada) |
| 🖼️ Banners de artigo | Clube (`ads`: sidebar/inline) | Ponte `/api/import/sync-blog` (generalizada) |
| 🚀 Landing page | Clube (`landing_pages` → `/p/{slug}`) | CLI API existente (`/api/cli/landing-pages`) |
| 🛒 Funil | Clube (`products.*`) | Campos da ponte (bump + upsell + downsell) |
| 🔒 Área de membros | Clube (`member_courses/lessons`) | Novo `/api/import/member-course` |
| 📱 MiniApp / entregável | Adm (`miniapps`/`mindmaps`/`books`) | Pipelines existentes (link de entrega) |
| 🎨 Todos os assets de imagem | Blueprint (Adm) | Agnes AI → cascata, com **super prompt** |

**Fluxo:** `Criar receita → IA gera rascunho completo → Revisão visual (assets) → Publicar no Clube`

---

## 2. Arquitetura

```
club-frontend (Next.js 14)              Backend Adm (FastAPI)                    DezafiraClube (SvelteKit v1.9)
┌───────────────────────────┐          ┌──────────────────────────────┐          ┌──────────────────────────────┐
│ /admin/blueprint          │  /api/v1 │ blueprint_engine.py          │  ponte   │ /api/import/product         │
│  • criar receita          │ ────────▶│  • tabela blueprints (DB)    │ ────────▶│ /api/import/sync-blog (gen) │
│  • estágios + progresso   │          │  • 6 estágios do motor       │          │ /api/import/member-course   │
│  • AssetSlot (revisão)    │          │  • template_registry         │  CLI     │ /api/cli/landing-pages      │
│  • publicar + status      │          │  • orquestrador de publicação│ ────────▶│ /api/cli/posts · /api/cli/  │
└───────────────────────────┘          └──────────────────────────────┘          │  upload (Cloudinary)         │
                                                                                 └──────────────────────────────┘
```

Decisões-chave:
- **Landing:** o Adm monta os blocos (mesmo formato que o Clube já valida em `landing-blocks.ts`) e publica via CLI API com `CLI_TOKEN` — **zero mudança no Clube** para landing.
- **Funil:** os produtos-filhos (upsell/downsell) são criados **primeiro**, para que a ponte do produto principal já receba `upsell_product_id`/`downsell_product_id` válidos (evita endpoint de update no Clube no MVP).
- **Assets:** todas as imagens nascem com `{url, super_prompt, provider, source, width, height}` persistidos no blueprint — o super prompt é o `expanded_prompt` que o `ImageGeneratorAgent` já retorna.

---

## 3. Dados (Adm)

### 3.1 Nova tabela `blueprints` (SQLAlchemy)

| campo | tipo | descrição |
|---|---|---|
| `id` | str (uuid) | chave |
| `name` | str | nome interno do blueprint |
| `theme` | str | tema/título do produto |
| `niche` | str | nicho |
| `price_cents` | int | preço |
| `formats` | JSON | `["ebook","curso","app","blog"]` |
| `status` | str | `draft │ generating │ review │ publishing │ published │ failed` |
| `stage` | str | estágio atual do motor |
| `config` | JSON | receita completa (parâmetros por formato, nº de artigos, template de landing, CTA…) |
| `content` | JSON | artefatos gerados: produto, posts, blocks da landing, funil, membros, miniapp |
| `assets` | JSON | `{ slot_key: {url, super_prompt, provider, source, width, height} }` |
| `publish_log` | JSON | `{ etapa: {status, detail, ts} }` |
| `created_at` / `updated_at` | datetime | — |

### 3.2 Slots de asset padronizados

| slot | uso | dim. gerada (Agnes tier/ratio) |
|---|---|---|
| `product_image` | capa do produto no catálogo | 2K 1:1 |
| `blog_banner_sidebar` | ad sidebar do blog | 1K 1:1 |
| `blog_banner_inline` | ad inline dos posts | 2K 16:9 |
| `post_cover_i` | capa de cada artigo (nº artigos) | 2K 16:9 |
| `landing_hero` | hero da landing | 2K 16:9 |
| `landing_offer` | bloco de oferta | 2K 16:9 |
| `upsell_image` / `downsell_image` | ofertas da esteira | 2K 16:9 |
| `member_cover` | capa do curso na área de membros | 2K 16:9 |
| `miniapp_logo` | logo do MiniApp | 1K 1:1 |

> Cada slot tem `source: "ai" │ "upload"` — o AssetSlot controla isso.

---

## 4. Motor — `modules/blueprint_engine.py`

```
Estágio 0 · FUNDAÇÃO      LLM (agents/llm.py): nome, slug, descrição, proposta de valor,
                          persona, CTAs, pitch → config/content
Estágio 1 · CONTEÚDO      Dispara pipelines EXISTENTES por formato:
                          ebook_pipeline · course_pipeline · mindmap/miniapp_factory ·
                          blog_pipeline (artigos) → coleta external_link + metadados
Estágio 2 · ASSETS        Por slot: super prompt (_expand_prompt_with_llm) + imagem
                          (Agnes → Gemini → FLUX → Pexels → Unsplash → SVG) em paralelo
                          (asyncio.gather, timeout por chamada) → assets[]
Estágio 3 · LANDING       Monta blocks via template_registry + resources reais do
                          blueprint (produto/posts) → content.landing_blocks (draft)
Estágio 4 · FUNIL         Define bump (extra_service_*) e filhos upsell/downsell
                          (produtos do próprio blueprint ou catálogo existente)
Estágio 5 · REVISÃO       status=review — UI mostra todos os slots (AssetSlot)
Estágio 6 · PUBLICAÇÃO    Orquestrador da ponte (seção 7)
```

Regras:
- **Idempotência:** cada estágio pode ser re-executado; assets regenerados sobrescrevem o slot.
- **Resiliência:** falha num slot não derruba o motor (placeholder SVG + aviso).
- **Paralelismo:** geração de imagens em lotes paralelos (respeitando limites da API).

---

## 5. Landing templates — `modules/landing_templates.py`

**Registry** no Adm: `{ nome_do_template: [factory_de_bloco, ...] }` — mesmas formas que o Clube aceita (`LANDING_BLOCK_TYPES`: hero, product-showcase, posts-grid, pricing, faq, cta, trust-bar, video…).

Template padrão **"Dezafira"** (MVP):
```
hero (título + CTA → /product/{slug})
product-showcase (produto real do blueprint)
video (youtube_video_url do produto, se houver)
posts-grid (posts do blueprint, até 6)
faq (3-5 perguntas geradas na fundação)
cta (botão → checkout do produto)
```

- Novo template = nova entrada no registry (sem tocar no Clube).
- Publicação via CLI: `POST /api/cli/landing-pages` com `{title, slug, status, blocks}` → `public_url: /p/{slug}`.

---

## 6. Ofertas

### MVP (sem mudança no Clube)
- **Order bump:** `has_extra_service + extra_service_title/price/description` (já suportado pela ponte).
- **Esteira:** `upsell_product_id` / `downsell_product_id` apontando para produtos do catálogo (já suportado). Fluxo de criação: **filhos primeiro → principal depois** (ids conhecidos na criação).

### Fase 2 (fora deste escopo)
- **Combo/Pacote nativo:** tabela `bundles` no Clube + checkout agregado + área de membros agregada.

---

## 7. Publicação — orquestrador (etapa 6)

Ordem executada pelo Adm com `publish_log` por etapa:

| # | Ação | Endpoint | Origem |
|---|---|---|---|
| 1 | Criar produtos-filhos (upsell/downsell/bump) | `POST /api/v1/clube/import-product` ×N | Adm → Clube |
| 2 | Criar produto principal (com todos os campos: `youtube_video_url`, `category`, bump, upsell, downsell, `image_url`) | `POST /api/v1/clube/import-product` | Adm → Clube |
| 3 | Criar posts + banners + vínculo `post_products` | `POST /api/import/sync-blog` (generalizada) | Adm → Clube |
| 4 | Criar/publicar landing | `POST /api/cli/landing-pages` (Bearer `CLI_TOKEN`) | Adm → Clube |
| 5 | Criar área de membros (se curso) | `POST /api/import/member-course` | Adm → Clube |

Cada etapa retorna `{status, detail}`; falha não bloqueia as demais (marcadas como pendentes/manuais).

---

## 8. Endpoints novos (Adm — todos `require_admin`)

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/blueprints` | Criar blueprint (draft) |
| GET | `/api/v1/blueprints` | Listar |
| GET | `/api/v1/blueprints/{id}` | Estado completo (config, content, assets, stage, publish_log) |
| POST | `/api/v1/blueprints/{id}/run` | Disparar motor (estágios 0-5) — retorna task_id p/ polling |
| POST | `/api/v1/blueprints/{id}/assets/{slot}/regenerate` | Regenerar imagem (nova seed) |
| POST | `/api/v1/blueprints/{id}/assets/{slot}/upload` | Upload manual (multipart → `modules/uploader.py`) |
| POST | `/api/v1/blueprints/{id}/publish` | Executar etapa 6 (ponte) |

---

## 9. Mudanças no DezafiraClube

| Arquivo | Mudança |
|---|---|
| `src/routes/api/import/sync-blog/+server.ts` | **Generalizar:** aceitar payload `{product_slug, posts:[{title, slug, content, excerpt, cover_image, tags, youtube_video_url}], ads:[{name, placement, type, image_url, link_url, weight}]}`. Backward compatible (sem body = comportamento atual). |
| `src/routes/api/import/member-course/+server.ts` | **Novo:** cria `member_courses` + `member_lessons` (content/video_url/video_type/topic/is_preview). Mesma auth `x-import-key` dos demais. |
| `src/routes/api/import/product/+server.ts` | Sem mudança (já aceita todos os campos). |

> Landing, posts (CLI) e upload já existem — sem mudança.

---

## 10. UI — `club-frontend/app/admin/blueprint/`

Substitui a Fábrica de Produtos:
- **Nova rota** `/admin/blueprint` + link no layout do admin.
- `fabrica-produtos` vira stub que redireciona (padrão já usado em `auth/register`).

### Telas
1. **Criar receita:** tema, nicho, preço, formatos (ebook/curso/app/blog), nº de artigos, template de landing, CTA.
2. **Acompanhamento:** progresso por estágio (polling de task, como o atual) + logs.
3. **Revisão de assets:** grade de slots com `AssetSlot`.
4. **Publicação:** botão 🚀 Publicar + status por etapa (`publish_log`).

### Componente `AssetSlot` (reutilizável)
- Miniatura da imagem (provedor no badge: 🎨 Agnes / Gemini / FLUX…).
- **Clique na miniatura → modal com a imagem em tamanho real + dimensões (W×H)** para avaliar qualidade.
- **Super prompt** ao lado (botão 📋 copiar).
- Botões: 🔄 **Regenerar** (nova seed) · 📤 **Upload** (arquivo local → URL salva no slot).

---

## 11. Ordem de execução (fases com testes)

| Fase | Escopo | Verificação |
|---|---|---|
| **F1** | Backend Adm: tabela `blueprints` + CRUD + `run` (esqueleto) | `pytest` básico de CRUD; `py_compile` |
| **F2** | Motor: estágios 0-4 (fundação, conteúdo, assets, landing blocks, funil) | testes unitários do engine com LLM mockado |
| **F3** | Clube: generalizar `sync-blog` + novo `member-course` | testes com `TestClient` + curl contra ponte |
| **F4** | UI: página `/admin/blueprint` + `AssetSlot` | `next build` / lint |
| **F5** | Publicação: orquestrador etapa 6 + `publish_log` | E2E sandbox: blueprint → Clube real (draft) |
| **F6** | E2E completo: receita → revisão → publicar → conferir no Clube | script `.e2e_blueprint.sh` (padrão dos `.e2e_*.sh`) |

Dependência: criar `.venv` e instalar `requirements.txt` para rodar testes locais (Python global sem `httpx`).

---

## 12. Fora de escopo (fase 2)

- Combo/Pacote nativo (`bundles`)
- Novos templates de landing (infra pronta; conteúdo depois)
- Configuração real do Asaas (créditos de pagamento)
- Google Search Console / AdSense / indexação

---

## 13. Riscos & mitigação

| Risco | Mitigação |
|---|---|
| `sync-blog` atual é hardcoded (posts de `articles_export.json` + produto `movimento-1convite`) | Generalizar mantendo o comportamento atual quando sem payload |
| N imagens em sequência é lento (Agnes ~10-60s) | Paralelismo com `asyncio.gather` + timeout; regeneração sob demanda |
| Dependências Python não instaladas localmente | Criar `.venv` no projeto (pedir permissão) |
| CLI_TOKEN do Clube (hash+expiração v1.9) pode expirar | Regerar em `admin/cli` do Clube e setar `CLI_TOKEN` no Adm |
| Mudanças pendentes já existentes no workspace (server.py, modules/database.py, club-frontend) | Não sobrescrever; trabalhar por cima, diffs por arquivo |

---

*Plano Blueprint Dezafira — Agosto 2026*
