"""Testes do Blueprint Engine (F2) — estágios com LLM/pipelines/imagens mockados."""

import json
import pytest
from unittest.mock import AsyncMock

from modules.database import create_db_blueprint, get_db_blueprint, delete_db_blueprint


@pytest.fixture
def bp():
    b = create_db_blueprint(
        name="Teste Engine",
        theme="Guia de IA para Iniciantes",
        niche="Tecnologia & IA",
        price_cents=1990,
        formats=["ebook", "blog"],
        config={
            "artigos": 2,
            "funil": {
                "upsell": {"name": "Mentoria IA", "price_cents": 990, "slug": ""},
                "downsell": {"name": "Guia Rápido", "price_cents": 490, "slug": ""},
            },
        },
    )
    yield b
    delete_db_blueprint(b["id"])


# ── Fundação ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fundacao_usa_llm_com_fallback_deterministico(bp, monkeypatch):
    """LLM retorna JSON → fundação usa os dados; sem LLM → fallback determinístico."""
    from modules.blueprint_engine import _stage_fundacao

    async def fake_query_llm(messages, **kw):
        return json.dumps({
            "name": "Guia IA Pro", "slug": "guia-ia-pro",
            "description": "Descrição gerada", "pitch": "Pitch de venda",
            "cta_primary": "Comprar agora", "cta_secondary": "Ver",
            "faq": [{"q": "Como acesso?", "a": "Na hora."}],
        })

    monkeypatch.setattr("agents.llm.query_llm", fake_query_llm)
    res = await _stage_fundacao(bp)
    assert res["name"] == "Guia IA Pro"
    assert res["slug"] == "guia-ia-pro"
    assert res["faq"][0]["q"] == "Como acesso?"

    # Fallback determinístico (LLM falha → prefixo de erro)
    async def failing_llm(messages, **kw):
        return "[[ERRO]] todos os LLMs falharam"

    monkeypatch.setattr("agents.llm.query_llm", failing_llm)
    res2 = await _stage_fundacao(bp)
    assert res2["name"] == bp["theme"]
    assert res2["slug"] == "guia-de-ia-para-iniciantes"
    assert res2["cta_primary"] == "Quero acesso agora"


# ── Conteúdo ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_conteudo_delega_pipelines_e_coleta_artifacts(bp, monkeypatch):
    from modules.blueprint_engine import _stage_conteudo

    async def fake_ebook(**kw):
        return {"book_id": "book_abc", "title": "Guia IA Pro", "cover_url": "/capa.png",
                "status": "completed", "error": ""}

    monkeypatch.setattr("modules.ebook_pipeline.run_ebook_macro_pipeline", AsyncMock(side_effect=fake_ebook))
    monkeypatch.setattr("modules.blog_pipeline.run_blog_macro_pipeline", AsyncMock(return_value={
        "channel_id": "ch_1", "status": "completed", "articles_generated": 2, "banner_url": ""
    }))

    res = await _stage_conteudo(bp["id"], bp, {"name": "Guia IA Pro", "slug": "guia-ia-pro"})
    formats = [a["format"] for a in res["artifacts"]]
    assert "ebook" in formats and "blog" in formats
    ebook = next(a for a in res["artifacts"] if a["format"] == "ebook")
    assert ebook["id"] == "book_abc"
    assert ebook["status"] == "completed"
    assert ebook["external_link"].endswith("/api/v1/ebooks/book_abc")


# ── Assets ───────────────────────────────────────────────────────────────────

class _FakeImageAgent:
    def __init__(self):
        self.last_provider = None
        self.last_url = None

    async def generate_image_for_post(self, **kw):
        return {
            "image_url": "https://img.agnes/hero.png",
            "provider": "agnes",
            "credit": "Agnes",
            "expanded_prompt": "super prompt hiper detalhado de teste",
        }


@pytest.mark.asyncio
async def test_assets_geram_slots_com_super_prompt(bp, monkeypatch):
    from modules.blueprint_engine import _stage_assets

    monkeypatch.setattr("modules.image_factory.ImageGeneratorAgent", _FakeImageAgent)

    async def fake_agnes_cover(bp_id, slot, style_id="moderno"):
        return {"slot": slot, "url": "/outputs/agnes/prod-fake.png", "super_prompt": "agnes",
                "provider": "agnes-studio", "source": "ai", "width": 1024, "height": 1024,
                "agnes_style": style_id}

    monkeypatch.setattr("modules.blueprint_engine.generate_agnes_cover_asset", fake_agnes_cover)

    content = {
        "fundacao": {"name": "Guia IA Pro", "slug": "guia-ia-pro"},
        "conteudo": {
            "formats": ["ebook", "blog"],
            "artifacts": [
                {"format": "blog", "slug": "post-1", "status": "completed", "articles_generated": 2},
            ],
        },
        "funil": {"upsell": {"name": "Mentoria IA"}, "downsell": {"name": "Guia Rápido"}},
    }
    res = await _stage_assets(bp["id"], bp, content)
    keys = [s["key"] for s in res["slots"]]
    assert "product_image" in keys
    assert "product_image_agnes" in keys
    assert "landing_hero" in keys
    assert "blog_banner_sidebar" in keys
    assert "post_cover_0" in keys and "post_cover_1" in keys
    assert "upsell_image" in keys and "downsell_image" in keys

    stored = get_db_blueprint(bp["id"])["assets"]
    assert stored["product_image"]["source"] == "ai"
    assert stored["product_image"]["provider"] == "agnes"
    assert stored["product_image_agnes"]["provider"] == "agnes-studio"
    assert stored["product_image"]["super_prompt"] == "super prompt hiper detalhado de teste"
    assert stored["product_image"]["width"] == 1024


# ── Landing ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_landing_monta_blocos_do_template(bp, monkeypatch):
    from modules.blueprint_engine import _stage_landing

    content = {
        "fundacao": {
            "name": "Guia IA Pro", "slug": "guia-ia-pro", "description": "Desc",
            "pitch": "Pitch", "cta_primary": "Comprar", "cta_secondary": "Ver",
            "faq": [{"q": "q1", "a": "a1"}],
        },
        "conteudo": {"artifacts": [{"format": "blog", "slug": "post-1"}]},
        "funil": {},
    }
    assets = {"landing_hero": {"url": "https://img/hero.png"}, "landing_offer": {"url": "https://img/offer.png"}}
    bp["assets"] = assets

    res = await _stage_landing(bp["id"], bp, content)
    types = [b["type"] for b in res["blocks"]]
    assert res["template"] == "dezafira"
    assert "hero" in types
    assert "product-showcase" in types
    assert "posts-grid" in types
    assert "faq" in types
    assert "cta" in types
    hero = next(b for b in res["blocks"] if b["type"] == "hero")
    assert hero["properties"]["title"] == "Guia IA Pro"


# ── Funil ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_funil_define_bump_upsell_downsell(bp):
    from modules.blueprint_engine import _stage_funil
    bp["config"] = {
        "funil": {
            "order_bump": {"title": "Impressão Premium", "price_cents": 500, "description": "Versão física"},
            "upsell": {"name": "Mentoria IA", "price_cents": 990},
            "downsell": {"name": "Guia Rápido", "price_cents": 490},
        }
    }
    res = await _stage_funil(bp)
    assert res["order_bump"]["title"] == "Impressão Premium"
    assert res["upsell"]["slug"] == "mentoria-ia"
    assert res["downsell"]["price_cents"] == 490


# ── Fluxo completo ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_blueprint_fluxo_completo_ate_review(bp, monkeypatch):
    from modules.blueprint_engine import run_blueprint

    async def fake_query_llm(messages, **kw):
        return json.dumps({"name": "Guia IA Pro", "slug": "guia-ia-pro",
                           "description": "D", "pitch": "P", "cta_primary": "C1",
                           "cta_secondary": "C2", "faq": [{"q": "q", "a": "a"}]})

    monkeypatch.setattr("agents.llm.query_llm", fake_query_llm)
    monkeypatch.setattr("modules.ebook_pipeline.run_ebook_macro_pipeline", AsyncMock(return_value={
        "book_id": "book_abc", "title": "Guia IA Pro", "cover_url": "", "status": "completed", "error": ""}))
    monkeypatch.setattr("modules.blog_pipeline.run_blog_macro_pipeline", AsyncMock(return_value={
        "channel_id": "ch_1", "status": "completed", "articles_generated": 2, "banner_url": ""}))
    monkeypatch.setattr("modules.image_factory.ImageGeneratorAgent", _FakeImageAgent)

    async def fake_agnes_cover(bp_id, slot, style_id="moderno"):
        return {"slot": slot, "url": "/outputs/agnes/prod-fake.png", "super_prompt": "agnes",
                "provider": "agnes-studio", "source": "ai", "width": 1024, "height": 1024,
                "agnes_style": style_id}

    monkeypatch.setattr("modules.blueprint_engine.generate_agnes_cover_asset", fake_agnes_cover)

    result = await run_blueprint(bp["id"])
    assert result["status"] == "review"

    stored = get_db_blueprint(bp["id"])
    assert stored["stage"] == "revisao"
    assert stored["content"]["fundacao"]["name"] == "Guia IA Pro"
    assert stored["content"]["conteudo"]["artifacts"][0]["format"] == "ebook"
    assert stored["assets"]["product_image"]["super_prompt"].startswith("super prompt")
    assert stored["assets"]["product_image_agnes"]["provider"] == "agnes-studio"
    assert stored["content"]["landing"]["blocks"][0]["type"] == "hero"


# ── Capa editorial Agnes Studio (asset) ─────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_agnes_cover_asset(bp, monkeypatch):
    """generate_agnes_cover_asset mapeia o slot → capa do studio, persiste o
    asset com provider agnes-studio + estilo usado (identidade em regeneração)."""
    from modules import agnes_studio as _agn
    from modules.blueprint_engine import generate_agnes_cover_asset
    from modules.database import update_db_blueprint

    update_db_blueprint(bp["id"], content={
        "fundacao": {"name": "Guia IA Pro", "description": "Desc"},
        "assets": {"slots": [{"key": "product_image", "label": "Capa do produto",
                               "width": 1024, "height": 1024, "prompt": "x"}]},
    })

    async def fake_product(self, **kwargs):
        return {"cover_url": "/outputs/agnes/prod-bp_0000.png", "width": 1024,
                "height": 1024, "design": {"style_id": kwargs.get("style_id")}}

    monkeypatch.setattr(_agn.AgnesStudio, "generate_product_cover", fake_product)

    res = await generate_agnes_cover_asset(bp["id"], "product_image", "elegante")
    assert res["provider"] == "agnes-studio"
    assert res["agnes_style"] == "elegante"
    persisted = get_db_blueprint(bp["id"])["assets"]["product_image"]
    assert persisted["url"] == "/outputs/agnes/prod-bp_0000.png"
    assert persisted["provider"] == "agnes-studio"

    # Estilo inválido → cai em moderno (nunca quebra)
    res2 = await generate_agnes_cover_asset(bp["id"], "product_image", "nao-existe")
    assert res2["agnes_style"] == "moderno"


@pytest.mark.asyncio
async def test_stage_assets_genera_agnes_only_slot(bp, monkeypatch):
    """O estágio de assets gera o slot agnes_only (product_image_agnes)
    automaticamente via generate_agnes_cover_asset, fora do lote paralelo."""
    from modules.blueprint_engine import _stage_assets
    from modules.database import update_db_blueprint

    content = {
        "fundacao": {"name": "Guia IA Pro", "description": "D", "slug": "guia"},
        "conteudo": {"formats": ["ebook"], "artifacts": []},
        "assets": {"slots": [
            {"key": "product_image", "label": "Capa do produto",
             "width": 1024, "height": 1024, "prompt": "p"},
            {"key": "product_image_agnes", "label": "Capa Agnes",
             "width": 1024, "height": 1024, "prompt": "p", "agnes_only": True},
        ]},
    }
    update_db_blueprint(bp["id"], content=content)

    captured = {}

    async def fake_agnes_cover(bp_id, slot, style_id="moderno"):
        captured["slot"] = slot
        captured["style"] = style_id
        return {"slot": slot, "url": "/outputs/agnes/prod-fake.png", "super_prompt": "agnes",
                "provider": "agnes-studio", "source": "ai", "width": 1024, "height": 1024,
                "agnes_style": style_id}

    monkeypatch.setattr("modules.blueprint_engine.generate_agnes_cover_asset", fake_agnes_cover)

    class _FakeImageAgent:
        async def generate_image_for_post(self, **kw):
            return {"image_url": "https://img/fake.png", "provider": "agnes",
                    "credit": "A", "expanded_prompt": "super prompt fake"}

    monkeypatch.setattr("modules.image_factory.ImageGeneratorAgent", _FakeImageAgent)

    info = await _stage_assets(bp["id"], bp, content)
    assert captured["slot"] == "product_image_agnes"
    assert captured["style"] == "moderno"
    stored = get_db_blueprint(bp["id"])["assets"]
    assert stored["product_image_agnes"]["provider"] == "agnes-studio"
    assert stored["product_image"]["provider"] == "agnes"
    # 4 slots gerados: product_image, product_image_agnes, landing_hero, landing_offer
    assert info["generated"] == 4


# ── Variantes (comparador) ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agnes_variants_e_apply(bp, monkeypatch):
    """generate_agnes_variants gera um arquivo por estilo (sem persistir) e
    apply_agnes_variant aplica a escolhida ao asset."""
    from modules import agnes_studio as _agn
    from modules.blueprint_engine import apply_agnes_variant, generate_agnes_variants
    from modules.database import update_db_blueprint

    update_db_blueprint(bp["id"], content={
        "fundacao": {"name": "Guia IA Pro", "description": "D"},
        "assets": {"slots": [{"key": "product_image", "label": "Capa do produto",
                               "width": 1024, "height": 1024, "prompt": "p"}]},
    })

    calls = []

    async def fake_product(self, **kwargs):
        st = kwargs.get("style_id")
        calls.append(st)
        return {"cover_url": f"/outputs/agnes/prod-{st}.png",
                "filename": f"prod-{st}_0000.png", "width": 1024, "height": 1024,
                "design": {"style_id": st}}

    monkeypatch.setattr(_agn.AgnesStudio, "generate_product_cover", fake_product)

    res = await generate_agnes_variants(bp["id"], "product_image", ["moderno", "elegante"])
    assert [v["style_id"] for v in res["variants"]] == ["moderno", "elegante"]
    assert calls == ["moderno", "elegante"]
    # Nada persistido ainda
    assert "product_image" not in (get_db_blueprint(bp["id"])["assets"] or {})

    # Aplica a variante escolhida (arquivo existe — mocka o isfile)
    monkeypatch.setattr("os.path.isfile", lambda p: True)
    applied = await apply_agnes_variant(bp["id"], "product_image",
                                        "prod-elegante_0000.png", "elegante")
    assert applied["agnes_style"] == "elegante"
    stored = get_db_blueprint(bp["id"])["assets"]["product_image"]
    assert stored["url"].endswith("prod-elegante_0000.png")
    assert stored["provider"] == "agnes-studio"


# ── Combo/pacote nativo (fase 2) ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_funil_combo_bundle_define_slug_e_desconto(bp):
    """Funil com bundle habilitado → definição do combo com slug determinístico
    ("{slug}-pacote") e desconto normalizado (0–90%)."""
    from modules.blueprint_engine import _stage_funil
    bp["content"] = {"fundacao": {"name": "Guia IA Pro", "slug": "guia-ia-pro"}}
    bp["config"] = {
        "funil": {
            "upsell": {"name": "Mentoria IA", "price_cents": 990},
            "downsell": {"name": "Guia Rápido", "price_cents": 490},
            "bundle": {"enabled": True, "discount_pct": 35, "include_upsell": True, "include_downsell": True},
        }
    }
    res = await _stage_funil(bp)
    assert res["bundle"]["enabled"] is True
    assert res["bundle"]["slug"] == "guia-ia-pro-pacote"
    assert res["bundle"]["discount_pct"] == 35
    assert res["bundle"]["include_upsell"] is True

    # Desconto fora da faixa → normalizado
    bp["config"]["funil"]["bundle"]["discount_pct"] = 150
    res2 = await _stage_funil(bp)
    assert res2["bundle"]["discount_pct"] == 90


@pytest.mark.asyncio
async def test_landing_combo_promove_o_pacote():
    """Combo habilitado → a landing aponta pro produto pacote (slug -pacote)
    com preço agregado com desconto."""
    from modules.landing_templates import build_landing_blocks

    content = {
        "fundacao": {"name": "Guia IA Pro", "slug": "guia-ia-pro", "pitch": "P",
                     "cta_primary": "Comprar", "cta_secondary": "Ver",
                     "description": "D", "faq": []},
        "funil": {
            "upsell": {"name": "Mentoria IA", "price_cents": 990},
            "downsell": {"name": "Guia Rápido", "price_cents": 490},
            "bundle": {"enabled": True, "slug": "guia-ia-pro-pacote",
                        "discount_pct": 30, "include_upsell": True, "include_downsell": True},
        },
    }
    config = {"price_cents": 1990}
    blocks = build_landing_blocks("dezafira", content, config, {})
    product = next(b for b in blocks if b["type"] == "product-showcase")
    # 1990 + 990 + 490 = 3470 → -30% = 2429
    assert product["properties"]["productSlug"] == "guia-ia-pro-pacote"
    assert product["properties"]["price"] == "R$ 24,29"
    cta = next(b for b in blocks if b["type"] == "cta")
    assert cta["properties"]["productSlug"] == "guia-ia-pro-pacote"
    assert cta["properties"]["buttonHref"] == "/product/guia-ia-pro-pacote"


@pytest.mark.asyncio
async def test_landing_vsl_usa_bloco_nativo_do_clube():
    """Blueprint com VSL (MP4 gerado) → a landing emite o bloco `vsl` com
    vslId/src/thumbnail/headline_a..c pro player do Clube (sem iframe YouTube)."""
    from modules.landing_templates import build_landing_blocks

    content = {
        "fundacao": {"name": "Curso X", "slug": "curso-x", "pitch": "P",
                     "description": "D", "cta_primary": "Comprar", "faq": []},
        "funil": {},
        "vsl": {"vsl_id": 42, "video_url": "https://cdn/vsl.mp4",
                 "thumbnail_url": "https://cdn/cover.png",
                 "headline_a": "Headline A", "headline_b": "Headline B",
                 "headline_c": "Headline C"},
    }
    config = {"price_cents": 1990}
    blocks = build_landing_blocks("dezafira", content, config, {})
    types = [b["type"] for b in blocks]
    assert "vsl" in types and "video" not in types
    vsl = next(b for b in blocks if b["type"] == "vsl")
    props = vsl["properties"]
    assert props["vslId"] == 42
    assert props["src"] == "https://cdn/vsl.mp4"
    assert props["thumbnail"] == "https://cdn/cover.png"
    assert props["headline_a"] == "Headline A"
    assert props["headline_c"] == "Headline C"


@pytest.mark.asyncio
async def test_landing_vsl_sem_mp4_mantem_iframe_youtube():
    """VSL sem vídeo renderizado (só roteiro) → mantém o bloco `video` com
    iframe do YouTube quando config.youtube_video_url existe."""
    from modules.landing_templates import build_landing_blocks

    content = {
        "fundacao": {"name": "Curso X", "slug": "curso-x", "pitch": "P",
                     "description": "D", "cta_primary": "Comprar", "faq": []},
        "funil": {},
        "vsl": {"vsl_id": 7, "video_url": "", "headline_a": "H"},
    }
    config = {"price_cents": 1990,
              "youtube_video_url": "https://www.youtube.com/watch?v=abc123"}
    blocks = build_landing_blocks("dezafira", content, config, {})
    types = [b["type"] for b in blocks]
    assert "video" in types and "vsl" not in types
    video = next(b for b in blocks if b["type"] == "video")
    assert video["properties"]["src"] == "https://www.youtube.com/watch?v=abc123"


@pytest.mark.asyncio
async def test_publish_cria_bundle_depois_do_produto_principal(bp, monkeypatch):
    """Publish com bundle habilitado → publica o combo (bundle_items) depois do
    produto principal e registra no publish_log + content.funil.bundle."""
    from modules.blueprint_engine import publish_blueprint
    from modules.database import update_db_blueprint

    update_db_blueprint(bp["id"], content={
        "fundacao": {"name": "Guia IA Pro", "slug": "guia-ia-pro", "description": "D"},
        "conteudo": {"artifacts": []},
        "funil": {
            "upsell": {"name": "Mentoria IA", "price_cents": 990},
            "downsell": {"name": "Guia Rápido", "price_cents": 490},
            "bundle": {"enabled": True, "discount_pct": 30,
                        "include_upsell": True, "include_downsell": True,
                        "slug": "guia-ia-pro-pacote"},
        },
        "landing": {"blocks": []},
    })
    update_db_blueprint(bp["id"], assets={"product_image": {"url": "https://img/x.png"}})

    calls = []

    async def fake_import_product(payload):
        calls.append(payload)
        if payload.get("bundle_items"):
            return {"success": True, "product_id": 777, "slug": "guia-ia-pro-pacote"}
        if payload.get("name") == "Mentoria IA":
            return {"success": True, "product_id": 101}
        if payload.get("name") == "Guia Rápido":
            return {"success": True, "product_id": 102}
        return {"success": True, "product_id": 100, "slug": "guia-ia-pro"}

    async def fake_sync_blog(payload):
        return {"success": True, "summary": {"posts_inserted": 0, "ads_created": 0}}

    async def fake_cli_landing(payload):
        return {"success": True, "slug": "guia-ia-pro", "public_url": "/p/guia-ia-pro"}

    async def fake_member_course(payload):
        return {"success": True, "course_id": 1}

    monkeypatch.setattr("modules.clube_bridge.bridge_import_product", fake_import_product)
    monkeypatch.setattr("modules.clube_bridge.bridge_sync_blog", fake_sync_blog)
    monkeypatch.setattr("modules.clube_bridge.cli_create_landing", fake_cli_landing)
    monkeypatch.setattr("modules.clube_bridge.bridge_member_course", fake_member_course)

    res = await publish_blueprint(bp["id"])
    assert res["status"] == "published"
    bundle_call = next(c for c in calls if c.get("bundle_items"))
    assert bundle_call["bundle_items"] == [100, 101, 102]
    assert bundle_call["price_cents"] == int(3470 * 0.7)  # 2429
    assert bundle_call["slug"] == "guia-ia-pro-pacote"
    stored = get_db_blueprint(bp["id"])
    assert stored["publish_log"]["bundle"]["status"] == "ok"
    assert stored["content"]["funil"]["bundle"]["product_id"] == 777


# ── Templates variados ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_template_dark_sales_constroi_blocos_com_urgencia():
    from modules.landing_templates import build_landing_blocks
    content = {"fundacao": {"name": "Curso X", "slug": "curso-x", "pitch": "P",
                            "description": "D", "cta_primary": "Garantir", "faq": []},
               "funil": {}}
    config = {"price_cents": 1990, "brand_kit": {"colors": {
        "bg": "#09090b", "accent": "#f59e0b"}}}
    blocks = build_landing_blocks("dark-sales", content, config, {})
    types = [b["type"] for b in blocks]
    assert "hero" in types and "testimonial" in types and "product-showcase" in types
    hero = next(b for b in blocks if b["type"] == "hero")
    assert hero["properties"]["badge"] == "Últimas vagas"
    assert hero["styles"]["backgroundColor"] == "#09090b"
    product = next(b for b in blocks if b["type"] == "product-showcase")
    assert product["properties"]["compareAtPrice"] == "R$ 31,84"


@pytest.mark.asyncio
async def test_template_clean_soft_usa_cores_claras():
    from modules.landing_templates import build_landing_blocks
    content = {"fundacao": {"name": "Curso X", "slug": "curso-x", "pitch": "P",
                            "description": "D", "cta_primary": "Quero", "faq": []},
               "conteudo": {"artifacts": [{"format": "blog", "slug": "post-1"}]},
               "funil": {}}
    config = {"price_cents": 1990, "brand_kit": {"colors": {
        "bg": "#f8fafc", "accent": "#0ea5e9"}}}
    blocks = build_landing_blocks("clean-soft", content, config, {})
    types = [b["type"] for b in blocks]
    assert "hero" in types and "product-showcase" in types and "posts-grid" in types
    hero = next(b for b in blocks if b["type"] == "hero")
    assert hero["styles"]["backgroundColor"] == "#f8fafc"
    assert hero["properties"]["eyebrow"] == "CONTEÚDO CURADO"


# ── Histórico e diff de assets ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_asset_historico_empilha_versoes_e_restaura(bp, monkeypatch):
    """Regenerar/upload empilham a versão anterior no histórico e
    restore_asset_version reverte (a atual volta pro histórico)."""
    from modules import agnes_studio as _agn
    from modules.blueprint_engine import generate_agnes_cover_asset, restore_asset_version
    from modules.database import update_db_blueprint

    update_db_blueprint(bp["id"], content={
        "fundacao": {"name": "Guia IA Pro", "description": "D"},
        "assets": {"slots": [{"key": "product_image", "label": "Capa do produto",
                               "width": 1024, "height": 1024, "prompt": "p"}]},
    })

    urls = iter(["/outputs/agnes/v1.png", "/outputs/agnes/v2.png", "/outputs/agnes/v3.png"])

    async def fake_product(self, **kwargs):
        return {"cover_url": next(urls), "width": 1024, "height": 1024,
                "design": {"style_id": kwargs.get("style_id")}}

    monkeypatch.setattr(_agn.AgnesStudio, "generate_product_cover", fake_product)

    await generate_agnes_cover_asset(bp["id"], "product_image", "moderno")
    await generate_agnes_cover_asset(bp["id"], "product_image", "elegante")
    await generate_agnes_cover_asset(bp["id"], "product_image", "tech")

    stored = get_db_blueprint(bp["id"])["assets"]["product_image"]
    assert stored["url"] == "/outputs/agnes/v3.png"
    hist = stored["history"]
    assert len(hist) == 2
    assert hist[0]["url"] == "/outputs/agnes/v1.png"
    assert hist[1]["url"] == "/outputs/agnes/v2.png"
    assert hist[1]["agnes_style"] == "elegante"

    # Restaura a v2 → vira a atual; v3 volta pro histórico
    restored = await restore_asset_version(bp["id"], "product_image", 1)
    assert restored["url"] == "/outputs/agnes/v2.png"
    stored2 = get_db_blueprint(bp["id"])["assets"]["product_image"]
    assert stored2["url"] == "/outputs/agnes/v2.png"
    assert stored2["history"][0]["url"] == "/outputs/agnes/v3.png"

    # Índice inválido → ValueError
    with pytest.raises(ValueError):
        await restore_asset_version(bp["id"], "product_image", 99)


# ── VSL no blueprint ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stage_vsl_gera_roteiro_e_persiste(bp, monkeypatch):
    """config.vsl.enabled → _stage_vsl gera script + headlines com thumbnail
    da capa do produto e persiste content.vsl."""
    from modules.blueprint_engine import _stage_vsl
    from modules.database import update_db_blueprint

    update_db_blueprint(bp["id"], content={
        "fundacao": {"name": "Guia IA Pro", "slug": "guia-ia-pro", "description": "Oferta"},
    })
    bp["config"] = {"vsl": {"enabled": True}}

    async def fake_create_vsl(**kw):
        return {"id": "vsl_abc123", "title": kw["title"], "script": "Roteiro completo",
                "headline_a": "A", "headline_b": "B", "headline_c": "C",
                "thumbnail_url": kw["thumbnail_url"], "video_url": ""}

    monkeypatch.setattr("modules.vsl_factory.create_vsl", fake_create_vsl)

    assets = {"product_image_agnes": {"url": "/outputs/agnes/capa.png"}}
    res = await _stage_vsl(bp, {}, assets)
    assert res["generated"] is True
    assert res["vsl_id"] == "vsl_abc123"
    assert res["script"] == "Roteiro completo"
    assert res["thumbnail_url"] == "/outputs/agnes/capa.png"

    # VSL desabilitado → nada (o run flow só chama se enabled)
    bp["config"] = {"vsl": {"enabled": False}}


# ── Landing com brand kit ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_landing_aplica_brand_kit_nos_blocos():
    """Os blocos da landing usam as cores do brand kit (hero/cta/buttons)."""
    from modules.landing_templates import build_landing_blocks

    content = {"fundacao": {"name": "Curso X", "slug": "curso-x", "pitch": "P",
                            "cta_primary": "Comprar", "cta_secondary": "Ver", "faq": []}}
    config = {"price_cents": 1990, "brand_kit": {"colors": {
        "bg": "#101010", "bg2": "#202020", "accent": "#ffcc00",
        "text": "#ffffff", "muted": "#999999"}}}
    blocks = build_landing_blocks("dezafira", content, config, {})

    hero = next(b for b in blocks if b["type"] == "hero")
    assert hero["styles"]["backgroundColor"] == "#101010"
    assert hero["styles"]["textColor"] == "#ffffff"
    product = next(b for b in blocks if b["type"] == "product-showcase")
    assert product["styles"]["backgroundColor"] == "#202020"
    cta = next(b for b in blocks if b["type"] == "cta")
    assert cta["properties"]["buttonBg"] == "#ffcc00"
    assert cta["properties"]["buttonColor"] == "#101010"


# ── Vídeo promocional (config.video.enabled) ─────────────────────────────────

@pytest.mark.asyncio
async def test_stage_promo_video_gera_slot_video(bp, monkeypatch):
    """config.video.enabled → _stage_promo_video gera o clipe (mockado),
    grava assets.promo_video (video=True) e adiciona o slot na UI."""
    from modules.blueprint_engine import _stage_promo_video
    from modules.database import update_db_blueprint, get_db_blueprint

    # PNG dummy real no disco (o frame local precisa existir p/ virar base64)
    import os as _os
    frame_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                               "outputs", "agnes", "capa_test_promo.png")
    _os.makedirs(_os.path.dirname(frame_path), exist_ok=True)
    with open(frame_path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)

    update_db_blueprint(bp["id"], content={
        "fundacao": {"name": "Guia IA Pro", "slug": "guia-ia-pro"},
        "assets": {"slots": [{"key": "product_image", "label": "Capa", "width": 1024, "height": 1024}]},
    }, assets={
        "product_image_agnes": {"url": "/outputs/agnes/capa_test_promo.png", "provider": "agnes-studio"},
    })
    bp = get_db_blueprint(bp["id"])
    bp["config"] = {"video": {"enabled": True}}

    async def fake_gen(prompt, image=None, **kw):
        assert image and image.startswith("data:image/png;base64,")  # frame local → base64
        return {"status": "completed", "url": "https://ex.com/video.mp4", "video_id": "task_v1",
                "raw": {"seconds": "5.0"}}

    async def fake_download(url, dest):
        return "outputs/vsl/bp_promo.mp4"

    monkeypatch.setattr("modules.agnes_video.agnes_video_generate_and_wait", fake_gen)
    monkeypatch.setattr("modules.agnes_video.agnes_download_video", fake_download)

    content = dict(bp.get("content") or {})
    assets = dict(bp.get("assets") or {})
    res = await _stage_promo_video(bp, content, assets)

    assert res["generated"] is True
    assert res["url"].startswith("/outputs/vsl/")

    saved = get_db_blueprint(bp["id"])
    promo = (saved.get("assets") or {}).get("promo_video") or {}
    assert promo.get("video") is True
    assert promo.get("provider") == "agnes-video"
    keys = [s.get("key") for s in ((saved.get("content") or {}).get("assets", {}).get("slots") or [])]
    assert "promo_video" in keys
    # o dict de vídeo volta no retorno (o run_blueprint grava content.video)
    assert res.get("url") and res.get("remote_url") == "https://ex.com/video.mp4"

    if _os.path.isfile(frame_path):
        _os.remove(frame_path)


@pytest.mark.asyncio
async def test_stage_promo_video_falha_sem_quebrar(bp, monkeypatch):
    """Falha na geração de vídeo → retorna generated=False sem exceção."""
    from modules.blueprint_engine import _stage_promo_video

    bp["config"] = {"video": {"enabled": True}}
    content = {"fundacao": {"name": "X", "slug": "x"}}
    assets = {"product_image_agnes": {"url": "/outputs/agnes/capa.png"}}

    async def fake_gen(prompt, image=None, **kw):
        return {"error": "video queue is full"}

    monkeypatch.setattr("modules.agnes_video.agnes_video_generate_and_wait", fake_gen)

    res = await _stage_promo_video(bp, content, assets)
    assert res["generated"] is False
    assert "error" in res
