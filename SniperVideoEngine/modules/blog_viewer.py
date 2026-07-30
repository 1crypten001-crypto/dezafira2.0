"""
Server-rendered blog viewer HTML generator.
Gera HTML completo com artigos (SEO-friendly, sem depender de JavaScript).
"""

from datetime import datetime
import html as html_mod


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


_BASE_CSS = """
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
:root{--gold:#d4a853;--gold-light:#f0d68a;--cream:#faf6ef;--cream-dark:#f0e8d5;--dark:#1a1410;--dark2:#2a2219;--text:#3d3227;--text-light:#7a6b5a;--accent:#8b2500;--border:#e0d5c0;--radius:12px;--radius-sm:8px;--shadow:0 2px 20px rgba(0,0,0,0.08)}
body{font-family:'Inter',system-ui,sans-serif;background:var(--cream);color:var(--text);line-height:1.7}
a{color:var(--gold);text-decoration:none}a:hover{color:var(--gold-dark,#a67c2e)}

/* ===== HEADER ===== */
.blog-header{background:linear-gradient(135deg,var(--dark),var(--dark2));padding:60px 24px 32px;text-align:center;position:relative;overflow:hidden}
.blog-header::before{content:'\u271d';position:absolute;font-size:300px;opacity:0.03;top:-80px;right:-40px;color:var(--gold)}
.blog-header h1{font-family:'Playfair Display',serif;font-size:2.5rem;color:var(--gold);margin-bottom:8px}
.blog-header p{color:var(--text-light);font-size:1.05rem;max-width:600px;margin:0 auto}
.blog-stats{display:flex;gap:12px;justify-content:center;margin-top:16px;flex-wrap:wrap}
.blog-stats span{background:rgba(255,255,255,0.08);padding:6px 14px;border-radius:20px;font-size:.85rem;color:var(--gold-light)}

/* ===== CONTENT ===== */
.blog-content{max-width:960px;margin:0 auto;padding:32px 20px}
.back-link{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);font-size:.9rem;font-weight:500;margin-bottom:20px;color:var(--text)}
.back-link:hover{background:var(--border)}

/* ===== POSTS GRID ===== */
.posts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:20px}
@media(max-width:640px){.posts-grid{grid-template-columns:1fr}}
.post-card{background:#fff;border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);transition:transform .2s,box-shadow .2s;cursor:pointer}
.post-card:hover{transform:translateY(-3px);box-shadow:0 8px 30px rgba(0,0,0,0.12)}
.card-image{width:100%;height:200px;object-fit:cover;display:block}
.card-image-placeholder{width:100%;height:200px;background:linear-gradient(135deg,#2a2219,#3d3227);display:flex;align-items:center;justify-content:center;font-size:3rem;color:var(--gold)}
.card-body{padding:20px}
.post-title{font-family:'Playfair Display',serif;font-size:1.2rem;margin-bottom:8px;color:var(--dark)}
.post-excerpt{font-size:.9rem;color:var(--text-light);margin-bottom:12px;line-height:1.5}
.post-meta{display:flex;gap:12px;flex-wrap:wrap;font-size:.8rem;color:var(--text-light);margin-bottom:10px}
.post-meta span{background:var(--cream);padding:3px 10px;border-radius:12px}
.post-tags{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.tag{background:rgba(212,168,83,0.12);color:#a67c2e;padding:3px 10px;border-radius:12px;font-size:.75rem;border:1px solid rgba(212,168,83,0.2)}
.read-more{display:inline-block;color:var(--gold);font-weight:600;font-size:.9rem;text-decoration:none;transition:color .2s}
.read-more:hover{color:var(--gold-dark,#a67c2e)}

/* ===== INDIVIDUAL POST ===== */
.post-viewer{max-width:780px;margin:0 auto}
.post-viewer .featured-image{width:100%;max-height:420px;object-fit:cover;border-radius:var(--radius);margin-bottom:24px;box-shadow:var(--shadow)}
.post-viewer h1{font-family:'Playfair Display',serif;font-size:2rem;color:var(--dark);margin-bottom:8px;line-height:1.3}
.post-viewer .post-meta-bar{display:flex;gap:16px;flex-wrap:wrap;font-size:.9rem;color:var(--text-light);margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid var(--border)}
.post-viewer .post-content{font-size:1.05rem;line-height:1.85;color:var(--text)}
.post-viewer .post-content h2{font-family:'Playfair Display',serif;font-size:1.5rem;margin:28px 0 12px;color:var(--dark)}
.post-viewer .post-content h3{font-size:1.2rem;margin:24px 0 10px;color:var(--dark)}
.post-viewer .post-content p{margin-bottom:16px}
.post-viewer .post-content blockquote{border-left:3px solid var(--gold);padding:12px 20px;margin:16px 0;background:rgba(212,168,83,0.06);border-radius:0 var(--radius-sm) var(--radius-sm) 0;font-style:italic;color:var(--text-light)}
.post-viewer .post-content img{max-width:100%;border-radius:var(--radius-sm);margin:16px 0}

/* ===== EMPTY / ERROR ===== */
.empty-state,.error-state{text-align:center;padding:60px 20px;color:var(--text-light)}
.empty-state .icon,.error-state .icon{font-size:3rem;margin-bottom:12px}

/* ===== ADMIN LINK ===== */
.admin-link{position:fixed;bottom:20px;right:20px;background:var(--dark);color:var(--gold);padding:10px 18px;border-radius:var(--radius);font-size:.85rem;text-decoration:none;opacity:.7;z-index:100;transition:opacity .2s}
.admin-link:hover{opacity:1}"""


def _page_frame(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
<style>{_BASE_CSS}</style>
</head>
<body>
{body_html}
</body>
</html>"""


def generate_blog_list(slug: str, blog_info: dict, posts: list) -> str:
    """Gera HTML da pagina inicial do blog com grade de artigos."""
    blog_name = esc(blog_info["name"])
    blog_niche = esc(blog_info.get("nicho", ""))
    pcount = len(posts)

    cards_html = ""
    for p in posts:
        wc = p.get("word_count", 0) or 0
        rt = max(1, round(wc / 200))
        excerpt = esc(p.get("excerpt", "")[:200])
        img = p.get("featured_image_url")
        img_tag = f'<img class="card-image" src="{esc(img)}" alt="{esc(p["title"])}" loading="lazy">' if img else '<div class="card-image-placeholder">&#10013;</div>'
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

    posts_html = f'<div class="posts-grid">{cards_html}</div>' if cards_html else '<div class="empty-state"><div class="icon">&#128221;</div><p>Nenhum artigo publicado ainda. Volte em breve!</p></div>'

    body = f"""<header class="blog-header">
  <h1>&#10013; {blog_name}</h1>
  <p>{blog_niche}</p>
  <div class="blog-stats"><span>&#128197; {pcount} artigo{"s" if pcount != 1 else ""}</span></div>
</header>
<main class="blog-content">
  <h2 style="font-family:'Playfair Display',serif;font-size:1.5rem;margin-bottom:20px;color:var(--dark)">&#128214; Todos os Artigos</h2>
  {posts_html}
</main>
<a href="/" class="admin-link">&#9881; Admin</a>"""

    return _page_frame(f"{blog_name} &mdash; Blog sobre {blog_niche}", body)


def generate_article_view(slug: str, blog_info: dict, post: dict) -> str:
    """Gera HTML da visualizacao de um artigo individual."""
    blog_name = esc(blog_info["name"])
    title = esc(post["title"])
    content = post.get("content", "")
    excerpt = esc(post.get("excerpt", "")[:200])
    img = post.get("featured_image_url")
    wc = post.get("word_count", 0) or 0
    rt = max(1, round(wc / 200))
    dt_str = fmt_date(post.get("created_at"))
    keywords = post.get("keywords", "")
    tags = "".join(f'<span class="tag">{esc(k.strip())}</span>' for k in keywords.split(",") if k.strip())

    img_html = f'<img class="featured-image" src="{esc(img)}" alt="{title}">' if img else ''

    body = f"""<header class="blog-header">
  <h1>&#10013; {blog_name}</h1>
  <p>{esc(blog_info.get("nicho",""))}</p>
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
<a href="/" class="admin-link">&#9881; Admin</a>"""

    return _page_frame(f"{title} &mdash; {blog_name}", body)


def generate_not_found() -> str:
    return _page_frame("Pagina nao encontrada",
        '<div class="error-state"><div class="icon">&#128533;</div><h2>Pagina nao encontrada</h2><p><a href="/">Voltar ao inicio</a></p></div>')


def generate_blog_html(slug: str, blog_info: dict, posts: list, post: dict = None) -> str:
    """
    Gera HTML completo do blog.
    Se post for fornecido e valido, renderiza o artigo individual.
    Senao, renderiza a grade de artigos.
    """
    if not blog_info:
        return generate_not_found()

    if post and post.get('title'):
        return generate_article_view(slug, blog_info, post)
    else:
        return generate_blog_list(slug, blog_info, posts)
