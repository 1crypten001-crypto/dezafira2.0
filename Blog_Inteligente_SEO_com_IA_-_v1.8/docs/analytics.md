# Sistema de Analytics e Filtro de Prefetch

O blog possui um mecanismo nativo e simplificado de estatísticas para contar acessos às páginas (Visualizações de Página), armazenados na tabela `page_views` do banco de dados.

---

## ⚙️ Como Funciona o Rastreamento

Toda a lógica de analytics é executada no servidor utilizando os **Server Hooks** do SvelteKit em `src/hooks.server.ts`. Isso traz grandes benefícios:
1. **Sem Dependência de Scripts de Terceiros**: Evita carregar scripts externos pesados no frontend (como Google Analytics ou Hotjar), melhorando os índices de PageSpeed e SEO.
2. **Respeito à Privacidade e Desempenho**: Funciona de forma assíncrona no backend, sem atrasar o carregamento visual da página para o usuário.

### Regras de Rastreabilidade:
No hook `analyticsHandle`, apenas são contabilizadas requisições que cumpram as seguintes regras:
* O método da requisição deve ser exatamente `GET`.
* O caminho (URL) não pode conter extensões ou referências a arquivos estáticos (exclui `.js`, `.css`, imagens, favicons).
* Não rastreia requisições internas das áreas `/admin`, `/api` ou de autenticação `/auth`.

Quando estas condições são atendidas, o servidor normaliza o endereço IP (removendo prefixos IPv6 de proxy local) e extrai o cabeçalho `User-Agent`. A função `recordPageView` classifica o tipo de página (`home`, `post` ou `category`) e insere o registro no banco.

---

## 🛡️ Evitando Duplicidade (Rate Limiting)

Para evitar inflação artificial de visualizações (por exemplo, quando o usuário atualiza a mesma página seguidas vezes):
* Existe uma trava de tempo baseada na combinação de **IP + User Agent + Slug**.
* Se um acesso com as mesmas características ocorrer dentro do intervalo de **1 hora**, a visualização adicional é ignorada e não é gravada no banco de dados.

---

## 🔍 Filtro de Pré-carregamento (Prefetch e Prerender)

Navegadores modernos (como o Chrome) realizam **Speculative Preloading** (pré-carregamento especulativo). Ao detectar links no viewport ou quando o usuário passa o mouse por cima de um card, o navegador faz uma requisição em segundo plano para o link (ex: `/post/como-ganhar-dinheiro`) para agilizar uma eventual transição.

Essas requisições de segundo plano eram incorretamente registradas como visualizações reais. Para solucionar esse problema, adicionamos verificações de cabeçalhos no hook de analytics.

### Cabeçalhos Filtrados:
O sistema analisa os seguintes cabeçalhos de requisição enviados pelos navegadores e pelo client do SvelteKit:

| Cabeçalho | Valor | Significado |
|-----------|-------|-------------|
| `Purpose` | `prefetch` | Pré-carregamento padrão de páginas. |
| `Sec-Purpose` | `prefetch` / `prerender` | Pré-carregamento/prerenderização especulativa no Chrome/Edge. |
| `X-Purpose` | `preview` / `prefetch` | Modos de visualização rápida ou prefetch de navegadores específicos. |
| `X-Moz` | `prefetch` | Pré-carregamento de links no Firefox. |
| `X-Sveltekit-Preload` | *(presença)* | SvelteKit pré-carregando dados ou código no hover/focus do link. |

Se qualquer uma das condições acima for atendida, o middleware identifica a requisição como pré-carregamento de máquina e **ignora a contagem da visualização**, mantendo a estatística limpa e realista no painel de administração.
