"""
Testes da telemetria das fontes de dores: PAA/SERP (keyword_miner_serp)
e Reddit (seu_reddit). O ObscuraBridge é mockado — nada de rede real.

Roda (a partir de SniperVideoEngine):
    python -m pytest tests/ -q
"""
import asyncio
from unittest.mock import patch

import pytest

from modules.blog_pipeline import get_reddit_questions
from services.obscura_bridge import get_serp_with_fallback
from services.obscura_service import ObscuraTelemetry

# Atalho: os dois patches usados em todos os testes
BRIDGE_PATCH = "services.obscura_bridge.ObscuraBridge"
TELEMETRY_PATCH = "services.obscura_service.obscura_telemetry"


class FakeBridge:
    """Substituto de ObscuraBridge com comportamento configurável."""

    def __init__(self, connected=True, serp_data=None, js_result=None):
        self._connected = connected
        self._serp_data = serp_data or {}
        self._js_result = js_result or ""

    async def connect(self):
        return self._connected

    async def disconnect(self):
        pass

    async def get_serp_data(self, keyword, lang):
        return self._serp_data

    async def navigate_and_get_html(self, url):
        pass

    async def execute_js(self, code):
        return self._js_result


@pytest.fixture
def telemetry():
    t = ObscuraTelemetry(max_recent=20)
    t._db_enabled = False
    return t


# ─── PAA / SERP (keyword_miner_serp) ────────────────────────────────────────

def test_serp_telemetry_ok(telemetry):
    fake = FakeBridge(connected=True, serp_data={
        "source": "obscura",
        "urls": ["https://site.com"],
        "people_also_ask": ["pergunta 1", "pergunta 2"],
    })
    with patch(BRIDGE_PATCH, return_value=fake), \
         patch(TELEMETRY_PATCH, telemetry):
        data = asyncio.run(get_serp_with_fallback("dieta", "pt"))

    assert data.get("source") == "obscura"
    s = telemetry.build_status()
    assert s["by_agent"]["keyword_miner_serp"]["ok"] == 1
    assert s["recent_calls"][0]["agent"] == "keyword_miner_serp"
    assert "google.com/search" in s["recent_calls"][0]["url"]


def test_serp_telemetry_falha_sem_engine(telemetry):
    fake = FakeBridge(connected=False)
    with patch(BRIDGE_PATCH, return_value=fake), \
         patch(TELEMETRY_PATCH, telemetry):
        data = asyncio.run(get_serp_with_fallback("dieta", "pt"))

    assert data.get("source") == "regex_fallback"
    s = telemetry.build_status()
    assert s["by_agent"]["keyword_miner_serp"]["fail"] == 1
    assert "nao conectado" in s["recent_calls"][0]["error"]


# ─── Reddit (seu_reddit) ────────────────────────────────────────────────────

def test_reddit_telemetry_ok(telemetry):
    fake = FakeBridge(connected=True, js_result='["como comecar", "vale a pena?"]')
    with patch(BRIDGE_PATCH, return_value=fake), \
         patch(TELEMETRY_PATCH, telemetry):
        questions = asyncio.run(get_reddit_questions("dieta", "pt"))

    assert questions == ["como comecar", "vale a pena?"]
    s = telemetry.build_status()
    assert s["by_agent"]["seu_reddit"]["ok"] == 1
    assert s["recent_calls"][0]["agent"] == "seu_reddit"
    assert "reddit" in s["recent_calls"][0]["url"]


def test_reddit_telemetry_falha_usar_fallback_generico(telemetry):
    fake = FakeBridge(connected=False)
    with patch(BRIDGE_PATCH, return_value=fake), \
         patch(TELEMETRY_PATCH, telemetry):
        questions = asyncio.run(get_reddit_questions("dieta", "pt"))

    # Sem motor, volta para a lista generica de 10 perguntas
    assert len(questions) == 10
    s = telemetry.build_status()
    assert s["by_agent"]["seu_reddit"]["fail"] == 1
