# 🚀 Deploy DezafiraClube - Status Atual

> **Última atualização:** 06/08/2026

---

## 📊 Status dos Serviços

| Serviço | URL | Status |
|---------|-----|--------|
| **dezafiraclube** | https://www.dezafira.com.br | ✅ Funcionando |
| **dezafiraadm** (API) | https://dezafiraadm-production.up.railway.app | ✅ Funcionando |
| **dezafiraadm-frontend** | https://adm.dezafira.com.br | ✅ Deploy OK (aguarda DNS) |
| **libsql-server** | libsql-server.railway.internal:8080 | ✅ Funcionando |

---

## ✅ O que já está configurado

### Infraestrutura
- Railway CLI logado (Pedro Kalelivia)
- Projeto "shimmering-possibility" linkado
- Serviços criados e deployados
- Volume 5GB para libsql-server
- Healthchecks funcionando

### Variáveis de Ambiente (dezafiraclube)
```
DATABASE_URL=http://libsql-server.railway.internal:8080
NEXT_PUBLIC_API_URL=https://dezafiraadm-production.up.railway.app
RESEND_API_KEY=re_sua_chave_aqui
RESEND_FROM_EMAIL=contato@dezafira.com.br
RESEND_FROM_NAME=Dezafira Club
ADMIN_USERNAME=jonatasprojetos2013@gmail.com
ADMIN_PASSWORD=sua_senha
```

### Branding Aplicado
- Logo: "D" roxo + "Dezafira Club"
- Cores: 60% azul escuro / 30% neutro / 10% roxo
- Dark mode: fundo #080d19 (quase preto)
- Header com links "Premium" e "Login"
- Footer com branding DezafiraClube

---

## ⏳ Pendente (fazer manualmente)

### 1. Ativar OTP no Admin
Acesse: `https://www.dezafira.com.br/admin/settings`
- Ative "Login via e-mail (OTP)"
- Ative "Cadastro de membros"
- Salve

### 2. Gerar Token CLI
Acesse: `https://www.dezafira.com.br/admin/cli`
- Clique em "Regenerar Token"
- Guarde o token gerado

### 3. Configurar Cloudinary (upload de imagens)
1. Crie conta em [cloudinary.com](https://cloudinary.com) (gratuito)
2. Vá em Account → API Keys
3. Me mande:
   - Cloud Name
   - API Key
   - API Secret

### 4. Domínio adm.dezafira.com.br
- CNAME record já criado: `adm` → `kb8ydjil.up.railway.app`
- Aguardando propagação DNS

---

## 🔧 Comandos Úteis

```bash
# Ver logs do dezafiraclube
railway logs --service dezafiraclube --project f3dec210-01c0-4364-801d-029a3c01aa46

# Verificar healthcheck
curl -s https://www.dezafira.com.br/healthz

# Ver variáveis de ambiente
railway variables --service dezafiraclube --project f3dec210-01c0-4364-801d-029a3c01aa46

# Deploy manual
railway up --service dezafiraclube --project f3dec210-01c0-4364-801d-029a3c01aa46
```

---

## 📁 Estrutura do Projeto

```
dezafira2.0/
├── Blog_Inteligente_SEO_com_IA_-_v1.8/  ← DezafiraClube (SvelteKit)
├── club-frontend/                        ← DezafiraADM Frontend (Next.js)
├── libsql-server/                        ← Banco libsql (Docker)
├── server.py                             ← Backend FastAPI
├── modules/database.py                   ← Camada de banco
└── docs/
    ├── deploy_dezafiraclube.md           ← Este arquivo
    ├── backup_restore_libsql.md          ← Backup/Restore
    └── setup_google_indexing.md          ← Google Search Console
```

---

*Desenvolvido por Dezafira Club - Agosto 2026*
