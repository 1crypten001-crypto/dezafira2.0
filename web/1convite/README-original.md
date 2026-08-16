# 1Convite — Ecossistema Completo

Super app cristão que integra a Palavra de Deus, interatividade, ferramentas de IA e criatividade em um só lugar.

## Status

| Serviço | URL | Status |
|---|---|---|
| Frontend | https://1convite.com.br | Ativo |
| Backend API | https://invigorating-expression-production-d4df.up.railway.app | Ativo |
| APK Android | GitHub Actions → artifact `1convite-apk` | Automático |
| Banco de Dados | PostgreSQL (Railway Plugin) | Ativo |

## Funcionalidades

- **Bíblia Sagrada:** Leitura completa com pesquisa por texto, áudio, livros, capítulos e versículos. Dados importados do API da Bíblia on-line.
- **Desafio do Dia:** Reflexão diária com código verbal, meditação guiada (áudio) e progresso em 365 dias.
- **Conselheiros IA:** Hub interativo com personagens bíblicos guiados por ChatGPT (LWC). Jesus Cristo desbloqueado por padrão; outros conselheiros desbloqueáveis com moedas.
- **Trilhas de Crescimento:** Séries temáticas (ex: Gratidão, Oração, Perdão) com versículos, reflexões e ações práticas ao longo de vários dias.
- **Trilha do Reino:** Plano de leitura bíblica cronológico em 18 ou 12 meses. Streak de dias seguidos, Talentos (moedas), devotionais diários, 1Convite Prático, mapa visual com 9 marcos de fé.
- **Arcade Bíblico:**
  - **Quiz:** 30 questões (10 por nível), temporizador dinâmico, pontuação progressiva.
  - **Quem Sou Eu? (Charadas):** 15 perguntas com dicas progressivas.
  - **Caça-Palavras:** Grid 10×10 / 12×12 / 14×14, palavras em 8 direções (horizontal, vertical e diagonal), normalização de acentos.
  - **Forca:** Teclado virtual, 8/6/4 vidas por nível, lista filtrada por dificuldade.
- **Lojinha & Economia:** Moedas ganhas por leitura, jogos e desafios. Compra de stickers, fontes, fundos e desbloqueio de conselheiros IA premium.
- **Studio de Cards:** Ferramenta estilo Canva para criar convites e cartões com fontes premium e fundos exclusivos.
- **Landing Page (Techla):** Página de captação de leads com formulário de WhatsApp e webhook integrado.
- **PWA:** Service Worker registrado, manifesto instalável, modo offline parcial.

## Arquitetura

Monorepo com dois serviços independentes deployados no Railway:

```
1convite/
├── frontend/                    # React + Vite (SPA)
│   ├── src/                     # Código-fonte React
│   │   ├── App.jsx              # Componente principal (monolito ~5700 linhas)
│   │   ├── index.css            # Tokens de design, temas, dark mode
│   │   ├── main.jsx             # Entry point
│   │   ├── components/          # LandingPage, Onboarding, trail/
│   │   ├── data/arcadeData.js   # Dados dos jogos
│   │   ├── data/trailData.js    # Plano bíblico cronológico (540/365 dias)
│   │   └── services/            # webhookService.js
│   ├── public/                  # Assets estáticos, áudios, imagens, frames
│   │   ├── favicon.png          # Favicon (chama sobre livro)
│   │   ├── LOGO.png             # Logo (chama, sem texto)
│   │   ├── LOGOMARCA.png        # Logomarca completa
│   │   ├── manifest.json        # Manifest PWA
│   │   ├── sw.js                # Service Worker (self-destructing)
│   │   ├── icons.svg            # Ícones SVG
│   │   └── intro_scroll/        # Frames da intro scroll
│   ├── android/                 # Capacitor Android (APK nativo)
│   ├── vite.config.js           # Proxy /api → localhost:3001 (dev)
│   ├── capacitor.config.json    # Configuração Capacitor
│   ├── railway.toml             # Config Railway (frontend)
│   └── package.json             # Deps: React, Vite, html2canvas
│
├── backend/                     # Express + PostgreSQL
│   ├── src/
│   │   ├── index.js             # Servidor Express (~1270 linhas, todas as rotas)
│   │   └── database/
│   │       ├── pool.js          # Conexão PostgreSQL (pg)
│   │       ├── migrations.js    # Runner de migrations
│   │       └── seed.js          # Seed do dicionário, trilhas e progresso
│   ├── migrations/
│   │   └── 001_initial.sql      # Schema completo (8 tabelas + índices GIN)
│   ├── import-bible.js          # Importador da Bíblia via API → PostgreSQL
│   └── package.json             # Deps: Express, pg, cors, dotenv, LWC
│
├── .github/workflows/
│   └── android.yml              # CI: build APK debug + upload artifact
│
├── package.json                 # Root: concurrently (dev, build, start)
├── .gitignore                   # node_modules, dist, .env, *.sqlite
└── README.md
```

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | React 19, Vite 5.4, Vanilla CSS, html2canvas |
| Backend | Express 5, Node.js >=20 |
| Banco | PostgreSQL 16 (Railway Plugin) |
| IA | ChatGPT via `@opencoredev/loginwithchatgpt-server` |
| Mobile | Capacitor 8 (Android, JDK 21) |
| Deploy Frontend | Railway (npx serve, static files) |
| Deploy Backend | Railway (Node.js) |
| CI/CD | GitHub Actions (APK build automático) |
| Proxy (dev) | Vite dev server → localhost:3001 |
| Proxy (prod) | Frontend aponta direto ao backend Railway (URL absoluta) |

## Variáveis de Ambiente

### Backend (Railway)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | Sim | URL de conexão PostgreSQL (Railway injeta automaticamente) |
| `FRONTEND_URL` | Sim | URL do frontend (ex: `https://1convite.com.br`) — usada no CORS |
| `PORT` | Não | Porta do servidor (default: 3001, Railway define automaticamente) |
| `LWC_SECRET` | Não | Secret para ChatGPT/LWC (tem fallback para dev) |

### Frontend (Railway)

Nenhuma variável necessária. O frontend aponta direto ao backend via URL absoluta.

## PWA (Progressive Web App)

| Asset | Arquivo | Descrição |
|---|---|---|
| Favicon | `public/favicon.png` | Chama sobre livro (ícone principal) |
| Logomarca | `public/LOGOMARCA.png` | Logo completa "chaminha PALAVRA VIVA" |
| Logo | `public/LOGO.png` | Ícone da chama (sem texto) |
| Manifest | `public/manifest.json` | Configuração PWA (ícones, cores, display) |
| Service Worker | `public/sw.js` | SW de limpeza de cache (self-destructing) |

Meta tags PWA no `index.html`: apple-touch-icon, theme-color, og:image, msapplication.

## Instalação e Execução

### Pré-requisitos
- Node.js >= 20
- PostgreSQL (local ou Railway plugin)

### Desenvolvimento (local)

```bash
# Clonar o repositório
git clone https://github.com/spcompensa-glitch/1convite.git
cd 1convite

# Instalar dependências (root + frontend + backend)
npm install
cd frontend && npm install && cd ..
cd backend && npm install && cd ..

# Criar arquivo .env no backend com DATABASE_URL
echo "DATABASE_URL=postgres://user:pass@localhost:5432/1convite" > backend/.env

# Rodar migrations e seed
npm run migrate
npm run seed
npm run import-bible

# Iniciar frontend e backend simultaneamente
npm run dev
```

- **Frontend:** http://localhost:5173
- **Backend:** http://localhost:3001

### Comandos Disponíveis (Root)

| Comando | Descrição |
|---|---|
| `npm run dev` | Inicia frontend + backend simultaneamente |
| `npm run dev:frontend` | Inicia apenas o frontend (Vite) |
| `npm run dev:backend` | Inicia apenas o backend (Express) |
| `npm run build` | Build de produção do frontend |
| `npm run start` | Inicia o backend em produção |
| `npm run migrate` | Roda migrations do PostgreSQL |
| `npm run seed` | Popula tabelas iniciais |
| `npm run import-bible` | Importa Bíblia completa para PostgreSQL |
| `npm run lint` | Lint do frontend (oxlint) |

## Deploy no Railway

### Serviço Backend
1. Criar serviço no Railway conectando ao repositório
2. **Root Directory:** `backend`
3. **Start Command:** `node src/index.js`
4. Adicionar plugin PostgreSQL (cria `DATABASE_URL` automaticamente)
5. Adicionar env var `FRONTEND_URL` → `https://1convite.com.br`
6. Após deploy, rodar no console: `npm run migrate && npm run seed && npm run import-bible`

### Serviço Frontend
1. Criar serviço no Railway conectando ao repositório
2. **Root Directory:** `frontend`
3. Nenhuma variável necessária
4. O `railway.toml` usa `npx serve -s dist -l 8080` para servir arquivos estáticos

## Build do APK (Android)

O workflow `.github/workflows/android.yml` roda automaticamente a cada push no `main`:

1. Instala dependências do frontend
2. Builda o Vite (`dist/`)
3. Sincroniza Capacitor (`npx cap sync android`)
4. Compila o APK com Gradle (JDK 21)
5. Faz upload como artifact GitHub Actions (download disponível por 30 dias)

Para baixar o APK: Actions → build mais recente → seção Artifacts → `1convite-apk`

## Banco de Dados (PostgreSQL)

### Tabelas

| Tabela | Descrição |
|---|---|
| `tb_matriz_diaria` | 365 dias de reflexão, código verbal, versículo, meditação |
| `tb_usuario_progresso` | Progresso do usuário (dia atual, plano, nome, avatar) |
| `tb_contatos` | Lista de contatos para compartilhamento |
| `tb_dicionario` | Dicionário teológico |
| `tb_trilhas` | Trilhas de crescimento (versículos, reflexões, ações) |
| `tb_usuario_trilha_progresso` | Progresso do usuário nas trilhas |
| `tb_biblia` | Bíblia completa (~31 mil versículos) com busca full-text (GIN index) |
| `tb_leads` | Leads captados pela landing page |

### Migrations e Seed

```bash
npm run migrate      # Cria tabelas (standalone)
npm run seed         # Popula dicionário, trilhas e progresso (standalone)
npm run import-bible # Importa Bíblia (~31 mil versículos, standalone)
```

> **Nota:** Em produção (Railway), o backend cria as tabelas automaticamente no startup via `ensureTables()` e importa a Bíblia se a tabela `tb_biblia` estiver vazia.

## API (Backend Rotas)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/usuario` | Retorna perfil do usuário |
| POST | `/api/v1/usuario/perfil` | Atualiza perfil (nome, email, avatar) |
| POST | `/api/v1/auth/google` | Autenticação Google |
| GET | `/api/v1/codigo-dia` | Código verbal do dia |
| POST | `/api/v1/codigo-dia/save` | Salva reflexão do dia |
| POST | `/api/v1/checkpoint/start` | Inicia checkpoint de 12min |
| POST | `/api/v1/sync-checkpoint` | Sincroniza progresso |
| POST | `/api/v1/avancar-dia` | Avança dia (admin) |
| POST | `/api/v1/reiniciar-jornada` | Reinicia progresso |
| GET/POST | `/api/v1/contatos` | CRUD de contatos |
| POST | `/api/v1/contatos/:id/acao` | Registra ação no contato |
| GET | `/api/v1/historico` | Histórico de ações |
| GET | `/api/v1/biblia/livros` | Lista livros da Bíblia |
| GET | `/api/v1/biblia/capitulos/:abrev` | Capítulos de um livro |
| GET | `/api/v1/biblia/texto/:abrev/:cap` | Versículos de um capítulo |
| GET | `/api/v1/biblia/busca?q=` | Busca full-text |
| GET | `/api/v1/biblia/aleatorio` | Versículo aleatório |
| GET | `/api/v1/biblia/audio/:abrev/:cap` | URL de áudio (beblia.bible primário, LibriVox fallback) |
| GET | `/api/v1/biblia/audio-stream-librivox/:itemId/:fileName` | Proxy de áudio LibriVox/Internet Archive (streaming) |
| GET | `/api/v1/biblia/audio-stream/:book/:chapter.mp3` | Proxy de áudio da Bíblia — fallback (streaming) |
| GET | `/api/v1/health` | Health check (status + DB connection) |
| GET | `/api/v1/dicionario/termos` | Dicionário teológico |
| GET | `/api/v1/trilhas/lista` | Lista trilhas disponíveis |
| GET | `/api/v1/trilhas/ativa` | Trilha ativa do usuário |
| POST | `/api/v1/trilhas/iniciar` | Inicia uma trilha |
| POST | `/api/v1/trilhas/completar-dia` | Marca dia como completo |
| POST | `/api/v1/trilhas/cancelar` | Cancela trilha ativa |
| POST | `/api/v1/pagamentos/criar-preferencia` | Cria preferência de pagamento |
| POST | `/api/v1/pagamentos/webhook` | Webhook de pagamento |
| POST | `/api/v1/admin/definir-plano` | Define plano do usuário |
| POST | `/api/v1/leads` | Registra lead da landing page |
| POST | `/api/v1/chatgpt/*` | Rotas ChatGPT/LWC |
| GET | `*` | SPA fallback (serve index.html) |

## Estrutura de Temas

O app usa CSS custom properties definidas em `index.css` com suporte a dark mode via classe `body.dark-mode`:

- `--bg-app`, `--bg-card`, `--bg-card-hover` — cores de fundo
- `--text-primary`, `--text-secondary`, `--text-muted` — cores de texto
- `--orange`, `--green` — cores de destaque
- Tema padrão: **dark mode**
- Acento de cor: esmeralda (`#10B981`)

## Changelog

### 2026-07-29

**Trilha do Reino — Leitura Bíblica Gamificada**
- Novo componente `TrailHome.jsx` com mapa visual, streak, talentos e devocional diário.
- Plano cronológico em `trailData.js`: 150 leituras (AT→NT), 120 devotionais, 50 ações rotativas.
- Suporte a 18 meses (540 dias, ~2.2 cap/dia) e 12 meses (365 dias, ~3.3 cap/dia).
- 9 marcos de fé: Criação, Patriarcas, Êxodo, Conquista, Reis, Exilo, Evangelhos, Igreja, Apocalipse.
- Integração com moedas existentes (+10 Talentos por dia concluído).
- Streak com persistência localStorage (dias seguidos, reset se pular).
- Efeitos sonoros Web Audio (trailSons.js): click, complete, streak, milestone, coin.
- Novo card "Trilha do Reino" no dashboard com ícone de chama.

### 2026-07-28

**Áudio da Bíblia — LibriVox como fallback**
- Fonte primária: beblia.bible (narração original mantida).
- Fallback: LibriVox/Internet Archive (domínio público) se a fonte primária falhar.
- 66 livros mapeados no LibriVox como alternativa.
- Nova rota proxy: `GET /api/v1/biblia/audio-stream-librivox/:itemId/:fileName`.
- Resposta da API inclui campo `source` ("primary" ou "librivox") e `license`.
- Aguardando API key do Faith Comes By Hearing (Bible Brain) para áudio de maior qualidade.

### 2026-07-27

**Monorepo & Deploy**
- Estrutura reorganizada em `frontend/` (React + Vite) e `backend/` (Express + PostgreSQL).
- Migrado de SQLite para PostgreSQL (placeholders `$1,$2,...`, `SERIAL`, JSONB, `ILIKE`, `gin` full-text index).
- Deploy no Railway: dois serviços (frontend + backend) + plugin PostgreSQL.
- Frontend servido via `npx serve` com API_BASE apontando direto ao backend (URL absoluta).
- GitHub Actions para build automático de APK Android (Capacitor 8, JDK 21).

**Backend**
- Criado `pool.js` com conexão PostgreSQL (SSL para Railway).
- Criado `migrations/001_initial.sql` com 8 tabelas + índices.
- `ensureTables()` cria tabelas automaticamente no startup (não precisa rodar migrate manualmente).
- `seedData()` importa Bíblia ACF automaticamente se tabela `tb_biblia` estiver vazia.
- Criado `seed.js` para popular dicionário, trilhas e progresso.
- Criado `import-bible.js` para importar Bíblia via API (standalone).
- Adicionada rota `POST /api/v1/leads` para captura de leads.
- Tabela `tb_leads` criada na migration.
- Rota `GET /api/v1/health` para health check.
- Proxy de áudio da Bíblia com streaming (não buffer completo).

**Frontend**
- Criado `services/webhookService.js` para envio de leads.
- `vite.config.js` com proxy `/api` → `localhost:3001` (dev).
- `capacitor.config.json` e projeto Android restaurados.
- `API_BASE` aponta direto ao backend Railway em produção.

**PWA**
- Favicon: chama sobre livro (`favicon.png`).
- Removido `favicon.svg` (era bolt do Vite, incorreto).
- Manifest atualizado com ícones `any` e `maskable`.
- Meta tags Apple (apple-touch-icon, apple-mobile-web-app).
- Meta tags Open Graph (og:title, og:image, og:description).
- Service Worker de limpeza de cache (self-destructing).

**Tema & UI**
- Tema padrão: dark mode.
- Corrigido bug de `LandingPage.css` sobrescrevendo variáveis globais.
- Cor `--green` atualizada para esmeralda (`#10B981`).

**Arcade Bíblico**
- Caça-Palavras: seleção em 8 direções, normalização de acentos, grades maiores.
- Forca: corrigido uso de lista filtrada por dificuldade.
- Quiz e Charadas: timers e listas confirmados corretos.

### 2026-07-23
- Integração Capacitor para APK nativo.
- Workflow GitHub Actions para build automático.
