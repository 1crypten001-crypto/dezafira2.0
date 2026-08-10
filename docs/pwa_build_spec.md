# PWA DEZAFIRA — Build Spec v1.0 (Construção via OpenCode)

## 1. Objetivo

Transformar o PWA da DEZAFIRA num produto **real, instalável, personalizado por nicho e feito para recorrência** (MRR), servido pelo FastAPI atual (sem build step Node). Base: auditoria `docs/pipeline_map.md` (P0) + recomendações de UI/UX do Gemini.

## 2. Estado atual (bugs a corrigir)

- `services/pwa_generator.py` é STUB vazio (4 linhas). `server.py:3311` chama `PWAGenerator.generate_quiz_pwa(...)` que **não existe** → `/api/v1/factory/build-app` sempre 500.
- `server.py:1141` `/app/{slug}` ignora o slug e serve `static/pwa_template.html` genérico (30KB) para TODOS os apps.
- `pwa_template.html` NÃO tem manifest link, service worker, icons, install meta → não instalável.
- `/manifest.json` e `/sw.js` → 404 em produção.
- App é gerado e salvo no PostgreSQL (`miniapps`), mas nunca servido como PWA instalável.

## 3. Decisões de arquitetura

1. **Sem build step**: PWA de arquivo único servido pelo FastAPI. Template mestre com placeholders + gerador determinístico em Python. (Deploy Railway continua `pip install -r requirements.txt`.)
2. **Icons PNG sem dependências**: gerar PNGs 192/512/maskable em Python puro (zlib + struct — gradient + círculo + iniciais via paths). NÃO adicionar Pillow ao requirements.
3. **Manifest e SW dinâmicos por app**: `GET /app/{slug}/manifest.json` e `GET /app/{slug}/sw.js`, escopados a `/app/{slug}/`.
4. **Nicho vira tema**: paleta CSS por nicho (finanças, emagrecimento, marketing, espiritual, saúde, tecnologia, geral) → gradient, cor primária, acento, emoji, copy padrão.
5. **Recorrência**: drip timeline (dias 1/7/14/30) da tabela `miniapp_drip_contents` + progresso persistido em localStorage + streak diário + CTA de checkout.
6. **Fonte de dados**: `GET /app/{slug}` resolve app no DB (id exato OU slugify(app_name), nesse fallback ordem) → gera HTML via `PWAGenerator` de forma determinística. `build-app` faz upsert do registro no DB (id = app_id) para o slug funcionar.

## 4. UI/UX (síntese Gemini — OBRIGATÓRIO)

- **Bottom sheets** em vez de modais (resultado de quiz, detalhes, menu) — CSS/JS puro, sem lib.
- **Haptic feedback**: `navigator.vibrate` (8–15ms) em tap em CTA, resposta de quiz, abrir sheet; guard para iOS/sem suporte.
- **Skeleton loaders**: shimmer enquanto "carrega" conteúdo (render assíncrono simulado curto — 300–500ms — para dar sensação de app nativo).
- **Safe-area**: `env(safe-area-inset-*)` em header fixo, bottom bar, sheets.
- **Dark-first**: tema escuro padrão com gradient glassmorphism (base já existe no template), `prefers-color-scheme` adaptativo.
- **Micro-interações**: escala no press (`:active` transform), transições spring-like (cubic-bezier), glow accent.
- **Progress bar** de quiz, uma pergunta por tela (slide), score final com resultado personalizado.
- **Compartilhar resultado**: Web Share API (`navigator.share`) + fallback clipboard.
- **Install prompt**: captura `beforeinstallprompt`, botão "Instalar App" no header/bottom sheet; some quando `appinstalled`.
- **Pull-to-refresh** onde houver lista (drip timeline).

## 5. Arquivos

### 5.1 `services/pwa_generator.py` (reescrita completa)

```python
class PWAGenerator:
    @staticmethod
    def slugify(text: str) -> str
    @staticmethod
    def niche_theme(nicho: str) -> dict   # {"primary","accent","gradient","bg","surface","emoji","tagline"} fallback geral
    @staticmethod
    def generate_icons(app_name, theme, size=512) -> bytes  # PNG puro, zlib+struct
    @staticmethod
    def generate_quiz_pwa(app_id, title, nicho, questions, cta_text="Obter Relatório", checkout_url="") -> dict
    # retorna {"success": True, "app_id", "app_url": f"/app/{slug}", "html": ..., "manifest": {...}, "service_worker": "...", "icons": {"192": "/app/{slug}/icon-192.png", "512": ..., "maskable": ...}}
    @staticmethod
    def generate_from_app_record(record: dict) -> dict   # app de miniapps/create: wrapper moderno + conteúdo salvo (pwa_html) injetado
    @staticmethod
    def generate_checkout_page(app_name, checkout_url, theme) -> dict
    @staticmethod
    def build_manifest(app_id, slug, app_name, theme, description) -> dict
    @staticmethod
    def build_service_worker(slug, app_id, precache_urls) -> str
```

**generate_quiz_pwa**: renderiza `static/pwa_template.html` substituindo placeholders `{{APP_ID}}`, `{{SLUG}}`, `{{APP_NAME}}`, `{{NICHE}}`, `{{THEME}}` (JSON com vars CSS), `{{QUESTIONS_JSON}}`, `{{CTA_TEXT}}`, `{{CHECKOUT_URL}}`, `{{MANIFEST_URL}}`, `{{SW_URL}}`, `{{ICON_192}}`, `{{ICON_512}}`, `{{DRIP_JSON}}`, `{{LOGO_URL}}`, `{{BANNER_URL}}`. Questions: lista de dicts `{"question": str, "options": [str...], "result": {"title","desc"}}` (tolerar formatos variados: aceitar strings simples também).

**Manifest**: `{"name","short_name","description","start_url":"/app/{slug}","scope":"/app/{slug}/","display":"standalone","background_color","theme_color","orientation":"portrait","icons":[{192},{512},{maskable}],"shortcuts":[...]}`.

**SW**: precache do shell (`/app/{slug}/` + manifest + icons), cache-first para shell/assets, network-first para conteúdo, fallback offline (página offline inline).

**generate_from_app_record**: se `pwa_html` salvo existir e for HTML substancial (>500 chars), serve como conteúdo dentro do shell moderno (header + install + sheets + SW + manifest). Se não, gera quiz PWA com dados do app (app_type/features → questions genéricas do nicho).

### 5.2 `static/pwa_template.html` (template mestre)

Manter base visual existente (glassmorphism dark) e adicionar:
- `<head>`: placeholders para manifest link, theme-color, `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`, `apple-touch-icon`, og tags.
- CSS: vars de tema via placeholder `{{THEME}}`; bottom sheet, skeleton shimmer, safe-area, haptics classes.
- JS embutido (vanilla, ~300–500 linhas): engine de quiz (slides, progresso, score, resultado em bottom sheet), install prompt, haptics helper, skeletons, share, drip timeline (fetch `/api/v1/miniapps/{id}` ou dados injetados), streak localStorage, SW register.

### 5.3 `server.py` (mudanças)

- `GET /app/{slug}` (linha ~1141): resolver app no DB (`get_db_miniapp(slug)` → fallback: `slugify(app_name) == slug` via `get_db_miniapps()` scan limit 200); 404 se não achar; gerar via `PWAGenerator.generate_from_app_record` ou `generate_quiz_pwa` (se app veio de build-app); headers `Cache-Control: no-cache` + `X-Frame-Options` ok. Se pwa_html salvo contém `{{` placeholders não resolvidos → resolver também.
- `GET /app/{slug}/manifest.json`: manifest do app (gerar on-the-fly).
- `GET /app/{slug}/sw.js`: SW do app (gerar on-the-fly, Content-Type `application/javascript`, `Service-Worker-Allowed: /app/{slug}/`).
- `GET /app/{slug}/icon-192.png` e `icon-512.png`: PNGs gerados (cache 7d, ETag).
- `POST /api/v1/factory/build-app` (linha ~3294): após gerar, **upsert** no DB (`create_db_miniapp` com id=app_id, slug via app_id; se já existe, atualizar pwa_html/manifest) → retornar `res` com `app_url`.
- Não quebrar endpoints existentes `/api/v1/miniapps*`.

### 5.4 `requirements.txt`

Sem mudanças (PNG puro). Confirmar que não há dependência nova.

### 5.5 Testes `tests/test_pwa_generator.py` (se pytest existe; senão criar)

- `generate_quiz_pwa` retorna dict com html contendo `manifest.json`, `sw.js`, `<link rel="manifest"`, `navigator.serviceWorker.register`.
- `build_manifest` JSON válido, icons 192/512/maskable presentes, start_url/scope corretos.
- `generate_icons` → bytes começando com assinatura PNG (`\x89PNG\r\n\x1a\n`), decodifica com `struct` (width/height corretos).
- `slugify`: acentos/ESPAÇOS → slug.
- `niche_theme`: nicho conhecido retorna paleta; desconhecido cai no fallback.
- `/app/{slug}` 404 para slug inexistente (teste de handler via `TestClient` se infra permitir).

## 6. Critérios de aceite (verificação pós-deploy)

1. `POST /api/v1/factory/build-app` (com X-Service-Key) com questions → 200, JSON com `html`, `manifest`, `app_url`.
2. `GET /app/{slug}` → HTML personalizado (título/nicho/tema do app), NÃO o genérico.
3. `GET /app/{slug}/manifest.json` → 200, JSON válido, icons presentes.
4. `GET /app/{slug}/sw.js` → 200, `application/javascript`.
5. `GET /app/{slug}/icon-192.png` → 200, `image/png`, assinatura PNG válida.
6. Slug desconhecido → 404 JSON/HTML com mensagem.
7. Lighthouse installability: manifest + SW + icons + HTTPS (avaliar com browser depois).

## 7. Fora de escopo (fase 2)

- APK via TWA (PWABuilder/Bubblewrap) — depois do PWA sólido.
- Auth nos endpoints miniapps (P1, backlog separado).
- Deduplicação das cópias legadas (P1, backlog separado).

## 8. Regras de execução

- Idioma dos arquivos: pt-BR no conteúdo, código/comentários em inglês ou pt-BR consistente com o repo.
- Não tocar em nada fora dos arquivos listados (não mexer em SniperVideoEngine/ nem Blog_Inteligente_SEO_com_IA_-_v1.8/).
- Rodar testes antes de finalizar. Reportar arquivos alterados + resultados.
