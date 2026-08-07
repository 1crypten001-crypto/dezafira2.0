"""
Testes do retry com backoff no ObscuraClient.

Roda (a partir de SniperVideoEngine):
    python -m pytest tests/ -q
"""
import time
from unittest.mock import patch

import pytest

from services.obscura_client import ObscuraClient
from services.obscura_service import ObscuraTelemetry


@pytest.fixture
def telemetry():
    t = ObscuraTelemetry(max_recent=20)
    t._db_enabled = False  # evita I/O de banco nos testes
    with patch("services.obscura_client.obscura_telemetry", t):
        yield t


@pytest.fixture
def client(telemetry):
    return ObscuraClient(agent="teste_retry")


def test_retry_2x_ate_sucesso(telemetry, client):
    """Bridge vazio nas 2 primeiras tentativas; 3a tentativa OK.
    Esperado: 2 retries com backoff (1.5s, 3.0s) e 1 log_call de sucesso."""
    with patch.object(client, "_fetch_via_bridge", side_effect=["", "", "<html>ok</html>"]), \
         patch.object(client, "_fallback_urllib", return_value=""), \
         patch.object(time, "sleep") as mock_sleep:
        html = client.fetch_html("https://example.com", timeout=5)

    assert html == "<html>ok</html>"
    s = telemetry.build_status()
    assert s["retries"] == 2
    assert s["ok_calls"] == 1 and s["fail_calls"] == 0
    assert s["by_agent"]["teste_retry"]["retries"] == 2
    sleeps = [c.args[0] for c in mock_sleep.call_args_list]
    assert sleeps == [1.5, 3.0]


def test_falha_total_3_tentativas(telemetry, client):
    """Bridge e fallback sempre vazios: 3 tentativas, 2 retries, 1 log_call de falha."""
    with patch.object(client, "_fetch_via_bridge", return_value=""), \
         patch.object(client, "_fallback_urllib", return_value=""), \
         patch.object(time, "sleep"):
        html = client.fetch_html("https://example.com", timeout=5)

    assert html == ""
    s = telemetry.build_status()
    assert s["retries"] == 2
    assert s["fail_calls"] == 1 and s["ok_calls"] == 0


def test_retry_apos_excecao_no_bridge(telemetry, client):
    """Bridge levanta excecao na 1a tentativa; 2a OK: 1 retry."""
    with patch.object(client, "_fetch_via_bridge", side_effect=[RuntimeError("timeout"), "<html>ok</html>"]), \
         patch.object(time, "sleep"):
        html = client.fetch_html("https://example.com", timeout=5)

    assert html == "<html>ok</html>"
    s = telemetry.build_status()
    assert s["retries"] == 1
    assert s["ok_calls"] == 1 and s["fail_calls"] == 0


def test_fetch_markdown_tambem_retenta(telemetry, client):
    """fetch_markdown também re-tenta e conta retry."""
    with patch.object(client, "_fetch_markdown_via_bridge", side_effect=["", "## titulo"]), \
         patch.object(client, "_fallback_urllib", return_value=""), \
         patch.object(time, "sleep"):
        md = client.fetch_markdown("https://example.com", timeout=5)

    assert md == "## titulo"
    s = telemetry.build_status()
    assert s["retries"] == 1
    assert s["ok_calls"] == 1


def test_obscura_desabilitado_ignora_bridge(telemetry, client):
    """OBSCURA_ENABLED=false: bridge nunca é chamado, usa fallback direto, 0 retries."""
    with patch("services.obscura_client._obscura_enabled", return_value=False), \
         patch.object(client, "_fallback_urllib", return_value="html"), \
         patch.object(client, "_fetch_via_bridge", side_effect=AssertionError("bridge nao devia rodar")) as mb, \
         patch.object(time, "sleep"):
        html = client.fetch_html("https://example.com", timeout=5)

    assert html == "html"
    mb.assert_not_called()
    s = telemetry.build_status()
    assert s["ok_calls"] == 1 and s["retries"] == 0
