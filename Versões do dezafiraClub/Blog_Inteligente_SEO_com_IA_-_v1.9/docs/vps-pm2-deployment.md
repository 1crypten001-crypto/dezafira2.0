# Guia de Implantação em VPS com PM2 (Hostinger, DigitalOcean, etc.)

Este guia descreve os passos recomendados para implantar o seu Blog Whitelabel em um servidor virtual privado (**VPS**) utilizando o **PM2** para gerenciar o processo da aplicação em segundo plano com persistência em caso de reinicialização do sistema.

---

## 📋 Pré-requisitos na VPS

Antes de começar, acesse sua VPS via SSH e garanta que as ferramentas básicas estão instaladas:

1.  **Node.js (v18 ou superior)** e **NPM**:
    ```bash
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    ```
2.  **Git**:
    ```bash
    sudo apt-get update
    sudo apt-get install git -y
    ```
3.  **PM2 (Process Manager)** instalado globalmente:
    ```bash
    sudo npm install -g pm2
    ```

---

## 🚀 Passo a Passo da Instalação

### 1. Enviar o Código para a VPS
Você pode clonar o código diretamente do seu repositório Git ou extrair os arquivos do ZIP na VPS:
```bash
git clone https://github.com/seu-usuario/seu-repositorio-blog.git
cd seu-repositorio-blog
```

### 2. Instalar Dependências
Rode a instalação das dependências do Node:
```bash
npm install --omit=dev
```
*(O parâmetro `--omit=dev` economiza espaço e tempo instalando apenas pacotes necessários para a execução em produção).*

### 3. Configurar Variáveis de Ambiente (`.env`)
Duplique o arquivo `.env.example` para gerar o `.env` de produção:
```bash
cp .env.example .env
```
Edite o arquivo `.env` com um editor de texto (como o `nano`):
```bash
nano .env
```

#### Requisitos Importantes no `.env`:
*   **`ADMIN_PASSWORD`**: Defina uma **senha forte** (mínimo 12 caracteres, contendo pelo menos uma letra maiúscula, uma minúscula, um número e um caractere especial). O sistema valida essa senha no startup para proteger seu painel contra invasores.
*   **`DATABASE_PATH`**: Deixe como `./blog.db` para utilizar o SQLite local persistente.
*   **`SITE_URL`**: Coloque o domínio do seu blog (ex: `https://meublog.com`).
*   **`ORIGIN`**: A URL de acesso ao site (ex: `https://meublog.com` ou `http://92.246.131.72`). **Obrigatório** para evitar o erro `403 Forbidden` nos formulários de login devido à proteção CSRF do SvelteKit.

> [!WARNING]
> **NODE_ENV**: Não defina `NODE_ENV=production` dentro do seu `.env` pois isso pode travar ou falhar o build do Vite silenciosamente. O SvelteKit já compila em modo de produção por padrão. Em vez disso, passe a variável direto ao rodar a aplicação com o PM2.

Salve o arquivo (`Ctrl + O`, depois `Enter`, e feche com `Ctrl + X`).

### 4. Compilar o Projeto (Build)
Se você estiver atualizando uma instalação existente, é recomendado limpar builds anteriores e parar processos legados para evitar processos órfãos:
```bash
# Limpar caches antigos
rm -rf .svelte-kit build

# Rodar a compilação limpa
npm run build
```

---

## ⚙️ Gerenciamento com PM2

O **PM2** garante que o blog continue rodando em segundo plano mesmo depois que você fechar a janela do terminal SSH.

### 1. Iniciar a Aplicação com PM2
O SvelteKit compilado com o adaptador para Node.js inicia através do arquivo `build/index.js`.
Inicie o processo definindo a porta padrão desejada (geralmente porta `3000`) e configurando o `NODE_ENV`:

```bash
PORT=3000 NODE_ENV=production pm2 start build/index.js --name "blog-inteligente"
```

Alternativamente, você pode usar um arquivo `ecosystem.config.cjs` na raiz:
```javascript
module.exports = {
  apps: [{
    name: "blog-inteligente",
    script: "build/index.js",
    env: {
      PORT: "3000",
      NODE_ENV: "production"
    }
  }]
};
```
E iniciar com: `pm2 start ecosystem.config.cjs`.

### 2. Configurar a Inicialização Automática no Boot da VPS
Para garantir que o blog inicie sozinho caso a VPS seja reiniciada física ou eletricamente:

1.  Gere o script de inicialização do sistema:
    ```bash
    pm2 startup
    ```
2.  O terminal exibirá um comando longo que você deve copiar e colar (geralmente começa com `sudo env PATH=...`). Execute esse comando copiado.
3.  Salve a lista de processos ativos no PM2 para que ele lembre do blog no próximo boot:
    ```bash
    pm2 save
    ```

### 3. Comandos Úteis do PM2:
*   **Verificar status do blog:** `pm2 status`
*   **Visualizar logs em tempo real:** `pm2 logs blog-inteligente`
*   **Reiniciar o blog (após atualizações de código):** `pm2 restart blog-inteligente`
*   **Parar a execução:** `pm2 stop blog-inteligente`

---

## 🔒 Nginx e SSL (Reverso Proxy recomendado)

Embora o blog funcione diretamente na porta `3000`, a prática padrão de mercado é rodar o **Nginx** na porta `80` (HTTP) e `443` (HTTPS) servindo de intermediário e criptografando a conexão com certificado SSL gratuito da Let's Encrypt.

### 1. Instalar Nginx
```bash
sudo apt install nginx -y
```

### 2. Configurar o Bloco do Servidor (Server Block)
Edite a configuração do Nginx:
```bash
sudo nano /etc/nginx/sites-available/meublog.com
```

Cole a configuração abaixo (substituindo `meublog.com` pelo seu domínio):
```nginx
server {
    listen 80;
    server_name meublog.com www.meublog.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        client_max_body_size 100M;
    }
}
```

Ative o arquivo e reinicie o Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/meublog.com /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### 3. Gerar Certificado SSL Grátis (HTTPS)
Instale o Certbot da Let's Encrypt e configure o SSL automático para seu domínio:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d meublog.com -d www.meublog.com
```
*(Siga as instruções na tela e escolha a opção de redirecionar automaticamente todo tráfego HTTP para HTTPS).*
