# 🎯 Blueprint de Produto — Guia Completo (v1)

> **O que é:** receita de produto. **Tema + nicho + preço** → a IA gera TODOS os
> artefatos de venda (produto no catálogo, blog + banners, landing page, funil
> bump/upsell/downsell, área de membros) e a **ponte** publica tudo no
> DezafiraClube — com revisão visual de cada imagem antes de publicar.
>
> **Status:** ✅ implementado (F1–F6) · Combo/Pacote nativo → fase 2
> **IA de imagens:** Agnes AI (provedor #0 da cascata — `apihub.agnes-ai.com`)

---

## 1. Fluxo de uso (UI)

1. **Criar receita** (`/admin/blueprint`): tema, nicho, preço, formatos
   (📗 Ebook · 🎓 Curso · 📱 MiniApp/Mapa · ✍️ Blog), nº de artigos e (opcional)
   esteira de ofertas (upsell + downsell).
2. **Gerar** (automático ao abrir o blueprint): o motor roda 6 estágios —
   Fundação → Conteúdo → Assets → Landing → Funil → Revisão. A UI mostra o
   progresso por estágio (polling de 3s).
3. **Revisar assets** (`/admin/blueprint/{id}`): cada imagem aparece num
   **AssetSlot** — miniatura → clique abre **modal em tamanho real com
   dimensões (W×H)** + provedor (🎨 Agnes / Gemini / FLUX…). Ao lado, o
   **super prompt** (copiável) e os botões **🔄 Regenerar** (nova seed) e
   **📤 Upload** (sua imagem substitui a gerada).
4. **Publicar** → botão 🚀 Publicar no Clube. O orquestrador roda a ponte em
   sequência e mostra o status por etapa (produto → blog/banners → landing →
   membros) em `publish_log`.

## 2. Arquitetura

```
club-frontend (/admin/blueprint)      Backend Adm (FastAPI)                  DezafiraClube (SvelteKit v1.9)
┌──────────────────────────────┐     ┌─────────────────────────────┐       ┌───────────────────────────────┐
│ BlueprintPage                │     │ modules/blueprint_engine.py │ ponte │ /api/import/product          │
│ BlueprintDetailPage          │────▶│  6 estágios + publicação    │──────▶│ /api/import/sync-blog (gen.) │
│ components/AssetSlot.tsx     │     │ modules/landing_templates.py│       │ /api/import/member-course    │
└──────────────────────────────┘     │ modules/clube_bridge.py     │ CLI   │ /api/cli/landing-pages       │
                                     └─────────────────────────────┘ ─────▶│ (Bearer CLI_TOKEN)           │
                                                                          └───────────────────────────────┘
```

### Arquivos novos / alterados

| Arquivo | Papel |
|---|---|
| `modules/blueprint_engine.py` | **Motor**: 6 estágios + orquestrador de publicação + assets (regenerar/upload) |
| `modules/landing_templates.py` | Registry de templates de landing (blocos no formato do Clube) — `dezafira` · `dark-sales` · `clean-soft` com brand kit injetado |
| `modules/vsl_factory.py` | 🎬 **VSL Factory** — script completo + headlines A/B/C (LLM + fallback determinístico), usado pela fábrica e pelo Blueprint |
| `modules/vsl_video.py` | 🎥 **VSL Video** — roteiro → cenas editoriais (Chrome CDP/Pillow) + narração TTS (`edge-tts`) → MP4 (ffmpeg via `imageio-ffmpeg`) |
| `scripts/clube_combo_e2e.sh` | 🔬 **E2E do combo no Clube** (sobe o SvelteKit com DB isolado, importa itens+pacote, simula webhook Asaas, confere desbloqueio) |
| `modules/clube_bridge.py` | Camada única da ponte Adm→Clube (`import-product`, `sync-blog`, `member-course`, CLI landing) |
| `modules/database.py` | Modelo `Blueprint` (tabela `blueprints`) + CRUD |
| `server.py` | Endpoints `/api/v1/blueprints*` |
| `club-frontend/app/admin/blueprint/` | Página do Blueprint (criar/listar + detalhe) |
| `club-frontend/components/AssetSlot.tsx` | Componente de imagem (zoom + super prompt + regenerar + upload) |
| `club-frontend/app/admin/fabrica-produtos/page.tsx` | Stub que redireciona para `/admin/blueprint` |
| Clube: `src/routes/api/import/sync-blog/+server.ts` | **Generalizado**: aceita payload `{product_slug, posts, ads}` (legado mantido) |
| Clube: `src/routes/api/import/member-course/+server.ts` | **Novo**: cria curso + aulas na área de membros |
| `modules/image_factory.py` | **Agnes AI = provedor #0** da cascata (com super prompt) |
| `modules/agnes_studio.py` | 🎨 **Agnes Studio** — capas com design editorial (HTML → PNG via Obscura `screenshot`, fallback Pillow) + **`generate_product_cover`** (1024×1024 p/ slot `product_image`) |
| `services/obscura_bridge.py` | Método `screenshot()` (CDP `Page.captureScreenshot` + `Emulation.setDeviceMetricsOverride` + **`clip` explícito** p/ dimensões exatas) |
| `modules/blueprint_engine.py` | `generate_agnes_cover_asset(bp_id, slot, style_id)` + slot automático **`product_image_agnes`** (agnes_only) no estágio assets; `brand_kit` do config nas capas |
| `club-frontend/components/AgnesCoverButton.tsx` | Seletor de estilo + gerar + preview (usado em fabrica-curso/ebook/blog) — envia o **brand kit** do `localStorage` junto |
| `club-frontend/components/BrandKitEditor.tsx` | **Brand kit global** (cores + fontes, `localStorage`) — compartilhado pelas 3 fábricas |
| `club-frontend/components/AssetSlot.tsx` | Botão 🖌️ **Capa Agnes** + seletor de estilo + **comparador de variantes** ao lado de Regenerar/Upload |
| `.github/workflows/ci.yml` | **CI**: `pytest` (banco temporário isolado) + teste CDP real de render com Chrome headless |
| `club-frontend/app/admin/agnes/` | 🖼️ **Galeria visual** de capas (grid + zoom + aplicar + remover) — link no sidebar |
| `scripts/agnes_studio_render_check.py` | Valida o render HTML→PNG **real** (Chrome headless local via CDP) |
| `tests/test_agnes_studio_render_cdp.py` | Teste CDP na suíte (pula sem Chrome) |
| `tests/conftest.py` | **Isolamento**: `DATABASE_URL` → SQLite temporário (`tests/.pytest_state/`) antes de qualquer import |
| `tests/test_agnes_studio.py` | 18 testes do Agnes Studio (design, slugs, HTML, geração, fallback Pillow, `style_id`, E2E da galeria, endpoint HTTP do Blueprint) |
| `requirements.txt` | `pillow` (fallback local do Agnes Studio) |
| `.env` / `.env.example` | `AGNES_API_KEY` (+ `CLI_TOKEN` documentado) |

## 3. Modelo de dados (Adm — tabela `blueprints`)

| campo | tipo | descrição |
|---|---|---|
| `id` | str (`bp_…`) | chave |
| `name`, `theme`, `niche`, `price_cents` | — | receita |
| `formats` | JSON | `["ebook","curso","app","blog"]` |
| `status` | str | `draft │ generating │ review │ publishing │ published │ failed` |
| `stage` | str | `fundacao │ conteudo │ assets │ landing │ funil │ revisao │ publicacao` |
| `config` | JSON | parâmetros por formato + `funil` + `template_landing` |
| `content` | JSON | `fundacao` (nome/slug/copy/faq), `conteudo.artifacts`, `assets.slots`, `landing.blocks`, `funil` |
| `assets` | JSON | `slot_key → {url, super_prompt, provider, source: ai|upload, width, height}` |
| `publish_log` | JSON | `etapa → {status, detail, ts}` |
| `error` | str | último erro |

### Slots de imagem (gerados pela Agnes)

| slot | dim. pedida | quando |
|---|---|---|
| `product_image` | 1024×1024 | sempre |
| `landing_hero` / `landing_offer` | 1200×630 | sempre |
| `blog_banner_sidebar` | 600×600 | formato `blog` |
| `blog_banner_inline` | 1200×630 | formato `blog` |
| `post_cover_{i}` | 1200×630 | 1 por artigo do blog (máx 6) |
| `member_cover` | 1280×720 | formato `curso` |
| `miniapp_logo` | 1024×1024 | formato `app` (miniapp) |
| `upsell_image` / `downsell_image` | 1200×630 | esteira configurada |

> O **super prompt** é o `expanded_prompt` do `ImageGeneratorAgent`
> (DeepSeek → Gemini LLM). Upload manual (`source: "upload"`) nunca é
> sobrescrito pelo motor.

## 4. Estágios do motor (`run_blueprint`)

| Estágio | O que faz |
|---|---|
| **0 · fundacao** | LLM cascade (`agents/llm.py`) gera name/slug/descrição/pitch/CTAs/FAQ; fallback determinístico se a LLM falhar |
| **1 · conteudo** | Dispara as pipelines existentes por formato: `ebook_pipeline`, `course_pipeline`, `mindmap_pipeline`/`miniapp_factory`, `blog_pipeline`; coleta `artifacts` (id, título, capa, `external_link` de entrega) |
| **2 · assets** | Gera cada slot via Agnes AI (→ Gemini → FLUX → Pexels → Unsplash → SVG) em lotes paralelos; persiste `{url, super_prompt, provider, source}`. Slots **agnes_only** (ex: `product_image_agnes`) saem **automaticamente** pela capa editorial do Agnes Studio (fora do lote, escrita sequencial). **Alternativa manual**: 🖌️ Capa Agnes por slot via `generate_agnes_cover_asset` — provider `agnes-studio` + `agnes_style`. Cores/fontes customizadas via **`config.brand_kit`**. **Variantes**: `generate_agnes_variants(bp_id, slot)` gera os 5 estilos do slot; `apply_agnes_variant` aplica um deles (mantém o estilo escolhido nas regenerações) |
| **3 · landing** | Monta os blocos do template (`landing_templates.py` — `dezafira` · `dark-sales` · `clean-soft`, selecionado por `config.template_landing`) no formato que o Clube valida — **injeta as cores/fontes do `config.brand_kit`** nos `styles`; se o **combo** estiver habilitado, a landing promove o pacote (slug `{slug}-pacote`, preço agregado com desconto); se a **VSL** tiver `video_url` **+ `vsl_id`**, emite o **bloco nativo `vsl`** do Clube (`vslId`/`src`/`thumbnail`/`headline_a..c` → player com A/B/C e analytics); sem MP4, cai pro iframe do YouTube (`config.youtube_video_url`) |
| **4 · funil** | Normaliza order bump + upsell/downsell + **combo/pacote** (`funil.bundle`: enabled, discount_pct 0–90, include_upsell/downsell, slug determinístico) |
| **2b · VSL** | Se `config.vsl.enabled` → `_stage_vsl` gera script + headlines (thumbnail = capa do produto); `content.vsl` alimenta o bloco `vsl` da landing (MP4) ou o `video` (YouTube) |
| **3 · landing (combo)** | Combo habilitado → landing promove o pacote: slug `{slug}-pacote`, preço com desconto, **`compareAtPrice` riscado** (soma dos itens) e CTA dedicado "Quero o pacote completo" |
| **5 · revisao** | `status=review` — UI mostra os AssetSlots |

## 5. Publicação (`publish_blueprint`) — ordem da ponte

| # | Etapa | Endpoint | Observação |
|---|---|---|---|
| 1 | Filhos da esteira (upsell/downsell) | `POST /api/import/product` | **criados primeiro** para a ponte receber os ids |
| 2 | Produto principal | `POST /api/import/product` | com `youtube_video_url`, `category`, bump, `upsell_product_id`, `downsell_product_id`, `image_url` |
| 3 | Blog + banners | `POST /api/import/sync-blog` | payload `{product_slug, posts, ads}` (generalizado) |
| 4 | Landing | `POST /api/cli/landing-pages` | `Authorization: Bearer CLI_TOKEN` |
| 5 | Área de membros (curso) | `POST /api/import/member-course` | `member_courses` + `member_lessons` |
| 2b | **Combo/pacote** (se `funil.bundle.enabled`) | `POST /api/import/product` | produto **Pacote** com `bundle_items` (ids do principal + upsell + downsell), preço = soma × (1 − desconto), slug `{slug}-pacote` |

- Cada etapa registra `{status, detail, ts}` em `publish_log` — falha numa etapa
  **não bloqueia** as demais.
- Falha no produto principal → blueprint `failed`.

## 6. Endpoints (Adm — `require_admin`)

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/blueprints` | Criar receita (draft) |
| GET | `/api/v1/blueprints` | Listar |
| GET | `/api/v1/blueprints/{id}` | Estado completo (inclui task em memória) |
| POST | `/api/v1/blueprints/{id}/run` | Disparar o motor (0–5) em background |
| DELETE | `/api/v1/blueprints/{id}` | Remover |
| PATCH | `/api/v1/blueprints/{id}` | Atualizar `config` (merge parcial — ex: `brand_kit`) |
| POST | `/api/v1/blueprints/{id}/assets/regenerate` | Regenerar slot `{slot}` (nova seed) |
| POST | `/api/v1/blueprints/{id}/assets/agnes-cover` | 🖌️ Capa **editorial** via Agnes Studio `{slot, style_id}` (alternativa à imagem por prompt; provider `agnes-studio` + `agnes_style` persistidos) |
| POST | `/api/v1/blueprints/{id}/assets/agnes-variants` | ⚖️ Gerar 5 variantes de estilo do slot `{slot}` (retorna lista com urls + dimensões) |
| POST | `/api/v1/blueprints/{id}/assets/agnes-apply-variant` | Aplicar variante `{slot, variant, index}` (persiste `agnes_style` do escolhido) |
| POST | `/api/v1/blueprints/{id}/assets/upload` | Upload `{slot, data_url}` (base64) → salva em `outputs/blueprints/{id}/` |
| POST | `/api/v1/blueprints/{id}/assets/restore` | 🕘 Restaurar versão do histórico `{slot, index}` (a atual volta pro histórico) |
| POST | `/api/v1/blueprints/{id}/publish` | Executar a ponte (estágio 6) |

> Rota do asset usa **body** (`{slot}`), não path param.

## 7. Bridge / Clube (mudanças)

### `POST /api/import/sync-blog` — agora com 2 modos
- **Modo blueprint** (com body): `{product_slug, posts:[{title, slug, content, excerpt, cover_image, tags, youtube_video_url, published}], ads:[{name, placement, type, image_url, link_url, weight}], category?}` → cria posts (skip por slug), vincula `post_products`, cria categorias e banners (idempotente por nome).
- **Modo legado** (sem body): comportamento original (`articles_export.json` + banners fixos).

### `POST /api/import/member-course` (novo)
`{title, slug?, description?, cover_image?, price_cents?, published?, lessons:[{title, content?, video_url?, video_type?, topic?, is_preview?, sort_order?}]}` → cria `member_courses` + `member_lessons`. Auth: `x-import-key`.

## 8. Variáveis de ambiente

| Variável | Onde | Uso |
|---|---|---|
| `AGNES_API_KEY` | Adm | IA oficial de imagens (`agnes-image-2.1-flash`) — **provedor #0** |
| `CLUBE_IMPORT_KEY` | Adm | chave da ponte (== `IMPORT_API_KEY` do Clube) |
| `CLUBE_PUBLIC_URL` | Adm | URL pública do Clube |
| `BACKEND_URL` | Adm | base dos links de entrega (`/curso/{id}`, `/miniapps/{id}/view`, `/mindmap/{id}`) |
| `CLI_TOKEN` | Adm | token da CLI do Clube (Admin → CLI & API) — usado na publicação da landing |
| `IMPORT_API_KEY` | Clube | espelho de `CLUBE_IMPORT_KEY` |

## 9. Testes

> 🔒 **Isolamento do banco real**: `tests/conftest.py` define `DATABASE_URL` para
> um SQLite temporário (`tests/.pytest_state/`, gitignored) **antes** de qualquer
> import — nenhum teste toca/polui o `dezafira.db`. Requer `server.py` com
> `load_dotenv(override=False)` (já aplicado).

```
.venv/Scripts/python -m pytest tests/ -q --timeout=120 --ignore=tests/test_hermes_pipeline.py
```

- `test_blueprints.py` — CRUD + fluxo do motor até `review` (pipelines/LLM/imagens mockados).
- `test_blueprint_engine.py` — fundação LLM (com fallback), conteúdo, assets (super prompt persistido), landing (blocos), funil e fluxo completo.
- `test_clube_bridge.py` — publicação: filhos primeiro → principal com ids, blog, landing e membros; caminho de falha.
- `test_agnes_studio.py` — design determinístico, slugs da galeria, HTML com escape, geração das capas (course/book/blog/product), fallback Pillow, `style_id` + **`brand_kit`** no body, **E2E da galeria** (capa real em `outputs/agnes` → `/gallery` → `/use-cover`), **endpoint de capa Agnes do Blueprint** (JWT + persistência) e **variantes** (5 estilos gerados + aplicar).
- `test_blueprint_engine.py` — inclui `generate_agnes_cover_asset` (mapeamento de slot, estilo persistido, fallback de estilo inválido → moderno), o estágio assets gerando o slot `agnes_only`, a **landing com brand kit** (cores/fontes injetadas), **combo/pacote** (funil + landing promovendo o bundle + publish criando o pacote), **templates variados** (dark-sales/clean-soft), **histórico/restore de assets** (empilha versões, restaura) e o **estágio de VSL**.
- `test_vsl_factory.py` — 4 testes do VSL Factory (fallback determinístico, LLM, erro/lixo → fallback, persistência do registro).
- `test_vsl_video.py` — 6 testes do VSL Video (divisão de cenas, cap de 8, fallback Pillow com dimensões, vídeo sem TTS com ffmpeg real, degradação sem ffmpeg).
- Landing VSL — `test_blueprint_engine.py`: bloco `vsl` emitido com `vslId`/`src`/`thumbnail`/`headline_a..c` quando há MP4 (sem iframe YouTube) e fallback pro bloco `video` quando a VSL não tem vídeo renderizado.
- `scripts/clube_combo_e2e.sh` — **E2E real do combo no Clube** (9 checks): import de itens + pacote via HTTP, `bundle_items` persistidos, bundle com item inexistente → 400, webhook Asaas → compra completed + itens desbloqueados, página pública do pacote → 200. Requer o Node portátil (`.tools/node/node-v22.23.2-win-x64/`).
- `test_agnes_studio_render_cdp.py` — render **real** HTML→PNG via Chrome headless (CDP): screenshot com clip (dimensões exatas) + capa real do studio; **pula automaticamente** sem Chrome (`CHROME_PATH`).

### CI com Chrome (GitHub Actions)

`.github/workflows/ci.yml` roda na PR/push: instala Python + Chrome headless,
roda a suíte `pytest` (banco temporário isolado — nunca toca `dezafira.db`) e
valida o teste CDP de render real. Sem Chrome o teste de render pula (não
falha) — no CI o Chrome está sempre presente, então o caminho real é coberto.

> ⚠️ Pipelines reais (ebook/curso/blog) e a geração de imagem **não rodam nos
> testes** — são mockados. Para um teste E2E real, use `scripts/blueprint_demo.sh`
> com o backend local e a ponte configurada.

### Render real HTML → PNG (Chrome via CDP)

```
.venv/Scripts/python scripts/agnes_studio_render_check.py
```

Sobe um Chrome headless local (`--remote-debugging-port=9333`, `CHROME_PATH`
para outro executável), valida o screenshot CDP (dimensões exatas via `clip`)
e gera uma capa real do Agnes Studio de ponta a ponta, conferindo o PNG.
Remova a capa de teste ao final. Requer `OBSCURA_PORT` apontando pro Chrome
(o script já faz isso) — sem Chrome, as capas saem pelo fallback Pillow.

### Smoke test HTTP real

```
bash scripts/blueprint_smoke_test.sh
```

Sobe o servidor local (porta 8765), cria um admin de teste + JWT direto no banco
local, exercita o CRUD completo via HTTP (401 sem token → create → list → get →
delete) e **limpa tudo no final** (usuário + blueprint). Detalhes importantes:

- O `server.py` usa `load_dotenv(override=False)`: variáveis de ambiente do
  usuário (ex: `DATABASE_URL` de teste) têm prioridade sobre o `.env`. O script
  usa o banco local e limpa os registros de teste.
- O seed silencia o stdout porque `modules.database` imprime ruído de migrations
  no **stdout** (não stderr) — sem isso o bash captura lixo como "token".
- Payloads usam apenas ASCII para evitar corromper o JSON com a codificação do
  terminal Windows (cp1252) durante o curl.

## 10. Fora de escopo (fase 2)

- **Combo/Pacote nativo** (`bundles` no Clube + checkout agregado) — MVP usa
  order bump + upsell/downsell.
- Novos templates de landing (infra pronta em `landing_templates.py`).
- Configuração real do Asaas.
