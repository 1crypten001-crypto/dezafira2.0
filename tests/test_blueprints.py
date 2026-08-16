"""Testes do Blueprint de Produto (F1).

Cobre:
  - CRUD da tabela blueprints (create/get/list/update/delete)
  - Fluxo do motor: run → estágios persistem → status final "review"
"""

import pytest
import asyncio

from modules.database import (
    create_db_blueprint,
    get_db_blueprint,
    list_db_blueprints,
    update_db_blueprint,
    delete_db_blueprint,
)


@pytest.fixture
def sample_bp():
    bp = create_db_blueprint(
        name="Teste Blueprint",
        theme="Guia Definitivo de Emagrecimento com IA",
        niche="Fitness & Saúde",
        price_cents=1990,
        formats=["ebook", "blog"],
        config={"artigos": 3, "template_landing": "dezafira"},
    )
    assert "id" in bp and not bp.get("error"), bp
    yield bp
    delete_db_blueprint(bp["id"])


def test_create_blueprint(sample_bp):
    assert sample_bp["status"] == "draft"
    assert sample_bp["stage"] == ""
    assert sample_bp["theme"].startswith("Guia Definitivo")
    assert sample_bp["formats"] == ["ebook", "blog"]
    assert sample_bp["config"]["template_landing"] == "dezafira"
    assert sample_bp["assets"] == {}
    assert sample_bp["publish_log"] == {}


def test_get_blueprint(sample_bp):
    bp = get_db_blueprint(sample_bp["id"])
    assert bp is not None
    assert bp["id"] == sample_bp["id"]
    assert bp["name"] == "Teste Blueprint"


def test_list_blueprints(sample_bp):
    items = list_db_blueprints(limit=100)
    ids = [b["id"] for b in items]
    assert sample_bp["id"] in ids


def test_update_blueprint(sample_bp):
    ok = update_db_blueprint(
        sample_bp["id"],
        status="generating",
        stage="fundacao",
        content={"fundacao": {"slug": "guia-emagrecimento"}},
    )
    assert ok
    bp = get_db_blueprint(sample_bp["id"])
    assert bp["status"] == "generating"
    assert bp["stage"] == "fundacao"
    assert bp["content"]["fundacao"]["slug"] == "guia-emagrecimento"


def test_delete_blueprint(sample_bp):
    assert delete_db_blueprint(sample_bp["id"]) is True
    assert get_db_blueprint(sample_bp["id"]) is None


@pytest.mark.asyncio
async def test_engine_flow_run_to_review(sample_bp, monkeypatch):
    """Disparar o motor deve percorrer os estágios e terminar em 'review'."""
    from unittest.mock import AsyncMock
    from modules.blueprint_engine import run_blueprint

    class _FakeImageAgent:
        async def generate_image_for_post(self, **kw):
            return {"image_url": "https://img/fake.png", "provider": "agnes",
                    "credit": "A", "expanded_prompt": "super prompt fake"}

    # Pipelines e imagens reais são pesadas — mock para testar a orquestração
    monkeypatch.setattr("modules.ebook_pipeline.run_ebook_macro_pipeline", AsyncMock(return_value={
        "book_id": "book_abc", "title": "X", "cover_url": "", "status": "completed", "error": ""}))
    monkeypatch.setattr("modules.blog_pipeline.run_blog_macro_pipeline", AsyncMock(return_value={
        "channel_id": "ch_1", "status": "completed", "articles_generated": 1, "banner_url": ""}))
    monkeypatch.setattr("modules.image_factory.ImageGeneratorAgent", _FakeImageAgent)

    async def fake_agnes_cover(bp_id, slot, style_id="moderno"):
        return {"slot": slot, "url": "/outputs/agnes/prod-fake.png", "super_prompt": "agnes",
                "provider": "agnes-studio", "source": "ai", "width": 1024, "height": 1024,
                "agnes_style": style_id}

    monkeypatch.setattr("modules.blueprint_engine.generate_agnes_cover_asset", fake_agnes_cover)

    result = await run_blueprint(sample_bp["id"])
    assert result["status"] == "review"
    assert result["stage"] == "revisao"

    bp = get_db_blueprint(sample_bp["id"])
    assert bp["status"] == "review"
    assert bp["stage"] == "revisao"
    # Fundação determinística preenchida
    fund = bp["content"]["fundacao"]
    assert fund["slug"] == "guia-definitivo-de-emagrecimento-com-ia"
    assert "pitch" in fund
    # Estruturas dos próximos estágios criadas (motor real)
    assert bp["content"]["conteudo"]["formats"] == ["ebook", "blog"]
    slot_keys = [s["key"] for s in bp["content"]["assets"]["slots"]]
    assert "product_image" in slot_keys
    assert "product_image_agnes" in slot_keys
    assert "landing_hero" in slot_keys
    assert bp["assets"]["product_image"]["source"] == "ai"
    assert bp["assets"]["product_image"]["super_prompt"].startswith("super prompt")
    assert bp["assets"]["product_image_agnes"]["provider"] == "agnes-studio"
    assert bp["content"]["landing"]["template"] == "dezafira"
    assert bp["content"]["funil"]["upsell"] is None


@pytest.mark.asyncio
async def test_engine_flow_failed_unknown_bp():
    from modules.blueprint_engine import run_blueprint

    with pytest.raises(ValueError):
        await run_blueprint("bp_inexistente")
