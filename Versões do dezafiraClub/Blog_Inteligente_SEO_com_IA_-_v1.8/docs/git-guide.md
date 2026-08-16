# Como Subir o Projeto no seu Repositório Git (Guia do Cliente)

Este guia orienta o cliente/desenvolvedor que adquiriu o pacote do blog sobre como inicializar o controle de versão Git e subir o código-fonte para o seu próprio repositório (ex: GitHub, GitLab ou Bitbucket) de maneira limpa e segura.

---

## 🛡️ Segurança por Padrão (.gitignore)

O pacote ZIP de distribuição já vem pré-configurado com o arquivo `.gitignore` na raiz. Isso garante que arquivos sensíveis ou desnecessários **nunca sejam enviados acidentalmente** para o seu repositório Git público ou privado.

Os seguintes itens já estão ignorados por padrão:
*   `node_modules/` (Dependências instaladas localmente)
*   `.env` (Chaves de API, credenciais e tokens privados)
*   `.svelte-kit/` & `build/` (Arquivos temporários e build de compilação)
*   `blog.db` & `*.db` (Bancos de dados SQLite locais de teste)
*   `*.zip` (Pacotes compactados gerados na raiz)

> [!WARNING]
> **Mantenha o Repositório Privado**: Como este é um produto whitelabel comercial, recomendamos fortemente que você crie o seu repositório no GitHub/GitLab como **Privado** (`Private`), limitando o acesso ao código apenas a pessoas autorizadas por você.

---

## 🚀 Passo a Passo para Inicialização e Envio

Siga as etapas abaixo a partir do terminal da pasta onde o ZIP foi extraído:

### 1. Iniciar o repositório Git local
Inicie o Git na raiz da pasta extraída do projeto:
```bash
git init
```

### 2. Criar o repositório no seu provedor Git
1. Acesse sua conta no **GitHub** (ou serviço equivalente).
2. Crie um novo repositório com o nome desejado (ex: `meu-blog-inteligente`).
3. Marque a visibilidade como **Privada** (`Private`).
4. **Importante**: Não selecione as opções de adicionar `README.md`, `.gitignore` ou licença (pois o projeto já possui esses arquivos).
5. Copie a URL HTTPS ou SSH do repositório gerado (ex: `https://github.com/seu-usuario/meu-blog-inteligente.git`).

### 3. Vincular o repositório remoto
No terminal do seu computador, vincule a pasta local ao link copiado:
```bash
git remote add origin https://github.com/seu-usuario/meu-blog-inteligente.git
```

### 4. Criar o primeiro Commit
Adicione todos os arquivos permitidos ao index do Git e crie o commit inicial:
```bash
git add .
git commit -m "feat: commit inicial do blog whitelabel"
```

### 5. Enviar para a nuvem
Defina a branch padrão como `main` (ou `master`) e envie os arquivos:
```bash
git branch -M main
git push -u origin main
```

---

## 🔄 Como Atualizar Posteriormente

Caso você faça edições nos posts, estilos CSS ou configurações de código locais e queira atualizar o seu repositório:

1. Adicione as novas modificações:
   ```bash
   git add .
   ```
2. Crie um commit identificando o que foi alterado:
   ```bash
   git commit -m "style: ajuste de cores do layout e fontes"
   ```
3. Envie para o GitHub:
   ```bash
   git push
   ```

> [!TIP]
> Toda vez que você for configurar o projeto em uma nova máquina ou servidor usando o seu repositório Git clonado, lembre-se de rodar `npm install` para instalar as dependências e recriar o arquivo `.env` baseado no arquivo `.env.example` fornecido na raiz.
