# 🚀 Tube Writer (SvelteKit + LibSQL/SQLite Whitelabel Blog)

Um sistema de blog completo, altamente otimizado para SEO, responsivo e com suporte **Whitelabel** integrado. Criado com **SvelteKit 2.x** + **Svelte 5 (Runes)** + **LibSQL (Turso)** ou **SQLite local**.

Destaques: importação automática do YouTube com IA (Google Gemini), **Web Stories AMP** com bolinhas estilo Instagram, feed inteligente (estilo YouTube), feeds Pinterest, anúncios, área de membros premium, produtos digitais, Asaas/Stripe, analytics com filtro de prefetch.

**Versão do pacote de distribuição:** `v1.7` — ver [docs/changelog-v1.7.md](docs/changelog-v1.7.md).

---

## ✨ Funcionalidades Principais

* **📱 Web Stories (AMP)**:
  * Admin em **Ferramentas → Web Stories** — criar, gerar a partir de post, status No ar/Rascunho.
  * Player público `/stories/[slug]` em HTML AMP (compatível com Google Web Stories).
  * Bolinhas opcionais abaixo do menu (sem caixa que corte o hero).
  * Stories publicadas entram no **sitemap** automaticamente.
* **🧠 Feed inteligente na home**:
  * Mix de conteúdo novo, relevante e descobertas (estilo feed inicial do YouTube).
  * Sem duplicatas; posts já vistos saem do topo por ~48h e voltam depois.
* **🎓 Área de Membros Completa**:
  * Organização em Cursos, Aulas e Materiais de apoio para download.
  * Três modelos de acesso configuráveis por curso: **Gratuito (`free`)**, **Premium (`premium`)** e **Pago individualmente (`paid`)**.
  * Proteção estrita de streaming: as URLs brutas de vídeo (YouTube/Vimeo) nunca são expostas no HTML público.
* **💳 Integração Financeira (Asaas / Stripe)**:
  * Cobranças recorrentes (assinatura Premium) e compras avulsas de cursos/produtos.
  * Produtos incluídos no Premium e planos específicos por produto.
  * Liberação automática do acesso via Webhooks.
* **🪄 Importador IA do YouTube**: Cole o link do vídeo → o Gemini analisa a transcrição e gera um artigo otimizado para SEO com imagens e formatação.
* **📊 Analytics e Proteção de Prefetch**:
  * Rastreamento local leve de visitas sem dependências externas ou cookies invasivos.
  * **Filtro Inteligente**: Ignora preloading especulativo (`Purpose: prefetch`, `X-Sveltekit-Preload`, etc.).
* **📌 Feeds Otimizados para Pinterest**: Feeds RSS dinâmicos globais e por categoria (imagens 9:16).
* **🔗 Links Curtos**: `/l/[slug]` com redirect direto ou interstitial de anúncios.
* **📄 Landing Pages**: Builder visual em `/p/[slug]` (mobile-first, i18n).
* **📢 Gestão de Anúncios**: Blocos HTML, imagem ou texto com pesos no painel.
* **🎨 Tema Claro/Escuro & Design Moderno**: Responsivo, masonry (Pinterest-like).

---

## 💻 Tech Stack

* **Frontend**: SvelteKit 2.x, Svelte 5 (com Runes como `$state`, `$derived`, `$props`), Vanilla CSS (sem TailwindCSS ou frameworks externos).
* **Backend**: SvelteKit Server Endpoints e hooks de ciclo de vida.
* **Banco de Dados**: Suporta SQLite nativo local com `better-sqlite3` e banco distribuído na nuvem com `@libsql/client` (Turso).
* **IA**: `@google/genai` (Gemini 2.5 Flash).
* **Uploads**: Cloudinary para armazenamento de imagens de posts, capas de cursos e materiais para download.

---

## 📚 Documentação Detalhada (/docs)

Toda a documentação operacional e técnica foi organizada e está disponível nos links abaixo:

1. **🚀 [Guia de Instalação e Inicialização](docs/installation.md)**: Clonar, dependências e bancos SQLite/Turso.
2. **⚙️ [Configurações do .env](docs/configuration.md)**: Variáveis de ambiente e senha forte em produção.
3. **🎓 [Área de Membros e Pagamentos](docs/members-area.md)**: Planos, streaming seguro e webhooks Asaas/Stripe.
4. **📊 [Analytics e Prefetch](docs/analytics.md)**: Rastreador interno e filtro de preloading.
5. **🔗 [Links Curtos e Interstitial](docs/shortlinks.md)**: `/l/[slug]`, anúncios e contador.
6. **📱 [Web Stories AMP](docs/web-stories.md)**: Admin, bolinhas, AMP, sitemap e Google.
7. **📄 [Landing Pages](docs/landing-pages.md)**: Builder visual e páginas `/p/[slug]`.
8. **🌍 [Sistema de idiomas](docs/language-system.md)**: i18n pt/en/es.
9. **🤖 [AI Agent Developer Manual](docs/agents.md)**: Guia para agentes de código (Svelte 5, schemas).
10. **📦 [Changelog v1.7](docs/changelog-v1.7.md)**: Novidades do pacote de distribuição.

### Gerar zip de distribuição

```powershell
.\criar-pacote.ps1 -Version "v1.7"
```

Gera `Blog Inteligente SEO com IA - v1.7.zip` na raiz (sem `.env`, `.db` nem `node_modules`).

---

## ⚡ Guia Rápido de Instalação

```bash
# 1. Instalar dependências
npm install

# 2. Configurar o ambiente
cp .env.example .env
# Edite as credenciais de banco, Cloudinary, Gemini, MP e Asaas

# 3. Inicializar e estruturar o banco
npm run init-db

# 4. Iniciar servidor local
npm run dev
```

Acesse o blog em `http://localhost:5173` e a área administrativa em `http://localhost:5173/admin`.

---

## 🔒 Segurança Integrada

* Proteção contra XSS e injeção de HTML via sanitizadores estruturados.
* Cabeçalhos de segurança (CSP, HSTS, X-Content-Type-Options).
* Validação rigorosa de uploads e hashes de senha com `bcrypt`.
* Rate Limiting nativo para tentativas de autenticação administrativa.

---

## 📝 Licença

MIT — Use e modifique conforme necessário.