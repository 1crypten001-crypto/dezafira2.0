"""
Server-rendered blog viewer HTML generator.
Gera HTML completo com artigos (SEO-friendly, sem depender de JavaScript).
Usa sistema de temas visuais por nicho (brand_themes.py).
"""

import json
from datetime import datetime
import html as html_mod
from modules.brand_themes import detect_theme, generate_theme_css


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


# ─── BASE CSS ────────────────────────────────────────────────────────────
# Estilos compartilhados entre todos os blogs (header, nav, footer, etc.)
_BASE_CSS = """
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:'Inter',-apple-system,sans-serif;background:var(--bg,#f8fafc);color:var(--text,#1e293b);min-height:100vh;padding-top:64px}
a{color:inherit;text-decoration:none}
img{max-width:100%;height:auto}

/* ─── HEADER ─── */
.site-header{position:fixed;top:0;left:0;right:0;z-index:100;background:var(--dark,#0f172a);border-bottom:1px solid rgba(255,255,255,.08);backdrop-filter:blur(12px)}
.header-inner{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:24px;padding:0 20px;height:64px}
.header-logo{display:flex;align-items:center;gap:10px;flex-shrink:0}
.logo-icon{width:34px;height:34px;display:flex;align-items:center;justify-content:center;background:var(--gold,#d4a853);border-radius:8px;font-size:18px;color:var(--dark,#0f172a);font-weight:700}
.logo-text{font-size:18px;font-weight:700;color:#fff}
.header-nav{display:flex;align-items:center;gap:4px;flex:1;overflow-x:auto}
.nav-link{padding:8px 14px;border-radius:8px;font-size:13px;font-weight:500;color:rgba(255,255,255,.7);white-space:nowrap;transition:all .15s ease}
.nav-link:hover{background:rgba(255,255,255,.08);color:#fff}
.nav-link.active{background:rgba(212,168,83,.15);color:var(--gold,#d4a853)}
.header-actions{display:flex;align-items:center;gap:8px;flex-shrink:0}
.search-toggle,.menu-toggle{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);color:rgba(255,255,255,.7);width:36px;height:36px;border-radius:8px;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;transition:all .15s ease}
.search-toggle:hover,.menu-toggle:hover{background:rgba(255,255,255,.12);color:#fff}
.menu-toggle{display:none}
.search-bar{max-width:1200px;margin:0 auto;padding:12px 20px;display:flex;gap:8px}
.search-bar input{flex:1;padding:10px 14px;border-radius:8px;border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.06);color:#fff;font-size:14px;font-family:inherit;outline:none}
.search-bar input:focus{border-color:var(--gold,#d4a853)}
.search-bar button{padding:10px 20px;border-radius:8px;border:none;background:var(--gold,#d4a853);color:var(--dark,#0f172a);font-weight:600;font-size:13px;cursor:pointer}
.search-bar button:hover{opacity:.9}

/* ─── FOOTER ─── */
.site-footer{background:var(--dark,#0f172a);border-top:1px solid rgba(255,255,255,.06);padding:48px 20px 24px;margin-top:48px;color:rgba(255,255,255,.7)}
.footer-grid{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px}
.footer-brand .logo-icon{margin-bottom:8px}
.footer-brand strong{display:block;font-size:16px;color:#fff;margin-bottom:6px}
.footer-brand p{font-size:13px;line-height:1.6;color:rgba(255,255,255,.5)}
.footer-links h4,.footer-social h4{font-size:12px;font-weight:600;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px}
.footer-links a{display:block;padding:4px 0;font-size:13px;color:rgba(255,255,255,.6);transition:color .15s ease}
.footer-links a:hover{color:#fff}
.social-links{display:flex;gap:8px}
.social-links a{width:36px;height:36px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.06);border-radius:8px;font-size:16px;color:rgba(255,255,255,.6);transition:all .15s ease}
.social-links a:hover{background:rgba(212,168,83,.15);color:var(--gold,#d4a853)}
.footer-bottom{max-width:1200px;margin:32px auto 0;padding-top:16px;border-top:1px solid rgba(255,255,255,.06);text-align:center;font-size:12px;color:rgba(255,255,255,.35)}

/* ─── BLOG CONTENT ─── */
.blog-content{max-width:1200px;margin:0 auto;padding:32px 20px}
.posts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}
.post-card{background:var(--card-bg,#fff);border:1px solid var(--border,#e2e8f0);border-radius:12px;overflow:hidden;transition:all .2s ease;display:flex;flex-direction:column}
.post-card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.08)}
.card-image{width:100%;height:180px;object-fit:cover}
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
.featured-image{width:100%;border-radius:12px;margin-bottom:24px;max-height:420px;object-fit:cover}
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

/* ─── BREADCRUMB ─── */
.breadcrumb{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--text-light,#94a3b8);margin-bottom:20px;flex-wrap:wrap}
.breadcrumb a{color:var(--text-light,#94a3b8);text-decoration:none;transition:color .15s ease}
.breadcrumb a:hover{color:var(--gold,#d4a853)}
.breadcrumb .sep{color:var(--text-light,#cbd5e1);font-size:10px}
.breadcrumb .current{color:var(--text,#1e293b);font-weight:500}

/* ─── RELATED ARTICLES ─── */
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

/* ─── ADMIN LINK ─── */
.admin-link{position:fixed;bottom:20px;right:20px;width:40px;height:40px;background:var(--dark,#0f172a);border:1px solid rgba(255,255,255,.1);border-radius:50%;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,.5);font-size:16px;z-index:99;transition:all .15s ease}
.admin-link:hover{background:var(--gold,#d4a853);color:var(--dark,#0f172a)}

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
}
"""


# ─── CATEGORIES ──────────────────────────────────────────────────────────

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
    """Retorna categorias baseadas no nicho do blog."""
    n = nicho.lower().strip()
    for key, cats in _CATEGORY_MAP.items():
        if key in n or n in key:
            return cats
    return ["Artigos", "Estudos", "Guias", "Noticias", "Dicas"]


# ─── PAGE FRAME ──────────────────────────────────────────────────────────

def _page_frame(title: str, body_html: str, theme_css: str = "",
               description: str = "", image_url: str = "",
               canonical_url: str = "", schema_json: str = "") -> str:
    """Gera pagina HTML completa com SEO: Open Graph, Twitter Cards, Schema.org e canonical."""
    google_fonts = "Inter:wght@300;400;500;600;700"
    if "Playfair" in theme_css:
        google_fonts += "|Playfair+Display:wght@400;700"
    if "Merriweather" in theme_css:
        google_fonts += "|Merriweather:wght@300;400;700"
    if "Lora" in theme_css:
        google_fonts += "|Lora:wght@400;600;700"

    favicon = ("data:image/svg+xml,"
               "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
               "%3Crect width='32' height='32' rx='6' fill='%23d4a853'/%3E"
               "%3Ctext x='16' y='23' font-size='22' text-anchor='middle' fill='%231a1410'%3E%E2%9C%9D%3C/text%3E"
               "%3C/svg%3E")

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
<title>{title}</title>
<meta name="description" content="{desc_escaped}">
{canonical}
{og_tags}
{og_img}
{schema_tag}
<link rel="icon" type="image/svg+xml" href="{favicon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?{google_fonts}&display=swap" rel="stylesheet">
<style>{_BASE_CSS}{theme_css}</style>
</head>
<body>
{body_html}
</body>
</html>"""


# ─── HEADER ──────────────────────────────────────────────────────────────

def _get_header_html(slug: str, blog_name: str, blog_niche: str, current_cat: str = "") -> str:
    """Gera header fixo com logo, navegacao por categorias e busca."""
    categories = _get_categories(blog_niche)
    nav_items = "".join(
        f'<a href="/blog/{slug}?cat={c.lower()}" class="nav-link{" active" if current_cat.lower() == c.lower() else ""}">{c}</a>'
        for c in categories
    )
    return f"""<header class="site-header">
  <div class="header-inner">
    <a href="/blog/{slug}" class="header-logo">
      <span class="logo-icon">&#10013;</span>
      <span class="logo-text">{blog_name}</span>
    </a>
    <nav class="header-nav" id="mainNav">
      {nav_items}
    </nav>
    <div class="header-actions">
      <button class="search-toggle" onclick="toggleSearch()" aria-label="Buscar">&#128269;</button>
      <button class="menu-toggle" onclick="toggleMobileMenu()" aria-label="Menu">&#9776;</button>
    </div>
  </div>
  <div class="search-bar" id="searchBar" style="display:none">
    <input type="text" id="searchInput" placeholder="Buscar artigos..." onkeydown="if(event.key==='Enter') searchArticles()">
    <button onclick="searchArticles()">Buscar</button>
  </div>
</header>
<script>
function toggleSearch(){{var sb=document.getElementById('searchBar');if(sb)sb.style.display=sb.style.display==='none'?'flex':'none';}}
function toggleMobileMenu(){{var nav=document.getElementById('mainNav');if(nav)nav.classList.toggle('open');}}
function searchArticles(){{var q=document.getElementById('searchInput');if(q&&q.value.trim())window.location='/blog/{slug}?q='+encodeURIComponent(q.value.trim());}}
</script>"""


# ─── FOOTER ──────────────────────────────────────────────────────────────

def _get_footer_html(slug: str, blog_name: str, blog_niche: str = "", year: str = None) -> str:
    """Gera footer com links e informacoes."""
    if not year:
        year = str(datetime.now().year)
    categories = _get_categories(blog_niche)
    cat_links = "".join(f'<a href="/blog/{slug}?cat={c.lower()}">{c}</a>' for c in categories[:4])
    # Descricao dinâmica baseada no nicho
    niche_desc = blog_niche[:80] if blog_niche else "conhecimento e inspiracao"
    return f"""<footer class="site-footer">
  <div class="footer-grid">
    <div class="footer-brand">
      <span class="logo-icon">&#10013;</span>
      <strong>{blog_name}</strong>
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
</footer>
<a href="/" class="admin-link">&#9881; Admin</a>"""


# ─── PAGE GENERATORS ─────────────────────────────────────────────────────

def generate_blog_list(slug: str, blog_info: dict, posts: list) -> str:
    """Gera HTML da pagina inicial do blog com grade de artigos."""
    blog_name = esc(blog_info["name"])
    blog_niche = esc(blog_info.get("nicho", ""))
    pcount = len(posts)
    theme = detect_theme(blog_info.get("nicho", ""))
    theme_css = generate_theme_css(blog_info.get("nicho", ""), blog_name)
    placeholder_icon = theme.get("placeholder_icon", "&#128214;")

    cards_html = ""
    for p in posts:
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

        cards_html += f"""
        <a href="/blog/{slug}?post={pid}" class="post-card">
          {img_tag}
          <div class="card-body">
            <h2 class="post-title">{tit}</h2>
            <p class="post-excerpt">{excerpt}</p>
            <div class="post-meta">
              <span>&#128197; {dt_str}</span>
              <span>&#128196; {wc} palavras</span>
              <span>&#9201; {rt} min</span>
            </div>
            {f'<div class="post-tags">{tags}</div>' if tags else ''}
            <span class="read-more">Ler artigo &rarr;</span>
          </div>
        </a>"""

    posts_html = (f'<div class="posts-grid">{cards_html}</div>' if cards_html
                  else f'<div class="empty-state"><div class="icon">{placeholder_icon}</div><p>Nenhum artigo publicado ainda. Volte em breve!</p></div>')

    subdomain = blog_info.get("subdomain", "")
    subdomain_html = f'<a href="https://{subdomain}.dezafira.com.br" target="_blank" style="display:inline-flex;align-items:center;gap:6px;margin-bottom:20px;padding:6px 14px;background:rgba(255,255,255,.06);border-radius:20px;font-size:.8rem;color:var(--gold,#d4a853);text-decoration:none">&#127760; {subdomain}.dezafira.com.br</a>' if subdomain else ""

    desc = f"Blog sobre {blog_niche}. Artigos, estudos e reflexoes." if blog_niche else blog_name
    canonical = f"https://dezafira.com.br/blog/{slug}"

    body = f"""{_get_header_html(slug, blog_info["name"], blog_info.get("nicho", ""))}
<main class="blog-content">
  {subdomain_html}
  <h2 style="font-family:var(--font-heading,inherit);font-size:1.5rem;margin-bottom:20px">&#128214; Todos os Artigos</h2>
  <div class="blog-stats" style="margin-bottom:20px">{pcount} artigo{"s" if pcount != 1 else ""}</div>
  {posts_html}
</main>
{_get_footer_html(slug, blog_info["name"], blog_info.get("nicho", ""))}"""

    title = f"{blog_name} &mdash; Blog sobre {blog_niche}" if blog_niche else blog_name
    return _page_frame(title, body, theme_css, description=desc, canonical_url=canonical)


def generate_article_view(slug: str, blog_info: dict, post: dict, related_posts: list = None) -> str:
    """Gera HTML da visualizacao de um artigo individual.
    Inclui breadcrumb, autor no meta bar e secao Leia Tambem com artigos relacionados.
    """
    blog_name = esc(blog_info["name"])
    blog_niche = esc(blog_info.get("nicho", ""))
    raw_title = post["title"]  # raw for breadcrumb truncation
    title = esc(raw_title)
    content = post.get("content", "")
    excerpt = esc(post.get("excerpt", "")[:200])
    img = post.get("featured_image_url")
    wc = post.get("word_count", 0) or 0
    rt = max(1, round(wc / 200))
    dt_str = fmt_date(post.get("created_at"))
    keywords = post.get("keywords", "")
    tags = "".join(f'<span class="tag">{esc(k.strip())}</span>' for k in keywords.split(",") if k.strip())
    # Author do post ou nome do blog
    author_name = esc(post.get("author") or blog_info.get("name", "Equipe"))

    theme = detect_theme(blog_info.get("nicho", ""))
    theme_css = generate_theme_css(blog_info.get("nicho", ""), blog_name)
    placeholder_icon = theme.get("placeholder_icon", "&#128214;")

    img_html = (f'<img class="featured-image" src="{esc(img)}" alt="{title}">' if img
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

    # Author in meta bar
    author_html = f'<span class="meta-item author">&#9997; {author_name}</span>'

    # Related articles (Leia Tambem)
    related_html = ""
    if related_posts:
        related_cards = ""
        for rp in related_posts:
            rp_id = esc(rp["id"])
            rp_tit = esc(rp["title"])
            rp_excerpt = esc(rp.get("excerpt", "")[:120])
            rp_img = rp.get("featured_image_url")
            rp_wc = rp.get("word_count", 0) or 0
            rp_rt = max(1, round(rp_wc / 200))
            if rp_img:
                rp_img_tag = f'<img class="card-image" src="{esc(rp_img)}" alt="{rp_tit}" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
            else:
                rp_img_tag = f'<div class="card-image-placeholder">{placeholder_icon}</div>'
            rp_dt = fmt_date(rp.get("created_at"))
            related_cards += f"""
            <a href="/blog/{slug}?post={rp_id}" class="related-card">
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

    # Schema.org JSON-LD para o artigo — usa json.dumps() para serializacao segura
    schema_obj = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": (post.get("excerpt") or "")[:500],
        "wordCount": wc,
        "datePublished": post.get("created_at", ""),
        "author": {
            "@type": "Organization",
            "name": blog_info.get("name", "O Reino")
        }
    }
    schema = json.dumps(schema_obj, ensure_ascii=False, indent=2)

    canonical = f"https://dezafira.com.br/blog/{slug}?post={esc(post['id'])}"
    excerpt_clean = (post.get("excerpt") or "")[:200]
    img_url = img or ""

    body = f"""{_get_header_html(slug, blog_info["name"], blog_info.get("nicho", ""))}
<main class="blog-content">
  {breadcrumb}
  <article class="post-viewer">
    {img_html}
    <h1>{title}</h1>
    <div class="post-meta-bar">
      {author_html}
      <span class="meta-item">&#128197; {dt_str}</span>
      <span class="meta-item">&#128196; {wc} palavras</span>
      <span class="meta-item">&#9201; {rt} min de leitura</span>
    </div>
    {f'<div class="post-tags">{tags}</div>' if tags else ''}
    <div class="post-content">{content}</div>
    {related_html}
    <div style="margin-top:32px;padding-top:24px;border-top:1px solid var(--border);text-align:center">
      <a href="/blog/{slug}" class="back-link" style="display:inline-flex">&larr; Voltar para todos os artigos</a>
    </div>
  </article>
</main>
{_get_footer_html(slug, blog_info["name"], blog_info.get("nicho", ""))}"""

    return _page_frame(f"{title} &mdash; {blog_name}", body, theme_css,
                       description=excerpt_clean, image_url=img_url,
                       canonical_url=canonical, schema_json=schema)


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
    """Gera pagina estatica (Sobre, Contato, Privacidade, Termos) com header/footer do blog."""
    blog_name = blog_info.get("name", "O Reino")
    blog_niche = blog_info.get("nicho", "")
    theme_css = _PAGE_STYLES

    body = f"""{_get_header_html(slug, blog_name, blog_niche)}
<main class="blog-content">
  <div class="static-page">
    <a href="/blog/{slug}" class="back-link">&larr; Voltar ao Blog</a>
    <h1>{page_title}</h1>
    {f'<div class="meta">{meta}</div>' if meta else ''}
    {content_html}
  </div>
</main>
{_get_footer_html(slug, blog_name, blog_niche)}"""

    full_title = f"{page_title} &mdash; {blog_name}"
    return _page_frame(full_title, body, theme_css)


def generate_privacy_page(slug: str, blog_info: dict) -> str:
    """Pagina de Politica de Privacidade."""
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
    """Pagina Sobre Nos."""
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
    """Pagina de Contato."""
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
    """Pagina de Termos de Uso."""
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
        '<div class="error-state"><div class="icon">&#128533;</div><h2>Pagina nao encontrada</h2><p><a href="/">Voltar ao inicio</a></p></div>')


def generate_blog_html(slug: str, blog_info: dict, posts: list, post: dict = None, related_posts: list = None) -> str:
    """Gera HTML completo do blog com tema personalizado por nicho.
    Se post for fornecido, mostra artigo individual (com related_posts).
    Senao, mostra lista de artigos.
    """
    if not blog_info:
        return generate_not_found()
    if post and post.get('title'):
        return generate_article_view(slug, blog_info, post, related_posts=related_posts)
    return generate_blog_list(slug, blog_info, posts)
