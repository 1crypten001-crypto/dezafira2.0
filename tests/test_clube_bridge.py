"""Testes da publicação do Blueprint (F5) — ponte Adm → Clube com mocks."""

import pytest

from modules.database import create_db_blueprint, get_db_blueprint, delete_db_blueprint, update_db_blueprint


def _review_blueprint():
    """Blueprint pronto em status=review com conteúdo de todos os estágios."""
    b = create_db_blueprint(
        name="Pub Teste", theme="Curso de Marketing Digital", niche="Marketing Digital",
        price_cents=4990, formats=["curso", "blog"],
        config={"funil": {"upsell": {"name": "Mentoria", "price_cents": 1990},
                          "downsell": {"name": "Guia Rápido", "price_cents": 990}}},
    )
    content = {
        "fundacao": {"name": "Curso de Marketing Digital", "slug": "curso-marketing-digital",
                     "description": "Desc", "pitch": "P", "cta_primary": "C", "cta_secondary": "V"},
        "conteudo": {
            "formats": ["curso", "blog"],
            "artifacts": [
                {"format": "curso", "id": "crs_1", "title": "Curso de Marketing Digital",
                 "cover_url": "", "price_cents": 4990,
                 "external_link": "http://backend/curso/crs_1", "status": "completed"},
                {"format": "blog", "id": "ch_1", "title": "Blog", "slug": "post-1",
                 "cover_url": "", "status": "completed", "articles_generated": 1},
            ],
        },
        "assets": {"slots": [
            {"key": "product_image", "width": 1024, "height": 1024},
            {"key": "upsell_image", "width": 1200, "height": 630},
            {"key": "downsell_image", "width": 1200, "height": 630},
        ]},
        "landing": {"template": "dezafira", "blocks": [
            {"id": "hero", "type": "hero", "properties": {"title": "X"}},
        ]},
        "funil": {
            "order_bump": None,
            "upsell": {"name": "Mentoria", "price_cents": 1990, "slug": "mentoria"},
            "downsell": {"name": "Guia Rápido", "price_cents": 990, "slug": "guia-rapido"},
        },
    }
    assets = {
        "product_image": {"url": "/outputs/bp/product.png", "source": "ai", "provider": "agnes"},
        "upsell_image": {"url": "/outputs/bp/upsell.png", "source": "ai", "provider": "agnes"},
        "downsell_image": {"url": "/outputs/bp/downsell.png", "source": "ai", "provider": "agnes"},
        "member_cover": {"url": "/outputs/bp/member.png", "source": "ai", "provider": "agnes"},
        "blog_banner_sidebar": {"url": "/outputs/bp/side.png", "source": "ai", "provider": "agnes"},
        "blog_banner_inline": {"url": "/outputs/bp/inline.png", "source": "ai", "provider": "agnes"},
    }
    update_db_blueprint(b["id"], status="review", stage="revisao", content=content, assets=assets)
    return b


@pytest.mark.asyncio
async def test_publish_fluxo_completo_ok(monkeypatch):
    from modules import clube_bridge

    calls = {"import": [], "sync": 0, "landing": 0, "member": 0}

    async def fake_import_product(payload):
        calls["import"].append(payload)
        return {"success": True, "product_id": 42, "slug": payload.get("slug") or "x"}

    async def fake_sync_blog(payload):
        calls["sync"] += 1
        return {"success": True, "summary": {"posts_inserted": 1, "ads_created": 2}}

    async def fake_landing(payload):
        calls["landing"] += 1
        return {"success": True, "slug": payload.get("slug"), "public_url": "/p/curso-marketing-digital"}

    async def fake_member(payload):
        calls["member"] += 1
        return {"success": True, "course_id": 7}

    monkeypatch.setattr(clube_bridge, "bridge_import_product", fake_import_product)
    monkeypatch.setattr(clube_bridge, "bridge_sync_blog", fake_sync_blog)
    monkeypatch.setattr(clube_bridge, "cli_create_landing", fake_landing)
    monkeypatch.setattr(clube_bridge, "bridge_member_course", fake_member)

    from modules.blueprint_engine import publish_blueprint

    b = _review_blueprint()
    try:
        res = await publish_blueprint(b["id"])
        assert res["status"] == "published"

        # Filhos criados primeiro (upsell/downsell) → principal com ids
        assert len(calls["import"]) == 3
        assert calls["import"][0]["name"] == "Mentoria"
        assert calls["import"][2]["name"] == "Curso de Marketing Digital"
        assert calls["import"][2]["upsell_product_id"] == 42
        assert calls["import"][2]["downsell_product_id"] == 42
        assert calls["sync"] == 1
        assert calls["landing"] == 1
        assert calls["member"] == 1

        stored = get_db_blueprint(b["id"])
        assert stored["status"] == "published"
        assert stored["publish_log"]["produto"]["status"] == "ok"
        assert stored["publish_log"]["landing"]["status"] == "ok"
        assert stored["publish_log"]["membros"]["status"] == "ok"
        assert stored["publish_log"]["blog"]["status"] == "ok"
    finally:
        delete_db_blueprint(b["id"])


@pytest.mark.asyncio
async def test_publish_falha_quando_ponte_do_produto_principal_falha(monkeypatch):
    from modules import clube_bridge

    async def fake_import_product(payload):
        # Filhos ok, principal falha
        if payload.get("name") == "Curso de Marketing Digital":
            return {"success": False, "error": "Clube HTTP 500"}
        return {"success": True, "product_id": 10, "slug": "x"}

    async def fake_others(**kw):
        return {"success": True}

    monkeypatch.setattr(clube_bridge, "bridge_import_product", fake_import_product)
    monkeypatch.setattr(clube_bridge, "bridge_sync_blog", fake_others)
    monkeypatch.setattr(clube_bridge, "cli_create_landing", fake_others)
    monkeypatch.setattr(clube_bridge, "bridge_member_course", fake_others)

    from modules.blueprint_engine import publish_blueprint

    b = _review_blueprint()
    try:
        res = await publish_blueprint(b["id"])
        assert res["status"] == "failed"
        stored = get_db_blueprint(b["id"])
        assert stored["publish_log"]["produto"]["status"] == "failed"
    finally:
        delete_db_blueprint(b["id"])


@pytest.mark.asyncio
async def test_publish_erro_quando_blueprint_nao_existe():
    from modules.blueprint_engine import publish_blueprint
    with pytest.raises(ValueError):
        await publish_blueprint("bp_inexistente")
