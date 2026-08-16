# Sistema de Links Curtos (Shortlinks) com Interstitial de Anúncios

O sistema de **Links Curtos** do blog permite gerar URLs amigáveis internas (ex: `/l/promocao`) que redirecionam os leitores para URLs de destino externas (ex: links de afiliados, páginas de venda, checkout de infoprodutos).

> **Rota pública:** `src/routes/l/[slug]/` — não remover. O admin em `/admin/shortlinks` só gerencia dados; o acesso real é `/l/{slug}`.

---

## 🛠️ 1. Como Criar e Gerenciar Links Curtos

A ferramenta está disponível no menu lateral do painel administrativo sob a seção **Ferramentas** -> **Links Curtos** (`/admin/shortlinks`).

### Parâmetros de Configuração:
* **Slug (URL Encurtada):** O identificador único do link. Por exemplo, se definir como `cupom-desconto`, a URL de acesso será `seusite.com/l/cupom-desconto`.
* **URL de Destino (Link Final):** O endereço completo da página para onde o usuário será enviado (ex: `https://hotmart.com/checkout/...`).
* **Exibir anúncio intermediário antes de redirecionar:**
  - **Desativado (⚡ Redirecionamento Direto):** O leitor é redirecionado instantaneamente (código HTTP `302`) ao acessar a URL encurtada.
  - **Ativado (📢 Interstitial de Anúncios):** O leitor passa por uma página intermediária contendo um anúncio ativo e um contador regressivo antes de ir para o destino.
* **Tempo do anúncio:** Quantidade de segundos que o contador aguardará antes de efetuar o redirecionamento automático (padrão: `5` segundos, configurável entre `3` e `30` segundos).
* **Permitir indexação no Google (SEO):** 
  - **Desativado (🔒 Privado - padrão):** Injeta tags `noindex, nofollow` na página e no cabeçalho HTTP de resposta, mantendo o redirecionamento privado.
  - **Ativado (🔍 Indexado):** Permite que robôs de busca indexem a rota curta.

---

## 📢 2. Funcionamento do Interstitial de Anúncios

Quando um link está configurado para exibir anúncios intermediários:
1. O sistema faz uma busca no banco de dados e escolhe de forma **aleatória** um dos anúncios que estejam cadastrados e com status **Ativo** na aba de **Anúncios** (`/admin/ads`).
2. O leitor é levado para a página `/l/[slug]`, que renderiza o anúncio em destaque (com suporte a todos os tipos de anúncio cadastrados: imagens clicáveis, blocos de códigos HTML como Google AdSense, banners nativos ou links de texto).
3. Um botão de **Pular Anúncio** fica desabilitado nos primeiros 2 segundos para garantir a visualização da propaganda, tornando-se clicável após esse período para que o usuário possa acelerar o redirecionamento sem se frustrar.
4. Um contador exibe o tempo restante em tempo real integrado a uma barra de progresso horizontal no topo da página. Ao atingir `0` segundos, o navegador do usuário realiza o redirecionamento automático de forma transparente.

> [!IMPORTANT]
> **Fallback de Segurança:** Caso um link esteja configurado com interstitial de anúncios, mas você **não** possua nenhum anúncio cadastrado ou ativo no sistema, o blog realizará o **redirecionamento direto e instantâneo** para evitar que o leitor se depare com uma página intermediária vazia.

---

## 📊 3. Contador de Cliques, Busca e Paginação

Toda vez que uma URL curta é acessada, o sistema computa o acesso incrementando de forma assíncrona o contador de cliques (`clicks_count`) daquele link específico no banco de dados. As estatísticas em tempo real podem ser conferidas diretamente na tabela da tela `/admin/shortlinks`.

### Gerenciamento Otimizado:
* **Filtro de Busca**: Um formulário de busca no topo da lista permite pesquisar rapidamente os links por slug ou por URL de destino final.
* **Paginação**: A listagem de links é paginada exibindo 10 registros por página, facilitando o gerenciamento em blogs com centenas de links encurtados.

---

## 🔒 4. Privacidade e Indexação no Google (SEO Whitelabel)

Com o foco em manter a flexibilidade de um blog **whitelabel**, o sistema de links curtos implementa um controle granular de indexação para motores de busca:
* **Privacidade por Padrão**: Toda vez que um link é criado, ele nasce configurado como **Privado (noindex)**. Isso evita que robôs do Google descubram e listem links promocionais, links de afiliados ou páginas de encaminhamento diretamente nos resultados de busca pública de inquilinos.
* **Mecanismo Técnico**: Quando o link é configurado como Privado, a página intermediária e a resposta HTTP de redirecionamento imediato carregam a tag de robots `<meta name="robots" content="noindex, nofollow" />` e o cabeçalho HTTP `X-Robots-Tag: noindex, nofollow`.
* **Indexação Ativa**: Caso deseje explicitamente que o link seja público e indexado nas buscas, basta habilitar a opção **Permitir indexação no Google** na criação ou na tela de edição rápida do link.
