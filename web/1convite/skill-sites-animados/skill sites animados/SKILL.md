---
name: sites-animados
description: "Transforma arquivos de vídeo em sites animados por scroll. Extrai quadros do MP4, converte para WebP otimizado e monta um site inteiro em um único HTML, com um motor de animação em canvas guiado pelo scroll que cria 'quase-paradas' naturais nas seções de conteúdo. A direção de arte vem do arquivo de design do projeto ou de perguntas ao usuário — nunca de um estilo fixo. Use quando o usuário disser 'site animado', 'animação no scroll', 'vídeo para site', 'página estilo Apple', 'site scroll-driven', 'animação de quadros', 'transformar esse vídeo em site', 'fazer um site com scroll' ou quiser converter um clipe em uma experiência interativa de scroll."
---

# Gerador de Sites Animados por Scroll

Pega um vídeo MP4 + um briefing de conceito, extrai os quadros, otimiza para web e gera um site completo onde o scroll toca o vídeo quadro a quadro num canvas — com textos sobrepostos, efeitos ambientes e galerias que levam a experiência além de um simples player.

## O motor é fixo. O visual, não.

Esta skill entrega **um motor**: canvas guiado por scroll, remap de pausas, carregamento progressivo de quadros, pilha de camadas, galeria com parallax. Isso é o que não muda.

O que **muda a cada site**: paleta, tipografia, efeitos ambientes, formato dos cards, alinhamento e ritmo das seções. Essa camada vem sempre de uma fonte externa — o arquivo de design do projeto, ou as respostas do usuário. Nunca de um padrão embutido aqui.

**Se você gerar dois sites que se distinguem só pela cor de destaque, a skill falhou.** Antes de escrever qualquer CSS, você precisa ter passado pelo Passo 1.

---

## Quando Usar Essa Skill

**Serve para:**
- Converter um MP4 em site animado por scroll
- Páginas de luxo (imóveis, arquitetura, produtos, portfólios)
- Sequências estilo Apple (scroll para tocar o vídeo)
- Qualquer pedido do tipo "vídeo → experiência interativa de scroll"

**NÃO serve para:**
- Embutir um player de vídeo na página (use `<video>`)
- Converter vídeo em GIF ou WebP animado
- Construir site normal sem animação de vídeo no scroll
- Animações só em CSS (use a skill `frontend-design`)

**Redirecionamento:** Se o usuário quiser um site animado comum SEM vídeo de origem, use a skill `frontend-design`.

---

## O Que Pedir ao Usuário

**Obrigatório:**
1. **Um arquivo MP4** — caminho absoluto do vídeo de origem
2. **Conceito do site** — o que ele é (produto, marca, imóvel, portfólio...)

**Resolvido no Passo 1 (design), nunca assumido:**
- Paleta, tipografia, efeitos, formato dos cards, ritmo do scroll

**Opcional (tem padrão razoável):**
- Quantidade de quadros (padrão: calculado pela duração)
- Textos das seções (títulos, corpo, CTAs)
- Nome da marca e slogan

---

## Passo a Passo

### 1. Estabelecer a Direção de Design

**Este passo é bloqueante. Não gere HTML antes de concluí-lo.**

#### 1a. Procure um arquivo de design no projeto

Rode isto a partir do diretório de trabalho do usuário (não da pasta da skill):

```bash
find . -maxdepth 3 \( -iname "design*.md" -o -iname "*design-system*" -o -iname "styleguide*.md" \
  -o -iname "style-guide*.md" -o -iname "brand*.md" -o -iname "*.design.md" -o -iname "CLAUDE.md" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*"
```

Se nada aparecer, procure tokens já existentes no código:

```bash
ls tailwind.config.* 2>/dev/null
find . -maxdepth 3 \( -name "globals.css" -o -name "theme.css" -o -name "tokens.*" \) -not -path "*/node_modules/*"
```

**Se encontrar qualquer um deles**, leia o arquivo e extraia:
- cores (fundo, superfície, texto, texto secundário, borda, destaque primário e secundário)
- famílias tipográficas de título e de corpo, e os pesos usados
- raio de borda, densidade de sombra, uso ou não de blur/glass
- qualquer regra explícita de movimento, espaçamento ou tom de voz

Depois **mostre ao usuário o que você extraiu** e confirme antes de seguir:

```
DESIGN ENCONTRADO EM: docs/design-system.md
Fundo:      #0b0b0f
Texto:      #eaeaf0
Destaque:   #6d5efc
Títulos:    Satoshi, 600
Corpo:      Inter, 400
Cantos:     12px
Superfícies: sombra suave, sem glass

Vou usar isso como base. Confirma?
```

Se o arquivo cobre só parte (ex.: cores mas não movimento), pergunte **apenas o que falta** — não invente e não caia no preset antigo.

#### 1b. Se não houver arquivo de design, pergunte

Use a ferramenta `AskUserQuestion` com estas quatro perguntas de uma vez. Adapte as opções ao conceito que o usuário deu — as abaixo são o esqueleto.

**Pergunta 1 — Temperamento visual** (header: `Estilo`)
Ofereça 4 dos presets de `references/presets-visuais.md`, escolhendo os que fazem sentido para o conceito. Cada opção descrita em uma linha concreta, não em adjetivos: "fundo quase preto, serifada display, grão de filme e partículas" em vez de "elegante e sofisticado".

**Pergunta 2 — Luminosidade** (header: `Fundo`)
Escuro (o vídeo brilha, texto claro) / Claro (arejado, exige overlay sobre o canvas) / Alto contraste (preto puro com destaque saturado).

**Pergunta 3 — Cores da marca** (header: `Cores`)
Se o usuário já citou cores, pule. Senão: ofereça 3 direções de destaque plausíveis para o conceito + deixe claro que ele pode responder com um hex em "Outro".

**Pergunta 4 — Ritmo do scroll** (header: `Ritmo`)
Contemplativo (pausas longas, 750vh) / Equilibrado (650vh) / Ágil (pausas curtas, 450vh).

Leia `references/presets-visuais.md` **antes** de montar as perguntas — ele traz os cinco presets completos e a tabela de eixos que diferenciam um site do outro.

#### 1c. Fixe os tokens antes de codar

Escreva o `:root` completo — todas as variáveis, valores finais — e só então comece o HTML. Todo CSS depois disso referencia variável, nunca literal. Um `#0e0d0c` solto no meio do arquivo é bug.

### 2. Analisar o Vídeo

Rode o ffprobe para entender o material:

```bash
ffprobe -v quiet -print_format json -show_format -show_streams "/caminho/video.mp4"
```

Mostre ao usuário algo como:

```
ANÁLISE DO VÍDEO:
Duração:     12.4s
Resolução:   3840x2160 (4K)
FPS:         30
Quadros:     372
Codec:       H.264
```

Sugira uma quantidade de quadros:

| Duração       | Quadros Recomendados | Altura do Scroll |
|---------------|----------------------|------------------|
| 0-5s          | 60-90                | 400vh            |
| 5-15s         | 100-150              | 650vh            |
| 15-30s        | 150-200              | 800vh            |
| 30s+          | teto de 200          | 900vh            |

**Confirme com o usuário antes de extrair.** Diga: "Sugiro extrair {N} quadros. Pode ser ou quer ajustar?"

A altura do scroll da tabela é ponto de partida — o ritmo escolhido no Passo 1 tem prioridade sobre ela.

### 3. Extrair e Otimizar os Quadros

Rode o script que vem com a skill (`scripts/extrair_quadros.py`, relativo a este SKILL.md):

```bash
python3 scripts/extrair_quadros.py \
  --input "/caminho/video.mp4" \
  --output "sites-animados/{slug}/quadros" \
  --quadros {N} \
  --qualidade 80
```

Aponte `--output` para uma pasta dentro do diretório de trabalho atual.

O script gera:
- `quadros/desktop/` — frames 1920x1080 em WebP
- `quadros/mobile/` — frames 960x540 em WebP
- `quadros/manifest.json` — metadados (contagens, tamanhos, altura do scroll)

Mostre o resumo do manifest ao usuário. Se o pacote passar do budget (>10MB desktop, >5MB mobile), sugira `--qualidade 60` ou menos quadros.

### 4. Levantar o Conteúdo

A partir do conceito, prepare o texto das seções de overlay no scroll. **Seis é o número usual, não uma regra** — um produto simples pede quatro; um portfólio denso, oito. Cada seção aparece numa posição de scroll, criando a narrativa.

Um arco que funciona para a maioria dos casos:

1. **Hero** — Nome, slogan, número-chave
2. **Visão** — Citação ou frase aspiracional
3. **Detalhes** — Especificações ou features
4. **Grade** — 4-6 diferenciais em grid
5. **Contexto** — Localização, disponibilidade, prova social
6. **CTA** — Chamada de ação com botões e contato

Descarte, funda ou reordene o que não servir ao tema. Um app não tem "Contexto"; um restaurante não tem "Especificações".

Se o usuário passar textos, use-os. Senão, escreva no tom que a direção de design pede — editorial e evocativo num preset cinematográfico, direto e técnico num brutalista.

### 5. Montar o Site

Gere um HTML único e completo. Salve em: `sites-animados/{slug}/index.html`

Antes de escrever: releia os tokens fixados no Passo 1c e o preset escolhido. O motor da seção "Arquitetura do Código" é o mesmo sempre; tudo o que é aparência sai dos tokens.

### 6. Servir e Conferir

```bash
cd "sites-animados/{slug}"
python3 -m http.server 8080
```

Abra `http://localhost:8080/index.html` no navegador e tire prints em posições diferentes de scroll para checar.

Pedidos comuns de ajuste:
- "Scroll mais lento" → aumente a altura da seção de animação (650vh → 900vh)
- "Scroll mais rápido" → diminua a altura (650vh → 400vh)
- "Animação mais suave" → reduza o LERP_FACTOR (0.09 → 0.05)
- "Mais responsivo" → aumente o LERP_FACTOR (0.09 → 0.15)
- "Trocar textos" → edite o conteúdo dos overlays de scroll
- "Outras cores" → ajuste as variáveis CSS em `:root`

---

## Sistema Visual

A linguagem é quente, escura e cinematográfica. Cada elemento serve à animação — os efeitos ao redor (grão, partículas, vinheta) adicionam profundidade sem competir com os quadros do vídeo.

### Paleta (variáveis CSS)

```css
:root {
  --concrete: #d4cfc8;       /* cinza quente suavizado */
  --concrete-dim: #9e9890;   /* texto secundário */
  --stone: #706050;          /* detalhes decorativos */
  --charcoal: #1a1816;       /* fundo de cards */
  --ink: #0e0d0c;            /* fundo da página */
  --warm-white: #f4f0ea;     /* texto principal */
  --warm-white-dim: #c8c0b4; /* secundário enfatizado */
  --accent-blue: #4a6aff;    /* cor de destaque - troque por marca */
  --accent-blue-glow: rgba(74, 106, 255, 0.35);
  --accent-blue-soft: rgba(74, 106, 255, 0.08);
  --sunset-pink: #d4a0b0;    /* destaque secundário */
  --gold-warm: #c89848;      /* destaque terciário */
  --heading: 'Playfair Display', 'Georgia', serif;
  --body: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

Troque a família `--accent-blue` para outras marcas. A base quente-escura (`--ink`, `--warm-white`) fica — é o que faz os quadros do vídeo brilharem e sustenta o ar de luxo.

### Tipografia

- **Títulos:** Playfair Display — peso 300 para elegância, itálico para ênfase
- **Corpo:** DM Sans — peso 300-500, espaçamento generoso entre letras
- **Rótulos:** DM Sans, 8-9px, peso 500, espaçamento 0.25-0.35em, CAIXA ALTA
- **Hero:** clamp(42px, 5.5vw, 76px) — grande mas leve

Carregue do Google Fonts:
```html
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Playfair+Display:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&display=swap" rel="stylesheet">
```

### Efeitos Ambientes

São opcionais aos cliques (pointer-events: none) e puramente decorativos — mas constroem a atmosfera cinematográfica.

**Grão de filme:** SVG feTurbulence fractalNoise, tile 256px, opacidade 0.035. Dá textura de filme.

**Vinheta:** Gradiente radial de transparente (centro 50%) para rgba(14,13,12,0.45) nas bordas. Concentra o olhar no centro.

**Partículas ambientes:** Canvas fixo, ~40 pontinhos (0.3-1.8px), deriva lenta aleatória, branco-quente a 5-35% de opacidade. Dá vida. Remixa nas bordas para flutuar continuamente.

**Tint dinâmico:** Overlay em canvas que muda matiz conforme a seção de scroll. Sutil (6-4% de opacidade) em gradiente do accent-blue para o sunset-pink. Diferencia as seções.

**Cursor personalizado (só desktop):** Cursor em duas partes: um ponto de 6px com mix-blend-mode: difference (sempre visível) + um anel de 36px que segue o ponto com LERP. O anel expande para 56px no hover de elementos interativos e ganha brilho accent-blue. Some no mobile.

### Pilha de Camadas (z-index)

O site empilha vários efeitos. Ordem, do topo para baixo:

| Z-Index | Elemento        | Função                                              |
|---------|-----------------|----------------------------------------------------|
| 9999    | Loader          | Tela de carregamento com barra de progresso da marca|
| 9998    | Ponto do cursor | Ponto interno do cursor (mix-blend-mode: difference)|
| 9997    | Anel do cursor  | Anel externo (expande no hover)                     |
| 100     | Grão de filme   | Overlay de ruído SVG a 3.5%                         |
| 99      | Vinheta         | Gradiente radial escurecendo as bordas             |
| 50      | Marcadores      | Pontos de navegação fixos na lateral direita        |
| 15      | Partículas      | Canvas de partículas ambientes flutuantes           |
| 10      | Texto de scroll | Conteúdo de overlay durante a animação             |
| 5       | Tint            | Lavagem de cor dinâmica por seção                   |
| 1       | Overlays canvas | Gradiente à esquerda + inferior p/ legibilidade     |
| 0       | Canvas do vídeo | A animação de quadros guiada pelo scroll            |

### Motor de Pausas Inteligentes (Scroll Dwell)

É o que faz o scroll parecer mágico em vez de mecânico. Em vez de mapear a posição do scroll linearmente para os quadros, o motor cria "quase-paradas" em cada seção de conteúdo — o scroll desacelera ali, dando tempo de leitura, e acelera entre seções.

**Como funciona:**
1. Defina centros de pausa — posições de scroll onde o conteúdo aparece (ex.: 0.065, 0.21, 0.365, 0.525, 0.685, 0.89)
2. Em cada centro, uma densidade Gaussiana atinge pico — ou seja, mais distância de scroll é consumida por unidade de progresso efetivo
3. Construa uma tabela de integral cumulativa (mapeamento direto)
4. Inverta-a para a função de remapeamento real (posição do scroll → progresso efetivo)

Os centros de pausa devem bater com os valores `data-show-at` das seções de texto. Com 6 seções, espace-as de forma razoavelmente uniforme em 0-1, mas afastadas das bordas.

Parâmetros para ajustar:
- `DWELL_WIDTH` (0.045): largura da zona lenta. Menor = pausa mais curta.
- `DWELL_PEAK` (3.5): quanto mais lento o scroll nos pontos de pausa. Maior = pausa mais dramática.
- `REMAP_N` (2000): resolução da tabela. 2000 já é suave o bastante.

### Overlays de Texto no Scroll

Seis seções que entram e saem em posições específicas de scroll. Cada uma tem layout e estilo próprios:

1. **Hero** (à esquerda, 6% da borda): nome com animação de letras, slogan, preço/métrica-chave. Tem barra de stats em vidro na base com 4-5 números.

2. **Visão** (à esquerda): aspa de abertura como elemento decorativo, citação em itálico serifado, linha divisória, atribuição.

3. **Detalhes** (à esquerda): rótulo overline, título serifado, corpo de texto, lista de features com ícones e bordas sutis.

4. **Grade** (à esquerda): rótulo overline, grid de vidro 2 colunas com 6 células de diferenciais com ícones e descrições.

5. **Contexto** (à esquerda): rótulo overline, título serifado, corpo, lista de distâncias/detalhes com linhas pontilhadas conectando.

6. **CTA** (centralizado): título serifado grande em itálico, subtítulo, dois botões (primário preenchido, secundário outline) e card de contato.

Cada seção entra com blur(6px→0) e translateX(-20px→0). A classe `.visible` é toggada conforme o progresso do scroll bate com os atributos `data-show-at` / `data-hide-at`.

### Cards em Glassmorphism

Usados em barras de stats e grades de diferenciais:
- Fundo: rgba(244, 240, 234, 0.03)
- backdrop-filter: blur(20px)
- Borda: 1px solid rgba(244, 240, 234, 0.06)
- No hover: fundo clareia para 0.06, borda ganha toque accent-blue

### Marcadores de Capítulo

Navegação vertical fixa na direita com 6 pontos conectados por linhas. O ponto ativo ganha brilho accent-blue e a linha conectora preenche com o progresso do scroll na seção. Os pontos podem ter rótulos que aparecem no hover.

### Galeria

Abaixo da animação de scroll, um grid estilo masonry com quadros do vídeo. Usa IntersectionObserver para reveals e transforms de parallax por requestAnimationFrame (atributo `data-parallax` com valores px positivos/negativos).

Layout: `grid-template-columns: repeat(3, 1fr)` com alguns itens ocupando 2 linhas via classe `.tall`. Hover sutil de zoom (scale 1.03) com overflow hidden.

Pegue 6-7 quadros igualmente espaçados do vídeo para as imagens da galeria.

### Loader da Marca

Não é só uma barra de progresso — é uma experiência marcada:
- Símbolo da marca centralizado em caixa alta, fonte de título, espaçada
- Linhas decorativas acima e abaixo
- Barra fina de 140px com gradiente (accent-blue → sunset-pink)
- Contador de porcentagem embaixo
- Sai com transição de opacidade 0 + blur(8px)

### Rodapé

Mínimo: nome da marca na fonte de título, linha legal no corpo pequeno, fundo escuro um pouco mais claro que o ink.

---

## Arquitetura do Código

O site inteiro é um único HTML. Ordem estrutural:

```
HTML:
  1. Google Fonts
  2. <style> com todo o CSS
  3. Divs do cursor personalizado (#cursor-dot, #cursor-ring)
  4. Overlay de grão de filme
  5. Overlay de vinheta
  6. Canvas de partículas (fixed)
  7. Loader (fixed, z-9999)
  8. Marcadores de capítulo (fixed à direita)
  9. Seção de animação (relative, 650vh)
     - Container do canvas (sticky)
       - Canvas principal
       - Gradiente à esquerda
       - Gradiente inferior
       - Overlay de tint
     - 6 overlays de texto (fixed, toggados por JS)
  10. Seção de galeria
  11. Rodapé
  12. <script> com todo o JS

Ordem do JS:
  1. Tracking do cursor + LERP do anel
  2. Sistema de partículas (init + loop)
  3. Animação de letras (atributo data-split)
  4. Motor de pausas/remap (construção da LUT)
  5. Carregamento dos quadros (críticos primeiro, depois em lotes)
  6. Loop de animação do scroll (remap → LERP → drawFrame)
  7. Toggle de visibilidade dos textos de scroll
  8. Atualização dos marcadores de capítulo
  9. Atualização do tint
  10. IntersectionObserver da galeria + parallax
  11. Animação dos contadores de stats
  12. Init: carrega quadros → esconde loader → start na animação
```

### Padrões-chave de JavaScript

**Carregamento progressivo dos quadros:**
```javascript
// Quadros críticos primeiro (espaçados), depois em lotes
// Use createImageBitmap para decode fora da thread quando disponível
// Mostre o primeiro quadro imediatamente após o carregamento crítico
```

**Scroll → quadro com remap de pausas:**
```javascript
function getScrollProgress() {
  const rect = section.getBoundingClientRect();
  return Math.max(0, Math.min(1, -rect.top / (rect.height - window.innerHeight)));
}

function animate() {
  const rawProgress = getScrollProgress();
  const remapped = remapProgress(rawProgress);  // motor de pausas
  targetFrame = Math.floor(remapped * (FRAME_COUNT - 1));
  currentFrame += (targetFrame - currentFrame) * LERP_FACTOR;
  drawFrame(Math.round(currentFrame));
  // Atualiza também: visibilidade dos textos, marcadores, tint
  requestAnimationFrame(animate);
}
```

**Animação dos contadores de stats:**
```javascript
// Quando a stat-bar fica visível, anima os números de 0 ao alvo
// Use easing ease-out cúbico ao longo de ~1.5s
// Leia o alvo do atributo data-target, lide com vírgulas/unidades
```

---

## Adaptando para Diferentes Temas

O sistema é flexível. Como adaptar:

**Imóveis:** A paleta padrão já funciona. Nome do imóvel como hero, preço e specs na barra, detalhes da arquitetura, grid de comodidades, distâncias do entorno, CTA de agendamento de visita.

**Produto Tech:** Troque o destaque para azul mais frio (#2563eb) ou violeta elétrico (#7c3aed). Hero com nome + slogan, barra com specs-chave (bateria, peso, preço), Detalhes com specs técnicos, Grade de features, CTA de pré-venda ou "Saiba mais".

**Portfólio/Criativo:** Use gold-warm (#c89848). Hero com nome do criador + área, Visão com uma formulação artística, Detalhes com obras, Grade de serviços, CTA "Entrar em contato".

**Restaurante/Hotelaria:** Destaque quente (#c89848 ou bordô). Hero com nome da casa, Visão com frase do chef, Detalhes com filosofia da cozinha, Grade de destaques do menu, Contexto com endereço/horários.

**Automotivo:** Mantenha accent-blue ou troque por prata (#a8a8a8). Hero com nome + preço de partida, barra com 0-100/cv/autonomia, Detalhes de engenharia.

Em todos os casos, a estrutura de 6 seções, os efeitos ambientes, o motor de pausas e os cards em glassmorphism se mantêm — é o que sustenta o ar de luxo independente do conteúdo.

---

## Checklist de Qualidade

Antes de entregar o site ao usuário, confira:

- [ ] **Rodando a 60fps** — sem engasgos ou quedas de quadro no scroll
- [ ] **Primeiro quadro em <1s** — carregamento progressivo funciona
- [ ] **Barra de carregamento precisa** — gradiente, contador atualiza
- [ ] **Pacote desktop <10MB** — cheque manifest.json
- [ ] **Pacote mobile <5MB** — cheque manifest.json
- [ ] **Movimento reduzido tratado** — primeiro quadro estático em prefers-reduced-motion
- [ ] **Sem quadros em branco** — fallback nearest-neighbor preenche lacunas
- [ ] **Responsivo** — canvas reescala no resize, layout mobile funciona
- [ ] **Cursor customizado no desktop** — ponto segue instantâneo, anel arrasta
- [ ] **Partículas animam** — pontinhos sutis visíveis contra o fundo escuro
- [ ] **Textos de scroll entram/saem** — 6 seções nas posições certas
- [ ] **Animação de letras do hero** — caracteres surgem em sequência
- [ ] **Barra de stats legível** — backdrop blur funciona, números visíveis
- [ ] **Galeria carrega** — imagens da pasta de quadros, parallax no scroll
- [ ] **Motor de pausas natural** — scroll desacelera no conteúdo, acelera entre
- [ ] **Marcadores de capítulo atualizam** — ponto ativo destacado, linhas preenchem

---

## Formato de Saída

```
sites-animados/{slug}/
├── quadros/
│   ├── desktop/              # 1920x1080 WebP
│   │   ├── frame-0001.webp
│   │   └── ...
│   ├── mobile/               # 960x540 WebP
│   │   ├── frame-0001.webp
│   │   └── ...
│   └── manifest.json         # Metadados dos quadros
└── index.html                # Site de scroll completo
```

Para visualizar: `cd` na pasta de saída, rode `python3 -m http.server 8080` e abra `localhost:8080`.

---

## Resolução de Problemas

| Problema                            | Solução                                                            |
|-------------------------------------|-------------------------------------------------------------------|
| FFmpeg não encontrado               | `brew install ffmpeg`                                             |
| Sem suporte a libwebp               | `brew reinstall ffmpeg` (já vem com libwebp)                       |
| Quadros grandes demais (>10MB)      | Baixe a qualidade: `--qualidade 60`. Reduza a contagem: `--quadros 90` |
| Animação trava                       | Reduza o nº de quadros. Confira o cap de DPR em 2. Diminua partículas. |
| Flash branco entre quadros           | Fallback de quadro mais próximo não encontrou. Verifique a extração.|
| Canvas em branco no mobile          | Confirme que os quadros mobile existem. Cheque o switch de FRAME_DIR.|
| Barra de carregamento travada       | Um quadro deu 404. Veja o console. Confira os caminhos dos quadros. |
| Scroll rápido/lento demais          | Ajuste a altura da seção de animação. 650vh = padrão.              |
| Pausa muito pegajosa                 | Reduza DWELL_PEAK (3.5 → 2.5) ou aumente DWELL_WIDTH              |
| Partículas muito visíveis           | Reduza a opacidade do canvas de partículas (0.4 → 0.2)            |
| Cursor customizado oscilando        | Aumente o LERP do anel (0.15 → 0.2)                                |
| Blur do vidro não funciona          | Safari precisa -webkit-backdrop-filter. Já incluído no CSS.        |
| Erro de CORS local                   | Sirva com `python3 -m http.server 8080`. Não clique direto no HTML. |
| Fontes não carregam                  | Confira o link do Google Fonts. Fallsback nas vars CSS cobrem.     |