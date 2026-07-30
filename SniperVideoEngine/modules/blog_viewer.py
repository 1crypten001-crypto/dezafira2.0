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


def generate_blog_html(slug: str, blog_info: dict, posts: list) -> str:
    """Gera HTML completo do blog com artigos renderizados no servidor."""
    if not blog_info:
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Blog nao encontrado</title>
<style>body{{font-family:system-ui;max-width:800px;margin:40px auto;padding:0 20px;color:#333;line-height:1.6;text-align:center}}h1{{color:#1a1a1a}}</style>
</head>
<body><h1>Blog nao encontrado</h1><p><a href="/">Voltar ao painel</a></p></body></html>"""

    blog_name = esc(blog_info["name"])
    blog_niche = esc(blog_info.get("nicho", ""))
    pcount = len(posts)

    # Build cards
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
        <article class="post-card" onclick="window.location='/blog/{slug}?post={pid}'">
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
            <a href="/blog/{slug}?post={pid}" class="read-more">Ler artigo &rarr;</a>
          </div>
        </article>"""

    posts_html = ""
    if cards_html:
        posts_html = f'<div class="posts-grid">{cards_html}</div>'
    else:
        posts_html = '<div class="empty-state"><div class="icon">&#128221;</div><p>Nenhum artigo publicado ainda. Volte em breve!</p></div>'

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{blog_name} &mdash; Blog sobre {blog_niche}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
:root{{--gold:#d4a853;--cream:#faf6ef;--dark:#1a1410;--text:#3d3227;--text-light:#7a6b5a;--border:#e0d5c0;--radius:12px;--shadow:0 2px 20px rgba(0,0,0,0.08)}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--cream);color:var(--text);line-height:1.7}}
.blog-header{{background:linear-gradient(135deg,var(--dark),var(--dark));padding:60px 24px 40px;text-align:center}}
.blog-header h1{{font-family:'Playfair Display',serif;font-size:2.5rem;color:var(--gold);margin-bottom:8px}}
.blog-header p{{color:var(--text-light);font-size:1.05rem;max-width:600px;margin:0 auto}}
.blog-stats{{display:flex;gap:12px;justify-content:center;margin-top:16px;flex-wrap:wrap}}
.blog-stats span{{background:rgba(255,255,255,0.08);padding:6px 14px;border-radius:20px;font-size:.85rem;color:var(--gold-light)}}
.blog-content{{max-width:900px;margin:0 auto;padding:32px 20px}}
.posts-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:20px}}
@media(max-width:640px){{.posts-grid{{grid-template-columns:1fr}}}}
.post-card{{background:#fff;border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);transition:transform .2s,box-shadow .2s;cursor:pointer}}
.post-card:hover{{transform:translateY(-3px);box-shadow:0 8px 30px rgba(0,0,0,0.12)}}
.card-image{{width:100%;height:200px;object-fit:cover;display:block}}
.card-image-placeholder{{width:100%;height:200px;background:linear-gradient(135deg,#2a2219,#3d3227);display:flex;align-items:center;justify-content:center;font-size:3rem;color:var(--gold)}}
.card-body{{padding:20px}}
.post-title{{font-family:'Playfair Display',serif;font-size:1.2rem;margin-bottom:8px;color:var(--dark)}}
.post-excerpt{{font-size:.9rem;color:var(--text-light);margin-bottom:12px;line-height:1.5}}
.post-meta{{display:flex;gap:12px;flex-wrap:wrap;font-size:.8rem;color:var(--text-light);margin-bottom:10px}}
.post-meta span{{background:var(--cream);padding:3px 10px;border-radius:12px}}
.post-tags{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}}
.tag{{background:rgba(212,168,83,0.12);color:#a67c2e;padding:3px 10px;border-radius:12px;font-size:.75rem}}
.read-more{{display:inline-block;color:var(--gold);font-weight:600;font-size:.9rem;text-decoration:none}}
.read-more:hover{{color:#a67c2e}}
.empty-state{{text-align:center;padding:60px 20px;color:var(--text-light)}}
.admin-link{{position:fixed;bottom:20px;right:20px;background:var(--dark);color:var(--gold);padding:10px 18px;border-radius:var(--radius);font-size:.85rem;text-decoration:none;opacity:.7;z-index:100}}
.admin-link:hover{{opacity:1}}
</style>
</head>
<body>
<header class="blog-header">
  <h1>&#10013; {blog_name}</h1>
  <p>{blog_niche}</p>
  <div class="blog-stats"><span>&#128197; {pcount} artigo{"s" if pcount != 1 else ""}</span></div>
</header>
<main class="blog-content">
  <h2 style="font-family:'Playfair Display',serif;font-size:1.5rem;margin-bottom:20px;color:var(--dark)">&#128214; Todos os Artigos</h2>
  {posts_html}
</main>
<a href="/" class="admin-link">&#9881; Admin</a>
</body>
</html>"""
