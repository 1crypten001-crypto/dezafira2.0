"""
🎨 Brand Themes v2 — Identidade Visual Profissional por Nicho.

Expansão: paletas 50-900 (Tailwind-style), logos SVG vetoriais,
favicons profissionais, sistema de sombras, dark mode automático.
"""

import unicodedata


# ═══════════════════════════════════════════════════════════════════════════════
# SVGs PROFISSIONAIS PARA LOGO/FAVICON
# ═══════════════════════════════════════════════════════════════════════════════

# Logos SVG limpos para cada nicho — usados no header e favicon
LOGOS_SVG = {
    "cristao": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect width="32" height="32" rx="8" fill="#d4a853"/>
  <path d="M16 6v20M6 16h20" stroke="#1a1410" stroke-width="3.5" stroke-linecap="round" fill="none"/>
</svg>""",
    "financas": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect width="32" height="32" rx="8" fill="#059669"/>
  <path d="M8 20c0-2 3-4 8-4s8 2 8 4-3 4-8 4-8-2-8-4z" fill="#fff" opacity=".9"/>
  <path d="M8 15c0-2 3-4 8-4s8 2 8 4" stroke="#fff" stroke-width="1.5" fill="none" opacity=".6"/>
  <path d="M10 22V10M22 22V10" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
</svg>""",
    "saude": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect width="32" height="32" rx="8" fill="#16a34a"/>
  <path d="M16 10v12M10 16h12" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
  <circle cx="16" cy="16" r="11" stroke="#fff" stroke-width="1.5" fill="none" opacity=".4"/>
</svg>""",
    "tecnologia": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect width="32" height="32" rx="8" fill="#3b82f6"/>
  <path d="M10 22l6-12 6 12" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <circle cx="16" cy="18" r="2" fill="#fff" opacity=".6"/>
</svg>""",
    "casa": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect width="32" height="32" rx="8" fill="#d97706"/>
  <path d="M6 18l10-10 10 10" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <rect x="12" y="18" width="8" height="8" rx="1" fill="#fff" opacity=".8"/>
  <path d="M6 18l10-10 10 10" stroke="#fff" stroke-width="1" fill="none" opacity=".3"/>
</svg>""",
    "default": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect width="32" height="32" rx="8" fill="#6366f1"/>
  <path d="M16 8l8 8-8 8-8-8 8-8z" fill="#fff" opacity=".9"/>
  <path d="M16 11l5 5-5 5-5-5 5-5z" fill="#c7d2fe"/>
  <circle cx="16" cy="16" r="13" stroke="#a5b4fc" stroke-width="1.5" fill="none" opacity=".4"/>
</svg>""",
}

# Versões simplificadas para favicon (apenas 16-32px)
FAVICON_SVGS = {
    "cristao": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23d4a853'/%3E%3Cpath d='M16 6v20M6 16h20' stroke='%231a1410' stroke-width='3.5' stroke-linecap='round' fill='none'/%3E%3C/svg%3E",
    "financas": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23059669'/%3E%3Cpath d='M8 20c0-2 3-4 8-4s8 2 8 4-3 4-8 4-8-2-8-4z' fill='%23fff' opacity='.9'/%3E%3Cpath d='M8 15c0-2 3-4 8-4s8 2 8 4' stroke='%23fff' stroke-width='1.5' fill='none' opacity='.6'/%3E%3Cpath d='M10 22V10M22 22V10' stroke='%23fff' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E",
    "saude": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%2316a34a'/%3E%3Cpath d='M16 10v12M10 16h12' stroke='%23fff' stroke-width='3' stroke-linecap='round'/%3E%3Ccircle cx='16' cy='16' r='11' stroke='%23fff' stroke-width='1.5' fill='none' opacity='.4'/%3E%3C/svg%3E",
    "tecnologia": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%233b82f6'/%3E%3Cpath d='M10 22l6-12 6 12' stroke='%23fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3Ccircle cx='16' cy='18' r='2' fill='%23fff' opacity='.6'/%3E%3C/svg%3E",
    "casa": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23d97706'/%3E%3Cpath d='M6 18l10-10 10 10' stroke='%23fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3Crect x='12' y='18' width='8' height='8' rx='1' fill='%23fff' opacity='.8'/%3E%3C/svg%3E",
}

# Mapa thema_id → FAVICON_SVGS

THEMES = {
    "cristao": {
        "id": "cristao",
        "name": "Fé & Tradição",
        "niche_keywords": ["ensinamentos de jesus", "bíblia", "cristão", "crista", "evangelho",
                          "oração", "jesus", "deus", "espírito santo", "espirito santo",
                          "fé", "igreja", "reino de deus", "marias"],
        "colors": {
            "primary": "#d4a853",
            "primary_light": "#f0d68a",
            "primary_dark": "#a67c2e",
            "bg": "#faf6ef",
            "bg_dark": "#f0e8d5",
            "dark": "#1a1410",
            "dark2": "#2a2219",
            "text": "#3d3227",
            "text_light": "#7a6b5a",
            "accent": "#8b2500",
            "border": "#e0d5c0",
        },
        "colors_dark": {
            "bg": "#0f0b08",
            "bg_dark": "#1a1410",
            "dark": "#faf6ef",
            "dark2": "#e0d5c0",
            "text": "#e8e0d0",
            "text_light": "#9a8b7a",
            "border": "#2a2219",
        },
        "fonts": {
            "heading": "'Playfair Display', serif",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#10013;",
        "header_bg": "linear-gradient(135deg, #1a1410, #2a2219)",
        "header_symbol": "&#10013;",
        "placeholder_icon": "&#10013;",
        "logo_initial": "O",
        "primary_rgb": "212,168,83",
        "shadow": "0 2px 20px rgba(212,168,83,.12)",
        "shadow_hover": "0 8px 32px rgba(212,168,83,.2)",
        "hero_gradient": "radial-gradient(circle at top right, rgba(212,168,83,.08), transparent 50%)",
        "glow": "0 0 20px rgba(212,168,83,.15)",
        "tag_color": "rgba(212,168,83,0.12)",
        "tag_text": "#a67c2e",
        "tag_border": "rgba(212,168,83,0.2)",
        "hero_image_url": "/static/images/hero_cristao.jpg",
    },
    "financas": {
        "id": "financas",
        "name": "Finanças & Prosperidade",
        "niche_keywords": ["finanças", "financas", "investimento", "economia", "dinheiro",
                          "renda", "poupança", "poupanca", "cartão", "cartao", "crédito",
                          "credito", "dívida", "divida", "orçamento", "orcamento",
                          "gastos", "renda extra", "planejamento financeiro"],
        "colors": {
            "primary": "#059669",
            "primary_light": "#6ee7b7",
            "primary_dark": "#047857",
            "bg": "#f0fdf4",
            "bg_dark": "#dcfce7",
            "dark": "#022c22",
            "dark2": "#064e3b",
            "text": "#1a2e05",
            "text_light": "#4a7c59",
            "accent": "#0d9488",
            "border": "#a7f3d0",
        },
        "colors_dark": {
            "bg": "#021a14",
            "bg_dark": "#022c22",
            "dark": "#f0fdf4",
            "dark2": "#dcfce7",
            "text": "#d1fae5",
            "text_light": "#6ee7b7",
            "border": "#064e3b",
        },
        "fonts": {
            "heading": "'Inter', system-ui, sans-serif",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#128176;",
        "header_bg": "linear-gradient(135deg, #022c22, #064e3b)",
        "header_symbol": "&#128200;",
        "placeholder_icon": "&#128176;",
        "logo_initial": "V",
        "primary_rgb": "5,150,105",
        "shadow": "0 2px 20px rgba(5,150,105,.12)",
        "shadow_hover": "0 8px 32px rgba(5,150,105,.2)",
        "hero_gradient": "radial-gradient(circle at top right, rgba(5,150,105,.08), transparent 50%)",
        "glow": "0 0 20px rgba(5,150,105,.15)",
        "tag_color": "rgba(5,150,105,0.12)",
        "tag_text": "#047857",
        "tag_border": "rgba(5,150,105,0.2)",
        "hero_image_url": "/static/images/hero_financas.jpg",
    },
    "saude": {
        "id": "saude",
        "name": "Saúde & Bem-Estar",
        "niche_keywords": ["saúde", "saude", "bem-estar", "bem estar", "alimentação",
                          "alimentacao", "natural", "detox", "emagrecer", "exercício",
                          "exercicio", "meditação", "meditacao", "yoga", "ansiedade",
                          "sono", "qualidade de vida"],
        "colors": {
            "primary": "#16a34a",
            "primary_light": "#86efac",
            "primary_dark": "#15803d",
            "bg": "#f0fdf4",
            "bg_dark": "#dcfce7",
            "dark": "#052e16",
            "dark2": "#166534",
            "text": "#1a2e05",
            "text_light": "#4a7c59",
            "accent": "#0d9488",
            "border": "#a7f3d0",
        },
        "colors_dark": {
            "bg": "#041a0c",
            "bg_dark": "#052e16",
            "dark": "#f0fdf4",
            "dark2": "#dcfce7",
            "text": "#d1fae5",
            "text_light": "#6ee7b7",
            "border": "#166534",
        },
        "fonts": {
            "heading": "'Merriweather', serif",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#127793;",
        "header_bg": "linear-gradient(135deg, #052e16, #166534)",
        "header_symbol": "&#129496;",
        "placeholder_icon": "&#127793;",
        "logo_initial": "S",
        "primary_rgb": "22,163,74",
        "shadow": "0 2px 20px rgba(22,163,74,.12)",
        "shadow_hover": "0 8px 32px rgba(22,163,74,.2)",
        "hero_gradient": "radial-gradient(circle at top right, rgba(22,163,74,.08), transparent 50%)",
        "glow": "0 0 20px rgba(22,163,74,.15)",
        "tag_color": "rgba(22,163,74,0.12)",
        "tag_text": "#15803d",
        "tag_border": "rgba(22,163,74,0.2)",
    },
    "tecnologia": {
        "id": "tecnologia",
        "name": "Tecnologia & Inovação",
        "niche_keywords": ["tecnologia", "tech", "programação", "programacao", "software",
                          "aplicativo", "app", "inteligência artificial", "inteligencia artificial",
                          "ia", "internet", "digital", "código", "codigo", "startup",
                          "inovação", "inovacao", "desenvolvimento"],
        "colors": {
            "primary": "#3b82f6",
            "primary_light": "#93c5fd",
            "primary_dark": "#2563eb",
            "bg": "#f0f5ff",
            "bg_dark": "#dbeafe",
            "dark": "#0f172a",
            "dark2": "#1e3a5f",
            "text": "#1e293b",
            "text_light": "#5b6b8a",
            "accent": "#8b5cf6",
            "border": "#bfdbfe",
        },
        "colors_dark": {
            "bg": "#080c14",
            "bg_dark": "#0f172a",
            "dark": "#f0f5ff",
            "dark2": "#dbeafe",
            "text": "#cbd5e1",
            "text_light": "#64748b",
            "border": "#1e3a5f",
        },
        "fonts": {
            "heading": "'Inter', system-ui, sans-serif",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#128187;",
        "header_bg": "linear-gradient(135deg, #0f172a, #1e3a5f)",
        "header_symbol": "&#9881;",
        "placeholder_icon": "&#128187;",
        "logo_initial": "T",
        "primary_rgb": "59,130,246",
        "shadow": "0 2px 20px rgba(59,130,246,.12)",
        "shadow_hover": "0 8px 32px rgba(59,130,246,.2)",
        "hero_gradient": "radial-gradient(circle at top right, rgba(59,130,246,.08), transparent 50%)",
        "glow": "0 0 20px rgba(59,130,246,.15)",
        "tag_color": "rgba(59,130,246,0.12)",
        "tag_text": "#2563eb",
        "tag_border": "rgba(59,130,246,0.2)",
    },
    "casa": {
        "id": "casa",
        "name": "Casa & Decoração",
        "niche_keywords": ["casa", "decoração", "decoracao", "lar", "jardinagem", "diy",
                          "faça você mesmo", "faça voce mesmo", "organização", "organizacao",
                          "limpeza", "móveis", "moveis", "conforto"],
        "colors": {
            "primary": "#d97706",
            "primary_light": "#fcd34d",
            "primary_dark": "#b45309",
            "bg": "#fffbeb",
            "bg_dark": "#fef3c7",
            "dark": "#1c1917",
            "dark2": "#292524",
            "text": "#3d3227",
            "text_light": "#7a6b5a",
            "accent": "#ea580c",
            "border": "#fde68a",
        },
        "colors_dark": {
            "bg": "#0f0d0a",
            "bg_dark": "#1c1917",
            "dark": "#fffbeb",
            "dark2": "#fef3c7",
            "text": "#e8e0d0",
            "text_light": "#9a8b7a",
            "border": "#292524",
        },
        "fonts": {
            "heading": "'Lora', serif",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#127968;",
        "header_bg": "linear-gradient(135deg, #1c1917, #292524)",
        "header_symbol": "&#128083;",
        "placeholder_icon": "&#127968;",
        "logo_initial": "C",
        "primary_rgb": "217,119,6",
        "shadow": "0 2px 20px rgba(217,119,6,.12)",
        "shadow_hover": "0 8px 32px rgba(217,119,6,.2)",
        "hero_gradient": "radial-gradient(circle at top right, rgba(217,119,6,.08), transparent 50%)",
        "glow": "0 0 20px rgba(217,119,6,.15)",
        "tag_color": "rgba(217,119,6,0.12)",
        "tag_text": "#b45309",
        "tag_border": "rgba(217,119,6,0.2)",
    },
}

DEFAULT_THEME = {
    "id": "default",
    "name": "Blog",
    "colors": {
        "primary": "#4f46e5",
        "primary_light": "#a5b4fc",
        "primary_dark": "#4338ca",
        "bg": "#f8fafc",
        "bg_dark": "#f1f5f9",
        "dark": "#0f172a",
        "dark2": "#1e293b",
        "text": "#334155",
        "text_light": "#64748b",
        "accent": "#6366f1",
        "border": "#cbd5e1",
    },
    "colors_dark": {
        "bg": "#080c14",
        "bg_dark": "#0f172a",
        "dark": "#f8fafc",
        "dark2": "#e2e8f0",
        "text": "#cbd5e1",
        "text_light": "#64748b",
        "border": "#1e293b",
    },
    "fonts": {
        "heading": "'Inter', system-ui, sans-serif",
        "body": "'Inter', system-ui, sans-serif",
    },
    "header_icon": "&#128214;",
    "header_bg": "linear-gradient(135deg, #0f172a, #1e293b)",
    "header_symbol": "&#128221;",
    "placeholder_icon": "&#128214;",
    "logo_initial": "B",
    "primary_rgb": "79,70,229",
    "shadow": "0 2px 20px rgba(79,70,229,.12)",
    "shadow_hover": "0 8px 32px rgba(79,70,229,.2)",
    "hero_gradient": "radial-gradient(circle at top right, rgba(79,70,229,.08), transparent 50%)",
    "glow": "0 0 20px rgba(79,70,229,.15)",
    "tag_color": "rgba(79,70,229,0.12)",
    "tag_text": "#4338ca",
    "tag_border": "rgba(79,70,229,0.2)",
}


def _normalize(text: str) -> str:
    """Remove acentos e normaliza para lowercase."""
    text = unicodedata.normalize('NFKD', text or "")
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text.lower().strip()


def detect_theme(nicho: str) -> dict:
    """Detecta o tema apropriado baseado no nicho do blog."""
    if not nicho:
        return DEFAULT_THEME
    niche_normalized = _normalize(nicho)
    for theme_id, theme in THEMES.items():
        for kw in theme["niche_keywords"]:
            kw_normalized = _normalize(kw)
            if kw_normalized in niche_normalized:
                return theme
    return DEFAULT_THEME


def get_logo_svg(nicho: str, size: int = 32) -> str:
    """Retorna logo SVG profissional para o nicho."""
    theme = detect_theme(nicho)
    theme_id = theme.get("id", "default")
    svg = LOGOS_SVG.get(theme_id) or LOGOS_SVG.get("default")
    if svg:
        if size != 32:
            svg = svg.replace('viewBox="0 0 32 32"', f'viewBox="0 0 32 32" width="{size}" height="{size}"')
        return svg
    # Fallback final: favicon (data URI — apenas se nenhum SVG inline existir)
    return get_favicon_svg(nicho)


def get_favicon_svg(nicho: str) -> str:
    """Retorna favicon SVG data URI profissional para o nicho."""
    theme = detect_theme(nicho)
    theme_id = theme.get("id", "default")
    fav = FAVICON_SVGS.get(theme_id)
    if fav:
        return fav
    return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%234f46e5'/%3E%3Ctext x='16' y='23' font-size='18' text-anchor='middle' fill='%23fff'%3E✝%3C/text%3E%3C/svg%3E"


def get_logo_initial(nicho: str) -> str:
    """Retorna a letra inicial do logo para o nicho."""
    theme = detect_theme(nicho)
    return theme.get("logo_initial", "B")


def _palette_css_vars(c: dict, prefix: str = "") -> str:
    """Gera variáveis CSS :root para um conjunto de cores."""
    return (f"--{prefix}primary:{c['primary']};--{prefix}primary-light:{c['primary_light']};"
            f"--{prefix}primary-dark:{c['primary_dark']};"
            f"--{prefix}bg:{c['bg']};--{prefix}bg-dark:{c['bg_dark']};"
            f"--{prefix}text:{c['text']};--{prefix}text-light:{c['text_light']};"
            f"--{prefix}dark:{c['dark']};--{prefix}dark2:{c['dark2']};"
            f"--{prefix}accent:{c['accent']};--{prefix}border:{c['border']};")


def generate_theme_css(nicho: str, blog_name: str = "") -> str:
    """Generate CSS variables for a blog based on its niche.
    Inclui dark mode, fluid typography, sombras, hero gradient.
    """
    theme = detect_theme(nicho)
    c = theme["colors"]
    cd = theme.get("colors_dark", c)
    f = theme["fonts"]
    prgb = theme.get("primary_rgb", "79,70,229")
    logo_svg = get_logo_svg(nicho)
    init = get_logo_initial(nicho)

    # Google Fonts import
    font_imports = []
    if "Playfair Display" in f["heading"]:
        font_imports.append("Playfair+Display:wght@400;700")
    if "Merriweather" in f["heading"]:
        font_imports.append("Merriweather:wght@300;400;700")
    if "Lora" in f["heading"]:
        font_imports.append("Lora:wght@400;600;700")
    if "JetBrains Mono" in f["heading"]:
        font_imports.append("JetBrains+Mono:wght@400;700")

    font_url = ""
    if font_imports:
        families = "|".join(font_imports)
        font_url = f'@import url("https://fonts.googleapis.com/css2?{families}&display=swap");'

    header_symbol = theme.get("header_symbol", theme["header_icon"])
    hero_grad = theme.get("hero_gradient", f"radial-gradient(circle at top right, rgba({prgb},.08), transparent 50%)")
    shadow = theme.get("shadow", f"0 2px 20px rgba({prgb},.12)")
    shadow_hover = theme.get("shadow_hover", f"0 8px 32px rgba({prgb},.2)")

    css = f"""\
{font_url}
:root{{
--primary:{c["primary"]};--primary-light:{c["primary_light"]};--primary-dark:{c["primary_dark"]};
--bg:{c["bg"]};--bg-dark:{c["bg_dark"]};
--dark:{c["dark"]};--dark2:{c["dark2"]};
--text:{c["text"]};--text-light:{c["text_light"]};
--accent:{c["accent"]};--border:{c["border"]};
--gold:{c["primary"]};
--radius:12px;--radius-sm:8px;
--shadow:{shadow};--shadow-hover:{shadow_hover};
--font-heading:{f["heading"]};--font-body:{f["body"]};
--hero-grad:{hero_grad};
--primary-rgb:{prgb};
--logo-init:{init};
--fs-sm:clamp(0.8rem,0.75rem+0.25vw,0.95rem);
--fs-base:clamp(1rem,0.92rem+0.4vw,1.15rem);
--fs-md:clamp(1.25rem,1.08rem+0.85vw,1.75rem);
--fs-lg:clamp(1.75rem,1.45rem+1.5vw,2.75rem);
--fs-xl:clamp(2.25rem,1.95rem+2.75vw,3.75rem);
--header-h:64px;
--content-max:960px;
--article-max:740px;
}}
[data-theme="dark"]{{
--primary:{cd["primary"] if "primary" in cd else c["primary"]};
--bg:{cd["bg"]};--bg-dark:{cd["bg_dark"]};
--dark:{cd["dark"]};--dark2:{cd["dark2"]};
--text:{cd["text"]};--text-light:{cd["text_light"]};
--border:{cd["border"]};
}}

*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{font-family:var(--font-body);background:var(--bg);color:var(--text);line-height:1.7;font-size:var(--fs-base)}}
a{{color:var(--primary);text-decoration:none;transition:color .2s}}
a:hover{{color:var(--primary-dark)}}

/* ─── HEADER ─── */
.site-header{{background:var(--dark);border-bottom:1px solid rgba(255,255,255,.08);backdrop-filter:blur(12px);transition:transform .3s ease}}
.header-inner{{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:24px;padding:0 20px;height:var(--header-h)}}
.header-logo{{display:flex;align-items:center;gap:10px;flex-shrink:0}}
.logo-icon{{width:34px;height:34px;display:flex;align-items:center;justify-content:center;background:var(--primary);border-radius:8px;font-size:16px;font-weight:800;color:var(--bg);overflow:hidden}}
.logo-icon svg{{width:22px;height:22px}}
.logo-text{{font-size:18px;font-weight:700;color:#fff}}

/* ─── HERO SECTION ─── */
.blog-hero{{padding:5rem 2rem;border-bottom:1px solid var(--border);position:relative;overflow:hidden;background-size:cover!important;background-position:center!important}}
.blog-hero::before{{content:"";position:absolute;inset:0;background:linear-gradient(135deg,rgba(var(--primary-rgb),.04),rgba(var(--primary-rgb),.09));z-index:1}}
.hero-inner-split{{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:1.2fr 1fr;gap:40px;align-items:center;position:relative;z-index:2}}
.hero-brand-col{{display:flex;flex-direction:column;align-items:flex-start;gap:1.2rem;text-align:left}}
.hero-badge{{background:var(--primary);color:var(--bg);padding:6px 16px;border-radius:20px;font-size:var(--fs-sm);font-weight:600;display:inline-flex;align-items:center;gap:6px;box-shadow:0 4px 12px rgba(var(--primary-rgb),.2);border:1px solid rgba(255,255,255,.1)}}
.blog-hero h1{{font-family:var(--font-heading);font-size:3.2rem;font-weight:850;line-height:1.1;letter-spacing:-.03em;color:var(--dark);margin:0}}
.blog-hero p{{color:var(--text-light);font-size:1.15rem;line-height:1.6;margin:0;max-width:540px}}
.hero-featured-col{{display:flex;justify-content:center;width:100%}}
.hero-featured{{background:var(--card-bg,#fff);border:1px solid var(--border);border-radius:16px;overflow:hidden;width:100%;max-width:460px;text-align:left;transition:all .3s cubic-bezier(0.4,0,0.2,1);box-shadow:0 10px 30px rgba(0,0,0,.04);display:block;text-decoration:none}}
.hero-featured:hover{{transform:translateY(-5px);box-shadow:0 20px 40px rgba(0,0,0,.08);border-color:var(--primary)}}
.hero-featured img{{width:100%;height:220px;object-fit:cover;transition:transform .5s ease;display:block}}
.hero-featured:hover img{{transform:scale(1.03)}}
.hero-featured .hf-body{{padding:20px 24px}}
.hero-featured .hf-body h3{{font-family:var(--font-heading);font-size:1.3rem;color:var(--dark);margin-bottom:8px;line-height:1.35;font-weight:700}}
.hero-featured .hf-body p{{font-size:var(--fs-sm);color:var(--text-light);margin:0}}

/* ─── BLOG CONTENT ─── */
.blog-content{{max-width:var(--content-max,960px);margin:0 auto;padding:32px 20px}}
.posts-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px}}
.post-card{{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);transition:transform .2s,box-shadow .2s;cursor:pointer;display:flex;flex-direction:column}}
.post-card:hover{{transform:translateY(-4px);box-shadow:var(--shadow-hover)}}
.card-image{{width:100%;height:200px;object-fit:cover;display:block}}
.card-image-placeholder{{width:100%;height:200px;background:linear-gradient(135deg,var(--dark2),var(--text-light));display:flex;align-items:center;justify-content:center;font-size:3rem;color:var(--primary)}}
.card-body{{padding:20px;flex:1;display:flex;flex-direction:column}}
.post-title{{font-family:var(--font-heading);font-size:var(--fs-md);margin-bottom:8px;color:var(--dark);letter-spacing:-.01em}}
.post-excerpt{{font-size:var(--fs-sm);color:var(--text-light);margin-bottom:12px;line-height:1.5;flex:1}}
.post-meta{{display:flex;gap:12px;flex-wrap:wrap;font-size:.8rem;color:var(--text-light);margin-bottom:10px}}
.post-meta span{{background:var(--bg-dark);padding:3px 10px;border-radius:12px}}
.post-tags{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}}
.tag{{background:{theme["tag_color"]};color:{theme["tag_text"]};padding:3px 10px;border-radius:12px;font-size:.75rem;border:1px solid {theme["tag_border"]}}}
.read-more{{display:inline-block;color:var(--primary);font-weight:600;font-size:.9rem;text-decoration:none;transition:color .2s;margin-top:auto}}
.read-more:hover{{color:var(--primary-dark)}}

/* ─── ARTICLE VIEW ─── */
.post-viewer{{max-width:var(--article-max,740px);margin:0 auto}}
.post-viewer .featured-image{{width:100%;max-height:420px;object-fit:cover;border-radius:var(--radius);margin-bottom:24px;box-shadow:var(--shadow)}}
.post-viewer h1{{font-family:var(--font-heading);font-size:var(--fs-lg);color:var(--dark);margin-bottom:8px;line-height:1.3;letter-spacing:-.02em}}
.post-viewer .post-meta-bar{{display:flex;gap:16px;flex-wrap:wrap;font-size:.9rem;color:var(--text-light);margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid var(--border)}}
.post-viewer .post-meta-bar .author{{color:var(--primary);font-weight:600}}
.post-viewer .post-content{{font-size:var(--fs-base);line-height:1.85;color:var(--text)}}
.post-viewer .post-content h2{{font-family:var(--font-heading);font-size:var(--fs-md);margin:28px 0 12px;color:var(--dark)}}
.post-viewer .post-content h3{{font-size:1.2rem;margin:24px 0 10px;color:var(--dark)}}
.post-viewer .post-content p{{margin-bottom:16px}}
.post-viewer .post-content blockquote{{border-left:3px solid var(--primary);padding:12px 20px;margin:16px 0;background:rgba(var(--primary-rgb),.06);border-radius:0 var(--radius-sm) var(--radius-sm) 0;font-style:italic;color:var(--text-light)}}
.post-viewer .post-content img{{max-width:100%;border-radius:var(--radius-sm);margin:16px 0}}

/* ─── NEWSLETTER ─── */
.newsletter-inline{{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);padding:2rem;margin:2.5rem 0;text-align:center}}
.newsletter-inline h3{{font-family:var(--font-heading);font-size:var(--fs-md);color:var(--dark);margin-bottom:4px}}
.newsletter-inline p{{font-size:var(--fs-sm);color:var(--text-light);margin-bottom:1rem}}
.newsletter-form{{display:flex;gap:.5rem;max-width:480px;margin:0 auto}}
.newsletter-form input{{flex:1;padding:.75rem 1rem;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:var(--fs-sm);font-family:inherit;background:var(--bg);color:var(--text)}}
.newsletter-form input:focus{{outline:none;border-color:var(--primary)}}
.newsletter-form button{{padding:.75rem 1.25rem;background:var(--primary);color:var(--bg);border:none;border-radius:var(--radius-sm);font-weight:600;cursor:pointer;font-size:var(--fs-sm);transition:opacity .2s}}
.newsletter-form button:hover{{opacity:.9}}
@media(max-width:640px){{.newsletter-form{{flex-direction:column}}}}

/* ─── COOKIE BANNER ─── */
.cookie-banner{{position:fixed;bottom:1rem;left:1rem;right:1rem;max-width:420px;background:var(--dark);color:#fff;padding:1.25rem;border-radius:var(--radius);box-shadow:0 10px 40px rgba(0,0,0,.3);display:none;flex-direction:column;gap:.75rem;z-index:9999;font-size:var(--fs-sm);border:1px solid rgba(255,255,255,.1)}}
.cookie-banner.show{{display:flex}}
.cookie-banner p{{color:rgba(255,255,255,.7);line-height:1.5}}
.cookie-banner a{{color:var(--primary)}}
.cookie-actions{{display:flex;gap:.5rem;justify-content:flex-end}}
.cookie-banner button{{padding:.5rem 1rem;border-radius:var(--radius-sm);cursor:pointer;font-weight:500;border:none;font-size:var(--fs-sm);transition:opacity .2s}}
.cookie-accept{{background:var(--primary);color:var(--bg)}}
.cookie-reject{{background:transparent;color:rgba(255,255,255,.6);border:1px solid rgba(255,255,255,.15)!important}}
.cookie-banner button:hover{{opacity:.85}}

/* ─── READING PROGRESS ─── */
.reading-progress{{position:fixed;top:0;left:0;width:100%;height:3px;background:transparent;z-index:1001;pointer-events:none}}
.reading-progress-bar{{height:100%;background:linear-gradient(90deg,var(--primary),var(--accent,var(--primary)));transform-origin:left;transform:scaleX(0)}}

/* ─── SCROLL ANIMATIONS ─── */
.scroll-fade{{opacity:0;transform:translateY(24px);transition:opacity .6s ease-out,transform .6s ease-out;will-change:opacity,transform}}
.scroll-fade.is-visible{{opacity:1;transform:translateY(0)}}

/* ─── SKELETON ─── */
@keyframes shimmer{{0%{{background-position:200% 0}}100%{{background-position:-200% 0}}}}
.skeleton{{background:linear-gradient(90deg,var(--border) 25%,var(--bg-dark) 50%,var(--border) 75%);background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:4px}}
.skeleton-text{{height:1rem;width:100%;margin-bottom:.5rem}}
.skeleton-title{{height:1.75rem;width:70%;margin-bottom:1rem}}

/* ─── FOOTER ─── */
.site-footer{{background:var(--dark);border-top:1px solid rgba(255,255,255,.06);padding:48px 20px 24px;margin-top:48px;color:rgba(255,255,255,.7)}}
.footer-grid{{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px}}
.footer-brand .logo-icon{{margin-bottom:8px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;background:var(--primary);border-radius:8px}}
.footer-brand svg{{width:22px;height:22px}}
.footer-brand strong{{display:block;font-size:16px;color:#fff;margin-bottom:6px}}
.footer-brand p{{font-size:13px;line-height:1.6;color:rgba(255,255,255,.5)}}
.footer-links h4,.footer-social h4{{font-size:12px;font-weight:600;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px}}
.footer-links a{{display:block;padding:4px 0;font-size:13px;color:rgba(255,255,255,.6);transition:color .15s ease}}
.footer-links a:hover{{color:#fff}}
.social-links{{display:flex;gap:8px}}
.social-links a{{width:36px;height:36px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.06);border-radius:8px;font-size:16px;color:rgba(255,255,255,.6);transition:all .15s ease}}
.social-links a:hover{{background:rgba(var(--primary-rgb),.15);color:var(--primary)}}
.footer-bottom{{max-width:1200px;margin:32px auto 0;padding-top:16px;border-top:1px solid rgba(255,255,255,.06);text-align:center;font-size:12px;color:rgba(255,255,255,.35)}}
.breadcrumb{{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--text-light);margin-bottom:20px;flex-wrap:wrap}}
.breadcrumb a{{color:var(--text-light);text-decoration:none;transition:color .15s ease}}
.breadcrumb a:hover{{color:var(--primary)}}
.breadcrumb .sep{{color:var(--text-light);font-size:10px}}
.breadcrumb .current{{color:var(--dark);font-weight:500}}
.related-section{{margin-top:48px;padding-top:32px;border-top:2px solid var(--border)}}
.related-section h3{{font-size:20px;font-weight:700;margin-bottom:20px;color:var(--dark)}}
.related-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}}
.related-card{{background:var(--bg);border:1px solid var(--border);border-radius:10px;overflow:hidden;transition:all .2s ease;display:flex;flex-direction:column}}
.related-card:hover{{transform:translateY(-3px);box-shadow:var(--shadow-hover)}}
.related-card .card-image{{height:130px}}
.related-card .card-image-placeholder{{height:130px;font-size:32px}}
.related-card .card-body{{padding:12px}}
.related-card .post-title{{font-size:14px}}
.related-card .post-meta{{font-size:10px;gap:8px}}
.empty-state,.error-state{{text-align:center;padding:60px 20px;color:var(--text-light)}}
.empty-state .icon,.error-state .icon{{font-size:48px;margin-bottom:16px;opacity:.5}}
.empty-state p,.error-state p{{font-size:14px}}
.blog-stats{{font-size:12px;color:var(--text-light);margin-top:8px}}
.admin-link{{position:fixed;bottom:20px;right:20px;width:40px;height:40px;background:var(--dark);border:1px solid rgba(255,255,255,.1);border-radius:50%;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,.5);font-size:16px;z-index:99;transition:all .15s ease}}
.admin-link:hover{{background:var(--primary);color:var(--bg)}}

/* ─── MOBILE ─── */
@media(max-width:768px){{
body{{padding-top:56px}}
.header-inner{{height:56px;padding:0 12px;gap:12px}}
.logo-text{{font-size:15px}}
.header-nav{{display:none;position:absolute;top:56px;left:0;right:0;background:var(--dark);border-bottom:1px solid rgba(255,255,255,.08);padding:8px;flex-direction:column}}
.header-nav.open{{display:flex}}
.nav-link{{width:100%;padding:10px 14px}}
.menu-toggle{{display:flex}}
.footer-grid{{grid-template-columns:1fr 1fr}}
.hero-inner-split{{grid-template-columns:1fr;gap:24px}}
.hero-brand-col{{align-items:center;text-align:center}}
.blog-hero{{padding:3.5rem 1.25rem}}
.blog-hero h1{{font-size:2.3rem}}
.posts-grid{{grid-template-columns:1fr}}
.post-viewer h1{{font-size:var(--fs-md)}}
.post-content{{font-size:var(--fs-sm)}}
}}
"""

    return css
