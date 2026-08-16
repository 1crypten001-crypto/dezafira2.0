# Sistema de Tradução Multilíngue (i18n)

Este documento descreve o funcionamento do sistema de internacionalização (i18n) do blog. O administrador define **um idioma global** do site (Português, Inglês ou Espanhol) em **Admin → Configurações → Geral** (`site_language`).

O objetivo é um **whitelabel global**: a UI pública e a área de membros respondem ao idioma configurado. Conteúdo do banco (títulos de posts, planos, cursos) **não** é traduzido automaticamente.

---

## 1. Arquivo central (`src/lib/i18n.ts`)

### Dicionários
- `pt` (padrão), `en`, `es`
- Namespaces principais:
  - `common` — botões e labels genéricos
  - `nav` — menu / a11y do header
  - `footer`, `cookie`, `age`, `newsletter`
  - `contact`, `home`, `post`, `categories`, `category`
  - `premium_page`, `products`, `product`, `reviews`
  - `pagination`, `search`, `share`, `ad`, `breadcrumb`
  - `error`, `shortlink`, `members`, `legal`
  - `admin` — menu do painel + UI das páginas admin (ver também `src/lib/i18n-admin.ts`)

### Helpers exportados
```ts
t(lang, key, vars?)           // resolve chave com fallback para pt
normalizeLang(lang)           // 'pt' | 'en' | 'es'
getLocale(lang)               // pt-BR | en-US | es-ES
htmlLang(lang)                // atributo <html lang>
formatDate(lang, date, opts?) // datas localizadas
formatMoney(lang, cents)      // moeda BRL com locale do idioma
memberErrorMessage(lang, err) // códigos de erro de form actions
```

### Função `t`
- `lang`: `'pt' | 'en' | 'es'`
- `key`: caminho com ponto, ex. `'product.secure_payment'`
- `vars`: interpolação `{name}` no texto
- Fallback: se a chave não existir no idioma ativo, usa `pt`

---

## 2. Como o idioma é carregado

1. `settings.site_language` no SQLite (`'pt' | 'en' | 'es'`)
2. `src/routes/+layout.server.ts` expõe `language: settings.site_language || 'pt'`
3. Disponível em toda a árvore via `$page.data.language`
4. `hooks.server.ts` ajusta `<html lang="...">` no HTML SSR
5. `+layout.svelte` também atualiza `document.documentElement.lang` no client

---

## 3. Uso em componentes (Svelte 5)

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import { t, formatDate, formatMoney } from '$lib/i18n';

  const lang = $derived($page.data.language || 'pt');
</script>

<h3>{t(lang, 'product.secure_payment')}</h3>
<p>{t(lang, 'home.results_for', { q: query })}</p>
<span>{formatMoney(lang, product.price_cents)}</span>
<span>{formatDate(lang, post.created_at)}</span>
```

Header/Footer também aceitam prop `language` repassada pelo layout.

---

## 4. Superfícies cobertas

| Área | Status |
|------|--------|
| Header, Footer, Cookie, Age 18+, Newsletter, ContactForm | Sim |
| Pagination, Search, SocialShare, PostCard, Related, Ad, Breadcrumb, Modal | Sim |
| Home, post, categories, category, contact | Sim |
| Premium, products, product | Sim |
| Privacy, Terms, Cookies (templates legais) | Sim |
| 404/500, shortlink `/l`, RSS language | Sim |
| Members: login, register, dashboard, area, player | Sim |
| Admin menu (sidebar) | Sim |
| Admin páginas e formulários (login, dashboard, posts, ads, products, courses, sales, users, settings, newsletter, shortlinks, cli…) | Sim — chaves em `admin.ui.*`, `admin.dash.*`, `admin.posts.*`, … (`src/lib/i18n-admin.ts`) |
| Conteúdo DB (posts, nomes de planos) | Não traduzido |

---

## 5. Configuração no admin

- Rota: `/admin/settings` → aba **Geral**
- Campo: `site_language`
- Valores válidos: `pt`, `en`, `es` (qualquer outro vira `pt` no save)

---

## 6. Erros de formulário (membros)

Preferência: retornar **códigos** no server (`INVALID_CREDENTIALS`, `RATE_LIMIT`, …) e mapear com `memberErrorMessage(lang, code)`.

Códigos conhecidos em `members.errors.*`. Strings legadas em português ainda são mapeadas quando possível.

---

## 7. URLs públicas: sempre em inglês (canônicas)

O idioma do site (`site_language`) traduz **labels da UI**, não os paths. Rotas públicas e de membros usam paths em **inglês** para whitelabel global, SEO e consistência:

| Path | Uso |
|------|-----|
| `/` | Home |
| `/categories`, `/category/[slug]` | Categorias |
| `/post/[slug]` | Post |
| `/products`, `/product/[slug]` | Vitrine e produto |
| `/premium` | Planos |
| `/contact`, `/privacy`, `/terms`, `/cookies` | Contato e legal |
| `/members/*` | Área de membros |
| `/p/[slug]` | Landing pages |
| `/admin/*` | Painel (inglês) |

**Não** localizar paths (`/produtos`, `/categorias`, `/privacidade`). Labels no menu mudam com o idioma; a URL permanece a mesma.

Redirect legado: `/produtos` → `301 /products` (bookmarks e links antigos).

---

## 8. O que não fazer

- Não hardcodar português em UI pública/membros nova
- Não hardcodar paths em português (ex.: `/produtos`) — use `/products`
- Não usar ternários `lang === 'en' ? ...` — use `t()`
- Não traduzir automaticamente HTML de posts (SEO/conteúdo editorial fica a cargo do admin)
- Legal templates são genéricos; o operador deve revisar juridicamente para o país/público-alvo

---

## 9. Extensão futura

- Exemplos curl/docs longos da página CLI (parte do conteúdo técnico pode permanecer bilingue)
- Seletor de idioma por visitante (cookie) em vez de só global
- Moeda configurável além de BRL
- Paths localizados só fariam sentido com seletor por visitante + hreflang; não é o modelo atual (idioma global do site)

### Arquivos de dicionário admin
- `src/lib/i18n-admin.ts` — base do painel
- `src/lib/i18n-admin-residual.ts` — labels densos (settings, sales, cli chrome, etc.)
- Merge em `src/lib/i18n.ts` via `deepMergeAdmin`
