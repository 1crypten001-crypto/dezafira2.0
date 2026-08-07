"""
================================================================================
DEZAFIRA — Chainlit UI para Hermes Agent + DeepSeek (Chat Conversacional)
================================================================================
Interface conversacional limpa em Chainlit integrada ao Hermes Agent + DeepSeek LLM.
Config lives in .chainlit/config.toml — no programmatic overrides needed.
"""

import chainlit as cl
import json
import asyncio
import os
from modules.hermes_orchestrator import get_or_create_orchestrator, HermesOrchestrator


def render_pipeline_markdown(session_id: str, status_dict: dict) -> str:
    """Gera a tabela Markdown da Pipeline Geral com Sinal de Vida e links de preview."""

    def get_badge(status: str) -> str:
        if status == "completed":
            return "🟢 **Concluido**"
        elif status == "running":
            return "🟡 **Processando**"
        elif status == "error":
            return "❌ **Erro**"
        else:
            return "⚪ **Pendente**"

    base_url = "/api/v1/hermes/preview/" + session_id

    md = f"""### ⚡ DEZAFIRA PIPELINE GERAL (DEEPSEEK LLM)
*Orquestracao de Inteligencia Hermes Agent*

| Estagio / Fabrica | Sinal de Vida | Acao / Preview |
|---|---|---|
| 📝 **Copy & Oferta** | {get_badge(status_dict.get("copy", {}).get("status", "pending"))} | [Ver Copy]({base_url}/copy) |
| 📗 **Fabrica Ebook 3D** | {get_badge(status_dict.get("ebook", {}).get("status", "pending"))} | [Capa 3D]({base_url}/products) |
| 🎓 **Fabrica Curso HD** | {get_badge(status_dict.get("course", {}).get("status", "pending"))} | [Modulos]({base_url}/products) |
| 📱 **Fabrica MiniApp** | {get_badge(status_dict.get("miniapp", {}).get("status", "pending"))} | [MiniApp PWA]({base_url}/products) |
| 💻 **Funil & Checkout** | {get_badge(status_dict.get("funnel", {}).get("status", "pending"))} | [VSL / Asaas]({base_url}/funnel) |
| 📢 **Divulgacao Postiz** | {get_badge(status_dict.get("ads", {}).get("status", "pending"))} | [Anuncios]({base_url}/ads) |

---
"""
    return md

@cl.on_chat_start
async def on_chat_start():
    session_id = cl.user_session.get("id") or "sess_default"
    cl.user_session.set("session_id", session_id)
    
    orchestrator = get_or_create_orchestrator(session_id)
    
    pipeline_md = render_pipeline_markdown(session_id, orchestrator.state["pipeline_status"])
    await cl.Message(content=pipeline_md, author="Dezafira Engine").send()

    actions = [
        cl.Action(name="start_pipeline", payload={"session_id": session_id}, label="▶️ INICIAR PIPELINE GERAL")
    ]

    welcome_text = """**Ola! Eu sou o Hermes Agent**, orquestrador de ofertas do ecossistema Dezafira powered por **DeepSeek LLM**.

Como posso te ajudar hoje? Podemos conversar sobre estrategia, tirar duvidas, ou clicar no botao **▶️ INICIAR PIPELINE GERAL** abaixo para rodar todas as fabricas!"""
    
    await cl.Message(content=welcome_text, actions=actions, author="Hermes").send()

@cl.action_callback("start_pipeline")
async def on_start_pipeline_action(action: cl.Action):
    session_id = cl.user_session.get("session_id") or "sess_default"
    orchestrator = get_or_create_orchestrator(session_id)

    status_msg = await cl.Message(content="⏳ **Iniciando orquestracao com DeepSeek...**", author="Hermes").send()

    async def update_listener(event):
        pipeline_md = render_pipeline_markdown(session_id, event["pipeline_status"])
        status_msg.content = f"{pipeline_md}\n⚡ **Sinal de Vida**: {event['message']}"
        await status_msg.update()

    orchestrator.register_callback(lambda evt: asyncio.create_task(update_listener(evt)))

    result = await orchestrator.run_pipeline("Criar Oferta Completa com MiniApp e Anuncios Postiz")

    final_md = render_pipeline_markdown(session_id, result["pipeline_status"])
    status_msg.content = f"{final_md}\n🎉 **Pipeline Concluida!** Oferta enviada para o painel."
    await status_msg.update()

@cl.on_message
async def on_message(message: cl.Message):
    session_id = cl.user_session.get("session_id") or "sess_default"
    orchestrator = get_or_create_orchestrator(session_id)
    text = message.content.strip().lower()

    trigger_words = ["iniciar", "executar", "criar oferta", "gerar esteira", "gerar funil", "rodar pipeline"]
    should_run_pipeline = any(w in text for w in trigger_words)

    if should_run_pipeline:
        status_msg = await cl.Message(content=f"⏳ **Hermes acionando pipeline para**: '{message.content}'...", author="Hermes").send()

        async def update_listener(event):
            pipeline_md = render_pipeline_markdown(session_id, event["pipeline_status"])
            status_msg.content = f"{pipeline_md}\n⚡ **Sinal de Vida**: {event['message']}"
            await status_msg.update()

        orchestrator.register_callback(lambda evt: asyncio.create_task(update_listener(evt)))

        result = await orchestrator.run_pipeline(message.content)
        final_md = render_pipeline_markdown(session_id, result["pipeline_status"])
        status_msg.content = f"{final_md}\n🎉 **Esteira Gerada!** Acesse os previews na tabela."
        await status_msg.update()
    else:
        response_msg = await cl.Message(content="", author="Hermes").send()
        
        system_prompt = "Voce e o Hermes Agent, assistente inteligente do ecossistema Dezafira. Responda de forma direta, amigavel e prestativa em Portugues do Brasil."
        
        ai_response = await orchestrator.call_deepseek_llm(message.content, system_prompt=system_prompt)
        
        response_msg.content = ai_response
        await response_msg.update()
