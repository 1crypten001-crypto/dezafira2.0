"""Testes da configuração de graça do healthcheck (obscura_health).

Cobre: default 300s, leitura do env, override em runtime, persistência no .env
(preservando outras linhas), criação do .env se faltar e erro em valor inválido.
"""
import os
import pytest

from services import obscura_health as h


@pytest.fixture(autouse=True)
def reset_runtime():
    """Cada teste começa com override zerado (e restaura ao final)."""
    h._RUNTIME_GRACE["seconds"] = None
    yield
    h._RUNTIME_GRACE["seconds"] = None


def test_default_300_sem_env(monkeypatch):
    monkeypatch.delenv("OBSCURA_HEALTH_GRACE", raising=False)
    assert h.get_grace_seconds() == 300.0
    assert h.get_grace_source() == "env"


def test_le_env_quando_sem_override(monkeypatch):
    monkeypatch.setenv("OBSCURA_HEALTH_GRACE", "120")
    assert h.get_grace_seconds() == 120.0
    assert h.get_grace_source() == "env"


def test_override_runtime_vence_env(monkeypatch):
    monkeypatch.setenv("OBSCURA_HEALTH_GRACE", "120")
    monkeypatch.setattr(h, "_persist_env_grace", lambda seconds: True)
    result = h.set_grace_seconds(60)
    assert result["grace_s"] == 60
    assert h.get_grace_seconds() == 60.0
    assert h.get_grace_source() == "runtime"


def test_persist_no_env_preserva_outras_linhas(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("OBSCURA_ENABLED=false\nSOME_KEY=1\n", encoding="utf-8")
    monkeypatch.setattr(h, "_ENV_PATH", str(env_file))
    result = h.set_grace_seconds(240)
    assert result["persisted"] is True
    content = env_file.read_text(encoding="utf-8")
    assert "OBSCURA_HEALTH_GRACE=240" in content
    assert "OBSCURA_ENABLED=false" in content  # linha original preservada
    assert "SOME_KEY=1" in content


def test_persist_cria_env_se_faltar(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(h, "_ENV_PATH", str(env_file))
    result = h.set_grace_seconds(30)
    assert result["persisted"] is True
    content = env_file.read_text(encoding="utf-8")
    assert "OBSCURA_HEALTH_GRACE=30" in content


def test_grace_invalida_sobe_valueerror():
    with pytest.raises(ValueError):
        h.set_grace_seconds("abc")
    with pytest.raises(ValueError):
        h.set_grace_seconds(None)
