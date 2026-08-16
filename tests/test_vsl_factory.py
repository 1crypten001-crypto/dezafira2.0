"""Testes do VSL Factory — geração de roteiro com fallback determinístico."""

import json
import pytest

from modules.vsl_factory import fallback_vsl, generate_vsl_content


@pytest.mark.asyncio
async def test_fallback_deterministico_gera_script_e_headlines():
    """Sem LLM → fallback nunca quebra e preenche script + 3 headlines."""
    res = fallback_vsl("Curso de Vendas", "Vendas & Marketing", "acesso vitalício")
    assert res["script"]
    assert "Curso de Vendas" in res["script"]
    assert res["headline_a"] and res["headline_b"] and res["headline_c"]
    assert "Vendas & Marketing" in res["headline_a"]


@pytest.mark.asyncio
async def test_generate_vsl_content_usa_llm_quando_disponivel(monkeypatch):
    """LLM responde JSON → conteúdo usado (script + headlines)."""

    async def fake_query_llm(messages, **kw):
        return json.dumps({
            "script": "Abra com a dor. Promessa. Oferta. Urgência. CTA: https://x.com",
            "headline_a": "A", "headline_b": "B", "headline_c": "C",
        })

    monkeypatch.setattr("agents.llm.query_llm", fake_query_llm)
    res = await generate_vsl_content("Título", "Nicho", "Oferta", "Público", "https://cta")
    assert res["script"].startswith("Abra com a dor")
    assert res["headline_a"] == "A"
    assert res["headline_c"] == "C"


@pytest.mark.asyncio
async def test_generate_vsl_content_fallback_em_erro_ou_json_invalido(monkeypatch):
    """LLM falha ou retorna lixo → fallback determinístico (nunca levanta)."""

    async def failing_llm(messages, **kw):
        return "[[ERRO]] todos os LLMs falharam"

    monkeypatch.setattr("agents.llm.query_llm", failing_llm)
    res = await generate_vsl_content("Título", "Nicho")
    assert res["script"]
    assert res["headline_a"]

    async def garbage_llm(messages, **kw):
        return "isso não é json"

    monkeypatch.setattr("agents.llm.query_llm", garbage_llm)
    res2 = await generate_vsl_content("Título", "Nicho")
    assert res2["script"]
    assert res2["headline_a"]


@pytest.mark.asyncio
async def test_create_vsl_persiste_registro(monkeypatch):
    """create_vsl gera conteúdo e salva via create_db_vsl_video."""
    from modules.vsl_factory import create_vsl

    captured = {}

    async def fake_query_llm(messages, **kw):
        return json.dumps({"script": "S", "headline_a": "A", "headline_b": "B", "headline_c": "C"})

    monkeypatch.setattr("agents.llm.query_llm", fake_query_llm)

    def fake_create_db_vsl_video(**kw):
        captured.update(kw)
        return {"id": "vsl_test1", "title": kw["title"], "script": kw["script"]}

    monkeypatch.setattr("modules.database.create_db_vsl_video", fake_create_db_vsl_video)

    res = await create_vsl("Curso X", "Nicho", video_url="https://v", thumbnail_url="https://t",
                           offer_description="Oferta", target_audience="Iniciantes", cta_url="https://c")
    assert res["id"] == "vsl_test1"
    assert captured["script"] == "S"
    assert captured["offer_description"] == "Oferta"
    assert captured["cta_url"] == "https://c"
