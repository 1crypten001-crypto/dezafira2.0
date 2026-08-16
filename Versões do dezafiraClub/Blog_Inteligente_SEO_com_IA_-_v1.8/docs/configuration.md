# Guia de Configuração (Variáveis de Ambiente)

A aplicação utiliza variáveis de ambiente para gerenciar credenciais do banco de dados, chaves de APIs parceiras e opções do sistema. Este documento descreve cada parâmetro disponível no arquivo `.env`.

---

## 🗄️ 1. Banco de Dados (SQLite / Turso)

* **`DATABASE_URL`**: URL de conexão do banco de dados Turso (ex: `libsql://meu-blog-usuario.turso.io`). Deixe em branco se desejar usar o SQLite local.
* **`DATABASE_AUTH_TOKEN`**: Token de autenticação gerado pelo Turso para acesso de escrita/leitura.
* **`DATABASE_PATH`**: Caminho relativo para o arquivo de banco local do SQLite (padrão: `./blog.db`). Usado quando `DATABASE_URL` não está definida.

> [!IMPORTANT]
> **Compatibilidade de Hospedagem (SQLite Local vs. Turso)**:
> * **Servidores Persistentes (VPS, Hostinger, cPanel com Node, PM2, Docker)**: O SQLite local (`better-sqlite3`) funciona perfeitamente em produção. Basta deixar a variável `DATABASE_URL` em branco e os dados serão salvos de forma persistente no arquivo definido em `DATABASE_PATH`.
> * **Plataformas Serverless (Vercel, Netlify, etc.)**: Devido ao sistema de arquivos efêmero dessas plataformas (instâncias temporárias que deletam dados locais ao entrar em standby), o uso do **Turso (`DATABASE_URL`) é obrigatório** em produção para evitar a perda de dados.

---

## 🔐 2. Credenciais de Admin

* **`ADMIN_USERNAME`**: Usuário principal para login no painel administrativo (padrão: `admin`).
* **`ADMIN_PASSWORD`**: Senha do usuário administrador.

> [!NOTE]
> **Validação de Força de Senha e Sincronização**:
> * **Comportamento no Startup**: Se a senha configurada em `ADMIN_PASSWORD` no `.env` não atender aos requisitos de segurança (menos de 12 caracteres, etc.), o servidor registrará avisos/erros no console, mas **não** abortará a execução. Isso garante que a aplicação continue online e acessível mesmo com configurações temporárias.
> * **Resiliência a Redepolys**: Para evitar que atualizações automáticas de código (redeploy) apaguem alterações de senha feitas diretamente através do Painel de Administração (`/admin/settings`), o sistema rastreia o parâmetro `last_env_password` no banco de dados. 
> * **Atualização via `.env`**: A senha do banco de dados só será atualizada no startup se você alterar explicitamente o valor de `ADMIN_PASSWORD` no arquivo `.env` para um valor diferente do último sincronizado. Caso contrário, a senha alterada pelo painel administrativo será mantida de forma segura.

---

## 🧠 3. Integração de IA (Google Gemini)

* **`GEMINI_API_KEY`**: Chave de API do Google AI Studio para recursos inteligentes (como resumos e importadores automáticos).
* **`GEMINI_API_MODEL`**: Modelo do Gemini a ser utilizado (recomendado: `gemini-2.5-flash`).

---

## 🔗 4. Integração com o Backend Adm (Funil de Vendas)

* **`IMPORT_API_KEY`**: Chave compartilhada com o backend Adm (igual a `CLUBE_IMPORT_KEY` no Adm). Protege as rotas de importação (`/api/import/product`, `/api/import/nurture`) e é usada pelo Adm para assinar os **tokens de acesso do player de curso** (HMAC-SHA256, TTL 30 dias) decorando o `external_link` dos produtos.
* **`BACKEND_URL`**: URL pública do backend Adm (ex: `https://dezafiraadm-production.up.railway.app`). Usada pela área de membros para montar links de entrega do player de curso.

---

## 💳 5. Meios de Pagamento (Asaas)

O blog utiliza a integração com o **Asaas** para assinaturas premium, área de membros e venda de produtos avulsos.

Todas as credenciais do Asaas são configuradas e gerenciadas de forma segura diretamente através do **Painel de Administração** (em `/admin/settings` > aba correspondente), não sendo necessário definir nenhuma variável de ambiente no arquivo `.env` para o processamento de pagamentos.

---

## ☁️ 6. Cloudinary (Armazenamento de Mídia)

Para uploads eficientes das capas de posts, materiais e produtos:
* **`CLOUDINARY_CLOUD_NAME`**: Nome da sua conta (Cloud Name) no painel do Cloudinary.
* **`CLOUDINARY_API_KEY`**: Chave de API do Cloudinary.
* **`CLOUDINARY_API_SECRET`**: Segredo de API do Cloudinary para assinatura de requisições de upload seguras.

---

## 🌐 7. Configurações de Sistema do SvelteKit

* **`SITE_URL`**: Endereço base da sua aplicação (ex: `https://dailyitgirl.com`). Usado para gerar sitemaps, RSS feeds e caminhos de redirecionamento absoluto de webhooks.
* **`BODY_SIZE_LIMIT`**: Limite de tamanho máximo permitido para o payload de requisições POST no servidor (ex: `10485760` para 10 MB). Necessário para uploads de imagens e materiais de maior tamanho no painel administrativo.

---

## 📁 8. Uploads Persistentes (Hostinger / Git-deploys)

Se você utiliza sistemas de implantação baseados em Git que realizam clones limpos ou apagam arquivos não monitorados (como o painel Node.js da **Hostinger**), os arquivos locais enviados pela administração na pasta `static/uploads` podem ser apagados a cada novo deploy.

Para evitar isso, configure o parâmetro abaixo:

* **`PRODUCT_UPLOADS_DIR`**: O caminho absoluto no servidor de hospedagem onde os arquivos de produtos digitais serão armazenados permanentemente (ex: `/home/u123456789/domains/danisaints.com/uploads`). 
  * Quando esta variável está definida, novos produtos carregados no painel administrativo são armazenados de forma persistente nesta pasta externa ao repositório git.
  * O sistema possui **retrocompatibilidade**: se um arquivo não for encontrado na pasta externa, ele fará a busca automática na pasta `static` padrão do projeto.

