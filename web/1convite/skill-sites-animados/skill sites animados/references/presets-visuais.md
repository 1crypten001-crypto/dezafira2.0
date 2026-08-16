# Presets Visuais

Cada preset é um ponto de partida completo — paleta, tipografia, efeitos e temperamento das seções. **Nenhum é o padrão.** Use o que o arquivo de design ou as respostas do usuário indicarem, e adapte.

Se o usuário escolher um preset, ainda assim troque a cor de destaque e as fontes pela identidade dele quando houver. O preset dá o *temperamento*, não a marca.

---

## 1. Cinemático Quente

Lançamentos imobiliários high-end, arquitetura, joalheria. Escuro, sépia, contemplativo.

```css
:root {
  --bg: #0e0d0c;
  --surface: #1a1816;
  --text: #f4f0ea;
  --text-dim: #c8c0b4;
  --muted: #9e9890;
  --line: #706050;
  --accent: #4a6aff;
  --accent-2: #d4a0b0;
  --heading: 'Playfair Display', Georgia, serif;
  --body: 'DM Sans', -apple-system, sans-serif;
}
```

- **Efeitos:** grão de filme 3.5%, vinheta radial, partículas âmbar, tint por seção, cursor de dois anéis
- **Cards:** glassmorphism — `rgba(244,240,234,0.03)` + `backdrop-filter: blur(20px)`
- **Seções:** alinhadas à esquerda a 6% da borda, entrada com `blur(6px)` + `translateX(-20px)`
- **Ritmo:** dwell longo (`DWELL_PEAK 3.5`), scroll de 650vh — o usuário demora em cada parada

---

## 2. Editorial Claro

Moda, revista, portfólio de fotografia, hotelaria boutique. Claro, arejado, tipografia como protagonista.

```css
:root {
  --bg: #f7f5f2;
  --surface: #ffffff;
  --text: #16150f;
  --text-dim: #4a4740;
  --muted: #8b8780;
  --line: #ddd8d0;
  --accent: #1a1a1a;
  --accent-2: #b8503c;
  --heading: 'Instrument Serif', 'Times New Roman', serif;
  --body: 'Inter', -apple-system, sans-serif;
}
```

- **Efeitos:** SEM grão, SEM partículas, SEM cursor customizado. Só uma vinheta clara invertida bem sutil sobre o canvas
- **Cards:** borda `1px solid var(--line)` sobre fundo branco. Zero blur — sombra `0 1px 3px rgba(0,0,0,0.04)` no hover
- **Seções:** centralizadas com `max-width: 640px`, entrada só com fade + `translateY(12px)`
- **Ritmo:** dwell curto (`DWELL_PEAK 2.0`), scroll de 450vh — leitura rápida, o vídeo é o fôlego entre blocos
- **Cuidado:** o canvas precisa de overlay branco a 15-25% para o texto escuro ter contraste. Cheque com quadros claros e escuros.

---

## 3. Brutalista Tech

SaaS, dev tools, hardware, lançamento de produto técnico. Denso, mono, sem cerimônia.

```css
:root {
  --bg: #08090a;
  --surface: #101214;
  --text: #e6e8eb;
  --text-dim: #8b9198;
  --muted: #5c6166;
  --line: #22262b;
  --accent: #00e5a0;
  --accent-2: #ff4d00;
  --heading: 'Inter Tight', -apple-system, sans-serif;
  --body: 'JetBrains Mono', ui-monospace, monospace;
}
```

- **Efeitos:** scanline horizontal de 2px a 2% de opacidade, sem grão orgânico. Ruído digital, não fílmico. Sem partículas.
- **Cards:** borda dura `1px solid var(--line)`, cantos retos (`border-radius: 0`), fundo `var(--surface)` sólido
- **Seções:** grid de 12 colunas, rótulos em mono caixa alta com prefixo (`[01] VISÃO`), entrada sem blur — corte seco de opacidade em 120ms
- **Ritmo:** dwell médio (`DWELL_PEAK 2.8`), scroll de 550vh
- **Extra:** números da stat-bar em mono com `font-variant-numeric: tabular-nums`

---

## 4. Neon Noir

Automotivo, gaming, música, nightlife, esporte. Alto contraste, glow, movimento.

```css
:root {
  --bg: #05060a;
  --surface: #0d1018;
  --text: #ffffff;
  --text-dim: #a0a8bb;
  --muted: #5a6274;
  --line: #1c2130;
  --accent: #ff0055;
  --accent-2: #00d9ff;
  --heading: 'Archivo', Impact, sans-serif;
  --body: 'Archivo', -apple-system, sans-serif;
}
```

- **Efeitos:** aberração cromática nas bordas do canvas, glow `box-shadow: 0 0 40px var(--accent)` nos elementos ativos, tint agressivo (12-15%), partículas rápidas
- **Cards:** fundo escuro + borda `1px` com gradiente accent → accent-2
- **Seções:** títulos em caixa alta pesados (`font-weight: 800`, `letter-spacing: -0.03em`), entrada com `scale(0.94)` + fade
- **Ritmo:** dwell curto e agressivo (`DWELL_PEAK 2.2`, `DWELL_WIDTH 0.03`), scroll de 500vh — a energia vem do movimento, não da pausa

---

## 5. Orgânico Natural

Bem-estar, gastronomia, sustentabilidade, spa, agricultura. Terroso, macio, respirado.

```css
:root {
  --bg: #1c1a15;
  --surface: #26231c;
  --text: #f0ebe0;
  --text-dim: #b8b0a0;
  --muted: #8a8271;
  --line: #3a3529;
  --accent: #8fa356;
  --accent-2: #c9743a;
  --heading: 'Fraunces', Georgia, serif;
  --body: 'Karla', -apple-system, sans-serif;
}
```

- **Efeitos:** grão suave 2%, vinheta muito leve, partículas lentas cor de pólen, sem cursor customizado
- **Cards:** `border-radius: 20px`, fundo `rgba(240,235,224,0.04)`, blur 16px, sem borda visível
- **Seções:** alinhadas à esquerda com bastante `line-height` (1.8), entrada lenta (700ms) com `translateY(24px)`
- **Ritmo:** dwell muito longo (`DWELL_PEAK 4.2`), scroll de 750vh — tudo respira

---

## Eixos para criar um preset novo

Se nenhum dos cinco serve, construa um combinando estas decisões. Elas são o que efetivamente diferencia um site do outro:

| Eixo | Extremos |
|---|---|
| **Luminosidade** | fundo escuro (vídeo brilha) ↔ fundo claro (precisa overlay no canvas) |
| **Textura** | grão/ruído/partículas ↔ superfície totalmente limpa |
| **Forma dos cards** | glassmorphism ↔ borda dura ↔ sombra ↔ sem card algum |
| **Cantos** | `0px` (brutalista) ↔ `4px` (neutro) ↔ `20px+` (orgânico) |
| **Tipografia** | serifada display ↔ sans neutra ↔ mono ↔ sans pesada condensada |
| **Alinhamento** | seções à esquerda ↔ centralizadas ↔ grid alternado esquerda/direita |
| **Entrada** | blur + slide ↔ fade puro ↔ scale ↔ corte seco |
| **Ritmo do dwell** | `DWELL_PEAK 2.0` (ágil) ↔ `4.2` (contemplativo) |
| **Cursor** | anel customizado ↔ cursor nativo |

Regra prática: mude **pelo menos quatro** desses eixos em relação ao último site gerado. Dois sites que só diferem na cor de destaque parecem o mesmo site.
