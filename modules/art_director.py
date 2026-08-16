"""
Agnes — Diretora Geral de Arte do Dezafira.

Catálogo de Vibes cinematográficas (estilo Apple TV+ / editorial de cinema),
Brand Kit com cores e fontes, Super Prompts de imagem e instruções de câmera.

Identidade Visual Dezafira:
  Primária  : Ciano elétrico #00CFFF
  Secundária: Roxo/violeta  #7B4FD6
  Gradiente : Ciano → Azul → Roxo
  Background: #0d1b2a (azul noite profundo)
  Texto     : Branco puro #FFFFFF
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional

# ── Paleta Oficial da Marca ────────────────────────────────────────────────
DEZAFIRA_BRAND = {
    "primary":    "#00CFFF",   # ciano elétrico
    "secondary":  "#7B4FD6",   # roxo/violeta
    "bg":         "#0d1b2a",   # azul noite profundo
    "text":       "#FFFFFF",   # branco puro
    "gradient_from": "#00CFFF",
    "gradient_to":   "#7B4FD6",
}

# ── Catálogo de Vibes Cinematográficas ────────────────────────────────────
VIBES: Dict[str, Dict[str, Any]] = {

    "dezafira": {
        "name": "Dezafira Original",
        "description": "Identidade oficial Dezafira. Azul noite profundo, ciano elétrico e roxo vibrante. Sci-fi premium.",
        "colors": {
            "bg":     "#0d1b2a",
            "bg2":    "#112236",
            "accent": "#00CFFF",
            "text":   "#FFFFFF",
            "muted":  "#7B99B5",
        },
        "fonts": {
            "font":      "Orbitron",
            "font_sans": "Exo 2",
        },
        "image_style": (
            "cinematic dark sci-fi panorama, deep navy blue atmosphere, electric cyan and violet energy streams, "
            "volumetric fog, glowing crystal formations, ultra-detailed, photorealistic, 8k IMAX quality, "
            "dramatic cinematic lighting, award-winning visual effects"
        ),
        "motion_style": (
            "epic slow push-in with depth-of-field transition, electric cyan particles drifting upward, "
            "ambient light shift from violet to cyan, premium motion graphics, cinematic grade"
        ),
        "logo_overlay": True,
    },

    "apple": {
        "name": "Apple Cinematic",
        "description": "Minimalismo premium estilo Apple TV+. Fotografia editorial de alto impacto com espaçamento respirado.",
        "colors": {
            "bg":     "#000000",
            "bg2":    "#0a0a0a",
            "accent": "#f5f5f7",
            "text":   "#f5f5f7",
            "muted":  "#86868b",
        },
        "fonts": {
            "font":      "Inter",
            "font_sans": "Inter",
        },
        "image_style": (
            "dramatic cinematic movie poster photography, ultra-detailed, award-winning cinematography, "
            "Dolby Vision HDR color grade, deep blacks with precise highlights, bokeh background, "
            "shot on ARRI Alexa with Zeiss Master Prime 85mm lens, f/1.4, professional Hollywood lighting, "
            "atmospheric volumetric light rays, photorealistic, 8k"
        ),
        "motion_style": (
            "slow cinematic dolly-in, depth of field breathing effect, Dolby Vision color grade shift, "
            "subtle anamorphic lens flare, elegant parallax layers, premium motion, studio quality"
        ),
        "logo_overlay": True,
    },

    "linear": {
        "name": "Linear / Dark Tech",
        "description": "Estilo técnico premium. Grafite escuro, indigo e tipografia de alta legibilidade.",
        "colors": {
            "bg":     "#0c0c0d",
            "bg2":    "#141416",
            "accent": "#5e6ad2",
            "text":   "#f7f7f8",
            "muted":  "#828288",
        },
        "fonts": {
            "font":      "Space Grotesk",
            "font_sans": "Space Grotesk",
        },
        "image_style": (
            "ultra-clean dark tech product photography, glossy matte graphite surfaces, sleek indigo and violet ambient glow, "
            "precise reflections on polished metal, studio light raking across textures, "
            "architectural product composition, hyper-realistic, 8k"
        ),
        "motion_style": (
            "dynamic 3D camera orbit right, ambient light pulsing from indigo core, "
            "floating geometric particles, high-tech HUD elements, cinematic motion"
        ),
        "logo_overlay": True,
    },

    "claude": {
        "name": "Claude Editorial",
        "description": "Editorial aconchegante. Terracota, bege e tipografia serifada minimalista.",
        "colors": {
            "bg":     "#fbfaf7",
            "bg2":    "#f5f2eb",
            "accent": "#d97757",
            "text":   "#191919",
            "muted":  "#6b6b6b",
        },
        "fonts": {
            "font":      "Playfair Display",
            "font_sans": "Plus Jakarta Sans",
        },
        "image_style": (
            "elegant editorial magazine photography, warm biscuit and terracotta tones, "
            "Monocle magazine aesthetic, natural soft window light, linen textures, aged vellum paper, "
            "premium editorial composition, shallow depth of field, 8k"
        ),
        "motion_style": (
            "slow gentle dolly zoom, warm color temperature shift, dust particles drifting in soft light, "
            "elegant parallax, film-grain texture overlay, editorial premium motion"
        ),
        "logo_overlay": True,
    },

    "stripe": {
        "name": "Stripe / Corporate Tech",
        "description": "Tecnologia corporativa vibrante. Branco limpo com gradientes indigo, profissional.",
        "colors": {
            "bg":     "#ffffff",
            "bg2":    "#f6f9fc",
            "accent": "#635bff",
            "text":   "#0a2540",
            "muted":  "#425466",
        },
        "fonts": {
            "font":      "Inter",
            "font_sans": "Inter",
        },
        "image_style": (
            "vibrant 3D render of smooth gradient shapes, crisp clean white background, "
            "indigo and violet soft lighting, glass morphism elements, ultra-precise vectors, "
            "corporate premium tech aesthetic, 8k"
        ),
        "motion_style": (
            "gentle circular camera orbit, soft gradient hue shift, floating isometric UI elements, "
            "clean corporate motion, elegant drift"
        ),
        "logo_overlay": True,
    },

    "nintendo": {
        "name": "Nintendo Retro Y2K",
        "description": "Estética de consoles clássicos Y2K. Carbono, neon laranja e tipografia pesada.",
        "colors": {
            "bg":     "#12131a",
            "bg2":    "#282a36",
            "accent": "#ff5b06",
            "text":   "#f8f8f2",
            "muted":  "#6272a4",
        },
        "fonts": {
            "font":      "Rajdhani",
            "font_sans": "Rajdhani",
        },
        "image_style": (
            "retro-futuristic Y2K console aesthetic, brushed carbon fiber and metallic chrome textures, "
            "neon orange scan-lines, glossy plastic highlights, CRT monitor glow, bold shadow contrast, "
            "2000s tech nostalgia, 8k"
        ),
        "motion_style": (
            "rapid camera tilt with motion blur, neon glow pulse sweep, retro screen wipe transition, "
            "digital glitch bursts, arcade energy motion"
        ),
        "logo_overlay": True,
    },
}

DEFAULT_VIBE = "apple"

# ── Regras de Composição Cinematográfica (Agnes Art Director Rules) ────────
COMPOSITION_RULES = """
AGNES ART DIRECTOR — REGRAS OBRIGATÓRIAS:

1. TIPOGRAFIA: Nunca use fonte padrão do sistema. Cada vibe tem fonte específica carregada do Google Fonts.
2. HIERARQUIA: Título = peso visual máximo. Subtítulo = 60% do peso. Créditos = 30%.
3. ESPAÇAMENTO: Mínimo 48px de margem de segurança em todos os lados (Safe Frame).
4. LOGO: Logo Dezafira SEMPRE presente como watermark discreto no canto superior esquerdo.
5. TEXTO SOBRE IMAGEM: text-shadow obrigatório para garantir legibilidade sobre qualquer fundo.
6. COMPOSIÇÃO: Texto posicionado onde a imagem de fundo "respira" (área escura/vazia).
7. CONTRASTE: Mínimo WCAG AA (4.5:1) para título, 3:1 para subtítulo.
8. SEM TEMPLATE: Cada peça deve parecer criada especificamente para aquele produto.
"""


class ArtDirector:
    """Agnes — Diretora Geral de Arte do Dezafira. Exigente, cinematográfica, nunca genérica."""

    def __init__(self, default_vibe: str = DEFAULT_VIBE):
        self.default_vibe = default_vibe
        self.brand = DEZAFIRA_BRAND

    def get_vibe(self, vibe_id: str) -> Dict[str, Any]:
        v_id = (vibe_id or "").lower().strip()
        if v_id not in VIBES:
            return VIBES[self.default_vibe]
        return VIBES[v_id]

    def generate_brand_kit(self, vibe_id: str, niche: str = "") -> Dict[str, Any]:
        """Gera o Brand Kit completo para a vibe solicitada."""
        vibe = self.get_vibe(vibe_id)

        layout_map = {
            "nintendo": "console-retro",
            "claude":   "editorial-cream",
            "apple":    "cinematic-dark",
            "dezafira": "sci-fi-dark",
            "linear":   "tech-dark",
            "stripe":   "corporate-light",
        }

        return {
            "colors":      vibe["colors"],
            "font":        vibe["fonts"]["font"],
            "font_sans":   vibe["fonts"]["font_sans"],
            "fonts":       vibe["fonts"],
            "vibe_id":     vibe_id or self.default_vibe,
            "layout":      layout_map.get(vibe_id, "hero-left"),
            "nicho":       niche or "Geral",
            "description": vibe["description"],
            "logo_overlay": vibe.get("logo_overlay", True),
            "brand":       self.brand,
        }

    def generate_image_prompt(self, vibe_id: str, subject: str, scene: str = "",
                               seed: Optional[int] = None) -> str:
        """Monta o Super Prompt cinematográfico para geração de imagem."""
        vibe = self.get_vibe(vibe_id)
        style_suffix = vibe["image_style"]
        seed_str = f" seed:{seed}," if seed is not None else ""

        prompt = (
            f"Cinematic movie poster composition: {subject}. "
            f"{scene}. "
            f"Dezafira brand identity, {style_suffix}."
            f"{seed_str} No text, no watermarks, no UI elements in the image itself."
        )
        return prompt.strip()

    def generate_video_motion_prompt(self, vibe_id: str, name: str,
                                      subject: str = "") -> Dict[str, Any]:
        """Retorna o prompt e parâmetros de movimento para o Agnes Video IA."""
        vibe = self.get_vibe(vibe_id)
        motion_suffix = vibe["motion_style"]

        prompt = (
            f"Cinematic abstract motion sequence. "
            f"{motion_suffix}. "
            "Pure visual atmosphere without any text, letters, or typography. "
            "Smooth motion, no morphing artifacts. Premium commercial quality. 4K HDR."
        )

        motion_intensity = 85 if vibe_id == "nintendo" else 60

        return {
            "prompt": prompt,
            "motion": motion_intensity,
            "aspect_ratio": "16:9",
            "fps": 24,
            "negative_prompt": (
                "text warping, ugly letters, distorted logo, low quality, "
                "glitch artifacts, blurry foreground, hand mutation, watermark"
            ),
        }

    def generate_storyboard_config(self, vibe_id: str, niche: str, title: str, subtitle: str, cta_text: str, domain: str) -> list:
        """Gera as configurações de layout e animação de tipografia para as 3 cenas baseadas na vibe."""
        # A Agnes (IA) decide o layout e animação de cada cena com base na vibe
        if vibe_id == "apple":
            return [
                {
                    "type": "intro",
                    "niche": niche.upper(),
                    "title": title,
                    "layout": "hero-left",
                    "align": "left",
                    "animation": "slide-blur"
                },
                {
                    "type": "features",
                    "subtitle": subtitle,
                    "layout": "center",
                    "align": "center",
                    "animation": "fade-scale"
                },
                {
                    "type": "cta",
                    "ctaText": cta_text,
                    "domain": domain,
                    "layout": "hero-right",
                    "align": "right",
                    "animation": "glow"
                }
            ]
        elif vibe_id == "linear":
            return [
                {
                    "type": "intro",
                    "niche": niche.upper(),
                    "title": title,
                    "layout": "hero-left",
                    "align": "left",
                    "animation": "slide-blur"
                },
                {
                    "type": "features",
                    "subtitle": subtitle,
                    "layout": "hero-left",
                    "align": "left",
                    "animation": "slide-blur"
                },
                {
                    "type": "cta",
                    "ctaText": cta_text,
                    "domain": domain,
                    "layout": "center",
                    "align": "center",
                    "animation": "fade-scale"
                }
            ]
        else:
            # Fallback geral
            return [
                {
                    "type": "intro",
                    "niche": niche.upper(),
                    "title": title,
                    "layout": "hero-left",
                    "align": "left",
                    "animation": "slide-blur"
                },
                {
                    "type": "features",
                    "subtitle": subtitle,
                    "layout": "center",
                    "align": "center",
                    "animation": "fade-scale"
                },
                {
                    "type": "cta",
                    "ctaText": cta_text,
                    "domain": domain,
                    "layout": "center",
                    "align": "center",
                    "animation": "fade-scale"
                }
            ]

