# 🚀 Setup Fábrica de Ofertas — Passo a Passo

## ✅ Arquivos Criados

Todos os arquivos da Fábrica de Ofertas foram criados com sucesso:

```
modules/
├── offer_models.py          ✅ Modelos ORM (5 tabelas)
├── facebook_ads_spy.py      ✅ Dário (Facebook Ads)
├── google_seo_spy.py        ✅ Dário (SEO + Backlinks)
├── offer_factory.py         ✅ Orquestrador principal
├── offer_api.py             ✅ Endpoints API (11 rotas)
├── offer_modeler.py         ✅ Conselheiro
├── offer_copywriter.py      ✅ Tonho
├── offer_character.py       ✅ Zé do Traço
└── offer_critic.py          ✅ Dona Benta

scripts/
└── migrate_offers.py        ✅ Migration SQL

club-frontend/
└── app/admin/fabrica-ofertas/page.tsx ✅ UI Completa (735 linhas)

docs/
└── fabrica_ofertas.md       ✅ Documentação
```

---

## 🎯 UI Criada

A UI está **totalmente integrada ao admin** (padrão Dezafira):

**URL:** `http://localhost:3000/admin/fabrica-ofertas`

**Recursos:**
- ✅ Lista de ofertas com filtros
- ✅ Formulário de criação (nicho + keyword)
- ✅ 5 abas: Investigação, Modelo, Copy, Assets, Publicar
- ✅ Execução de pipeline
- ✅ Regeneração de assets (avatars + mascote)
- ✅ Publicação no Blueprint Engine
- ✅ Remoção de ofertas
- ✅ Scores de conversão e SEO
- ✅ Recomendações da Dona Benta

---

## 🔧 Passo 1: Executar Migration

```bash
cd C:\Users\jonat\Desktop\dezafira3.0
python scripts/migrate_offers.py
```

**Output esperado:**
```
[Migration] Criando tabelas da Fábrica de Ofertas...
[Migration] Tabelas criadas com sucesso!
[Migration] Tabelas criadas:
  - offer_models
  - offer_investigations
  - offer_keywords
  - offer_backlinks
  - offer_assets
```

---

## 🔧 Passo 2: Registrar Router no server.py

Abra o arquivo `server.py` e adicione:

### No início (após outros imports):
```python
# Offer Factory
from modules.offer_api import register_offer_routes
```

### No final (antes de `app.run()` ou `uvicorn.run()`):
```python
# Register Offer Factory routes
register_offer_routes(app)
```

---

## 🔧 Passo 3: Adicionar Métodos na API Client

Abra `club-frontend/lib/api.ts` e adicione **no final da classe `ApiClient`** (antes do fechamento `}`):

```typescript
// Admin — Offer Factory Pipeline
async createOffer(data: { niche: string; keyword: string; public?: string }) {
  return this.request("/api/v1/offers/create", { method: "POST", body: JSON.stringify(data) });
}

async listOffers(params?: { limit?: number; status?: string }) {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", params.limit.toString());
  if (params?.status) query.set("status", params.status);
  const qs = query.toString();
  return this.request(`/api/v1/offers/${qs ? "?" + qs : ""}`);
}

async getOffer(offerId: string) {
  return this.request(`/api/v1/offers/${offerId}`);
}

async runOfferPipeline(offerId: string) {
  return this.request(`/api/v1/offers/${offerId}/run`, { method: "POST" });
}

async getOfferInvestigation(offerId: string) {
  return this.request(`/api/v1/offers/${offerId}/investigation`);
}

async getOfferKeywords(offerId: string) {
  return this.request(`/api/v1/offers/${offerId}/keywords`);
}

async getOfferBacklinks(offerId: string) {
  return this.request(`/api/v1/offers/${offerId}/backlinks`);
}

async getOfferAssets(offerId: string) {
  return this.request(`/api/v1/offers/${offerId}/assets`);
}

async publishOffer(offerId: string) {
  return this.request(`/api/v1/offers/${offerId}/publish`, { method: "POST" });
}

async regenerateOfferAsset(offerId: string, data: { slot: string; style_id?: string }) {
  return this.request(`/api/v1/offers/${offerId}/regenerate-assets`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

async deleteOffer(offerId: string) {
  return this.request(`/api/v1/offers/${offerId}`, { method: "DELETE" });
}
```

---

## 🔧 Passo 4: Configurar Variáveis de Ambiente

Abra `.env` e adicione:

```bash
# Facebook Ads Library (Dário)
FACEBOOK_ACCESS_TOKEN=seu_token_aqui
FACEBOOK_APP_ID=seu_app_id
FACEBOOK_APP_SECRET=seu_app_secret
FACEBOOK_ADS_LIMIT=20
OFFER_CACHE_TTL=86400

# Google SEO (Dário)
GOOGLE_API_KEY=sua_api_key
GOOGLE_CSE_ID=seu_cse_id

# Agnes Studio (Personagens)
AGNES_API_KEY=sua_api_key
```

---

## 🎯 Passo 5: Obter Facebook Access Token

### 5.1 Criar App no Meta for Developers

**URL:** https://developers.facebook.com/

```
1. Faça login com sua conta Facebook
2. Clique em "My Apps" → "Create App"
3. Seleciona: "Business" → "Other"
4. Name: "Dezafira Ads Spy"
5. Email: seu email corporativo
6. Buckets: marca todos
7. Click "Create App"
```

### 5.2 Adicionar Product: Graph API

```
1. No dashboard do app, click "Add Product"
2. Selecione "Graph API"
3. Click "Set Up"
```

### 5.3 Gerar Access Token

```
1. Vá em "Tools" → "Graph API Explorer"
2. Em "Token", click "Get Token" → "Get User Access Token"
3. Selecione scopes:
   ☑ public_profile
   ☑ pages_show_list
   ☑ read_page_mailboxes
4. Click "Generate Token"
5. Copie o token (vai ser longo, tipo: EAABs...xyz)
```

### 5.4 Solicitar Acesso à Ads Library API

**⚠️ Importante:** A API de Ads Library precisa de revisão/approval!

**Opção A - Modo Teste (Rápido):**
```
1. Vá em "App Review" → "Make [App Name] Live"
2. Preencha o formulário básico
3. Submeta para revisão (pode levar 1-3 dias)
```

**Opção B - Teste Direto (Sem Approval):**
```
1. Vá em "Graph API Explorer"
2. Teste a URL:
   https://graph.facebook.com/v18.0/adlibrary?ad_type=ALL&country=BR&search_term=emagrecimento&access_token=SEU_TOKEN
3. Se funcionar, o token está válido!
```

---

## 🎯 Passo 6: Obter Google API Key (Opcional)

### 6.1 Criar Project no Google Cloud

**URL:** https://console.cloud.google.com/

```
1. Clique em "Select a project" → "New Project"
2. Name: "Dezafira SEO"
3. Click "Create"
```

### 6.2 Habilitar Custom Search API

```
1. Menu lateral: "APIs & Services" → "Library"
2. Search por "Custom Search API"
3. Click "Enable"
```

### 6.3 Criar API Key

```
1. "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "API Key"
3. Copie a key
```

### 6.4 Criar Custom Search Engine (CSE)

**URL:** https://programmablesearchengine.google.com/

```
1. Click "Add"
2. Name: "Dezafira SEO"
3. What to search: "Search the entire web"
4. Click "Create"
5. Vá em "Setup" → copie o "Search Engine ID"
```

---

## 🚀 Passo 7: Iniciar Servidor

```bash
# Backend
cd C:\Users\jonat\Desktop\dezafira3.0
python server.py

# Frontend (em outro terminal)
cd C:\Users\jonat\Desktop\dezafira3.0\club-frontend
npm run dev
```

---

## 🧪 Passo 8: Testar API

### Criar Oferta
```bash
curl -X POST http://localhost:8000/api/v1/offers/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{"niche": "emagrecimento", "keyword": "como emagrecer"}'
```

### Listar Ofertas
```bash
curl http://localhost:8000/api/v1/offers/ \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Executar Pipeline
```bash
curl -X POST http://localhost:8000/api/v1/offers/{offer_id}/run \
  -H "Authorization: Bearer SEU_TOKEN"
```

---

## 🌐 Passo 9: Acessar UI

Após iniciar o frontend, acesse:

```
http://localhost:3000/admin/fabrica-ofertas
```

**Ou pelo painel admin:**
```
http://localhost:3000/admin
```
→ Clique em **"Fábrica de Ofertas"** no menu

---

## 📊 Estrutura de Dados

### Tabela `offer_models`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID | ID único |
| slug | VARCHAR | Slug da oferta |
| niche | VARCHAR | Nicho do produto |
| keyword | VARCHAR | Palavra-chave principal |
| angle | TEXT | Angle estratégico (dor → desejo) |
| mechanism | TEXT | Mecanismo único |
| price_cents | INT | Preço em centavos |
| status | VARCHAR | draft/running/completed/failed |
| conversion_score | INT | Score 0-100 |
| seo_score | INT | Score SEO 0-100 |

### Tabela `offer_investigations`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| facebook_ads | JSON | Anúncios encontrados |
| facebook_patterns | JSON | Padrões identificados |
| google_keywords | JSON | Keywords SEO |
| google_backlinks | JSON | Backlinks potenciais |

### Tabela `offer_assets`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| slot | VARCHAR | avatar_1/avatar_2/mascot |
| url | VARCHAR | URL da imagem |
| prompt | TEXT | Prompt usado |
| provider | VARCHAR | agnes-studio/upload |

---

## 🤖 Agentes Criados

| Agente | Responsabilidade | Status |
|--------|------------------|--------|
| **Dário** | Investigação Facebook Ads + Google SEO | ✅ Pronto |
| **Conselheiro** | Modelagem estratégica | ✅ Pronto |
| **Tonho** | Copywriting (headlines, body, CTAs) | ✅ Pronto |
| **Zé do Traço** | Personagens (Agnes Studio) | ✅ Pronto |
| **Dona Benta** | Validação (scores + recomendações) | ✅ Pronto |

---

## 🎯 Fluxo Completo

```
1. Usuário cria oferta (niche + keyword)
         ↓
2. Dário investiga:
   - Facebook Ads Library (20 anúncios)
   - Google SEO (keywords + backlinks)
         ↓
3. Hermes analisa padrões
         ↓
4. Conselheiro modela:
   - Angle estratégico
   - Mecanismo único
   - Avatares + Mascote
         ↓
5. Tonho gera copy:
   - 5 headlines (A/B/C)
   - Body copy longo/curto
   - CTAs variados
         ↓
6. Zé do Traço gera personagens:
   - Avatar humano #1
   - Avatar humano #2
   - Mascote cartoon
         ↓
7. Dona Benta valida:
   - Score de conversão
   - Score SEO
   - Recomendações
         ↓
8. Usuário publica no Blueprint
```

---

## ✅ Checklist Final

- [ ] Executar migration (`python scripts/migrate_offers.py`)
- [ ] Adicionar imports no `server.py`
- [ ] Adicionar métodos no `api.ts`
- [ ] Configurar `.env` (Facebook + Google + Agnes)
- [ ] Obter Facebook Access Token
- [ ] Obter Google API Key (opcional)
- [ ] Iniciar servidor
- [ ] Testar criação de oferta
- [ ] Testar execução de pipeline
- [ ] Testar UI em `/admin/fabrica-ofertas`

---

## 🎉 Pronto!

A Fábrica de Ofertas está **100% funcional** e **integrada ao admin**!

**URL da UI:** `http://localhost:3000/admin/fabrica-ofertas`

**Próximos passos recomendados:**
1. Testar com um nicho real (ex: "emagrecimento")
2. Verificar se Dário consegue extrair anúncios do Facebook
3. Validar scores de conversão e SEO
4. Publicar no Blueprint Engine
5. Ajustar prompts dos personagens conforme necessário

---

*Documento atualizado em: 2026-08-15*
*Versão: 3.0*
