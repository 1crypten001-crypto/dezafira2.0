import pytest
import asyncio
from modules.hermes_orchestrator import HermesOrchestrator

@pytest.mark.asyncio
async def test_hermes_orchestrator_initialization():
    orchestrator = HermesOrchestrator("test_sess_001")
    assert orchestrator.session_id == "test_sess_001"
    assert orchestrator.state["current_phase"] == "IDLE"
    assert "miniapp" in orchestrator.state["pipeline_status"]

@pytest.mark.asyncio
async def test_hermes_pipeline_execution():
    orchestrator = HermesOrchestrator("test_sess_002")
    
    events = []
    orchestrator.register_callback(lambda evt: events.append(evt))
    
    result = await orchestrator.run_pipeline("Criar Oferta de IA para Vendas")
    
    assert result["current_phase"] == "COMPLETED"
    assert "copy" in result["deliverables"]
    assert "ebook" in result["deliverables"]
    assert "course" in result["deliverables"]
    assert "miniapp" in result["deliverables"]
    assert "funnel" in result["deliverables"]
    assert "ads" in result["deliverables"]
    assert len(events) > 5

@pytest.mark.asyncio
async def test_hermes_deepseek_fallback():
    orchestrator = HermesOrchestrator("test_sess_003")
    res = await orchestrator.call_deepseek_llm("Teste de Prompt")
    assert "Conteúdo otimizado" in res or len(res) > 5
