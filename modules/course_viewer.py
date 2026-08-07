"""
course_viewer.py — Player público de cursos do DezafiraAdm.

Renderiza uma página HTML com o curso, seus módulos e aulas completas.
Usado como destino de entrega (external_link) dos produtos do Clube,
para que o comprador acesse o conteúdo de forma visual (em vez de JSON).

Nota de segurança/conteúdo: a rota é pública (entrega por link, padrão do
sistema). A página é noindex. Para restringir acesso por compra, seria
necessário um token de acesso por pedido — melhoria futura.
"""
import hashlib
import hmac
import html as html_mod
import os
import re
import time
from typing import Optional


ACCESS_TOKEN_TTL_SECONDS = 30 * 24 * 3600  # 30 dias


def _esc(v):
    """Escapa valor para HTML seguro."""
    return html_mod.escape(str(v if v is not None else ""))


def _access_secret() -> str:
    """Segredo compartilhado para tokens de acesso do player.

    Usa a mesma chave da ponte Adm→Clube (CLUBE_IMPORT_KEY no Adm ==
    IMPORT_API_KEY no Clube). Sem ela configurada, o player fica bloqueado
    (fail-closed).
    """
    return os.getenv("CLUBE_IMPORT_KEY") or os.getenv("IMPORT_API_KEY") or ""


def generate_course_access_token(course_id: str, user_ref: str) -> str:
    """Gera um token de acesso assinado (HMAC-SHA256) para o player.

    Formato: <exp_ts>.<user_ref>.<sig>
    O Clube usa a mesma chave (IMPORT_API_KEY) para gerar no momento da
    entrega; o Adm valida aqui com CLUBE_IMPORT_KEY.
    """
    secret = _access_secret()
    exp = int(time.time()) + ACCESS_TOKEN_TTL_SECONDS
    payload = f"{course_id}:{exp}:{user_ref}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{exp}.{user_ref}.{sig}"


def validate_course_access_token(course_id: str, token: str) -> bool:
    """Valida um token de acesso do player (HMAC + expiração)."""
    if not token:
        return False
    secret = _access_secret()
    if not secret:
        return False
    try:
        exp_str, user_ref, sig = token.split(".", 2)
        exp = int(exp_str)
    except (ValueError, AttributeError):
        return False
    if exp < int(time.time()):
        return False
    payload = f"{course_id}:{exp}:{user_ref}"
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)


def _render_markdown(text: str) -> str:
    """Mini-renderizador markdown → HTML seguro (escapa tudo e aplica formato)."""
    out = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            close_list()
            out.append("<p></p>")
            continue

        # Headings
        hm = re.match(r"^(#{1,4})\s+(.*)$", line)
        if hm:
            close_list()
            level = len(hm.group(1)) + 1  # h2..h5
            out.append(f"<h{min(level, 5)}>{_esc(hm.group(2))}</h{min(level, 5)}>")
            continue

        # Listas não ordenadas
        lm = re.match(r"^[-*•]\s+(.*)$", line)
        if lm:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_esc(lm.group(1))}</li>")
            continue

        # Listas ordenadas
        om = re.match(r"^\d+[.)]\s+(.*)$", line)
        if om:
            if not in_list:
                out.append("<ol>")
                in_list = True
            out.append(f"<li>{_esc(om.group(1))}</li>")
            continue

        close_list()
        # Parágrafo com formatação inline (negrito/itálico) — escapa primeiro
        escaped = _esc(line)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", escaped)
        out.append(f"<p>{escaped}</p>")

    close_list()
    return "\n".join(out)


def generate_course_player_html(course: dict, modules: list) -> str:
    """
    Gera o HTML completo do player de um curso.
    course: dict com id/title/subtitle/description/difficulty/price_cents/cover_url
    modules: lista de dicts {id, number, title, description, lessons: [...]}
    """
    title = _esc(course.get("title", "Curso"))
    subtitle = _esc(course.get("subtitle", "") or "")
    desc = _esc(course.get("description", "") or "")
    difficulty = _esc(course.get("difficulty", ""))
    cover = course.get("cover_url") or ""
    total_lessons = sum(len(m.get("lessons", [])) for m in modules)

    cover_html = ""
    if cover:
        cover_html = f'<img class="cover" src="{_esc(cover)}" alt="" loading="lazy" />'

    mods_html = ""
    for m in modules:
        mnum = m.get("number", "")
        mtitle = _esc(m.get("title", "Módulo"))
        mdesc = _esc(m.get("description", "") or "")
        lessons_html = ""
        for l in m.get("lessons", []):
            lnum = l.get("number", "")
            ltitle = _esc(l.get("title", "Aula"))
            lmin = l.get("estimated_minutes") or 0
            lbody = _render_markdown(l.get("content"))
            lessons_html += f"""
            <details class="lesson">
              <summary>
                <span class="lesson-badge">Aula {lnum}</span>
                <span class="lesson-title">{ltitle}</span>
                <span class="lesson-meta">{lmin} min</span>
              </summary>
              <div class="lesson-body">{lbody}</div>
            </details>"""
        mods_html += f"""
        <section class="module">
          <h3>Módulo {mnum} — {mtitle}</h3>
          {f'<p class="module-desc">{mdesc}</p>' if mdesc else ''}
          {lessons_html}
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} — Área do Aluno</title>
  <meta name="robots" content="noindex, nofollow" />
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; color: #111827; line-height: 1.6; }}
    .topbar {{ background: #111827; color: #fff; padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; }}
    .topbar .brand {{ font-weight: 800; font-size: 1.05rem; }}
    .topbar .tag {{ font-size: 0.75rem; background: #22c55e; color: #052e16; font-weight: 700; padding: 3px 10px; border-radius: 999px; }}
    .wrap {{ max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; }}
    .hero {{ background: #fff; border-radius: 16px; padding: 28px; box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-bottom: 24px; }}
    .hero .cover {{ width: 100%; max-height: 260px; object-fit: cover; border-radius: 10px; margin-bottom: 16px; }}
    .hero h1 {{ font-size: 1.7rem; font-weight: 800; margin-bottom: 8px; }}
    .hero .sub {{ color: #4b5563; margin-bottom: 10px; }}
    .hero .meta {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; }}
    .pill {{ background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; border-radius: 999px; font-size: 0.8rem; font-weight: 600; padding: 4px 12px; }}
    .module {{ background: #fff; border-radius: 12px; padding: 20px 22px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.06); }}
    .module h3 {{ font-size: 1.05rem; font-weight: 700; margin-bottom: 4px; }}
    .module-desc {{ color: #6b7280; font-size: 0.9rem; margin-bottom: 12px; }}
    .lesson {{ border: 1px solid #e5e7eb; border-radius: 10px; margin-top: 10px; overflow: hidden; }}
    .lesson summary {{ list-style: none; cursor: pointer; padding: 12px 14px; display: flex; align-items: center; gap: 10px; background: #f9fafb; }}
    .lesson summary::-webkit-details-marker {{ display: none; }}
    .lesson-badge {{ background: #2563eb; color: #fff; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; }}
    .lesson-title {{ font-weight: 600; flex: 1; }}
    .lesson-meta {{ font-size: 0.78rem; color: #6b7280; }}
    .lesson-body {{ padding: 12px 14px; font-size: 0.92rem; color: #374151; }}
    .lesson-body p {{ margin-bottom: 8px; }}
    .lesson-body h2, .lesson-body h3, .lesson-body h4, .lesson-body h5 {{ margin: 10px 0 6px; font-size: 1rem; }}
    .lesson-body ul, .lesson-body ol {{ margin: 0 0 8px 20px; }}
    .cta {{ text-align: center; margin-top: 28px; }}
    .btn {{ display: inline-block; background: #111827; color: #fff; text-decoration: none; font-weight: 700; padding: 12px 26px; border-radius: 10px; }}
    .btn:hover {{ filter: brightness(1.2); }}
  </style>
</head>
<body>
  <div class="topbar">
    <span class="brand">🎓 {title}</span>
    <span class="tag">Área do Aluno</span>
  </div>
  <div class="wrap">
    <div class="hero">
      {cover_html}
      <h1>{title}</h1>
      {f'<p class="sub">{subtitle}</p>' if subtitle else ''}
      <p>{desc}</p>
      <div class="meta">
        <span class="pill">{_esc(difficulty)}</span>
        <span class="pill">{len(modules)} módulos</span>
        <span class="pill">{total_lessons} aulas</span>
      </div>
    </div>
    {mods_html}
    <div class="cta">
      <a class="btn" href="/products">Voltar ao catálogo</a>
    </div>
  </div>
</body>
</html>"""


def generate_access_denied_html() -> str:
    """Página de acesso negado quando o token é ausente/inválido/expirado."""
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Acesso restrito — Dezafira</title>
  <meta name="robots" content="noindex, nofollow" />
  <style>
    body {{ font-family: system-ui, sans-serif; background: #f3f4f6; display: grid; place-items: center; min-height: 100vh; margin: 0; color: #111827; }}
    .card {{ background: #fff; border-radius: 16px; padding: 40px 32px; max-width: 420px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,.08); }}
    .lock {{ font-size: 3rem; }}
    h1 {{ font-size: 1.4rem; margin: 12px 0 8px; }}
    p {{ color: #6b7280; font-size: .95rem; line-height: 1.6; margin: 0 0 20px; }}
    .btn {{ display: inline-block; background: #111827; color: #fff; text-decoration: none; font-weight: 700; padding: 12px 24px; border-radius: 10px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="lock">🔒</div>
    <h1>Acesso restrito</h1>
    <p>Este conteúdo é exclusivo para compradores. Use o link de acesso que você recebeu após a compra.</p>
    <a class="btn" href="/products">Ver catálogo</a>
  </div>
</body>
</html>"""


def build_course_page(course_id: str) -> Optional[str]:
    """Carrega curso + módulos + aulas do banco e retorna o HTML."""
    from modules.database import SessionLocal, Course, CourseModule, CourseLesson

    db = SessionLocal()
    try:
        c = db.query(Course).filter(Course.id == course_id).first()
        if not c:
            return None
        mods_rows = (
            db.query(CourseModule)
            .filter(CourseModule.course_id == course_id)
            .order_by(CourseModule.module_number)
            .all()
        )
        modules = []
        for m in mods_rows:
            lessons_rows = (
                db.query(CourseLesson)
                .filter(CourseLesson.module_id == m.id)
                .order_by(CourseLesson.lesson_number)
                .all()
            )
            modules.append({
                "id": m.id,
                "number": m.module_number,
                "title": m.title,
                "description": m.description,
                "lessons": [
                    {
                        "number": l.lesson_number,
                        "title": l.title,
                        "content": l.content,
                        "estimated_minutes": l.estimated_minutes,
                    }
                    for l in lessons_rows
                ],
            })
        course = {
            "id": c.id,
            "title": c.title,
            "subtitle": c.subtitle,
            "description": c.description,
            "difficulty": c.difficulty,
            "price_cents": c.price_cents,
            "cover_url": c.cover_url,
        }
        return generate_course_player_html(course, modules)
    finally:
        db.close()
