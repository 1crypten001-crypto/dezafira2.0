# Guia de Instalação e Configuração Inicial

Este guia orienta no processo de clonagem, instalação de dependências e inicialização do banco de dados do Blog Whitelabel.

---

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:
* **Node.js** (Versão 18 ou superior)
* **npm** ou gerenciador de pacotes equivalente (yarn, pnpm)
* **Git**
* Uma conta na [Turso DB](https://turso.tech) (caso vá utilizar banco de dados na nuvem para produção)

---

## 🚀 Passos para Instalação

### 1. Clonar o Repositório
Abra seu terminal e execute o comando:
```bash
git clone <url-do-repositorio>
cd blog-svelte-sqlite
```

### 2. Instalar as Dependências
Instale todos os pacotes necessários do projeto:
```bash
npm install
```

### 3. Configurar Variáveis de Ambiente
Duplique o arquivo `.env.example` para criar o seu arquivo `.env`:
```bash
cp .env.example .env
```
Abra o arquivo `.env` e configure suas variáveis (consulte o [Guia de Configuração](configuration.md) para detalhes de cada chave).

---

## 🗄️ Inicialização do Banco de Dados

O blog suporta **SQLite local** (para desenvolvimento) e **Turso/LibSQL** (para produção). O processo de estruturação e criação de tabelas é **100% automático e auto-recuperável** (self-healing), ocorrendo na primeira inicialização do servidor.

> [!IMPORTANT]
> **Compatibilidade de Hospedagem (SQLite Local vs. Turso)**:
> * **SQLite Local**: Pode ser usado em produção se você hospedar em um servidor persistente (como VPS, PM2, Docker, cPanel ou servidor Node persistente).
> * **Turso**: É obrigatório se você hospedar em plataformas serverless (como Vercel ou Netlify), onde o sistema de arquivos local é reiniciado constantemente.

### Opção A: SQLite Local
1. No arquivo `.env`, aponte a variável `DATABASE_PATH` para o caminho do arquivo local (padrão: `./blog.db`).
2. O arquivo do banco e todas as tabelas básicas, anúncios, área de membros e configurações serão criados de forma transparente no primeiro acesso ao site.

### Opção B: Turso DB (Produção / VPS)
1. Crie um banco de dados no Turso usando a CLI do Turso ou console web:
   ```bash
   turso db create meu-blog
   ```
2. Obtenha a URL de conexão e o Token de autenticação:
   ```bash
   turso db show meu-blog
   turso db tokens create meu-blog
   ```
3. Preencha os campos correspondentes no `.env`:
   ```env
   DATABASE_URL=libsql://meu-blog-usuario.turso.io
   DATABASE_AUTH_TOKEN=seu_token_aqui
   ```
4. Inicie o servidor. O blog detectará que o banco está vazio, estruturará as tabelas e semeará o usuário administrador e as opções gerais automaticamente. Não é necessário executar comandos manuais no terminal.

---

## 💻 Executando o Projeto

### Modo de Desenvolvimento
Para iniciar o servidor local com hot-reloading ativo:
```bash
npm run dev
```
O projeto estará disponível por padrão em `http://localhost:5173`.

### Compilação de Produção
Para compilar e gerar a build otimizada da aplicação:
```bash
npm run build
```
Para testar a build de produção localmente:
```bash
npm run preview
```
