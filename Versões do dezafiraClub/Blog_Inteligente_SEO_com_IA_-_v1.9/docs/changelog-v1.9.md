# Changelog — v1.9 (DezafiraClube)

Resumo das novidades da v1.9 + a migração aplicada ao projeto Dezafira (customizações preservadas).

---

## 🆕 Novidades da ferramenta (v1.9)

### 🧱 Landing Pages — Builder v2
- **Drag-and-drop** no editor visual (`src/lib/landing-dnd.ts`, `LpEditableShell`, `LandingBlockTree`)
- **Painel CLI no editor** (`LandingCliPanel.svelte`) + **manifesto de contratos** (`landing-cli-manifest.ts`)
- **Endpoints CLI de landings**: `GET/POST /api/cli/landing-pages`, `PUT/DELETE /api/cli/landing-pages/:id`, `GET /api/cli/landing-pages/schema`, `GET /api/cli/landing-pages/resources` (produtos + posts reais)
- **Sanitização server-side** de blocos (`src/lib/server/landing-pages.ts`): até 250 blocos, 8 níveis de profundidade, HTML sanitizado

### 🗣️ Comunidade (fórum)
- Seção **admin/community** (fixar/excluir tópicos)
- Área de membros: tópicos, comentários e likes (`community_topics`, `community_comments`, `community_likes` — 3 tabelas novas, criadas automaticamente no boot)
- Rota pública premium: `/members/area/topic/[id]`

### 🔐 CLI/API — endurecimento
- **Validação com Zod** (`src/routes/api/cli/validation.ts`) em posts e landings
- **Rate limiting** no token CLI (120 req/min, cabeçalhos `X-RateLimit-*`)
- **Token com hash + expiração** (`cli_token_hash` + `cli_token_expires_at`) — ⚠️ *depois do deploy, regenere o token na página Admin → CLI & API*
- **Paginação** em `GET /api/cli/posts` e `GET /api/cli/landing-pages`
- `getPostsAdminPage`, `getExistingCategoryIds`, `runBatch` (transação em lote)

### ⚡ Outros
- **Cache em memória** (`src/lib/server/cache.ts`) com invalidação de posts
- **Página `/about`** (rascunho do fornecedor — pasta vazia, aguardando conteúdo)
- Ajustes em post, product, members/area, admin, i18n, sanitize, app.css

---

## 🔧 Migração Dezafira v1.8 → v1.9 (preservado)

Todas as customizações Dezafira foram mantidas sobre a base v1.9:

| Customização | Status |
|---|---|
| Funil de vendas: checkout + upsell/downsell (`/checkout/obrigado`) | ✅ Mantido |
| Ponte Adm→Clube: `/api/import/product`, `/api/import/nurture`, `/api/import/sync-blog` (`IMPORT_API_KEY`) | ✅ Mantida |
| Proxy `/api/v1/*` para o backend Adm | ✅ Mantido |
| Painel legado `/adm` + `/healthz` | ✅ Mantidos |
| Player de curso (`courseAccess.ts` — HMAC, TTL 30d) decorando links em dashboard/post/product/download | ✅ Mantido |
| Sync de senha do admin via `ADMIN_PASSWORD` (database.ts, auth.ts, init-db.ts) | ✅ Mantido |
| `successUrl` custom no Asaas (redireciona p/ funil) | ✅ Mantido |
| Colunas `upsell_product_id` / `downsell_product_id` (migração + CRUD) | ✅ Mantidas |
| Dockerfile, railway.toml, .dockerignore, scripts de migração | ✅ Mantidos |
| Docs de configuração (seções `IMPORT_API_KEY`/`BACKEND_URL`) | ✅ Mantidos |

**Dependências:** nenhuma nova (package.json idêntico à v1.8, exceto vitest 2.1.9).  
**Env vars:** nenhuma nova.  
**Banco:** 3 tabelas novas aditivas; nada é removido.

> ⚠️ **Pós-deploy:** regenere o **token da CLI/API** (Admin → CLI & API → Regenerar Token) — a v1.9 passa a armazenar o token com hash e expiração.
