# 🦉 Plano: Agente Bidu — Diretor de Identidade Visual dos MiniApps

> Autor: Hermes DEZAFIRA · Data: 2026-08-11 · Status: IMPLEMENTADO (aguardando aprovação do Jonatas para push/deploy)
> Padrão de referência: Duolingo (mascote memorável, identidade consistente, estilo flat vector)
> Motor de imagem: Agnes AI (apihub.agnes-ai.com — OpenAI-compatível, $0/imagem)
> Implementação: `modules/agnes_client.py` + `modules/bidu_visual.py` + `modules/agnes_studio.py` + integração (miniapp_factory/database/server) + `tests/test_bidu_visual.py` (6/6 verde) + regressão PWA (51/51 verde)

---

## 1. Contexto e problema

Os MiniApps da DEZAFIRA nascem "born-complete" (Sala de Agentes: Nexo → Carlão → Dona Célia → Ricardo → Coder → Verificador → DB Chronicler), mas a identidade visual é genérica: logo placeholder/SVG e banner aleatório, **sem mascote, sem consistência, sem memorabilidade**. O usuário quer o padrão Duolingo: um personagem único que vira a cara do app (a coruja verde, o Duo).

## 2. Objetivo

Criar o **Agente Bidu** — Diretor de Identidade Visual dos MiniApps — que gera, via Agnes AI (grátis), um kit completo de identidade por MiniApp:

- **Logo** (ícone 1:1 + horizontal 16:9 + favicon)
- **Mascote** (character sheet: frente + 2-3 expressões + 1 pose assinatura) — com **consistência garantida via img2img** (mesmo personagem, variações controladas)
- **og-image** (1200×630 para compartilhamento)

Posição no fluxo: **Dona Célia → [Bidu] → Coder**. Bidu consome o branding kit (nome, paleta, personalidade) + dor única (Nexo) e entrega assets em nomes padronizados. Se Agnes falhar, **fallback automático para o pipeline atual do Ricardo** — a esteira nunca quebra.

## 3. Estado atual do código (achados da auditoria)

| Arquivo | Achado |
|---|---|
| `modules/miniapp_factory.py` | Fluxo completo da Sala de Agentes; PASSO 4 = Ricardo (`_ricardo_visual`) gera logo+banner via `ImageGeneratorAgent`; `logo_url`/`banner_url` vão para DB + PWA |
| `agents/image_factory.py` | Classe `ImageGeneratorAgent` usada pelo miniapp (HF + Pexels). **Sem Agnes.** |
| `modules/image_factory.py` | Outro `ImageGeneratorAgent` (blogs/capas); linha 28 já lê `AGNES_API_KEY` mas **não usa de fato** |
| `server.py` | **3 endpoints quebrados**: `POST /api/v1/{courses|ebooks|blog/post}/{id}/agnes-cover` + `GET /api/v1/agnes/gallery` + `POST /api/v1/agnes/use-cover` importam `modules.agnes_studio` que **NÃO EXISTE** → 500 |
| `services/pwa_generator.py` | PWA injeta `{{LOGO_URL}}` no header; ícones 192/512 via rota `/app/{slug}/icon-*.png` (SVG interpolado) |
| `.env` | `AGNES_API_KEY` já presente (validada ao vivo nesta sessão) |
| `modules/brand_designer.py` | Dona Célia: paleta (`colors.primary/accent`, `colors_dark`), `header_symbol`, tipografia, tom |

**Decisão de arquitetura**: o Bidu **cria** o `modules/agnes_studio.py` que falta (corrigindo os 3 endpoints 500 de bônus) e entrega o novo agente de identidade. Zero duplicação: um único cliente Agnes AI compartilhado.

## 4. Arquitetura da solução

### 4.1 `modules/agnes_client.py` — cliente Agnes AI (novo, compartilhado)

```python
class AgnesClient:
    """Cliente OpenAI-compatível para apihub.agnes-ai.com/v1 (imagens, $0)."""
    BASE_URL = "https://apihub.agnes-ai.com/v1"
    IMAGE_MODEL = "agnes-image-2.1-flash"

    def __init__(self, api_key: str | None = None):
        # lê AGNES_API_KEY do ambiente (dotenv); nunca loga a chave

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",      # 1K..4K
        ratio: str = "1:1",           # 1:1 | 16:9 | 9:16 | 3:4
        ref_images: list[str] | None = None,   # URLs ou base64 → img2img (consistência)
        timeout: float = 90.0,
    ) -> str | None:
        """POST /images/generations → retorna URL da imagem gerada (ou None)."""
        # body: {model, prompt, size, ratio, image: ref_images}
        # retry: 2x com backoff em 429/5xx/timeout
```

- **img2img = mecanismo de consistência**: para cada variação (expressão/pose), passa a imagem-base do mascote em `image[]`. O personagem não muda de forma; só a pose/emoção.
- Base64 recomendado para refs (evita dependência de URL pública do resultado anterior).
- `ratio` mapeado: 1:1 (logo/mascote) · 16:9 (banner/og) · 9:16 (story).

### 4.2 `modules/agnes_studio.py` — estúdio de capas (NOVO — corrige endpoints 500)

```python
class AgnesStudio:
    """Capa profissional HTML→PNG? Não — capa direto via Agnes AI + overlay via Obscura (reuso do padrão existente)."""
    async def generate_course_cover(self, title, subtitle, author, niche, style_id, course_id, difficulty, modules_count, design) -> dict
    async def generate_ebook_cover(self, ...) -> dict
    async def generate_blog_cover(self, title, subtitle, niche, style_id, post_id, blog_name) -> dict
```

- Implementa exatamente as assinaturas que `server.py` já chama (ver linhas 2315-2356, 2934+, 5761-5801).
- Pipeline: prompt de capa (título + nicho + estilo) → `AgnesClient.generate_image(ratio="16:9")` → salva em `outputs/agnes/{entity}_{id}_{ts}.png` → retorna `{"cover_url": "/outputs/agnes/...", "design": {...}}`.
- Fallback: se Agnes falhar → SVGRenderer/capa anterior (nunca 500).
- `GET /api/v1/agnes/gallery` já espera arquivos em `outputs/agnes/` (server.py:5810).

### 4.3 `modules/bidu_visual.py` — o Agente Bidu (NOVO, coração do plano)

```python
class BiduVisualAgent:
    """Diretor de Identidade Visual dos MiniApps — padrão Duolingo via Agnes AI."""

    async def generate_assets(
        self,
        brand: dict,          # saída da Dona Célia: brand_name, colors, header_symbol, brand_voice
        pain: str,            # dor única (Nexo)
        app_name: str,
        slug: str,
    ) -> dict:
        """Gera kit completo → outputs/miniapps/{slug}/assets/ → dict de URLs."""
```

**Etapas internas:**

1. **Briefing de 5 atributos** (LLM via `query_llm`, JSON estrito — mesmo padrão dos outros agentes):
   - `species` — forma/espécie ligada à dor (ex.: calculadora de déficit → capivara contadora; organização financeira → gato economista; inglês → coruja)
   - `color` — cor principal extraída da paleta da Dona Célia (`theme.primary`)
   - `emotion` — emoção base (determinado, curioso, acolhedor…)
   - `pose` — pose assinatura (polegar pra cima, empunhando ferramenta do nicho…)
   - `style` — SEMPRE: `flat vector mascot, big expressive eyes, one accent color, white/transparent background, Duolingo-style, no text, no watermark` (estilo fixo; os 4 primeiros variam)
   - Fallback determinístico se o LLM falhar (espécie = animal neutro, cor = primary, etc.) — a esteira nunca para.

2. **Prompt-mestre do personagem**: `"{style} | {species} mascot, main color {color}, {emotion} expression, signature pose: {pose}, for '{app_name}' — app that solves: {pain}"` → `AgnesClient.generate_image(ratio="1:1")` → **imagem-base** (guarda base64 em memória).

3. **Loop de consistência (img2img)**: com a base em `ref_images`, gera:
   - `mascot-happy.png` (emoção positiva), `mascot-thinking.png` (quiz/loading), `mascot-pose.png` (pose alternativa)
   - Se uma variação perder a identidade (comparação via LLM opcional, custo-baixo), 1 retry com prompt mais restrito.

4. **Derivações de logo**: a partir da base (img2img ou crop), gera:
   - `logo-icon.png` (1:1, personagem + fundo limpo) — vira `logo_url` do app
   - `logo-horizontal.png` (16:9, personagem à esquerda + espaço para nome) — vira `banner_url`
   - `favicon.png` (1:1, rosto do personagem em close)
   - `og-image.png` (16:9 com texto do app? Não — imagem pura; texto vem do HTML de compartilhamento)

5. **Persistência**: salva em `outputs/miniapps/{slug}/assets/` com nomes fixos (abaixo); retorna dict com `logo_url`, `banner_url`, `favicon_url`, `og_image_url`, `mascot` (frente + variações), `character_brief` (os 5 atributos, para reuso/regeneração).

**Fallback (crítico)**: qualquer falha no Agnes → `self._fallback_ricardo(app_name)` que reusa `agents/image_factory.py` atual; o resultado final SEMPRE tem `logo_url` + `banner_url` não-vazios (se nada der certo, o SVG do `PWAGenerator` cobre).

### 4.4 Integração no `modules/miniapp_factory.py`

- Novo PASSO 4.5: após Dona Célia (PASSO 3) e antes do Coder (PASSO 5):
  ```python
  # ── PASSO 4: Bidu (Identidade Visual) — logo + mascote + banner via Agnes ──
  logs.append({"agent": "🦉 Bidu (Identidade Visual)", "message": "Criando logo e mascote no padrão Duolingo..."})
  bidu = await self._bidu_visual(brand, pain, app_name, slug)
  # visual["logo_url"]/["banner_url"] = bidu["logo_url"]/["banner_url"] se preenchidos, senão mantém Ricardo
  ```
- `_bidu_visual` = método novo na classe: instancia `BiduVisualAgent`, chama `generate_assets`, loga o `character_brief`, nunca lança (try/except → fallback).
- Ricardo continua existindo como fallback e para outros contextos (banners de blog/ebook etc.). **Bidu é a primeira opção no miniapp.**
- `record`/DB: adicionar `mascot_url`, `character_brief` (JSON), `assets_dir` — colunas opcionais via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` no `modules/database.py` (mesmo padrão das migrações leves existentes).

### 4.5 Endpoints novos (server.py)

- `POST /api/v1/miniapps/{app_id}/bidu-assets` → regenera o kit visual de um app existente (para o piloto e para upgrades). Lê o record do DB, monta brand a partir do `theme` persistido, chama Bidu, faz `update_db_miniapp`.
- `GET /api/v1/agnes/gallery` — já existe; só passa a funcionar quando `outputs/agnes/` for populado.

## 5. Padrão de assets (nomes fixos — contrato)

Diretório: `outputs/miniapps/{slug}/assets/`

| Arquivo | Ratio | Uso |
|---|---|---|
| `logo-icon.png` | 1:1 | Ícone do app / header PWA (`logo_url`) |
| `logo-horizontal.png` | 16:9 | Banner (`banner_url`) |
| `favicon.png` | 1:1 | Favicon (close no rosto) |
| `mascot-front.png` | 1:1 | Tela inicial / empty state |
| `mascot-happy.png` | 1:1 | Estado positivo (acerto, streak) |
| `mascot-thinking.png` | 1:1 | Quiz/loading |
| `mascot-pose.png` | 1:1 | Celebração (dia completo) |
| `og-image.png` | 16:9 | Compartilhamento social |
| `character-brief.json` | — | Os 5 atributos + prompt-mestre (reuso/regeneração) |

URLs servidas como `/outputs/miniapps/{slug}/assets/{file}` (FastAPI já serve `outputs/` — verificar em server.py e manter o mesmo prefixo dos outputs existentes).

## 6. Briefing do personagem (system prompt do Bidu)

```
Você é o Bidu, Diretor de Identidade Visual dos MiniApps da DEZAFIRA.
Seu padrão é o Duolingo: UM personagem inesquecível que vira a cara do app.
A partir do branding (Dona Célia) e da dor única (Nexo), defina o personagem em 5 atributos:
1. species: forma/espécie que CONVERSA com a dor (metáfora clara, ex.: coruja=aprender, capivara=calma financeira)
2. color: a cor principal da paleta da marca (exato, do theme.primary)
3. emotion: a emoção base do personagem (determinado, curioso, acolhedor, travesso)
4. pose: a pose assinatura (1 só, memorável — ex.: polegar pra cima, segurando o item do nicho)
5. style: SEMPRE "flat vector mascot, big expressive eyes, one accent color, white background, Duolingo-style, no text, no watermark, clean simple shapes"
Regra de ouro: criança de 5 anos desenha o personagem de memória depois de ver 1 vez.
Responda APENAS com JSON: {"species","color","emotion","pose","style"} — sem markdown.
```

## 7. Testes e verificação

1. **Unit (novo `tests/test_bidu_visual.py`)**: `AgnesClient.generate_image` com mock de httpx (200 → URL; 429 → retry; 500 → None); `BiduVisualAgent.generate_assets` com mock do cliente → valida: 8 arquivos criados, nomes exatos, `character_brief` presente, fallback chamado quando Agnes falha.
2. **Regressão**: `pytest tests/test_pwa_generator.py` continua verde.
3. **Import check**: `python -c "from modules.bidu_visual import BiduVisualAgent; from modules.agnes_studio import AgnesStudio; from modules.agnes_client import AgnesClient"` sem erro.
4. **Smoke real (manual, supervisionado pelo Hermes)**: rodar Bidu para 1 MiniApp real (o pior da lista — piloto), inspecionar as imagens geradas (visão), validar consistência do mascote entre variações.
5. **Endpoint check**: `POST /api/v1/miniapps/{id}/bidu-assets` e os 3 `agnes-cover` respondem 200 (não mais 500).

## 8. Piloto

- **Alvo**: o MiniApp existente com pior visual (definir com Jonatas; sugestão: o que estiver com logo SVG placeholder).
- Critério de aceite: mascote consistente entre as 4 variações (img2img funcionou), logo limpo 1:1, banner 16:9 decente, tudo servido via `/outputs/` e persistido no DB.
- Depois do piloto aprovado → plugar no fluxo normal da Sala de Agentes (já implementado nesta entrega, com fallback).

## 9. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Agnes fora do ar / rate limit | Retry 2x + backoff; fallback Ricardo; nunca bloqueia a esteira |
| Mascote perde identidade no img2img | Base em base64 como ref; retry com prompt restrito; comparação via LLM opcional |
| Key ausente em produção | `AGNES_API_KEY` no .env do Railway (acionar Jonatas); fallback cobre até lá |
| Consistência de estilo entre logos | `style` fixo no system prompt do Bidu; `character-brief.json` permite regenerar idêntico |
| Endpoints agnes-cover quebrados | Corrigidos de bônus pelo `agnes_studio.py` (mesma entrega) |

## 10. Ordem de implementação (OpenCode)

1. `modules/agnes_client.py` (cliente base + retry)
2. `modules/bidu_visual.py` (agente completo + fallback)
3. `modules/agnes_studio.py` (capas — corrige 3 endpoints 500)
4. Integração `modules/miniapp_factory.py` (PASSO 4 Bidu + `_bidu_visual`)
5. `modules/database.py` (colunas novas, opcionais)
6. `server.py` (endpoint `bidu-assets`; verificar `outputs/` static mount)
7. `tests/test_bidu_visual.py` + regressão
8. Smoke real (piloto) — supervisionado pelo Hermes, fora do escopo OpenCode

## 11. Refino — lições dos 5 vídeos de mascote (pesquisa YouTube)

Transcrições completas em `/opt/data/transcripts/mascote/` (5 vídeos: Adam Lyttle "apps with mascots", 2 tutoriais EN de mascote fofo + animado, 2 PT de consistência com IA e Canva). Tudo que eles ensinam **já foi absorvido no desenho do Bidu**:

| Lição dos vídeos | Onde entrou no Bidu |
|---|---|
| "Mascots dão alma ao app — os apps do topo da App Store têm mascote com emoção" | Justificativa do agente; mascote obrigatório no kit (não só logo) |
| "A mascote tem que CONVERSAR com o app, não estar 'plunked in'" | `species` = metáfora da dor (coruja=aprender, gato=economizar…) — o personagem NASCE do problema que o app resolve |
| "Simples, instantaneamente reconhecível, com personalidade" | `_FIXED_STYLE` flat vector + 1 cor de destaque + `emotion` base |
| "ChatGPT cria a base mas NÃO mantém consistência — use img2img para variações" | Exatamente o loop do Bidu: base → variações via `image[]` (img2img) |
| "Estados emocionais mapeados a eventos do app (acerto=festa, erro=lágrima, quiz=pensando)" | `mascot-happy` (streak/acerto), `mascot-thinking` (quiz/loading), `mascot-pose` (celebração) |
| "Fácil de animar = formas simples, poucos detalhes" | `clean simple shapes` fixo no style; personagem 2D plano (pronto pra animação futura no app) |
| "Gere vídeo da mascote com Sora usando a ref; corte em loop; GIF sem fundo" | Fase 2 (fora do escopo atual): mascote animada via agnes-video-v2.0 + GIF para o app |

**Validação real do img2img (Agnes, 2026-08-11)**: `scripts/test_agnes_img2img.py` gerou base (robô azul) + 3 variações com a base como ref. Métricas: cor dominante permanece na família azul em todas; similaridade perceptual 0.17–0.21 vs base (mesmo personagem, expressão diferente — consistência OK, não cópia). Grade visual: `/tmp/grade_mascote.png`.

**Scripts do piloto prontos**: `scripts/piloto_bidu.py <app_id>` (kit para app real via API), `scripts/inspect_bidu_kit.py <assets_dir>` (grade + análise), `scripts/test_agnes_img2img.py` (consistência), `scripts/test_agnes_url_ref.py` (ref por URL vs base64).

## 12. Status da implementação (2026-08-11)

- [x] `modules/agnes_client.py` — cliente Agnes (retry, img2img, download PNG)
- [x] `modules/bidu_visual.py` — agente completo (briefing 5 atributos + loop img2img + fallback Ricardo)
- [x] `modules/agnes_studio.py` — capas course/ebook/blog (corrige os 3 endpoints 500)
- [x] `modules/miniapp_factory.py` — PASSO 4 Bidu + PASSO 4.5 Ricardo fallback
- [x] `modules/database.py` — colunas `mascot_url`, `character_brief`, `assets_dir` + migração
- [x] `server.py` — endpoint `POST /api/v1/miniapps/{app_id}/bidu-assets`
- [x] `tests/test_bidu_visual.py` — 6/6 passando
- [x] Regressão `tests/test_pwa_generator.py` — 51/51 passando
- [x] Import check — `modules.bidu_visual`, `modules.agnes_studio`, `modules.agnes_client` OK
- [x] Prova real img2img — 4 imagens geradas na Agnes, consistência validada por métricas
- [ ] Piloto em MiniApp real (escolher o pior visual — aguardando Jonatas)
- [ ] Push para main → Railway autodeploy (SOMENTE após aprovação do Jonatas)
