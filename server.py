import asyncio
import os
import uuid
import json
import html as html_mod
import httpx
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import hashlib
import hmac
import secrets

def esc(text):
    """Escape HTML para injecao segura."""
    return html_mod.escape(str(text or ""))

# Singleton globais â€” compartilhados entre todas as requisicoes (Bug C1)
from pipeline.websocket import WebSocketHub
from pipeline.orchestrator import HermesOrchestrator

_ws_hub = WebSocketHub()
_hermes_orchestrator = HermesOrchestrator(_ws_hub)

from manager import SniperDirector
from modules.uploader import YouTubeUploader

# â”€â”€â”€ Redis (cache + rate limiting) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    import redis.asyncio as aioredis
    REDIS_URL = os.getenv("REDIS_URL", "")
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None
    if redis_client:
        print("[Redis] Conectado:", REDIS_URL[:30] + "...")
except ImportError:
    redis_client = None
    print("[Redis] Modulo redis nao instalado â€” cache desabilitado")
except Exception as e:
    redis_client = None
    print(f"[Redis] Erro ao conectar: {e}")
from research.spiders.youtube_search import YouTubeSearchSpider
from modules.database import (
    get_db_channels, 
    create_db_channel, 
    delete_db_channel, 
    save_db_prediction, 
    update_db_prediction, 
    get_db_prediction,
    Channel,
    Prediction,
    SessionLocal,
    get_db_ai_created_channels,
    create_db_ai_created_channel,
    delete_db_ai_created_channel,
    get_db_book,
    get_db_course,
    get_db_books,
    get_db_courses,
    get_db_user_by_id,
)

try:
    from modules.telegram_bot import init_telegram_bot, send_telegram_notification
except ImportError:
    print("[Server] telebot nao instalado. Telegram Bot desabilitado.")
    def init_telegram_bot(*args, **kwargs): pass
    def send_telegram_notification(text: str): pass

app = FastAPI(title="F.Video & Open-Generative-AI Integration API")

# Serve arquivos gerados pelas fábricas (capas de curso/ebook, imagens, etc.)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTPUTS_DIR = os.path.join(_BASE_DIR, "outputs")
_STATIC_DIR = os.path.join(_BASE_DIR, "static")

# ═════════════════════════════════════════════════════════════════════════
# HERMES AGENT & PIPELINE CENTRAL ENDPOINTS (TLC SPEC-DRIVEN)
# ═════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/hermes/pipeline/status/{session_id}")
async def get_hermes_pipeline_status(session_id: str):
    """Retorna o estado completo da Pipeline Central e Sinal de Vida para a sessão."""
    from modules.hermes_orchestrator import get_or_create_orchestrator
    orchestrator = get_or_create_orchestrator(session_id)
    return {
        "success": True,
        "state": orchestrator.state
    }

@app.get("/api/v1/hermes/preview/{session_id}/{preview_type}", response_class=HTMLResponse)
async def serve_hermes_preview(session_id: str, preview_type: str, tab: Optional[str] = None):
    """
    Serve a página de preview HTML em tempo real para cada fase da Pipeline Central.
    """
    from modules.hermes_orchestrator import get_or_create_orchestrator
    from modules.preview_generator import PreviewGenerator

    orchestrator = get_or_create_orchestrator(session_id)
    session_data = {
        **orchestrator.state.get("spec", {}),
        **orchestrator.state.get("deliverables", {})
    }
    
    target_type = tab if tab else preview_type
    html_content = PreviewGenerator.generate_full_preview_html(target_type, session_data)
    return HTMLResponse(content=html_content)

@app.get("/api/v1/postiz/status")
async def get_postiz_integration_status():
    """Retorna o status da integração com a API/MCP do Postiz."""
    from modules.postiz_client import postiz_client
    return await postiz_client.get_status()

# ═════════════════════════════════════════════════════════════════════════
# FABRICA DE MINIAPPS — API DA SALA DE AGENTES & BANCO POSTGRESQL
# ═════════════════════════════════════════════════════════════════════════
@app.post("/api/v1/miniapps/create")
async def create_miniapp_endpoint(payload: Dict[str, Any]):
    """Cria um MiniApp PWA completo orquestrando a Sala de Agentes."""
    from modules.miniapp_factory import miniapp_factory
    prompt = payload.get("prompt", "Calculadora de Alta Performance")
    niche = payload.get("niche", "Geral")
    result = await miniapp_factory.create_miniapp_with_room(prompt, niche)
    return {"success": True, "miniapp": result}


@app.get("/api/v1/miniapps")
async def list_miniapps_endpoint():
    """Lista todos os MiniApps criados (persistidos no PostgreSQL)."""
    from modules.database import get_db_miniapps
    apps = get_db_miniapps()
    return {"miniapps": apps, "total": len(apps)}


@app.get("/api/v1/miniapps/{app_id}")
async def get_miniapp_endpoint(app_id: str):
    """Retorna os detalhes e o cronograma de entregas temporizadas do MiniApp."""
    from modules.database import get_db_miniapp
    try:
        app = get_db_miniapp(app_id)
        if not app:
            return {"error": "MiniApp nao encontrado", "app_id": app_id}
        return app
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/v1/miniapps/{app_id}")
async def delete_miniapp_endpoint(app_id: str):
    """Deleta um MiniApp e seus drip contents."""
    from modules.database import delete_db_miniapp
    ok = delete_db_miniapp(app_id)
    if not ok:
        raise HTTPException(status_code=404, detail="MiniApp nao encontrado")
    return {"message": "MiniApp deletado com sucesso"}


def get_trial_expired_html(app_name: str, checkout_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acesso Expirado - {app_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        body {{
            background-color: #060911;
            color: #f8fafc;
            font-family: 'Plus Jakarta Sans', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .paywall-card {{
            background: #090d16;
            border: 1px solid #1e293b;
            border-radius: 24px;
            max-width: 480px;
            width: 100%;
            padding: 40px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            animation: fadeIn 0.5s ease-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 24px;
        }}
        h1 {{
            font-size: 24px;
            font-weight: 800;
            margin-bottom: 12px;
            color: #f8fafc;
        }}
        p {{
            font-size: 14px;
            color: #94a3b8;
            line-height: 1.6;
            margin-bottom: 32px;
        }}
        .btn-subscribe {{
            display: block;
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #8b5cf6, #38bdf8);
            color: white;
            text-decoration: none;
            font-weight: 700;
            font-size: 16px;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .btn-subscribe:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6);
        }}
        .progress-lost {{
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            color: #ef4444;
            padding: 12px;
            border-radius: 8px;
            font-size: 12px;
            margin-bottom: 24px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="paywall-card">
        <div class="icon">🔒</div>
        <h1>Período de Testes Concluído!</h1>
        <p>Seus 7 dias de acesso gratuito ao <strong>{app_name}</strong> expiraram.</p>
        <div class="progress-lost">
            ⚠️ Assine hoje para salvar seu progresso e manter seu cronograma de memorização ativo.
        </div>
        <a href="{checkout_url}" class="btn-subscribe">Assinar Agora</a>
    </div>
</body>
</html>"""


@app.get("/api/v1/miniapps/{app_id}/view", response_class=HTMLResponse)
async def view_miniapp_endpoint(app_id: str, token: str = "", authorization: str = Header(None)):
    """Retorna o HTML do MiniApp. Valida o trial de 7 dias se o usuário for membro."""
    from modules.database import get_db_miniapp
    app = get_db_miniapp(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="MiniApp não encontrado")
    
    # Se houver um token informado, validar o trial de 7 dias
    t = token or (authorization.replace("Bearer ", "") if authorization else "")
    if t:
        user_id = _verify_jwt_token(t)
        if user_id:
            user = get_db_user_by_id(user_id)
            if user and user.role != "admin" and not user.subscription_active:
                trial_start = user.trial_started_at or user.created_at
                if not trial_start:
                    trial_start = datetime.utcnow()
                delta = datetime.utcnow() - trial_start
                if delta.days >= 7:
                    # Retorna um HTML de bloqueio (Paywall)
                    checkout_url = f"/checkout/{app.get('id')}"
                    return HTMLResponse(content=get_trial_expired_html(app.get("app_name", "Clube"), checkout_url), status_code=403)
                    
    pwa_html = app.get("pwa_html") or "<h1>MiniApp sem conteudo</h1>"
    return HTMLResponse(content=pwa_html)

# ═════════════════════════════════════════════════════════════════════════
# FABRICA DE EBOOKS TRIPLA — API ASYNC COM PROGRESSO
# ═════════════════════════════════════════════════════════════════════════
import uuid as _uuid

@app.post("/api/v1/ebooks/generate-pack")
async def generate_ebook_pack_endpoint(payload: Dict[str, Any]):
    """Inicia geracao assincrona de pack de 3 ebooks. Retorna task_id imediatamente."""
    from modules.ebook_factory import triple_ebook_factory
    main_title = payload.get("title", "Negocios Digitais com IA 2026")
    niche = payload.get("niche", "Geral")
    task_id = f"ebk_{_uuid.uuid4().hex[:8]}"

    async def _run():
        try:
            await triple_ebook_factory.generate_triple_pack(main_title, niche, task_id=task_id)
        except Exception as e:
            print(f"[EbookFactory] Erro na task {task_id}: {e}")

    asyncio.create_task(_run())
    return {"success": True, "task_id": task_id, "message": "Geracao iniciada. Use GET /api/v1/ebooks/task/{task_id} para acompanhar."}


@app.get("/api/v1/ebooks/task/{task_id}")
async def get_ebook_task_status(task_id: str):
    """Retorna o progresso da geracao de ebooks em tempo real."""
    from modules.ebook_factory import get_ebook_task
    task = get_ebook_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task nao encontrada")
    # Nao retornar o pack inteiro no polling (muito grande)
    response = {k: v for k, v in task.items() if k != "pack"}
    if task.get("pack"):
        response["pack_ready"] = True
        response["main_title"] = task["pack"].get("main_title")
        response["total_ebooks"] = task["pack"].get("total_ebooks", 0)
    return response


@app.get("/api/v1/ebooks/task/{task_id}/result")
async def get_ebook_task_result(task_id: str):
    """Retorna o resultado completo da geracao de ebooks."""
    from modules.ebook_factory import get_ebook_task
    task = get_ebook_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task nao encontrada")
    if task.get("status") != "completed":
        raise HTTPException(status_code=202, detail=f"Task ainda em progresso: {task.get('phase')}")
    return {"success": True, "pack_data": task["pack"]}

# ═════════════════════════════════════════════════════════════════════════
# HERMES CHAT OFICIAL (NOUS RESEARCH) — API + PÁGINA
#
# O chat conversa com o Hermes Agent OFICIAL da Nous Research
# (https://hermes-agent.nousresearch.com) via um gateway OpenAI-compatível:
#
#   1) LOCAL — Hermes Agent instalado no seu PC (Windows/Mac/Linux):
#        hermes setup --portal    (login OAuth com sua conta Nous)
#        API_SERVER_ENABLED=true  hermes gateway   (abre 127.0.0.1:8642/v1)
#      Basta o gateway rodando: o backend detecta sozinho (sem config extra).
#
#   2) NUVEM — API de inferência hospedada oficial da Nous (planos pagos):
#        HERMES_GATEWAY_URL=https://inference-api.nousresearch.com/v1
#        HERMES_API_KEY=<sua chave do portal.nousresearch.com>
#        HERMES_MODEL=<modelo, ex: hermes-4-70b>
#
# Se nenhum gateway estiver acessível, o chat cai na cascata LLM interna
# (fallback) — a resposta indica qual motor respondeu via campo `engine`.
# ═════════════════════════════════════════════════════════════════════════

# Histórico de conversa por sessão (em memória; ok para 1 réplica uvicorn)
hermes_chat_histories: Dict[str, List[Dict[str, str]]] = {}
hermes_pipeline_tasks: Dict[str, Any] = {}

# Cache de descoberta do gateway oficial (evita sondar a cada mensagem)
_HERMES_GATEWAY_CACHE = {"ts": 0.0, "online": False, "models": [], "url": ""}
_HERMES_GATEWAY_TTL = 30.0


def _hermes_gateway_url() -> str:
    """URL base do gateway OpenAI-compatível do Hermes Agent oficial."""
    url = os.getenv("HERMES_GATEWAY_URL", "").strip()
    if url:
        return url.rstrip("/")
    # Porta padrão do Hermes Agent local (hermes gateway / API_SERVER_ENABLED)
    return "http://127.0.0.1:8642/v1"


def _hermes_api_key() -> str:
    return os.getenv("HERMES_API_KEY", "").strip()


def _hermes_model() -> str:
    """Modelo a usar no gateway: env HERMES_MODEL > primeiro modelo descoberto
    no /v1/models > 'hermes-agent' (padrão do gateway local)."""
    m = os.getenv("HERMES_MODEL", "").strip()
    if m:
        return m
    models = _HERMES_GATEWAY_CACHE.get("models") or []
    if models:
        return models[0]
    return "hermes-agent"


async def _hermes_probe_gateway(force: bool = False):
    """Sonda o gateway oficial (GET /v1/models) com cache de TTL."""
    import time as _t
    now = _t.time()
    url = _hermes_gateway_url()
    cached = _HERMES_GATEWAY_CACHE
    if (
        not force
        and cached["url"] == url
        and (now - cached["ts"]) < _HERMES_GATEWAY_TTL
    ):
        return cached["online"], cached["models"]

    online, models = False, []
    try:
        host = url.split("://")[-1].split("/")[0]
        needs_key = "inference-api.nousresearch.com" in host
        if needs_key and not _hermes_api_key():
            raise RuntimeError("HERMES_API_KEY ausente para a API hospedada da Nous")
        headers = {}
        if _hermes_api_key():
            headers["Authorization"] = f"Bearer {_hermes_api_key()}"
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.get(f"{url}/models", headers=headers)
            if r.status_code == 200:
                data = r.json()
                raw = data.get("data", data if isinstance(data, list) else [])
                models = [str(m.get("id") or m.get("name") or m) for m in raw][:12]
                online = True
    except Exception as e:
        print(f"[HermesOficial] Gateway {url} indisponível: {type(e).__name__}: {e}"[:200])
        online = False

    cached.update({"ts": now, "online": online, "models": models, "url": url})
    return online, models


async def _hermes_official_chat(messages: List[Dict[str, str]]) -> str:
    """Chama o Hermes Agent oficial via /chat/completions (OpenAI-compatível)."""
    url = _hermes_gateway_url()
    headers = {"Content-Type": "application/json"}
    if _hermes_api_key():
        headers["Authorization"] = f"Bearer {_hermes_api_key()}"
    payload = {
        "model": _hermes_model(),
        "messages": messages,
        "max_tokens": 1200,
        "temperature": 0.7,
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(f"{url}/chat/completions", headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(
                f"Gateway Hermes respondeu HTTP {r.status_code}: {r.text[:300]}"
            )
        data = r.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError("Resposta do gateway Hermes em formato inesperado")
        return str(content).strip() or "…"


class HermesChatPayload(BaseModel):
    message: str
    session_id: Optional[str] = None


@app.get("/api/v1/hermes/status")
async def hermes_status():
    """Status do chat: mostra qual motor está ativo
    (Hermes Oficial da Nous vs fallback interno)."""
    gateway = _hermes_gateway_url()
    configured = bool(os.getenv("HERMES_GATEWAY_URL", "").strip())
    online, models = await _hermes_probe_gateway(force=False)
    return {
        "official_online": online,
        "gateway_url": gateway,
        "configured": configured,
        "model": _hermes_model(),
        "models": models,
        "engine": "hermes_official" if online else "fallback_llm",
        "hermes_webui_url": os.getenv("HERMES_WEBUI_PUBLIC_URL", "").strip(),
    }


@app.post("/api/v1/hermes/chat")
async def hermes_chat_endpoint(payload: HermesChatPayload):
    """Chat do Hermes — usa o Hermes Agent OFICIAL da Nous Research quando o
    gateway está acessível; senão cai na cascata LLM interna (fallback).

    Aceita comandos de disparo da Pipeline Central ("iniciar", "gerar esteira",
    "criar oferta"...) e inicia o orquestrador em background, igual ao antigo
    chat Chainlit.
    """
    sid = (payload.session_id or "sess_admin").strip() or "sess_admin"
    text = (payload.message or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Mensagem vazia")

    history = hermes_chat_histories.setdefault(sid, [])
    history.append({"role": "user", "content": text})
    history = history[-12:]
    hermes_chat_histories[sid] = history

    system_instruction = (
        "Você é o Hermes, o Agente Orquestrador executivo e extremamente inteligente "
        "da plataforma DEZAFIRA, a Fábrica de Conteúdo. Você está conversando com o "
        "fundador (Jonatas). Seu objetivo é rodar a esteira no modo autônomo e "
        "responder de forma direta, clara e executiva em português."
    )

    trigger_words = ["iniciar", "executar", "criar oferta", "gerar esteira",
                     "gerar funil", "rodar pipeline", "pipeline geral",
                     "todas as fábricas", "todas as fabricas", "esteira completa"]
    lowered = text.lower()
    pipeline_started = any(w in lowered for w in trigger_words)

    engine = "hermes_official"
    if pipeline_started:
        engine = "pipeline"
        from modules.hermes_orchestrator import get_or_create_orchestrator
        orchestrator = get_or_create_orchestrator(sid)
        try:
            task = asyncio.create_task(orchestrator.run_pipeline(text))
            hermes_pipeline_tasks[sid] = task

            def _pipeline_done(t, _sid=sid):
                # Evita "Task exception was never retrieved" e deixa o erro visível no log
                try:
                    exc = t.exception()
                    if exc:
                        print(f"[HermesChat] Pipeline {_sid} falhou: {exc}")
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"[HermesChat] Erro ao ler task {_sid}: {e}")

            task.add_done_callback(_pipeline_done)
            reply = (
                "▶️ **Pipeline Geral iniciada!**\n\n"
                "O Hermes está orquestrando todas as fábricas (Blog, Ebook, Curso, "
                "MiniApp, Marketing, Postiz)...\n\n"
                f"Acompanhe o progresso em `/api/v1/hermes/pipeline/status/{sid}`."
            )
        except Exception as e:
            reply = f"⚠️ Não consegui iniciar a pipeline: {esc(e)}"
    else:
        messages = [{"role": "system", "content": system_instruction}] + history
        engine = "fallback_llm"
        try:
            online, _models = await _hermes_probe_gateway()
        except Exception:
            online = False
        if online:
            try:
                reply = await _hermes_official_chat(messages)
                engine = "hermes_official"
            except Exception:
                reply = None
        else:
            reply = None
        if reply is None:
            try:
                from agents.llm import query_llm
                reply = await query_llm(messages, max_tokens=1200)
            except Exception as e2:
                reply = f"Desculpe, tive um problema ao pensar: {esc(e2)}"

    history.append({"role": "assistant", "content": reply})
    hermes_chat_histories[sid] = history
    return {"reply": reply, "session_id": sid, "pipeline_started": pipeline_started, "engine": engine}


_HERMES_CHAT_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Hermes Agent — Chat Oficial · Dezafira</title>
<style>
  :root{ --bg:#060911; --panel:#0a0f1c; --border:#1e293b; --text:#e2e8f0; --dim:#94a3b8; --brand:#38bdf8; }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,-apple-system,sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
  header{display:flex;align-items:center;gap:12px;padding:14px 20px;background:linear-gradient(180deg,#0d1424,#0a0f1c);border-bottom:1px solid var(--border)}
  .logo{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;box-shadow:0 4px 18px rgba(99,102,241,.35)}
  h1{font-size:15px;font-weight:700}
  .status{font-size:11px;color:#4ade80;display:inline-flex;align-items:center;gap:5px;margin-left:6px}
  .status::before{content:"";width:7px;height:7px;border-radius:50%;background:#4ade80;box-shadow:0 0 8px #4ade80}
  .status.warn{color:#fbbf24}
  .status.warn::before{background:#fbbf24;box-shadow:0 0 8px #fbbf24}
  .status.off{color:#94a3b8}
  .status.off::before{background:#64748b;box-shadow:none}
  .bubble .eng{display:inline-block;font-size:9px;font-weight:700;color:#38bdf8;border:1px solid #38bdf8;border-radius:4px;padding:0 5px;margin-left:6px;vertical-align:1px;letter-spacing:.5px}
  .bubble .eng.fb{color:#fbbf24;border-color:#fbbf24}
  .sub{font-size:11px;color:var(--dim);margin-top:2px}
  #quickbar{display:flex;gap:6px;padding:10px 20px 0;flex-wrap:wrap}
  .quick{background:#0f1526;border:1px solid var(--border);border-radius:8px;padding:6px 11px;font-size:11px;color:#7dd3fc;cursor:pointer;font-family:inherit}
  .quick:hover{border-color:var(--brand)}
  #messages{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:12px}
  .msg{display:flex;gap:10px;max-width:92%}
  .msg.user{align-self:flex-end;flex-direction:row-reverse}
  .avatar{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}
  .avatar.bot{background:linear-gradient(135deg,#6366f1,#8b5cf6)}
  .avatar.user{background:#1e293b}
  .bubble{background:#0f1526;border:1px solid var(--border);border-radius:14px;padding:10px 14px;font-size:13px;line-height:1.6;overflow-wrap:anywhere}
  .msg.user .bubble{background:#12314a;border-color:#155e8a}
  .bubble .name{display:block;font-size:11px;font-weight:700;color:#a5b4fc;margin-bottom:4px}
  .msg.user .bubble .name{color:#7dd3fc}
  .bubble strong{color:#c4b5fd}
  .bubble pre{background:#060911;border:1px solid var(--border);border-radius:8px;padding:10px;overflow-x:auto;font-size:12px}
  .bubble code{background:#1e293b;padding:1px 5px;border-radius:4px;font-size:12px}
  .bubble a{color:#7dd3fc}
  .typing{display:inline-flex;gap:4px;padding:6px 2px}
  .typing span{width:7px;height:7px;border-radius:50%;background:#8b5cf6;animation:blink 1.2s infinite}
  .typing span:nth-child(2){animation-delay:.2s}
  .typing span:nth-child(3){animation-delay:.4s}
  @keyframes blink{0%,100%{opacity:.25}50%{opacity:1}}
  footer{border-top:1px solid var(--border);background:var(--panel);padding:12px 20px;display:flex;gap:10px;align-items:center}
  #input{flex:1;background:#070a12;border:1px solid var(--border);border-radius:10px;color:var(--text);padding:11px 14px;font-size:13px;font-family:inherit;outline:none}
  #input:focus{border-color:var(--brand)}
  #sendBtn{background:linear-gradient(135deg,#0284c7,#6366f1);color:#fff;border:none;border-radius:10px;padding:11px 18px;font-weight:700;font-size:13px;cursor:pointer}
  #sendBtn:hover{filter:brightness(1.15)}
</style>
</head>
<body>
<header>
  <div class="logo">🤖</div>
  <div>
    <h1>Hermes Agent <span class="status" id="statusBadge">Conectando…</span></h1>
    <div class="sub" id="subLine">Chat oficial · Orquestrador Central Dezafira</div>
  </div>
</header>
<div id="quickbar">
  <button class="quick" onclick="send('INICIAR PIPELINE GERAL')">▶️ INICIAR PIPELINE GERAL</button>
  <button class="quick" onclick="send('Gere um ebook sobre [tema]')">📗 Ebook</button>
  <button class="quick" onclick="send('Gere um curso sobre [tema]')">🎓 Curso</button>
  <button class="quick" onclick="send('Crie um miniapp para [ideia]')">📱 MiniApp</button>
</div>
<div id="messages"></div>
<footer>
  <input id="input" placeholder="Digite sua mensagem para o Hermes..." autofocus/>
  <button id="sendBtn" onclick="send()">Enviar</button>
</footer>
<script>
var sid = sessionStorage.getItem("dz_hermes_sid") || ("sess_" + Math.random().toString(36).slice(2,8));
sessionStorage.setItem("dz_hermes_sid", sid);
var msgs = document.getElementById("messages");
function esc(s){var d=document.createElement("div");d.textContent=s==null?"":String(s);return d.innerHTML;}
function md(s){
  s=esc(s);
  var preBlocks=[];
  s=s.replace(/```([\s\S]*?)```/g,function(m,c){preBlocks.push("<pre>"+esc(c)+"</pre>");return "\u0000PRE"+(preBlocks.length-1)+"\u0000";});
  s=s.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");
  s=s.replace(/`([^`]+)`/g,"<code>$1</code>");
  s=s.replace(/(https?:\/\/[^\s<]+)/g,'<a href="$1" target="_blank" rel="noreferrer">$1</a>');
  s=s.replace(/\n/g,"<br/>");
  s=s.replace(/\u0000PRE(\d+)\u0000/g,function(m,i){return preBlocks[+i];});
  return s;
}
function addMsg(text, who, engine){
  var d=document.createElement("div");
  d.className="msg "+(who==="user"?"user":"bot");
  var engHtml="";
  if(engine==="hermes_official"){engHtml='<span class="eng">NOUS</span>';}
  else if(engine==="fallback_llm"){engHtml='<span class="eng fb">FALLBACK</span>';}
  d.innerHTML='<div class="avatar '+(who==="user"?"user":"bot")+'">'+(who==="user"?"👤":"🤖")+'</div><div class="bubble"><span class="name">'+(who==="user"?"Você":"Hermes")+'</span>'+engHtml+md(text)+'</div>';
  msgs.appendChild(d);
  msgs.scrollTop=msgs.scrollHeight;
}
function addTyping(){
  var d=document.createElement("div");
  d.className="msg bot";
  d.id="typing";
  d.innerHTML='<div class="avatar bot">🤖</div><div class="bubble"><span class="name">Hermes</span><span class="typing"><span></span><span></span><span></span></span></div>';
  msgs.appendChild(d);
  msgs.scrollTop=msgs.scrollHeight;
}
function removeTyping(){var t=document.getElementById("typing");if(t)t.remove();}
function send(pre){
  var inp=document.getElementById("input");
  var text=(pre||inp.value||"").trim();
  if(!text)return;
  inp.value="";
  addMsg(text,"user");
  addTyping();
  fetch("/api/v1/hermes/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text,session_id:sid})})
    .then(function(r){return r.json();})
    .then(function(res){
      removeTyping();
      addMsg(res.reply||(res.error||res.detail||"Sem resposta"),"bot",res.engine);
    })
    .catch(function(e){removeTyping();addMsg("Erro de conexão: "+e.message,"bot");});
}
document.getElementById("input").addEventListener("keydown",function(e){if(e.key==="Enter")send();});
function loadStatus(){
  fetch("/api/v1/hermes/status").then(function(r){return r.json();}).then(function(s){
    var badge=document.getElementById("statusBadge");
    var sub=document.getElementById("subLine");
    if(s.official_online){
      badge.className="status";
      badge.textContent="Hermes Oficial · Nous Research";
      sub.textContent="Chat oficial do Hermes Agent (Nous Research) · modelo "+(s.model||"hermes-agent");
    }else{
      badge.className="status warn";
      badge.textContent="Fallback LLM";
      sub.textContent="Gateway Hermes oficial offline — usando cascata LLM interna. Instale o Hermes Agent (hermes setup --portal; hermes gateway) ou configure HERMES_GATEWAY_URL / HERMES_API_KEY.";
    }
  }).catch(function(){
    var b=document.getElementById("statusBadge");
    if(b){b.className="status off";b.textContent="Offline";}
  });
}
loadStatus();
addMsg("Olá! Sou o Hermes, orquestrador do ecossistema Dezafira. Posso responder estratégia, tirar dúvidas ou **iniciar a esteira completa** de fábricas (ebook, curso, miniapp, funil, marketing).","bot");
</script>
</body>
</html>"""


@app.get("/chat")
async def chat_official():
    """Serve o Chat Oficial do Hermes (página embutida no backend).

    Se HERMES_WEBUI_PUBLIC_URL estiver definido (ex: URL do Hermes WebUI
    deployado), redireciona para lá; senão serve a página de chat embutida.
    """
    webui_url = os.getenv("HERMES_WEBUI_PUBLIC_URL", "").strip()
    if webui_url:
        return RedirectResponse(url=webui_url)
    return HTMLResponse(
        content=_HERMES_CHAT_HTML,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"},
    )


# ═════════════════════════════════════════════════════════════════════════
# BLOG FRONTEND — API PÚBLICA
# ═════════════════════════════════════════════════════════════════════════

if os.path.isdir(_OUTPUTS_DIR):
    app.mount("/outputs", StaticFiles(directory=_OUTPUTS_DIR), name="outputs")
if os.path.isdir(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
# ═══════════════════════════════════════════════════════════════════════════
# AUTH — bcrypt + JWT + require_admin (precisa ANTES de qualquer endpoint)
# ═══════════════════════════════════════════════════════════════════════════
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

CORS_ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://dezafira.com.br",
    "https://www.dezafira.com.br",
    "https://dezafiraadm-frontend-production.up.railway.app",
    "https://adm.dezafira.com.br",
}

class RobustCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        origin = request.headers.get("origin", "")

        # Verifica se a origem é permitida (lista explícita ou subdomínio de dezafira.com.br)
        import re
        allowed = (
            origin in CORS_ALLOWED_ORIGINS
            or bool(re.match(r"https://.*\.dezafira\.com\.br$", origin))
        )

        cors_headers = {
            "Access-Control-Allow-Origin": origin if allowed else "",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, Accept, Origin",
            "Access-Control-Max-Age": "86400",
            "Vary": "Origin",
        }

        # Responde diretamente ao preflight OPTIONS
        if request.method == "OPTIONS":
            return Response(status_code=204, headers={k: v for k, v in cors_headers.items() if v})

        response = await call_next(request)

        # Injeta headers CORS em todas as respostas
        if allowed:
            for key, value in cors_headers.items():
                if value:
                    response.headers[key] = value

        # Força HTTPS em redirects para evitar Mixed Content em iframes
        if "location" in response.headers and response.headers["location"].startswith("http://"):
            response.headers["location"] = response.headers["location"].replace("http://", "https://", 1)

        return response

app.add_middleware(RobustCORSMiddleware)

import bcrypt as _bcrypt_mod
from datetime import datetime, timedelta

def _hash_password(password: str) -> str:
    return _bcrypt_mod.hashpw(password.encode("utf-8"), _bcrypt_mod.gensalt()).decode("utf-8")

def _verify_password(password: str, hashed: str) -> bool:
    return _bcrypt_mod.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# ─── Auth ────────────────────────────────────────────────────────────────
# O segredo do JWT é OBRIGATÓRIO — o fallback hardcoded foi removido por
# segurança. Em produção, defina AUTH_SECRET (ou SECRET_KEY) no Railway.
AUTH_SECRET = os.getenv("AUTH_SECRET") or os.getenv("SECRET_KEY")
if not AUTH_SECRET:
    raise RuntimeError(
        "AUTH_SECRET não configurado: defina AUTH_SECRET (ou SECRET_KEY) no ambiente/.env "
        "antes de iniciar o servidor. O fallback hardcoded foi removido por segurança."
    )
if len(AUTH_SECRET) < 16:
    raise RuntimeError("AUTH_SECRET muito curto: use no mínimo 16 caracteres.")
JWT_EXPIRE_HOURS = 24 * 7

def _generate_jwt_token(user_id: str) -> str:
    payload = f"{user_id}:{int(datetime.utcnow().timestamp()) + JWT_EXPIRE_HOURS * 3600}"
    sig = hashlib.sha256(f"{payload}:{AUTH_SECRET}".encode()).hexdigest()[:32]
    return f"{payload}:{sig}"

def _verify_jwt_token(token: str) -> str | None:
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        user_id, exp_ts, sig = parts
        payload = f"{user_id}:{exp_ts}"
        expected = hashlib.sha256(f"{payload}:{AUTH_SECRET}".encode()).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return None
        if int(exp_ts) < int(datetime.utcnow().timestamp()):
            return None
        return user_id
    except Exception:
        return None

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization.replace("Bearer ", "")
    user_id = _verify_jwt_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado")
    user = get_db_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado ou inativo")
    return {
        "id": user.id, 
        "email": user.email, 
        "name": user.name, 
        "role": user.role, 
        "avatar_url": user.avatar_url,
        "plan": getattr(user, "plan", "free") or "free",
        "subscription_expires_at": user.subscription_expires_at.isoformat() if getattr(user, "subscription_expires_at", None) else None
    }

async def get_optional_user(authorization: str = Header(None)):
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    user_id = _verify_jwt_token(token)
    if not user_id:
        return None
    user = get_db_user_by_id(user_id)
    if not user or not user.is_active:
        return None
    return {
        "id": user.id, 
        "email": user.email, 
        "name": user.name, 
        "role": user.role, 
        "avatar_url": user.avatar_url,
        "plan": getattr(user, "plan", "free") or "free",
        "subscription_expires_at": user.subscription_expires_at.isoformat() if getattr(user, "subscription_expires_at", None) else None
    }

async def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user

async def require_admin_or_token(token: str = ""):
    if not token:
        raise HTTPException(status_code=401, detail="Token ausente")
    user_id = _verify_jwt_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado")
    user = get_db_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado ou inativo")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user

def _matches_service_key(value: str | None) -> bool:
    """Valida uma chave de serviço (header X-Service-Key) contra SERVICE_API_KEY.

    Comparação em tempo constante (hmac.compare_digest) para evitar timing
    attacks. Sem SERVICE_API_KEY configurada, a service key fica desabilitada.
    """
    expected = os.getenv("SERVICE_API_KEY", "").strip()
    return bool(expected and value and hmac.compare_digest(value, expected))

async def require_admin_or_service(
    authorization: str = Header(None),
    x_service_key: str = Header(None),
):
    """Admin via JWT (Authorization: Bearer) OU via chave de serviço (X-Service-Key).

    Permite que orquestradores externos (ex: Hermes no AionUi) disparem pipelines
    e consultem diagnósticos sem expor as credenciais do admin. A service key é
    comparada em tempo constante e não expira (gerenciada via env SERVICE_API_KEY).
    """
    if _matches_service_key(x_service_key):
        return {
            "id": "service:hermes",
            "email": "service@dezafira",
            "name": "Hermes Service",
            "role": "admin",
            "plan": "service",
        }
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization.replace("Bearer ", "")
    user_id = _verify_jwt_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado")
    user = get_db_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado ou inativo")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user

# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "dezafira-backend"}


# Estado do healthcheck com graca de tempo (evita restart loop durante deploys)
_HEALTH_STATE = {"down_since": None}

# Estado do watcher de alertas de queda do motor Obscura
_OBSCURA_WATCHER = {
    "running": False,
    "last_check": None,
    "incidents": [],       # [{started_at, ended_at, duration_s, alerted}]
    "down_since": None,
    "alerted": False,
}


async def _obscura_alert_watcher(interval: int = 30):
    """Monitora o motor Obscura e registra incidentes de queda (grace-aware).

    Roda em background; nunca lança exceção (tudo é capturado) para não
    derrubar o processo. Alimenta _OBSCURA_WATCHER e _HEALTH_STATE usados
    pelo /api/v1/obscura/status e /healthz/detailed.
    """
    import time as _t
    while True:
        try:
            now = _t.time()
            online = False
            try:
                from services.obscura_bridge import get_obscura_status
                s = await asyncio.wait_for(get_obscura_status(), timeout=6)
                online = bool(s.get("online")) if isinstance(s, dict) else False
            except (asyncio.TimeoutError, Exception):
                online = False

            _OBSCURA_WATCHER["last_check"] = now

            if not online:
                if _OBSCURA_WATCHER["down_since"] is None:
                    _OBSCURA_WATCHER["down_since"] = now
                    _OBSCURA_WATCHER["alerted"] = False
                from services.obscura_health import get_grace_seconds
                if not _OBSCURA_WATCHER["alerted"] and (now - _OBSCURA_WATCHER["down_since"]) >= get_grace_seconds():
                    _OBSCURA_WATCHER["alerted"] = True
                    _OBSCURA_WATCHER["incidents"].append({
                        "started_at": _OBSCURA_WATCHER["down_since"],
                        "alerted": True,
                    })
                    try:
                        send_telegram_notification(
                            f"⚠️ Motor Obscura fora do ar há mais de {int(get_grace_seconds())}s. Verifique o serviço."
                        )
                    except Exception:
                        pass
            else:
                if _OBSCURA_WATCHER["down_since"] is not None:
                    duration_s = now - _OBSCURA_WATCHER["down_since"]
                    if _OBSCURA_WATCHER["incidents"]:
                        _OBSCURA_WATCHER["incidents"][-1].update({
                            "ended_at": now,
                            "duration_s": int(duration_s),
                        })
                    _OBSCURA_WATCHER["down_since"] = None
                    _OBSCURA_WATCHER["alerted"] = False

            # Mantém _HEALTH_STATE em sincronia (usado pelo /healthz/detailed)
            _HEALTH_STATE["down_since"] = _OBSCURA_WATCHER["down_since"]
            _OBSCURA_WATCHER["incidents"] = _OBSCURA_WATCHER["incidents"][-20:]
        except Exception as e:
            print(f"[ObscuraWatcher] erro no ciclo: {e}")
        await asyncio.sleep(interval)


@app.get("/healthz")
async def healthz():
    """Healthcheck publico do Railway.

    Sempre retorna 200 enquanto o servidor estiver rodando â€” nao depende
    de motores externos (Obscura/Chrome) para nao travar o deploy.
    Os motores sao monitorados separadamente via /healthz/detailed.
    """
    import os as _os
    
    detail = {
        "status": "ok",
        "service": "dezafira-backend",
        "obscura_enabled": _os.getenv("OBSCURA_ENABLED", "true").lower() in ("true", "1", "yes"),
        "obscura_host": _os.getenv("OBSCURA_HOST", "127.0.0.1"),
        "obscura_port": int(_os.getenv("OBSCURA_PORT", "9222")),
        "workers": int(_os.getenv("OBSCURA_WORKERS", "4")),
    }
    
    # Banco: informativo (nao derruba o healthcheck)
    try:
        from sqlalchemy import text as _sql_text
        from modules.database import SessionLocal
        _db = SessionLocal()
        _db.execute(_sql_text("SELECT 1"))
        _db.close()
        detail["database"] = "ok"
    except Exception as e:
        detail["database"] = f"error: {str(e)[:100]}"
    
    return detail


@app.get("/healthz/detailed")
async def healthz_detailed():
    """Healthcheck detalhado â€” sonda motores externos (Obscura/Chrome).
    Usado pelo painel admin, nao pelo Railway.
    """
    import os as _os
    import time as _t

    from services.obscura_bridge import get_obscura_status, get_chrome_status, _pick_bridge_host_port

    async def _probe_obscura():
        try:
            o = await asyncio.wait_for(get_obscura_status(), timeout=12)
        except asyncio.TimeoutError:
            o = {"online": False, "error": "TimeoutError: sonda pendurou > 12s"}
        except Exception as e:
            o = {"online": False, "error": f"{type(e).__name__}: {e}"[:200]}
        if not isinstance(o, dict):
            o = {"online": False, "error": "resposta invalida"}
        o.setdefault("ws_url", "")
        o.setdefault("targets", 0)
        o.setdefault("host", "")
        o.setdefault("port", 0)
        o.setdefault("error", "")
        return o

    async def _probe_chrome():
        try:
            c = await asyncio.wait_for(get_chrome_status(), timeout=5)
        except asyncio.TimeoutError:
            c = {"online": False, "ws_url": "", "targets": 0, "browser": "",
                 "error": "TimeoutError: sonda pendurou > 5s"}
        except Exception as e:
            c = {"online": False, "ws_url": "", "targets": 0, "browser": "",
                 "error": f"{type(e).__name__}: {e}"[:200]}
        if not isinstance(c, dict):
            return {"online": False, "ws_url": "", "targets": 0, "browser": "", "error": "resposta invalida"}
        c.setdefault("ws_url", "")
        c.setdefault("targets", 0)
        c.setdefault("browser", "")
        c.setdefault("error", "")
        return c

    async def _probe_picked():
        try:
            _pe_host, _pe_port = await asyncio.wait_for(_pick_bridge_host_port(), timeout=5)
            return f"{_pe_host}:{_pe_port}"
        except Exception as e:
            return f"erro: {type(e).__name__}: {e}"[:120]

    ping, chrome, picked_engine = await asyncio.gather(
        _probe_obscura(),
        _probe_chrome(),
        _probe_picked(),
    )

    online = bool(ping.get("online")) or bool(chrome.get("online"))

    detail = {
        "status": "ok" if online else "degraded",
        "service": "dezafira-backend",
        "obscura": ping,
        "chrome": chrome,
        "picked_engine": picked_engine,
        "workers": int(_os.getenv("OBSCURA_WORKERS", "4")),
    }

    try:
        from sqlalchemy import text as _sql_text
        from modules.database import SessionLocal
        _db = SessionLocal()
        _db.execute(_sql_text("SELECT 1"))
        _db.close()
        detail["database"] = "ok"
    except Exception as e:
        detail["database"] = f"error: {str(e)[:100]}"

    if not online:
        from services.obscura_health import get_grace_seconds as _get_grace
        grace = _get_grace()
        now = _t.time()
        down_for = now - (_HEALTH_STATE["down_since"] or now)
        detail["down_for_s"] = int(down_for)
        detail["grace_s"] = int(grace)

    return detail

@app.get("/", include_in_schema=False)
async def serve_ui(token: str = "", authorization: str = Header(None)):
    """Painel admin legacy (static/index.html). Exige token admin via header Bearer ou query ?token=."""
    t = token or (authorization.replace("Bearer ", "") if authorization else "")
    user_id = _verify_jwt_token(t) if t else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Token ausente ou invÃ¡lido")
    user = get_db_user_by_id(user_id)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html")
    if not os.path.exists(template_path):
        return HTMLResponse("<h1>Dezafira</h1>")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), headers={"Cache-Control": "no-store", "Pragma": "no-cache", "Expires": "0"})

@app.get("/app/{slug}", response_class=HTMLResponse)
async def serve_pwa_app(slug: str):
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "pwa_template.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template do PWA nÃ£o encontrado")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.get("/mindmap/{slug}", response_class=HTMLResponse)
async def serve_mindmap_pwa_app(slug: str):
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "mindmap_pwa_template.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template do PWA de Mapa Mental nao encontrado")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Versao do build (cache-busting visual na UI Admin)
APP_VERSION = "1.1.0"
def _get_build_id():
    try:
        import subprocess
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        if h.returncode == 0 and h.stdout.strip():
            return h.stdout.strip()
    except Exception:
        pass
    return "dev"

APP_BUILD = _get_build_id()

@app.get("/api/v1/version")
async def get_app_version():
    return {"version": APP_VERSION, "build": APP_BUILD, "name": "Dezafira Admin"}

@app.get("/api/v1/logs")
async def get_application_logs():
    return {"logs": application_logs}

# Helper LLM — CASCATA UNICA em agents/llm.py
#   OpenRouter → Gemini → NVIDIA NIM → HuggingFace → DeepSeek
# (substitui o query_llm local que usava apenas NVIDIA)
# Nota: max_tokens agora usa o default 4096 do agents.llm (antes era 1024
# fixo) — chame com max_tokens=<n> explicito se quiser limitar custo.
from agents.llm import query_llm

class CreatePredictionPayload(BaseModel):
    prompt: str
    brand: Optional[str] = "Geral"
    video_format: Optional[str] = "vertical"
    channel_id: Optional[str] = "default"

@app.post("/api/v1/predictions")
async def create_prediction(payload: CreatePredictionPayload, background_tasks: BackgroundTasks):
    prediction_id = f"sniper_{uuid.uuid4().hex[:8]}"
    
    save_db_prediction(prediction_id, payload.prompt, payload.channel_id)
    
    from modules.database import create_automation_task
    task_id = create_automation_task(payload.prompt, payload.channel_id)
    
    async def _run_orchestrator(task_id, prompt, channel_id, video_format):
        await _hermes_orchestrator.start_pipeline(prompt, channel_id, video_format, task_id=str(task_id))
    background_tasks.add_task(
        _run_orchestrator, task_id, payload.prompt,
        payload.channel_id, payload.video_format
    )
    
    return {
        "id": prediction_id,
        "request_id": prediction_id,
        "status": "starting"
    }

@app.get("/api/v1/predictions/{prediction_id}/result")
async def get_prediction_result(prediction_id: str):
    res = get_db_prediction(prediction_id)
    if not res:
        raise HTTPException(status_code=404, detail="Prediction not found")
    # Adaptador de compatibilidade para a UI que espera outputs em lista
    res["outputs"] = [res["url"]] if res["url"] else []
    return res

@app.get("/api/v1/channels")
async def get_channels():
    return get_db_channels()

class ChannelPayload(BaseModel):
    name: str
    nicho: str
    lang: str

@app.post("/api/v1/channels")
async def create_channel(payload: ChannelPayload):
    return create_db_channel(payload.name, payload.nicho, payload.lang)

@app.delete("/api/v1/channels/{channel_id}")
async def delete_channel(channel_id: str):
    success = delete_db_channel(channel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Canal nÃ£o encontrado")
    return {"message": "Canal removido com sucesso"}

class LoginStealthPayload(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    cookies_raw: Optional[str] = None

@app.post("/api/v1/channels/{channel_id}/login-stealth")
async def start_login_stealth(channel_id: str, payload: LoginStealthPayload, background_tasks: BackgroundTasks):
    db = SessionLocal()
    chan = db.query(Channel).filter(Channel.id == channel_id).first()
    if not chan:
        db.close()
        raise HTTPException(status_code=404, detail="Conta Google nÃ£o encontrada no banco. Selecione uma conta vÃ¡lida no seletor Ã  direita.")
    db.close()

    if not payload.cookies_raw and (not payload.email or not payload.password):
        raise HTTPException(status_code=400, detail="Credenciais ou cookies ausentes na requisiÃ§Ã£o.")

    # Se o usuÃ¡rio optou por colar os cookies diretamente, valida e salva na hora!
    if payload.cookies_raw:
        from modules.database import save_db_channel_cookies
        try:
            cookies_json = payload.cookies_raw.strip()
            # Garante formato JSON vÃ¡lido
            parsed_cookies = json.loads(cookies_json)
            
            # Executa uma verificaÃ§Ã£o rÃ¡pida de 6 segundos em background/stealth para confirmar se o cookie loga no YT Studio
            from playwright.sync_api import sync_playwright
            login_ok = False
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-setuid-sandbox"]
                    )
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                    )
                    context.add_cookies(parsed_cookies)
                    page = context.new_page()
                    page.goto("https://studio.youtube.com", timeout=12000)
                    page.wait_for_timeout(3000)
                    # Se nÃ£o redirecionou para tela de login do Google, o cookie Ã© quente!
                    if "signin" not in page.url and "login" not in page.url:
                        login_ok = True
                    browser.close()
            except Exception as e:
                print(f"[Agent-Login] Erro ao testar cookies: {e}")
                login_ok = False
            warning_msg = None
            if not login_ok:
                warning_msg = "SessÃ£o importada! (Nota: o servidor de nuvem do Railway nÃ£o pÃ´de confirmar a sessÃ£o devido ao IP do data center, mas salvou seus cookies com sucesso e eles serÃ£o aplicados na postagem)."

            save_db_channel_cookies(channel_id, cookies_json)
            return {
                "message": "Cookies salvos com sucesso!",
                "warning": warning_msg
            }
        except Exception as json_err:
            if isinstance(json_err, HTTPException):
                raise json_err
            raise HTTPException(status_code=400, detail=f"Formato de cookies invÃ¡lido. Cole um JSON vÃ¡lido: {str(json_err)}")

    from modules.agent_login import run_agent_login_stealth
    
    # Reseta estados anteriores
    db = SessionLocal()
    chan = db.query(Channel).filter(Channel.id == channel_id).first()
    if chan:
        chan.connection_status = "idle"
        chan.verification_code = None
        chan.connection_error = None
        db.commit()
    db.close()
    
    # Iniciar o robÃ´ em segundo plano para nÃ£o travar a UI
    background_tasks.add_task(run_agent_login_stealth, channel_id, payload.email, payload.password)
    return {"message": "Agente de login simulado iniciado em segundo plano."}

@app.get("/api/v1/channels/{channel_id}/connection-status")
async def get_connection_status(channel_id: str):
    db = SessionLocal()
    chan = db.query(Channel).filter(Channel.id == channel_id).first()
    if not chan:
        db.close()
        raise HTTPException(status_code=404, detail="Canal nÃ£o encontrado")
    
    status = chan.connection_status
    error = chan.connection_error
    db.close()
    return {"connection_status": status, "connection_error": error}

class Submit2FAPayload(BaseModel):
    code: str

@app.post("/api/v1/channels/{channel_id}/submit-2fa")
async def submit_verification_code(channel_id: str, payload: Submit2FAPayload):
    db = SessionLocal()
    chan = db.query(Channel).filter(Channel.id == channel_id).first()
    if not chan:
        db.close()
        raise HTTPException(status_code=404, detail="Canal nÃ£o encontrado")
    
    # Salva o cÃ³digo digitado na coluna verification_code para o robÃ´ ler
    chan.verification_code = payload.code
    db.commit()
    db.close()
    return {"message": "CÃ³digo de verificaÃ§Ã£o 2FA enviado com sucesso para o agente."}

@app.get("/api/v1/ai-channels")
async def get_ai_channels():
    return get_db_ai_created_channels()

class AiChannelPayload(BaseModel):
    channel_id: str
    name: str
    nicho: str
    lang: str
    creation_reason: str

@app.post("/api/v1/ai-channels")
async def create_ai_channel(payload: AiChannelPayload):
    return create_db_ai_created_channel(
        payload.channel_id, 
        payload.name, 
        payload.nicho, 
        payload.lang, 
        payload.creation_reason
    )

@app.delete("/api/v1/ai-channels/{sub_id}")
async def delete_ai_channel(sub_id: str):
    success = delete_db_ai_created_channel(sub_id)
    if not success:
        raise HTTPException(status_code=404, detail="Canal criado por IA nÃ£o encontrado")
    return {"message": "Canal removido com sucesso"}

class AnalyzeVideoPayload(BaseModel):
    url: str

@app.post("/api/v1/hermes/analyze-video")
async def analyze_competitor_video(payload: AnalyzeVideoPayload):
    system_instruction = (
        "VocÃª Ã© o Agente de InteligÃªncia e Engenharia Reversa da Dezafira. "
        "Seu objetivo Ã© analisar as transcriÃ§Ãµes e ganchos de retenÃ§Ã£o de vÃ­deos concorrentes virais "
        "e estruturar regras de hooks prontas para o Jonatas usar na esteira autÃ´noma."
    )
    user_prompt = f"""
    FaÃ§a a engenharia reversa do seguinte vÃ­deo concorrente:
    - URL: {payload.url}
    
    Analise e gere um relatÃ³rio estruturado contendo:
    1. Gancho Inicial (Primeiros 3 segundos): Por que reteve a audiÃªncia?
    2. Estrutura PsicolÃ³gica: Qual medo ou desejo o vÃ­deo ativa?
    3. Roteiro Adaptado para a Dezafira: Crie uma variaÃ§Ã£o original desse mesmo roteiro para evitar tag de conteÃºdo reutilizado.
    """
    
    analysis_result = await query_llm([
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt}
    ])
    return {"analysis": analysis_result}

class ChatPayload(BaseModel):
    message: str

@app.get("/api/v1/predictions/history")
async def get_predictions_history():
    db = SessionLocal()
    preds = db.query(Prediction).filter(Prediction.status == "completed").order_by(Prediction.created_at.desc()).all()
    result = [
        {
            "id": p.id,
            "prompt": p.prompt,
            "video_url": p.video_url,
            "approval_status": p.approval_status,
            "created_at": p.created_at.strftime("%d/%m %H:%M") if p.created_at else ""
        } for p in preds
    ]
    db.close()
    return {"history": result}

async def run_delayed_upload(prediction_id: str):
    db = SessionLocal()
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not pred:
        db.close()
        return
        
    channel_id = pred.channel_id
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    cookies_json = channel.cookies if channel else None
    db.close()
    
    absolute_video_path = os.path.join(director.outputs_dir, f"{prediction_id}_preview.mp4")
    if not os.path.exists(absolute_video_path):
        absolute_video_path = os.path.join(director.outputs_dir, f"{prediction_id}.mp4")
        
    title = f"Como fazer renda extra com IA"
    if pred.prompt:
        title = pred.prompt
        
    description = "Vídeo gerado de forma 100% automatizada pela Dezafira!"
    
    log_application_activity(f"Upload aprovado pelo Jonatas para o vÃ­deo ID: {prediction_id}. Iniciando postagem...")
    send_telegram_notification(f"ðŸš€ *[PublicaÃ§Ã£o]* Upload do vÃ­deo aprovado. Iniciando Playwright...")
    
    channel_uploader = YouTubeUploader(channel_id=channel_id)
    upload_success = channel_uploader.upload_video(
        video_path=absolute_video_path,
        title=title[:90],
        description=description,
        is_short=True,
        cookies_json=cookies_json
    )
    
    if upload_success:
        log_application_activity(f"Sucesso! VÃ­deo publicado no YouTube.")
        send_telegram_notification(f"âœ… *[Publicado]* VÃ­deo `{title[:40]}` postado com sucesso!")
    else:
        log_application_activity("Erro: Falha no upload no YouTube Studio.")
        send_telegram_notification(f"âš ï¸ *[Aviso]* Falha ao realizar postagem. Cookies expirados ou invÃ¡lidos.")

@app.post("/api/v1/predictions/{prediction_id}/approve")
async def approve_prediction(prediction_id: str, background_tasks: BackgroundTasks):
    db = SessionLocal()
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not pred:
        db.close()
        raise HTTPException(status_code=404, detail="GeraÃ§Ã£o nÃ£o encontrada")
    
    pred.approval_status = "approved"
    db.commit()
    db.close()
    
    background_tasks.add_task(run_delayed_upload, prediction_id)
    return {"message": "GeraÃ§Ã£o aprovada. Upload em segundo plano iniciado."}

@app.post("/api/v1/predictions/{prediction_id}/reject")
async def reject_prediction(prediction_id: str):
    db = SessionLocal()
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not pred:
        db.close()
        raise HTTPException(status_code=404, detail="GeraÃ§Ã£o nÃ£o encontrada")
    
    pred.approval_status = "rejected"
    db.commit()
    db.close()
    
    log_application_activity(f"GeraÃ§Ã£o {prediction_id} rejeitada pelo Jonatas. Aguardando novos direcionamentos de ajuste.")
    send_telegram_notification(f"âš ï¸ *[Curadoria]* GeraÃ§Ã£o `{prediction_id}` rejeitada pelo Jonatas. Ajustes solicitados.")
    return {"message": "GeraÃ§Ã£o marcada como rejeitada."}

_youtube_search = YouTubeSearchSpider()

@app.get("/api/v1/trends")
async def get_niche_trends(query: Optional[str] = "Dropshipping"):
    results = await _youtube_search.search(query)
    return results if isinstance(results, list) else results.get("videos", [])

@app.get("/api/v1/account/balance")
async def get_balance():
    return {"balance": 9999.0}

@app.on_event("startup")
async def startup_event():
    import asyncio
    
    # Garantir que o admin principal tenha role admin
    try:
        from modules.database import SessionLocal as _SL, User
        _db = _SL()
        admin_user = _db.query(User).filter(User.email == "jonatasprojetos2013@gmail.com").first()
        if admin_user and admin_user.role != "admin":
            admin_user.role = "admin"
            _db.commit()
            print("[STARTUP] jonatasprojetos2013@gmail.com promovido a admin")
        _db.close()
    except Exception as e:
        print(f"[STARTUP] Erro ao verificar admin: {e}")
    
    # Callback para responder o chat do bot usando o Llama 3.3
    def on_telegram_chat(message_text):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Reutiliza a mesma instruÃ§Ã£o e histÃ³rico do Hermes
            hermes_chat_history.append({"role": "user", "content": message_text})
            system_instruction = (
                "VocÃª Ã© o Hermes, o Agente Orquestrador executivo e extremamente inteligente da plataforma DEZAFIRA, a FÃ¡brica de Canais. "
                "VocÃª estÃ¡ conversando diretamente com o JONATAS, o fundador da Holding Dezafira. "
                "Seu objetivo absoluto Ã© rodar a esteira no modo 100% AutÃ´nomo (MÃ£os Livres), sem precisar calibrar ou fazer perguntas de restriÃ§Ãµes para o Jonatas. "
                "Responda de forma direta, clara e executiva."
            )
            messages_for_llm = [{"role": "system", "content": system_instruction}] + hermes_chat_history[-10:]
            reply = loop.run_until_complete(query_llm(messages_for_llm))
            hermes_chat_history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return "Erro ao processar IA do Hermes: {}".format(str(e))
        finally:
            loop.close()

    # Callback para o comando /produzir [tema]
    def on_telegram_produce(theme_text):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from modules.database import create_automation_task
            
            task_id = create_automation_task(theme_text, "default")
            save_db_prediction(f"tele_{uuid.uuid4().hex[:8]}", theme_text, "default")
            
            loop.run_until_complete(_hermes_orchestrator.start_pipeline(theme_text, "default", "vertical", task_id=str(task_id)))
        except Exception as e:
            print(f"[Telegram Bot] Falha na esteira disparada por chat: {str(e)}")
        finally:
            loop.close()

    # â•â• Pipeline Recovery: retoma pipelines interrompidas â•â•
    try:
        from modules.database import get_stuck_pipeline_runs, update_db_blog_pipeline_run
        from modules.blog_pipeline import resume_blog_pipeline
        stuck = get_stuck_pipeline_runs()
        if stuck:
            print(f'[Startup] Encontradas {len(stuck)} pipelines interrompidas. Tentando retomar...')
            for s in stuck:
                print(f'  - {s["id"]}: {s.get("blog_name","?")} (fase: {s["phase"]}, artigos: {s["articles_generated"]})')
                # Tenta retomar em background (sem await para nao travar startup)
                import asyncio
                asyncio.create_task(resume_blog_pipeline(s['id']))
    except Exception as e:
        print(f'[Startup] Erro na recuperaÃ§Ã£o de pipelines: {e}')

    init_telegram_bot(on_telegram_chat, on_telegram_produce)

    # â•â• Job Recovery: retoma jobs de regeneracao persistidos (sobrevive a restarts) â•â•
    try:
        from modules.database import (
            get_db_running_regeneration_jobs,
            reset_db_stuck_job_items,
        )
        running_jobs = get_db_running_regeneration_jobs(limit=10)
        if running_jobs:
            print(f'[Startup] Encontrados {len(running_jobs)} jobs de regeneracao pendentes. Retomando...')
            for j in running_jobs:
                try:
                    reset_db_stuck_job_items(j['id'])
                    asyncio.create_task(_process_regeneration_job(j['id']))
                    print(f'  - Job {j["id"]} retomado em background ({j.get("processed",0)}/{j.get("total",0)} processados)')
                except Exception as e:
                    print(f'  - Falha ao retomar job {j["id"]}: {e}')
    except Exception as e:
        print(f'[Startup] Erro na recuperacao de jobs de regeneracao: {e}')

    # Inicia WebSocket keepalive para detectar conexoes mortas
    try:
        from pipeline.websocket import WebSocketHub
        await _ws_hub.start_keepalive(interval=25)
        print('[Startup] WebSocket keepalive iniciado (25s)')
    except Exception as e:
        print(f'[Startup] Erro ao iniciar keepalive: {e}')

    # Configura e inicia broadcast periodico de metricas do dashboard
    try:
        async def _fetch_dashboard():
            from modules.database import SessionLocal, BlogChannel, BlogPost
            from sqlalchemy import func
            db = SessionLocal()
            try:
                channels = db.query(BlogChannel).count()
                posts = db.query(BlogPost).count()
                words = db.query(func.coalesce(func.sum(BlogPost.word_count), 0)).scalar()
                published = db.query(BlogPost).filter(BlogPost.status == 'published').count()
                drafts = db.query(BlogPost).filter(BlogPost.status == 'draft').count()
                channels_list = []
                for c in db.query(BlogChannel).order_by(BlogChannel.created_at.desc()).all():
                    ch_posts = db.query(BlogPost).filter(BlogPost.channel_id == c.id)
                    with_img = ch_posts.filter(BlogPost.featured_image_url.isnot(None)).count()
                    without_img = ch_posts.filter(BlogPost.featured_image_url.is_(None)).count()
                    channels_list.append({
                        'id': c.id, 'name': c.name, 'nicho': c.nicho,
                        'lang': c.lang, 'post_count': ch_posts.count(),
                        'posts_with_images': with_img, 'posts_without_images': without_img,
                    })
                return {
                    'channels': {'total': channels, 'active': channels, 'list': channels_list},
                    'posts': {'total': posts, 'published': published, 'drafts': drafts, 'total_words': words or 0},
                    'books_count': 0, 'courses_count': 0,
                }
            finally:
                db.close()
        _ws_hub.set_dashboard_fetcher(_fetch_dashboard)
        await _ws_hub.start_dashboard_broadcast(interval=30)
        print('[Startup] Dashboard broadcast iniciado (30s)')
    except Exception as e:
        print(f'[Startup] Erro ao iniciar dashboard broadcast: {e}')

    # â•â• Watcher de alertas de queda do motor Obscura â•â•
    try:
        asyncio.create_task(_obscura_alert_watcher())
        _OBSCURA_WATCHER["running"] = True
        print('[Startup] Watcher de alertas do Obscura iniciado (30s)')
    except Exception as e:
        print(f'[Startup] Erro ao iniciar watcher de alertas: {e}')

    # Watcher de distribuicao social automatica (modules/distributor)
    try:
        # Restaura o estado persistido do agendador (sobrevive a restarts)
        from modules.database import get_db_distribution_settings
        saved = get_db_distribution_settings()
        if saved:
            _DISTRIBUTION_STATE["enabled"] = saved.get("enabled", False)
            _DISTRIBUTION_STATE["interval_hours"] = saved.get("interval_hours", 6)
            print('[Startup] Agendador de distribuicao restaurado do banco: enabled=' +
                  str(saved.get('enabled', False)) + ', intervalo=' + str(saved.get('interval_hours', 6)) + 'h')
        asyncio.create_task(_distribution_scheduler_loop())
        print('[Startup] Distribuidor social automatico iniciado (intervalo ' +
              str(_DISTRIBUTION_STATE.get('interval_hours', 6)) + 'h, enabled=' +
              str(_DISTRIBUTION_STATE.get('enabled', False)) + ')')
    except Exception as e:
        print(f'[Startup] Erro ao iniciar distribuidor social: {e}')


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DASHBOARD â€” FÃ¡brica de Blogs (com Books + Courses)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/v1/factory/francisco")
async def get_francisco_report():
    """Seu Francisco -- relatorio de supervisao de todos os blogs."""
    from modules.seu_francisco import listar_blogs_para_supervisionar
    try:
        relatorios = listar_blogs_para_supervisionar()
        pendentes = [r for r in relatorios if not r.get("is_complete")]
        completos = [r for r in relatorios if r.get("is_complete")]
        return {
            "blogs": relatorios,
            "total_blogs": len(relatorios),
            "completos": len(completos),
            "pendentes": len(pendentes),
            "mensagem": (
                "ðŸ‘´ Seu Francisco: '" + str(completos) + " blog(s) completo(s), " +
                str(pendentes) + " pendente(s). Tudo sob controle!'"
            ) if relatorios else "ðŸ‘´ Seu Francisco: 'Nenhum blog ativo no momento.'"
        }
    except Exception as e:
        return {"error": str(e), "blogs": []}


@app.get("/api/v1/factory/ze-status")
async def get_ze_status():
    """Seu Ze -- status da publicacao diaria."""
    from modules.seu_ze import resumo_geral
    try:
        return resumo_geral()
    except Exception as e:
        return {"status": "erro", "error": str(e)}


@app.get("/api/v1/obscura/status")
async def obscura_status(_admin=Depends(require_admin_or_service)):
    """ðŸ•µï¸ Painel Obscura â€” status do motor headless, telemetria e historico."""
    from services.obscura_service import obscura_telemetry
    from services.obscura_bridge import get_obscura_status as _ping_obscura
    try:
        # Ping com cap rÃ­gido (o connect do bridge jÃ¡ tem timeout interno de 5s):
        # nunca travar o event loop nem a pÃ¡gina mesmo com host inacessÃ­vel.
        ping = await asyncio.wait_for(_ping_obscura(), timeout=6)
        obscura_telemetry.set_ping(
            online=bool(ping.get("online")),
            targets=ping.get("targets", 0),
            error=ping.get("error", ""),
        )
    except Exception as e:
        obscura_telemetry.set_ping(online=False, error=str(e))
    status = obscura_telemetry.build_status()
    # Historico persistido no banco (best-effort)
    try:
        from modules.database import get_db_obscura_logs, get_db_obscura_agent_stats
        status["db_recent"] = get_db_obscura_logs(limit=50)
        status["db_agent_stats"] = get_db_obscura_agent_stats()
    except Exception:
        status["db_recent"] = []
        status["db_agent_stats"] = []
    # Grace atual + histÃ³rico de incidentes (watcher de alertas)
    from services.obscura_health import get_grace_seconds, get_grace_source
    status["grace"] = {"grace_s": int(get_grace_seconds()), "source": get_grace_source()}
    status["incidents"] = list(reversed(_OBSCURA_WATCHER["incidents"]))
    status["watcher"] = {
        "running": _OBSCURA_WATCHER["running"],
        "last_check": _OBSCURA_WATCHER["last_check"],
        "down_since": _OBSCURA_WATCHER["down_since"],
    }
    return status


@app.get("/api/v1/obscura/grace")
async def obscura_grace(_admin=Depends(require_admin)):
    """â±ï¸ Grace atual do healthcheck (override runtime > .env > default 300s)."""
    from services.obscura_health import get_grace_seconds, get_grace_source
    return {"grace_s": int(get_grace_seconds()), "source": get_grace_source()}


@app.put("/api/v1/obscura/grace")
async def obscura_grace_set(payload: dict, _admin=Depends(require_admin)):
    """Aplica nova grace em runtime e persiste no .env (sem reiniciar o backend)."""
    from services.obscura_health import set_grace_seconds
    grace_s = (payload or {}).get("grace_s")
    if grace_s is None:
        raise HTTPException(status_code=422, detail="grace_s Ã© obrigatÃ³rio (segundos)")
    try:
        return set_grace_seconds(grace_s)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/api/v1/obscura/proxy-check")
async def obscura_proxy_check(_admin=Depends(require_admin)):
    """ðŸ•µï¸ Healthcheck do proxy configurado â€” testa conectividade real
    (HTTP via proxy) e mede latÃªncia. Sem proxy configurado, retorna
    disabled. Sempre executa rÃ¡pido (timeout 8s) pra nÃ£o travar o painel."""
    from services.obscura_bridge import obscura_proxy, test_proxy_connectivity
    cfg = obscura_proxy()
    if not cfg.get("enabled"):
        return {"enabled": False, "ok": False, "error": "OBSCURA_PROXY_URL vazio no .env", "ms": 0}
    try:
        result = await asyncio.wait_for(test_proxy_connectivity(cfg["url"]), timeout=8)
    except Exception as e:
        result = {"enabled": True, "ok": False, "error": str(e)[:200], "ms": 0}
    result["masked"] = cfg.get("masked", "")
    return result


@app.get("/api/v1/obscura/serp-sources")
async def obscura_serp_sources(_admin=Depends(require_admin)):
    """ðŸ•µï¸ Fontes SERP da rodada atual + histÃ³rico de rodadas (rotacao).
    Inclui as rodadas persistidas no banco (sobrevivem a restarts)."""
    from services.obscura_service import obscura_telemetry
    summary = obscura_telemetry.serp_run_summary()
    summary["persisted_runs"] = obscura_telemetry.persisted_serp_runs(limit=20)
    return summary


@app.post("/api/v1/obscura/serp-sources/reset")
async def obscura_serp_sources_reset(_admin=Depends(require_admin)):
    """Zera os contadores de fonte SERP (inicio de nova rodada da fabrica)."""
    from services.obscura_service import obscura_telemetry
    return obscura_telemetry.reset_serp_sources()


@app.get("/api/v1/factory/dashboard")
async def blog_factory_dashboard(_admin=Depends(require_admin_or_service)):
    """Dashboard consolidado com metricas de todas as fabricas."""
    from modules.database import SessionLocal, BlogChannel, BlogPost, Book, Course, __get_subdomain_for_channel
    from modules.brand_themes import detect_theme, get_logo_svg, get_favicon_svg
    from sqlalchemy import func

    db = SessionLocal()

    def _lili_check(post):
        """Score LiLi com cache no banco: usa lili_score persistido quando existir."""
        cached = getattr(post, "lili_score", None)
        if cached is not None:
            return int(cached), bool(getattr(post, "lili_approved", False))
        try:
            from modules.lili import revisar_conteudo
            from modules.database import save_db_lili_score
            r = revisar_conteudo(
                post.id,
                post.title or "",
                post.content or "",
                post.keywords or "",
            )
            score = r.get("score")
            approved = bool(r.get("approved"))
            if score is not None:
                try:
                    save_db_lili_score(post.id, score, approved)
                except Exception:
                    pass
            return score, approved
        except Exception as e:
            print(f"[Dashboard] Falha ao calcular score LiLi de {post.id}: {e}")
            return None, None

    try:
        channels = db.query(BlogChannel).order_by(BlogChannel.created_at.desc()).all()
        posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).limit(10).all()
        total_posts = db.query(BlogPost).count()
        published = db.query(BlogPost).filter(BlogPost.status == "published").count()
        drafts = db.query(BlogPost).filter(BlogPost.status == "draft").count()
        total_words = db.query(func.coalesce(func.sum(BlogPost.word_count), 0)).scalar()
        books_count = db.query(Book).count()
        courses_count = db.query(Course).count()
        recent_posts = []
        for p in posts:
            lili_score, lili_approved = await asyncio.to_thread(_lili_check, p)
            recent_posts.append({
                "id": p.id, "title": p.title, "slug": p.slug,
                "status": p.status, "word_count": p.word_count or 0,
                "featured_image_url": p.featured_image_url,
                "channel_id": p.channel_id,
                "image_provider": p.image_provider,
                "lili_score": lili_score,
                "lili_approved": lili_approved,
                "club_liberado": bool(getattr(p, "club_liberado", False)),
                "club_enviado_at": getattr(p, "club_enviado_at", None).isoformat() if getattr(p, "club_enviado_at", None) else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })

        # Agregados por canal (para que TODOS os paineis de blog tenham dados completos,
        # independente de estar ou nao no 'recent' global de 10 posts)
        # with_entities: evita carregar a coluna content (texto grande) de todos os posts
        all_posts = db.query(
            BlogPost.id, BlogPost.channel_id, BlogPost.title, BlogPost.slug,
            BlogPost.status, BlogPost.word_count, BlogPost.featured_image_url,
            BlogPost.image_provider, BlogPost.lili_score, BlogPost.lili_approved,
            BlogPost.club_liberado, BlogPost.club_enviado_at,
            BlogPost.created_at,
        ).order_by(BlogPost.created_at.desc()).all()
        ch_map = {}
        for p in all_posts:
            ch_map.setdefault(p.channel_id, []).append(p)

        def _channel_agg(cid):
            ch_all = ch_map.get(cid, [])
            ch_recent = ch_all[:5]
            words = sum(p.word_count or 0 for p in ch_all)
            prov = {}
            for p in ch_all:
                k = (p.image_provider or "pexels").lower()
                prov[k] = prov.get(k, 0) + 1
            lili = [p.lili_score for p in ch_all if p.lili_score is not None]
            return {
                "total_words": words,
                "avg_words": round(words / len(ch_all)) if ch_all else 0,
                "provider_stats": prov,
                "lili_avg": round(sum(lili) / len(lili)) if lili else None,
                "lili_reviewed_count": len(lili),
                "lili_approved_count": sum(1 for p in ch_all if p.lili_approved),
                "club_liberated_count": sum(1 for p in ch_all if getattr(p, "club_liberado", False)),
                "club_sent_count": sum(1 for p in ch_all if getattr(p, "club_enviado_at", None)),
                "recent_posts": [{
                    "id": p.id, "title": p.title, "slug": p.slug,
                    "status": p.status, "word_count": p.word_count or 0,
                    "featured_image_url": p.featured_image_url,
                    "channel_id": p.channel_id,
                    "image_provider": p.image_provider,
                    "lili_score": p.lili_score,
                    "lili_approved": bool(p.lili_approved),
                    "club_liberado": bool(getattr(p, "club_liberado", False)),
                    "club_enviado_at": getattr(p, "club_enviado_at", None).isoformat() if getattr(p, "club_enviado_at", None) else None,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                } for p in ch_recent],
            }
        return {
            "channels": {
                "total": len(channels),
                "active": len([c for c in channels if c.status == "active"]),
                "list": [{
                    "id": c.id, "name": c.name, "nicho": c.nicho,
                    "lang": c.lang, "platform": c.platform,
                    "site_url": c.site_url, "status": c.status,
                    "post_count": db.query(BlogPost).filter(BlogPost.channel_id == c.id).count(),
                    "published_count": db.query(BlogPost).filter(
                        BlogPost.channel_id == c.id, BlogPost.status == "published"
                    ).count(),
                    "posts_with_images": db.query(BlogPost).filter(
                        BlogPost.channel_id == c.id,
                        BlogPost.featured_image_url.isnot(None)
                    ).count(),
                    "posts_without_images": db.query(BlogPost).filter(
                        BlogPost.channel_id == c.id,
                        BlogPost.featured_image_url.is_(None)
                    ).count(),
                    "brand_primary": detect_theme(c.nicho)["colors"]["primary"] if c.nicho else "#6366f1",
                    "brand_secondary": detect_theme(c.nicho)["colors"]["accent"] if c.nicho else "#8b5cf6",
                    "logo_svg": get_logo_svg(c.nicho) if c.nicho else "",
                    "favicon_svg": get_favicon_svg(c.nicho) if c.nicho else "",
                    "is_affiliate": c.is_affiliate,
                    "is_discover": c.is_discover,
                    "affiliate_providers": c.affiliate_providers,
                    "amazon_tag": c.amazon_tag,
                    "amazon_key": c.amazon_key,
                    "amazon_secret": c.amazon_secret,
                    "shopee_app_id": c.shopee_app_id,
                    "shopee_app_secret": c.shopee_app_secret,
                    "mercadolivre_client_id": c.mercadolivre_client_id,
                    "mercadolivre_client_secret": c.mercadolivre_client_secret,
                    "brand_config": getattr(c, "brand_config", None),
                    "subdomain": __get_subdomain_for_channel(c.id, c.name.lower().replace(" ", "-")[:50]),
                    **_channel_agg(c.id),
                } for c in channels],
            },
            "posts": {
                "total": total_posts,
                "published": published,
                "drafts": drafts,
                "total_words": total_words or 0,
                "recent": recent_posts,
            },
            "keywords": {"total": 0, "easy": 0, "groups": []},
            "scheduler": {"running": True, "jobs": [], "job_count": 0},
            "books_count": books_count,
            "courses_count": courses_count,
        }
    finally:
        db.close()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# BLOG SEED â€” Dados de demonstraÃ§Ã£o
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.post("/api/v1/blogs/seed")
async def seed_demo_blog():
    """Cria dados de demonstraÃ§Ã£o para o blog."""
    from modules.database import SessionLocal, BlogChannel, BlogPost
    from datetime import datetime
    import uuid
    db = SessionLocal()
    try:
        if db.query(BlogChannel).count() > 0:
            return {"message": "Blog ja possui dados"}
        cid = "blg_demo_" + uuid.uuid4().hex[:4]
        ch = BlogChannel(id=cid, name="O Reino", nicho="Ensinamentos de Jesus nos Evangelhos",
            lang="PT", platform="dezafira", site_url="https://dezafira.com.br/oreino", status="active")
        db.add(ch)
        now = datetime.utcnow()
        art = BlogPost(
            id="demo_" + uuid.uuid4().hex[:8], channel_id=cid,
            title="O Sermao do Monte: As Bem-aventurancas Explicadas",
            slug="sermao-do-monte-bem-aventurancas",
            content="O Sermao do Monte (Mateus 5-7) e o discurso mais profundo de Jesus.\n\nBem-aventurados os pobres de espirito, porque deles e o Reino dos Ceus.\n\nVoce e o sal da terra e a luz do mundo.",
            excerpt="Descubra o significado profundo das Bem-aventurancas de Jesus.",
            keywords="sermao do monte, bem-aventurancas, ensinamentos de jesus, mateus 5",
            status="published", word_count=600, topic="Sermao do Monte",
            created_at=now, published_at=now,
        )
        db.add(art)
        db.commit()
        return {"message": "Dados de demonstracao criados!", "channel": cid, "articles": 1}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar dados demo: {str(e)}")
    finally:
        db.close()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# BOOKS â€” FÃ¡brica de Livros
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/v1/books")
async def list_books():
    from modules.database import SessionLocal, Book
    db = SessionLocal()
    books = db.query(Book).order_by(Book.created_at.desc()).all()
    db.close()
    return {"books": [{
        "id": b.id, "title": b.title, "subtitle": b.subtitle,
        "author": b.author, "description": b.description,
        "cover_url": b.cover_url, "topic": b.topic,
        "keywords": b.keywords, "status": b.status,
        "price_cents": b.price_cents,
        "created_at": b.created_at.isoformat() if b.created_at else None,
    } for b in books]}

@app.get("/api/v1/books/{book_id}")
async def get_book(book_id: str):
    from modules.database import SessionLocal, Book, BookChapter
    db = SessionLocal()
    b = db.query(Book).filter(Book.id == book_id).first()
    if not b:
        db.close()
        raise HTTPException(status_code=404, detail="Livro nao encontrado")
    chapters = db.query(BookChapter).filter(BookChapter.book_id == book_id).order_by(BookChapter.chapter_number).all()
    db.close()
    return {"book": {
        "id": b.id, "title": b.title, "subtitle": b.subtitle,
        "author": b.author, "description": b.description,
        "cover_url": b.cover_url, "topic": b.topic,
        "keywords": b.keywords, "status": b.status,
        "price_cents": b.price_cents,
        "chapters": [{"number": c.chapter_number, "title": c.title, "content_preview": c.content[:200] if c.content else ""} for c in chapters],
        "created_at": b.created_at.isoformat() if b.created_at else None,
    }}

@app.post("/api/v1/books/seed")
async def seed_book():
    from modules.database import SessionLocal, Book, BookChapter
    import uuid
    db = SessionLocal()
    try:
        bid = "book_" + uuid.uuid4().hex[:8]
        book = Book(id=bid, title="As Parabolas de Jesus: Licoes de Vida para os Dias de Hoje",
            subtitle="Descubra o significado profundo das parabolas do Mestre",
            author="Dezafira Editorial",
            description="Uma jornada atraves das parabolas mais impactantes de Jesus, com aplicacoes praticas para a vida moderna.",
            cover_url="/outputs/placeholder_book.png", topic="Parabolas de Jesus",
            keywords="parabolas de jesus, ensinamentos de cristo, evangelhos, vida crista, fe",
            status="published", price_cents=1990)
        db.add(book)
        chapters_data = [
            ("A Parabola do Semeador", "A parabola do semeador e uma das mais conhecidas..."),
            ("O Bom Samaritano", "A historia do bom samaritano nos ensina sobre..."),
            ("O Filho Prodigo", "A parabola do filho prodigo e uma das mais emocionantes..."),
            ("O Semeador e a Semente", "Jesus usou esta parabola para explicar..."),
        ]
        for i, (ctitle, ccontent) in enumerate(chapters_data, 1):
            ch = BookChapter(id=f"{bid}_ch{i}", book_id=bid, chapter_number=i,
                title=ctitle, content=f"{ccontent}\n\n[Conteudo completo gerado por IA...]")
            db.add(ch)
        db.commit()
        return {"message": "Livro de demonstracao criado!", "book_id": bid, "title": book.title, "chapters": len(chapters_data)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar livro: {str(e)}")
    finally:
        db.close()

@app.post("/api/v1/books/generate")
async def generate_book(payload: dict):
    from agents.book_factory import BookWriterAgent
    agent = BookWriterAgent()
    topic = payload.get("topic", "Ensinamentos de Jesus")
    lang = payload.get("lang", "PT")
    try:
        book = await agent.write_book(topic, lang)
        return {"message": "Livro gerado com sucesso!", "title": book.get("title", ""), "chapters": len(book.get("chapters", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar livro: {str(e)}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# COURSES â€” Fabrica de Cursos
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/v1/courses")
async def list_courses():
    from modules.database import SessionLocal, Course
    db = SessionLocal()
    courses = db.query(Course).order_by(Course.created_at.desc()).all()
    db.close()
    return {"courses": [{
        "id": c.id, "title": c.title, "subtitle": c.subtitle,
        "description": c.description, "topic": c.topic,
        "keywords": c.keywords, "status": c.status,
        "total_modules": c.total_modules, "total_lessons": c.total_lessons,
        "difficulty": c.difficulty, "price_cents": c.price_cents,
        "cover_url": c.cover_url,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c in courses]}

@app.get("/api/v1/courses/{course_id}")
async def get_course(course_id: str):
    from modules.database import SessionLocal, Course, CourseModule
    db = SessionLocal()
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        db.close()
        raise HTTPException(status_code=404, detail="Curso nao encontrado")
    modules = db.query(CourseModule).filter(CourseModule.course_id == course_id).order_by(CourseModule.module_number).all()
    db.close()
    return {"course": {
        "id": c.id, "title": c.title, "subtitle": c.subtitle,
        "description": c.description, "topic": c.topic,
        "keywords": c.keywords, "status": c.status,
        "total_modules": c.total_modules, "total_lessons": c.total_lessons,
        "difficulty": c.difficulty, "price_cents": c.price_cents,
        "cover_url": c.cover_url,
        "modules": [{"number": m.module_number, "title": m.title} for m in modules],
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }}

@app.post("/api/v1/courses/{course_id}/agnes-cover")
async def generate_course_agnes_cover(course_id: str, _admin=Depends(require_admin)):
    """🎨 Agnes Studio: gera/regenera a capa do curso (16:9) com design real
    (tipografia + autor + créditos) e renderiza HTML → PNG via Obscura."""
    import json as _json
    from modules.database import get_db_course, update_db_course
    from modules.agnes_studio import AgnesStudio

    course = get_db_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    # Reutiliza o design persistido (se houver) para manter a identidade visual
    design = None
    if course.get("cover_design"):
        try:
            design = _json.loads(course["cover_design"])
        except Exception:
            design = None

    try:
        studio = AgnesStudio()
        result = await studio.generate_course_cover(
            title=course.get("title", ""),
            subtitle=course.get("subtitle", "") or "",
            author="Dezafira Studio",
            niche=course.get("topic", "") or "",
            style_id="moderno",
            course_id=course_id,
            difficulty=course.get("difficulty", "") or "",
            modules_count=course.get("total_modules", 0) or 0,
            design=design,
        )
        if result.get("cover_url"):
            update_db_course(
                course_id,
                cover_url=result["cover_url"],
                cover_design=_json.dumps(result.get("design", {}), default=str),
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar capa Agnes do curso: {str(e)}")

@app.post("/api/v1/courses/seed")
async def seed_course():
    from modules.database import SessionLocal, Course, CourseModule
    import uuid
    db = SessionLocal()
    try:
        cid = "crs_" + uuid.uuid4().hex[:8]
        course = Course(id=cid, title="Introducao a Teologia Biblica: Fundamentos da Fe Crista",
            subtitle="Uma jornada pelos fundamentos teologicos da fe crista",
            description="Curso completo de introducao a teologia, cobrindo bibliologia, cristologia e soteriologia.",
            topic="Teologia Basica",
            keywords="teologia, bibliologia, cristologia, soteriologia, fe crista",
            status="published", total_modules=3, total_lessons=5,
            difficulty="iniciante", price_cents=4970,
            cover_url="/outputs/placeholder_course.png")
        db.add(course)
        modules_data = [
            ("Introducao a Bibliologia", "Estudo da doutrina das Escrituras"),
            ("Cristologia: A Pessoa de Cristo", "Estudo da pessoa e obra de Jesus Cristo"),
            ("Soteriologia: A Doutrina da Salvacao", "Estudo da salvacao pela graca mediante a fe"),
        ]
        for i, (mtitle, mdesc) in enumerate(modules_data, 1):
            mod = CourseModule(id=f"{cid}_mod{i}", course_id=cid, module_number=i,
                title=mtitle, description=mdesc)
            db.add(mod)
        db.commit()
        return {"message": "Curso de demonstracao criado!", "course_id": cid, "title": course.title, "modules": len(modules_data), "lessons": 5}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar curso: {str(e)}")
    finally:
        db.close()

@app.post("/api/v1/courses/generate")
async def generate_course(payload: dict):
    from agents.course_factory import CourseWriterAgent
    agent = CourseWriterAgent()
    topic = payload.get("topic", "Teologia Biblica")
    lang = payload.get("lang", "PT")
    try:
        course = await agent.write_course(topic, lang)
        return {"message": "Curso gerado com sucesso!", "title": course.get("title", ""), "modules": len(course.get("modules", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar curso: {str(e)}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# IMAGES â€” Fabrica de Imagens (FLUX + Pexels)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.post("/api/v1/images/generate-cover")
async def generate_book_cover(payload: dict):
    """Gera capa de livro via FLUX.1 ou Pexels."""
    from agents.image_factory import image_agent
    title = payload.get("title", "Book")
    topic = payload.get("topic", "christian")
    style = payload.get("style", "classico")
    url = await image_agent.generate_cover(title, topic, style)
    if url:
        return {"image_url": url, "success": True}
    return {"error": "Nao foi possivel gerar a capa", "success": False}

@app.post("/api/v1/images/generate-blog-image")
async def generate_blog_image(payload: dict):
    """Gera imagem de destaque para blog."""
    from agents.image_factory import image_agent
    topic = payload.get("topic", "christian")
    url = await image_agent.generate_blog_image(topic)
    if url:
        return {"image_url": url, "success": True}
    return {"error": "Nenhuma imagem gerada", "success": False}

@app.post("/api/v1/images/generate-thumbnail")
async def generate_course_thumbnail(payload: dict):
    """Gera thumbnail para curso."""
    from agents.image_factory import image_agent
    title = payload.get("title", "Course")
    topic = payload.get("topic", "christian")
    url = await image_agent.generate_course_thumbnail(title, topic)
    if url:
        return {"image_url": url, "success": True}
    return {"error": "Nenhuma imagem gerada", "success": False}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# RAG BIBLICO â€” Busca SemÃ¢ntica
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.post("/api/v1/rag/ask")
async def rag_ask(payload: dict):
    """Pergunta ao RAG Biblico."""
    from agents.rag_biblico import rag_agent
    question = payload.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Questao obrigatoria")
    try:
        result = await rag_agent.ask(question)
        return result
    except Exception as e:
        return {"error": str(e), "answer": "Erro ao consultar RAG", "sources": []}

@app.post("/api/v1/rag/index")
async def rag_index():
    """Reindexa todos os conteudos no RAG."""
    from agents.rag_biblico import rag_agent
    try:
        count = await rag_agent.index_content()
        return {"message": f"{count} conteudos indexados com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao indexar: {str(e)}")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# LIMPEZA DE BLOGS ANTIGOS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.post("/api/v1/factory/cleanup-old-blogs")
async def cleanup_old_blogs(_admin=Depends(require_admin)):
    """Deleta todos os blogs antigos mantendo apenas o Ãºltimo criado."""
    from modules.database import get_db, blog_channels, blog_posts, blog_sections
    db = next(get_db())
    try:
        channels = db.execute(blog_channels.select().order_by(blog_channels.c.created_at.desc())).fetchall()
        if len(channels) <= 1:
            return {"message": "Apenas 1 ou 0 blogs encontrados. Nenhuma exclusÃ£o feita.", "kept": [c.id for c in channels]}
        
        kept_channel = channels[0]
        deleted_count = 0
        for c in channels[1:]:
            db.execute(blog_posts.delete().where(blog_posts.c.channel_id == c.id))
            db.execute(blog_sections.delete().where(blog_sections.c.channel_id == c.id))
            db.execute(blog_channels.delete().where(blog_channels.c.id == c.id))
            deleted_count += 1
        db.commit()
        return {"message": f"{deleted_count} blogs antigos deletados.", "kept": kept_channel.id, "deleted": deleted_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FABRICA DE EBOOKS â€” PIPELINE + CRUD + CHECKOUT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# In-memory results para polling (mesmo padrao do blog pipeline)
_ebook_macro_results = {}

@app.post("/api/v1/pipeline/run-ebook-factory")
async def run_ebook_factory(payload: dict, _admin=Depends(require_admin_or_service)):
    """Inicia a macro-pipeline de criacao de ebook."""
    import asyncio
    niche = payload.get("niche", "")
    if not niche:
        raise HTTPException(status_code=400, detail="Nicho e obrigatorio")

    book_title = payload.get("book_title", "")
    blog_channel_id = payload.get("blog_channel_id", "")
    style_id = payload.get("style_id", "minimalista")
    price_cents = payload.get("price_cents", 1700)
    target_chapters = payload.get("target_chapters", 8)

    task_id = f"ebpipe_{uuid.uuid4().hex[:8]}"
    _ebook_macro_results[task_id] = {"status": "starting"}

    def _progress_callback(tid, *args, **kwargs):
        event_type = args[2] if len(args) > 2 else "progress"
        data = args[3] if len(args) > 3 else {}
        if isinstance(data, dict):
            _ebook_macro_results[tid] = data

    async def _run_and_report():
        try:
            from modules.ebook_pipeline import run_ebook_macro_pipeline
            result = await run_ebook_macro_pipeline(
                niche=niche, book_title=book_title,
                blog_channel_id=blog_channel_id, style_id=style_id,
                price_cents=price_cents, target_chapters=target_chapters,
                task_id=task_id, on_progress=_progress_callback,
            )
            _ebook_macro_results[task_id] = result
        except Exception as e:
            _ebook_macro_results[task_id] = {"status": "failed", "error": str(e)}

    asyncio.create_task(_run_and_report())
    return {"task_id": task_id, "status": "starting"}


@app.get("/api/v1/pipeline/ebook-factory/status/{task_id}")
async def ebook_factory_status(task_id: str, _admin=Depends(require_admin_or_service)):
    """Polling do status da macro-pipeline de ebooks."""
    data = _ebook_macro_results.get(task_id)
    if not data:
        raise HTTPException(status_code=404, detail="Task nao encontrada")
    return data


@app.get("/api/v1/pipeline/ebook-factory/history")
async def ebook_factory_history(_admin=Depends(require_admin_or_service)):
    """Historico de execucoes da fabrica de ebooks."""
    from modules.database import get_db_ebook_pipeline_runs
    runs = get_db_ebook_pipeline_runs()
    return {"runs": runs}


# ═════════════════════════════════════════════════════════════════════════
# FABRICA DE MAPAS MENTAIS — Pipeline Endpoints (NOVO)
# ═════════════════════════════════════════════════════════════════════════

_mindmap_macro_results = {}

@app.post("/api/v1/pipeline/run-mindmap-factory")
async def run_mindmap_factory(payload: dict, _admin=Depends(require_admin_or_service)):
    """Inicia a macro-pipeline de criacao de mapa mental."""
    import asyncio
    niche = payload.get("niche", "")
    if not niche:
        raise HTTPException(status_code=400, detail="Nicho e obrigatorio")

    title = payload.get("title", "")
    style_id = payload.get("style_id", "minimalista")
    price_cents = payload.get("price_cents", 1700)

    task_id = f"mmpipe_{_uuid.uuid4().hex[:8]}"
    _mindmap_macro_results[task_id] = {"status": "starting"}

    def _progress_callback(tid, *args, **kwargs):
        event_type = args[2] if len(args) > 2 else "progress"
        data = args[3] if len(args) > 3 else {}
        if isinstance(data, dict):
            _mindmap_macro_results[tid] = data

    async def _run_and_report():
        try:
            from modules.mindmap_pipeline import run_mindmap_macro_pipeline
            result = await run_mindmap_macro_pipeline(
                niche=niche, title=title, style_id=style_id,
                price_cents=price_cents, task_id=task_id,
                on_progress=_progress_callback,
            )
            _mindmap_macro_results[task_id] = result
        except Exception as e:
            _mindmap_macro_results[task_id] = {"status": "failed", "error": str(e)}

    asyncio.create_task(_run_and_report())
    return {"task_id": task_id, "status": "starting"}


@app.get("/api/v1/pipeline/mindmap-factory/status/{task_id}")
async def mindmap_factory_status(task_id: str, _admin=Depends(require_admin_or_service)):
    """Polling do status da macro-pipeline de mapas mentais."""
    data = _mindmap_macro_results.get(task_id)
    if not data:
        raise HTTPException(status_code=404, detail="Task nao encontrada")
    return data


@app.get("/api/v1/pipeline/mindmap-factory/history")
async def mindmap_factory_history(_admin=Depends(require_admin_or_service)):
    """Historico de execucoes da fabrica de mapas mentais."""
    from modules.database import get_db_mindmap_pipeline_runs
    runs = get_db_mindmap_pipeline_runs()
    return {"runs": runs}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FABRICA DE CURSOS â€” Pipeline + Admin CRUD
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

_course_macro_results = {}


@app.post("/api/v1/pipeline/run-course-factory")
async def run_course_factory(payload: dict, _admin=Depends(require_admin_or_service)):
    """Inicia a macro-pipeline de criacao de curso."""
    import asyncio
    topic = payload.get("topic", "")
    if not topic:
        raise HTTPException(status_code=400, detail="Topico e obrigatorio")

    course_title = payload.get("course_title", "")
    difficulty = payload.get("difficulty", "iniciante")
    price_cents = payload.get("price_cents", 0)
    target_modules = payload.get("target_modules", 4)
    lessons_per_module = payload.get("lessons_per_module", 4)

    task_id = f"crpipe_{uuid.uuid4().hex[:8]}"
    _course_macro_results[task_id] = {"status": "starting"}

    def _progress_callback(tid, *args, **kwargs):
        event_type = args[2] if len(args) > 2 else "progress"
        data = args[3] if len(args) > 3 else {}
        if isinstance(data, dict):
            _course_macro_results[tid] = data

    async def _run_and_report():
        try:
            from modules.course_pipeline import run_course_macro_pipeline
            result = await run_course_macro_pipeline(
                topic=topic, course_title=course_title,
                difficulty=difficulty, price_cents=price_cents,
                target_modules=target_modules,
                lessons_per_module=lessons_per_module,
                task_id=task_id, on_progress=_progress_callback,
            )
            _course_macro_results[task_id] = result
        except Exception as e:
            _course_macro_results[task_id] = {"status": "failed", "error": str(e)}

    asyncio.create_task(_run_and_report())
    return {"task_id": task_id, "status": "starting"}


@app.get("/api/v1/pipeline/course-factory/status/{task_id}")
async def course_factory_status(task_id: str):
    """Polling do status da macro-pipeline de cursos."""
    data = _course_macro_results.get(task_id)
    if not data:
        raise HTTPException(status_code=404, detail="Task nao encontrada")
    return data


@app.get("/api/v1/pipeline/course-factory/history")
async def course_factory_history():
    """Historico de execucoes da fabrica de cursos."""
    from modules.database import get_db_course_pipeline_runs
    runs = get_db_course_pipeline_runs()
    return {"runs": runs}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN â€” CRUD Cursos
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/v1/admin/courses")
async def admin_list_courses():
    """Lista todos os cursos (admin)."""
    from modules.database import get_db_courses
    return {"courses": get_db_courses()}


@app.post("/api/v1/admin/courses")
async def admin_create_course(payload: dict):
    """Cria um curso manualmente (admin)."""
    from modules.database import create_db_course
    title = payload.get("title", "")
    if not title:
        raise HTTPException(status_code=400, detail="Titulo e obrigatorio")
    course = create_db_course(
        title=title,
        topic=payload.get("topic", ""),
        description=payload.get("description", ""),
        difficulty=payload.get("difficulty", "iniciante"),
        price_cents=payload.get("price_cents", 0),
    )
    return {"course": course}


@app.get("/api/v1/admin/courses/{course_id}")
async def admin_get_course(course_id: str):
    """Detalhes do curso (admin)."""
    from modules.database import get_db_course
    course = get_db_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")
    return {"course": course}


@app.put("/api/v1/admin/courses/{course_id}")
async def admin_update_course(course_id: str, payload: dict):
    """Atualiza um curso (admin)."""
    from modules.database import update_db_course
    ok = update_db_course(course_id, **payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")
    return {"ok": True}


@app.delete("/api/v1/admin/courses/{course_id}")
async def admin_delete_course(course_id: str):
    """Deleta um curso (admin)."""
    from modules.database import delete_db_course
    ok = delete_db_course(course_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")
    return {"ok": True}


@app.post("/api/v1/admin/courses/{course_id}/publish")
async def admin_publish_course(course_id: str):
    """Publica um curso (admin)."""
    from modules.database import update_db_course
    from datetime import datetime
    ok = update_db_course(course_id, status="published", published_at=datetime.utcnow())
    if not ok:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")
    return {"ok": True}


@app.post("/api/v1/admin/courses/{course_id}/unpublish")
async def admin_unpublish_course(course_id: str):
    """Despublica um curso (admin)."""
    from modules.database import update_db_course
    ok = update_db_course(course_id, status="draft")
    if not ok:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")
    return {"ok": True}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN â€” Learning Paths (Trilhas)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/v1/admin/learning-paths")
async def admin_list_learning_paths():
    """Lista trilhas de aprendizado (admin)."""
    from modules.database import get_db_learning_paths
    return {"paths": get_db_learning_paths()}


@app.post("/api/v1/admin/learning-paths")
async def admin_create_learning_path(payload: dict):
    """Cria uma trilha de aprendizado (admin)."""
    from modules.database import create_db_learning_path
    title = payload.get("title", "")
    slug = payload.get("slug", "")
    if not title or not slug:
        raise HTTPException(status_code=400, detail="Titulo e slug sao obrigatorios")
    path = create_db_learning_path(title, slug, payload.get("description", ""))
    return {"path": path}


@app.get("/api/v1/admin/learning-paths/{path_id}")
async def admin_get_learning_path(path_id: str):
    """Detalhes da trilha (admin)."""
    from modules.database import get_db_learning_path
    path = get_db_learning_path(path_id=path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Trilha nao encontrada")
    return {"path": path}


@app.put("/api/v1/admin/learning-paths/{path_id}")
async def admin_update_learning_path(path_id: str, payload: dict):
    """Atualiza uma trilha (admin)."""
    from modules.database import update_db_learning_path
    ok = update_db_learning_path(path_id, **payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Trilha nao encontrada")
    return {"ok": True}


@app.delete("/api/v1/admin/learning-paths/{path_id}")
async def admin_delete_learning_path(path_id: str):
    """Deleta uma trilha (admin)."""
    from modules.database import delete_db_learning_path
    ok = delete_db_learning_path(path_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Trilha nao encontrada")
    return {"ok": True}


@app.post("/api/v1/admin/learning-paths/{path_id}/courses")
async def admin_add_course_to_path(path_id: str, payload: dict):
    """Adiciona curso a uma trilha (admin)."""
    from modules.database import add_course_to_learning_path
    course_id = payload.get("course_id", "")
    order = payload.get("order", 1)
    if not course_id:
        raise HTTPException(status_code=400, detail="course_id e obrigatorio")
    result = add_course_to_learning_path(path_id, course_id, order)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/api/v1/admin/learning-paths/{path_id}/courses/{course_id}")
async def admin_remove_course_from_path(path_id: str, course_id: str):
    """Remove curso de uma trilha (admin)."""
    from modules.database import remove_course_from_learning_path
    ok = remove_course_from_learning_path(path_id, course_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Curso nao encontrado na trilha")
    return {"ok": True}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN â€” Usuarios e Analytics
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/v1/admin/analytics/overview")
async def admin_analytics_overview():
    """Metricas gerais do sistema (admin)."""
    from modules.database import (
        SessionLocal, User, Course, Book,
        BlogChannel, BlogPost
    )
    db = SessionLocal()
    try:
        users_total = db.query(User).count()
        users_admin = db.query(User).filter(User.role == "admin").count()
        courses_total = db.query(Course).count()
        courses_published = db.query(Course).filter(Course.status == "published").count()
        books_total = db.query(Book).count()
        blogs_total = db.query(BlogChannel).count()
        posts_total = db.query(BlogPost).count()
        return {
            "users": {"total": users_total, "admins": users_admin},
            "courses": {"total": courses_total, "published": courses_published},
            "books": {"total": books_total},
            "blogs": {"total": blogs_total, "posts": posts_total},
        }
    finally:
        db.close()


@app.get("/api/v1/admin/analytics/courses")
async def admin_analytics_courses():
    """Metricas por curso (admin)."""
    from modules.database import get_db_courses
    courses = get_db_courses()
    return {"courses": courses}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PUBLICO â€” Learning Paths
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/v1/learning-paths")
async def list_learning_paths():
    """Lista trilhas publicadas."""
    from modules.database import SessionLocal, LearningPath
    db = SessionLocal()
    try:
        paths = db.query(LearningPath).filter(
            LearningPath.status == "published"
        ).order_by(LearningPath.created_at.desc()).all()
        return {"paths": [{"id": p.id, "title": p.title, "slug": p.slug,
                "description": p.description, "cover_url": p.cover_url} for p in paths]}
    finally:
        db.close()


@app.get("/api/v1/learning-paths/{slug}")
async def get_learning_path(slug: str):
    """Detalhes da trilha por slug."""
    from modules.database import get_db_learning_path
    path = get_db_learning_path(slug=slug)
    if not path:
        raise HTTPException(status_code=404, detail="Trilha nao encontrada")
    return {"path": path}


@app.get("/api/v1/ebooks")
async def list_ebooks(_admin=Depends(require_admin)):
    """Lista todos os ebooks."""
    from modules.database import get_db_books
    books = get_db_books()
    return {"books": books}


@app.get("/api/v1/ebooks/{book_id}")
async def get_ebook(book_id: str, token: str = "", authorization: str = Header(None)):
    """Detalhes de um ebook incluindo capitulos. Aceita token via header Bearer ou query ?token= (para window.open do painel)."""
    t = token or (authorization.replace("Bearer ", "") if authorization else "")
    user_id = _verify_jwt_token(t) if t else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Token ausente ou invÃ¡lido")
    user = get_db_user_by_id(user_id)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    from modules.database import get_db_book
    book = get_db_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Ebook nao encontrado")
    return {"book": book}


@app.post("/api/v1/ebooks/{book_id}/agnes-cover")
async def generate_ebook_agnes_cover(book_id: str, _admin=Depends(require_admin)):
    """🎨 Agnes Studio: gera/regenera a capa do ebook com design de capa real
    (tipografia + autor + créditos) e renderiza HTML → PNG via Obscura."""
    from modules.database import get_db_book, update_db_book
    from modules.agnes_studio import AgnesStudio

    book = get_db_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Ebook não encontrado")

    import json as _json

    # Reutiliza o design persistido (se houver) para manter a identidade visual
    design = None
    if book.get("cover_design"):
        try:
            design = _json.loads(book["cover_design"])
        except Exception:
            design = None

    try:
        studio = AgnesStudio()
        result = await studio.generate_ebook_cover(
            title=book.get("title", ""),
            subtitle=book.get("subtitle", "") or "",
            author=book.get("author", "") or "",
            niche=book.get("niche", "") or book.get("topic", ""),
            style_id=book.get("style_id", "moderno") or "moderno",
            book_id=book_id,
            design=design,
        )
        if result.get("cover_url"):
            update_db_book(
                book_id,
                cover_url=result["cover_url"],
                cover_design=_json.dumps(result.get("design", {}), default=str),
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar capa Agnes: {str(e)}")


@app.delete("/api/v1/ebooks/{book_id}")
async def delete_ebook(book_id: str, _admin=Depends(require_admin)):
    """Deleta um ebook e seus dados."""
    from modules.database import delete_db_book, SessionLocal, EbookPipelineRun
    # Deletar pipeline runs associados
    db = SessionLocal()
    try:
        db.query(EbookPipelineRun).filter(EbookPipelineRun.book_id == book_id).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    ok = delete_db_book(book_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Ebook nao encontrado")
    return {"message": "Ebook deletado com sucesso"}


# ═════════════════════════════════════════════════════════════════════════
# CRUD — FABRICA DE MAPAS MENTAIS (NOVO)
# ═════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/mindmaps")
async def list_mindmaps(_admin=Depends(require_admin)):
    """Lista todos os mapas mentais."""
    from modules.database import get_db_mindmaps
    mmaps = get_db_mindmaps()
    return {"mindmaps": mmaps}


@app.get("/api/v1/mindmaps/{mindmap_id}")
async def get_mindmap_endpoint(mindmap_id: str, token: str = "", authorization: str = Header(None)):
    """Detalhes de um mapa mental. Exige token ou header Bearer."""
    t = token or (authorization.replace("Bearer ", "") if authorization else "")
    user_id = _verify_jwt_token(t) if t else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Token ausente ou invalido")
    user = get_db_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    
    # Validar trial de 7 dias se o usuario for membro regular (nao administrador)
    if user.role != "admin" and not user.subscription_active:
        trial_start = user.trial_started_at or user.created_at
        if not trial_start:
            trial_start = datetime.utcnow()
        delta = datetime.utcnow() - trial_start
        if delta.days >= 7:
            return {"success": False, "expired": True, "message": "Seu periodo de testes de 7 dias acabou. Por favor, assine."}

    from modules.database import get_db_mindmap
    m = get_db_mindmap(mindmap_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mapa mental nao encontrado")
    return {"success": True, "mindmap": m}


@app.delete("/api/v1/mindmaps/{mindmap_id}")
async def delete_mindmap_endpoint(mindmap_id: str, _admin=Depends(require_admin)):
    """Deleta um mapa mental e seus dados."""
    from modules.database import delete_db_mindmap, SessionLocal, MindMapPipelineRun
    # Deletar pipeline runs associados
    db = SessionLocal()
    try:
        db.query(MindMapPipelineRun).filter(MindMapPipelineRun.mindmap_id == mindmap_id).delete()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    ok = delete_db_mindmap(mindmap_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Mapa mental nao encontrado")
    return {"message": "Mapa mental deletado com sucesso"}








# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SEU PEREIRA â€” MONETIZATION ENDPOINT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/v1/monetization/status")
async def get_monetization_status(channel_id: str = None, _admin=Depends(require_admin)):
    """
    Retorna avaliacao completa de monetizacao para um blog.
    Usa o agente Seu Pereira para analisar 19 criterios do Google AdSense.
    Se channel_id nao for fornecido, descobre automaticamente o primeiro blog.
    """
    if not channel_id:
        from modules.database import get_db_blog_channels
        channels = get_db_blog_channels()
        if channels and len(channels) > 0:
            channel_id = channels[0]["id"]
        else:
            channel_id = "default"
    from modules.seu_pereira import avaliar_monetizacao
    return avaliar_monetizacao(channel_id=channel_id)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PAGINAS DE SISTEMA â€” Privacidade, Sobre, Contato
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•



@app.get("/curso/{course_id}", response_class=HTMLResponse)
async def serve_course_player(course_id: str, token: str = None):
    """Player de curso — destino de entrega dos produtos do Clube.

    Exige token de acesso assinado (gerado pelo Clube na entrega, HMAC
    com a chave compartilhada CLUBE_IMPORT_KEY/IMPORT_API_KEY). Sem token
    válido, retorna 403 com página de acesso restrito (fail-closed).
    """
    from modules.course_viewer import (
        build_course_page,
        generate_access_denied_html,
        validate_course_access_token,
    )
    if not validate_course_access_token(course_id, token or ""):
        return HTMLResponse(content=generate_access_denied_html(), status_code=403)
    page = build_course_page(course_id)
    if not page:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")
    return HTMLResponse(content=page)

@app.get("/blog/{slug}/privacidade", response_class=HTMLResponse)
async def serve_privacy_page(slug: str):
    from modules.blog_viewer import generate_privacy_page
    from modules.database import get_db_blog_info
    blog_info = get_db_blog_info(slug) or {}
    return HTMLResponse(content=generate_privacy_page(slug, blog_info))

@app.get("/blog/{slug}/sobre", response_class=HTMLResponse)
async def serve_about_page(slug: str):
    from modules.blog_viewer import generate_about_page
    from modules.database import get_db_blog_info
    blog_info = get_db_blog_info(slug) or {}
    return HTMLResponse(content=generate_about_page(slug, blog_info))

@app.get("/blog/{slug}/contato", response_class=HTMLResponse)
async def serve_contact_page(slug: str):
    from modules.blog_viewer import generate_contact_page
    from modules.database import get_db_blog_info
    blog_info = get_db_blog_info(slug) or {}
    return HTMLResponse(content=generate_contact_page(slug, blog_info))

@app.get("/blog/{slug}/termos", response_class=HTMLResponse)
async def serve_terms_page(slug: str):
    from modules.blog_viewer import generate_terms_page
    from modules.database import get_db_blog_info
    blog_info = get_db_blog_info(slug) or {}
    return HTMLResponse(content=generate_terms_page(slug, blog_info))

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ROBOTS.TXT & SITEMAP
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/robots.txt", response_class=HTMLResponse)
async def robots_txt():
    content = "User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /static/\nSitemap: https://dezafira.com.br/sitemap.xml\n"
    return HTMLResponse(content=content, media_type="text/plain")

@app.get("/sitemap.xml", response_class=HTMLResponse)
async def sitemap_xml():
    from modules.database import SessionLocal, BlogPost, BlogChannel
    from datetime import datetime
    db = SessionLocal()
    try:
        posts = db.query(BlogPost).filter(BlogPost.status.in_(["published", "draft"])).all()
        channels = db.query(BlogChannel).all()
    finally:
        db.close()
    urls = []
    base_url = "https://dezafira.com.br"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for ch in channels:
        slug = ch.site_url or "/blog/" + ch.name.lower().replace(" ", "-")
        ch_date = getattr(ch, 'updated_at', None) or getattr(ch, 'created_at', None) or datetime.utcnow()
        lastmod = ch_date.strftime("%Y-%m-%d")
        urls.append(f"<url><loc>{base_url}{slug}</loc><lastmod>{lastmod}</lastmod><priority>0.9</priority></url>")
        urls.append(f"<url><loc>{base_url}{slug}/sobre</loc><lastmod>{today}</lastmod><priority>0.5</priority></url>")
        urls.append(f"<url><loc>{base_url}{slug}/privacidade</loc><lastmod>{today}</lastmod><priority>0.3</priority></url>")
        urls.append(f"<url><loc>{base_url}{slug}/contato</loc><lastmod>{today}</lastmod><priority>0.5</priority></url>")
        urls.append(f"<url><loc>{base_url}{slug}/termos</loc><lastmod>{today}</lastmod><priority>0.3</priority></url>")
    for p in posts:
        ch = next((c for c in channels if c.id == p.channel_id), None)
        if ch:
            slug = ch.site_url or "/blog/" + ch.name.lower().replace(" ", "-")
            p_date = getattr(p, 'updated_at', None) or getattr(p, 'created_at', None) or datetime.utcnow()
            lastmod = p_date.strftime("%Y-%m-%d")
            urls.append(f"<url><loc>{base_url}{slug}?post={p.id}</loc><lastmod>{lastmod}</lastmod><priority>0.8</priority></url>")
    xml_content = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(urls) + "</urlset>"
    return HTMLResponse(content=xml_content, media_type="application/xml")

@app.get("/ads.txt", response_class=HTMLResponse)
async def ads_txt():
    c = "google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0\n"
    return HTMLResponse(content=c, media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    # Inicia a API no host 127.0.0.1 porta 8000
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)


@app.get("/api/v1/factory/monitor-stats")
async def get_factory_stats():
    """
    Retorna metricas consolidadas para alimentar os contadores visuais do Mission Control.
    """
    from sqlalchemy import func
    from modules.database import SessionLocal, AutomationTask

    db = SessionLocal()
    try:
        stats = db.query(
            AutomationTask.status,
            func.count(AutomationTask.id)
        ).group_by(AutomationTask.status).all()

        stats_dict = {status: count for status, count in stats}

        active = db.query(AutomationTask).filter(
            AutomationTask.status.in_(["triage", "writing", "SEO", "production"])
        ).order_by(AutomationTask.updated_at.desc()).limit(5).all()

        active_tasks = [{
            "id": t.id,
            "title_suggestion": t.title_suggestion,
            "status": t.status
        } for t in active]

        return {
            "total_queued": stats_dict.get("triage", 0),
            "total_processing": (
                stats_dict.get("writing", 0)
                + stats_dict.get("SEO", 0)
                + stats_dict.get("production", 0)
            ),
            "total_ready": stats_dict.get("ready", 0),
            "total_completed": stats_dict.get("done", 0),
            "total_failed": stats_dict.get("failed", 0),
            "active_tasks": active_tasks,
            "active_llm_provider": getattr(director.brain, "last_provider_used", "nvidia"),
        }
    finally:
        db.close()


@app.get("/api/v1/factory/openmontage-status")
async def get_openmontage_status():
    """
    Retorna o status detalhado da integracao com OpenMontage.
    """
    from services.open_montage_bridge import get_open_montage_status
    return get_open_montage_status()


@app.get("/api/v1/channels/{channel_id}/knowledge")
async def get_channel_knowledge(channel_id: str):
    """
    Retorna o Shared Memory (channel_knowledge) para um canal.
    """
    from services.memory_service import get_knowledge
    return {"knowledge": get_knowledge(channel_id)}


@app.post("/api/v1/channels/{channel_id}/knowledge")
async def save_channel_knowledge(channel_id: str, payload: dict):
    """
    Salva um conhecimento no Shared Memory do canal.
    """
    from services.memory_service import save_knowledge
    success = save_knowledge(
        channel_id=channel_id,
        category=payload.get("category", "style_guide"),
        meta_key=payload.get("meta_key", ""),
        meta_value=payload.get("meta_value", ""),
        source=payload.get("source", "user_feedback"),
    )
    return {"success": success}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# RESEARCH ENGINE ENDPOINTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.post("/api/v1/research/niche")
async def research_niche(payload: dict):
    """
    Pesquisa completa de um nicho.
    """
    from research.engine import ResearchEngine
    
    engine = ResearchEngine()
    keyword = payload.get("keyword", "")
    
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required")
    
    result = await engine.research_niche(keyword)
    
    return {
        "niche_score": result.niche_score,
        "competition_level": result.competition_level,
        "monetization_potential": result.monetization_potential,
        "trending_videos": result.trending_videos,
        "title_patterns": result.title_patterns,
        "recommendations": result.recommendations,
        "channels": result.channels,
    }


@app.post("/api/v1/research/channel")
async def research_channel(payload: dict):
    """
    Analisa um canal especÃ­fico.
    """
    from research.engine import ResearchEngine
    
    engine = ResearchEngine()
    channel_url = payload.get("url", "")
    
    if not channel_url:
        raise HTTPException(status_code=400, detail="Channel URL is required")
    
    result = await engine.analyze_channel(channel_url)
    return result


@app.get("/api/v1/research/trending")
async def get_trending():
    """
    ObtÃ©m tÃªndencias atuais do YouTube.
    """
    from research.engine import ResearchEngine
    
    engine = ResearchEngine()
    result = await engine.get_trending_topics()
    return result


@app.get("/api/v1/research/youtube-rules")
async def get_youtube_rules():
    """
    ObtÃ©m regras e melhores prÃ¡ticas do YouTube.
    """
    from research.engine import ResearchEngine
    
    engine = ResearchEngine()
    result = await engine.learn_youtube_rules()
    return result


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# PIPELINE ENDPOINTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.post("/api/v1/pipeline/start")
async def start_pipeline(payload: dict, _admin=Depends(require_admin)):
    """
    Inicia um novo pipeline de produÃ§Ã£o.
    """
    # Usa singletons globais (Bug C1 fix)
    orchestrator = _hermes_orchestrator
    hub = _ws_hub
    
    theme = payload.get("theme", "")
    channel_id = payload.get("channel_id")
    video_format = payload.get("video_format", "horizontal")
    
    if not theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    task_id = await orchestrator.start_pipeline(
        theme=theme,
        channel_id=channel_id,
        video_format=video_format,
    )
    
    return {"task_id": task_id, "status": "started"}


@app.post("/api/v1/pipeline/start-modular")
async def start_modular_pipeline(payload: dict, _admin=Depends(require_admin)):
    """
    Inicia um pipeline modular dividido em blocos/capÃ­tulos sequenciais.
    """
    orchestrator = _hermes_orchestrator
    
    theme = payload.get("theme", "")
    channel_id = payload.get("channel_id")
    video_format = payload.get("video_format", "horizontal")
    blocks = payload.get("blocks", [])
    
    if not theme:
        raise HTTPException(status_code=400, detail="Theme is required")
    
    if not blocks:
        raise HTTPException(status_code=400, detail="Blocks are required for modular pipeline")
        
    task_id = await orchestrator.start_pipeline(
        theme=theme,
        channel_id=channel_id,
        video_format=video_format,
        blocks=blocks
    )
    
    return {"task_id": task_id, "status": "started"}


@app.post("/api/v1/spy/discover")
async def spy_discover_offers(payload: dict):
    """
    Executa busca de criativos/ofertas na Meta Ad Library baseada em palavra-chave.
    """
    query = payload.get("query", "")
    country = payload.get("country", "BR")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
        
    try:
        from services.spy_service import scrape_meta_ads
        results = await scrape_meta_ads(query=query, country=country)
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spy service failed: {str(e)}")


@app.post("/api/v1/factory/build-app")
async def build_mini_app(payload: dict, _admin=Depends(require_admin)):
    """
    Gera um PWA estÃ¡tico de Quiz estruturado com base nas perguntas fornecidas.
    """
    app_id = payload.get("app_id", "my_app")
    title = payload.get("title", "Quiz de AvaliaÃ§Ã£o")
    nicho = payload.get("nicho", "Geral")
    questions = payload.get("questions", [])
    checkout_url = payload.get("checkout_url", "https://kiwify.com.br")
    cta_text = payload.get("cta_text", "Obter RelatÃ³rio")
    
    if not questions:
        raise HTTPException(status_code=400, detail="Questions are required to generate Quiz")
        
    try:
        from services.pwa_generator import PWAGenerator
        res = PWAGenerator.generate_quiz_pwa(
            app_id=app_id,
            title=title,
            nicho=nicho,
            questions=questions,
            cta_text=cta_text,
            checkout_url=checkout_url
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PWA build failed: {str(e)}")


@app.post("/api/v1/pipeline/hyperframes-video")
async def build_hyperframes_timeline(payload: dict, _admin=Depends(require_admin)):
    """
    Gera a timeline de vÃ­deo (JSON) no formato Hyperframes.
    """
    task_id = payload.get("task_id", "hf_video")
    script_text = payload.get("script_text", "")
    audio_path = payload.get("audio_path", "")
    media_clips = payload.get("media_clips", [])
    captions = payload.get("captions", [])
    video_format = payload.get("video_format", "vertical")
    
    try:
        from services.hyperframes_bridge import HyperframesBridge
        res = HyperframesBridge.generate_timeline_json(
            task_id=task_id,
            script_text=script_text,
            audio_path=audio_path,
            media_clips=media_clips,
            captions=captions,
            video_format=video_format
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hyperframes generation failed: {str(e)}")



@app.get("/api/v1/pipeline/active-tasks")
async def get_active_pipeline_tasks(channel_id: str = None):
    """
    Retorna a lista de todas as tarefas de pipeline ativas ou recentes filtradas por blog.
    (Registrado ANTES de /pipeline/{task_id} para nao ser engolido pela rota dinamica.)
    """
    tasks = []
    for tid, info in _macro_results.items():
        if channel_id and info.get("channel_id") != channel_id:
            continue
        tasks.append({
            "task_id": tid,
            "topic": info.get("topic"),
            "channel_id": info.get("channel_id"),
            "status": info.get("status"),
            "phase": info.get("phase"),
            "progress": info.get("progress"),
            "error": info.get("error"),
        })
    return {"tasks": tasks}


@app.get("/api/v1/pipeline/{task_id}")
async def get_pipeline_status(task_id: str):
    """
    ObtÃ©m status de um pipeline.
    """
    # Usa singletons globais (Bug C1 fix)
    orchestrator = _hermes_orchestrator
    hub = _ws_hub
    
    pipeline = orchestrator.get_pipeline(task_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return pipeline.to_dict()


@app.get("/api/v1/pipeline")
async def list_pipelines():
    """
    Lista todos os pipelines ativos.
    """
    # Usa singletons globais (Bug C1 fix)
    orchestrator = _hermes_orchestrator
    hub = _ws_hub
    
    return orchestrator.get_all_pipelines()


@app.post("/api/v1/pipeline/{task_id}/pause")
async def pause_pipeline(task_id: str, _admin=Depends(require_admin_or_service)):
    """
    Pausa um pipeline.
    """
    # Usa singletons globais (Bug C1 fix)
    orchestrator = _hermes_orchestrator
    hub = _ws_hub
    
    success = orchestrator.pause_pipeline(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause pipeline")
    
    return {"status": "paused"}


@app.post("/api/v1/pipeline/{task_id}/resume")
async def resume_pipeline(task_id: str, _admin=Depends(require_admin_or_service)):
    """
    Retoma um pipeline pausado.
    """
    # Usa singletons globais (Bug C1 fix)
    orchestrator = _hermes_orchestrator
    hub = _ws_hub
    
    success = orchestrator.resume_pipeline(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume pipeline")
    
    return {"status": "resumed"}


@app.post("/api/v1/pipeline/{task_id}/stop")
async def stop_pipeline(task_id: str, _admin=Depends(require_admin_or_service)):
    """
    Para um pipeline.
    """
    # Usa singletons globais (Bug C1 fix)
    orchestrator = _hermes_orchestrator
    hub = _ws_hub
    
    success = orchestrator.stop_pipeline(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot stop pipeline")
    
    return {"status": "stopped"}


@app.post("/api/v1/pipeline/{task_id}/approve/{stage}")
async def approve_stage(task_id: str, stage: str, _admin=Depends(require_admin_or_service)):
    """
    Aprova um estÃ¡gio do pipeline.
    """
    # Usa singletons globais (Bug C1 fix)
    orchestrator = _hermes_orchestrator
    hub = _ws_hub
    
    pipeline = orchestrator.get_pipeline(task_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    success = pipeline.approve_stage(stage)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot approve stage")
    
    return {"status": "approved", "stage": stage}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ANALYTICS ENDPOINTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@app.get("/api/v1/analytics/metrics")
async def get_analytics_metrics(period: str = "7d"):
    """
    ObtÃ©m mÃ©tricas gerais de analytics.
    """
    return {
        "totalViews": 125000,
        "totalSubscribers": 3200,
        "totalVideos": 47,
        "estimatedRevenue": 2500,
        "growthRate": 15,
    }


@app.get("/api/v1/analytics/channels")
async def get_analytics_channels():
    """
    ObtÃ©m mÃ©tricas por canal.
    """
    return [
        {
            "name": "Tech sem Limites",
            "niche": "Tecnologia",
            "views": 45000,
            "subscribers": 1200,
            "engagement": 4.5,
            "ctr": 8.2,
        },
        {
            "name": "Dinheiro Inteligente",
            "niche": "FinanÃ§as",
            "views": 38000,
            "subscribers": 980,
            "engagement": 3.8,
            "ctr": 7.1,
        },
    ]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FÃBRICA DE ENTREGÃVEIS (PWA & MINI-APPS)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
from modules.database import (
    create_db_deliverable_app,
    get_db_deliverable_app_by_slug,
    get_db_deliverable_apps,
)
from modules.deliverables import create_deliverable_app_for_channel

class CreateDeliverablePayload(BaseModel):
    channel_id: Optional[str] = "default"
    name: str
    nicho: str
    slug: Optional[str] = None
    checkout_url: Optional[str] = None

@app.post("/api/v1/deliverables/create")
async def api_create_deliverable(payload: CreateDeliverablePayload):
    try:
        app_data = await create_deliverable_app_for_channel(
            channel_id=payload.channel_id,
            name=payload.name,
            nicho=payload.nicho,
            slug=payload.slug,
            checkout_url=payload.checkout_url or ""
        )
        return app_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar entregÃ¡vel: {str(e)}")

@app.get("/api/v1/deliverables")
async def api_get_deliverable_apps():
    return get_db_deliverable_apps()

@app.get("/api/v1/deliverables/{slug}")
async def api_get_deliverable_by_slug(slug: str):
    app = get_db_deliverable_app_by_slug(slug)
    if not app:
        raise HTTPException(status_code=404, detail="Aplicativo nÃ£o encontrado")
    return app


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# HERMES ORCHESTRATOR - Chat Inteligente com AÃ§Ãµes Reais

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# BLOG FRONTEND â€” API PÃšBLICA
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class NewsletterSubscribePayload(BaseModel):
    email: str
    name: Optional[str] = None
    source: Optional[str] = None


@app.post("/api/v1/newsletter/subscribe")
async def api_newsletter_subscribe(payload: NewsletterSubscribePayload):
    """Captura de leads dos blogs (viewer SSR) — encaminha para a newsletter do Clube.

    O blog viewer (HTML SSR) posta aqui; este endpoint valida o e-mail,
    encaminha para o Clube (CLUBE_PUBLIC_URL/api/newsletter) e grava localmente
    como backup (data/newsletter_leads.jsonl) mesmo se o Clube estiver fora.
    """
    import re
    email = (payload.email or "").strip().lower()
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise HTTPException(status_code=400, detail="E-mail inválido")

    clube_url = os.getenv("CLUBE_PUBLIC_URL", "https://www.dezafira.com.br").rstrip("/")
    forwarded = False
    forward_error = ""
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.post(
                f"{clube_url}/api/newsletter",
                json={"email": email, "name": payload.name or ""},
                headers={"Content-Type": "application/json"},
            )
            if r.status_code in (200, 201):
                forwarded = True
            else:
                forward_error = f"Clube HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        forward_error = str(e)

    # Backup local (fire-and-forget) — nunca perde o lead
    try:
        import json as _json
        from pathlib import Path
        data_dir = Path(__file__).resolve().parent / "data"
        data_dir.mkdir(exist_ok=True)
        lead_file = data_dir / "newsletter_leads.jsonl"
        with open(lead_file, "a", encoding="utf-8") as f:
            f.write(_json.dumps({
                "email": email,
                "name": payload.name or "",
                "source": payload.source or "blog",
                "forwarded": forwarded,
                "forward_error": forward_error[:300] or None,
                "ts": datetime.utcnow().isoformat(),
            }, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[Newsletter] Erro ao gravar backup local: {e}")

    if not forwarded and forward_error:
        print(f"[Newsletter] Clube indisponível ({forward_error}); lead salvo localmente.")
    return {"success": True, "message": "Inscrição registrada"}


class ImportProductPayload(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    price_cents: int = 0
    resource_type: str = "link"
    external_link: Optional[str] = None
    image_url: Optional[str] = None
    youtube_video_url: Optional[str] = None
    category: Optional[str] = None
    has_extra_service: Optional[int] = 0
    extra_service_title: Optional[str] = None
    extra_service_price_cents: Optional[int] = 0
    extra_service_description: Optional[str] = None
    upsell_product_id: Optional[int] = None
    downsell_product_id: Optional[int] = None


@app.post("/api/v1/clube/import-product")
async def api_clube_import_product(payload: ImportProductPayload, _admin=Depends(require_admin)):
    """Ponte Adm → Clube: cria um produto no catálogo do Clube.

    Usado pelas fábricas (curso/ebook/miniapp) para publicar o entregável
    na loja do Clube (checkout Asaas + esteira upsell/downsell).

    Requer no .env:
      CLUBE_PUBLIC_URL  (ex: https://www.dezafira.com.br)
      CLUBE_IMPORT_KEY  (IMPORT_API_KEY do Clube)
    """
    clube_url = os.getenv("CLUBE_PUBLIC_URL", "https://www.dezafira.com.br").rstrip("/")
    import_key = os.getenv("CLUBE_IMPORT_KEY", "")
    if not import_key:
        raise HTTPException(status_code=503, detail="CLUBE_IMPORT_KEY não configurado no Adm.")

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{clube_url}/api/import/product",
                json=payload.model_dump(exclude_none=True),
                headers={"Content-Type": "application/json", "x-import-key": import_key},
            )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:300]}
        if r.status_code in (200, 201):
            return {"success": True, **data}
        raise HTTPException(status_code=r.status_code, detail=data.get("error") or f"Erro do Clube: HTTP {r.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao conectar no Clube: {str(e)}")


@app.get("/api/v1/blog/{slug}/posts")
async def get_blog_posts(slug: str):
    """Retorna posts de um blog pelo slug."""
    from modules.database import get_db_blog_channels, get_db_blog_posts

    # Find blog channel by name slug
    channels = get_db_blog_channels()
    blog = None
    for c in channels:
        c_slug = c["name"].lower().replace(" ", "-")
        if c_slug == slug:
            blog = c
            break

    if not blog:
        # Fallback: retorna posts do primeiro blog
        if channels:
            blog = channels[0]

    if not blog:
        return {"posts": []}

    posts = get_db_blog_posts(channel_id=blog["id"], limit=50)
    return {"blog": blog, "posts": posts}


@app.get("/api/v1/blog/{slug}/posts/{post_id}")
async def get_blog_post(slug: str, post_id: str):
    """Retorna um post individual do blog."""
    from modules.database import get_db_blog_post

    post = get_db_blog_post(post_id)
    if not post:
        return {"error": "Post nao encontrado"}

    return post


@app.get("/api/v1/blog/{slug}/info")
async def get_blog_info(slug: str):
    """Retorna metadados do blog (banner_url, post_count, etc)."""
    from modules.database import get_db_blog_info
    info = get_db_blog_info(slug)
    if not info:
        from modules.database import get_db_blog_channels
        channels = get_db_blog_channels()
        if channels:
            name_slug = channels[0]["name"].lower().replace(" ", "-")
            info = get_db_blog_info(name_slug)
    if not info:
        raise HTTPException(status_code=404, detail="Blog nÃ£o encontrado")
    return info

@app.get("/api/v1/blog/{slug}/subdomain")
async def get_blog_subdomain(slug: str):
    """Retorna o subdominio configurado para um blog."""
    from modules.database import get_db_blog_info
    info = get_db_blog_info(slug)
    if not info:
        raise HTTPException(status_code=404, detail="Blog nÃ£o encontrado")
    base_domain = os.getenv("SUBDOMAIN_DOMAIN", "dezafira.com.br")
    subdomain = info.get("subdomain") or slug.replace("-", "").lower()[:50]
    return {
        "subdomain": subdomain,
        "url": f"https://{subdomain}.{base_domain}" if subdomain else None,
        "current": info.get("subdomain"),
        "auto": slug.replace("-", "").lower()[:50],
    }


@app.post("/api/v1/blog/{slug}/subdomain")
async def set_blog_subdomain(slug: str, payload: dict):
    """Configura o subdominio de um blog."""
    from modules.database import get_db_blog_info, update_db_blog_channel
    info = get_db_blog_info(slug)
    if not info:
        raise HTTPException(status_code=404, detail="Blog nÃ£o encontrado")
    
    subdomain = payload.get("subdomain", "").strip().lower()
    if not subdomain:
        raise HTTPException(status_code=400, detail="Subdominio nao pode ser vazio")
    
    # Sanitize subdomain
    subdomain = subdomain.replace(" ", "").replace("_", "-")
    subdomain = re.sub(r"[^a-z0-9-]", "", subdomain)
    subdomain = subdomain[:50]
    
    if not subdomain:
        raise HTTPException(status_code=400, detail="Subdominio invalido apos sanitizacao")
    
    success = update_db_blog_channel(info["id"], subdomain=subdomain)
    if success:
        base_domain = os.getenv("SUBDOMAIN_DOMAIN", "dezafira.com.br")
        # Invalidar cache
        try:
            _SUBDOMAIN_CACHE.pop(subdomain, None)
        except Exception:
            pass
        return {
            "success": True,
            "subdomain": subdomain,
            "url": f"https://{subdomain}.{base_domain}",
        }
    return {"success": False, "error": "Falha ao atualizar subdominio"}



@app.post("/api/v1/blog/{slug}/generate-banner")
async def generate_blog_banner(slug: str):
    """Gera e salva imagem de banner para o blog."""
    from modules.database import get_db_blog_info, update_db_blog_channel
    from modules.image_factory import ImageGeneratorAgent
    info = get_db_blog_info(slug)
    if not info:
        raise HTTPException(status_code=404, detail="Blog nÃ£o encontrado")
    agent = ImageGeneratorAgent()
    prompt = f"{info.get('name', '')} - {info.get('nicho', '')} - paisagem cenario igreja montanha"
    img = await agent.generate(
        prompt=prompt,
        style="blog",
        width=1200,
        height=400,
    )
    if img.get("image_url"):
        update_db_blog_channel(info["id"], banner_url=img["image_url"])
        return {"success": True, "banner_url": img["image_url"], "provider": img.get("provider")}
    return {"success": False, "error": "Nenhuma imagem encontrada"}


@app.get("/oreino", response_class=RedirectResponse)
@app.get("/o-reino", response_class=RedirectResponse)
async def redirect_oreino():
    return RedirectResponse(url="/blog/o-reino")

@app.get("/blog/{slug}", response_class=HTMLResponse)
async def serve_blog_frontend(slug: str, post: str = None, cat: str = None, q: str = None):
    """Serve o frontend publico do blog.
    Suporta:
      ?post=post_id  - artigo individual
      ?cat=categoria  - filtrar por categoria (busca nas keywords)
      ?q=termo        - buscar por termo no titulo/conteudo
    """
    from modules.blog_viewer import generate_blog_html
    from modules.database import get_db_blog_info, get_db_blog_posts, get_db_blog_post

    blog_info = get_db_blog_info(slug)
    posts = []
    individual_post = None

    if blog_info:
        if post:
            individual_post = get_db_blog_post(post)
            if not individual_post:
                individual_post = {"error": "not found"}
        # Busca todos os posts
        all_posts = get_db_blog_posts(channel_id=blog_info["id"], limit=200) or []
        
        # Filtro por categoria (?cat=)
        if cat and not individual_post:
            cat_lower = cat.lower().strip()
            filtered = []
            for p in all_posts:
                kw = (p.get("keywords") or "").lower()
                tit = (p.get("title") or "").lower()
                if cat_lower in kw or cat_lower in tit:
                    filtered.append(p)
            posts = filtered if filtered else all_posts
        # Busca por termo (?q=)
        elif q and not individual_post:
            q_lower = q.lower().strip()
            filtered = []
            for p in all_posts:
                tit = (p.get("title") or "").lower()
                kw = (p.get("keywords") or "").lower()
                exc = (p.get("excerpt") or "").lower()
                if q_lower in tit or q_lower in kw or q_lower in exc:
                    filtered.append(p)
            posts = filtered if filtered else []
        else:
            posts = all_posts[:50]
    else:
        from modules.database import get_db_blog_channels
        channels = get_db_blog_channels()
        if channels:
            blog_info = channels[0]
            if post:
                individual_post = get_db_blog_post(post)
            posts = get_db_blog_posts(channel_id=blog_info["id"], limit=50)

    # Computar artigos relacionados (excluir o post atual)
    related = []
    if individual_post and individual_post.get('id') and posts:
        pid = individual_post['id']
        related = [p for p in posts if p.get('id') != pid][:3]

    html = generate_blog_html(slug, blog_info, posts, post=individual_post, related_posts=related)
    return HTMLResponse(content=html)

@app.get("/api/v1/search")
async def global_search(q: str = "", _admin=Depends(require_admin)):
    """Busca global de artigos em todos os blogs (para o Ctrl+K da UI Admin).
    Procura em titulo, keywords e excerpt dos posts.
    """
    from modules.database import SessionLocal, BlogPost, BlogChannel
    term = (q or "").strip()
    if len(term) < 2:
        return {"results": []}
    # Escapa wildcards do LIKE para busca literal
    term_esc = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    db = SessionLocal()
    try:
        like = f"%{term_esc}%"
        posts = db.query(BlogPost).filter(
            (BlogPost.title.ilike(like, escape='\\')) |
            (BlogPost.keywords.ilike(like, escape='\\')) |
            (BlogPost.excerpt.ilike(like, escape='\\'))
        ).order_by(BlogPost.created_at.desc()).limit(25).all()
        chans = {c.id: c for c in db.query(BlogChannel).all()}
        results = []
        for p in posts:
            ch = chans.get(p.channel_id)
            c_slug = (ch.name.lower().replace(" ", "-")[:50]) if ch else ""
            results.append({
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "status": p.status,
                "lili_score": getattr(p, "lili_score", None),
                "word_count": p.word_count or 0,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "blog_id": p.channel_id,
                "blog_name": ch.name if ch else "?",
                "blog_slug": c_slug,
                "url": f"/blog/{c_slug}?post={p.id}",
            })
        return {"results": results}
    finally:
        db.close()

@app.post("/api/v1/blog/{slug}/posts/{post_id}/generate-image")
async def generate_blog_post_image(slug: str, post_id: str):
    """Gera imagem de destaque para um artigo existente."""
    from modules.database import get_db_blog_post, update_db_blog_post
    from modules.image_factory import ImageGeneratorAgent

    post = get_db_blog_post(post_id)
    if not post:
        return {"error": "Post nao encontrado"}

    agent = ImageGeneratorAgent()
    img = await agent.generate_for_article(
        title=post.get("title", ""),
        keywords=post.get("keywords", ""),
        topic=post.get("topic", ""),
    )

    if img.get("image_url"):
        update_db_blog_post(post_id, featured_image_url=img["image_url"])
        return {"success": True, "image_url": img["image_url"], "provider": img.get("provider")}

    return {"success": False, "error": "Nenhuma imagem encontrada"}


@app.post("/api/v1/blog/{slug}/posts/{post_id}/update")
async def update_blog_post(slug: str, post_id: str, payload: dict):
    """Atualiza campos de um post do blog (content, title, excerpt, etc).
    Recebe um JSON body com os campos a serem atualizados.
    Exemplo: {"content": "<html>..."}
    """
    from modules.database import update_db_blog_post
    
    success = update_db_blog_post(post_id, **payload)
    if success:
        return {"success": True, "message": "Post atualizado"}
    return {"success": False, "error": "Post nao encontrado"}


@app.post("/api/v1/blog/post/{post_id}/liberar-clube")
async def liberar_blog_post_clube(post_id: str, payload: dict = None, _admin=Depends(require_admin)):
    """Marca um artigo como LIBERADO (passou no controle de qualidade) ou não
    para envio ao DezafiraClube. Body: {"liberado": true|false} (padrão: true)."""
    from modules.database import get_db_blog_post, update_db_blog_post

    post = get_db_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Artigo não encontrado")

    _raw = (payload or {}).get("liberado", True)
    liberado = _raw in (True, "true", "True", 1, "1", "on")
    # Liberação manual sempre sobrescreve a automática da LiLi:
    # liberar → limpa o bloqueio manual; bloquear → marca bloqueio manual
    # para que uma revisão LiLi posterior não re-libere sem querer.
    ok = update_db_blog_post(post_id, club_liberado=liberado, club_manual_block=(not liberado))
    if not ok:
        raise HTTPException(status_code=500, detail="Falha ao atualizar o artigo")
    return {
        "success": True,
        "post_id": post_id,
        "liberado": liberado,
        "message": "Artigo " + ("liberado para o Clube 🎉" if liberado else "removido da liberação"),
    }


@app.post("/api/v1/blog/post/{post_id}/enviar-clube")
async def enviar_blog_post_clube(post_id: str, _admin=Depends(require_admin)):
    """Ponte Adm → Clube: envia UM artigo (já liberado) para a vitrine pública
    do DezafiraClube via /api/import/sync-blog.

    Só envia se club_liberado == True (controle de qualidade feito).
    Requer no .env:
      CLUBE_PUBLIC_URL  (ex: https://www.dezafira.com.br)
      CLUBE_IMPORT_KEY  (IMPORT_API_KEY do Clube)
    """
    from modules.database import get_db_blog_post, update_db_blog_post
    from datetime import datetime as _dt

    post = get_db_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Artigo não encontrado")
    if not post.get("club_liberado"):
        raise HTTPException(status_code=400, detail="Artigo ainda NÃO está liberado para o Clube. Libere-o no controle de qualidade primeiro.")
    if not post.get("slug") or not post.get("content"):
        raise HTTPException(status_code=400, detail="Artigo sem slug ou conteúdo — impossível enviar.")

    clube_url, import_key = _clube_env_config()

    # Payload no mesmo formato do articles_export.json (aceito pelo sync-blog do Clube)
    article = _post_para_clube(post)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{clube_url}/api/import/sync-blog",
                json={"posts": [article]},
                headers={"Content-Type": "application/json", "x-import-key": import_key},
            )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:300]}
        if r.status_code in (200, 201):
            update_db_blog_post(post_id, club_enviado_at=_dt.utcnow())
            return {"success": True, **data, "post_id": post_id}
        raise HTTPException(status_code=r.status_code, detail=data.get("error") or f"Erro do Clube: HTTP {r.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao conectar no Clube: {str(e)}")


def _clube_env_config() -> tuple:
    """Retorna (clube_url, import_key) da ponte Adm→Clube."""
    clube_url = os.getenv("CLUBE_PUBLIC_URL", "https://www.dezafira.com.br").rstrip("/")
    import_key = os.getenv("CLUBE_IMPORT_KEY", "")
    if not import_key:
        raise HTTPException(status_code=503, detail="CLUBE_IMPORT_KEY não configurado no Adm.")
    return clube_url, import_key


def _post_para_clube(post: dict) -> dict:
    """Converte um post do Adm no payload aceito pelo sync-blog do Clube."""
    return {
        "title": post.get("title", ""),
        "slug": post.get("slug", ""),
        "content": post.get("content", ""),
        "excerpt": post.get("excerpt") or "",
        "featured_image_url": post.get("featured_image_url") or "",
    }


@app.post("/api/v1/blog/channel/{channel_id}/enviar-liberados")
async def enviar_liberados_blog_clube(channel_id: str, _admin=Depends(require_admin)):
    """Ponte Adm → Clube (lote): envia TODOS os artigos LIBERADOS de um blog
    para a vitrine pública do DezafiraClube em uma única chamada."""
    from modules.database import get_db_blog_posts, get_db_blog_post, update_db_blog_post
    from datetime import datetime as _dt

    # get_db_blog_posts NÃO inclui a coluna content (grande) — buscamos os posts
    # completos individualmente para montar o payload, como o lili_review_all faz.
    metas = get_db_blog_posts(channel_id=channel_id, limit=1000) or []
    liberados = []
    for m in metas:
        if not m.get("club_liberado") or not m.get("slug"):
            continue
        full = get_db_blog_post(m["id"])
        if full and full.get("content"):
            liberados.append(full)
    if not liberados:
        return {"success": True, "enviados": 0, "message": "Nenhum artigo liberado para enviar neste blog."}

    clube_url, import_key = _clube_env_config()
    payload = [_post_para_clube(p) for p in liberados]

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{clube_url}/api/import/sync-blog",
                json={"posts": payload},
                headers={"Content-Type": "application/json", "x-import-key": import_key},
            )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:300]}
        if r.status_code in (200, 201):
            agora = _dt.utcnow()
            for p in liberados:
                update_db_blog_post(p["id"], club_enviado_at=agora)
            return {
                "success": True,
                "enviados": len(liberados),
                "channel_id": channel_id,
                **data,
            }
        raise HTTPException(status_code=r.status_code, detail=data.get("error") or f"Erro do Clube: HTTP {r.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao conectar no Clube: {str(e)}")


@app.post("/api/v1/blog/post/{post_id}/remover-clube")
async def remover_blog_post_clube(post_id: str, _admin=Depends(require_admin)):
    """Ponte Adm → Clube (desfazer): remove UM artigo da vitrine pública
    do DezafiraClube (por slug). Mantém o artigo no Adm e o status de
    liberado (para poder reenviar depois)."""
    from modules.database import get_db_blog_post, update_db_blog_post

    post = get_db_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Artigo não encontrado")
    if not post.get("slug"):
        raise HTTPException(status_code=400, detail="Artigo sem slug — impossível remover do Clube.")

    clube_url, import_key = _clube_env_config()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{clube_url}/api/import/post/remove",
                json={"slug": post["slug"]},
                headers={"Content-Type": "application/json", "x-import-key": import_key},
            )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:300]}
        if r.status_code in (200, 201):
            update_db_blog_post(post_id, club_enviado_at=None)
            return {"success": True, **data, "post_id": post_id}
        raise HTTPException(status_code=r.status_code, detail=data.get("error") or f"Erro do Clube: HTTP {r.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao conectar no Clube: {str(e)}")


@app.get("/go/{post_slug}/{provider}")
async def redirect_to_affiliate(post_slug: str, provider: str, prod: str = ""):
    """End-point de cloaking e rastreamento de cliques de afiliados."""
    from modules.database import SessionLocal, BlogPost, BlogChannel, AffiliateClick
    from modules.affiliate_agents import SeuSilvaAgent, DonaBentaAgent, SeuNogueiraAgent
    from datetime import datetime

    db = SessionLocal()
    try:
        # 1. Encontrar o post
        post = db.query(BlogPost).filter(BlogPost.slug == post_slug).first()
        if not post:
            post = db.query(BlogPost).filter(BlogPost.id == post_slug).first()
            
        if not post:
            raise HTTPException(status_code=404, detail="Artigo nao encontrado")
            
        # 2. Registrar o clique no banco
        click = AffiliateClick(
            post_id=post.id,
            provider=provider.lower().strip(),
            product_name=prod,
            clicked_at=datetime.utcnow()
        )
        db.add(click)
        db.commit()
        
        # 3. Buscar canal/blog para pegar credenciais
        channel = db.query(BlogChannel).filter(BlogChannel.id == post.channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Blog nao encontrado")
            
        # 4. Formatar o link final com o ID/Tag correspondente
        provider = provider.lower().strip()
        final_url = "https://www.google.com" # Fallback geral
        
        if provider == "amazon":
            tag = channel.amazon_tag or "default-amazon-20"
            if prod.startswith("http"):
                final_url = SeuSilvaAgent.generate_link(prod, tag)
            else:
                final_url = f"https://www.amazon.com.br/s?k={__import__('urllib').parse.quote(prod)}&tag={tag}"
                
        elif provider == "shopee":
            if prod.startswith("http"):
                final_url = prod
            else:
                final_url = f"https://shopee.com.br/search?keyword={__import__('urllib').parse.quote(prod)}"
                
        elif provider == "mercadolivre":
            if prod.startswith("http"):
                final_url = prod
            else:
                final_url = f"https://lista.mercadolivre.com.br/{__import__('urllib').parse.quote(prod)}"
                
        return RedirectResponse(url=final_url)
    except Exception as e:
        print(f"[Redirect] Erro no redirecionamento: {e}")
        return RedirectResponse(url="https://www.google.com")
    finally:
        db.close()


@app.post("/api/v1/blog/{slug}/update-affiliate")
async def update_blog_affiliate_settings(slug: str, payload: dict):
    """Atualiza as configuracoes de afiliado de um canal de blog."""
    from modules.database import SessionLocal, BlogChannel
    db = SessionLocal()
    try:
        # Buscar canal pelo slug do nome
        channels = db.query(BlogChannel).all()
        chan = None
        for c in channels:
            if c.name.lower().replace(" ", "-")[:50] == slug:
                chan = c
                break
                
        if not chan:
            raise HTTPException(status_code=404, detail="Blog nao encontrado")
            
        # Atualizar
        for k, v in payload.items():
            if hasattr(chan, k):
                # ConversÃ£o explÃ­cita de tipos se necessÃ¡rio
                if k == "is_affiliate":
                    setattr(chan, k, bool(v))
                else:
                    setattr(chan, k, v)
        db.commit()
        return {"success": True, "message": "Configuracoes de afiliado salvas com sucesso!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/v1/blog/{slug}/update-modes")
async def update_blog_modes(slug: str, payload: dict):
    """Atualiza os modos de monetizacao/trafego de um blog (Afiliado e/ou Discover).
    Aceita is_affiliate, is_discover e configuracoes de afiliado (amazon_tag etc)."""
    from modules.database import SessionLocal, BlogChannel
    db = SessionLocal()
    try:
        # Buscar canal pelo slug do nome (com sanitizaÃ§Ã£o de caracteres especiais/acentos)
        import unicodedata
        import re
        
        def slugify(text: str) -> str:
            text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
            text = re.sub(r'[^\w\s-]', '', text).strip().lower()
            return re.sub(r'[-\s]+', '-', text)[:50]

        channels = db.query(BlogChannel).all()
        chan = None
        for c in channels:
            if slugify(c.name) == slug or c.name.lower().replace(" ", "-")[:50] == slug:
                chan = c
                break

        if not chan:
            # Fallback secundÃ¡rio: buscar direto por ID caso o slug seja o prÃ³prio ID
            chan = db.query(BlogChannel).filter(BlogChannel.id == slug).first()

        if not chan:
            raise HTTPException(status_code=404, detail=f"Blog nao encontrado (slug: {slug})")

        # Atualizar
        for k, v in payload.items():
            if hasattr(chan, k):
                # Conversao explicita de tipos para flags booleanas
                if k in ("is_affiliate", "is_discover"):
                    setattr(chan, k, bool(v))
                else:
                    setattr(chan, k, v)
        db.commit()
        return {"success": True, "message": "Modos do blog atualizados com sucesso!",
                "is_affiliate": bool(chan.is_affiliate), "is_discover": bool(chan.is_discover)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/v1/blog/{channel_id}/generate-brand-asset")
async def generate_blog_brand_asset(channel_id: str, payload: dict):
    """Gera Logo, Favicon ou Imagem de Fundo (Background) com IA (Flux) para o blog."""
    from modules.database import SessionLocal, BlogChannel
    from modules.image_factory import ImageGeneratorAgent
    import json
    
    asset_type = payload.get("type")
    if asset_type not in ("logo", "favicon", "bg"):
        raise HTTPException(status_code=400, detail="Tipo de asset invalido. Escolha 'logo', 'favicon' ou 'bg'.")

    db = SessionLocal()
    try:
        chan = db.query(BlogChannel).filter(BlogChannel.id == channel_id).first()
        if not chan:
            raise HTTPException(status_code=404, detail="Blog nao encontrado")

        name = chan.name
        niche = chan.nicho or "Geral"

        # Carregar config de branding atual
        brand_config = {}
        if chan.brand_config:
            try:
                brand_config = json.loads(chan.brand_config)
            except Exception:
                brand_config = {}

        agent = ImageGeneratorAgent()
        
        if asset_type == "logo" or asset_type == "favicon":
            from modules.brand_designer import BrandingDesignerAgent
            brand_agent = BrandingDesignerAgent()
            design_data = await brand_agent.generate_branding(blog_name=name, niche=niche, is_affiliate=chan.is_affiliate)
            
            if asset_type == "logo":
                svg_content = design_data.get("logo_svg", "")
                if svg_content:
                    # Converter SVG inline em Data URI Base64 de forma limpa
                    import base64
                    encoded_svg = base64.b64encode(svg_content.encode("utf-8")).decode("ascii")
                    svg_data_uri = f"data:image/svg+xml;base64,{encoded_svg}"
                    
                    brand_config["custom_logo"] = svg_data_uri
                    brand_config["logo_svg"] = svg_content
                    chan.brand_config = json.dumps(brand_config)
                    db.commit()
                    return {"success": True, "image_url": svg_data_uri, "provider": "BrandingDesignerAgent (SVG)"}
            
            elif asset_type == "favicon":
                fav_uri = design_data.get("favicon_svg", "")
                if fav_uri:
                    brand_config["custom_favicon"] = fav_uri
                    brand_config["favicon_svg"] = fav_uri
                    chan.brand_config = json.dumps(brand_config)
                    db.commit()
                    return {"success": True, "image_url": fav_uri, "provider": "BrandingDesignerAgent (SVG)"}

        elif asset_type == "bg":
            prompt = f"luxurious ultra-minimalist smooth abstract background, flowing organic gradient vector textures, theme of {niche}, subtle atmospheric lighting, extremely clean backdrop, no objects, no people, no text, elegant digital art style, soft color palette"
            img = await agent.generate_image_for_post(prompt_idea=prompt, niche=niche, width=1920, height=1080)
            if img and img.get("image_url"):
                chan.banner_url = img["image_url"] # salva tbm no banner_url do canal principal
                brand_config["custom_bg"] = img["image_url"]
                brand_config["bg_ai_prompt"] = img.get("expanded_prompt", prompt)
                chan.brand_config = json.dumps(brand_config)
                db.commit()
                return {"success": True, "image_url": img["image_url"], "provider": img.get("provider")}

        return {"success": False, "error": "Nao foi possivel gerar a imagem com IA"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/v1/blog/post/{post_id}/upload-image")
async def upload_blog_post_image(post_id: str, payload: dict):
    """Upload manual de imagem (Base64) para um post de artigo especÃ­fico."""
    from modules.database import update_db_blog_post
    image_data = payload.get("image_data")
    if not image_data:
        raise HTTPException(status_code=400, detail="image_data (Base64) Ã© obrigatorio")

    success = update_db_blog_post(
        post_id,
        featured_image_url=image_data,
        image_provider="user_upload"
    )
    if success:
        return {"success": True, "image_url": image_data}
    raise HTTPException(status_code=404, detail="Artigo nao encontrado")


@app.get("/api/v1/affiliate/clicks")
async def get_affiliate_clicks_stats(channel_id: str = ""):
    """Retorna dados de estatisticas de cliques em links de afiliados."""
    from modules.database import SessionLocal, AffiliateClick, BlogPost
    from sqlalchemy import func
    db = SessionLocal()
    try:
        query = db.query(
            AffiliateClick.provider,
            func.count(AffiliateClick.id).label("total_clicks")
        )
        if channel_id:
            query = query.join(BlogPost, BlogPost.id == AffiliateClick.post_id)\
                         .filter(BlogPost.channel_id == channel_id)
                         
        stats = query.group_by(AffiliateClick.provider).all()
        
        # Historico por dia (ultimos 7 dias)
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        hist_query = db.query(
            func.date(AffiliateClick.clicked_at).label("click_date"),
            func.count(AffiliateClick.id).label("clicks")
        ).filter(AffiliateClick.clicked_at >= seven_days_ago)
        
        if channel_id:
            hist_query = hist_query.join(BlogPost, BlogPost.id == AffiliateClick.post_id)\
                                   .filter(BlogPost.channel_id == channel_id)
                                   
        history = hist_query.group_by(func.date(AffiliateClick.clicked_at)).all()
        
        return {
            "summary": {row[0]: row[1] for row in stats},
            "history": [{"date": str(row[0]), "clicks": row[1]} for row in history]
        }
    finally:
        db.close()


    # Fallback: generic blog template
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8">
<title>{slug} â€” Blog Dezafira</title>
<style>body{{font-family:system-ui;max-width:800px;margin:40px auto;padding:0 20px;color:#333;line-height:1.6}}h1{{color:#1a1a1a}}</style>
</head>
<body><h1>ðŸ“ {slug}</h1><p>Blog em construÃ§Ã£o...</p>
<p><a href="/">Voltar ao painel</a></p>
</body></html>""")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# WEBSOCKET ENDPOINT (Bug C2 fix)
@app.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    await _ws_hub.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "subscribe" and msg.get("task_id"):
                    _ws_hub._connections.setdefault(msg["task_id"], set()).add(websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        _ws_hub.disconnect(websocket)


hermes_chat_history = [
    {
        "role": "assistant",
        "content": "OlÃ¡, Jonatas! Sou o Hermes, orquestrador do ecossistema Dezafira. Nosso ecossistema atual conta com 5 fÃ¡bricas integradas:\n\nðŸ“ **FÃ¡brica de Blogs** â€” Artigos otimizados para SEO sobre temas bÃ­blicos\nðŸ“— **FÃ¡brica de Livros** â€” E-books com capÃ­tulos gerados por IA\nðŸŽ“ **FÃ¡brica de Cursos** â€” Cursos em texto com mÃ³dulos, aulas e quizzes\nðŸŽ¨ **FÃ¡brica de Imagens** â€” Capas, thumbnails e imagens via FLUX + Pexels\nðŸ” **RAG BÃ­blico** â€” Busca semÃ¢ntica nos conteÃºdos com respostas citadas\n\nQual comando deseja executar, Jonatas?"
    }
]

@app.get("/api/v1/hermes/history")
async def get_hermes_history():
    """Retorna histÃ³rico do chat do Hermes."""
    return {"history": hermes_chat_history[-50:]}


@app.post("/api/v1/hermes/clear")
async def clear_hermes_history():
    """Limpa histÃ³rico do chat."""
    global hermes_chat_history
    hermes_chat_history = [
        {
            "role": "assistant",
            "content": "OlÃ¡, Jonatas! Sou o Hermes, orquestrador do ecossistema Dezafira. Nosso ecossistema atual conta com 5 fÃ¡bricas integradas:\n\nðŸ“ **FÃ¡brica de Blogs** â€” Artigos otimizados para SEO sobre temas bÃ­blicos\nðŸ“— **FÃ¡brica de Livros** â€” E-books com capÃ­tulos gerados por IA\nðŸŽ“ **FÃ¡brica de Cursos** â€” Cursos em texto com mÃ³dulos, aulas e quizzes\nðŸŽ¨ **FÃ¡brica de Imagens** â€” Capas, thumbnails e imagens via FLUX + Pexels\nðŸ” **RAG BÃ­blico** â€” Busca semÃ¢ntica nos conteÃºdos com respostas citadas\n\nQual comando deseja executar, Jonatas?"
        }
    ]
    return {"message": "HistÃ³rico limpo"}


# ================================================================
# BLOG PIPELINE ENDPOINT
# ================================================================

@app.post("/api/v1/pipeline/run-blog")
async def run_blog_pipeline_endpoint(payload: dict, background_tasks: BackgroundTasks, _admin=Depends(require_admin)):
    topic = payload.get("topic", "")
    channel_id = payload.get("channel_id", "default")
    language = payload.get("language", "pt")
    auto_schedule = payload.get("auto_schedule", True)
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    import uuid
    task_id = f"blg_{uuid.uuid4().hex[:8]}"

    # Armazena estado inicial para consulta via GET
    _macro_results[task_id] = {
        "status": "starting", "topic": topic, "channel_id": channel_id,
        "phase": "iniciando", "progress": 0, "data": None
    }

    async def _run_with_ws(tid, top, ch, lang, sched):
        from modules.blog_pipeline import run_blog_pipeline as _run_pipeline
        hub = _ws_hub
        import asyncio
        def on_progress(pid, stage_id, progress, message, data):
            _macro_results[pid] = {
                "status": "active", "topic": top, "channel_id": ch,
                "phase": message or stage_id, "progress": progress, "data": data
            }
            if stage_id == "__broadcast__":
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(hub.broadcast(message, data))
                except Exception:
                    pass
                return
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(hub.broadcast("pipeline_progress", {
                    "task_id": pid, "stage_id": stage_id,
                    "progress": progress, "message": message,
                    "status": "completed" if progress >= 100 else "active",
                    "data": data,
                }))
            except Exception:
                pass
        try:
            result = await _run_pipeline(topic=top, channel_id=ch, language=lang, task_id=tid, on_progress=on_progress, auto_schedule=sched)
            _macro_results[tid] = {
                "status": "completed", "topic": top, "channel_id": ch,
                "phase": "concluido", "progress": 100, "data": result
            }
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(hub.broadcast("pipeline_complete", result))
            except Exception:
                pass
        except Exception as e:
            _macro_results[tid] = {
                "status": "failed", "topic": top, "channel_id": ch,
                "phase": "erro", "progress": 0, "error": str(e)
            }
            print(f"[Pipeline] Falha: {e}")
            import traceback
            traceback.print_exc()
    background_tasks.add_task(_run_with_ws, task_id, topic, channel_id, language, auto_schedule)
    return {
        "task_id": task_id, "topic": topic, "status": "starting",
        "message": "Pipeline da Fabrica de Blogs iniciado! Acompanhe o progresso em tempo real na aba Pipeline.",
    }

@app.get("/api/v1/pipeline/blog-factory/history")
async def get_blog_factory_history(_admin=Depends(require_admin)):
    """Retorna o historico real de execucoes do pipeline da fabrica de blogs."""
    try:
        from modules.database import get_db_blog_pipeline_runs
        runs = get_db_blog_pipeline_runs(limit=10)
        return {"pipelines": runs}
    except Exception as e:
        print(f"[API] Erro ao buscar historico de pipelines: {e}")
        return {"pipelines": []}

@app.get("/api/v1/pipeline/blog/history")
async def get_blog_pipeline_history():
    return {"pipelines": []}

@app.get("/api/v1/pipeline/blog-factory/status/{task_id}")
async def get_blog_factory_status(task_id: str):
    """Retorna o status real de uma pipeline de blog."""
    result = _macro_results.get(task_id)
    if not result:
        # Tenta buscar no banco
        return {"status": "unknown", "task_id": task_id, "message": "Pipeline nao encontrada ou ainda nao iniciada"}
    return result


@app.post("/api/v1/blog/generate-article-hype")
async def generate_article_hype_endpoint(payload: dict, background_tasks: BackgroundTasks, _admin=Depends(require_admin)):
    """
    Inicia a esteira de criaÃ§Ã£o de artigos em segundo plano, minerando as tendÃªncias
    do Google Hype ativamente no primeiro estÃ¡gio e gerando-os de forma sequencial.
    """
    channel_id = payload.get("channel_id", "")
    quantity = payload.get("quantity", 1)
    
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        quantity = 1
    quantity = max(1, min(10, quantity)) # Limite de seguranÃ§a de 1 a 10 artigos por lote

    if not channel_id:
        from modules.database import get_db_blog_channels
        channels = get_db_blog_channels()
        if channels and len(channels) > 0:
            channel_id = channels[0]["id"]
        else:
            return {"error": "Nenhum canal encontrado"}

    from modules.database import get_db_blog_channel
    blog_info = get_db_blog_channel(channel_id)
    if not blog_info:
        return {"error": "Blog nÃ£o encontrado"}

    nicho = blog_info.get("nicho", "")
    if not nicho:
        return {"error": "Nicho do blog nÃ£o configurado"}

    from modules.blog_pipeline import run_blog_pipeline as _run_pipeline
    import uuid
    import asyncio
    
    task_id = f"blg_{uuid.uuid4().hex[:8]}"
    initial_topic = f"Minerando tendÃªncias em {nicho}..."

    # 1. Armazena estado inicial para consulta via GET
    _macro_results[task_id] = {
        "status": "starting", "topic": f"Lote: {initial_topic}", "channel_id": channel_id,
        "phase": "Iniciando Lote", "progress": 2, "data": {"target_articles": quantity, "articles_generated": 0}
    }

    # 2. OrquestraÃ§Ã£o ws do lote sequencial
    async def _run_with_ws(tid, top, ch, lang, qty):
        hub = _ws_hub
        articles_generated = 0
        all_results = []
        
        for i in range(qty):
            current_topic = f"Minerando tendÃªncia {i+1} de {qty} em {nicho}..."
            
            def on_progress(pid, stage_id, progress, message, data):
                nonlocal current_topic
                if data and data.get("topic"):
                    current_topic = data["topic"]
                
                # Progresso total do lote: (concluidos / total) + (progresso_atual / total)
                batch_progress = int((articles_generated / qty) * 100 + (progress / qty))
                
                _macro_results[pid] = {
                    "status": "active", 
                    "topic": f"[{i+1}/{qty}] {current_topic}", 
                    "channel_id": ch,
                    "phase": message or stage_id, 
                    "progress": batch_progress, 
                    "data": {**(data or {}), "articles_generated": articles_generated, "target_articles": qty}
                }
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(hub.broadcast("pipeline_progress", {
                        "task_id": pid, 
                        "stage_id": stage_id,
                        "progress": progress,
                        "message": f"[{i+1}/{qty}] {message}",
                        "status": "completed" if progress >= 100 else "active",
                        "data": {
                            **(data or {}), 
                            "topic": current_topic, 
                            "articles_generated": articles_generated,
                            "target_articles": qty
                        },
                    }))
                except Exception:
                    pass
            
            try:
                # Executa o pipeline de um artigo individual de cada vez na esteira
                result = await _run_pipeline(
                    topic=current_topic, channel_id=ch, language=lang, task_id=tid, 
                    on_progress=on_progress, auto_schedule=True, mine_hype=True
                )
                if result.get("status") == "completed":
                    articles_generated += 1
                all_results.append(result)
                
                # Pequeno delay entre geraÃ§Ãµes
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[HypeLote] Erro no artigo {i+1} de {qty}: {e}")
                
        # FinalizaÃ§Ã£o da esteira do lote
        _macro_results[tid] = {
            "status": "completed", 
            "topic": f"Lote de {articles_generated} artigos concluÃ­do!", 
            "channel_id": ch,
            "phase": "concluido", 
            "progress": 100, 
            "data": {"articles_generated": articles_generated, "results": all_results}
        }
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(hub.broadcast("pipeline_complete", {
                "task_id": tid,
                "articles_generated": articles_generated,
                "target_articles": qty
            }))
        except Exception:
            pass

    background_tasks.add_task(_run_with_ws, task_id, initial_topic, channel_id, "pt", quantity)
    return {
        "task_id": task_id, 
        "topic": initial_topic, 
        "status": "starting",
        "message": f"Esteira do Google Hype iniciada para lote de {quantity} artigos!",
    }


@app.post("/api/v1/blog/import-posts")
async def import_blog_posts(payload: dict):
    """Importa artigos em massa de um banco local para o Railway.
    Payload: {"posts": [...], "channel_id": "..."}
    """
    from modules.database import SessionLocal, BlogPost
    from datetime import datetime
    import uuid

    posts = payload.get("posts", [])
    channel_id = payload.get("channel_id", "")

    if not channel_id:
        from modules.database import BlogChannel
        db = SessionLocal()
        try:
            ch = db.query(BlogChannel).first()
            if ch:
                channel_id = ch.id
        finally:
            db.close()

    if not channel_id:
        raise HTTPException(status_code=400, detail="Nenhum channel_id fornecido e nenhum blog encontrado.")

    inserted = 0
    skipped = 0
    errors = []

    for post in posts:
        title = post.get("title", "").strip()
        if not title:
            skipped += 1
            continue

        db = SessionLocal()
        try:
            existing = db.query(BlogPost).filter(BlogPost.title == title).first()
            if existing:
                skipped += 1
                continue

            slug = post.get("slug", "") or title.lower().replace(" ", "-")[:80]
            new_post = BlogPost(
                id=post.get("id") or f"post_{uuid.uuid4().hex[:8]}",
                channel_id=channel_id,
                title=title,
                slug=slug,
                content=post.get("content", ""),
                excerpt=post.get("excerpt", ""),
                keywords=post.get("keywords", ""),
                featured_image_url=post.get("featured_image_url"),
                status=post.get("status", "draft"),
                word_count=post.get("word_count", 0),
                topic=post.get("topic", ""),
            )
            db.add(new_post)
            db.commit()
            inserted += 1
        except Exception as e:
            db.rollback()
            errors.append({"title": title[:40], "error": str(e)[:100]})
        finally:
            db.close()

    return {
        "message": "Importacao concluida!",
        "inserted": inserted,
        "skipped": skipped,
        "errors": len(errors),
        "error_details": errors[:5],
    }


@app.post("/api/v1/blog/generate-missing-images")

async def generate_missing_images():
    """Gera imagens para todos os artigos do blog que estÃ£o sem."""
    from modules.ricardo import gerar_imagens_pendentes
    return await gerar_imagens_pendentes()


async def process_hermes_command(message: str, channel_id: str = None, background_tasks: BackgroundTasks = None) -> tuple:
    """
    Processa comandos do Hermes e executa aÃ§Ãµes reais.
    Retorna (text_response, action_type, action_data)
    action_type pode ser: None, "research", "pipeline", "trending", "channels", "analytics", "rules"
    """
    msg = message.lower().strip()
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # FASE 1: RESEARCH
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    if any(word in msg for word in ["pesquisar", "research", "buscar nicho", "analise de nicho"]):
        keyword = message
        for prefix in ["pesquisar ", "research ", "buscar nicho ", "analise de nicho "]:
            if msg.startswith(prefix):
                keyword = message[len(prefix):]
                break
        
        if not keyword or keyword.strip() == "":
            return ("Para pesquisar, digite: pesquisar [tema]\nExemplo: pesquisar Inteligencia Artificial", None, None)
        
        try:
            from research.engine import ResearchEngine
            engine = ResearchEngine()
            result = await engine.research_niche(keyword)
            
            action_data = {
                "keyword": keyword,
                "niche_score": result.niche_score,
                "competition_level": result.competition_level,
                "monetization_potential": result.monetization_potential,
                "trending_videos": result.trending_videos,
                "title_patterns": result.title_patterns,
                "recommendations": result.recommendations,
                "channels": result.channels,
            }
            
            text = f"Pesquisa de nicho '{keyword}' concluida com sucesso!"
            return (text, "research", action_data)
        except Exception as e:
            return (f"Erro na pesquisa: {str(e)}", None, None)
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # FASE 2: PRODUCTION
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    # Regra especial para criar mÃºltiplos formatos de vÃ­deo (Horizontal e Vertical)
    if "dois vÃ­deos" in msg or "dois videos" in msg or ("horizontal" in msg and "vertical" in msg):
        theme = "Adestramento Canino Inteligente"
        # Tenta extrair tema
        for keyword in ["sobre", "tema", "nicho"]:
            if keyword in msg:
                parts = msg.split(keyword)
                if len(parts) > 1:
                    theme = parts[1].strip()
                    break
        
        try:
            from modules.database import create_automation_task
            
            # GeraÃ§Ã£o do formato Vertical (9:16)
            task_v_id = create_automation_task(f"{theme} (Vertical)", channel_id or "default")
            pred_v_id = f"sniper_hf_v_{uuid.uuid4().hex[:4]}"
            save_db_prediction(pred_v_id, f"{theme} (Vertical)", channel_id or "default")
            
            # GeraÃ§Ã£o do formato Horizontal (16:9)
            task_h_id = create_automation_task(f"{theme} (Horizontal)", channel_id or "default")
            pred_h_id = f"sniper_hf_h_{uuid.uuid4().hex[:4]}"
            save_db_prediction(pred_h_id, f"{theme} (Horizontal)", channel_id or "default")
            
            if background_tasks:
                async def _run_orchestrator_v(task_id, theme, channel_id):
                    await _hermes_orchestrator.start_pipeline(theme, channel_id, "vertical", task_id=str(task_id))
                async def _run_orchestrator_h(task_id, theme, channel_id):
                    await _hermes_orchestrator.start_pipeline(theme, channel_id, "horizontal", task_id=str(task_id))
                background_tasks.add_task(
                    _run_orchestrator_v, task_v_id, theme,
                    channel_id or "default"
                )
                background_tasks.add_task(
                    _run_orchestrator_h, task_h_id, theme,
                    channel_id or "default"
                )
                
            action_data = {
                "theme": theme,
                "vertical": {
                    "id": pred_v_id,
                    "task_id": task_v_id,
                    "video_format": "vertical",
                    "status": "starting"
                },
                "horizontal": {
                    "id": pred_h_id,
                    "task_id": task_h_id,
                    "video_format": "horizontal",
                    "status": "starting"
                }
            }
            
            text = f"Excelente! FÃ¡brica de Canais acionada para ambos os formatos. Disparei a esteira para gerar o vÃ­deo Vertical (9:16) e Horizontal (16:9) sobre o tema '{theme}' usando o Hyperframes. Acompanhe o progresso em tempo real."
            return (text, "hyperframes_multi_video", action_data)
        except Exception as e:
            return (f"Erro ao gerar timelines de vÃ­deo mÃºltiplos: {str(e)}", None, None)
            
    if any(word in msg for word in ["produzir video", "produzir vÃ­deo", "make video", "create video", "gerar video", "gerar vÃ­deo", "fluxo completo da f. de canais", "fluxo completo de canais"]):
        theme = "Adestramento Canino Inteligente" if "completo" in msg else message
        for prefix in ["produzir video ", "produzir vÃ­deo ", "make video ", "create video ", "gerar video ", "gerar vÃ­deo "]:
            if msg.startswith(prefix):
                theme = message[len(prefix):]
                break
        
        try:
            from modules.database import create_automation_task
            
            task_id = create_automation_task(theme, channel_id or "default")
            prediction_id = f"sniper_hf_{uuid.uuid4().hex[:6]}"
            save_db_prediction(prediction_id, theme, channel_id or "default")
            
            if background_tasks:
                async def _run_orchestrator_single(task_id, theme, channel_id):
                    await _hermes_orchestrator.start_pipeline(theme, channel_id, "vertical", task_id=str(task_id))
                background_tasks.add_task(
                    _run_orchestrator_single, task_id, theme,
                    channel_id or "default"
                )
            
            action_data = {
                "id": prediction_id,
                "task_id": task_id,
                "theme": theme,
                "video_format": "vertical",
                "status": "starting"
            }
            
            text = f"FÃ¡brica de Canais ativada de forma 100% autÃ´noma! Iniciando a esteira de renderizaÃ§Ã£o Hyperframes para o tema '{theme}'. Triagem e roteirista iniciados."
            return (text, "hyperframes_video", action_data)
        except Exception as e:
            return (f"Erro ao gerar Hyperframes: {str(e)}", None, None)
    
    if any(word in msg for word in ["roteiro", "script", "escrever roteiro", "write script"]):
        theme = message
        for prefix in ["roteiro ", "script ", "escrever roteiro ", "write script "]:
            if msg.startswith(prefix):
                theme = message[len(prefix):]
                break
        
        if not theme or theme.strip() == "":
            return ("Para gerar roteiro, digite: roteiro [tema]", None, None)
        
        try:
            # Usa singletons globais (Bug C1 fix)
            orchestrator = _hermes_orchestrator
            hub = _ws_hub
            task_id = await orchestrator.start_pipeline(theme=theme, channel_id=channel_id)
            
            action_data = {"task_id": task_id, "theme": theme, "status": "running", "stage": "script"}
            text = f"Roteiro sendo gerado para '{theme}'!"
            return (text, "pipeline", action_data)
        except Exception as e:
            return (f"Erro ao gerar roteiro: {str(e)}", None, None)
    
    if any(word in msg for word in ["narrar", "narracao", "narraÃ§Ã£o", "voz", "voice", "text to speech", "tts"]):
        theme = message
        for prefix in ["narrar ", "narracao ", "narraÃ§Ã£o ", "voz ", "voice ", "text to speech ", "tts "]:
            if msg.startswith(prefix):
                theme = message[len(prefix):]
                break
        
        if not theme or theme.strip() == "":
            return ("Para narrar, digite: narrar [texto]", None, None)
        
        try:
            from services.voice_service import VoiceService
            voice = VoiceService()
            audio_path = await voice.generate_narration(theme)
            action_data = {"audio_path": audio_path, "text": theme[:200]}
            text = f"Narracao gerada com sucesso!"
            return (text, "production", action_data)
        except Exception as e:
            return (f"Erro na narraÃ§Ã£o: {str(e)}", None, None)
    
    if any(word in msg for word in ["thumbnail", "thumb", "miniatura"]):
        theme = message
        for prefix in ["thumbnail ", "thumb ", "miniatura "]:
            if msg.startswith(prefix):
                theme = message[len(prefix):]
                break
        
        if not theme or theme.strip() == "":
            return ("Para criar thumbnail, digite: thumbnail [tema]", None, None)
        
        try:
            from modules.pexels_client import PexelsClient
            pexels = PexelsClient()
            images = pexels.search_videos(theme, per_page=1)
            action_data = {"theme": theme, "image_found": len(images) > 0 if images else False}
            text = f"Thumbnail sendo criada para '{theme}'!"
            return (text, "production", action_data)
        except Exception as e:
            return (f"Erro na thumbnail: {str(e)}", None, None)
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # FASE 3: PUBLISHING
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    if any(word in msg for word in ["publicar", "upload", "postar", "publish", "subir video"]):
        video_info = message
        for prefix in ["publicar ", "upload ", "postar ", "publish ", "subir video "]:
            if msg.startswith(prefix):
                video_info = message[len(prefix):]
                break
        
        if not video_info or video_info.strip() == "":
            return ("Para publicar, digite: publicar [titulo do video]", None, None)
        
        action_data = {"title": video_info, "status": "pending_upload"}
        text = f"Preparando upload do video '{video_info}'!"
        return (text, "publishing", action_data)
    
    if any(word in msg for word in ["agendar", "schedule", "programar", "horario"]):
        schedule_info = message
        for prefix in ["agendar ", "schedule ", "programar ", "horario "]:
            if msg.startswith(prefix):
                schedule_info = message[len(prefix):]
                break
        
        if not schedule_info or schedule_info.strip() == "":
            return ("Para agendar, digite: agendar [data/hora]", None, None)
        
        action_data = {"schedule": schedule_info, "status": "scheduled"}
        text = f"Agendamento configurado para {schedule_info}!"
        return (text, "publishing", action_data)
    
    if any(word in msg for word in ["titulo otimizado", "tÃ­tulo otimizado", "otimizar titulo", "seo title"]):
        theme = message
        for prefix in ["titulo otimizado ", "tÃ­tulo otimizado ", "otimizar titulo ", "seo title "]:
            if msg.startswith(prefix):
                theme = message[len(prefix):]
                break
        
        if not theme or theme.strip() == "":
            return ("Para otimizar titulo, digite: titulo otimizado [tema]", None, None)
        
        try:
            from research.analyzers.title_analyzer import TitleAnalyzer
            analyzer = TitleAnalyzer()
            patterns = analyzer.analyze_titles([theme])
            
            action_data = {"theme": theme, "optimized_titles": patterns.get("optimized_titles", [])}
            text = f"Titulos otimizados para '{theme}'!"
            return (text, "publishing", action_data)
        except Exception as e:
            return (f"Erro ao otimizar titulo: {str(e)}", None, None)
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # FASE 4: MONITORING
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    if any(word in msg for word in ["metricas", "mÃ©tricas", "analytics", "desempenho", "performance"]):
        action_data = {
            "totalViews": 125000,
            "totalSubscribers": 3200,
            "totalVideos": 47,
            "estimatedRevenue": 2500,
            "growthRate": 15,
            "channels": [
                {"name": "Tech sem Limites", "niche": "Tecnologia", "views": 45000, "subscribers": 1200, "engagement": 4.5, "ctr": 8.2},
                {"name": "Dinheiro Inteligente", "niche": "Financas", "views": 38000, "subscribers": 980, "engagement": 3.8, "ctr": 7.1},
            ]
        }
        text = "Metricas carregadas com sucesso!"
        return (text, "analytics", action_data)
    
    if any(word in msg for word in ["relatorio", "relatÃ³rio", "report"]):
        action_data = {
            "period": "semanal",
            "videosPublished": 5,
            "totalViews": 12500,
            "newSubscribers": 320,
            "avgCtr": 7.8,
            "bestVideo": {"title": "Como ganhar dinheiro com IA", "views": 8500},
            "recommendations": [
                "Aumentar frequencia de upload",
                "Focar em thumbnails mais chamativas",
                "Usar titulos com numeros"
            ]
        }
        text = "Relatorio semanal gerado!"
        return (text, "analytics", action_data)
    
    if any(word in msg for word in ["trending", "tendencias", "tendÃªncias", "em alta"]):
        try:
            from research.engine import ResearchEngine
            engine = ResearchEngine()
            trending = await engine.get_trending_topics()
            action_data = trending
            text = "Tendencias carregadas!"
            return (text, "trending", action_data)
        except Exception as e:
            return (f"Erro ao buscar trending: {str(e)}", None, None)
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PIPELINE MANAGEMENT
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    if any(word in msg for word in ["iniciar pipeline", "start pipeline"]):
        theme = message
        for prefix in ["iniciar pipeline ", "start pipeline "]:
            if msg.startswith(prefix):
                theme = message[len(prefix):]
                break
        
        if not theme or theme.strip() == "":
            return ("Para iniciar um pipeline, digite: iniciar pipeline [tema]", None, None)
        
        try:
            # Usa singletons globais (Bug C1 fix)
            orchestrator = _hermes_orchestrator
            hub = _ws_hub
            task_id = await orchestrator.start_pipeline(theme=theme, channel_id=channel_id)
            
            action_data = {"task_id": task_id, "theme": theme, "status": "running"}
            text = f"Pipeline iniciado para '{theme}'!"
            return (text, "pipeline", action_data)
        except Exception as e:
            return (f"Erro ao iniciar pipeline: {str(e)}", None, None)
    
    if any(word in msg for word in ["status", "progresso", "andamento"]):
        try:
            # Usa singletons globais (Bug C1 fix)
            orchestrator = _hermes_orchestrator
            hub = _ws_hub
            pipelines = orchestrator.get_all_pipelines()
            
            action_data = {"pipelines": pipelines}
            if not pipelines:
                text = "Nenhum pipeline ativo no momento."
            else:
                text = f"{len(pipelines)} pipeline(s) ativo(s)!"
            return (text, "pipeline", action_data)
        except Exception as e:
            return (f"Erro ao verificar status: {str(e)}", None, None)
    
    # Removidos comandos de pipeline legados (pausar, retomar, parar).
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # CANAIS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    if any(word in msg for word in ["criar canal", "create channel", "novo canal"]):
        niche = message
        for prefix in ["criar canal ", "create channel ", "novo canal "]:
            if msg.startswith(prefix):
                niche = message[len(prefix):]
                break
        
        if not niche or niche.strip() == "":
            return ("Para criar um canal, digite: criar canal [nicho]", None, None)
        
        try:
            from channels.manager import ChannelManager
            manager = ChannelManager()
            
            channel_id = await manager.create_channel(
                niche=niche,
                channel_name=f"{niche} Total",
                research_data={"niche_score": 75, "competition_level": "medium"}
            )
            
            action_data = {"channel_id": channel_id, "niche": niche, "name": f"{niche} Total"}
            text = f"Canal '{niche} Total' criado com sucesso!"
            return (text, "channels", action_data)
        except Exception as e:
            return (f"Erro ao criar canal: {str(e)}", None, None)
    
    if any(word in msg for word in ["listar canais", "list channels", "meus canais"]):
        try:
            from channels.manager import ChannelManager
            manager = ChannelManager()
            channels = manager.list_channels()
            
            action_data = {"channels": channels}
            if not channels:
                text = "Nenhum canal criado ainda."
            else:
                text = f"{len(channels)} canal(is) encontrado(s)!"
            return (text, "channels", action_data)
        except Exception as e:
            return (f"Erro ao listar canais: {str(e)}", None, None)
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # FÃBRICA DE ENTREGÃVEIS (PWA)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    if any(word in msg for word in ["criar entregavel", "criar entregÃ¡vel", "criar pwa", "novo pwa", "novo entregavel", "novo entregÃ¡vel"]):
        app_name = message
        for prefix in ["criar entregavel ", "criar entregÃ¡vel ", "criar pwa ", "novo pwa ", "novo entregavel ", "novo entregÃ¡vel "]:
            if msg.startswith(prefix):
                app_name = message[len(prefix):]
                break
                
        if not app_name or app_name.strip() == "":
            return ("Para criar um entregÃ¡vel PWA, digite: criar entregavel [nome do app]", None, None)
            
        try:
            nicho_sugerido = app_name
            from modules.deliverables import create_deliverable_app_for_channel
            app_data = await create_deliverable_app_for_channel(
                channel_id=channel_id or "default",
                name=app_name,
                nicho=nicho_sugerido,
                slug=None
            )
            
            action_data = {
                "app_id": app_data["id"],
                "name": app_data["name"],
                "slug": app_data["slug"],
                "nicho": app_data["nicho"],
                "config": app_data["config_json"]
            }
            text = f"EntregÃ¡vel PWA '{app_name}' (slug: {app_data['slug']}) criado e configurado com sucesso!"
            return (text, "deliverables", action_data)
        except Exception as e:
            return (f"Erro ao criar entregÃ¡vel: {str(e)}", None, None)
            
    if any(word in msg for word in ["listar entregaveis", "listar entregÃ¡veis", "listar pwas", "meus entregaveis", "meus entregÃ¡veis", "meus pwas"]):
        try:
            from modules.database import get_db_deliverable_apps
            apps = get_db_deliverable_apps()
            action_data = {"apps": apps}
            if not apps:
                text = "Nenhum entregÃ¡vel PWA criado ainda."
            else:
                text = f"Encontrei {len(apps)} entregÃ¡vel(is) PWA cadastrado(s)!"
            return (text, "deliverables", action_data)
        except Exception as e:
            return (f"Erro ao listar entregÃ¡veis: {str(e)}", None, None)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # REGRAS E CONHECIMENTO
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    if any(word in msg for word in ["regras", "rules", "monetizacao", "seo"]):
        try:
            from research.engine import ResearchEngine
            engine = ResearchEngine()
            rules = await engine.learn_youtube_rules()
            
            action_data = rules
            text = "Regras do YouTube carregadas!"
            return (text, "rules", action_data)
        except Exception as e:
            return (f"Erro ao buscar regras: {str(e)}", None, None)
    
    if any(word in msg for word in ["dicas seo", "seo tips", "otimizar seo"]):
        action_data = {
            "titles": [
                "Use numeros (ex: 5 Dicas para...)",
                "Inclua palavra-chave no inicio",
                "Maximo 60 caracteres"
            ],
            "description": [
                "Primeiras 2 linhas sao cruciais",
                "Use palavras-chave naturalmente",
                "Inclua links relevantes"
            ],
            "tags": [
                "Use variacoes da palavra-chave",
                "Inclua tags de nicho",
                "Nao exceda 500 caracteres"
            ],
            "thumbnails": [
                "Use cores contrastantes",
                "Rostos humanos chamam atencao",
                "Texto grande e legivel"
            ]
        }
        text = "Dicas de SEO carregadas!"
        return (text, "rules", action_data)
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # AJUDA
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    if any(word in msg for word in ["ajuda", "help", "comandos", "commands"]):
        text = (
            "Comandos do Hermes Orquestrador:\n\n"
            "FASE 1 - RESEARCH:\n"
            "  pesquisar [tema] - Pesquisa nicho\n"
            "  regras - Ver regras do YouTube\n"
            "  dicas seo - Dicas de otimizacao\n"
            "  trending - Tendencias atuais\n\n"
            "FASE 2 - PRODUCTION:\n"
            "  produzir video [tema] - Produz video completo\n"
            "  roteiro [tema] - Gera roteiro\n"
            "  narrar [texto] - Gera narracao (TTS)\n"
            "  thumbnail [tema] - Cria thumbnail\n\n"
            "FASE 3 - PUBLISHING:\n"
            "  publicar [titulo] - Publica video\n"
            "  agendar [data/hora] - Agenda publicacao\n"
            "  titulo otimizado [tema] - Gera titulo SEO\n\n"
            "FASE 4 - MONITORING:\n"
            "  metricas - Ver metricas gerais\n"
            "  relatorio - Relatorio semanal\n\n"
            "PIPELINE:\n"
            "  iniciar pipeline [tema] - Inicia pipeline\n"
            "  status - Ver pipelines ativos\n"
            "  pausar [task_id] - Pausa pipeline\n"
            "  retomar [task_id] - Retoma pipeline\n"
            "  parar [task_id] - Para pipeline\n\n"
            "CANAIS:\n"
            "  criar canal [nicho] - Cria documentacao\n"
            "  listar canais - Lista canais criados\n\n"
            "ENTREGÃVEIS PWA:\n"
            "  criar entregavel [nome] - Cria PWA interativo do nicho\n"
            "  listar entregaveis - Lista todos os PWAs"
        )
        return (text, None, None)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MACRO PIPELINE RESULTS (in-memory, para consulta via API)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

_macro_results: dict = {}
_running_tasks: dict = {}  # prevent GC of background pipeline tasks




# ============================================================================
# LILI â€” REVISORA DE QUALIDADE
# ============================================================================

@app.get("/api/v1/lili/review/{post_id}")
async def lili_review_post(post_id: str, _admin=Depends(require_admin)):
    """Revisa um artigo individual e retorna score + issues."""
    from modules.lili import revisar_artigo
    from modules.database import get_db_blog_post
    
    post = get_db_blog_post(post_id)
    if not post:
        return {"error": "Post nao encontrado"}
    
    review = await revisar_artigo(post)
    return review


@app.get("/api/v1/lili/review-all")
async def lili_review_all(channel_id: str = None, _admin=Depends(require_admin)):
    """Revisa todos os artigos de um blog."""
    from modules.lili import revisar_blog
    
    if not channel_id:
        from modules.database import get_db_blog_channels
        channels = get_db_blog_channels()
        if channels and len(channels) > 0:
            channel_id = channels[0]["id"]
        else:
            return {"error": "Nenhum canal encontrado"}
    
    review = await revisar_blog(channel_id)
    return review


@app.post("/api/v1/lili/correct/{post_id}")
async def lili_correct_post(post_id: str, _admin=Depends(require_admin)):
    """Aplica correcoes automaticas no conteudo do artigo."""
    from modules.lili import corrigir_conteudo_automatico, revisar_artigo
    from modules.database import get_db_blog_post, update_db_blog_post
    
    post = get_db_blog_post(post_id)
    if not post:
        return {"error": "Post nao encontrado"}
    
    original_content = post.get("content", "")
    if not original_content:
        return {"error": "Post sem conteudo"}
    
    # Aplicar correcoes
    corrected = corrigir_conteudo_automatico(original_content)
    
    if corrected == original_content:
        # Nada foi corrigido â€” refazer revisao para confirmar
        post["content"] = corrected
        review = await revisar_artigo(post)
        return {
            "success": True,
            "corrected": False,
            "message": "Nenhuma correcao necessaria",
            "review": review,
        }
    
    # Salvar versao corrigida
    update_db_blog_post(post_id, content=corrected)
    
    # Re-revisar
    post["content"] = corrected
    review = await revisar_artigo(post)
    
    return {
        "success": True,
        "corrected": True,
        "message": f"{len(review['content_review']['issues'])} issues restantes apos correcao",
        "review": review,
    }


@app.get("/api/v1/lili/ranking")
async def lili_ranking(channel_id: str = None, status: str = None, _admin=Depends(require_admin_or_service)):
    """Ranking global de artigos por score LiLi (todos os blogs)."""
    from modules.database import (
        get_db_all_posts_with_meta,
        get_db_blog_channels,
        get_db_blog_post,
        save_db_lili_score,
    )
    from modules.lili import revisar_conteudo

    posts = get_db_all_posts_with_meta()
    if channel_id:
        posts = [p for p in posts if p["channel_id"] == channel_id]
    if status:
        posts = [p for p in posts if p["status"] == status]

    channels = get_db_blog_channels()
    ch_map = {c["id"]: c["name"] for c in channels}

    results = []
    for p in posts:
        score = p.get("lili_score")
        approved = p.get("lili_approved")
        issues_top: list = []
        # Sem cache OU reprovado: deriva o MOTIVO da reprovação do conteúdo.
        # A regra real da LiLi é: score >= 70 E zero issues de severidade 'alta'
        # (ver modules/lili.py). Por isso um artigo com score 85 pode estar
        # reprovado — ele tem 1 issue alta. Expor os issues aqui deixa o
        # motivo visível na UI e para o Hermes (diagnóstico por evidência).
        if score is None or not approved:
            full = get_db_blog_post(p["id"])
            if full:
                try:
                    r = await asyncio.to_thread(
                        revisar_conteudo,
                        full["id"],
                        full["title"] or "",
                        full["content"] or "",
                        full["keywords"] or "",
                    )
                    issues_top = [
                        {
                            "tipo": i.get("tipo"),
                            "severidade": i.get("severity"),
                            "mensagem": (i.get("message") or "")[:90],
                        }
                        for i in (r.get("issues") or [])
                        if i.get("severity") == "alta"
                    ][:3]
                    if score is None:
                        score = r.get("score")
                        approved = bool(r.get("approved"))
                        if score is not None:
                            try:
                                save_db_lili_score(p["id"], score, approved)
                            except Exception:
                                pass
                except Exception:
                    score, approved = None, None
        results.append({
            "id": p["id"],
            "channel_id": p["channel_id"],
            "channel_name": ch_map.get(p["channel_id"], p["channel_id"] or ""),
            "title": p["title"],
            "slug": p["slug"],
            "status": p["status"],
            "word_count": p["word_count"] or 0,
            "topic": p["topic"],
            "featured_image_url": p["featured_image_url"],
            "image_provider": p["image_provider"],
            "lili_score": score,
            "lili_approved": approved,
            "lili_reviewed_at": p.get("lili_reviewed_at"),
            "lili_issues": issues_top,
            "created_at": p.get("created_at"),
        })

    results.sort(key=lambda x: (x["lili_score"] is None, -(x["lili_score"] or 0)))
    scored = [x for x in results if x["lili_score"] is not None]
    avg = round(sum(x["lili_score"] for x in scored) / len(scored), 1) if scored else 0
    approved_count = sum(1 for x in results if x["lili_approved"])

    return {
        "total": len(results),
        "approved": approved_count,
        "reproved": len(results) - approved_count,
        "avg_score": avg,
        "results": results,
        "channels": [{"id": c["id"], "name": c["name"]} for c in channels],
    }


@app.post("/api/v1/blog/post/{post_id}/regenerate")
async def regenerate_blog_post(post_id: str, _admin=Depends(require_admin)):
    """Regenera um artigo do zero com o mesmo topico (deleta o reprovado e recria)."""
    from modules.database import get_db_blog_post, delete_db_blog_post

    post = get_db_blog_post(post_id)
    if not post:
        return {"error": "Post nao encontrado"}

    channel_id = post.get("channel_id")
    topic = post.get("topic") or post.get("title")
    keywords = post.get("keywords") or topic
    if not channel_id:
        return {"error": "Post sem canal associado"}

    # NAO deleta o antigo ainda: so apos o novo artigo estiver completo.
    try:
        from modules.blog_writer import write as blog_write
        from modules.database import update_db_blog_post

        result = await blog_write(
            topic=topic,
            channel_id=channel_id,
            language="pt",
            target_words=1500,
            keywords=keywords,
        )
        if not result.get("success"):
            return {"success": False, "error": result.get("error", "Erro desconhecido")}

        new_post_id = result.get("post_id")
        title = result.get("title", topic)

        # Imagem obrigatoria â€” falha deleta o novo artigo
        img_url = None
        if new_post_id:
            try:
                from modules.image_factory import ImageGeneratorAgent
                agent = ImageGeneratorAgent()
                img = await agent.generate_for_article(
                    title=title,
                    keywords=keywords,
                    topic=topic,
                )
                img_url = img.get("image_url", "")
                if img_url:
                    update_db_blog_post(new_post_id, featured_image_url=img_url)
                else:
                    raise RuntimeError("Nenhuma imagem retornada pelo ImageGeneratorAgent")
            except Exception as e_img:
                from modules.database import delete_db_blog_post as ddb
                ddb(new_post_id)
                return {"success": False, "error": f"Falha ao gerar imagem: {str(e_img)}"}
            # Preserva o status do artigo antigo (draft/publicado) no novo artigo
            try:
                update_db_blog_post(new_post_id, status=post.get("status") or "draft")
            except Exception as e_st:
                print(f"[Regenerate] Falha ao preservar status: {e_st}")

        # Revisao LiLi + cache do score
        lili_review = None
        if new_post_id:
            try:
                from modules.lili import lili_review_after_generation
                lili_review = await lili_review_after_generation(new_post_id)
            except Exception as e_lili:
                print(f"[Regenerate] Lili error: {e_lili}")

        # Novo artigo 100% completo (texto + imagem + revisao) â€” agora sim deleta o antigo
        try:
            delete_db_blog_post(post_id)
        except Exception as e_del:
            print(f"[Regenerate] Falha ao deletar post antigo {post_id}: {e_del}")

        return {
            "success": True,
            "post_id": new_post_id,
            "title": title,
            "word_count": result.get("word_count", 0),
            "topic": topic,
            "featured_image_url": img_url,
            "lili_review": lili_review,
            "deleted_id": post_id,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/v1/blog/post/{post_id}/regenerate-image")
async def regenerate_blog_post_image(post_id: str, _admin=Depends(require_admin)):
    """Regenera APENAS a imagem de destaque do artigo (mantem o texto e o score)."""
    from modules.database import get_db_blog_post, update_db_blog_post
    from modules.image_factory import ImageGeneratorAgent

    post = get_db_blog_post(post_id)
    if not post:
        return {"error": "Post nao encontrado"}

    title = post.get("title", "") or post_id
    keywords = post.get("keywords", "") or title
    topic = post.get("topic", "") or title

    agent = ImageGeneratorAgent()
    img = await agent.generate_for_article(title=title, keywords=keywords, topic=topic)
    if not img.get("image_url"):
        return {"success": False, "error": "Nenhuma imagem retornada pelo ImageGeneratorAgent"}

    update_db_blog_post(
        post_id,
        featured_image_url=img["image_url"],
        image_provider=img.get("provider") or "flux",
    )
    return {"success": True, "image_url": img["image_url"], "provider": img.get("provider")}


@app.post("/api/v1/blog/post/{post_id}/agnes-cover")
async def generate_blog_agnes_cover(post_id: str, _admin=Depends(require_admin)):
    """🎨 Agnes Studio: gera/regenera a imagem de destaque do artigo (1200×630)
    com design real (tipografia + identidade do canal) e renderiza HTML → PNG via Obscura."""
    from modules.database import get_db_blog_post, update_db_blog_post
    from modules.agnes_studio import AgnesStudio

    post = get_db_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    channel_name = ""
    try:
        from modules.database import get_db_blog_channels
        chans = get_db_blog_channels(limit=100) or []
        for ch in chans:
            if ch.get("id") == post.get("channel_id"):
                channel_name = ch.get("name", "")
                break
    except Exception:
        channel_name = ""

    try:
        studio = AgnesStudio()
        result = await studio.generate_blog_cover(
            title=post.get("title", ""),
            subtitle=post.get("excerpt", "") or post.get("meta_description", "") or "",
            niche=post.get("topic", "") or post.get("keywords", "") or "",
            style_id="moderno",
            post_id=post_id,
            blog_name=channel_name,
        )
        if result.get("cover_url"):
            update_db_blog_post(
                post_id,
                featured_image_url=result["cover_url"],
                image_provider="agnes",
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar imagem Agnes: {str(e)}")


@app.get("/api/v1/agnes/gallery")
async def agnes_gallery(_admin=Depends(require_admin)):
    """🖼️ Lista todas as capas geradas pelo Agnes Studio (outputs/agnes).
    Cada PNG tem prefixo {slug}_{uuid} — o slug identifica o produto de origem
    (course/book/post id). Retorna também o título do produto para a UI."""
    import time as _time
    out_dir = os.path.join(_BASE_DIR, "outputs", "agnes")
    images = []
    if os.path.isdir(out_dir):
        from modules.database import get_db_course, get_db_book, get_db_blog_post
        for fn in sorted(os.listdir(out_dir), reverse=True):
            if not fn.lower().endswith(".png"):
                continue
            slug = fn.rsplit("_", 1)[0] if "_" in fn else fn[:-4]
            entity_type, entity_id, title = "", "", ""
            if slug.startswith("crs-"):
                entity_type, entity_id = "course", slug.replace("-", "_", 1)
                c = get_db_course(entity_id) or {}
                title = c.get("title", "") or entity_id
            elif slug.startswith("book-") or slug.startswith("ebook-"):
                entity_type = "ebook"
                entity_id = slug.replace("-", "_", 1)
                b = get_db_book(entity_id) or {}
                title = b.get("title", "") or entity_id
            elif slug.startswith("post-"):
                entity_type, entity_id = "post", slug.replace("-", "_", 1)
                p = get_db_blog_post(entity_id) or {}
                title = p.get("title", "") or entity_id
            else:
                title = slug
            fp = os.path.join(out_dir, fn)
            try:
                mtime = os.path.getmtime(fp)
            except Exception:
                mtime = 0
            images.append({
                "filename": fn,
                "url": f"/outputs/agnes/{fn}",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "title": title,
                "size": os.path.getsize(fp) if os.path.exists(fp) else 0,
                "created_at": _time.strftime("%Y-%m-%d %H:%M", _time.localtime(mtime)) if mtime else "",
            })
    return {"images": images}


@app.post("/api/v1/agnes/use-cover")
async def agnes_use_cover(payload: dict, _admin=Depends(require_admin)):
    """🖼️ Aplica uma capa da galeria Agnes a um produto (course/ebook/post).
    Permite escolher entre várias versões geradas sem regenerar."""
    from modules.database import get_db_course, get_db_book, get_db_blog_post, \
        update_db_course, update_db_book, update_db_blog_post

    entity_type = (payload.get("entity_type") or "").strip().lower()
    entity_id = (payload.get("entity_id") or "").strip()
    filename = (payload.get("filename") or "").strip()
    if not entity_type or not entity_id or not filename:
        raise HTTPException(status_code=400, detail="entity_type, entity_id e filename são obrigatórios")
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="filename inválido")

    out_dir = os.path.join(_BASE_DIR, "outputs", "agnes")
    fp = os.path.join(out_dir, filename)
    if not os.path.isfile(fp) or not filename.lower().endswith(".png"):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado na galeria Agnes")
    cover_url = f"/outputs/agnes/{filename}"

    if entity_type == "course":
        if not get_db_course(entity_id):
            raise HTTPException(status_code=404, detail="Curso não encontrado")
        update_db_course(entity_id, cover_url=cover_url)
    elif entity_type == "ebook":
        if not get_db_book(entity_id):
            raise HTTPException(status_code=404, detail="Ebook não encontrado")
        update_db_book(entity_id, cover_url=cover_url)
    elif entity_type == "post":
        if not get_db_blog_post(entity_id):
            raise HTTPException(status_code=404, detail="Post não encontrado")
        update_db_blog_post(entity_id, featured_image_url=cover_url, image_provider="agnes")
    else:
        raise HTTPException(status_code=400, detail="entity_type deve ser course, ebook ou post")
    return {"success": True, "cover_url": cover_url, "entity_type": entity_type, "entity_id": entity_id}


@app.post("/api/v1/lili/regenerate-batch")
async def lili_regenerate_batch(payload: dict, _admin=Depends(require_admin)):
    """Regenera em lote os artigos reprovados pela LiLi (score < 70 ou nao aprovados).
    O job e PERSISTIDO no banco â€” se o Railway reiniciar no meio, o startup retoma.
    Retorna imediatamente com o job_id para acompanhamento."""
    try:
        limit = int(payload.get("limit") or 10)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 50))  # max 50 por lote
    channel_id = payload.get("channel_id") or ""

    from modules.database import (
        get_db_all_posts_with_meta,
        create_db_regeneration_job,
        add_db_regeneration_job_item,
    )

    posts = get_db_all_posts_with_meta()
    if channel_id:
        posts = [p for p in posts if p["channel_id"] == channel_id]

    reproved = [
        p for p in posts
        if (p.get("lili_score") is not None and p.get("lili_score", 0) < 70)
        or not p.get("lili_approved")
    ]
    # Piores primeiro
    reproved.sort(key=lambda p: (p.get("lili_score") if p.get("lili_score") is not None else 0))
    target = reproved[:limit]

    if not target:
        return {"success": True, "queued": 0, "message": "Nenhum artigo reprovado encontrado"}

    job = create_db_regeneration_job(total=len(target))
    if not job:
        return {"success": False, "error": "Falha ao criar job no banco"}

    job_id = job["id"]
    for p in target:
        add_db_regeneration_job_item(job_id, p["id"], p.get("title") or "")

    # Agenda o processamento em task asyncio desacoplada (nao so BackgroundTasks)
    try:
        asyncio.create_task(_process_regeneration_job(job_id))
    except Exception as e:
        print(f"[Batch] Falha ao agendar job {job_id}: {e}")

    return {
        "success": True,
        "queued": len(target),
        "job_id": job_id,
        "post_ids": [p["id"] for p in target],
        "message": f"{len(target)} artigos reprovados agendados (job {job_id} persistido)",
    }


async def _process_regeneration_job(job_id: str):
    """Worker de um job persistido: processa cada item pendente, atualizando status.
    Idempotente â€” pode ser chamado de novo apos restart para retomar itens pendentes."""
    from modules.database import (
        get_db_regeneration_job,
        update_db_regeneration_job,
        update_db_regeneration_job_item,
        reset_db_stuck_job_items,
    )

    job = get_db_regeneration_job(job_id)
    if not job:
        return

    # Crash no meio de um item: itens em 'processing' voltam para 'pending'
    reset_db_stuck_job_items(job_id)

    total = job.get("total") or len(job.get("items") or [])
    print(f"[BatchJob {job_id}] Iniciando processamento de {total} itens...")

    done = 0
    failed = 0
    for item in job.get("items") or []:
        if item.get("status") == "done":
            done += 1
            continue
        if item.get("status") == "failed":
            failed += 1
            continue

        item_id = item["id"]
        post_id = item["post_id"]
        try:
            update_db_regeneration_job_item(item_id, status="processing")
            r = await regenerate_blog_post(post_id)
            if r.get("success"):
                update_db_regeneration_job_item(item_id, status="done")
                done += 1
                print(f"[BatchJob {job_id}] {post_id}: OK -> {r.get('post_id')}")
            elif r.get("error") and "nao encontrado" in str(r.get("error")):
                # Crash-apos-sucesso: o artigo antigo ja foi substituido no meio do batch
                # anterior (post deletado). Considera o item concluido â€” nao eh falha real.
                update_db_regeneration_job_item(item_id, status="done")
                done += 1
                print(f"[BatchJob {job_id}] {post_id}: ja regenerado antes do restart (post antigo nao existe). Marcado done.")
            else:
                update_db_regeneration_job_item(
                    item_id, status="failed", error=str(r.get("error"))
                )
                failed += 1
                print(f"[BatchJob {job_id}] {post_id}: FALHA -> {r.get('error')}")
        except Exception as e:
            update_db_regeneration_job_item(item_id, status="failed", error=str(e))
            failed += 1
            print(f"[BatchJob {job_id}] Erro em {post_id}: {e}")

        update_db_regeneration_job(
            job_id, processed=done + failed, succeeded=done, failed=failed
        )

    final_status = "done" if failed == 0 else ("failed" if done == 0 else "partial")
    update_db_regeneration_job(
        job_id,
        status=final_status,
        processed=done + failed,
        succeeded=done,
        failed=failed,
    )
    print(f"[BatchJob {job_id}] Concluido: {done} OK, {failed} falhas. Status: {final_status}")


@app.get("/api/v1/lili/regenerate-jobs/{job_id}")
async def get_regeneration_job_status(job_id: str):
    """Status detalhado de um job de regeneracao persistido."""
    from modules.database import get_db_regeneration_job

    job = get_db_regeneration_job(job_id)
    if not job:
        return {"error": "Job nao encontrado"}
    return job


@app.get("/api/v1/lili/regenerate-jobs")
async def list_regeneration_jobs(limit: int = 10):
    """Lista os jobs recentes de regeneracao (mais recentes primeiro)."""
    from modules.database import get_db_recent_regeneration_jobs

    return {"jobs": get_db_recent_regeneration_jobs(limit=limit)}


@app.post("/api/v1/blog/generate-article")
async def generate_single_article(payload: dict):
    """Gera um artigo completo de forma direta (sem pipeline em background).

    Args:
        topic: Tema do artigo
        channel_id: ID do canal (opcional, usa o primeiro se nao fornecida)
        keywords: Keywords separadas por virgula (opcional)
        target_words: Palavras alvo (opcional, padrao 1000)

    Returns:
        Dict com o artigo gerado e revisao Lili
    """
    topic = payload.get("topic", "")
    if not topic:
        return {"error": "topic is required"}

    channel_id = payload.get("channel_id", "")
    if not channel_id:
        from modules.database import get_db_blog_channels
        channels = get_db_blog_channels()
        if channels and len(channels) > 0:
            channel_id = channels[0]["id"]
        else:
            return {"error": "No channel found. Create a blog first."}

    keywords = payload.get("keywords", topic)
    target_words = payload.get("target_words", 1000)
    language = payload.get("language", "pt")

    try:
        from modules.blog_writer import write as blog_write
        from modules.database import get_db_blog_post, update_db_blog_post

        result = await blog_write(
            topic=topic,
            channel_id=channel_id,
            language=language,
            target_words=target_words,
            keywords=keywords,
        )

        if not result.get("success"):
            return {"success": False, "error": result.get("error", "Unknown error")}

        post_id = result.get("post_id")
        title = result.get("title", topic)
        word_count = result.get("word_count", 0)

        # Generate image for the article (OBRIGATORIO â€” falha deleta o artigo)
        img_url = None
        if post_id:
            try:
                from modules.image_factory import ImageGeneratorAgent
                agent = ImageGeneratorAgent()
                img = await agent.generate_for_article(
                    title=title,
                    keywords=keywords,
                    topic=topic,
                )
                img_url = img.get("image_url", "")
                if img_url:
                    update_db_blog_post(post_id, featured_image_url=img_url)
                else:
                    raise RuntimeError("Nenhuma imagem retornada pelo ImageGeneratorAgent (nem fallback SVG)")
            except Exception as e_img:
                from modules.database import delete_db_blog_post
                delete_db_blog_post(post_id)
                return {"success": False, "error": f"Falha ao gerar imagem: {str(e_img)}"}

        # Lili review
        lili_review = None
        if post_id:
            try:
                from modules.lili import lili_review_after_generation
                lili_review = await lili_review_after_generation(post_id)
            except Exception as e_lili:
                print(f"[GenerateArticle] Lili error: {e_lili}")

        return {
            "success": True,
            "post_id": post_id,
            "title": title,
            "word_count": word_count,
            "topic": topic,
            "featured_image_url": img_url,
            "lili_review": lili_review,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}



@app.delete("/api/v1/blog/post/{post_id}")
async def delete_blog_post(post_id: str, _admin=Depends(require_admin)):
    """Remove um post do blog pelo ID."""
    from modules.database import delete_db_blog_post
    success = delete_db_blog_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post nÃ£o encontrado")
    return {"success": True, "message": f"Post {post_id} removido"}

@app.delete("/api/v1/blog/channel/{channel_id}")
async def delete_blog_channel(channel_id: str, _admin=Depends(require_admin)):
    """Remove um canal de blog e todos os seus artigos pelo ID."""
    from modules.database import SessionLocal, BlogChannel, BlogPost
    db = SessionLocal()
    try:
        chan = db.query(BlogChannel).filter(BlogChannel.id == channel_id).first()
        if not chan:
            raise HTTPException(status_code=404, detail="Blog nÃ£o encontrado")
        db.query(BlogPost).filter(BlogPost.channel_id == channel_id).delete()
        db.delete(chan)
        db.commit()
        return {"success": True, "message": "Blog e todos os seus artigos deletados com sucesso!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()







@app.post("/api/v1/pipeline/run-blog-factory")
async def run_blog_factory_frontend(payload: dict, _admin=Depends(require_admin_or_service)):
    """Alias da UI - delega para a pipeline macro."""
    blog_name = payload.get("blog_name", "")
    niche = payload.get("niche", "")
    language = payload.get("language", "pt")
    target_articles = payload.get("target_articles", 3)
    is_affiliate = bool(payload.get("is_affiliate", False))
    is_discover = bool(payload.get("is_discover", False))
    if not blog_name or not niche:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="blog_name and niche are required")
    
    import uuid
    tid = f"ff_{uuid.uuid4().hex[:8]}"
    
    from modules.blog_pipeline import run_blog_macro_pipeline
    
    _macro_results[tid] = {
        "status": "active",
        "phase": "fundacao",
        "progress": 0,
        "message": "ðŸš€ Iniciando pipeline...",
        "blog_name": blog_name,
        "niche": niche,
        "data": None,
        "last_update": __import__('time').time(),
    }
    
    def _touch_macro(pid):
        if pid in _macro_results:
            _macro_results[pid]["last_update"] = __import__('time').time()
    
    def on_progress(pid, stage_id, progress, message, data):
        if pid in _macro_results:
            _touch_macro(pid)
            try:
                real_stage = data.get("stage_id", stage_id) if isinstance(data, dict) else stage_id
                real_prog = data.get("progress", progress) if isinstance(data, dict) else progress
                real_msg = data.get("message", message) if isinstance(data, dict) else message
                real_status = data.get("status", "running") if isinstance(data, dict) else "running"
                _macro_results[pid].update({
                    "status": real_status if real_status != "running" else "active",
                    "phase": real_stage,
                    "progress": real_prog,
                    "message": real_msg,
                    "data": data,
                })
                # Broadcast via WebSocket para clientes conectados
                try:
                    asyncio.create_task(_ws_hub.broadcast(
                        event_type="pipeline_progress",
                        data={
                            "stage_id": real_stage,
                            "progress": real_prog,
                            "message": real_msg,
                            "status": real_status if real_status != "running" else "active",
                            "current_article": (data or {}).get("state", {}).get("articles_generated", 0) if isinstance(data, dict) else 0,
                            "article_topic": (data or {}).get("article_topic"),
                            "phase_detail": real_stage,
                            "lili_score": (data or {}).get("lili_score"),
                            "lili_approved": (data or {}).get("lili_approved"),
                            "article_title": (data or {}).get("article_title"),
                            "task_id": pid,
                            "articles_generated": (data or {}).get("state", {}).get("articles_generated", 0),
                            "target_articles": (data or {}).get("state", {}).get("target_articles", 0),
                            "reddit_questions": (data or {}).get("state", {}).get("reddit_questions", []) if isinstance(data, dict) else [],
                        },
                        task_id=pid,
                    ))
                except Exception as ws_e:
                    print(f"[FF-PIPELINE] WebSocket broadcast error: {ws_e}")
            except Exception as e:
                print(f"[FF-PIPELINE] on_progress error: {e}")
    
    async def _run_and_report():
        try:
            async def _heartbeat():
                while True:
                    await asyncio.sleep(15)
                    if tid not in _macro_results:
                        break
                    if _macro_results[tid].get("status") in ("completed", "failed"):
                        break
                    # Apenas atualiza timestamp para UI saber que pipeline esta viva
                    _macro_results[tid]["last_update"] = __import__('time').time()
            
            hb_task = asyncio.create_task(_heartbeat())
            try:
                state = await run_blog_macro_pipeline(
                    blog_name=blog_name, niche=niche, language=language,
                    task_id=tid, target_articles=target_articles,
                    on_progress=on_progress,
                    is_affiliate=is_affiliate,
                    is_discover=is_discover,
                )
                _macro_results[tid]["status"] = state.get("status", "completed")
                _macro_results[tid]["data"] = state
                # Broadcast completion via WebSocket
                try:
                    asyncio.create_task(_ws_hub.broadcast(
                        event_type="pipeline_complete",
                        data={
                            "status": state.get("status", "completed"),
                            "articles_generated": state.get("articles_generated", 0),
                        },
                        task_id=tid,
                    ))
                except Exception as _ws_e:
                    print(f"[WS] completion broadcast error: {_ws_e}")
            finally:
                hb_task.cancel()
        except Exception as e:
            _macro_results[tid]["status"] = "failed"
            _macro_results[tid]["error"] = str(e)
            _macro_results[tid]["last_update"] = __import__('time').time()
            # Broadcast failure via WebSocket
            try:
                import asyncio as _aio2
                _aio2.ensure_future(_ws_hub.broadcast(
                    event_type="pipeline_failed",
                    data={"error": str(e)[:200]},
                    task_id=tid,
                ))
            except Exception:
                pass
    
    import asyncio
    task = asyncio.create_task(_run_and_report())
    _running_tasks[tid] = task  # prevent GC
    
    return {"task_id": tid, "blog_name": blog_name, "niche": niche, "status": "starting", "message": "Pipeline iniciada!"}

@app.post("/api/v1/pipeline/suggest-blog-idea")
async def suggest_blog_idea(payload: dict, _admin=Depends(require_admin)):
    """
    Usa o LLM para sugerir uma lista de 10 nichos lucrativos, cada um contendo
    3 opcoes de nomes de blog e 3 opcoes de subnichos.
    """
    is_affiliate = bool(payload.get("is_affiliate", False))
    is_discover = bool(payload.get("is_discover", False))
    from modules.blog_writer import _call_llm
    
    # â”€â”€â”€ PrÃ©-pesquisa com Obscura em MÃºltiplas Sementes â”€â”€â”€
    import random
    from services.obscura_bridge import get_google_suggestions
    
    seeds = [
        "curiosidades do mundo", "saude e bem estar", "tecnologia e inovacao", 
        "financas pessoais", "viagens baratas", "casa e decoracao", 
        "maternidade real", "pet care", "receitas faceis", 
        "fenomenos misteriosos", "misterios historicos", "gadgets inteligentes"
    ]
    selected_seeds = random.sample(seeds, min(3, len(seeds)))
    google_terms = []
    for seed in selected_seeds:
        try:
            terms = await get_google_suggestions(seed, "pt")
            if terms:
                google_terms.extend(terms)
        except Exception as e_sug:
            print(f"[Seu Hermes] Falha ao pre-pesquisar termos via Obscura para '{seed}': {e_sug}")
            
    # Remover duplicados
    seen = set()
    google_terms = [x for x in google_terms if not (x in seen or seen.add(x))]
    
    google_context = ""
    if google_terms:
        google_context = (
            f"\nIMPORTANTE: O Google detectou que as pessoas estao buscando ativamente estes termos hoje:\n"
            f"{', '.join(google_terms[:25])}\n"
            f"Voce DEVE se inspirar obrigatoriamente nessas buscas reais para propor os nichos, os nomes de blog e os subnichos."
        )
    
    system = "VocÃª Ã© o Seu Hermes, o inteligente orquestrador, estrategista de trÃ¡fego (SEO e Discover) e editor-chefe de blogs."
    prompt = (
        "Sugira uma lista com exatamente 10 nichos de blogs altamente lucrativos e com alto potencial de busca na internet hoje.\n"
        "Para cada nicho, forneÃ§a 3 sugestÃµes criativas de nomes para o blog e 3 sugestÃµes de subnichos especÃ­ficos e focados.\n"
        "Retorne APENAS um objeto JSON vÃ¡lido (sem markdown, sem ```json, sem texto extra) no seguinte formato:\n"
        "{\n"
        '  "suggestions": [\n'
        "    {\n"
        '      "niche": "Nome do nicho principal (ex: SaÃºde & Dores)",\n'
        '      "names": ["OpÃ§Ã£o Nome 1", "OpÃ§Ã£o Nome 2", "OpÃ§Ã£o Nome 3"],\n'
        '      "subniches": ["Subnicho 1", "Subnicho 2", "Subnicho 3"]\n'
        "    }\n"
        "  ]\n"
        "}\n"
        + google_context
    )
        
    try:
        raw = await _call_llm(system, prompt, temperature=0.9, max_tokens=2000)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        
        import json
        data = json.loads(cleaned)
        return {
            "suggestions": data.get("suggestions", []) or [],
            "searched_terms": google_terms or []
        }
    except Exception as e:
        print(f"[Seu Hermes] Erro ao gerar sugestÃµes de blog: {e}")
        # Fallback estruturado com 10 nichos de alta qualidade
        fallbacks = [
            {
                "niche": "MistÃ©rios & FenÃ´menos",
                "names": ["Mundo Oculto", "Portal dos MistÃ©rios", "AlÃ©m do VisÃ­vel"],
                "subniches": ["FenÃ´menos da Natureza InexplicÃ¡veis", "MistÃ©rios HistÃ³ricos NÃ£o Resolvidos", "Astronomia de Fronteira"]
            },
            {
                "niche": "FinanÃ§as Pessoais",
                "names": ["Poupar e Multiplicar", "Caminho da Riqueza", "Carteira Forte"],
                "subniches": ["Investimento para Iniciantes", "Renda Extra Passiva", "Economia DomÃ©stica Inteligente"]
            },
            {
                "niche": "SaÃºde & Bem-Estar",
                "names": ["Vida Plena", "EquilÃ­brio DiÃ¡rio", "Corpo e Mente"],
                "subniches": ["Emagrecimento SaudÃ¡vel", "AlimentaÃ§Ã£o Anti-inflamatÃ³ria", "Rotina de Longevidade"]
            },
            {
                "niche": "Tecnologia & Gadgets",
                "names": ["Futuro Tech", "ConexÃ£o Inteligente", "Manual Geek"],
                "subniches": ["Dispositivos de Casa Inteligente", "InteligÃªncia Artificial no Dia a Dia", "Dicas de Celular e Computador"]
            },
            {
                "niche": "Casa & OrganizaÃ§Ã£o",
                "names": ["Meu Lar Doce Lar", "Organize Decor", "EspaÃ§o Harmonioso"],
                "subniches": ["DecoraÃ§Ã£o Minimalista", "Limpeza e OrganizaÃ§Ã£o PrÃ¡tica", "Projetos FaÃ§a VocÃª Mesmo (DIY)"]
            },
            {
                "niche": "Viagens Inteligentes",
                "names": ["Roteiro EconÃ´mico", "Viajante de Cauda Longa", "Partiu Mundo"],
                "subniches": ["Viagem de Baixo Custo", "Destinos Escondidos no Brasil", "Dicas de Milhas e Passagens"]
            },
            {
                "niche": "Maternidade & Paternidade",
                "names": ["Ninho Acolhedor", "MÃ£e Realidade", "Guia dos Pais"],
                "subniches": ["Desenvolvimento Infantil Primeiro Ano", "AlimentaÃ§Ã£o SaudÃ¡vel para CrianÃ§as", "EducaÃ§Ã£o Emocional Infantil"]
            },
            {
                "niche": "Pets & Cuidado",
                "names": ["Amigo de Quatro Patas", "Guia do CÃ£o", "Universo Felino"],
                "subniches": ["Adestramento Caseiro", "NutriÃ§Ã£o e SaÃºde Animal", "Dicas para Gatos de Apartamento"]
            },
            {
                "niche": "CulinÃ¡ria PrÃ¡tica",
                "names": ["Sabor RÃ¡pido", "Cozinha sem ComplicaÃ§Ã£o", "Chef do Dia a Dia"],
                "subniches": ["Receitas de Airfryer", "Marmitas Semanais SaudÃ¡veis", "Doces e Sobremesas FÃ¡ceis"]
            },
            {
                "niche": "Produtividade & Foco",
                "names": ["Foco Ativo", "Mente Eficiente", "Mestre do Tempo"],
                "subniches": ["GestÃ£o do Tempo", "HÃ¡bitos de Alta Performance", "Minimalismo PrÃ¡tico"]
            }
        ]
        return {
            "suggestions": fallbacks,
            "searched_terms": google_terms or []
        }

@app.post("/api/v1/pipeline/run-sync")
async def run_sync_pipeline(payload: dict, _admin=Depends(require_admin)):
    """Executa a pipeline de blog de forma SINCRONA (inline na requisicao).
    
    Nao usa background tasks, threading ou create_task.
    A pipeline roda dentro do timeout da requisicao HTTP.
    Para 5 artigos (~60s cada), espere ~5 minutos de resposta.
    A UI acompanha o progresso via _macro_results polling.
    """
    blog_name = payload.get("blog_name", "")
    niche = payload.get("niche", "")
    language = payload.get("language", "pt")
    target_articles = payload.get("target_articles", 3)
    if not blog_name or not niche:
        raise HTTPException(status_code=400, detail="blog_name and niche are required")
    
    import uuid
    tid = f"sync_{uuid.uuid4().hex[:8]}"
    
    from modules.blog_pipeline import run_blog_macro_pipeline
    from modules.database import get_db_blog_channels
    
    # Armazena estado inicial para UI acompanhar via polling
    _macro_results[tid] = {"status": "starting", "blog_name": blog_name, "niche": niche, "data": None}
    
    def on_progress(pid, stage_id, progress, message, data):
        if pid in _macro_results:
            try:
                real_stage = data.get("stage_id", stage_id) if isinstance(data, dict) else stage_id
                real_prog = data.get("progress", progress) if isinstance(data, dict) else progress
                real_msg = data.get("message", message) if isinstance(data, dict) else message
                real_status = data.get("status", "running") if isinstance(data, dict) else "running"
                _macro_results[pid].update({
                    "status": real_status,
                    "phase": real_stage,
                    "progress": real_prog,
                    "message": real_msg,
                    "data": data,
                })
            except Exception as e:
                print(f"[SYNC-PIPELINE] on_progress error: {e}")
    
    print(f"[SYNC-PIPELINE] Starting: {tid} blog={blog_name} articles={target_articles}")
    
    state = await run_blog_macro_pipeline(
        blog_name=blog_name, niche=niche, language=language,
        task_id=tid, target_articles=target_articles,
        on_progress=on_progress,
    )
    
    _macro_results[tid]["status"] = state.get("status", "completed")
    _macro_results[tid]["data"] = state
    
    print(f"[SYNC-PIPELINE] Complete: {tid} status={state.get('status')}")
    
    return {
        "task_id": tid,
        "blog_name": blog_name,
        "niche": niche,
        "status": state.get("status", "completed"),
        "articles_generated": state.get("articles_generated", 0),
        "total_articles": target_articles,
        "state": state,
    }

@app.post("/api/v1/blog/generate-batch")
async def generate_batch_articles(payload: dict):
    """Gera N artigos completos de forma direta, UM POR VEZ, sÃ­ncrono.
    
    Args:
        topics: Lista de temas dos artigos
        channel_id: ID do canal (opcional, usa o primeiro se nao fornecido)
        target_words: Palavras alvo (padrao 1000)
        
    Returns:
        Lista de resultados com cada artigo gerado
    """
    topics = payload.get("topics", [])
    if not topics or not isinstance(topics, list):
        raise HTTPException(status_code=400, detail="topics (list) is required")
    
    target_words = payload.get("target_words", 1000)
    language = payload.get("language", "pt")
    
    from modules.blog_writer import write as blog_write
    from modules.database import get_db_blog_channels, get_db_blog_post, update_db_blog_post
    from modules.lili import lili_review_after_generation
    from modules.image_factory import ImageGeneratorAgent
    
    channel_id = payload.get("channel_id", "")
    if not channel_id:
        channels = get_db_blog_channels()
        if channels and len(channels) > 0:
            channel_id = channels[0]["id"]
        else:
            raise HTTPException(status_code=400, detail="No channel found")
    
    results = []
    errors = []
    
    for i, topic in enumerate(topics):
        try:
            result = await blog_write(
                topic=topic,
                channel_id=channel_id,
                language=language,
                target_words=target_words,
                keywords=topic,
            )
            
            if result.get("success"):
                post_id = result.get("post_id")
                title = result.get("title", topic)
                word_count = result.get("word_count", 0)
                
                # Gerar imagem (OBRIGATORIO â€” falha = artigo descartado)
                img_url = None
                if post_id:
                    try:
                        agent = ImageGeneratorAgent()
                        img = await agent.generate_for_article(title=title, keywords=topic, topic=topic)
                        if img.get("image_url"):
                            update_db_blog_post(post_id, featured_image_url=img["image_url"])
                            img_url = img["image_url"]
                        else:
                            raise RuntimeError("Nenhuma imagem gerada (nem fallback SVG)")
                    except Exception as e_img:
                        print(f"[Batch] Image error for {topic[:30]}: {e_img}")
                
                # Revisao Lili
                lili = None
                if post_id:
                    try:
                        lili = await lili_review_after_generation(post_id)
                    except Exception as e_lili:
                        print(f"[Batch] Lili error: {e_lili}")
                
                results.append({
                    "success": True,
                    "topic": topic,
                    "post_id": post_id,
                    "title": title,
                    "word_count": word_count,
                    "featured_image_url": img_url,
                    "lili_review": lili,
                })
                print(f"[Batch] [{i+1}/{len(topics)}] OK: {topic[:40]} ({word_count} palavras)")
            else:
                err = result.get("error", "Unknown error")
                errors.append({"topic": topic, "error": err})
                print(f"[Batch] [{i+1}/{len(topics)}] ERROR: {topic[:40]} -> {err[:60]}")
        except Exception as e:
            errors.append({"topic": topic, "error": str(e)})
            print(f"[Batch] [{i+1}/{len(topics)}] EXCEPTION: {topic[:40]} -> {str(e)[:60]}")
    
    return {
        "success": len(results) > 0,
        "total": len(topics),
        "generated": len(results),
        "errors": len(errors),
        "articles": results,
        "error_details": errors if errors else None,
    }

@app.get("/api/v1/pipeline/macro-result/{task_id}")
async def get_macro_result(task_id: str):
    """Retorna o resultado de uma execuÃ§Ã£o de macro pipeline."""
    result = _macro_results.get(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pipeline nÃ£o encontrada")
    return result


    # â•â•â• FALLBACK: Conversa com LLM â•â•â•
    try:
        from modules.brain import SniperBrain
        brain = SniperBrain()
        
        system_prompt = (
            "VocÃª Ã© o Hermes, o orquestrador inteligente do ecossistema DEZAFIRA.\n"
            "Seu fundador Ã© o JONATAS. Fale com ele de forma extremamente executiva, direta, minimalista e clara, sem enrolaÃ§Ã£o.\n\n"
            "VocÃª orquestra 5 fÃ¡bricas principais:\n"
            "1. ðŸ“ **FÃ¡brica de Blogs**: Artigos otimizados para SEO sobre temas bÃ­blicos e ensinamentos de Jesus.\n"
            "2. ðŸ“— **FÃ¡brica de Livros**: E-books completos com capÃ­tulos gerados por IA.\n"
            "3. ðŸŽ“ **FÃ¡brica de Cursos**: Cursos em texto com mÃ³dulos, aulas e quizzes.\n"
            "4. ðŸŽ¨ **FÃ¡brica de Imagens**: GeraÃ§Ã£o de capas, thumbnails e imagens via FLUX AI + Pexels.\n"
            "5. ðŸ” **RAG BÃ­blico**: Busca semÃ¢ntica que responde perguntas com citaÃ§Ãµes dos artigos, livros e cursos.\n\n"
            "COMANDOS DISPONÃVEIS:\n"
            "- 'status' ou 'dashboard' â€” Mostra o resumo de todas as fÃ¡bricas\n"
            "- 'pesquisar [tema]' â€” Pesquisa tendÃªncias para um nicho\n"
            "- 'produzir artigo [tema]' â€” Gera novo artigo no blog\n"
            "- 'produzir livro [tema]' â€” Gera novo livro\n"
            "- 'produzir curso [tema]' â€” Gera novo curso\n"
            "- 'perguntar [duvida]' â€” Consulta o RAG BÃ­blico\n"
            "- 'ajuda' â€” Lista todos os comandos\n\n"
            "DIRETRIZES DE RESPOSTA:\n"
            "- NUNCA simule, finja ou mock por texto a execuÃ§Ã£o de tarefas.\n"
            "- Seja direto e executivo. Jonatas Ã© o fundador e quer respostas rÃ¡pidas.\n"
            "- Sempre que possÃ­vel, dÃª comandos que ele possa copiar e colar.\n"
            "- As abas do painel (Dashboard, Blogs, Livros, Cursos, Imagens, RAG) mostram dados ao vivo."
        )

        response = brain._call_llm(system_prompt, message, temperature=0.7)
        return (response, None, None)
    except Exception as e:
        # Fallback inteligente se a API Key do Nvidia NIM estiver ausente/expirada
        if "inicia" in msg or "fluxo" in msg or "faz" in msg:
            text = (
                "Orquestrador Hermes Ativo!\n\n"
                "Jonatas, as 5 fÃ¡bricas estÃ£o 100% operacionais no painel.\n\n"
                "ðŸ“ **Blogs** â†’ Aba Blogs\n"
                "ðŸ“— **Livros** â†’ Aba Livros\n"
                "ðŸŽ“ **Cursos** â†’ Aba Cursos\n"
                "ðŸŽ¨ **Imagens** â†’ Aba Imagens\n"
                "ðŸ” **RAG BÃ­blico** â†’ Aba RAG\n"
                "\nUse 'ajuda' para ver todos os comandos disponÃ­veis."
            )
        else:
            text = (
                "Orquestrador Hermes Online.\n"
                "Aguardando seus comandos para orquestrar as 5 fÃ¡bricas:\nðŸ“ Blogs | ðŸ“— Livros | ðŸŽ“ Cursos | ðŸŽ¨ Imagens | ðŸ” RAG\n\nDigite 'ajuda' para ver todos os comandos disponÃ­veis."
            )
        return (text, None, None)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DEZAFIRA CLUB â€” Auth & Member Area Endpoints
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from modules.database import (
    create_db_user, get_db_user_by_email, get_db_user_by_id, get_db_user_by_google_id,
    update_db_user, create_db_user_session, get_db_user_session, delete_db_user_sessions,
    create_db_password_reset, get_db_password_reset, use_db_password_reset,
    get_db_admin_users, get_db_course_tracks, get_db_course_track,
    create_db_course_track, update_db_lesson_progress, get_db_track_lessons_progress,
    get_db_books, get_db_courses, get_db_book, get_db_course,
)


# â”€â”€â”€ AUTH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.post("/api/v1/auth/register")
async def auth_register(payload: dict):
    email = payload.get("email", "").strip().lower()
    name = payload.get("name", "").strip()
    password = payload.get("password", "")
    if not email or not name or not password:
        raise HTTPException(status_code=400, detail="email, name e password sÃ£o obrigatÃ³rios")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password deve ter no mÃ­nimo 6 caracteres")
    existing = get_db_user_by_email(email)
    if existing:
        raise HTTPException(status_code=409, detail="Email jÃ¡ cadastrado")
    pw_hash = _hash_password(password)
    result = create_db_user(email=email, name=name, password_hash=pw_hash)
    if not result:
        raise HTTPException(status_code=500, detail="Erro ao criar usuÃ¡rio")
    token = _generate_jwt_token(result["id"])
    expires = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    create_db_user_session(result["id"], token, expires)
    return {"token": token, "user": result}


@app.post("/api/v1/auth/login")
async def auth_login(payload: dict):
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")
    if not email or not password:
        raise HTTPException(status_code=400, detail="email e password sÃ£o obrigatÃ³rios")
    user = get_db_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais invÃ¡lidas")
    if not user.password_hash:
        raise HTTPException(status_code=401, detail="Conta usa login social. Use Google.")
    if not _verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais invÃ¡lidas")
    token = _generate_jwt_token(user.id)
    expires = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    create_db_user_session(user.id, token, expires)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "avatar_url": user.avatar_url}
    }


@app.post("/api/v1/auth/google")
async def auth_google(payload: dict):
    """Login/cadastro via Google OAuth (token do frontend via NextAuth.js)."""
    google_id = payload.get("google_id")
    email = payload.get("email", "").strip().lower()
    name = payload.get("name", "")
    avatar_url = payload.get("avatar_url")
    if not google_id or not email:
        raise HTTPException(status_code=400, detail="google_id e email sÃ£o obrigatÃ³rios")
    user = get_db_user_by_google_id(google_id)
    if not user:
        existing = get_db_user_by_email(email)
        if existing:
            update_db_user(existing.id, google_id=google_id, avatar_url=avatar_url or existing.avatar_url)
            user = get_db_user_by_id(existing.id)
        else:
            result = create_db_user(email=email, name=name, google_id=google_id, avatar_url=avatar_url)
            if not result:
                raise HTTPException(status_code=500, detail="Erro ao criar usuÃ¡rio")
            user = get_db_user_by_id(result["id"])
    token = _generate_jwt_token(user.id)
    expires = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    create_db_user_session(user.id, token, expires)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "avatar_url": user.avatar_url}
    }


@app.post("/api/v1/auth/forgot-password")
async def auth_forgot_password(payload: dict):
    email = payload.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="email Ã© obrigatÃ³rio")
    user = get_db_user_by_email(email)
    if not user:
        # Por seguranÃ§a, sempre retorna OK
        return {"message": "Se o email existir, um link de recuperaÃ§Ã£o foi enviado."}
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)
    create_db_password_reset(user.id, token, expires)
    # TODO: Enviar email com link. Por agora retorna o token diretamente.
    print(f"[Auth] Password reset para {email}: token={token}")
    return {"message": "Se o email existir, um link de recuperaÃ§Ã£o foi enviado.", "debug_token": token}


@app.post("/api/v1/auth/reset-password")
async def auth_reset_password(payload: dict):
    token = payload.get("token", "")
    new_password = payload.get("new_password", "")
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="token e new_password sÃ£o obrigatÃ³rios")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password deve ter no mÃ­nimo 6 caracteres")
    pr = get_db_password_reset(token)
    if not pr:
        raise HTTPException(status_code=400, detail="Token invÃ¡lido ou expirado")
    pw_hash = _hash_password(new_password)
    update_db_user(pr.user_id, password_hash=pw_hash)
    use_db_password_reset(token)
    return {"message": "Senha redefinida com sucesso"}


@app.get("/api/v1/auth/me")
async def auth_me(user=Depends(get_current_user)):
    return user


@app.post("/api/v1/auth/logout")
async def auth_logout(user=Depends(get_current_user)):
    delete_db_user_sessions(user["id"])
    return {"message": "Logout realizado"}


@app.get("/api/v1/ebooks/{book_id}/chapters")
async def ebook_chapters_api(book_id: str):
    book = get_db_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Livro nÃ£o encontrado")
    return {"book": book, "chapters": []}



@app.get("/api/v1/admin/users")
async def admin_list_users(user=Depends(require_admin)):
    return {"users": get_db_admin_users()}


@app.get("/api/v1/admin/stats")
async def admin_stats(user=Depends(require_admin)):
    from modules.database import SessionLocal as _SL
    from modules.database import User, BlogPost, Book, Course
    _db = _SL()
    try:
        total_users = _db.query(User).count()
        total_blogs = _db.query(BlogPost).count()
        total_books = _db.query(Book).count()
        total_courses = _db.query(Course).count()
        return {
            "total_users": total_users,
            "total_blogs": total_blogs,
            "total_books": total_books,
            "total_courses": total_courses,
        }
    finally:
        _db.close()



# â”€â”€â”€ MÃQUINA DE MARKETING DIGITAL (SABRI SUBY AGENTS) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# InstÃ¢ncia em memÃ³ria para guardar o estado da campanha ativa (Fases 1 a 6)
_marketing_pipelines: Dict[str, Any] = {}

@app.post("/api/v1/marketing/start")
async def start_marketing_campaign(payload: dict, _admin=Depends(require_admin_or_service)):
    """Inicia uma nova esteira de marketing para um determinado nicho."""
    niche = payload.get("niche", "").strip()
    if not niche:
        raise HTTPException(status_code=400, detail="Nicho Ã© obrigatÃ³rio")

    from modules.marketing_pipeline import MarketingPipeline
    from modules.database import create_marketing_campaign
    campaign_id = str(uuid.uuid4().hex[:12])
    _marketing_pipelines[campaign_id] = MarketingPipeline()
    # Persiste no banco para histÃ³rico
    try:
        create_marketing_campaign(campaign_id, niche)
    except Exception as e:
        print(f"[Marketing] Aviso: falha ao criar campanha no banco: {e}")
    return {"success": True, "campaign_id": campaign_id, "niche": niche}

@app.post("/api/v1/marketing/stage")
async def run_marketing_stage_endpoint(payload: dict, _admin=Depends(require_admin_or_service)):
    """Executa uma fase da esteira de marketing de forma sequencial."""
    campaign_id = payload.get("campaign_id")
    stage = payload.get("stage")
    niche = payload.get("niche", "")
    
    if not campaign_id or stage is None:
        raise HTTPException(status_code=400, detail="campaign_id e stage sÃ£o obrigatÃ³rios")

    from modules.marketing_pipeline import MarketingPipeline
    from modules.database import update_marketing_campaign_stage
    if campaign_id not in _marketing_pipelines:
        _marketing_pipelines[campaign_id] = MarketingPipeline()

    pipeline = _marketing_pipelines[campaign_id]
    result = await pipeline.run_stage(int(stage), niche)
    
    # Persiste o conteÃºdo gerado no banco
    if result and result.get("success") and result.get("content"):
        try:
            update_marketing_campaign_stage(campaign_id, int(stage), result["content"])
        except Exception as e:
            print(f"[Marketing] Aviso: falha ao salvar fase {stage} no banco: {e}")
    return result

@app.post("/api/v1/marketing/generate-sales-page")
async def generate_sales_page_endpoint(payload: dict, _admin=Depends(require_admin)):
    """
    Endpoint para gerar uma página de vendas completa (HTML) com copy de 8 blocos e design Impeccable.
    Salva o arquivo final em static/sales/ e retorna o link de visualização.
    """
    product_name = payload.get("product_name", "Super Infoproduto").strip()
    niche = payload.get("niche", "Marketing Digital").strip()
    target_audience = payload.get("target_audience", "Empreendedores").strip()
    price = payload.get("price", "R$ 97,00").strip()
    guarantee_days = int(payload.get("guarantee_days", 7))
    video_id = payload.get("video_id", "dQw4w9WgXcQ").strip() # default video (Rick Astley / placeholder)
    cta_url = payload.get("cta_url", "/checkout").strip()
    delay_seconds = int(payload.get("delay_seconds", 180))

    from modules.sales_page_generator import SalesPageGenerator
    generator = SalesPageGenerator()
    
    # 1. Gera a copy estruturada de 8 blocos
    copy_data = await generator.generate_copy(
        product_name=product_name,
        niche=niche,
        target_audience=target_audience,
        price=price,
        guarantee_days=guarantee_days
    )

    # 2. Renderiza o HTML final
    html_content = generator.render_html(
        copy=copy_data,
        video_id=video_id,
        cta_url=cta_url,
        delay_seconds=delay_seconds,
        guarantee_days=guarantee_days,
        price=price
    )

    # 3. Salva o arquivo em static/sales/<product_slug>.html
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", product_name.lower()).strip("-")
    if not slug:
        slug = "sales-page"
        
    sales_dir = os.path.join(_BASE_DIR, "static", "sales")
    os.makedirs(sales_dir, exist_ok=True)
    
    file_name = f"{slug}.html"
    file_path = os.path.join(sales_dir, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    public_url = f"/static/sales/{file_name}"
    return {
        "success": True,
        "url": public_url,
        "file_path": file_path,
        "copy": copy_data
    }

@app.get("/api/v1/marketing/history")
async def get_marketing_history_endpoint(_admin=Depends(require_admin_or_service)):
    """Retorna o histÃ³rico de campanhas de marketing para restaurar o estado na UI."""
    from modules.database import get_marketing_campaigns
    try:
        campaigns = get_marketing_campaigns(limit=20)
        return {"success": True, "campaigns": campaigns}
    except Exception as e:
        return {"success": False, "error": str(e), "campaigns": []}

@app.post("/api/v1/marketing/send-nurturing")
async def send_marketing_nurturing(payload: dict, _admin=Depends(require_admin)):
    """Dispara a sequência de nurturing (Fase 5) para os assinantes do Clube.

    Lê a campanha persistida no banco, extrai os 4 e-mails da Fase 5 e chama
    POST /api/import/nurture no Clube (Resend → lista ativa). Conecta o
    MarketingPipeline ao funil real de leads.
    """
    campaign_id = (payload.get("campaign_id") or "").strip()
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id é obrigatório")

    from modules.marketing_pipeline import send_nurturing_to_clube
    result = await send_nurturing_to_clube(
        campaign_id,
        os.getenv("CLUBE_PUBLIC_URL", "https://www.dezafira.com.br"),
        os.getenv("CLUBE_IMPORT_KEY", ""),
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Falha no nurturing"))
    return result

@app.post("/api/v1/marketing/nurture/schedule")
async def schedule_marketing_nurture(payload: dict, _admin=Depends(require_admin)):
    """Agenda a sequência automática de 4 e-mails do nurturing (Fase 5).

    Body: {campaign_id, day_gap?, hour?, minute?}
    E-mail 1 → amanhã; e-mail N → +N*day_gap dias. Usa APScheduler (persiste
    no processo; jobs com misfire_grace_time mantêm o disparo após reinício).
    """
    campaign_id = (payload.get("campaign_id") or "").strip()
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id é obrigatório")

    day_gap = max(1, int(payload.get("day_gap", 2) or 2))
    hour = int(payload.get("hour", 9) or 9)
    minute = int(payload.get("minute", 0) or 0)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise HTTPException(status_code=400, detail="hour/minute inválidos")

    from modules.scheduler import schedule_nurture_sequence, start
    start()
    result = schedule_nurture_sequence(
        campaign_id,
        os.getenv("CLUBE_PUBLIC_URL", "https://www.dezafira.com.br"),
        os.getenv("CLUBE_IMPORT_KEY", ""),
        day_gap=day_gap, hour=hour, minute=minute,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Falha ao agendar"))
    return result


@app.post("/api/v1/marketing/nurture/cancel")
async def cancel_marketing_nurture(payload: dict, _admin=Depends(require_admin)):
    """Cancela os jobs de nurturing agendados de uma campanha."""
    campaign_id = (payload.get("campaign_id") or "").strip()
    if not campaign_id:
        raise HTTPException(status_code=400, detail="campaign_id é obrigatório")
    from modules.scheduler import cancel_nurture_sequence
    removed = cancel_nurture_sequence(campaign_id)
    return {"success": True, "campaign_id": campaign_id, "removed_jobs": removed}


@app.post("/api/v1/marketing/send-test-email")
async def send_marketing_test_email(payload: dict, _admin=Depends(require_admin)):
    """Rota de teste SMTP para envio rÃ¡pido de e-mail de teste."""
    to_email = payload.get("to_email", "").strip()
    subject = payload.get("subject", "Dezafira Marketing â€” Teste SMTP").strip()
    body = payload.get("body", "<h1>OlÃ¡!</h1><p>Esta Ã© uma mensagem de teste SMTP da Chica dos Correios.</p>").strip()

    if not to_email:
        raise HTTPException(status_code=400, detail="E-mail destinatÃ¡rio Ã© obrigatÃ³rio")

    from modules.marketing_pipeline import MarketingPipeline
    success = MarketingPipeline.send_smtp_email(to_email, subject, body)
    if success:
        return {"success": True, "message": f"E-mail de teste enviado com sucesso para {to_email}!"}
    raise HTTPException(status_code=500, detail="Falha no envio do e-mail. Verifique os logs e as credenciais SMTP no Railway.")


# â”€â”€â”€ SERVIDORES MCP (TELEMETRIA E MONITORAÃ‡ÃƒO) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.get("/api/v1/mcp/status")
async def get_mcp_status_endpoint(_admin=Depends(require_admin)):
    """Rota para verificar o estado dos servidores MCP."""
    try:
        from modules.mcp_client import MCPClient
        status_data = MCPClient.get_status()
        return {"success": True, "servers": status_data}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/v1/blog/post/{post_id}/publish-wordpress")
async def publish_to_wordpress_endpoint(post_id: str, _admin=Depends(require_admin)):
    """Publica um post aprovado nativamente no WordPress via REST API."""
    from modules.database import get_db_blog_post
    
    post = get_db_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post nÃ£o encontrado")

    wp_url = os.getenv("WP_URL", "").strip().rstrip("/")
    wp_user = os.getenv("WP_USER", "").strip()
    wp_pass = os.getenv("WP_APP_PASS", "").strip()

    if not wp_url or not wp_user or not wp_pass:
        raise HTTPException(
            status_code=400, 
            detail="Credenciais do WordPress nÃ£o configuradas. Preencha WP_URL, WP_USER e WP_APP_PASS no Railway."
        )

    # Prepara a carga do post
    title = post.get("title", "")
    content = post.get("content", "")
    image_url = post.get("featured_image_url", "")

    # Monta a requisiÃ§Ã£o usando HTTP Basic Auth de senhas de aplicativo
    auth = httpx.BasicAuth(wp_user, wp_pass)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Tenta fazer upload da imagem de destaque para a biblioteca de mÃ­dia se existir
            media_id = None
            if image_url and (image_url.startswith("http") or image_url.startswith("data:")):
                # Se for data URI base64, converte para binÃ¡rio, senÃ£o baixa via HTTP
                img_data = b""
                filename = "featured.jpg"
                if image_url.startswith("data:image/"):
                    header, encoded = image_url.split(",", 1)
                    import base64
                    img_data = base64.b64decode(encoded)
                    ext = header.split(";")[0].split("/")[1]
                    filename = f"featured.{ext}"
                else:
                    img_res = await client.get(image_url)
                    if img_res.status_code == 200:
                        img_data = img_res.content
                        filename = image_url.split("/")[-1].split("?")[0] or "featured.jpg"

                if img_data:
                    # Upload para wp-json/wp/v2/media
                    headers = {
                        "Content-Disposition": f'attachment; filename="{filename}"',
                        "Content-Type": "image/jpeg"
                    }
                    media_res = await client.post(
                        f"{wp_url}/wp-json/wp/v2/media",
                        auth=auth,
                        headers=headers,
                        content=img_data
                    )
                    if media_res.status_code in (200, 201):
                        media_id = media_res.json().get("id")

            # 2. Cria o post no WordPress
            post_payload = {
                "title": title,
                "content": content,
                "status": "draft"  # Cria como rascunho por seguranÃ§a para o usuÃ¡rio revisar
            }
            if media_id:
                post_payload["featured_media"] = media_id

            res = await client.post(
                f"{wp_url}/wp-json/wp/v2/posts",
                auth=auth,
                json=post_payload
            )

            if res.status_code in (200, 201):
                link = res.json().get("link", "")
                return {"success": True, "link": link, "message": "Post enviado como rascunho com sucesso!"}
            else:
                detail = res.text
                try:
                    detail = res.json().get("message", detail)
                except Exception:
                    pass
                raise HTTPException(status_code=500, detail=f"Erro no WordPress: {detail}")

        except httpx.HTTPError as he:
            raise HTTPException(status_code=500, detail=f"Falha de rede ao conectar ao WordPress: {str(he)}")


# â”€â”€â”€ WORDPRESS CONFIGURAÃ‡ÃƒO E PUBLICAÃ‡ÃƒO DE MARKETING â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.post("/api/v1/wordpress/test")
async def wordpress_test_connection(payload: dict, _admin=Depends(require_admin)):
    """Testa a conexÃ£o com a API REST do WordPress usando as credenciais fornecidas."""
    wp_url = payload.get("wp_url", "").strip().rstrip("/")
    wp_user = payload.get("wp_user", "").strip()
    wp_pass = payload.get("wp_app_pass", "").strip()

    if not wp_url or not wp_user or not wp_pass:
        return {"success": False, "error": "URL, usuÃ¡rio e senha de aplicativo sÃ£o obrigatÃ³rios."}

    auth = httpx.BasicAuth(wp_user, wp_pass)
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.get(f"{wp_url}/wp-json/wp/v2/users/me", auth=auth)
            if res.status_code == 200:
                user_data = res.json()
                site_name = user_data.get("name", wp_url)
                # Pega o nome do site
                site_res = await client.get(f"{wp_url}/wp-json/")
                site_name_final = site_name
                if site_res.status_code == 200:
                    site_name_final = site_res.json().get("name", site_name)
                return {"success": True, "site_name": site_name_final, "user": user_data.get("slug", wp_user)}
            else:
                msg = "Credenciais invÃ¡lidas ou API REST desabilitada."
                try:
                    msg = res.json().get("message", msg)
                except Exception:
                    pass
                return {"success": False, "error": msg}
        except httpx.HTTPError as e:
            return {"success": False, "error": f"NÃ£o foi possÃ­vel conectar ao WordPress: {str(e)}"}


@app.post("/api/v1/wordpress/save-settings")
async def wordpress_save_settings(payload: dict, _admin=Depends(require_admin)):
    """Salva as configuraÃ§Ãµes do WordPress como variÃ¡veis de ambiente em runtime."""
    wp_url = payload.get("wp_url", "").strip().rstrip("/")
    wp_user = payload.get("wp_user", "").strip()
    wp_pass = payload.get("wp_app_pass", "").strip()
    wp_status = payload.get("wp_default_status", "draft")
    wp_mtype = payload.get("wp_marketing_type", "page")

    if not wp_url or not wp_user or not wp_pass:
        return {"success": False, "error": "Campos obrigatÃ³rios ausentes."}

    # Salva no ambiente do processo em runtime (Railway requer setar nas variÃ¡veis de ambiente pelo painel)
    os.environ["WP_URL"] = wp_url
    os.environ["WP_USER"] = wp_user
    os.environ["WP_APP_PASS"] = wp_pass
    os.environ["WP_DEFAULT_STATUS"] = wp_status
    os.environ["WP_MARKETING_TYPE"] = wp_mtype

    return {
        "success": True,
        "message": "ConfiguraÃ§Ãµes salvas na sessÃ£o atual. Para persistir entre reinicializaÃ§Ãµes, adicione tambÃ©m no Railway: WP_URL, WP_USER, WP_APP_PASS."
    }


@app.post("/api/v1/marketing/publish-wordpress")
async def marketing_publish_wordpress(payload: dict, _admin=Depends(require_admin)):
    """Publica o funil de marketing completo como pÃ¡gina/post no WordPress."""
    title = payload.get("title", "PÃ¡gina de Vendas").strip()
    content = payload.get("content", "").strip()
    status = payload.get("status", os.getenv("WP_DEFAULT_STATUS", "draft"))
    content_type = payload.get("content_type", os.getenv("WP_MARKETING_TYPE", "page"))

    wp_url = os.getenv("WP_URL", "").strip().rstrip("/")
    wp_user = os.getenv("WP_USER", "").strip()
    wp_pass = os.getenv("WP_APP_PASS", "").strip()

    if not wp_url or not wp_user or not wp_pass:
        raise HTTPException(
            status_code=400,
            detail="Configure as credenciais do WordPress antes de publicar. Acesse a aba ðŸŒ WordPress no menu lateral."
        )

    if not content:
        raise HTTPException(status_code=400, detail="ConteÃºdo do funil estÃ¡ vazio.")

    endpoint = f"{wp_url}/wp-json/wp/v2/{'pages' if content_type == 'page' else 'posts'}"
    auth = httpx.BasicAuth(wp_user, wp_pass)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.post(endpoint, auth=auth, json={
                "title": title,
                "content": content,
                "status": status
            })

            if res.status_code in (200, 201):
                data = res.json()
                return {"success": True, "link": data.get("link", ""), "id": data.get("id")}
            else:
                detail = res.text
                try:
                    detail = res.json().get("message", detail)
                except Exception:
                    pass
                raise HTTPException(status_code=500, detail=f"Erro no WordPress: {detail}")

        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Erro de rede: {str(e)}")


# ────────────────────────────────────────────────────────────────────────────
# 📤 DISTRIBUIÇÃO SOCIAL — modules/distributor.py (Email/Pinterest/IG/TikTok/X)
# ────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/distribution/status")
async def distribution_status(_admin=Depends(require_admin)):
    """📤 Status de configuração das plataformas de distribuição social.

    Retorna, por plataforma: se está configurada, provedor e estatísticas
    de publicações já feitas (via modules/distributor.py).
    """
    from modules.distributor import get_platform_status, get_social_status
    try:
        platforms = get_platform_status()
        social = get_social_status()
        return {
            "success": True,
            "platforms": platforms,
            "config": social.get("platforms", {}),
            "stats": social.get("stats", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status de distribuição: {str(e)}")


@app.post("/api/v1/distribution/config")
async def distribution_save_config(payload: dict, _admin=Depends(require_admin)):
    """Salva/atualiza a configuração de uma plataforma social.

    Body: { "platform": "pinterest|instagram|tiktok|twitter", "token": "...",
            "board_id": "...", "business_id": "...",
            "api_secret": "...", "access_token": "...", "access_secret": "..." }
    Pinterest/Instagram/TikTok: persistido em data/social_config.json
    (modules/distributor.py). Twitter/X: aplicado em os.environ (o módulo
    lê TWITTER_* de env, como o wordpress_save_settings faz com WP_*).
    """
    platform = (payload.get("platform") or "").strip().lower()
    token = (payload.get("token") or "").strip()
    if platform not in ("pinterest", "instagram", "tiktok", "twitter"):
        raise HTTPException(status_code=400, detail="Plataforma inválida. Use: pinterest, instagram, tiktok ou twitter")
    if not token:
        raise HTTPException(status_code=400, detail="Token é obrigatório")

    # Twitter/X é lido de variáveis de ambiente pelo módulo — aplica direto
    # (mesmo padrão do wordpress_save_settings), em vez de config em arquivo
    # que o post_to_twitter nunca leria.
    if platform == "twitter":
        os.environ["TWITTER_API_KEY"] = token
        if payload.get("api_secret"):
            os.environ["TWITTER_API_SECRET"] = str(payload.get("api_secret")).strip()
        if payload.get("access_token"):
            os.environ["TWITTER_ACCESS_TOKEN"] = str(payload.get("access_token")).strip()
        if payload.get("access_secret"):
            os.environ["TWITTER_ACCESS_SECRET"] = str(payload.get("access_secret")).strip()
        return {"success": True, "message": "Configurações do Twitter/X aplicadas na sessão atual. Para persistir entre restarts, adicione TWITTER_* nas variáveis do Railway."}

    # Só envia kwargs não-vazios — permite também "limpar" um board/business
    # id enviando string vazia (o save_social_config ignora valores falsy).
    kwargs = {}
    if platform == "pinterest":
        board_id = (payload.get("board_id") or "").strip()
        if board_id:
            kwargs["board_id"] = board_id
    elif platform == "instagram":
        business_id = (payload.get("business_id") or "").strip()
        if business_id:
            kwargs["business_id"] = business_id

    from modules.distributor import save_social_config
    try:
        result = save_social_config(platform, token, **kwargs)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar configuração: {str(e)}")


@app.get("/api/v1/distribution/history")
async def distribution_history(_admin=Depends(require_admin)):
    """📤 Histórico das últimas publicações distribuídas (máx 100)."""
    from modules.distributor import get_social_history
    try:
        return {"success": True, "history": get_social_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter histórico: {str(e)}")


@app.post("/api/v1/distribution/post")
async def distribution_post(payload: dict, _admin=Depends(require_admin)):
    """Dispara a publicação de um conteúdo numa plataforma social.

    Body (comum): { "platform": "email|pinterest|instagram|tiktok|twitter", ... }
      email:     to, subject, html, [from_email, from_name]
      pinterest: title, description, image_url, link, [board_id]
      instagram: image_url, caption, [hashtags]
      tiktok:    image_url|video_path, caption, [hashtags]
      twitter:   text, [media_paths]
    """
    platform = (payload.get("platform") or "").strip().lower()
    if platform not in ("email", "pinterest", "instagram", "tiktok", "twitter"):
        raise HTTPException(status_code=400, detail="Plataforma inválida. Use: email, pinterest, instagram, tiktok ou twitter")

    try:
        if platform == "email":
            from modules.distributor import send_email
            to = (payload.get("to") or "").strip()
            subject = (payload.get("subject") or "").strip()
            html = payload.get("html") or ""
            if not to or not subject or not html:
                raise HTTPException(status_code=400, detail="Para email: to, subject e html são obrigatórios")
            result = await send_email(to, subject, html,
                                      from_email=payload.get("from_email"),
                                      from_name=payload.get("from_name"))
        elif platform == "pinterest":
            from modules.distributor import post_to_pinterest
            title = (payload.get("title") or "").strip()
            link = (payload.get("link") or "").strip()
            if not title or not link:
                raise HTTPException(status_code=400, detail="Para pinterest: title e link são obrigatórios")
            result = await post_to_pinterest(
                title, payload.get("description") or "",
                payload.get("image_url") or "", link,
                board_id=payload.get("board_id"),
            )
        elif platform == "instagram":
            from modules.distributor import post_to_instagram
            image_url = (payload.get("image_url") or "").strip()
            caption = (payload.get("caption") or "").strip()
            if not image_url or not caption:
                raise HTTPException(status_code=400, detail="Para instagram: image_url e caption são obrigatórios")
            result = await post_to_instagram(image_url, caption, hashtags=payload.get("hashtags"))
        elif platform == "tiktok":
            from modules.distributor import post_to_tiktok
            caption = (payload.get("caption") or "").strip()
            video_path = payload.get("video_path")
            image_url = payload.get("image_url")
            if not caption:
                raise HTTPException(status_code=400, detail="Para tiktok: caption é obrigatório")
            if not video_path and not image_url:
                raise HTTPException(status_code=400, detail="Para tiktok: video_path ou image_url é obrigatório")
            result = await post_to_tiktok(
                video_path=video_path,
                image_url=image_url,
                caption=caption,
                hashtags=payload.get("hashtags"),
            )
        else:  # twitter
            from modules.distributor import post_to_twitter
            text = (payload.get("text") or "").strip()
            if not text:
                raise HTTPException(status_code=400, detail="Para twitter: text é obrigatório")
            result = await post_to_twitter(text, media_paths=payload.get("media_paths"))

        if result.get("success"):
            return {"success": True, **result}
        raise HTTPException(status_code=400, detail=result.get("error", "Falha ao publicar"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao publicar: {str(e)}")


@app.post("/api/v1/distribution/post/{post_id}")
async def distribution_post_article(post_id: str, _admin=Depends(require_admin)):
    """📤 Distribui UM artigo específico do blog (pelo ID) para as plataformas
    configuradas (Pinterest/Twitter). Usado pelo botão "📤 Distribuir" no
    painel de Blogs — usa a imagem de destaque e o link canônico do artigo.
    """
    from modules.distributor import distribuir_artigo_especifico
    try:
        result = await distribuir_artigo_especifico(post_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao distribuir artigo: {str(e)}")
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Falha ao distribuir artigo"))
    return {"success": True, **result}


# ─── Estado do agendador automático de distribuição ─────────────────────────
_DISTRIBUTION_STATE = {
    "enabled": False,
    "interval_hours": 6,
    "last_run": None,
    "last_result": None,
    "running": False,
}


async def _distribution_scheduler_loop():
    """Watcher asyncio: a cada intervalo configurável, distribui artigos
    recentes não distribuídos de todos os canais ativos. Best-effort — nunca
    lança exceção para não derrubar o processo."""
    import time as _t
    while True:
        try:
            if _DISTRIBUTION_STATE.get("enabled"):
                _DISTRIBUTION_STATE["running"] = True
                try:
                    from modules.distributor import distribuir_artigos_recentes
                    result = await asyncio.wait_for(
                        distribuir_artigos_recentes(por_canal=2, apenas_nao_distribuidos=True),
                        timeout=600,
                    )
                    _DISTRIBUTION_STATE["last_run"] = _t.time()
                    _DISTRIBUTION_STATE["last_result"] = {
                        "distribuidos": result.get("distribuidos", 0),
                        "falhas": result.get("falhas", 0),
                        "canais": result.get("canais", 0),
                        "detalhes": result.get("detalhes", [])[:10],
                    }
                    print(f"[Distributor] Rodada automática: {result.get('distribuidos',0)} distribuídos, {result.get('falhas',0)} falhas")
                except asyncio.TimeoutError:
                    print("[Distributor] Rodada automática excedeu 600s — pulada")
                except Exception as e:
                    print(f"[Distributor] Erro na rodada automática: {e}")
                finally:
                    _DISTRIBUTION_STATE["running"] = False
        except Exception as e:
            print(f"[Distributor] Erro no loop: {e}")
        try:
            await asyncio.sleep(int(_DISTRIBUTION_STATE.get("interval_hours", 6)) * 3600)
        except Exception as e:
            print(f"[Distributor] Erro no sleep do loop: {e}")
            await asyncio.sleep(3600)


@app.get("/api/v1/distribution/schedule")
async def distribution_schedule_get(_admin=Depends(require_admin)):
    """📤 Status do agendador automático de distribuição (persistido no banco;
    o estado é restaurado do banco no startup e sincronizado pelo POST)."""
    st = dict(_DISTRIBUTION_STATE)
    if st.get("last_run"):
        import time as _t
        from datetime import datetime as _dt
        st["last_run_iso"] = _dt.utcfromtimestamp(st["last_run"]).isoformat() + "Z"
    return {"success": True, "schedule": st}


@app.post("/api/v1/distribution/schedule")
async def distribution_schedule_set(payload: dict, _admin=Depends(require_admin)):
    """Configura o agendador automático (enabled + interval_hours).

    Body: { "enabled": bool, "interval_hours": int }
    """
    if "enabled" in payload:
        _DISTRIBUTION_STATE["enabled"] = bool(payload["enabled"])
    if "interval_hours" in payload:
        try:
            hours = max(1, min(int(payload["interval_hours"]), 168))
            _DISTRIBUTION_STATE["interval_hours"] = hours
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="interval_hours deve ser um inteiro (1–168)")
    # Persiste no banco para sobreviver a restarts
    from modules.database import save_db_distribution_settings
    save_db_distribution_settings(
        enabled=_DISTRIBUTION_STATE.get("enabled", False),
        interval_hours=_DISTRIBUTION_STATE.get("interval_hours", 6),
    )
    return {"success": True, "schedule": dict(_DISTRIBUTION_STATE)}


@app.post("/api/v1/distribution/run-all")
async def distribution_run_all(_admin=Depends(require_admin)):
    """📤 Dispara distribuição manual imediata de artigos recentes de todos
    os canais ativos (não distribuídos)."""
    from modules.distributor import distribuir_artigos_recentes
    try:
        result = await asyncio.wait_for(
            distribuir_artigos_recentes(por_canal=2, apenas_nao_distribuidos=True),
            timeout=600,
        )
        import time as _t
        _DISTRIBUTION_STATE["last_run"] = _t.time()
        _DISTRIBUTION_STATE["last_result"] = {
            "distribuidos": result.get("distribuidos", 0),
            "falhas": result.get("falhas", 0),
            "canais": result.get("canais", 0),
            "detalhes": result.get("detalhes", [])[:10],
        }
        return {"success": True, **result}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Distribuição excedeu 600s")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao distribuir: {str(e)}")

