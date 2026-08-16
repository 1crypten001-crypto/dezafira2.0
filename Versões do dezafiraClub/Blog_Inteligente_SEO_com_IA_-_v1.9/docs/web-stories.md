# Web Stories (AMP) — Guia de Uso

Web Stories no Tube Writer são histórias curtas em formato **AMP Story**, gerenciadas em **Admin → Ferramentas → Web Stories**. Podem reutilizar posts, aparecer como bolinhas estilo Instagram no site e ser descobertas pelo Google via sitemap.

---

## 1. O que é

| Item | Detalhe |
|------|---------|
| **Admin** | `/admin/web-stories` |
| **URL pública** | `/stories/[slug]` (HTML AMP controlado no servidor) |
| **Sitemap** | Stories **publicadas** entram em `/sitemap.xml` como `/stories/slug` |
| **Bolinhas no site** | Opcional — switch no admin (“Bolinhas no site”) |

Formato compatível com **Google Web Stories** (AMP): poster vertical, publisher, slides com imagem + texto + CTA.

---

## 2. Criar e gerenciar

### A partir de um post
1. Em Web Stories, clique em **Do post**.
2. Escolha o artigo e **Gerar**.
3. O sistema cria um **rascunho** com título, capa e trechos do conteúdo.
4. Revise slides, imagens e marque **No ar**.

### Manual
1. **+ Nova** (`/admin/web-stories?new=1`).
2. Preencha título (slug pode ser automático).
3. Envie **poster 9:16** e **bolinha** (Cloudinary ou URL).
4. Adicione slides (acordeão no editor).
5. Status **No ar** ou **Rascunho** — também pode alternar na lista com 1 clique.

### Status
| Badge | Significado |
|-------|-------------|
| **No ar** | Pública, bolinhas (se ativas), sitemap |
| **Rascunho** | Só no admin |

---

## 3. Bolinhas na home

1. No topo da lista de Web Stories, ative **Bolinhas no site**.
2. Só aparecem stories **No ar**.
3. Ficam **logo abaixo do menu**, sem caixa/fundo extra (não “cortam” o hero).
4. Clique abre `/stories/slug` (reload full — player AMP).

---

## 4. Google e SEO

### Precisa de cadastro manual no Google?
**Não.** Não há painel separado de “Web Stories”. Com a story **publicada**:

- Entra no **sitemap** automaticamente  
- Pode ser descoberta por links do site  
- O Google decide se mostra em Discover/busca  

### Recomendações
1. Site no **Search Console** (uma vez).  
2. Sitemap `https://seusite.com/sitemap.xml` enviado (se ainda não).  
3. Poster vertical de qualidade (~720×1280).  
4. Conteúdo útil nos slides + CTA para o post.  
5. Opcional: Inspecionar URL `/stories/...` e solicitar indexação.

**Expectativa:** Stories **complementam** SEO; o artigo longo continua sendo o principal para palavras-chave.

---

## 5. Regras técnicas (AMP)

O HTML da story é **gerado no servidor** (`src/lib/server/web-story-amp.ts` + rota `src/routes/stories/[slug]/+server.ts`):

- Documento AMP completo (sem shell SvelteKit no miolo)  
- Tags `amp-story` / `amp-story-page` / `amp-img`  
- Sem HTML livre do editor no corpo da story  
- JSON-LD Article básico  

Validação opcional: [AMP Validator](https://validator.ampproject.org/).

---

## 6. Banco de dados

```sql
web_stories (
  id, title, slug, cover_image, poster_portrait,
  source_type, source_post_id, cta_url, cta_text,
  published, sort_order, created_at, updated_at
)

web_story_slides (
  id, story_id, sort_order,
  background_image, title, body, cta_url, cta_text
)
```

Setting: `enable_web_stories_bar` = `1` | `0`.

Uploads de imagem usam a API `/api/upload` com pasta `blog/stories` (Cloudinary, com fallback local).

---

## 7. Rotas e arquivos

| Caminho | Função |
|---------|--------|
| `src/routes/admin/web-stories/` | CRUD admin |
| `src/routes/stories/[slug]/+server.ts` | Página pública AMP |
| `src/lib/server/web-story-amp.ts` | Builder AMP + split de texto do post |
| `src/lib/components/StoriesBar.svelte` | Bolinhas no layout |
| `src/routes/sitemap.xml/+server.ts` | Inclui stories publicadas |
