# 1Convite — produto absorvido na fábrica DezafiraADM

> Super app cristão ("Um APP sobre o Reino") — Bíblia narrada, matriz diária,
> arcade bíblico, trilha do reino, conselheiros IA. **Absorvido do repo
> `spcompensa-glitch/1convite` para dentro do ecossistema Dezafira** (conteúdo
> no banco do ADM, PWA servido pelo ADM, domínio dedicado `1convite.com.br`).

## Arquitetura (como ficou)

```
1convite.com.br  (DNS → serviço dezafiraadm no Railway)
      │  Host header → middleware de Host-routing no server.py
      ▼
DezafiraADM (FastAPI)
  ├─ /app/1convite            → PWA servido pelo gerador (ou bundle estático)
  ├─ /api/v1/convite/*        → API de conteúdo (Bíblia, matriz, trilhas, jogos)
  ├─ /api/v1/* (compat)       → contrato EXATO da API Express original (este módulo)
  └─ /api/v1/chatgpt/*        → proxy → sidecar LWC (Conselheiros IA)
```

- **Conteúdo** (Bíblia ACF ~31k versículos, matriz 365, trilhas, jogos, trilha
  do reino) vive nas tabelas `convite_*` do banco do ADM — populadas por
  `scripts/seed_convite.py`.
- **Estado de usuário** começa do ZERO (decisão do dono): `convite_user_progress`
  nasce vazio/sob demanda; contatos e histórico começam vazios.
- **Conselheiros IA** mantêm a chave ChatGPT original via LWC — o FastAPI faz
  proxy para o sidecar Node (`backend-lwc/`).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `frontend/` | PWA React 19 + Vite (App.jsx 5.9k linhas, componentes, dados dos jogos, mídias) |
| `frontend/android/` | Build Capacitor/Android (referência — o build APK falhava no Railway) |
| `backend/` | Backend Express original (referência do contrato da API — não roda mais) |
| `backend-lwc/` | **Sidecar Node mínimo**: só o handler Login-with-ChatGPT (roda de verdade) |
| `skill-sites-animados/` | Skill de sites animados (capacidade reutilizável da fábrica) |

## Como buildar o PWA (onde houver Node)

```bash
bash scripts/build_convite_pwa.sh   # npm install → vite build → web/1convite/dist
```

> ✅ **Já buildado** — `web/1convite/dist/` contém o bundle (SPA 626KB JS + CSS +
> mídias, ~52MB). O middleware de Host-routing serve esse bundle na raiz de
> `1convite.com.br` (verificado: index.html, /assets/*, sw.js, SPA fallback,
> API pass-through — TODOS OK). Rebuild quando o App.jsx mudar.

O bundle é entregue pelo próprio ADM: o middleware detecta `web/1convite/dist/index.html`
e serve na raiz do domínio dedicado. Alternativa (sem dist/): o PWA gerado
dinamicamente em `/app/1convite` (fallback).

> ⚠️ O app chama a API em `API_BASE = /api/v1` (mesmo host). Ajuste o fallback
> hardcoded em `App.jsx` (linha ~1128) se quiser apontar explicitamente para o
> domínio do ADM.

## Como rodar o sidecar LWC (Conselheiros IA)

```bash
cd web/1convite/backend-lwc
npm install
LWC_SECRET=<mesmo segredo de antes> PORT=3111 npm start
```

E no backend do ADM:

```bash
LWC_SIDECAR_URL=http://127.0.0.1:3111 python server.py
```

Sem `LWC_SIDECAR_URL`, `/api/v1/chatgpt/*` responde `503` JSON — o PWA mostra
"Conselheiros offline" sem quebrar o app.

## Conteúdo preservado (fonte da verdade no banco do ADM)

- 📖 Bíblia ACF completa (31.106 versículos) — `convite_biblia`
- 🗓️ Matriz diária 365 dias — `convite_matriz_diaria`
- 🛤️ Trilhas de crescimento (4 temas × 30 dias) — `convite_trilhas`
- 🎮 Arcade bíblico: quiz (30), charadas (15), forca (30), caça-palavras (37) — `convite_jogos_*`
- 📚 Trilha do Reino (plano 18m/540 e 12m/365 + marcos + ações) — `convite_trilha_reino*`
- 📖 Dicionário teológico — `convite_dicionario`

Origem original: repo `spcompensa-glitch/1convite` (README em `README-original.md`).
