"""Testes do Agnes Studio — estúdio de capas (HTML → PNG + fallback Pillow).

Cobrem: design determinístico, slugs da galeria, HTML com escape seguro,
geração das 3 capas (course/book/post) e o fallback local Pillow.
"""

import asyncio
import os

import pytest

from modules import agnes_studio
from modules.agnes_studio import AgnesStudio, DEFAULT_STYLE, STYLES


# ─── Design ─────────────────────────────────────────────────────────────

def test_make_design_deterministic():
    s = AgnesStudio()
    d1 = s._make_design("moderno", "financas")
    d2 = s._make_design("moderno", "financas")
    assert d1 == d2
    assert d1["style_id"] == "moderno"
    assert d1["colors"]["accent"] == STYLES["moderno"]["colors"]["accent"]


def test_make_design_fallback_unknown_style():
    d = AgnesStudio()._make_design("nao-existe", "")
    assert d["style_id"] == DEFAULT_STYLE


def test_make_design_brand_kit_overrides_style():
    """Brand kit (cores/fontes customizadas) sobrepõe o estilo base."""
    kit = {
        "colors": {"accent": "#123456", "bg": "#ffffff"},
        "font": "Verdana, sans-serif",
    }
    d = AgnesStudio()._make_design("moderno", "financas", brand_kit=kit)
    assert d["colors"]["accent"] == "#123456"
    assert d["colors"]["bg"] == "#ffffff"
    assert d["font"] == "Verdana, sans-serif"
    # Não mencionados no kit → mantêm o estilo
    assert d["colors"]["muted"] == STYLES["moderno"]["colors"]["muted"]
    # Kit com cores inválidas é ignorado (segurança)
    bad = AgnesStudio()._make_design("moderno", "", brand_kit={"colors": {"accent": "azul"}})
    assert bad["colors"]["accent"] == STYLES["moderno"]["colors"]["accent"]


def test_make_design_brand_kit_flat_format():
    """Regressão: brand kit no formato plano {primary_color, accent_color}
    (usado pela API/seed) é normalizado para colors.* sem quebrar."""
    kit = {"primary_color": "#ff5b06", "accent_color": "#0f1a21"}
    d = AgnesStudio()._make_design("moderno", "financas", brand_kit=kit)
    assert d["colors"]["accent"] == "#ff5b06"
    assert d["colors"]["bg"] == "#0f1a21"
    assert d["colors"]["bg2"] == "#0f1a21"


def test_make_design_keeps_persisted_design():
    # Regeneração com design persistido mantém a identidade visual
    persisted = AgnesStudio()._make_design("elegante", "cristao")
    novo = AgnesStudio()._make_design("moderno", "outro")
    assert novo["style_id"] == "moderno"  # sem design persistido
    # O endpoint passa o design persistido → generate_* usa ele (testado abaixo)


# ─── Slug da galeria ────────────────────────────────────────────────────

def test_slug_for_course_book_post():
    s = AgnesStudio()
    assert s._slug_for("crs", "crs_abc123") == "crs-abc123"
    assert s._slug_for("book", "book_abc123") == "book-abc123"
    assert s._slug_for("ebook", "book_abc123") == "book-abc123"
    assert s._slug_for("ebook", "ebook_xyz") == "ebook-xyz"
    assert s._slug_for("post", "post_abc123") == "post-abc123"
    assert s._slug_for("crs", "") == "crs-"


# ─── HTML (escape seguro + elementos) ───────────────────────────────────

def test_html_course_escapes_and_contains_key_parts():
    s = AgnesStudio()
    design = s._make_design("moderno", "financas")
    html = s._html_course(
        design, title="Meu Curso <b>Teste</b>", subtitle="Subtítulo",
        niche="Finanças", difficulty="Iniciante", modules_count=5,
        author="Dezafira Studio",
    )
    assert "Meu Curso &lt;b&gt;Teste&lt;/b&gt;" in html
    assert "Dezafira Studio" in html
    assert "dezafira.com.br" in html
    assert "5 módulos" in html
    assert "1280px" in html and "720px" in html


def test_html_blog_and_ebook_contain_identity():
    s = AgnesStudio()
    design = s._make_design("tech", "saude")
    blog = s._html_blog(design, title="Artigo Teste", subtitle="Excerpt",
                        niche="Saúde", blog_name="Canal Saúde")
    assert "Canal Saúde" in blog and "1200px" in blog and "630px" in blog
    ebook = s._html_ebook(design, title="Ebook Teste", subtitle="Sub",
                          author="Autor X", niche="Saúde")
    assert "Autor X" in ebook and "1200px" in ebook and "1600px" in ebook


# ─── Geração (render mockado — sem browser) ─────────────────────────────

async def _fake_render(html, kind, design, title, subtitle, author, width, height):
    return b"PNGDATA"


def test_generate_course_cover_saves_file(tmp_path, monkeypatch):
    s = AgnesStudio(outputs_dir=str(tmp_path))
    monkeypatch.setattr(s, "_render", _fake_render)
    res = asyncio.run(s.generate_course_cover(
        title="Curso Teste", subtitle="Sub", author="Autor",
        niche="Finanças", course_id="crs_abc123",
    ))
    assert res["cover_url"].startswith("/outputs/agnes/")
    assert res["filename"].startswith("crs-abc123_") and res["filename"].endswith(".png")
    assert res["width"] == 1280 and res["height"] == 720
    assert res["provider"] == "agnes-studio"
    assert res["design"]["style_id"] == "moderno"
    fp = os.path.join(tmp_path, res["filename"])
    assert os.path.isfile(fp) and open(fp, "rb").read() == b"PNGDATA"


def test_generate_blog_and_ebook_sizes(tmp_path, monkeypatch):
    s = AgnesStudio(outputs_dir=str(tmp_path))
    monkeypatch.setattr(s, "_render", _fake_render)
    blog = asyncio.run(s.generate_blog_cover(
        title="Artigo", subtitle="Excerpt", niche="Saúde", post_id="post_xyz",
    ))
    assert blog["filename"].startswith("post-xyz_")
    assert blog["width"] == 1200 and blog["height"] == 630
    book = asyncio.run(s.generate_ebook_cover(
        title="Ebook", subtitle="Sub", author="A", niche="Saúde", book_id="book_abc",
    ))
    assert book["filename"].startswith("book-abc_")
    assert book["width"] == 1200 and book["height"] == 1600


def test_generate_reuses_persisted_design(tmp_path, monkeypatch):
    s = AgnesStudio(outputs_dir=str(tmp_path))
    monkeypatch.setattr(s, "_render", _fake_render)
    persisted = s._make_design("elegante", "cristao")
    res = asyncio.run(s.generate_course_cover(
        title="T", course_id="crs_1", design=persisted,
    ))
    assert res["design"] == persisted  # identidade visual preservada


# ─── Fallback Pillow (nunca falha sem browser) ──────────────────────────

def test_pillow_fallback_renders_real_png():
    s = AgnesStudio()
    design = s._make_design("moderno", "financas")
    png = s._render_via_pillow("course", design, "Título de Teste",
                               "Subtítulo", "Autor", 1280, 720)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 1000


def test_render_falls_back_to_pillow_when_obscura_fails(monkeypatch):
    s = AgnesStudio()

    async def boom(*a, **k):
        raise RuntimeError("Obscura fora do ar")

    monkeypatch.setattr(s, "_render_via_obscura", boom)
    png = asyncio.run(s._render("<html></html>", "course",
                                s._make_design("moderno", ""), "T", "", "A", 640, 360))
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_obscura_disabled_raises(monkeypatch):
    monkeypatch.setenv("OBSCURA_ENABLED", "false")
    s = AgnesStudio()
    with pytest.raises(Exception):
        asyncio.run(s._render_via_obscura("<html></html>", 100, 100))


# ─── Integração: endpoint /agnes-cover (JWT + admin + banco ISOLADO) ────

def test_endpoint_course_agnes_cover_via_http(monkeypatch):
    """End-to-end pelo FastAPI: JWT de admin → curso → Agnes Studio → capa persistida.
    Usa o banco temporário do conftest (nunca toca o dezafira.db real)."""
    import hashlib
    from datetime import datetime

    from fastapi.testclient import TestClient

    # AUTH_SECRET precisa existir ANTES do import de server.py (que valida ≥16 chars)
    monkeypatch.setenv("AUTH_SECRET", "test-secret-12345678901234567890")
    monkeypatch.setenv("OBSCURA_ENABLED", "false")

    from server import AUTH_SECRET, app
    from modules import agnes_studio
    from modules.database import (create_db_course, create_db_user,
                                  get_db_course, update_db_user)

    admin = create_db_user(email="admin@agnes.test", name="Admin Agnes", password_hash="x")
    assert admin, "admin não criado no banco isolado"
    update_db_user(admin["id"], role="admin")

    course = create_db_course(title="Curso Agnes Teste", topic="Teologia")
    assert course, "curso não criado no banco isolado"

    payload = f"{admin['id']}:{int(datetime.utcnow().timestamp()) + 3600}"
    sig = hashlib.sha256(f"{payload}:{AUTH_SECRET}".encode()).hexdigest()[:32]
    token = f"{payload}:{sig}"

    async def fake_generate(self, **kwargs):
        return {
            "cover_url": "/outputs/agnes/crs-test_00000000.png",
            "filename": "crs-test_00000000.png",
            "design": {"style_id": "moderno"},
            "width": 1280, "height": 720,
        }

    monkeypatch.setattr(agnes_studio.AgnesStudio, "generate_course_cover", fake_generate)

    client = TestClient(app)
    r = client.post(
        f"/api/v1/courses/{course['id']}/agnes-cover",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cover_url"] == "/outputs/agnes/crs-test_00000000.png"

    # A capa foi persistida no curso (update_db_course com cover_url + cover_design)
    persisted = get_db_course(course["id"])
    assert persisted["cover_url"] == "/outputs/agnes/crs-test_00000000.png"
    assert "style_id" in (persisted.get("cover_design") or "")


def test_endpoint_requires_admin(monkeypatch):
    """Sem token → 401 (rota protegida por require_admin)."""
    monkeypatch.setenv("AUTH_SECRET", "test-secret-12345678901234567890")
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)
    r = client.post("/api/v1/courses/nao-existe/agnes-cover")
    assert r.status_code in (401, 403)


def test_endpoint_accepts_style_id(monkeypatch):
    """O endpoint agnes-cover aceita {style_id} no body (seletor da UI)."""
    import hashlib
    from datetime import datetime

    from fastapi.testclient import TestClient

    monkeypatch.setenv("AUTH_SECRET", "test-secret-12345678901234567890")
    monkeypatch.setenv("OBSCURA_ENABLED", "false")

    from server import AUTH_SECRET, app
    from modules import agnes_studio
    from modules.database import (create_db_course, create_db_user,
                                  update_db_user)

    admin = create_db_user(email="admin@style.test", name="Admin Style", password_hash="x")
    update_db_user(admin["id"], role="admin")
    course = create_db_course(title="Curso Style", topic="Teologia")

    payload = f"{admin['id']}:{int(datetime.utcnow().timestamp()) + 3600}"
    sig = hashlib.sha256(f"{payload}:{AUTH_SECRET}".encode()).hexdigest()[:32]
    token = f"{payload}:{sig}"

    captured = {}

    async def fake_generate(self, **kwargs):
        captured.update(kwargs)
        return {"cover_url": "/outputs/agnes/x.png", "design": {"style_id": kwargs.get("style_id")}}

    monkeypatch.setattr(agnes_studio.AgnesStudio, "generate_course_cover", fake_generate)

    client = TestClient(app)
    r = client.post(
        f"/api/v1/courses/{course['id']}/agnes-cover",
        headers={"Authorization": f"Bearer {token}"},
        json={"style_id": "elegante"},
    )
    assert r.status_code == 200, r.text
    assert captured.get("style_id") == "elegante"


def test_endpoint_accepts_brand_kit(monkeypatch):
    """Brand kit global no body → vira design customizado no studio (prioridade)."""
    import hashlib
    from datetime import datetime

    from fastapi.testclient import TestClient

    monkeypatch.setenv("AUTH_SECRET", "test-secret-12345678901234567890")
    monkeypatch.setenv("OBSCURA_ENABLED", "false")

    from server import AUTH_SECRET, app
    from modules import agnes_studio
    from modules.database import (create_db_course, create_db_user,
                                  update_db_user)

    admin = create_db_user(email="admin@bk.test", name="Admin BK", password_hash="x")
    update_db_user(admin["id"], role="admin")
    course = create_db_course(title="Curso BK", topic="Teologia")

    payload = f"{admin['id']}:{int(datetime.utcnow().timestamp()) + 3600}"
    sig = hashlib.sha256(f"{payload}:{AUTH_SECRET}".encode()).hexdigest()[:32]
    token = f"{payload}:{sig}"

    captured = {}

    async def fake_generate(self, **kwargs):
        captured.update(kwargs)
        return {"cover_url": "/outputs/agnes/x.png", "design": kwargs.get("design") or {}}

    monkeypatch.setattr(agnes_studio.AgnesStudio, "generate_course_cover", fake_generate)

    client = TestClient(app)
    r = client.post(
        f"/api/v1/courses/{course['id']}/agnes-cover",
        headers={"Authorization": f"Bearer {token}"},
        json={"style_id": "elegante", "brand_kit": {"colors": {"accent": "#123456"}}},
    )
    assert r.status_code == 200, r.text
    design = captured.get("design") or {}
    assert design.get("colors", {}).get("accent") == "#123456"


# ─── E2E: galeria Agnes (capa REAL + /gallery + /use-cover) ────────────────

def test_agnes_gallery_and_use_cover_e2e(monkeypatch):
    """Gera capa REAL (fallback Pillow) em outputs/agnes, lista na galeria e
    aplica via use-cover num post do banco isolado. Arquivo é removido ao final."""
    import hashlib
    from datetime import datetime

    from fastapi.testclient import TestClient

    monkeypatch.setenv("AUTH_SECRET", "test-secret-12345678901234567890")
    monkeypatch.setenv("OBSCURA_ENABLED", "false")

    from server import AUTH_SECRET, _BASE_DIR, app
    from modules.database import (create_db_blog_channel, create_db_blog_post,
                                  create_db_user, get_db_blog_post, update_db_user)

    admin = create_db_user(email="admin@gallery.test", name="Admin Galeria", password_hash="x")
    update_db_user(admin["id"], role="admin")
    payload = f"{admin['id']}:{int(datetime.utcnow().timestamp()) + 3600}"
    sig = hashlib.sha256(f"{payload}:{AUTH_SECRET}".encode()).hexdigest()[:32]
    token = f"{payload}:{sig}"
    headers = {"Authorization": f"Bearer {token}"}

    ch = create_db_blog_channel(name="Canal E2E", nicho="Saúde", lang="PT")
    post = create_db_blog_post(channel_id=ch["id"], title="Post E2E",
                               slug="post-e2e", content="x")
    post_id = post["id"]

    # 1. Capa real (Pillow) direto no diretório da galeria (outputs/agnes)
    out_dir = os.path.join(_BASE_DIR, "outputs", "agnes")
    studio = AgnesStudio(outputs_dir=out_dir)
    design = studio._make_design("tech", "saude")
    png = studio._render_via_pillow("blog", design, "Post E2E", "", "Dezafira Studio", 1200, 630)
    saved = studio._save_cover("post", post_id, png, design, 1200, 630)
    filename = saved["filename"]
    fp = os.path.join(out_dir, filename)
    assert os.path.isfile(fp)

    client = TestClient(app)
    try:
        # 2. Galeria lista a capa com produto de origem resolvido
        r = client.get("/api/v1/agnes/gallery", headers=headers)
        assert r.status_code == 200, r.text
        match = [im for im in r.json()["images"] if im["filename"] == filename]
        assert match, "capa não encontrada na galeria"
        assert match[0]["entity_type"] == "post"
        assert match[0]["entity_id"] == post_id
        assert match[0]["title"] == "Post E2E"

        # 3. use-cover aplica a capa no post
        r2 = client.post("/api/v1/agnes/use-cover", headers=headers, json={
            "entity_type": "post", "entity_id": post_id, "filename": filename,
        })
        assert r2.status_code == 200, r2.text
        assert r2.json()["cover_url"] == f"/outputs/agnes/{filename}"
        p = get_db_blog_post(post_id)
        assert p["featured_image_url"] == f"/outputs/agnes/{filename}"
        assert p["image_provider"] == "agnes"

        # 4. DELETE remove a capa da galeria
        r3 = client.delete(f"/api/v1/agnes/gallery/{filename}", headers=headers)
        assert r3.status_code == 200, r3.text
        assert not os.path.exists(fp)
        # Re-deletar → 404
        r4 = client.delete(f"/api/v1/agnes/gallery/{filename}", headers=headers)
        assert r4.status_code == 404
    finally:
        try:
            os.remove(fp)
        except Exception:
            pass


def test_blueprint_patch_config_brand_kit_via_http(monkeypatch):
    """PATCH /api/v1/blueprints/{id} salva o brand_kit no config (merge parcial)."""
    import hashlib
    from datetime import datetime

    from fastapi.testclient import TestClient

    monkeypatch.setenv("AUTH_SECRET", "test-secret-12345678901234567890")
    from server import AUTH_SECRET, app
    from modules.database import (create_db_blueprint, create_db_user,
                                  get_db_blueprint, update_db_user)

    admin = create_db_user(email="admin@brandkit.test", name="Admin BK", password_hash="x")
    update_db_user(admin["id"], role="admin")
    payload = f"{admin['id']}:{int(datetime.utcnow().timestamp()) + 3600}"
    sig = hashlib.sha256(f"{payload}:{AUTH_SECRET}".encode()).hexdigest()[:32]
    token = f"{payload}:{sig}"

    bp = create_db_blueprint(name="BP BK", theme="Curso", niche="Finanças",
                             price_cents=1990, formats=["ebook"])

    client = TestClient(app)
    r = client.patch(
        f"/api/v1/blueprints/{bp['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"config": {"brand_kit": {"colors": {"accent": "#123456"}, "font": "Verdana"}}},
    )
    assert r.status_code == 200, r.text
    assert r.json()["config"]["brand_kit"]["colors"]["accent"] == "#123456"
    persisted = get_db_blueprint(bp["id"])["config"]
    assert persisted["brand_kit"]["colors"]["accent"] == "#123456"
    # Merge preserva outras chaves do config (ex: template_landing)
    r2 = client.patch(
        f"/api/v1/blueprints/{bp['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"config": {"template_landing": "dezafira"}},
    )
    assert r2.status_code == 200
    persisted2 = get_db_blueprint(bp["id"])["config"]
    assert persisted2["template_landing"] == "dezafira"
    assert persisted2["brand_kit"]["colors"]["accent"] == "#123456"


# ─── Blueprint: capa editorial Agnes Studio (asset) ─────────────────────────

def test_blueprint_agnes_cover_endpoint_via_http(monkeypatch):
    """POST /api/v1/blueprints/{id}/assets/agnes-cover gera o asset do slot
    com provider agnes-studio e persistência (banco isolado)."""
    import hashlib
    from datetime import datetime

    from fastapi.testclient import TestClient

    monkeypatch.setenv("AUTH_SECRET", "test-secret-12345678901234567890")
    monkeypatch.setenv("OBSCURA_ENABLED", "false")

    from server import AUTH_SECRET, app
    from modules import blueprint_engine
    from modules.database import (create_db_blueprint, create_db_user,
                                  get_db_blueprint, update_db_blueprint, update_db_user)

    admin = create_db_user(email="admin@bpagnes.test", name="Admin BP", password_hash="x")
    update_db_user(admin["id"], role="admin")
    payload = f"{admin['id']}:{int(datetime.utcnow().timestamp()) + 3600}"
    sig = hashlib.sha256(f"{payload}:{AUTH_SECRET}".encode()).hexdigest()[:32]
    token = f"{payload}:{sig}"

    bp = create_db_blueprint(name="BP Agnes", theme="Curso Teste", niche="Finanças",
                             price_cents=1990, formats=["curso"])
    update_db_blueprint(bp["id"], content={
        "fundacao": {"name": "Curso Teste", "description": "Desc"},
        "assets": {"slots": [{"key": "product_image", "label": "Capa do produto",
                               "width": 1024, "height": 1024, "prompt": "x"}]},
    })

    async def fake_product(self, **kwargs):
        return {"cover_url": "/outputs/agnes/prod-test_0000.png", "width": 1024,
                "height": 1024, "design": {"style_id": kwargs.get("style_id")}}

    monkeypatch.setattr(agnes_studio.AgnesStudio, "generate_product_cover", fake_product)

    client = TestClient(app)
    r = client.post(
        f"/api/v1/blueprints/{bp['id']}/assets/agnes-cover",
        headers={"Authorization": f"Bearer {token}"},
        json={"slot": "product_image", "style_id": "elegante"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provider"] == "agnes-studio"
    assert body["agnes_style"] == "elegante"
    persisted = get_db_blueprint(bp["id"])["assets"]["product_image"]
    assert persisted["url"] == "/outputs/agnes/prod-test_0000.png"
    assert persisted["provider"] == "agnes-studio"
