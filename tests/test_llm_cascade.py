"""Cascata do LLM — Agnes AI (agnes-2.5-flash) é o PROVEDOR 1 (IA oficial).

Sem tocar na API real: mocka os helpers HTTP e verifica a ORDEM da cascata
(Agnes antes de OpenRouter) e o fallback quando a Agnes falha.
"""
import pytest

from agents import llm


@pytest.mark.asyncio
async def test_query_llm_usa_agnes_primeiro(monkeypatch):
    """Com AGNES_API_KEY setada, a Agnes responde antes de qualquer outro."""
    monkeypatch.setenv("AGNES_API_KEY", "cpk-teste")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    calls = []

    async def fake_agnes(key, model, messages, temp, max_tok):
        calls.append(("agnes", model))
        return "Resposta da Agnes"

    async def fake_openrouter(key, model, messages, temp, max_tok):
        calls.append(("openrouter", model))
        return "Resposta do OpenRouter"

    monkeypatch.setattr(llm, "_call_agnes", fake_agnes)
    monkeypatch.setattr(llm, "_call_openrouter", fake_openrouter)

    out = await llm.query_llm([{"role": "user", "content": "oi"}])

    assert out == "Resposta da Agnes"
    assert calls == [("agnes", "agnes-2.5-flash")]


@pytest.mark.asyncio
async def test_query_llm_cai_para_openrouter_quando_agnes_falha(monkeypatch):
    """Agnes falha (exceção) → cascata segue para OpenRouter."""
    monkeypatch.setenv("AGNES_API_KEY", "cpk-teste")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-teste")

    async def fake_agnes(key, model, messages, temp, max_tok):
        raise RuntimeError("Agnes fora do ar")

    async def fake_openrouter(key, model, messages, temp, max_tok):
        return "Resposta do OpenRouter"

    monkeypatch.setattr(llm, "_call_agnes", fake_agnes)
    monkeypatch.setattr(llm, "_call_openrouter", fake_openrouter)

    out = await llm.query_llm([{"role": "user", "content": "oi"}])

    assert out == "Resposta do OpenRouter"


@pytest.mark.asyncio
async def test_query_llm_sem_chave_agnes_pula_provedor(monkeypatch):
    """Sem AGNES_API_KEY, a Agnes não é chamada (vai direto ao OpenRouter)."""
    monkeypatch.delenv("AGNES_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-teste")
    calls = []

    async def fake_agnes(key, model, messages, temp, max_tok):
        calls.append("agnes")
        return "x"

    async def fake_openrouter(key, model, messages, temp, max_tok):
        calls.append("openrouter")
        return "y"

    monkeypatch.setattr(llm, "_call_agnes", fake_agnes)
    monkeypatch.setattr(llm, "_call_openrouter", fake_openrouter)

    out = await llm.query_llm([{"role": "user", "content": "oi"}])

    assert out == "y"
    assert calls == ["openrouter"]
