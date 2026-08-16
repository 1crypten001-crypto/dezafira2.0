# Changelog — v1.7

Resumo das novidades para divulgação do pacote `Blog Inteligente SEO com IA - v1.7.zip`.

---

## Inteligência & conteúdo

- **Feed estilo YouTube** — mix de novos + relevantes + descobertas, sem duplicar, com posts vistos saindo por 48h e voltando depois
- **Web Stories AMP** — admin em Ferramentas, player `/stories/[slug]`, bolinhas opcionais no site, sitemap automático
- **Editor de Stories premium** — preview de celular, upload Cloudinary, status No ar/Rascunho em 1 clique, gerar a partir de post

---

## Produtos & monetização

- **Produtos na assinatura Premium** — vitrine com banners e inclusão retrocompatível
- **Planos premium por produto** — escolher quais planos liberam cada produto (com validação no load/download)
- **Catálogo com categorias do admin** — filtro real pela tabela gerenciada (não mais dado legado)
- **Fix LibSQL/Turso** — filtro de categorias de produtos estável no banco em nuvem
- **UX de produto no post** — link para a página do produto, descrição com fade + “ver mais”, download com loading e anti double-click
- **i18n de textos premium/produto** — promoções e acesso premium traduzíveis

---

## Landing pages (builder)

- **Builder multilingue** — defaults e fallbacks em pt/en/es
- **UI mobile-first** — template starter, cards e espaçamentos pensados pro celular
- **Ícones e editor consistentes** — outline unificado e HTML do builder mais limpo (também em páginas antigas)

---

## Mídia & qualidade

- **Cloudinary sem `f_auto`** — evita forçar WebP no mobile e quebrar imagem em alguns dispositivos

---

## Estabilidade

- **Shortlinks `/l/[slug]`** — rota pública restaurada (redirect direto e interstitial de anúncios)

---

## Pacote

```powershell
.\criar-pacote.ps1 -Version "v1.7"
```

Arquivo: `Blog Inteligente SEO com IA - v1.7.zip`  
Docs: [web-stories.md](./web-stories.md) · [shortlinks.md](./shortlinks.md)
