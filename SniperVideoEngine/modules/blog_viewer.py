"""
Server-rendered blog viewer HTML generator.
Gera HTML completo com artigos (SEO-friendly, sem depender de JavaScript).
Usa sistema de temas visuais por nicho (brand_themes.py).
"""

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


def _page_frame(title: str, body_html: str, theme_css: str = "") -> str:
    google_fonts = ("Inter:wght@300;400;500;600;700")
    if "Playfair" in theme_css:
        google_fonts += "|Playfair+Display:wght@400;700"
    if "Merriweather" in theme_css:
        google_fonts += "|Merriweather:wght@300;400;700"
    if "Lora" in theme_css:
        google_fonts += "|Lora:wght@400;600;700"
    if "JetBrains" in theme_css:
        google_fonts += "|JetBrains+Mono:wght@400;700"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?{google_fonts}&display=swap" rel="stylesheet">
<style>{theme_css}</style>
</head>
<body>
{body_html}
</body>
</html>"""


def _get_footer_html(slug: str, blog_name: str, year: str = None) -> str:
    """Gera footer com links dinâmicos usando o slug do blog."""
    if not year:
        year = str(datetime.now().year)
    return f"""<footer class=blog-footer>
  <div class=footer-links>
    <a href="/blog/{slug}/sobre">Sobre</a>
    <a href="/blog/{slug}/privacidade">Privacidade</a>
    <a href="/blog/{slug}/contato">Contato</a>
  </div>
  <p>&copy; {year} {blog_name} &mdash; Todos os direitos reservados</p>
</footer>
<a href="/" class="admin-link">&#9881; Admin</a>"""


def generate_blog_list(slug: str, blog_info: dict, posts: list) -> str:
    """Gera HTML da pagina inicial do blog com grade de artigos e tema personalizado."""
    blog_name = esc(blog_info["name"])
    blog_niche = esc(blog_info.get("nicho", ""))
    pcount = len(posts)
    subdomain = blog_info.get("subdomain", "")

    # Detectar tema baseado no nicho
    theme = detect_theme(blog_info.get("nicho", ""))
    theme_css = generate_theme_css(blog_info.get("nicho", ""), blog_name)
    header_icon = theme.get("header_icon", "&#128214;")
    placeholder_icon = theme.get("placeholder_icon", "&#128214;")

    subdomain_html = ""
    if subdomain:
        subdomain_html = f'<a href="https://{subdomain}.dezafira.com.br" target="_blank" style="display:inline-block;margin-top:8px;padding:4px 12px;background:rgba(255,255,255,0.08);border-radius:20px;font-size:.8rem;color:var(--primary-light);text-decoration:none">&#128279; {subdomain}.dezafira.com.br</a>'

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

    posts_html = f'<div class="posts-grid">{cards_html}</div>' if cards_html else f'<div class="empty-state"><div class="icon">{placeholder_icon}</div><p>Nenhum artigo publicado ainda. Volte em breve!</p></div>'

    body = f"""<header class="blog-header">
  <h1>{header_icon} {blog_name}</h1>
  <p>{blog_niche}</p>
  {subdomain_html}
  <div class="blog-stats"><span>&#128197; {pcount} artigo{"s" if pcount != 1 else ""}</span></div>
</header>
<main class="blog-content">
  <h2 style="font-family:var(--font-heading);font-size:1.5rem;margin-bottom:20px;color:var(--dark)">&#128214; Todos os Artigos</h2>
  {posts_html}
</main>
{_get_footer_html(slug, blog_name)}"""

    title = f"{blog_name} &mdash; Blog sobre {blog_niche}" if blog_niche else blog_name
    return _page_frame(title, body, theme_css)


def generate_article_view(slug: str, blog_info: dict, post: dict) -> str:
    """Gera HTML da visualizacao de um artigo individual com tema personalizado."""
    blog_name = esc(blog_info["name"])
    blog_niche = esc(blog_info.get("nicho", ""))
    title = esc(post["title"])
    content = post.get("content", "")
    excerpt = esc(post.get("excerpt", "")[:200])
    img = post.get("featured_image_url")
    wc = post.get("word_count", 0) or 0
    rt = max(1, round(wc / 200))
    dt_str = fmt_date(post.get("created_at"))
    keywords = post.get("keywords", "")
    tags = "".join(f'<span class="tag">{esc(k.strip())}</span>' for k in keywords.split(",") if k.strip())

    # Detectar tema baseado no nicho
    theme = detect_theme(blog_info.get("nicho", ""))
    theme_css = generate_theme_css(blog_info.get("nicho", ""), blog_name)
    header_icon = theme.get("header_icon", "&#128214;")
    placeholder_icon = theme.get("placeholder_icon", "&#128214;")

    img_html = f'<img class="featured-image" src="{esc(img)}" alt="{title}">' if img else f'<div class="card-image-placeholder" style="height:280px;margin-bottom:24px">{placeholder_icon}</div>'

    body = f"""<header class="blog-header">
  <h1>{header_icon} {blog_name}</h1>
  <p>{blog_niche}</p>
</header>
<main class="blog-content">
  <a href="/blog/{slug}" class="back-link">&larr; Todos os Artigos</a>
  <article class="post-viewer">
    {img_html}
    <h1>{title}</h1>
    <div class="post-meta-bar">
      <span>&#128197; {dt_str}</span>
      <span>&#128196; {wc} palavras</span>
      <span>&#9201; {rt} min de leitura</span>
    </div>
    {f'<div class="post-tags">{tags}</div>' if tags else ''}
    <div class="post-content">{content}</div>
    <div style="margin-top:40px;padding-top:24px;border-top:1px solid var(--border);text-align:center">
      <a href="/blog/{slug}" class="back-link" style="display:inline-flex">&larr; Voltar para todos os artigos</a>
    </div>
  </article>
</main>
{_get_footer_html(slug, blog_name)}"""

    return _page_frame(f"{title} &mdash; {blog_name}", body, theme_css)


def generate_not_found() -> str:
    return _page_frame("Pagina nao encontrada",
        '<div class="error-state"><div class="icon">&#128533;</div><h2>Pagina nao encontrada</h2><p><a href="/">Voltar ao inicio</a></p></div>',
        ":root{--bg:#f8fafc;--text:#334155;}")


def generate_blog_html(slug: str, blog_info: dict, posts: list, post: dict = None) -> str:
    """
    Gera HTML completo do blog com tema personalizado por nicho.
    Se post for fornecido e valido, renderiza o artigo individual.
    Senao, renderiza a grade de artigos.
    """
    if not blog_info:
        return generate_not_found()

    if post and post.get('title'):
        return generate_article_view(slug, blog_info, post)
    else:
        return generate_blog_list(slug, blog_info, posts)
