"""
Server-rendered blog viewer HTML generator v2.
Gera HTML completo com artigos (SEO-friendly, sem depender de JavaScript).
Usa sistema de temas visuais por nicho (brand_themes.py).
v2: dark mode, scroll animations, reading progress, newsletter, cookie banner, hero, SVG logos.
"""

import json
from datetime import datetime
import html as html_mod
from modules.brand_themes import detect_theme, generate_theme_css, get_favicon_svg, get_logo_svg
from urllib.parse import quote


def esc(text):
    return html_mod.escape(str(text or ""))


def fmt_date(d):
    if not d:
        return ""
    try:
        dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(d)[:10]


def _apply_brand_overrides(blog_info: dict, theme_css: str) -> tuple[str, dict]:
    """Retorna (theme_css_atualizado, brand_config_dict) após aplicar customizações do Seu Design."""
    import json
    brand_config = None
    if blog_info and blog_info.get("brand_config"):
        try:
            brand_config = json.loads(blog_info["brand_config"])
        except Exception:
            pass
            
    if not brand_config:
        return theme_css, {}
        
    c = brand_config.get("colors", {})
    cd = brand_config.get("colors_dark", c)
    f = brand_config.get("fonts", {})
    
    font_imports = []
    for font_key in ["heading", "body"]:
        font_family = f.get(font_key, "")
        if font_family and ("'" in font_family or '"' in font_family):
            font_name = font_family.replace("'", "").replace('"', "").split(",")[0].strip()
            font_name_api = font_name.replace(" ", "+")
            font_imports.append(f"family={font_name_api}:wght@300;400;500;600;700;800")
            
    font_import_css = ""
    if font_imports:
        queries = "&".join(font_imports)
        font_import_css = f'@import url("https://fonts.googleapis.com/css2?{queries}&display=swap");\n'

    css_overrides = ":root {\n"
    for k, v in c.items():
        css_overrides += f"  --{k}: {v} !important;\n"
    css_overrides += f"  --header-bg: {c.get('dark2', '#0f172a')} !important;\n"
    if "heading" in f:
        css_overrides += f"  --font-heading: {f['heading']} !important;\n"
    if "body" in f:
        css_overrides += f"  --font-body: {f['body']} !important;\n"
    
    # Extrair RGB
    prim_hex = c.get("primary", "")
    if prim_hex.startswith("#") and len(prim_hex) == 7:
        try:
            r = int(prim_hex[1:3], 16)
            g = int(prim_hex[3:5], 16)
            b = int(prim_hex[5:7], 16)
            css_overrides += f"  --primary-rgb: {r},{g},{b} !important;\n"
        except Exception:
            pass
            
    css_overrides += "}\n"
    
    css_overrides += "html[data-theme=\"dark\"] {\n"
    for k, v in cd.items():
        css_overrides += f"  --{k}: {v} !important;\n"
    css_overrides += f"  --header-bg: {cd.get('bg_dark', '#0f172a')} !important;\n"
    css_overrides += "}\n"
    
    custom_bg = brand_config.get("custom_bg") if brand_config else None
    if custom_bg:
        css_overrides += f"""
        body {{
            background-image: 
                linear-gradient(to right, var(--bg) 0%, var(--bg) 35%, rgba(15, 23, 42, 0.4) 60%, rgba(15, 23, 42, 0.1) 100%),
                linear-gradient(to bottom, transparent 350px, var(--bg) 550px),
                url("{custom_bg}") !important;
            background-size: 100% 550px !important;
            background-repeat: no-repeat !important;
            background-attachment: scroll !important;
            background-position: top center !important;
        }}
        """
    
    return font_import_css + theme_css + "\n" + css_overrides, brand_config


# ─── COMMON JS SNIPPETS ─────────────────────────────────────────────

_DARK_MODE_JS = """
<script>
(function(){
  var d=document.documentElement,s='light';
  try{s=localStorage.getItem('theme')||'light';}catch(e){}
  d.setAttribute('data-theme',s);
})();
function toggleDark(){
  var d=document.documentElement;
  var t=d.getAttribute('data-theme');
  var n=t==='dark'?'light':'dark';
  d.setAttribute('data-theme',n);
  try{localStorage.setItem('theme',n);}catch(e){}
}
</script>"""

def _cookie_banner_html(slug: str = "") -> str:
    """Gera HTML do banner de cookies com link dinamico para a pagina de privacidade."""
    privacy_url = f"/blog/{slug}/privacidade" if slug else "/privacidade"
    return f"""
<div class="cookie-banner" id="cookieBanner">
  <p>Usamos cookies para melhorar sua experiencia. Ao continuar, voce concorda com nossa <a href="{privacy_url}">Politica de Privacidade</a>.</p>
  <div class="cookie-actions">
    <button class="cookie-reject" onclick="document.getElementById('cookieBanner').classList.remove('show');document.cookie='cookieConsent=rejected;max-age=31536000;path=/'">Rejeitar</button>
    <button class="cookie-accept" onclick="document.getElementById('cookieBanner').classList.remove('show');document.cookie='cookieConsent=accepted;max-age=31536000;path=/'">Aceitar</button>
  </div>
</div>
<script>
(function(){{
  if(document.cookie.indexOf('cookieConsent')===-1){{document.getElementById('cookieBanner').classList.add('show');}}
}})();
</script>"""

_SCROLL_OBSERVER_JS = """
<script>
(function(){
  if('IntersectionObserver' in window){
    var observer=new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if(e.isIntersecting){e.target.classList.add('is-visible');observer.unobserve(e.target);}
      });
    },{threshold:0.1});
    document.querySelectorAll('.scroll-fade').forEach(function(el){observer.observe(el);});
  }else{
    document.querySelectorAll('.scroll-fade').forEach(function(el){el.classList.add('is-visible');});
  }
})();
</script>"""

_READING_PROGRESS_JS = """
<script>
(function(){
  var bar=document.getElementById('readingProgress');
  if(!bar)return;
  function update(){var s=document.documentElement.scrollTop||document.body.scrollTop;var h=document.documentElement.scrollHeight-document.documentElement.clientHeight;bar.style.transform='scaleX('+(h>0?s/h:0)+')';}
  window.addEventListener('scroll',update);update();
})();
</script>"""


# ─── BASE CSS ────────────────────────────────────────────────────────
_BASE_CSS = """
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:var(--font-body, 'Inter', -apple-system, sans-serif);background:var(--bg,#f8fafc);color:var(--text,#1e293b);min-height:100vh;padding-top:64px;transition:background .3s,color .3s}
h1,h2,h3,h4,h5,h6,.logo-text,.post-title,.logo-icon{font-family:var(--font-heading, 'Inter', -apple-system, sans-serif);color:var(--dark, #0f172a)}
a{color:inherit;text-decoration:none}
img{max-width:100%;height:auto}

/* ─── HEADER ─── */
.site-header{position:fixed;top:0;left:0;right:0;z-index:100;background:var(--header-bg,#0f172a);border-bottom:1px solid rgba(255,255,255,.08);backdrop-filter:blur(12px);transition:transform .3s ease,background .3s}
.header-inner{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:24px;padding:0 20px;height:64px}
.header-logo{display:flex;align-items:center;gap:10px;flex-shrink:0}
.logo-icon{width:34px;height:34px;display:flex;align-items:center;justify-content:center;background:var(--primary, #4f46e5);border-radius:8px;font-size:18px;color:#fff;font-weight:800;overflow:hidden}
.logo-icon svg{width:22px;height:22px}
.logo-text{font-size:18px;font-weight:700;color:#fff}
.header-nav{display:flex;align-items:center;gap:4px;flex:1;overflow-x:auto}
.nav-link{padding:8px 14px;border-radius:8px;font-size:13px;font-weight:500;color:rgba(255,255,255,.7);white-space:nowrap;transition:all .15s ease}
.nav-link:hover{background:rgba(255,255,255,.08);color:#fff}
.nav-link.active{background:rgba(var(--primary-rgb,79,70,229),.15);color:var(--primary, #4f46e5)}
.header-actions{display:flex;align-items:center;gap:8px;flex-shrink:0}
.search-toggle,.menu-toggle,.dark-toggle{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);color:rgba(255,255,255,.7);width:36px;height:36px;border-radius:8px;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;transition:all .15s ease}
.search-toggle:hover,.menu-toggle:hover,.dark-toggle:hover{background:rgba(255,255,255,.12);color:#fff}
.menu-toggle{display:none}
.dark-toggle{font-size:15px}
.search-bar{max-width:1200px;margin:0 auto;padding:12px 20px;display:flex;gap:8px;transition:all .3s ease}
.search-bar input{flex:1;padding:10px 14px;border-radius:8px;border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.06);color:#fff;font-size:14px;font-family:inherit;outline:none}
.search-bar input:focus{border-color:var(--primary, #4f46e5)}
.search-bar button{padding:10px 20px;border-radius:8px;border:none;background:var(--primary, #4f46e5);color:#fff;font-weight:600;font-size:13px;cursor:pointer}
.search-bar button:hover{opacity:.9}

/* ─── FOOTER ─── */
.site-footer{background:var(--header-bg,#0f172a);border-top:1px solid rgba(255,255,255,.06);padding:48px 20px 24px;margin-top:48px;color:rgba(255,255,255,.7);transition:background .3s}
.footer-grid{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px}
.footer-brand .logo-icon{margin-bottom:8px}
.footer-brand strong{display:block;font-size:16px;color:#fff;margin-bottom:6px}
.footer-brand p{font-size:13px;line-height:1.6;color:rgba(255,255,255,.5)}
.footer-links h4,.footer-social h4{font-size:12px;font-weight:600;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px}
.footer-links a{display:block;padding:4px 0;font-size:13px;color:rgba(255,255,255,.6);transition:color .15s ease}
.footer-links a:hover{color:#fff}
.social-links{display:flex;gap:8px}
.social-links a{width:36px;height:36px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.06);border-radius:8px;font-size:16px;color:rgba(255,255,255,.6);transition:all .15s ease}
.social-links a:hover{background:rgba(var(--primary-rgb,79,70,229),.15);color:var(--primary, #4f46e5)}
.footer-bottom{max-width:1200px;margin:32px auto 0;padding-top:16px;border-top:1px solid rgba(255,255,255,.06);text-align:center;font-size:12px;color:rgba(255,255,255,.35)}

/* ─── BLOG CONTENT ─── */
.blog-content{max-width:1200px;margin:0 auto;padding:32px 20px}
.posts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}
.post-card{background:var(--card-bg,#fff);border:1px solid var(--border,#e2e8f0);border-radius:12px;overflow:hidden;transition:all .2s ease;display:flex;flex-direction:column}
.post-card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.08)}
.card-image{width:100%;height:180px;object-fit:cover;object-position:center;background:var(--primary-light,#e0e7ff)}
body.mode-discover .card-image{height:auto;aspect-ratio:16/9}
body.mode-discover .card-image-placeholder{aspect-ratio:16/9;height:auto}
body.mode-discover .featured-image{aspect-ratio:16/9;max-height:none}
/* Badges de qualidade (score LiLi + status) */
.quality-badges{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;align-items:center}
.qb{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;font-size:10px;font-weight:700;line-height:1.4}
.qb-score{background:rgba(var(--primary-rgb,99,102,241),.12);color:var(--primary,#6366f1)}
.qb-score.good{background:rgba(34,197,94,.14);color:#16a34a}
.qb-score.mid{background:rgba(245,158,11,.14);color:#d97706}
.qb-score.bad{background:rgba(239,68,68,.14);color:#dc2626}
.qb-status{background:rgba(255,255,255,.06);color:rgba(255,255,255,.6)}
.qb-status.published{background:rgba(34,197,94,.14);color:#22c55e}
.qb-status.draft{background:rgba(148,163,184,.14);color:#94a3b8}
.card-image-placeholder{width:100%;height:180px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--primary-light,#e0e7ff),var(--primary,#6366f1));color:#fff;font-size:48px}
.card-body{padding:16px;flex:1;display:flex;flex-direction:column}
.post-title{font-size:15px;font-weight:600;color:var(--text,#1e293b);margin-bottom:8px;line-height:1.4}
.post-excerpt{font-size:13px;color:var(--text-light,#64748b);line-height:1.5;flex:1;margin-bottom:12px}
.post-meta{display:flex;gap:12px;font-size:11px;color:var(--text-light,#94a3b8);margin-bottom:8px}
.post-tags{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px}
.tag{padding:2px 8px;border-radius:6px;background:var(--tag-bg,#f1f5f9);color:var(--text-light,#64748b);font-size:10px;font-weight:500}
.read-more{font-size:13px;font-weight:600;color:var(--primary,#6366f1);margin-top:auto}

/* ─── ARTICLE VIEW ─── */
.post-viewer{max-width:740px;margin:0 auto}
.back-link{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:8px;background:var(--card-bg,#fff);border:1px solid var(--border,#e2e8f0);font-size:13px;font-weight:500;color:var(--text,#1e293b);margin-bottom:24px;transition:all .15s ease}
.back-link:hover{background:var(--tag-bg,#f1f5f9)}
.featured-image{width:100%;border-radius:12px;margin-bottom:24px;max-height:420px;object-fit:cover;object-position:center;background:var(--primary-light,#e0e7ff)}
.post-viewer h1{font-size:28px;font-weight:700;margin-bottom:12px;line-height:1.3}
.post-meta-bar{display:flex;flex-wrap:wrap;gap:12px 16px;font-size:13px;color:var(--text-light,#94a3b8);margin-bottom:16px}
.post-meta-bar .meta-item{display:inline-flex;align-items:center;gap:4px}
.post-meta-bar .author{color:var(--gold,#d4a853);font-weight:600}
.post-content{font-size:16px;line-height:1.8;color:var(--text,#334155)}
.post-content h2{font-size:22px;font-weight:700;margin:32px 0 12px}
.post-content h3{font-size:18px;font-weight:600;margin:24px 0 10px}
.post-content p{margin-bottom:16px}
.post-content blockquote{border-left:3px solid var(--gold,#d4a853);padding:12px 20px;margin:16px 0;background:rgba(212,168,83,.06);border-radius:0 8px 8px 0;font-style:italic}
.post-content ul,.post-content ol{padding-left:24px;margin-bottom:16px}
.post-content li{margin-bottom:6px}
.post-content table{display:block;width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;border-collapse:collapse;margin-bottom:16px}
.post-content pre{overflow-x:auto;max-width:100%}

/* ─── BREADCRUMB ─── */
.breadcrumb{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--text-light,#94a3b8);margin-bottom:20px;flex-wrap:wrap}
.breadcrumb a{color:var(--text-light,#94a3b8);text-decoration:none;transition:color .15s ease}
.breadcrumb a:hover{color:var(--gold,#d4a853)}
.breadcrumb .sep{color:var(--text-light,#cbd5e1);font-size:10px}
.breadcrumb .current{color:var(--text,#1e293b);font-weight:500}

/* ─── RELATED ─── */
.related-section{margin-top:48px;padding-top:32px;border-top:2px solid var(--border,#e2e8f0)}
.related-section h3{font-size:20px;font-weight:700;margin-bottom:20px;color:var(--text,#1e293b)}
.related-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
.related-card{background:var(--card-bg,#fff);border:1px solid var(--border,#e2e8f0);border-radius:10px;overflow:hidden;transition:all .2s ease;display:flex;flex-direction:column}
.related-card:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.06)}
.related-card .card-image{height:130px}
.related-card .card-image-placeholder{height:130px;font-size:32px}
.related-card .card-body{padding:12px}
.related-card .post-title{font-size:14px}
.related-card .post-meta{font-size:10px;gap:8px}

/* ─── EMPTY / ERROR ─── */
.empty-state,.error-state{text-align:center;padding:60px 20px;color:var(--text-light,#94a3b8)}
.empty-state .icon,.error-state .icon{font-size:48px;margin-bottom:16px;opacity:.5}
.empty-state p,.error-state p{font-size:14px}
.blog-stats{font-size:12px;color:var(--text-light,#94a3b8);margin-top:8px}

/* ─── ADMIN LINK (REMOVIDO) ─── */
.admin-link{display:none!important}

/* ─── HERO SHADOW CONTRAST ─── */
.hero-brand-col h1 {
    text-shadow: 0 2px 14px rgba(0,0,0,0.85) !important;
}
.hero-brand-col p {
    text-shadow: 0 1px 6px rgba(0,0,0,0.85) !important;
}
.hero-badge {
    text-shadow: 0 1px 4px rgba(0,0,0,0.5) !important;
}

/* ─── TABLE OF CONTENTS (SUMÁRIO AEVO-STYLE) ─── */
.table-of-contents{background:var(--card-bg,#fff);border:1px solid var(--border,#e2e8f0);border-left:4px solid var(--primary, #4f46e5);border-radius:10px;padding:18px 20px;margin:24px 0 32px;box-shadow:var(--shadow,0 4px 15px rgba(0,0,0,.04))}
.toc-title{font-size:14px;font-weight:700;color:var(--text,#1e293b);margin-bottom:10px;text-transform:uppercase;letter-spacing:.04em;display:flex;align-items:center;gap:6px}
.table-of-contents ul{list-style:none!important;padding-left:0!important;margin-bottom:0!important}
.table-of-contents li{margin-bottom:8px!important;font-size:14px;line-height:1.4}
.table-of-contents li:last-child{margin-bottom:0!important}
.table-of-contents a{color:var(--primary,#6366f1);text-decoration:none;font-weight:500;transition:color .15s ease}
.table-of-contents a:hover{color:var(--accent, var(--primary,#6366f1));text-decoration:underline}

/* ─── AUTHOR BOX (E-E-A-T) ─── */
.author-box{display:flex;gap:16px;background:var(--card-bg,#fff);border:1px solid var(--border,#e2e8f0);border-radius:12px;padding:20px;margin:40px 0 24px;align-items:center;box-shadow:var(--shadow,0 4px 15px rgba(0,0,0,.04))}
.author-avatar{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;color:#fff;flex-shrink:0;background:linear-gradient(135deg,var(--primary, #4f46e5),var(--accent,var(--primary, #4f46e5)));border:2px solid rgba(255,255,255,.2);box-shadow:0 4px 12px rgba(0,0,0,.1)}
.author-info{flex:1}
.author-title{font-size:14px;font-weight:700;color:var(--text,#1e293b);margin-bottom:4px}
.author-bio{font-size:13px;color:var(--text-light,#64748b);line-height:1.5;margin-bottom:0!important}

/* ─── LEIA MAIS INLINE ─── */
.leia-mais-inline{background:rgba(var(--primary-rgb,99,102,241),.06);border:1px solid rgba(var(--primary-rgb,99,102,241),.15);border-left:4px solid var(--primary,#6366f1);border-radius:8px;padding:12px 16px;margin:24px 0;font-size:14px;font-weight:600}
.leia-mais-inline a{color:var(--primary,#6366f1);text-decoration:none}
.leia-mais-inline a:hover{text-decoration:underline;color:var(--gold,#d4a853)}

/* ─── MOBILE ─── */
@media(max-width:768px){
  body{padding-top:56px}
  .header-inner{height:56px;padding:0 12px;gap:12px}
  .logo-text{font-size:15px}
  .header-nav{display:none;position:absolute;top:56px;left:0;right:0;background:var(--dark,#0f172a);border-bottom:1px solid rgba(255,255,255,.08);padding:8px;flex-direction:column}
  .header-nav.open{display:flex}
  .nav-link{width:100%;padding:10px 14px}
  .menu-toggle{display:flex}
  .footer-grid{grid-template-columns:1fr 1fr}
  .posts-grid{grid-template-columns:1fr}
  .post-viewer h1{font-size:22px}
  .post-content{font-size:15px}
  .author-box{flex-direction:column;text-align:center;padding:16px}
  .related-grid{grid-template-columns:1fr}
}
@media(max-width:480px){
  .footer-grid{grid-template-columns:1fr}
  .blog-content{padding:24px 12px}
  .post-viewer h1{font-size:20px}
  .header-inner{gap:8px}
  .header-logo .logo-text{max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .search-bar{padding:10px 12px}
  .breadcrumb{font-size:12px}
  .featured-image{border-radius:8px}
}
"""


# ─── CATEGORIES ──────────────────────────────────────────────────────

_CATEGORY_MAP = {
    "ensinamentos de jesus": ["Evangelhos", "Parabolas", "Milagres", "Ensinamentos", "Oracao"],
    "espirito santo": ["Frutos", "Dons", "Direcao", "Intimidade", "Poder"],
    "profecias": ["Apocalipse", "Vinda de Cristo", "Sinais", "Israel", "Sonhos"],
    "financas": ["Investimentos", "Economia", "Planejamento", "Renda Fixa", "Mercado"],
    "tecnologia": ["Programacao", "Inteligencia Artificial", "Ferramentas", "Tutoriais", "Reviews"],
    "saude": ["Bem-estar", "Nutricao", "Exercicios", "Saude Mental", "Prevencao"],
    "empreendedorismo": ["Startups", "Marketing Digital", "Vendas", "Gestao", "Inovacao"],
    "educacao": ["Estudo", "Carreira", "Cursos", "Metodologias", "Dicas de Estudo"],
    "culinaria": ["Receitas", "Ingredientes", "Tecnicas", "Bebidas", "Sobremesas"],
    "viagem": ["Destinos", "Roteiros", "Dicas", "Cultura", "Acomodacao"],
    "bem-estar": ["Meditacao", "Mindfulness", "Autocuidado", "Relacionamentos", "Equilibrio"],
    "marketing": ["Redes Sociais", "Conteudo", "SEO", "Anuncios", "Estrategia"],
    "devocional": ["Leitura Biblica", "Oracao", "Testemunhos", "Gratidao", "Fe"],
    "lifestyle": ["Produtividade", "Organizacao", "Minimalismo", "Habitos", "Inspiracao"],
}


def _get_categories(nicho: str) -> list:
    n = nicho.lower().strip()
    for key, cats in _CATEGORY_MAP.items():
        if key in n or n in key:
            return cats
    return ["Artigos", "Estudos", "Guias", "Noticias", "Dicas"]


# ─── PAGE FRAME v2 ───────────────────────────────────────────────────

def _page_frame(title: str, body_html: str, theme_css: str = "",
               description: str = "", image_url: str = "",
               canonical_url: str = "", schema_json: str = "",
               theme: dict = None, slug: str = "", brand_config: dict = None,
               body_class: str = "") -> str:
    """Gera pagina HTML completa com SEO, dark mode, e branding profissional.
    slug: usado para link dinamico no cookie banner.
    """
    requested_fonts = ["Inter:wght@300;400;500;600;700;800"]
    if brand_config and brand_config.get("fonts"):
        for fkey, font_name in brand_config["fonts"].items():
            font_clean = font_name.split(",")[0].replace("'", "").replace('"', '').strip()
            if font_clean and font_clean not in ["Inter", "sans-serif", "serif", "system-ui"]:
                font_param = font_clean.replace(" ", "+")
                if font_clean in ["Lora", "Playfair Display", "Merriweather", "Playfair+Display"]:
                    requested_fonts.append(f"{font_param}:wght@400;600;700")
                else:
                    requested_fonts.append(f"{font_param}:wght@400;500;600;700;800")

    # Fallbacks baseados no CSS
    if "Playfair" in theme_css and not any("Playfair" in f for f in requested_fonts):
        requested_fonts.append("Playfair+Display:wght@400;700")
    if "Merriweather" in theme_css and not any("Merriweather" in f for f in requested_fonts):
        requested_fonts.append("Merriweather:wght@300;400;700")
    if "Lora" in theme_css and not any("Lora" in f for f in requested_fonts):
        requested_fonts.append("Lora:wght@400;600;700")
    if "JetBrains" in theme_css and not any("JetBrains" in f for f in requested_fonts):
        requested_fonts.append("JetBrains+Mono:wght@400;700")

    google_fonts = "&".join(f"family={f}" for f in requested_fonts)

    # Favicon profissional
    if brand_config and brand_config.get("custom_favicon"):
        favicon = brand_config["custom_favicon"]
    elif brand_config and brand_config.get("favicon_svg"):
        favicon = brand_config["favicon_svg"]
    elif theme:
        favicon = get_favicon_svg(theme.get("id", ""))
    else:
        favicon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%236366f1'/%3E%3Cpath d='M16 6v20M6 16h20' stroke='%23fff' stroke-width='2.5' stroke-linecap='round' fill='none'/%3E%3C/svg%3E"

    icon_type = 'type="image/svg+xml"'
    if favicon.startswith("data:image/png") or ".png" in favicon.lower():
        icon_type = 'type="image/png"'
    elif favicon.startswith("data:image/x-icon") or ".ico" in favicon.lower():
        icon_type = 'type="image/x-icon"'
    elif favicon.startswith("data:image/jpeg") or ".jpg" in favicon.lower() or ".jpeg" in favicon.lower():
        icon_type = 'type="image/jpeg"'

    # Apple touch icon (PNG fallback) + PWA manifest hints
    apple_touch = f'<link rel="apple-touch-icon" href="{favicon}">'
    theme_color = theme["colors"]["primary"] if theme else "#0f172a"

    desc_escaped = esc(description[:160]) if description else ""
    img_escaped = esc(image_url) if image_url else ""
    canonical = f'<link rel="canonical" href="{esc(canonical_url)}">' if canonical_url else ""
    og_tags = f"""
    <meta property="og:title" content="{esc(title[:90])}">
    <meta property="og:description" content="{desc_escaped}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{esc(canonical_url)}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(title[:90])}">
    <meta name="twitter:description" content="{desc_escaped}">""" if canonical_url else ""
    og_img = f'<meta property="og:image" content="{img_escaped}">\n    <meta name="twitter:image" content="{img_escaped}">' if img_escaped else ""
    schema_tag = f'<script type="application/ld+json">{schema_json}</script>' if schema_json else ""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="{theme_color}">
<title>{title}</title>
<meta name="description" content="{desc_escaped}">
{canonical}
{og_tags}
{og_img}
{schema_tag}
<link rel="icon" {icon_type} href="{favicon}">
{apple_touch}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?{google_fonts}&display=swap" rel="stylesheet">
{_DARK_MODE_JS}
<style>{_BASE_CSS}{theme_css}</style>
</head>
<body class="{body_class}">
{body_html}
{_cookie_banner_html(slug)}
</body>
</html>"""


# ─── HEADER v2 ───────────────────────────────────────────────────────

def _safe_logo_el(logo: str, img_style: str = "height:36px; max-width:180px; object-fit:contain;") -> str:
    """Retorna elemento de logo seguro: data URI/URL vira <img>, SVG inline volta intacto."""
    logo = (logo or "").strip()
    if not logo:
        return ""
    if logo.startswith("data:") or logo.startswith("http://") or logo.startswith("https://") or logo.startswith("/"):
        return f'<img src="{logo}" style="{img_style}" alt="" />'
    return logo  # SVG inline — seguro para embutir


def _get_header_html(slug: str, blog_name: str, blog_niche: str, current_cat: str = "", brand_config: dict = None) -> str:
    """Gera header fixo com logo SVG profissional, dark mode toggle, busca."""
    categories = _get_categories(blog_niche)
    theme = detect_theme(blog_niche)
    logo_svg = brand_config.get("logo_svg") if (brand_config and brand_config.get("logo_svg")) else get_logo_svg(blog_niche)
    custom_logo = brand_config.get("custom_logo") if brand_config else None
    if custom_logo:
        logo_markup = f'<img class="custom-logo" src="{custom_logo}" style="height:36px; max-width:180px; object-fit:contain;" alt="{blog_name}" />'
    else:
        logo_markup = f'<span class="logo-icon">{_safe_logo_el(logo_svg)}</span><span class="logo-text">{blog_name}</span>'

    nav_items = "".join(
        f'<a href="/blog/{slug}?cat={c.lower()}" class="nav-link{" active" if current_cat.lower() == c.lower() else ""}">{c}</a>'
        for c in categories
    )
    return f"""<header class="site-header">
  <div class="header-inner">
    <a href="/blog/{slug}" class="header-logo">
      {logo_markup}
    </a>
    <nav class="header-nav" id="mainNav">
      {nav_items}
    </nav>
    <div class="header-actions">
      <button class="search-toggle" onclick="var s=document.getElementById('searchBar');if(s)s.style.display=s.style.display==='none'?'flex':'none';" aria-label="Buscar">&#128269;</button>
      <button class="dark-toggle" onclick="toggleDark()" aria-label="Alternar tema">&#9790;</button>
      <button class="menu-toggle" onclick="var n=document.getElementById('mainNav');if(n)n.classList.toggle('open');" aria-label="Menu">&#9776;</button>
    </div>
  </div>
  <div class="search-bar" id="searchBar" style="display:none">
    <input type="text" id="searchInput" placeholder="Buscar artigos..." onkeydown="if(event.key==='Enter'){{var q=document.getElementById('searchInput');if(q&&q.value.trim())window.location='/blog/{slug}?q='+encodeURIComponent(q.value.trim());}}">
    <button onclick="var q=document.getElementById('searchInput');if(q&&q.value.trim())window.location='/blog/{slug}?q='+encodeURIComponent(q.value.trim());">Buscar</button>
  </div>
</header>"""


# ─── FOOTER v2 ───────────────────────────────────────────────────────

def _get_footer_html(slug: str, blog_name: str, blog_niche: str = "", year: str = None, brand_config: dict = None) -> str:
    """Gera footer com logo SVG, links reais e newsletter call-to-action."""
    if not year:
        year = str(datetime.now().year)
    theme = detect_theme(blog_niche)
    logo_svg = brand_config.get("logo_svg") if (brand_config and brand_config.get("logo_svg")) else get_logo_svg(blog_niche)
    custom_logo = brand_config.get("custom_logo") if brand_config else None
    if custom_logo:
        logo_markup = f'<img class="custom-logo" src="{custom_logo}" style="height:36px; max-width:180px; object-fit:contain; margin-bottom:12px;" alt="{blog_name}" />'
    else:
        logo_markup = f'<span class="logo-icon">{_safe_logo_el(logo_svg, img_style="height:36px; max-width:180px; object-fit:contain; margin-bottom:12px;")}</span><strong style="display:block;margin-top:4px;">{blog_name}</strong>'

    categories = _get_categories(blog_niche)
    cat_links = "".join(f'<a href="/blog/{slug}?cat={c.lower()}">{c}</a>' for c in categories[:4])
    niche_desc = blog_niche[:80] if blog_niche else "conhecimento e inspiracao"
    return f"""<footer class="site-footer">
  <div class="footer-grid">
    <div class="footer-brand">
      {logo_markup}
      <p>Blog dedicado a {niche_desc.lower()}.</p>
    </div>
    <div class="footer-links">
      <h4>Categorias</h4>
      {cat_links}
    </div>
    <div class="footer-links">
      <h4>Paginas</h4>
      <a href="/blog/{slug}/sobre">Sobre</a>
      <a href="/blog/{slug}/privacidade">Privacidade</a>
      <a href="/blog/{slug}/contato">Contato</a>
      <a href="/blog/{slug}/termos">Termos de Uso</a>
    </div>
    <div class="footer-social">
      <h4>Redes Sociais</h4>
      <div class="social-links">
        <a href="#" aria-label="Instagram">&#10070;</a>
        <a href="#" aria-label="Facebook">&#120143;</a>
        <a href="#" aria-label="YouTube">&#9654;</a>
      </div>
    </div>
  </div>
  <div class="footer-bottom">
    <p>&copy; {year} {blog_name} &mdash; Todos os direitos reservados</p>
  </div>
</footer>"""


# ─── PAGE GENERATORS v2 ──────────────────────────────────────────────

def generate_blog_list(slug: str, blog_info: dict, posts: list) -> str:
    """Gera HTML da pagina inicial com hero section + grade de artigos + scroll-fade."""
    blog_name = esc(blog_info["name"])
    blog_niche = esc(blog_info.get("nicho", ""))
    pcount = len(posts)
    theme = detect_theme(blog_info.get("nicho", ""))
    theme_css = generate_theme_css(blog_info.get("nicho", ""), blog_name)
    theme_css, brand_config = _apply_brand_overrides(blog_info, theme_css)
    placeholder_icon = theme.get("placeholder_icon", "&#128214;")
    subdomain_html = ""

    # Hero — artigo mais recente em destaque no formato Split-Screen
    hero_html = ""
    if posts:
        top = posts[0]
        wc = top.get("word_count", 0) or 0
        rt = max(1, round(wc / 200))
        img = top.get("featured_image_url")
        img_tag = f'<img src="{esc(img)}" alt="{esc(top["title"])}" loading="eager">' if img else f'<div class="card-image-placeholder">{placeholder_icon}</div>'
        
        hero_img = theme.get("hero_image_url", "")
        # Degradê dinâmico usando var(--bg) que se adapta perfeitamente ao Light/Dark mode
        hero_style = f"style=\"background: linear-gradient(to right, var(--bg) 40%, rgba(var(--primary-rgb), 0.08) 100%), url('{hero_img}');\"" if hero_img else ""
        
        hero_html = f"""
    <div class="blog-hero" {hero_style}>
      <div class="hero-inner-split">
        <div class="hero-brand-col">
          <span class="hero-badge">★ Artigo em Destaque</span>
          <h1>{blog_name}</h1>
          <p>Artigos, estudos e reflexões sobre {blog_niche.lower()}.</p>
        </div>
        <div class="hero-featured-col">
          <a href="/blog/{slug}?post={esc(top["id"])}" class="hero-featured">
            {img_tag}
            <div class="hf-body">
              <h3>{esc(top["title"])}</h3>
              <p>📅 {fmt_date(top.get("created_at"))} &middot; {rt} min de leitura</p>
            </div>
          </a>
        </div>
      </div>
    </div>"""

    # Card grid com scroll-fade
    cards_html = ""
    for i, p in enumerate(posts):
        wc = p.get("word_count", 0) or 0
        rt = max(1, round(wc / 200))
        excerpt = esc(p.get("excerpt", "")[:200])
        img = p.get("featured_image_url")
        if img:
            img_tag = f'<img class="card-image" src="{esc(img)}" alt="{esc(p["title"])}" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
        else:
            img_tag = f'<div class="card-image-placeholder">{placeholder_icon}</div>'
        dt_str = fmt_date(p.get("created_at"))
        tags = "".join(f'<span class="tag">{esc(k.strip())}</span>' for k in (p.get("keywords") or "").split(",")[:3] if k.strip())
        pid = esc(p["id"])
        tit = esc(p["title"])

        # Badges de qualidade (score LiLi + status)
        _lsc = p.get("lili_score")
        _st = (p.get("status") or "draft")
        _badges_html = ""
        if _lsc is not None:
            _bcls = "good" if _lsc >= 80 else ("mid" if _lsc >= 50 else "bad")
            _badges_html += f'<span class="qb qb-score {_bcls}">🌸 {_lsc}/100</span>'
        _badges_html += f'<span class="qb qb-status {"published" if _st == "published" else "draft"}">{"✓ Publicado" if _st == "published" else "⏳ Rascunho"}</span>'
        badges = f'<div class="quality-badges">{_badges_html}</div>'

        # Delay nos primeiros cards para efeito cascata
        delay = min(i * 0.1, 1.0)
        cards_html += f"""
        <a href="/blog/{slug}?post={pid}" class="post-card scroll-fade" style="transition-delay:{delay}s">
          {img_tag}
          <div class="card-body">
            <h2 class="post-title">{tit}</h2>
            <p class="post-excerpt">{excerpt}</p>
            <div class="post-meta">
              <span>&#128197; {dt_str}</span>
              <span>&#128196; {wc} palavras</span>
              <span>&#9201; {rt} min</span>
            </div>
            {badges}
            {f'<div class="post-tags">{tags}</div>' if tags else ''}
            <span class="read-more">Ler artigo &rarr;</span>
          </div>
        </a>"""

    posts_html = (f'<div class="posts-grid">{cards_html}</div>' if cards_html
                  else f'<div class="empty-state"><div class="icon">{placeholder_icon}</div><p>Nenhum artigo publicado ainda. Volte em breve!</p></div>')

    desc = f"Blog sobre {blog_niche}. Artigos, estudos e reflexões." if blog_niche else blog_name
    canonical = f"https://dezafira.com.br/blog/{slug}"

    body = f"""{_get_header_html(slug, blog_info["name"], blog_info.get("nicho", ""), brand_config=brand_config)}
{hero_html}
<main class="blog-content">
  <h2 style="font-family:var(--font-heading,inherit);font-size:1.5rem;margin-bottom:20px">&#128214; Todos os Artigos</h2>
  <div class="blog-stats" style="margin-bottom:20px">{pcount} artigo{"s" if pcount != 1 else ""}</div>
  {posts_html}
</main>
{_get_footer_html(slug, blog_info["name"], blog_info.get("nicho", ""), brand_config=brand_config)}
{_SCROLL_OBSERVER_JS}"""

    title = f"{blog_name} &mdash; Blog sobre {blog_niche}" if blog_niche else blog_name
    _discover = blog_info.get("is_discover", False)
    return _page_frame(title, body, theme_css, description=desc, canonical_url=canonical, theme=theme, slug=slug, brand_config=brand_config,
                       body_class="mode-discover" if _discover else "")


def generate_article_view(slug: str, blog_info: dict, post: dict, related_posts: list = None) -> str:
    """Gera HTML de artigo individual com newsletter, progress bar, sumario dinâmico (TOC) e author box."""
    import re
    blog_name = esc(blog_info["name"])
    blog_niche = esc(blog_info.get("nicho", ""))
    raw_title = post["title"]
    title = esc(raw_title)
    content = post.get("content", "")
    excerpt = esc(post.get("excerpt", "")[:200])
    img = post.get("featured_image_url")
    wc = post.get("word_count", 0) or 0
    rt = max(1, round(wc / 200))
    dt_str = fmt_date(post.get("created_at"))
    keywords = post.get("keywords", "")
    tags = "".join(f'<span class="tag">{esc(k.strip())}</span>' for k in keywords.split(",") if k.strip())
    author_name = esc(post.get("author") or blog_info.get("name", "Equipe"))
    _lsc_art = post.get("lili_score")
    if _lsc_art is not None:
        _bcls_art = "good" if _lsc_art >= 80 else ("mid" if _lsc_art >= 50 else "bad")
        score_chip = f'<span class="meta-item qb qb-score {_bcls_art}">🌸 {_lsc_art}/100</span>'
    else:
        score_chip = ""

    theme = detect_theme(blog_info.get("nicho", ""))
    theme_css = generate_theme_css(blog_info.get("nicho", ""), blog_name)
    theme_css, brand_config = _apply_brand_overrides(blog_info, theme_css)
    placeholder_icon = theme.get("placeholder_icon", "&#128214;")

    is_affiliate = blog_info.get("is_affiliate", False)
    if is_affiliate:
        theme_css += """
        /* === AFFILIATE CRO CSS === */
        .blog-content { max-width: 800px !important; margin: 0 auto; display: block; }
        .sidebar { display: none !important; }
        .post-viewer { width: 100% !important; border: none; padding: 10px; box-shadow: none; }
        .post-content a[href^="http"] { 
            display: block; 
            background: #25d366; 
            color: #fff !important; 
            padding: 16px 24px; 
            border-radius: 8px; 
            font-weight: 800; 
            text-align: center; 
            text-decoration: none; 
            margin: 30px auto; 
            width: 100%; 
            max-width: 500px; 
            box-sizing: border-box; 
            box-shadow: 0 6px 12px rgba(37,211,102,0.3); 
            font-size: 18px; 
            text-transform: uppercase; 
            transition: all 0.2s;
            border-bottom: 4px solid #1da851;
        }
        .post-content a[href^="http"]:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 16px rgba(37,211,102,0.4); 
            text-decoration: none;
            border-bottom-width: 6px;
        }
        .post-content h2, .post-content h3 { text-align: left; margin-top: 40px; }
        .post-content p { font-size: 18px; line-height: 1.8; color: #1e293b; margin-bottom: 20px; }
        .featured-image { border-radius: 12px; margin-bottom: 30px; width: 100%; height: auto; }
        h1 { font-size: 36px; text-align: center; margin-bottom: 24px; font-weight: 800; line-height: 1.3; }
        .post-content table { width: 100%; border-collapse: collapse; margin: 24px 0; font-size: 16px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .post-content th { background: #0f172a; color: #fff; font-weight: 700; padding: 12px 16px; text-align: left; }
        .post-content td { border: 1px solid #e2e8f0; padding: 12px 16px; }
        .post-content tr:nth-child(even) td { background: #f8fafc; }
        .post-content td:first-child { font-weight: 600; }
        .post-content ul, .post-content ol { margin: 16px 0; }
        .post-content li { margin-bottom: 8px; }
        """

    img_html = (f'<img class="featured-image" src="{esc(img)}" alt="{title}" loading="eager">' if img
                else f'<div class="card-image-placeholder" style="height:280px;margin-bottom:24px">{placeholder_icon}</div>')

    # Breadcrumb
    breadcrumb = f"""
    <nav class="breadcrumb">
      <a href="/">Inicio</a>
      <span class="sep">&#9654;</span>
      <a href="/blog/{slug}">{blog_name}</a>
      <span class="sep">&#9654;</span>
      <span class="current">{esc(raw_title[:60])}</span>
    </nav>"""

    # Author
    author_html = f'''<span class="meta-item author" style="display:inline-flex;align-items:center;gap:6px;">
        <span style="width:20px;height:20px;border-radius:50%;background:linear-gradient(135deg, var(--primary, #4f46e5), var(--accent, var(--primary, #4f46e5)));color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;">{author_name[0].upper()}</span>
        <strong style="color:var(--dark);">{author_name}</strong>
    </span>'''

    # Sumario Dinamico (TOC) via Regex nos h2
    h2_pattern = re.compile(r'<h2([^>]*)>(.*?)</h2>', re.IGNORECASE | re.DOTALL)
    h2_matches = list(h2_pattern.finditer(content))
    toc_html = ""
    if h2_matches:
        toc_items = []
        new_content = ""
        last_idx = 0
        for idx, match in enumerate(h2_matches):
            attrs, raw_h2_text = match.groups()
            clean_text = re.sub(r'<[^>]*>', '', raw_h2_text).strip()
            anchor_id = f"topico-{idx+1}"
            
            new_content += content[last_idx:match.start()]
            
            # Se for o primeiro H2 e o blog for de afiliado, insere o Veredito Rápido (TL;DR)
            h2_html = f'<h2{attrs} id="{anchor_id}">{raw_h2_text}</h2>'
            if idx == 0 and blog_info.get("is_affiliate"):
                tldr_html = f"""
                <div class="tldr-box" style="margin: 28px 0; padding: 24px; background: var(--bg-dark); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.02);">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                        <span style="font-size: 20px;">⚡</span>
                        <h3 style="margin: 0; font-size: 16px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: var(--dark); font-family: var(--font-heading);">Veredito Rápido (TL;DR)</h3>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                        <div>
                            <h4 style="margin: 0 0 10px; font-size: 14px; font-weight: 700; color: var(--primary); font-family: var(--font-heading);">🟢 Destaques / Prós</h4>
                            <ul style="margin: 0; padding-left: 18px; font-size: 13.5px; color: var(--text); line-height: 1.6; list-style-type: disc;">
                                <li>Desempenho e durabilidade aprovados.</li>
                                <li>Excelente custo-benefício editorial.</li>
                                <li>Foco total em usabilidade e ergonomia.</li>
                            </ul>
                        </div>
                        <div>
                            <h4 style="margin: 0 0 10px; font-size: 14px; font-weight: 700; color: var(--accent); font-family: var(--font-heading);">🟡 Pontos de Atenção</h4>
                            <ul style="margin: 0; padding-left: 18px; font-size: 13.5px; color: var(--text); line-height: 1.6; list-style-type: disc;">
                                <li>Pode exigir pequeno tempo de adaptação.</li>
                                <li>Disponibilidade de estoque oscila rápido.</li>
                            </ul>
                        </div>
                    </div>
                </div>
                """
                h2_html = tldr_html + h2_html
                
            new_content += h2_html
            last_idx = match.end()
            
            toc_items.append(f'<li><a href="#{anchor_id}">📌 {clean_text}</a></li>')
        
        new_content += content[last_idx:]
        content = new_content
        
        if toc_items:
            toc_html = f"""
            <nav class="table-of-contents scroll-fade" aria-label="Sumario">
              <div class="toc-title">💡 Neste artigo voce vai conferir:</div>
              <ul>
                {"".join(toc_items)}
              </ul>
            </nav>"""

    # Author Box com Biografia por Nicho (E-E-A-T)
    nicho_lower = blog_info.get("nicho", "").lower()
    if "crist" in nicho_lower or "jesus" in nicho_lower:
        real_author_name = "Carlos de Souza (Carlão)"
        author_bio = "Carlos é escritor e teólogo especializado em estudos bíblicos, história do cristianismo antigo e análise dos evangelhos. Dedica-se a tornar os ensinamentos de Jesus acessíveis a todos."
        author_initial = "C"
    elif "finan" in nicho_lower or "econom" in nicho_lower or "invest" in nicho_lower:
        real_author_name = "Rosa Guedes (Dona Rosa)"
        author_bio = "Rosa é consultora financeira e especialista em economia doméstica e planejamento financeiro pessoal. Escreve artigos práticos para ajudar famílias a organizarem suas finanças."
        author_initial = "R"
    else:
        real_author_name = f"Equipe {blog_name}"
        author_bio = f"Produzido pelo conselho de redatores especializados do blog {blog_name}, focados em trazer guias autoritativos e informativos."
        author_initial = blog_name[0] if blog_name else "E"

    author_box_html = f"""
    <div class="author-box scroll-fade">
      <div class="author-avatar" style="background:var(--primary,#6366f1)">{author_initial}</div>
      <div class="author-info">
        <div class="author-title">Escrito por {real_author_name}</div>
        <p class="author-bio">{author_bio}</p>
      </div>
    </div>"""

    # Newsletter inline
    newsletter_html = f"""
    <aside class="newsletter-inline scroll-fade" aria-label="Newsletter">
      <h3>&#128231; Gostou do artigo?</h3>
      <p>Receba novos conteudos diretamente no seu e-mail. Sem spam, apenas conteudo de qualidade.</p>
      <form class="newsletter-form" onsubmit="alert('Funcionalidade em breve! Envie um e-mail para contato@dezafira.com.br');return false">
        <input type="email" placeholder="Seu melhor e-mail" required aria-label="Email">
        <button type="submit">Inscrever</button>
      </form>
    </aside>"""

    # Related
    related_html = ""
    if related_posts:
        related_cards = ""
        for rp in related_posts:
            rp_id = esc(rp["id"])
            rp_tit = esc(rp["title"])
            rp_img = rp.get("featured_image_url")
            rp_wc = rp.get("word_count", 0) or 0
            rp_rt = max(1, round(rp_wc / 200))
            if rp_img:
                rp_img_tag = f'<img class="card-image" src="{esc(rp_img)}" alt="{rp_tit}" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
            else:
                rp_img_tag = f'<div class="card-image-placeholder">{placeholder_icon}</div>'
            rp_dt = fmt_date(rp.get("created_at"))
            related_cards += f"""
            <a href="/blog/{slug}?post={rp_id}" class="related-card scroll-fade">
              {rp_img_tag}
              <div class="card-body">
                <h4 class="post-title">{rp_tit}</h4>
                <div class="post-meta">
                  <span>&#128197; {rp_dt}</span>
                  <span>&#9201; {rp_rt} min</span>
                </div>
              </div>
            </a>"""
        if related_cards:
            related_html = f"""
    <section class="related-section">
      <h3>&#128214; Leia Tambem</h3>
      <div class="related-grid">{related_cards}
      </div>
    </section>"""

    canonical = f"https://dezafira.com.br/blog/{slug}?post={esc(post['id'])}"
    excerpt_clean = (post.get("excerpt") or "")[:200]
    img_url = img or ""

    # Schema.org Article enriquecido (E-E-A-T)
    schema_obj = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": (post.get("excerpt") or "")[:500],
        "wordCount": wc,
        "datePublished": post.get("created_at", ""),
        "dateModified": post.get("published_at") or post.get("created_at", ""),
        "inLanguage": blog_info.get("lang", "pt-BR"),
        "mainEntityOfPage": canonical,
        "articleSection": ((post.get("keywords") or "").split(",")[0].strip() if post.get("keywords") else blog_niche),
        "author": {"@type": "Person", "name": real_author_name},
        "publisher": {"@type": "Organization", "name": blog_name}
    }
    if img_url:
        schema_obj["image"] = img_url
    schema = json.dumps(schema_obj, ensure_ascii=False, indent=2)

    body = f"""{_get_header_html(slug, blog_info["name"], blog_info.get("nicho", ""), brand_config=brand_config)}
<div class="reading-progress"><div class="reading-progress-bar" id="readingProgress"></div></div>
<main class="blog-content">
  {breadcrumb}
  <article class="post-viewer">
    {img_html}
    <h1>{title}</h1>
    <div class="post-meta-bar">
      {author_html}
      {score_chip}
      <span class="meta-item">&#128197; {dt_str}</span>
      <span class="meta-item">&#128196; {wc} palavras</span>
      <span class="meta-item">&#9201; {rt} min de leitura</span>
    </div>
    {f'<div class="post-tags">{tags}</div>' if tags else ''}
    {toc_html}
    <div class="post-content">{content}</div>
    {author_box_html}
    {newsletter_html}
    {related_html}
    <div style="margin-top:32px;padding-top:24px;border-top:1px solid var(--border);text-align:center">
      <a href="/blog/{slug}" class="back-link" style="display:inline-flex">&larr; Voltar para todos os artigos</a>
    </div>
  </article>
</main>
{_get_footer_html(slug, blog_info["name"], blog_info.get("nicho", ""), brand_config=brand_config)}
{_READING_PROGRESS_JS}
{_SCROLL_OBSERVER_JS}"""

    _discover = blog_info.get("is_discover", False)
    return _page_frame(f"{title} &mdash; {blog_name}", body, theme_css,
                       description=excerpt_clean, image_url=img_url,
                       canonical_url=canonical, schema_json=schema, theme=theme, slug=slug, brand_config=brand_config,
                       body_class="mode-discover" if _discover else "")


# ─── STATIC PAGES ────────────────────────────────────────────────────

_PAGE_STYLES = """
.static-page{max-width:740px;margin:0 auto;padding:32px 20px}
.static-page h1{font-size:28px;font-weight:700;margin-bottom:8px;color:var(--text,#1e293b)}
.static-page .meta{font-size:13px;color:var(--text-light,#94a3b8);margin-bottom:24px}
.static-page h2{font-size:20px;font-weight:600;margin:32px 0 12px;padding-bottom:6px;border-bottom:2px solid var(--border,#e2e8f0);color:var(--text,#1e293b)}
.static-page h3{font-size:16px;font-weight:600;margin:24px 0 10px;color:var(--text,#1e293b)}
.static-page p{margin-bottom:16px;line-height:1.8;color:var(--text,#334155)}
.static-page ul,.static-page ol{padding-left:24px;margin-bottom:16px;color:var(--text,#334155)}
.static-page li{margin-bottom:8px;line-height:1.6}
.static-page a{color:var(--gold,#d4a853);font-weight:500}
.static-page a:hover{text-decoration:underline}
.static-page .contact-card{background:var(--card-bg,#fff);border:1px solid var(--border,#e2e8f0);border-radius:12px;padding:28px;margin:24px 0}
.static-page .contact-card label{display:block;font-size:13px;font-weight:600;margin-bottom:4px;color:var(--text,#1e293b)}
.static-page .contact-card input,.static-page .contact-card textarea{width:100%;padding:10px 14px;border:1px solid var(--border,#e2e8f0);border-radius:8px;font-size:14px;font-family:inherit;margin-bottom:14px;background:var(--bg,#f8fafc);color:var(--text,#1e293b)}
.static-page .contact-card input:focus,.static-page .contact-card textarea:focus{outline:none;border-color:var(--gold,#d4a853)}
.static-page .contact-card button{padding:12px 28px;background:var(--gold,#d4a853);color:var(--dark,#0f172a);border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer}
.static-page .contact-card button:hover{opacity:.9}
.static-page blockquote{border-left:3px solid var(--gold,#d4a853);padding:12px 20px;margin:16px 0;background:rgba(212,168,83,.06);border-radius:0 8px 8px 0;font-style:italic}
"""


def generate_static_page(slug: str, blog_info: dict, page_title: str, content_html: str, meta: str = "") -> str:
    blog_name = blog_info.get("name", "O Reino")
    blog_niche = blog_info.get("nicho", "")
    theme_css = _PAGE_STYLES
    theme_css, brand_config = _apply_brand_overrides(blog_info, theme_css)
    body = f"""{_get_header_html(slug, blog_name, blog_niche, brand_config=brand_config)}
<main class="blog-content">
  <div class="static-page">
    <a href="/blog/{slug}" class="back-link">&larr; Voltar ao Blog</a>
    <h1>{page_title}</h1>
    {f'<div class="meta">{meta}</div>' if meta else ''}
    {content_html}
  </div>
</main>
{_get_footer_html(slug, blog_name, blog_niche, brand_config=brand_config)}
{_SCROLL_OBSERVER_JS}"""
    full_title = f"{page_title} &mdash; {blog_name}"
    return _page_frame(full_title, body, theme_css, theme=detect_theme(blog_niche), slug=slug, brand_config=brand_config)


def generate_privacy_page(slug: str, blog_info: dict) -> str:
    content = """
<h2>1. Introducao</h2>
<p>O blog respeita a sua privacidade. Esta Politica de Privacidade explica como coletamos, usamos, compartilhamos e protegemos suas informacoes quando voce visita nosso site.</p>
<h2>2. Dados que Coletamos</h2>
<ul>
<li><strong>Dados de navegacao:</strong> endereco IP, tipo de navegador, paginas visitadas</li>
<li><strong>Cookies:</strong> utilizamos cookies proprios e de terceiros para melhorar a experiencia</li>
<li><strong>Dados fornecidos voluntariamente:</strong> nome e e-mail em formularios de contato</li>
</ul>
<h2>3. Cookies do Google (AdSense)</h2>
<p>Utilizamos o <strong>Google AdSense</strong> para exibir anuncios. O Google utiliza cookies para veicular anuncios com base nas visitas anteriores dos usuarios ao nosso site ou a outros sites. Voce pode desativar a personalizacao de anuncios visitando as <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Configuracoes de Anuncios do Google</a>.</p>
<p>Para mais informacoes: <a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener">Como o Google usa as informacoes de sites</a>.</p>
<h2>4. LGPD (Lei Geral de Protecao de Dados)</h2>
<p>Em conformidade com a Lei 13.709/2018 (LGPD), voce tem direito a:</p>
<ul>
<li>Acessar seus dados pessoais</li>
<li>Corrigir dados incompletos ou desatualizados</li>
<li>Solicitar a eliminacao dos dados</li>
<li>Revogar o consentimento a qualquer momento</li>
</ul>
<h2>5. Contato para Exercer seus Direitos</h2>
<p>Para qualquer questao relacionada a privacidade: <strong>contato@dezafira.com.br</strong></p>
"""
    return generate_static_page(slug, blog_info, "Politica de Privacidade", content, "Ultima atualizacao: julho de 2026")


def generate_about_page(slug: str, blog_info: dict) -> str:
    blog_name = blog_info.get("name", "O Reino")
    niche = blog_info.get("nicho", "")
    content = f"""
<h2>Nosso Proposito</h2>
<p><strong>"{blog_name}"</strong> e um blog dedicado a explorar e compartilhar conhecimento sobre <strong>{niche}</strong>. Oferecemos reflexoes profundas, estudos e meditacoes que ajudam pessoas a compreender e aplicar principios transformadores em sua vida diaria.</p>
<h2>Nossa Missao</h2>
<ul>
<li><strong>Ensinar:</strong> Explicar temas complexos de forma clara e acessivel</li>
<li><strong>Refletir:</strong> Provocar reflexao profunda sobre fe, valores e proposito</li>
<li><strong>Aplicar:</strong> Mostrar como viver esses ensinamentos no seculo XXI</li>
</ul>
<h2>Nossa Equipe</h2>
<p>Contamos com uma equipe dedicada de redatores, revisores e pesquisadores que trabalham para trazer o melhor conteudo, sempre com qualidade e profundidade.</p>
<h2>Entre em Contato</h2>
<p>Tem alguma duvida ou sugestao? Fale conosco: <strong>contato@dezafira.com.br</strong></p>
"""
    return generate_static_page(slug, blog_info, f"Sobre Nos &mdash; {blog_name}", content)


def generate_contact_page(slug: str, blog_info: dict) -> str:
    content = """
<div class="contact-card">
  <label for="contact-name">Seu Nome</label>
  <input type="text" id="contact-name" placeholder="Digite seu nome">
  <label for="contact-email">Seu E-mail</label>
  <input type="email" id="contact-email" placeholder="Digite seu e-mail">
  <label for="contact-subject">Assunto</label>
  <input type="text" id="contact-subject" placeholder="Assunto da mensagem">
  <label for="contact-message">Mensagem</label>
  <textarea id="contact-message" rows="5" placeholder="Sua mensagem..."></textarea>
  <button onclick="alert('Funcionalidade em breve! Envie um e-mail para contato@dezafira.com.br')">Enviar Mensagem</button>
</div>
<h3>Outras formas de contato</h3>
<p><strong>E-mail:</strong> contato@dezafira.com.br</p>
"""
    return generate_static_page(slug, blog_info, "Contato", content)


def generate_terms_page(slug: str, blog_info: dict) -> str:
    content = """
<h2>1. Aceitacao dos Termos</h2>
<p>Ao acessar este blog, voce concorda com estes Termos de Uso. Se nao concordar, por favor, nao utilize nosso site.</p>
<h2>2. Uso do Conteudo</h2>
<p>Todo o conteudo publicado neste blog e protegido por direitos autorais. E permitido compartilhar os links e trechos com devida atribuicao, mas a reproducao integral do conteudo sem autorizacao e proibida.</p>
<h2>3. Responsabilidades</h2>
<ul>
<li>O conteudo e fornecido "como esta", para fins informativos e educacionais</li>
<li>Nao nos responsabilizamos por decisoes tomadas com base no conteudo</li>
<li>Links externos sao fornecidos como conveniencia, sem endorsamento</li>
</ul>
<h2>4. Alteracoes</h2>
<p>Estes termos podem ser atualizados a qualquer momento. Recomendamos revisar esta pagina periodicamente.</p>
<h2>5. Contato</h2>
<p>Para questoes sobre estes termos: <strong>contato@dezafira.com.br</strong></p>
"""
    return generate_static_page(slug, blog_info, "Termos de Uso", content, "Ultima atualizacao: julho de 2026")


def generate_not_found() -> str:
    return _page_frame("Pagina nao encontrada",
        '<div class="error-state"><div class="icon">&#128533;</div><h2>Pagina nao encontrada</h2><p><a href="/">Voltar ao inicio</a></p></div>',
        slug="")


def generate_blog_html(slug: str, blog_info: dict, posts: list, post: dict = None, related_posts: list = None) -> str:
    """Gera HTML completo do blog com tema personalizado por nicho.
    Se post for fornecido, mostra artigo individual (com related_posts).
    Senao, mostra lista de artigos com hero section.
    """
    if not blog_info:
        return generate_not_found()
    if post and post.get('title'):
        return generate_article_view(slug, blog_info, post, related_posts=related_posts)
    return generate_blog_list(slug, blog_info, posts)
