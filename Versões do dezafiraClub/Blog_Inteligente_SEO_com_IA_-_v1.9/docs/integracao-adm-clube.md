# 🔗 Integração DezafiraAdm → DezafiraClube (v1.9)

Como o backend Adm (fábricas + Hermes) alimenta o DezafiraClube sem recriar
nada: ponte de importação, player de curso, funil de vendas, nurturing e o
novo fluxo de **landing pages via CLI**.

> **Pacote:** `Blog_Inteligente_SEO_com_IA_-_v1.9` (SvelteKit)
> **Backend Adm:** `server.py` (FastAPI) — 181 endpoints

---

## 🏗️ Arquitetura

```
DezafiraAdm (fábricas/Hermes)                        DezafiraClube (v1.9)
┌────────────────────────────┐                       ┌──────────────────────────────┐
│ Fábrica Blog  → artigo     │── POST /api/import/sync-blog ─▶ /post/[slug] + feeds │
│ Fábrica Ebook → produto    │── POST /api/import/product ───▶ /product/[slug]      │
│ Fábrica Curso → curso      │── external_link com token ───▶ /curso/[id]?token=   │
│ Marketing     → nurturing  │── POST /api/import/nurture ───▶ Resend (4 e-mails)   │
│ Hermes        → landing    │── CLI API /api/cli/landing-pages ─▶ /p/[slug]        │
│ Clube         → checkout   │── Asaas successUrl ──▶ /checkout/obrigado (upsell)   │
└────────────────────────────┘                       └──────────────────────────────┘
```

## 🔑 Variáveis de ambiente (espelho entre os dois lados)

| No Adm | No Clube | Uso |
|---|---|---|
| `CLUBE_IMPORT_KEY` | `IMPORT_API_KEY` | Chave compartilhada (**mesmo valor**) — protege `/api/import/*` e assina o token do player de curso (HMAC-SHA256, TTL 30 dias) |
| `CLUBE_PUBLIC_URL` | — | URL pública do Clube usada pela ponte |
| — | `BACKEND_URL` | URL do backend Adm (ex: `https://dezafiraadm-production.up.railway.app`) usada nos links de entrega do player |
| — | `PUBLIC_ADM_API_URL` | URL do backend Adm usada pelo **VslPlayer** para enviar analytics de retenção (`POST /api/v1/vsl/analytics`). Default: produção |
| `SERVICE_API_KEY` | — | Service key do Hermes no Adm (header `X-Service-Key`) |
| — | `CLI_TOKEN` | Token da **CLI API** do Clube (Admin → **CLI & API**). ⚠️ Na v1.9 é armazenado com **hash + expiração** — regenere após o deploy |

## 📡 Ponte Adm → Clube (`/api/import/*`)

> Autenticação: header `X-Import-Key: <IMPORT_API_KEY>` — comparação timing-safe.

| Método | Rota (no Clube) | O que faz |
|---|---|---|
| POST | `/api/import/product` | Cria produto no catálogo (link/manual; exige `external_link`). Aceita `upsell_product_id`/`downsell_product_id` e **`bundle_items`** (ids dos produtos incluídos num combo/pacote — validados) |
| POST | `/api/import/nurture` | Envia e-mail de nurturing via **Resend** para assinantes ativos |
| POST | `/api/import/sync-blog` | **2 modos**: (1) blueprint `{product_slug, posts[], ads[]}` → cria posts + banners + vínculo; (2) sem body → legado (`articles_export.json`) |
| POST | `/api/import/member-course` | **Novo (Blueprint)**: `{title, lessons[]}` → cria `member_courses` + `member_lessons` na área de membros |

Do lado Adm, os endpoints que disparam a ponte:
`POST /api/v1/clube/import-product` (Adm) → `/api/import/product` (Clube).

### 🎯 Blueprint de Produto (nova ponte completa)

O **Blueprint** (`/admin/blueprint` no Adm — `docs/blueprint_guia.md`) publica um
produto inteiro no Clube nesta ordem (com `publish_log` por etapa):

```
1. Filhos da esteira (upsell/downsell) → /api/import/product
2. Produto principal (com bump, youtube, category e ids da esteira) → /api/import/product
2b. Combo/pacote (se funil.bundle.enabled) → /api/import/product (bundle_items = principal + upsell + downsell)
3. Blog + banners (payload generalizado) → /api/import/sync-blog
4. Landing (blocos prontos do Clube) → /api/cli/landing-pages (Bearer CLI_TOKEN)
5. Área de membros (se curso) → /api/import/member-course
```

### 📦 Combo/pacote nativo (fase 2)

- **Criação**: `bundle_items` (JSON de ids) guardado na coluna `products.bundle_items` (migração automática no `initDatabase`).
- **Desbloqueio**: ao confirmar o pagamento de um bundle (webhooks Asaas/Stripe), `unlockBundleForUser` cria `product_purchases` `completed` para cada produto incluído → aparecem na área de membros e o re-compra é bloqueado (`hasUserPurchasedProduct`).
- **Vitrine**: a página pública do produto (`/product/[slug]`) lista o conteúdo do pacote (thumbnails + nomes).
- **Upsell no pós-compra**: `checkout/obrigado/[productId]` faz reverse lookup (`findBundleForProduct`) — quem comprou só o principal vê o estágio "🎁 Pacote completo" (itens listados + preço original riscado + preço do bundle) antes do upsell.
- **E2E**: `bash scripts/clube_combo_e2e.sh` (sobe o Clube com DB isolado `.e2e_clube.db`, importa itens + pacote, simula webhook Asaas e confere o desbloqueio).

> 🔧 **Fix de banco fresco**: `initDatabase` tinha migrações que rodavam ANTES da
> criação das tabelas (`products.category_id`, `product_purchases.stripe_session_id`,
> `course_purchases.stripe_session_id`) — um deploy/banco novo quebrava. Foram
> movidas para depois dos `CREATE TABLE` (idempotentes — sem efeito em bancos existentes).

## 🎓 Player de curso (entrega protegida)

- Produto com `external_link` apontando para `/curso/{id}` do Adm.
- O Clube decora o link com **token assinado** (`decorateCourseLink` em
  `src/lib/server/courseAccess.ts`): HMAC-SHA256 com `IMPORT_API_KEY`, TTL 30 dias.
- Aplicado em: dashboard, página do produto, página do post, download.
- Sem token válido → **403** (fail-closed).

## 🛒 Funil de vendas (checkout)

1. Compra via Asaas (`createPayment` com `successUrl`) → `/checkout/obrigado/{productId}`
2. Página de obrigado: **Upsell** → recusou → **Downsell** → Dashboard
3. Configuração: Admin → Produtos → seção **🎯 Esteira de Produtos** (campos `upsell_product_id`/`downsell_product_id`)

## 💌 Nurturing (Fase 5 do MarketingPipeline)

- Adm: `POST /api/v1/marketing/nurture/schedule` agenda a régua de 4 e-mails
  (APScheduler) → cada passo chama `POST /api/import/nurture` no Clube.
- `POST /api/v1/marketing/send-nurturing` dispara imediatamente.

## 🧱 Landing pages via CLI (NOVO na v1.9)

O Hermes cria landings de oferta **sem abrir o builder**:

```
GET  /api/cli/landing-pages/schema      → contratos dos blocos (hero, product-showcase,
                                          posts-grid, pricing, faq, cta, ...)
GET  /api/cli/landing-pages/resources   → produtos + posts REAIS do catálogo
POST /api/cli/landing-pages             → cria (status=draft) → retorna edit_url + public_url
GET/PUT/DELETE /api/cli/landing-pages/:id → revisar, editar, publicar, excluir
```

- Autenticação: `Authorization: Bearer <CLI_TOKEN>`
- Rate limit: **120 req/min** (v1.9)
- Validação: Zod + sanitização de blocos (250 blocos máx, 8 níveis, HTML seguro)
- **Script pronto:** `scripts/landing-via-cli.sh` — monta hero → oferta → posts → FAQ → CTA
  com produto/posts reais e publica em `/p/[slug]`:

```bash
CLUBE_URL=https://www.dezafira.com.br CLI_TOKEN=SEU_TOKEN \
  ./scripts/landing-via-cli.sh --title "Guia Completo de X" --product 42 --publish
```

### Exemplo direto (curl)

```bash
# 1. Buscar produto/posts reais
curl -H "Authorization: Bearer SEU_TOKEN" \
  https://www.dezafira.com.br/api/cli/landing-pages/resources

# 2. Criar landing (draft)
curl -X POST -H "Authorization: Bearer SEU_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "title": "Guia Completo de Emagrecimento",
    "slug": "guia-emagrecimento",
    "status": "draft",
    "blocks": [
      { "id": "hero", "type": "hero", "properties": {
          "title": "Guia Completo de Emagrecimento",
          "primaryText": "Quero este guia",
          "primaryHref": "/product/42" } },
      { "id": "oferta", "type": "product-showcase", "properties": {
          "productId": 42, "buttonText": "Garantir acesso",
          "buttonHref": "/product/42" } }
    ]
  }' \
  https://www.dezafira.com.br/api/cli/landing-pages

# 3. Publicar
curl -X PUT -H "Authorization: Bearer SEU_TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"published"}' \
  https://www.dezafira.com.br/api/cli/landing-pages/<ID>
```

## 🧩 CLI de posts (conteúdo via agentes)

| Método | Rota | Observações v1.9 |
|---|---|---|
| GET | `/api/cli/posts?page=&limit=&search=` | agora com **paginação** |
| POST | `/api/cli/posts` | validação Zod (URLs http(s), tamanhos) |
| PUT | `/api/cli/posts/:id` | atualização parcial validada |
| DELETE | `/api/cli/posts/:id` | — |
| PATCH | `/api/cli/categories/:id` | liga/desliga feed Pinterest |
| POST | `/api/cli/upload` | upload Cloudinary |

## 🐳 Deploy (Railway)

- **Root Directory:** `Blog_Inteligente_SEO_com_IA_-_v1.9` (pasta dentro de `Versões do dezafiraClub/`)
- Mesmo `Dockerfile`/`railway.toml` da v1.8.
- Banco: 3 tabelas novas de comunidade (`community_topics/comments/likes`) são criadas no boot — sem migração manual.
- ⚠️ **Pós-deploy:** regenere o token CLI (Admin → CLI & API).
