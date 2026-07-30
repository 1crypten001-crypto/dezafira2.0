"""
🎨 Brand Themes — Identidade Visual por Nicho.

Cada nicho de blog tem seu próprio tema de cores, fontes e ícones.
O tema é selecionado automaticamente baseado no campo "nicho" do blog.
"""

import unicodedata
import re

# ═══════════════════════════════════════════════════════════════════════════════
# DEFINIÇÃO DE TEMAS
# ═══════════════════════════════════════════════════════════════════════════════

THEMES = {
    "cristao": {
        "name": "Fé & Tradição",
        "niche_keywords": ["ensinamentos de jesus", "bíblia", "cristão", "crista", "evangelho",
                          "oração", "oração", "jesus", "deus", "espírito santo", "espirito santo",
                          "fé", "igreja", "reino de deus"],
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
        "fonts": {
            "heading": "'Playfair Display', serif",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#10013;",  # ✝ cross
        "header_bg": "linear-gradient(135deg, #1a1410, #2a2219)",
        "header_symbol": "&#10013;",
        "placeholder_icon": "&#10013;",
        "tag_color": "rgba(212,168,83,0.12)",
        "tag_text": "#a67c2e",
        "tag_border": "rgba(212,168,83,0.2)",
        "footer_year": None,  # Usa o nome do blog
    },
    "financas": {
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
        "fonts": {
            "heading": "'Inter', system-ui, sans-serif",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#128176;",  # 💰 money bag
        "header_bg": "linear-gradient(135deg, #022c22, #064e3b)",
        "header_symbol": "&#128200;",  # 📈 chart
        "placeholder_icon": "&#128176;",
        "tag_color": "rgba(5,150,105,0.12)",
        "tag_text": "#047857",
        "tag_border": "rgba(5,150,105,0.2)",
        "footer_year": None,
    },
    "saude": {
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
        "fonts": {
            "heading": "'Merriweather', serif",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#127793;",  # 🌱 seedling
        "header_bg": "linear-gradient(135deg, #052e16, #166534)",
        "header_symbol": "&#129496;",  # 🧘 person in lotus
        "placeholder_icon": "&#127793;",
        "tag_color": "rgba(22,163,74,0.12)",
        "tag_text": "#15803d",
        "tag_border": "rgba(22,163,74,0.2)",
        "footer_year": None,
    },
    "tecnologia": {
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
        "fonts": {
            "heading": "'JetBrains Mono', monospace",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#128187;",  # 💻 laptop
        "header_bg": "linear-gradient(135deg, #0f172a, #1e3a5f)",
        "header_symbol": "&#9881;",  # ⚙ gear
        "placeholder_icon": "&#128187;",
        "tag_color": "rgba(59,130,246,0.12)",
        "tag_text": "#2563eb",
        "tag_border": "rgba(59,130,246,0.2)",
        "footer_year": None,
    },
    "casa": {
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
        "fonts": {
            "heading": "'Lora', serif",
            "body": "'Inter', system-ui, sans-serif",
        },
        "header_icon": "&#127968;",  # 🏠 house
        "header_bg": "linear-gradient(135deg, #1c1917, #292524)",
        "header_symbol": "&#128083;",  # 👓
        "placeholder_icon": "&#127968;",
        "tag_color": "rgba(217,119,6,0.12)",
        "tag_text": "#b45309",
        "tag_border": "rgba(217,119,6,0.2)",
        "footer_year": None,
    },
}

DEFAULT_THEME = {
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
    "fonts": {
        "heading": "'Inter', system-ui, sans-serif",
        "body": "'Inter', system-ui, sans-serif",
    },
    "header_icon": "&#128214;",
    "header_bg": "linear-gradient(135deg, #0f172a, #1e293b)",
    "header_symbol": "&#128221;",
    "placeholder_icon": "&#128214;",
    "tag_color": "rgba(79,70,229,0.12)",
    "tag_text": "#4338ca",
    "tag_border": "rgba(79,70,229,0.2)",
    "footer_year": None,
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


def generate_theme_css(nicho: str, blog_name: str = "") -> str:
    """Generate CSS variables for a blog based on its niche."""
    theme = detect_theme(nicho)
    c = theme["colors"]
    f = theme["fonts"]

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

    css = f"""{font_url}
:root{{
--primary:{c["primary"]};--primary-light:{c["primary_light"]};--primary-dark:{c["primary_dark"]};
--bg:{c["bg"]};--bg-dark:{c["bg_dark"]};
--dark:{c["dark"]};--dark2:{c["dark2"]};
--text:{c["text"]};--text-light:{c["text_light"]};
--accent:{c["accent"]};--border:{c["border"]};
--radius:12px;--radius-sm:8px;--shadow:0 2px 20px rgba(0,0,0,0.08);
--font-heading:{f["heading"]};--font-body:{f["body"]};
}}
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--font-body);background:var(--bg);color:var(--text);line-height:1.7}}
a{{color:var(--primary);text-decoration:none}}a:hover{{color:var(--primary-dark)}}
.blog-header{{background:{theme["header_bg"]};padding:60px 24px 32px;text-align:center;position:relative;overflow:hidden}}
.blog-header::before{{content:'{header_symbol}';position:absolute;font-size:300px;opacity:0.04;top:-80px;right:-40px;color:var(--primary)}}
.blog-header h1{{font-family:var(--font-heading);font-size:2.5rem;color:var(--primary);margin-bottom:8px;letter-spacing:-0.02em}}
.blog-header p{{color:var(--text-light);font-size:1.05rem;max-width:600px;margin:0 auto}}
.blog-stats{{display:flex;gap:12px;justify-content:center;margin-top:16px;flex-wrap:wrap}}
.blog-stats span{{background:rgba(255,255,255,0.08);padding:6px 14px;border-radius:20px;font-size:.85rem;color:var(--primary-light)}}
.blog-content{{max-width:960px;margin:0 auto;padding:32px 20px}}
.back-link{{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:var(--bg-dark);border-radius:var(--radius-sm);font-size:.9rem;font-weight:500;margin-bottom:20px;color:var(--text)}}
.back-link:hover{{background:var(--border)}}
.posts-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:20px}}
@media(max-width:640px){{.posts-grid{{grid-template-columns:1fr}}}}
.post-card{{background:#fff;border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);transition:transform .2s,box-shadow .2s;cursor:pointer}}
.post-card:hover{{transform:translateY(-3px);box-shadow:0 8px 30px rgba(0,0,0,0.12)}}
.card-image{{width:100%;height:200px;object-fit:cover;display:block}}
.card-image-placeholder{{width:100%;height:200px;background:linear-gradient(135deg,var(--dark2),var(--text-light));display:flex;align-items:center;justify-content:center;font-size:3rem;color:var(--primary)}}
.card-body{{padding:20px}}
.post-title{{font-family:var(--font-heading);font-size:1.2rem;margin-bottom:8px;color:var(--dark);letter-spacing:-0.01em}}
.post-excerpt{{font-size:.9rem;color:var(--text-light);margin-bottom:12px;line-height:1.5}}
.post-meta{{display:flex;gap:12px;flex-wrap:wrap;font-size:.8rem;color:var(--text-light);margin-bottom:10px}}
.post-meta span{{background:var(--bg);padding:3px 10px;border-radius:12px}}
.post-tags{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}}
.tag{{background:{theme["tag_color"]};color:{theme["tag_text"]};padding:3px 10px;border-radius:12px;font-size:.75rem;border:1px solid {theme["tag_border"]}}}
.read-more{{display:inline-block;color:var(--primary);font-weight:600;font-size:.9rem;text-decoration:none;transition:color .2s}}
.read-more:hover{{color:var(--primary-dark)}}
.post-viewer{{max-width:780px;margin:0 auto}}
.post-viewer .featured-image{{width:100%;max-height:420px;object-fit:cover;border-radius:var(--radius);margin-bottom:24px;box-shadow:var(--shadow)}}
.post-viewer h1{{font-family:var(--font-heading);font-size:2rem;color:var(--dark);margin-bottom:8px;line-height:1.3;letter-spacing:-0.02em}}
.post-viewer .post-meta-bar{{display:flex;gap:16px;flex-wrap:wrap;font-size:.9rem;color:var(--text-light);margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid var(--border)}}
.post-viewer .post-content{{font-size:1.05rem;line-height:1.85;color:var(--text)}}
.post-viewer .post-content h2{{font-family:var(--font-heading);font-size:1.5rem;margin:28px 0 12px;color:var(--dark)}}
.post-viewer .post-content h3{{font-size:1.2rem;margin:24px 0 10px;color:var(--dark)}}
.post-viewer .post-content p{{margin-bottom:16px}}
.post-viewer .post-content blockquote{{border-left:3px solid var(--primary);padding:12px 20px;margin:16px 0;background:rgba(0,0,0,0.03);border-radius:0 var(--radius-sm) var(--radius-sm) 0;font-style:italic;color:var(--text-light)}}
.post-viewer .post-content img{{max-width:100%;border-radius:var(--radius-sm);margin:16px 0}}
.empty-state,.error-state{{text-align:center;padding:60px 20px;color:var(--text-light)}}
.empty-state .icon,.error-state .icon{{font-size:3rem;margin-bottom:12px}}
.blog-footer{{background:var(--dark);color:var(--text-light);padding:40px 24px;margin-top:40px;text-align:center}}
.blog-footer a{{color:var(--primary);text-decoration:none;margin:0 12px;font-size:.9rem}}
.blog-footer a:hover{{color:var(--primary-light)}}
.blog-footer p{{font-size:.8rem;margin-top:12px;color:var(--text-light);opacity:0.6}}
.footer-links{{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-bottom:12px;font-size:.85rem}}
.admin-link{{position:fixed;bottom:20px;right:20px;background:var(--dark);color:var(--primary);padding:10px 18px;border-radius:var(--radius);font-size:.85rem;text-decoration:none;opacity:.7;z-index:100;transition:opacity .2s}}
.admin-link:hover{{opacity:1}}"""

    return css
