"""Testes dos contadores via (bridge/fallback) por agente na telemetria.

O painel usa esses contadores para desenhar a barra ⚡bridge/🟡fallback de
cada agente e o resumo do dashboard.
"""
from services.obscura_service import ObscuraTelemetry


def _fresh_telemetry():
    t = ObscuraTelemetry(max_recent=50)
    t._db_enabled = False
    return t


def test_via_counters_por_agente():
    t = _fresh_telemetry()
    t.log_call("seu_youtube", "https://youtube.com/results?q=x", True, 900, via="bridge")
    t.log_call("seu_youtube", "https://youtube.com/results?q=x", True, 50, via="bridge")
    t.log_call("seu_youtube", "https://youtube.com/results?q=x", True, 120, via="fallback")
    t.log_call("joaquim", "https://reddit.com/r/x", False, 60, via="")

    st = t.build_status()
    yt = st["by_agent"]["seu_youtube"]
    assert yt["via_bridge"] == 2
    assert yt["via_fallback"] == 1
    assert yt["total"] == 3
    jq = st["by_agent"]["joaquim"]
    assert jq["via_bridge"] == 0
    assert jq["via_fallback"] == 0


def test_via_fallback_sem_chamada_bridge():
    t = _fresh_telemetry()
    t.log_call("keyword_miner_serp", "https://google.com/search?q=x", True, 300, via="fallback")
    st = t.build_status()
    ag = st["by_agent"]["keyword_miner_serp"]
    assert ag["via_bridge"] == 0
    assert ag["via_fallback"] == 1


def test_recent_calls_levam_via():
    t = _fresh_telemetry()
    t.log_call("seu_reddit", "https://google.com/search?q=x", True, 80, via="bridge")
    t.log_call("seu_reddit", "https://google.com/search?q=x", True, 90, via="fallback")
    recent = t.build_status()["recent_calls"]
    vias = [c["via"] for c in recent]
    assert vias == ["bridge", "fallback"]
