# Construtor de Landing Pages (Landing Page Builder)

Documentação técnica do construtor visual de Landing Pages integrado ao painel administrativo.

---

## 1. Visão geral

| Item | Valor |
|------|--------|
| Admin listagem | `/admin/landing-pages` |
| Editor visual | `/admin/landing-pages/[id]` |
| Público | `/p/[slug]` |
| Tabela DB | `landing_pages` |
| Factories/templates | `src/lib/landing-blocks.ts` |
| Renderer compartilhado | `src/lib/components/LandingBlockTree.svelte` |

Landing pages públicas são **full-bleed**: não exibem header/footer/WhatsApp do blog (rota `/p/*` no `+layout.svelte`).

---

## 2. Banco de dados

```sql
CREATE TABLE IF NOT EXISTS landing_pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'draft',          -- draft | published
  content TEXT NOT NULL DEFAULT '[]',  -- árvore de blocos JSON
  settings TEXT NOT NULL DEFAULT '{}', -- SEO + tema da página
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Helpers em `src/lib/server/database.ts`:
- `getAllLandingPages`, `getLandingPageById`, `getLandingPageBySlug`
- `createLandingPage`, `updateLandingPage`, `deleteLandingPage`
- `duplicateLandingPage` — clona conteúdo/settings, slug único, status `draft`

---

## 3. Rotas

### A. Admin — listagem (`/admin/landing-pages`)
Actions: `create`, `update`, `delete`, **`duplicate`**

UI:
- Empty state com CTA
- Tabela com status, link público `/p/{slug}`
- **Copiar URL** e **Duplicar**
- Modais: criar, editar metadados, confirmar exclusão
- i18n via `admin.landing_pages.*`

### B. Admin — builder (`/admin/landing-pages/[id]`)
Actions: `save`, `uploadImage`

**Painel esquerdo — abas:**
- **Blocos**: básicos (section, text, image, button, video, divider, spacer, html), estrutura (2/3 colunas, container), conversão (CTA, depoimento, pricing, FAQ, **newsletter**)
- **Bloco newsletter** (captura de lead): renderiza `NewsletterSignup` nativo → POST `/api/newsletter` (Resend). Propriedades editáveis: título, descrição, placeholder e texto do botão (i18n pt/en/es). Útil em landings de lead magnet ligadas ao funil Adm→Clube.
- **Templates**: seções prontas (CTA, depoimentos 3 col, tabela de preços, FAQ, CTA de produto)

**Canvas:**
- Preview desktop/mobile
- Drag-and-drop de blocos
- Seleção com highlight

**Painel direito:**
- SEO da página + propriedades/estilos do bloco selecionado
- Seletor de **produto digital** em botão, CTA e pricing (define `href` → `/product/{slug}`)

**Atalhos de teclado:**
| Atalho | Ação |
|--------|------|
| `Ctrl/Cmd + S` | Salvar |
| `Ctrl/Cmd + Z` | Desfazer |
| `Ctrl/Cmd + Y` ou `Ctrl/Cmd + Shift + Z` | Refazer |

Também: Undo/Redo por botões na topbar · status draft/published · template inicial (hero + features) ao criar página vazia.

O load do editor carrega `products` via `getAllProducts()` para o picker de produto.

### C. Público (`/p/[slug]`)
- `draft` → 404 para visitantes; admin logado vê com banner “Draft preview” + `noindex`
- `published` → render completo
- SEO: title, description, OG/Twitter (imagem absoluta quando relativa)
- Renderer **recursivo** (containers aninhados e colunas)

---

## 4. Modelo de blocos (JSON)

```ts
type Block = {
  id: string;
  type:
    | 'section' | 'container' | 'column' | 'columns'
    | 'text' | 'html' | 'image' | 'button' | 'video'
    | 'divider' | 'spacer'
    | 'cta' | 'testimonial' | 'pricing' | 'faq';
  content?: string;
  styles?: Record<string, string>;
  properties?: Record<string, any>;
  children?: Block[];
};
```

**Importante:** o público e o canvas usam `LandingBlockTree`, que desce a árvore recursivamente. Containers aninhados (ex.: hero com botões) e grids de colunas **são** renderizados.

### Tipos e properties principais

| type | Uso | properties relevantes |
|------|-----|------------------------|
| `section` | Seção full-width | (via styles: bg, padding, textAlign) |
| `container` / `column` | Wrapper aninhável | children |
| `columns` | Grid 2/3 colunas | `cols`, `gap`; children = `column[]` |
| `text` / `html` | Conteúdo HTML | `content` |
| `image` | Imagem | `src`, `alt` |
| `button` | CTA simples | `href`, `productId`, `productSlug` |
| `video` | YouTube | `src` (URL ou ID) |
| `divider` / `spacer` | Separadores | estilos de borda / altura |
| `cta` | Bloco de conversão | `subtitle`, `buttonText`, `buttonHref`, `buttonBg`, `buttonColor`, `productId` |
| `testimonial` | Depoimento | `quote`, `author`, `role`, `avatar`, `rating` |
| `pricing` | Card de plano | `name`, `price`, `period`, `features[]`, `buttonText`, `buttonHref`, `featured`, `productId` |
| `faq` | FAQ expansível | `title`, `items: { q, a }[]` |

### Templates de conversão (`createTemplate`)

| Nome | Conteúdo |
|------|----------|
| `cta_section` | Seção escura + bloco CTA |
| `testimonials` | Título + 3 depoimentos em colunas |
| `pricing` | Título + 3 planos (meio destacado) |
| `faq_section` | Seção com FAQ |
| `product_cta` | CTA verde para produto digital |

Factories em `src/lib/landing-blocks.ts`: `createBlock`, `createColumns`, `createCtaBlock`, `createTestimonialBlock`, `createPricingBlock`, `createFaqBlock`, `createTemplate`, `youtubeId`.

Settings típicos da página:
```json
{
  "seoTitle": "",
  "seoDesc": "",
  "socialImage": "",
  "containerWidth": "1200px",
  "backgroundColor": "#ffffff",
  "textColor": "#111827"
}
```

---

## 5. Linkar produto digital

No painel de propriedades de **botão**, **CTA** ou **pricing**:

1. Selecione um produto no dropdown (lista vinda de `getAllProducts`)
2. O builder grava `productId`, `productSlug` e define o href para `/product/{slug}`
3. Na página pública, o clique leva à vitrine do produto

---

## 6. Upload de imagens

1. **Cloudinary** (pasta `blog/landings`) se `CLOUDINARY_*` estiver no `.env`
2. **Fallback local**: `static/uploads/landings/` → URL `/uploads/landings/...`

---

## 7. YouTube

O parser (`youtubeId` em `landing-blocks.ts`) aceita:
- `youtube.com/watch?v=ID`
- `youtu.be/ID`
- `youtube.com/embed/ID`
- `youtube.com/shorts/ID`
- ID puro de 11 caracteres

---

## 8. VSL (Video Sales Letter) & Teste A/B/C de Headlines

O DezafiraClube possui suporte nativo para VSLs de alta conversão gerenciadas pela Fábrica de VSLs no Dezafira Adm.

*   **Bloco `vsl`:** Renderiza uma VSL com o player HTML5 customizado (`VslPlayer.svelte`) e a headline sorteada para o visitante.
*   **Properties do Bloco `vsl`:**
    *   `vslId` (String) - ID único da VSL configurada no painel.
    *   `src` (String) - Link direto `.mp4` de vídeo hospedado no Cloudflare R2 / BunnyCDN.
    *   `thumbnail` (String) - URL da imagem de miniatura exibida antes do play.
    *   `delaySeconds` (Number) - Segundos de delay para exibir botões de compra, formulários e pricing na página.
    *   `headline_a`, `headline_b`, `headline_c` (String) - Variações de headlines persuasivas geradas automaticamente por IA.
*   **Comportamento do Player (`VslPlayer.svelte`):**
    *   *Smart Autoplay:* Tenta autoplay sonoro. Se bloqueado, executa silenciado e exibe overlay "🔊 Clique para ativar o som". Ao clicar, o vídeo reinicia com áudio do zero.
    *   *No-Seek & Barra Warped:* Desativa controles nativos e impede avançar/retroceder. A barra de progresso avança rápido no início e desacelera perto do pitch de vendas.
    *   *Pause Recovery:* Modal de atenção se o vídeo for pausado.
    *   *Smart Pause:* Pausa se o usuário rolar para longe ou mudar de aba do navegador.
    *   *Resume Watching:* Salva posição em `localStorage` para retomar em visitas futuras.
    *   *Analytics:* Envia eventos de visualização (0%, 25%, 50%, 75%, 100%) e conversões de lead para a API do Adm em tempo real.
*   **Split Testing A/B/C:**
    *   `LandingBlockTree.svelte` sorteia aleatoriamente a headline (A, B ou C) e persiste a escolha no cookie do navegador do visitante.
    *   Cliques em botões de conversão e CTAs disparam o evento de conversão associado à variação sorteada.

---

## 9. Checklist de verificação

1. Criar página em `/admin/landing-pages` → redireciona ao editor com ID válido
2. Template hero + features aparece no canvas **e** em `/p/{slug}` (containers aninhados)
3. Inserir **2/3 colunas** e componentes CTA / depoimento / pricing / FAQ
4. Aba **Templates** → inserir seções prontas (pricing, testimonials, etc.)
5. Em botão ou CTA: **linkar produto** → href vira `/product/{slug}`
6. `Ctrl+S` salva; `Ctrl+Z` / `Ctrl+Y` desfaz/refaz
7. Upload de imagem (Cloudinary ou pasta local)
8. Publicar → visitante anônimo acessa `/p/{slug}`
9. Draft → 404 para anônimo; admin vê banner
10. Duplicar → nova página draft com slug único
11. Página pública **sem** header/footer do blog

---

## 10. Melhorias futuras (backlog residual)

- Preview em iframe isolado com CSS da página
- i18n completo das labels do builder (hoje misturam PT fixo + chaves admin)
- Reordenar blocos por drag entre posições da árvore
- Variantes de template por nicho (infoproduto, SaaS, evento)
