"""
================================================================================
DEZAFIRA — Chainlit UI (Hermes Agent + DeepSeek)
================================================================================
Chat conversacional limpo. Config em .chainlit/config.toml.
"""

import chainlit as cl
import json
import asyncio
import os
from modules.hermes_orchestrator import get_or_create_orchestrator, HermesOrchestrator


WELCOME = (
    "**Ola! Eu sou o Hermes Agent**, assistente do ecossistema Dezafira.\n\n"
    "Posso te ajudar com estrategia, duvidas gerais, ou rodar as fabricas "
    "(ebook, curso, miniapp, funil). Basta digitar sua mensagem abaixo."
)


@cl.on_chat_start
async def on_chat_start():
    session_id = cl.user_session.get("id") or "sess_default"
    cl.user_session.set("session_id", session_id)
    get_or_create_orchestrator(session_id)
    await cl.Message(content=WELCOME, author="Hermes").send()


@cl.on_message
async def on_message(message: cl.Message):
    session_id = cl.user_session.get("session_id") or "sess_default"
    orchestrator = get_or_create_orchestrator(session_id)
    text = message.content.strip().lower()

    trigger_words = ["iniciar", "executar", "criar oferta", "gerar esteira", "gerar funil", "rodar pipeline"]

    if any(w in text for w in trigger_words):
        status_msg = await cl.Message(content="Iniciando pipeline...", author="Hermes").send()

        async def on_event(event):
            status_msg.content = f"**{event['message']}**"
            await status_msg.update()

        orchestrator.register_callback(lambda evt: asyncio.create_task(on_event(evt)))
        result = await orchestrator.run_pipeline(message.content)
        status_msg.content = "Pipeline concluida!"
        await status_msg.update()
    else:
        response_msg = await cl.Message(content="", author="Hermes").send()
        system_prompt = "Voce e o Hermes Agent, assistente inteligente do ecossistema Dezafira. Responda de forma direta e prestativa em Portugues do Brasil."
        ai_response = await orchestrator.call_deepseek_llm(message.content, system_prompt=system_prompt)
        response_msg.content = ai_response
        await response_msg.update()
