# Fábrica de Ofertas - Documentação Completa

## 🎯 Visão Geral

A **Fábrica de Ofertas** é um sistema completo de criação de ofertas digitais escaláveis, orquestrado por agentes IA com personalidades brasileiras.

### Agentes Envolvidos

| Agente | Função | Especialidade |
|--------|--------|---------------|
| **Dário** | Pesquisador | Facebook Ads (API Oficial + Obscura fallback) + Google SEO |
| **Seu Hermes** | Orquestrador | Análise estratégica |
| **Conselheiro** | Modelagem | Angle, mecanismo, avatares |
| **Tonho** | Copywriting | Headlines, corpo, CTAs |
| **Zé do Traço** | Design | Personagens (Agnes Studio) + Vídeo Apple (Remotion) |
| **Dona Benta** | Validação | Score de conversão + SEO |

---

## 📊 Arquitetura do Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FÁBRICA DE OFERTAS (Sequencial)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [USUÁRIO] Input: Nicho + Keyword + Público                          │
│                          ↓                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ [DÁRIO] FASE 1: INVESTIGAÇÃO COMPLETA                        │   │
│  │                                                              │   │
│  │   ┌─────────────────────┐    ┌─────────────────────┐         │   │
│  │   │ FACEBOOK ADS (20)   │    │  GOOGLE SEO (20)    │         │   │
│  │   │ • API Oficial ativa │    │ • Keywords top      │         │   │
│  │   │ • Obscura Fallback  │    │ • Backlinks potencia│         │   │
│  │   │ • CTAs vencedores   │    │ • Conteúdo relevante│         │   │
│  │   └─────────────────────┘    └─────────────────────┘         │   │
│  │                                                              │   │
│  │   OUTPUT: Relatório completo (JSON)                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ [SEU HERMES] FASE 2: ANÁLISE ESTRATÉGICA                     │   │
│  │  • Padrões dos anúncios vencedores                           │   │
│  │  • Oportunidades de SEO identificadas                        │   │
│  │  • Angle único (dor → desejo)                                │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ [CONSELHEIRO] FASE 3: MODELAGEM                              │   │
│  │  • Avatar humano #1 (demografia + psicografia)               │   │
│  │  • Avatar humano #2 (perfil alternativo)                      │   │
│  │  • Mascote (personalidade da marca)                          │   │
│  │  • Estrutura da oferta completa                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ [TONHO] FASE 4: COPYWRITING                                  │   │
│  │  • Headlines (5 variantes A/B/C)                             │   │
│  │  • Copy long/short/middle                                    │   │
│  │  • CTAs variados                                             │   │
│  │  • Keywords SEO + backlinks para artigos                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ [ZÉ DO TRAÇO] FASE 5: ASSETS VISUAIS (Agnes + Remotion)       │   │
│  │  • Avatar humano #1 (prompt gerado)                          │   │
│  │  • Avatar humano #2 (prompt gerado)                          │   │
│  │  • Mascote (prompt gerado)                                   │   │
│  │  • Vídeo Apple TV+ (Remotion 15s com transição de câmera)    │   │
│  │  • Botão "Upload" para substituir                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ [DONA BENTA] FASE 6: VALIDAÇÃO                               │   │
│  │  • Score de conversão (0-100)                                │   │
│  │  • Score SEO (palavras-chave, backlinks)                     │   │
│  │  • Recomendações de melhoria                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↓                                           │
│  OUTPUT: Enviado para o BLUEPRINT ENGINE                           │
│  └─ Todas as informações entram no blueprint como:                  │
│     • config.offer_model (avatar, angle, mecanismo)                │
│     • config.keywords (SEO + backlinks)                            │
│     • config.assets (avatares, mascote, produto)                   │
│     • config.copy (headlines, body, CTAs)                          │
│     • config.video (Vídeo Comercial Apple TV+ V14)                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Banco de Dados

### Tabelas Criadas

| Tabela | Descrição |
|--------|-----------|
| `offer_models` | Modelo principal da oferta |
| `offer_investigations` | Dados da investigação (FB + SEO) |
| `offer_keywords` | Keywords SEO identificadas |
| `offer_backlinks` | Backlinks potenciais |
| `offer_assets` | Assets visuais (avatares, mascote) |

### Migration

```bash
python scripts/migrate_offers.py
```

---

## 🔌 API Endpoints

### Criar Oferta
```http
POST /api/v1/offers/create
Content-Type: application/json

{
  "niche": "emagrecimento",
  "keyword": "como emagrecer",
  "public": "mulheres 25-45"
}
```

### Listar Ofertas
```http
GET /api/v1/offers/?limit=50&status=completed
```

### Detalhes da Oferta
```http
GET /api/v1/offers/{offer_id}
```

### Executar Pipeline
```http
POST /api/v1/offers/{offer_id}/run
```

### Investigações (Dário)
```http
GET /api/v1/offers/{offer_id}/investigation
GET /api/v1/offers/{offer_id}/keywords
GET /api/v1/offers/{offer_id}/backlinks
```

### Assets
```http
GET /api/v1/offers/{offer_id}/assets
POST /api/v1/offers/{offer_id}/regenerate-assets
{
  "slot": "avatar_1",
  "style_id": "moderno"
}
```

### Publicar
```http
POST /api/v1/offers/{offer_id}/publish
```

### Remover
```http
DELETE /api/v1/offers/{offer_id}
```

---

## 📁 Estrutura de Arquivos

```
modules/
├── offer_models.py          # Modelos ORM (5 tabelas)
├── offer_factory.py         # Orquestrador principal
├── offer_api.py             # Endpoints da API
├── offer_modeler.py         # Conselheiro
├── offer_copywriter.py      # Tonho
├── offer_character.py       # Zé do Traço
├── offer_critic.py          # Dona Benta
├── facebook_ads_spy.py      # Dário (Facebook Ads API + Scraper)
└── google_seo_spy.py        # Dário (SEO)

remotion-studio/
├── src/CinematicPromo.tsx   # Template de Vídeo Apple TV+ V14 (15 segundos)
├── src/Root.tsx             # Raiz de composições Remotion
└── remotion.config.ts       # Configurações do Rspack e Puppeteer

scripts/
└── migrate_offers.py        # Migration SQL

club-frontend/
└── app/admin/fabrica-ofertas/page.tsx  # UI da Fábrica
```

---

## 🔑 Variáveis de Ambiente

```bash
# Facebook Ads (Dário)
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

## 🚀 Como Usar

### 1. Executar Migration
```bash
cd C:\Users\jonat\Desktop\dezafira3.0
python scripts/migrate_offers.py
```

### 2. Iniciar Servidor
```bash
python server.py
```

### 3. Criar Oferta via API
```bash
curl -X POST http://localhost:8000/api/v1/offers/create \
  -H "Content-Type: application/json" \
  -d '{"niche": "emagrecimento", "keyword": "como emagrecer"}'
```

### 4. Executar Pipeline
```bash
curl -X POST http://localhost:8000/api/v1/offers/{offer_id}/run
```

### 5. Ver Resultados
```bash
curl http://localhost:8000/api/v1/offers/{offer_id}
```

---

## 🎨 Personagens (Avatares + Mascote)

### Avatar Humano #1
- **Gênero:** Masculino
- **Idade:** ~35 anos
- **Estilo:** Profissional, confiável, acessível
- **Uso:** Landing page principal, anúncios Facebook

### Avatar Humano #2
- **Gênero:** Feminino
- **Idade:** ~28 anos
- **Estilo:** Energética, confiante, inspiradora
- **Uso:** Anúncios Instagram, redes sociais

### Mascote
- **Estilo:** Cartoon 2D, flat design
- **Cores:** Vibrantes (laranja, amarelo, azul)
- **Uso:** Branding, interfaces, elementos visuais

---

## 📊 Scores de Validação

### Conversion Score (0-100)
- Angle claro (20pts)
- Mechanism definido (15pts)
- Promise clara (15pts)
- Headlines testáveis (20pts)
- Body copy completo (15pts)
- CTAs presentes (10pts)
- Avatares gerados (5pts)

### SEO Score (0-100)
- Meta title otimizado (20pts)
- Meta description presente (20pts)
- Keywords no meta (25pts)
- Keywords no body (20pts)
- Keywords nas headlines (15pts)

---

## ✅ Checklist de Implementação

- [x] Criar `modules/offer_models.py`
- [x] Criar `modules/facebook_ads_spy.py`
- [x] Criar `modules/google_seo_spy.py`
- [x] Criar `modules/offer_factory.py`
- [x] Criar `modules/offer_api.py`
- [x] Criar `modules/offer_modeler.py`
- [x] Criar `modules/offer_copywriter.py`
- [x] Criar `modules/offer_character.py`
- [x] Criar `modules/offer_critic.py`
- [x] Criar `scripts/migrate_offers.py`
- [x] Criar UI em `/admin/fabrica-ofertas`
- [x] Executar migration
- [x] Registrar router no server.py
- [x] Adicionar métodos na api.ts
- [x] Testar fluxo completo
- [x] Conectar com Blueprint Engine para geração de Vídeo Apple TV+ via Remotion

---

## 🎯 Próximos Passos

1. **Aprimorar prompts da apresentadora** na IA Agnes de acordo com novas tendências.
2. **Monitorar queries do Dário** via API Oficial com novas contas de anúncios do Facebook.
3. **Expandir biblioteca de templates Remotion** para outros formatos de comerciais além de Apple TV+.

---

*Documento atualizado em: 2026-08-15*
*Versão: 3.0 (Fase Remotion Apple TV+ & API Oficial)*
