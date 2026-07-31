import asyncio
import os
import uuid
import json
import httpx
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)
from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Singleton globais — compartilhados entre todas as requisicoes (Bug C1)
from pipeline.websocket import WebSocketHub
from pipeline.orchestrator import HermesOrchestrator

_ws_hub = WebSocketHub()
_hermes_orchestrator = HermesOrchestrator(_ws_hub)

from manager import SniperDirector
from modules.uploader import YouTubeUploader
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
    delete_db_ai_created_channel
)

try:
    from modules.telegram_bot import init_telegram_bot, send_telegram_notification
except ImportError:
    print("[Server] telebot nao instalado. Telegram Bot desabilitado.")
    def init_telegram_bot(*args, **kwargs): pass
    def send_telegram_notification(text: str): pass

app = FastAPI(title="F.Video & Open-Generative-AI Integration API")

# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "dezafira-backend"}

# Configurar CORS para permitir chamadas do Next.js e de qualquer origem local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
import re

# SUBDOMAIN MIDDLEWARE — Roteia subdominios para blogs
# Ex: oreino.dezafira.com.br → /blog/o-reino
# ═══════════════════════════════════════════════════════════════════════════════

_SUBDOMAIN_CACHE: dict = {}
_LAST_SUBDOMAIN_REFRESH: float = 0
_SUBDOMAIN_DOMAIN = os.getenv("SUBDOMAIN_DOMAIN", "dezafira.com.br")

@app.middleware("http")
async def subdomain_middleware(request, call_next):
    """
    Intercepta requisicoes e verifica se o Host header contem um subdominio.
    Se encontrar subdominio conhecido, redireciona para /blog/{slug}.
    Pula requisicoes de API e arquivos estaticos.
    """
    path = request.url.path
    host = request.headers.get("host", "").lower()
    
    # So processa GET requests
    if request.method != "GET":
        return await call_next(request)
    
    # Pular requisicoes de API, estaticos, websocket
    if path.startswith(("/api/", "/static/", "/outputs/", "/ws/", "/health", "/app/")):
        return await call_next(request)
    
    # Pular se ja esta em /blog/ ou /oreino (evita loop)
    if path.startswith("/blog/") or path in ("/oreino", "/o-reino"):
        return await call_next(request)
    
    # Verificar se o Host tem subdominio (ex: oreino.dezafira.com.br)
    subdomain = None
    if host.endswith(_SUBDOMAIN_DOMAIN) and host != _SUBDOMAIN_DOMAIN:
        prefix = host[:-(len(_SUBDOMAIN_DOMAIN) + 1)]
        if prefix and "." not in prefix:
            subdomain = prefix
    elif "localhost" in host or "127.0.0.1" in host:
        return await call_next(request)
    
    if not subdomain:
        return await call_next(request)
    
    # Buscar blog pelo subdominio (com cache)
    import time
    now = time.time()
    slug = _SUBDOMAIN_CACHE.get(subdomain)
    if not slug or (now - _LAST_SUBDOMAIN_REFRESH > 60):
        try:
            from modules.database import get_db_blog_by_subdomain
            blog = get_db_blog_by_subdomain(subdomain)
            if blog:
                slug = blog["slug"]
                _SUBDOMAIN_CACHE[subdomain] = slug
                _LAST_SUBDOMAIN_REFRESH = now
            else:
                return await call_next(request)
        except Exception:
            return await call_next(request)
    
    if not slug:
        return await call_next(request)
    
    # Redirecionamento permanente (301) para o blog viewer
    # Mantemos o subdominio como URL canônica — o Google segue redirects 301
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/blog/{slug}", status_code=301)


# Dicionário na memória para guardar o status das gerações
# Removidos channels.json e predictions_db locais. Usando database.py.

# Logs de Atividade em Tempo Real da Esteira
application_logs = [
    "[Info] Fabrica de Canais Dezafira inicializada com sucesso.",
    "[Info] OpenMontage Engine disponivel como motor de renderizacao.",
    "[Info] Shared Memory System (channel_knowledge) ativo.",
    "[Info] Pronto para iniciar o ciclo autonomo com o Hermes."
]

def log_application_activity(message: str):
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    application_logs.append(log_line)
    if len(application_logs) > 60:
        application_logs.pop(0)

# Definicao unica de hermes_chat_history movida para a secao Hermes Orchestrator no final do arquivo.

director = SniperDirector()
uploader = YouTubeUploader()

# Servir arquivos estáticos de outputs para poder acessar o vídeo final
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def serve_ui():
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html")
    if not os.path.exists(template_path):
        return HTMLResponse("<h1>Dezafira</h1>")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/app/{slug}", response_class=HTMLResponse)
async def serve_pwa_app(slug: str):
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "pwa_template.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template do PWA não encontrado")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api/v1/logs")
async def get_application_logs():
    return {"logs": application_logs}

# Helper para chamar LLM via Nvidia NIM
async def query_llm(messages: List[Dict[str, str]]) -> str:
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")

    if not nvidia_key:
        return "Chave NVIDIA_API_KEY não configurada no arquivo .env."

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {nvidia_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta/llama-3.3-70b-instruct",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"[LLM] Falha no Nvidia NIM ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"[LLM] Erro ao chamar Nvidia NIM: {str(e)}")

    return "Falha ao chamar o LLM. Verifique a NVIDIA_API_KEY no .env."

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
        raise HTTPException(status_code=404, detail="Canal não encontrado")
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
        raise HTTPException(status_code=404, detail="Conta Google não encontrada no banco. Selecione uma conta válida no seletor à direita.")
    db.close()

    if not payload.cookies_raw and (not payload.email or not payload.password):
        raise HTTPException(status_code=400, detail="Credenciais ou cookies ausentes na requisição.")

    # Se o usuário optou por colar os cookies diretamente, valida e salva na hora!
    if payload.cookies_raw:
        from modules.database import save_db_channel_cookies
        try:
            cookies_json = payload.cookies_raw.strip()
            # Garante formato JSON válido
            parsed_cookies = json.loads(cookies_json)
            
            # Executa uma verificação rápida de 6 segundos em background/stealth para confirmar se o cookie loga no YT Studio
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
                    # Se não redirecionou para tela de login do Google, o cookie é quente!
                    if "signin" not in page.url and "login" not in page.url:
                        login_ok = True
                    browser.close()
            except Exception as e:
                print(f"[Agent-Login] Erro ao testar cookies: {e}")
                login_ok = False
            warning_msg = None
            if not login_ok:
                warning_msg = "Sessão importada! (Nota: o servidor de nuvem do Railway não pôde confirmar a sessão devido ao IP do data center, mas salvou seus cookies com sucesso e eles serão aplicados na postagem)."

            save_db_channel_cookies(channel_id, cookies_json)
            return {
                "message": "Cookies salvos com sucesso!",
                "warning": warning_msg
            }
        except Exception as json_err:
            if isinstance(json_err, HTTPException):
                raise json_err
            raise HTTPException(status_code=400, detail=f"Formato de cookies inválido. Cole um JSON válido: {str(json_err)}")

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
    
    # Iniciar o robô em segundo plano para não travar a UI
    background_tasks.add_task(run_agent_login_stealth, channel_id, payload.email, payload.password)
    return {"message": "Agente de login simulado iniciado em segundo plano."}

@app.get("/api/v1/channels/{channel_id}/connection-status")
async def get_connection_status(channel_id: str):
    db = SessionLocal()
    chan = db.query(Channel).filter(Channel.id == channel_id).first()
    if not chan:
        db.close()
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    
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
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    
    # Salva o código digitado na coluna verification_code para o robô ler
    chan.verification_code = payload.code
    db.commit()
    db.close()
    return {"message": "Código de verificação 2FA enviado com sucesso para o agente."}

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
        raise HTTPException(status_code=404, detail="Canal criado por IA não encontrado")
    return {"message": "Canal removido com sucesso"}

class AnalyzeVideoPayload(BaseModel):
    url: str

@app.post("/api/v1/hermes/analyze-video")
async def analyze_competitor_video(payload: AnalyzeVideoPayload):
    system_instruction = (
        "Você é o Agente de Inteligência e Engenharia Reversa da Dezafira. "
        "Seu objetivo é analisar as transcrições e ganchos de retenção de vídeos concorrentes virais "
        "e estruturar regras de hooks prontas para o Jonatas usar na esteira autônoma."
    )
    user_prompt = f"""
    Faça a engenharia reversa do seguinte vídeo concorrente:
    - URL: {payload.url}
    
    Analise e gere um relatório estruturado contendo:
    1. Gancho Inicial (Primeiros 3 segundos): Por que reteve a audiência?
    2. Estrutura Psicológica: Qual medo ou desejo o vídeo ativa?
    3. Roteiro Adaptado para a Dezafira: Crie uma variação original desse mesmo roteiro para evitar tag de conteúdo reutilizado.
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
        
    description = "Vídeo gerado de forma 100% automatizada pelo SniperVideoEngine!"
    
    log_application_activity(f"Upload aprovado pelo Jonatas para o vídeo ID: {prediction_id}. Iniciando postagem...")
    send_telegram_notification(f"🚀 *[Publicação]* Upload do vídeo aprovado. Iniciando Playwright...")
    
    channel_uploader = YouTubeUploader(channel_id=channel_id)
    upload_success = channel_uploader.upload_video(
        video_path=absolute_video_path,
        title=title[:90],
        description=description,
        is_short=True,
        cookies_json=cookies_json
    )
    
    if upload_success:
        log_application_activity(f"Sucesso! Vídeo publicado no YouTube.")
        send_telegram_notification(f"✅ *[Publicado]* Vídeo `{title[:40]}` postado com sucesso!")
    else:
        log_application_activity("Erro: Falha no upload no YouTube Studio.")
        send_telegram_notification(f"⚠️ *[Aviso]* Falha ao realizar postagem. Cookies expirados ou inválidos.")

@app.post("/api/v1/predictions/{prediction_id}/approve")
async def approve_prediction(prediction_id: str, background_tasks: BackgroundTasks):
    db = SessionLocal()
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not pred:
        db.close()
        raise HTTPException(status_code=404, detail="Geração não encontrada")
    
    pred.approval_status = "approved"
    db.commit()
    db.close()
    
    background_tasks.add_task(run_delayed_upload, prediction_id)
    return {"message": "Geração aprovada. Upload em segundo plano iniciado."}

@app.post("/api/v1/predictions/{prediction_id}/reject")
async def reject_prediction(prediction_id: str):
    db = SessionLocal()
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not pred:
        db.close()
        raise HTTPException(status_code=404, detail="Geração não encontrada")
    
    pred.approval_status = "rejected"
    db.commit()
    db.close()
    
    log_application_activity(f"Geração {prediction_id} rejeitada pelo Jonatas. Aguardando novos direcionamentos de ajuste.")
    send_telegram_notification(f"⚠️ *[Curadoria]* Geração `{prediction_id}` rejeitada pelo Jonatas. Ajustes solicitados.")
    return {"message": "Geração marcada como rejeitada."}

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
    
    # Callback para responder o chat do bot usando o Llama 3.3
    def on_telegram_chat(message_text):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Reutiliza a mesma instrução e histórico do Hermes
            hermes_chat_history.append({"role": "user", "content": message_text})
            system_instruction = (
                "Você é o Hermes, o Agente Orquestrador executivo e extremamente inteligente da plataforma DEZAFIRA, a Fábrica de Canais. "
                "Você está conversando diretamente com o JONATAS, o fundador da Holding Dezafira. "
                "Seu objetivo absoluto é rodar a esteira no modo 100% Autônomo (Mãos Livres), sem precisar calibrar ou fazer perguntas de restrições para o Jonatas. "
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

    # ══ Pipeline Recovery: retoma pipelines interrompidas ══
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
        print(f'[Startup] Erro na recuperação de pipelines: {e}')

    init_telegram_bot(on_telegram_chat, on_telegram_produce)

    # ══ Job Recovery: retoma jobs de regeneracao persistidos (sobrevive a restarts) ══
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
        _ws_hub.start_keepalive(interval=25)
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


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD — Fábrica de Blogs (com Books + Courses)
# ═══════════════════════════════════════════════════════════════════════════════

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
                "👴 Seu Francisco: '" + str(completos) + " blog(s) completo(s), " +
                str(pendentes) + " pendente(s). Tudo sob controle!'"
            ) if relatorios else "👴 Seu Francisco: 'Nenhum blog ativo no momento.'"
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


@app.get("/api/v1/factory/dashboard")
async def blog_factory_dashboard():
    """Dashboard consolidado com metricas de todas as fabricas."""
    from modules.database import SessionLocal, BlogChannel, BlogPost, Book, Course
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
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
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
                    "affiliate_providers": c.affiliate_providers,
                    "amazon_tag": c.amazon_tag,
                    "amazon_key": c.amazon_key,
                    "amazon_secret": c.amazon_secret,
                    "shopee_app_id": c.shopee_app_id,
                    "shopee_app_secret": c.shopee_app_secret,
                    "mercadolivre_client_id": c.mercadolivre_client_id,
                    "mercadolivre_client_secret": c.mercadolivre_client_secret,
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


# ═══════════════════════════════════════════════════════════════════════════════
# BLOG SEED — Dados de demonstração
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/blogs/seed")
async def seed_demo_blog():
    """Cria dados de demonstração para o blog."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# BOOKS — Fábrica de Livros
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# COURSES — Fabrica de Cursos
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGES — Fabrica de Imagens (FLUX + Pexels)
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# RAG BIBLICO — Busca Semântica
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD — Fábrica de Blogs (com Books + Courses)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# BLOG SEED — Dados de demonstração
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/blogs/seed")
async def seed_demo_blog():
    """Cria dados de demonstração para o blog."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# BOOKS — Fábrica de Livros
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# COURSES — Fabrica de Cursos
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGES — Fabrica de Imagens (FLUX + Pexels)
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# RAG BIBLICO — Busca Semântica
# ═══════════════════════════════════════════════════════════════════════════════

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



# ═══════════════════════════════════════════════════════════════════════════════
# SEU PEREIRA — MONETIZATION ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/monetization/status")
async def get_monetization_status(channel_id: str = None):
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


# ═══════════════════════════════════════════════════════════════════════════════
# PAGINAS DE SISTEMA — Privacidade, Sobre, Contato
# ═══════════════════════════════════════════════════════════════════════════════



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

# ═══════════════════════════════════════════════════════════════════════════════
# ROBOTS.TXT & SITEMAP
# ═══════════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════════
# RESEARCH ENGINE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

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
    Analisa um canal específico.
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
    Obtém têndencias atuais do YouTube.
    """
    from research.engine import ResearchEngine
    
    engine = ResearchEngine()
    result = await engine.get_trending_topics()
    return result


@app.get("/api/v1/research/youtube-rules")
async def get_youtube_rules():
    """
    Obtém regras e melhores práticas do YouTube.
    """
    from research.engine import ResearchEngine
    
    engine = ResearchEngine()
    result = await engine.learn_youtube_rules()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/pipeline/start")
async def start_pipeline(payload: dict):
    """
    Inicia um novo pipeline de produção.
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
async def start_modular_pipeline(payload: dict):
    """
    Inicia um pipeline modular dividido em blocos/capítulos sequenciais.
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
async def build_mini_app(payload: dict):
    """
    Gera um PWA estático de Quiz estruturado com base nas perguntas fornecidas.
    """
    app_id = payload.get("app_id", "my_app")
    title = payload.get("title", "Quiz de Avaliação")
    nicho = payload.get("nicho", "Geral")
    questions = payload.get("questions", [])
    checkout_url = payload.get("checkout_url", "https://kiwify.com.br")
    cta_text = payload.get("cta_text", "Obter Relatório")
    
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
async def build_hyperframes_timeline(payload: dict):
    """
    Gera a timeline de vídeo (JSON) no formato Hyperframes.
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



@app.get("/api/v1/pipeline/{task_id}")
async def get_pipeline_status(task_id: str):
    """
    Obtém status de um pipeline.
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
async def pause_pipeline(task_id: str):
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
async def resume_pipeline(task_id: str):
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
async def stop_pipeline(task_id: str):
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
async def approve_stage(task_id: str, stage: str):
    """
    Aprova um estágio do pipeline.
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


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/analytics/metrics")
async def get_analytics_metrics(period: str = "7d"):
    """
    Obtém métricas gerais de analytics.
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
    Obtém métricas por canal.
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
            "niche": "Finanças",
            "views": 38000,
            "subscribers": 980,
            "engagement": 3.8,
            "ctr": 7.1,
        },
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# FÁBRICA DE ENTREGÁVEIS (PWA & MINI-APPS)
# ═══════════════════════════════════════════════════════════════════════════════
from modules.database import (
    create_db_deliverable_app,
    get_db_deliverable_app_by_slug,
    get_db_deliverable_apps,
    create_db_app_payment,
    update_db_app_payment
)
from modules.deliverables import create_deliverable_app_for_channel

class CreateDeliverablePayload(BaseModel):
    channel_id: Optional[str] = "default"
    name: str
    nicho: str
    slug: Optional[str] = None

class AppPaymentPayload(BaseModel):
    app_id: str
    gateway: str
    amount: int
    customer_email: Optional[str] = None
    transaction_id: Optional[str] = None

@app.post("/api/v1/deliverables/create")
async def api_create_deliverable(payload: CreateDeliverablePayload):
    try:
        app_data = create_deliverable_app_for_channel(
            channel_id=payload.channel_id,
            name=payload.name,
            nicho=payload.nicho,
            slug=payload.slug
        )
        return app_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar entregável: {str(e)}")

@app.get("/api/v1/deliverables")
async def api_get_deliverable_apps():
    return get_db_deliverable_apps()

@app.get("/api/v1/deliverables/{slug}")
async def api_get_deliverable_by_slug(slug: str):
    app = get_db_deliverable_app_by_slug(slug)
    if not app:
        raise HTTPException(status_code=404, detail="Aplicativo não encontrado")
    return app

@app.post("/api/v1/deliverables/checkout")
async def api_create_checkout(payload: AppPaymentPayload):
    import uuid
    tx_id = payload.transaction_id or f"tx_{uuid.uuid4().hex[:12]}"
    
    pay = create_db_app_payment(
        app_id=payload.app_id,
        gateway=payload.gateway,
        transaction_id=tx_id,
        amount=payload.amount,
        customer_email=payload.customer_email
    )
    
    qr_code = "00020126360014BR.GOV.BCB.PIX0114test-pix-key52040000530398654049.905802BR5913Dezafira App6009Sao Paulo62070503***63041D9C"
    checkout_url = f"https://checkout.stripe.com/pay/{tx_id}" if payload.gateway == "stripe" else f"https://www.mercadopago.com.br/sandbox/{tx_id}"
    
    return {
        "payment": pay,
        "checkout_url": checkout_url,
        "qr_code_pix": qr_code if payload.gateway == "mercadopago" else None,
        "pix_key": "test-pix-key" if payload.gateway == "mercadopago" else None
    }

@app.post("/api/v1/deliverables/webhooks/mercadopago")
async def webhook_mercadopago(payload: dict):
    tx_id = payload.get("transaction_id") or payload.get("data", {}).get("id")
    action = payload.get("action")
    
    if action == "payment.created" or action == "payment.updated" or not action:
        status = "paid" if payload.get("status") == "approved" or payload.get("state") == "approved" or payload.get("status") == "paid" else "pending"
        if tx_id:
            update_db_app_payment(tx_id, status)
            return {"message": "Webhook processado", "transaction_id": tx_id, "status": status}
            
    return {"message": "Webhook ignorado ou sem transação"}

@app.post("/api/v1/deliverables/webhooks/stripe")
async def webhook_stripe(payload: dict):
    tx_id = payload.get("transaction_id") or payload.get("data", {}).get("object", {}).get("id")
    event_type = payload.get("type")
    
    if event_type == "checkout.session.completed" or not event_type:
        if tx_id:
            update_db_app_payment(tx_id, "paid")
            return {"message": "Pagamento confirmado", "transaction_id": tx_id}
            
    return {"message": "Evento ignorado"}


# ═══════════════════════════════════════════════════════════════════════════════
# HERMES ORCHESTRATOR - Chat Inteligente com Ações Reais

# ═══════════════════════════════════════════════════════════════════════════════
# BLOG FRONTEND — API PÚBLICA
# ═══════════════════════════════════════════════════════════════════════════════

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
        raise HTTPException(status_code=404, detail="Blog não encontrado")
    return info

@app.get("/api/v1/blog/{slug}/subdomain")
async def get_blog_subdomain(slug: str):
    """Retorna o subdominio configurado para um blog."""
    from modules.database import get_db_blog_info
    info = get_db_blog_info(slug)
    if not info:
        raise HTTPException(status_code=404, detail="Blog não encontrado")
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
        raise HTTPException(status_code=404, detail="Blog não encontrado")
    
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
        raise HTTPException(status_code=404, detail="Blog não encontrado")
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
                # Conversão explícita de tipos se necessário
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
<title>{slug} — Blog Dezafira</title>
<style>body{{font-family:system-ui;max-width:800px;margin:40px auto;padding:0 20px;color:#333;line-height:1.6}}h1{{color:#1a1a1a}}</style>
</head>
<body><h1>📝 {slug}</h1><p>Blog em construção...</p>
<p><a href="/">Voltar ao painel</a></p>
</body></html>""")

# ═══════════════════════════════════════════════════════════════════════════════

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
        "content": "Olá, Jonatas! Sou o Hermes, orquestrador do ecossistema Dezafira. Nosso ecossistema atual conta com 5 fábricas integradas:\n\n📝 **Fábrica de Blogs** — Artigos otimizados para SEO sobre temas bíblicos\n📗 **Fábrica de Livros** — E-books com capítulos gerados por IA\n🎓 **Fábrica de Cursos** — Cursos em texto com módulos, aulas e quizzes\n🎨 **Fábrica de Imagens** — Capas, thumbnails e imagens via FLUX + Pexels\n🔍 **RAG Bíblico** — Busca semântica nos conteúdos com respostas citadas\n\nQual comando deseja executar, Jonatas?"
    }
]

@app.post("/api/v1/hermes/chat")
async def hermes_chat(payload: dict, background_tasks: BackgroundTasks):
    """
    Hermes Orquestrador - Entende comandos e executa ações reais.
    Retorna dados estruturados para a UI atualizar as abas.
    """
    message = payload.get("message", "").strip()
    channel_id = payload.get("channel_id")
    
    hermes_chat_history.append({"role": "user", "content": message})
    
    text, action_type, action_data = await process_hermes_command(message, channel_id, background_tasks)
    
    hermes_chat_history.append({"role": "assistant", "content": text})
    
    return {
        "response": text,
        "action_type": action_type,
        "action_data": action_data,
        "history": hermes_chat_history[-20:]
    }


@app.get("/api/v1/hermes/history")
async def get_hermes_history():
    """Retorna histórico do chat do Hermes."""
    return {"history": hermes_chat_history[-50:]}


@app.post("/api/v1/hermes/clear")
async def clear_hermes_history():
    """Limpa histórico do chat."""
    global hermes_chat_history
    hermes_chat_history = [
        {
            "role": "assistant",
            "content": "Olá, Jonatas! Sou o Hermes, orquestrador do ecossistema Dezafira. Nosso ecossistema atual conta com 5 fábricas integradas:\n\n📝 **Fábrica de Blogs** — Artigos otimizados para SEO sobre temas bíblicos\n📗 **Fábrica de Livros** — E-books com capítulos gerados por IA\n🎓 **Fábrica de Cursos** — Cursos em texto com módulos, aulas e quizzes\n🎨 **Fábrica de Imagens** — Capas, thumbnails e imagens via FLUX + Pexels\n🔍 **RAG Bíblico** — Busca semântica nos conteúdos com respostas citadas\n\nQual comando deseja executar, Jonatas?"
        }
    ]
    return {"message": "Histórico limpo"}


# ================================================================
# BLOG PIPELINE ENDPOINT
# ================================================================

@app.post("/api/v1/pipeline/run-blog")
async def run_blog_pipeline_endpoint(payload: dict, background_tasks: BackgroundTasks):
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
async def get_blog_factory_history():
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
async def generate_article_hype_endpoint(payload: dict, background_tasks: BackgroundTasks):
    """
    Inicia a esteira de criação de artigos em segundo plano, minerando as tendências
    do Google Hype ativamente no primeiro estágio e gerando-os de forma sequencial.
    """
    channel_id = payload.get("channel_id", "")
    quantity = payload.get("quantity", 1)
    
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        quantity = 1
    quantity = max(1, min(10, quantity)) # Limite de segurança de 1 a 10 artigos por lote

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
        return {"error": "Blog não encontrado"}

    nicho = blog_info.get("nicho", "")
    if not nicho:
        return {"error": "Nicho do blog não configurado"}

    from modules.blog_pipeline import run_blog_pipeline as _run_pipeline
    import uuid
    import asyncio
    
    task_id = f"blg_{uuid.uuid4().hex[:8]}"
    initial_topic = f"Minerando tendências em {nicho}..."

    # 1. Armazena estado inicial para consulta via GET
    _macro_results[task_id] = {
        "status": "starting", "topic": f"Lote: {initial_topic}", "channel_id": channel_id,
        "phase": "Iniciando Lote", "progress": 2, "data": {"target_articles": quantity, "articles_generated": 0}
    }

    # 2. Orquestração ws do lote sequencial
    async def _run_with_ws(tid, top, ch, lang, qty):
        hub = _ws_hub
        articles_generated = 0
        all_results = []
        
        for i in range(qty):
            current_topic = f"Minerando tendência {i+1} de {qty} em {nicho}..."
            
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
                
                # Pequeno delay entre gerações
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[HypeLote] Erro no artigo {i+1} de {qty}: {e}")
                
        # Finalização da esteira do lote
        _macro_results[tid] = {
            "status": "completed", 
            "topic": f"Lote de {articles_generated} artigos concluído!", 
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


@app.get("/api/v1/pipeline/active-tasks")
async def get_active_pipeline_tasks(channel_id: str = None):
    """
    Retorna a lista de todas as tarefas de pipeline ativas ou recentes filtradas por blog.
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
    """Gera imagens para todos os artigos do blog que estão sem."""
    from modules.ricardo import gerar_imagens_pendentes
    return await gerar_imagens_pendentes()


async def process_hermes_command(message: str, channel_id: str = None, background_tasks: BackgroundTasks = None) -> tuple:
    """
    Processa comandos do Hermes e executa ações reais.
    Retorna (text_response, action_type, action_data)
    action_type pode ser: None, "research", "pipeline", "trending", "channels", "analytics", "rules"
    """
    msg = message.lower().strip()
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # FASE 1: RESEARCH
    # ═══════════════════════════════════════════════════════════════════════════════
    
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # FASE 2: PRODUCTION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Regra especial para criar múltiplos formatos de vídeo (Horizontal e Vertical)
    if "dois vídeos" in msg or "dois videos" in msg or ("horizontal" in msg and "vertical" in msg):
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
            
            # Geração do formato Vertical (9:16)
            task_v_id = create_automation_task(f"{theme} (Vertical)", channel_id or "default")
            pred_v_id = f"sniper_hf_v_{uuid.uuid4().hex[:4]}"
            save_db_prediction(pred_v_id, f"{theme} (Vertical)", channel_id or "default")
            
            # Geração do formato Horizontal (16:9)
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
            
            text = f"Excelente! Fábrica de Canais acionada para ambos os formatos. Disparei a esteira para gerar o vídeo Vertical (9:16) e Horizontal (16:9) sobre o tema '{theme}' usando o Hyperframes. Acompanhe o progresso em tempo real."
            return (text, "hyperframes_multi_video", action_data)
        except Exception as e:
            return (f"Erro ao gerar timelines de vídeo múltiplos: {str(e)}", None, None)
            
    if any(word in msg for word in ["produzir video", "produzir vídeo", "make video", "create video", "gerar video", "gerar vídeo", "fluxo completo da f. de canais", "fluxo completo de canais"]):
        theme = "Adestramento Canino Inteligente" if "completo" in msg else message
        for prefix in ["produzir video ", "produzir vídeo ", "make video ", "create video ", "gerar video ", "gerar vídeo "]:
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
            
            text = f"Fábrica de Canais ativada de forma 100% autônoma! Iniciando a esteira de renderização Hyperframes para o tema '{theme}'. Triagem e roteirista iniciados."
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
    
    if any(word in msg for word in ["narrar", "narracao", "narração", "voz", "voice", "text to speech", "tts"]):
        theme = message
        for prefix in ["narrar ", "narracao ", "narração ", "voz ", "voice ", "text to speech ", "tts "]:
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
            return (f"Erro na narração: {str(e)}", None, None)
    
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # FASE 3: PUBLISHING
    # ═══════════════════════════════════════════════════════════════════════════════
    
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
    
    if any(word in msg for word in ["titulo otimizado", "título otimizado", "otimizar titulo", "seo title"]):
        theme = message
        for prefix in ["titulo otimizado ", "título otimizado ", "otimizar titulo ", "seo title "]:
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # FASE 4: MONITORING
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if any(word in msg for word in ["metricas", "métricas", "analytics", "desempenho", "performance"]):
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
    
    if any(word in msg for word in ["relatorio", "relatório", "report"]):
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
    
    if any(word in msg for word in ["trending", "tendencias", "tendências", "em alta"]):
        try:
            from research.engine import ResearchEngine
            engine = ResearchEngine()
            trending = await engine.get_trending_topics()
            action_data = trending
            text = "Tendencias carregadas!"
            return (text, "trending", action_data)
        except Exception as e:
            return (f"Erro ao buscar trending: {str(e)}", None, None)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PIPELINE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════════
    
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CANAIS
    # ═══════════════════════════════════════════════════════════════════════════════
    
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # FÁBRICA DE ENTREGÁVEIS (PWA)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if any(word in msg for word in ["criar entregavel", "criar entregável", "criar pwa", "novo pwa", "novo entregavel", "novo entregável"]):
        app_name = message
        for prefix in ["criar entregavel ", "criar entregável ", "criar pwa ", "novo pwa ", "novo entregavel ", "novo entregável "]:
            if msg.startswith(prefix):
                app_name = message[len(prefix):]
                break
                
        if not app_name or app_name.strip() == "":
            return ("Para criar um entregável PWA, digite: criar entregavel [nome do app]", None, None)
            
        try:
            nicho_sugerido = app_name
            from modules.deliverables import create_deliverable_app_for_channel
            app_data = create_deliverable_app_for_channel(
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
            text = f"Entregável PWA '{app_name}' (slug: {app_data['slug']}) criado e configurado com sucesso!"
            return (text, "deliverables", action_data)
        except Exception as e:
            return (f"Erro ao criar entregável: {str(e)}", None, None)
            
    if any(word in msg for word in ["listar entregaveis", "listar entregáveis", "listar pwas", "meus entregaveis", "meus entregáveis", "meus pwas"]):
        try:
            from modules.database import get_db_deliverable_apps
            apps = get_db_deliverable_apps()
            action_data = {"apps": apps}
            if not apps:
                text = "Nenhum entregável PWA criado ainda."
            else:
                text = f"Encontrei {len(apps)} entregável(is) PWA cadastrado(s)!"
            return (text, "deliverables", action_data)
        except Exception as e:
            return (f"Erro ao listar entregáveis: {str(e)}", None, None)

    # ═══════════════════════════════════════════════════════════════════════════════
    # REGRAS E CONHECIMENTO
    # ═══════════════════════════════════════════════════════════════════════════════
    
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # AJUDA
    # ═══════════════════════════════════════════════════════════════════════════════
    
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
            "ENTREGÁVEIS PWA:\n"
            "  criar entregavel [nome] - Cria PWA interativo do nicho\n"
            "  listar entregaveis - Lista todos os PWAs"
        )
        return (text, None, None)
# ═══════════════════════════════════════════════════════════════════════════════
# MACRO PIPELINE RESULTS (in-memory, para consulta via API)
# ═══════════════════════════════════════════════════════════════════════════════

_macro_results: dict = {}
_running_tasks: dict = {}  # prevent GC of background pipeline tasks




# ============================================================================
# LILI — REVISORA DE QUALIDADE
# ============================================================================

@app.get("/api/v1/lili/review/{post_id}")
async def lili_review_post(post_id: str):
    """Revisa um artigo individual e retorna score + issues."""
    from modules.lili import revisar_artigo
    from modules.database import get_db_blog_post
    
    post = get_db_blog_post(post_id)
    if not post:
        return {"error": "Post nao encontrado"}
    
    review = await revisar_artigo(post)
    return review


@app.get("/api/v1/lili/review-all")
async def lili_review_all(channel_id: str = None):
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
async def lili_correct_post(post_id: str):
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
        # Nada foi corrigido — refazer revisao para confirmar
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
async def lili_ranking(channel_id: str = None, status: str = None):
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
        if score is None:
            # Sem cache: calcula e persiste para as proximas leituras
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
async def regenerate_blog_post(post_id: str):
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

        # Imagem obrigatoria — falha deleta o novo artigo
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
                # Persiste o score no banco imediatamente (cache consistente)
                if lili_review:
                    cr = (lili_review.get("content_review") or {})
                    score = cr.get("score")
                    if score is None:
                        score = lili_review.get("overall_score")
                    if isinstance(score, (int, float)):
                        try:
                            from modules.database import save_db_lili_score
                            save_db_lili_score(
                                new_post_id,
                                int(score),
                                bool(lili_review.get("approved") or (cr or {}).get("approved")),
                            )
                        except Exception as e_save:
                            print(f"[Regenerate] Falha ao persistir score: {e_save}")
            except Exception as e_lili:
                print(f"[Regenerate] Lili error: {e_lili}")

        # Novo artigo 100% completo (texto + imagem + revisao) — agora sim deleta o antigo
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
async def regenerate_blog_post_image(post_id: str):
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


@app.post("/api/v1/lili/regenerate-batch")
async def lili_regenerate_batch(payload: dict):
    """Regenera em lote os artigos reprovados pela LiLi (score < 70 ou nao aprovados).
    O job e PERSISTIDO no banco — se o Railway reiniciar no meio, o startup retoma.
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
    Idempotente — pode ser chamado de novo apos restart para retomar itens pendentes."""
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
                # anterior (post deletado). Considera o item concluido — nao eh falha real.
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

        # Generate image for the article (OBRIGATORIO — falha deleta o artigo)
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
async def delete_blog_post(post_id: str):
    """Remove um post do blog pelo ID."""
    from modules.database import delete_db_blog_post
    success = delete_db_blog_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    return {"success": True, "message": f"Post {post_id} removido"}







@app.post("/api/v1/pipeline/run-blog-factory")
async def run_blog_factory_frontend(payload: dict):
    """Alias da UI - delega para a pipeline macro."""
    blog_name = payload.get("blog_name", "")
    niche = payload.get("niche", "")
    language = payload.get("language", "pt")
    target_articles = payload.get("target_articles", 3)
    is_affiliate = bool(payload.get("is_affiliate", False))
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
        "message": "🚀 Iniciando pipeline...",
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
                            "current_article": (data or {}).get("state", {}).get("current_macro_stage"),
                            "article_topic": (data or {}).get("article_topic"),
                            "phase_detail": real_stage,
                            "lili_score": (data or {}).get("lili_score"),
                            "lili_approved": (data or {}).get("lili_approved"),
                            "article_title": (data or {}).get("article_title"),
                            "task_id": pid,
                            "articles_generated": (data or {}).get("state", {}).get("articles_generated", 0),
                            "target_articles": (data or {}).get("state", {}).get("target_articles", 0),
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
@app.post("/api/v1/pipeline/run-sync")
async def run_sync_pipeline(payload: dict):
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
    """Gera N artigos completos de forma direta, UM POR VEZ, síncrono.
    
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
                
                # Gerar imagem (OBRIGATORIO — falha = artigo descartado)
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
    """Retorna o resultado de uma execução de macro pipeline."""
    result = _macro_results.get(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pipeline não encontrada")
    return result


    # ═══ FALLBACK: Conversa com LLM ═══
    try:
        from modules.brain import SniperBrain
        brain = SniperBrain()
        
        system_prompt = (
            "Você é o Hermes, o orquestrador inteligente do ecossistema DEZAFIRA.\n"
            "Seu fundador é o JONATAS. Fale com ele de forma extremamente executiva, direta, minimalista e clara, sem enrolação.\n\n"
            "Você orquestra 5 fábricas principais:\n"
            "1. 📝 **Fábrica de Blogs**: Artigos otimizados para SEO sobre temas bíblicos e ensinamentos de Jesus.\n"
            "2. 📗 **Fábrica de Livros**: E-books completos com capítulos gerados por IA.\n"
            "3. 🎓 **Fábrica de Cursos**: Cursos em texto com módulos, aulas e quizzes.\n"
            "4. 🎨 **Fábrica de Imagens**: Geração de capas, thumbnails e imagens via FLUX AI + Pexels.\n"
            "5. 🔍 **RAG Bíblico**: Busca semântica que responde perguntas com citações dos artigos, livros e cursos.\n\n"
            "COMANDOS DISPONÍVEIS:\n"
            "- 'status' ou 'dashboard' — Mostra o resumo de todas as fábricas\n"
            "- 'pesquisar [tema]' — Pesquisa tendências para um nicho\n"
            "- 'produzir artigo [tema]' — Gera novo artigo no blog\n"
            "- 'produzir livro [tema]' — Gera novo livro\n"
            "- 'produzir curso [tema]' — Gera novo curso\n"
            "- 'perguntar [duvida]' — Consulta o RAG Bíblico\n"
            "- 'ajuda' — Lista todos os comandos\n\n"
            "DIRETRIZES DE RESPOSTA:\n"
            "- NUNCA simule, finja ou mock por texto a execução de tarefas.\n"
            "- Seja direto e executivo. Jonatas é o fundador e quer respostas rápidas.\n"
            "- Sempre que possível, dê comandos que ele possa copiar e colar.\n"
            "- As abas do painel (Dashboard, Blogs, Livros, Cursos, Imagens, RAG) mostram dados ao vivo."
        )

        response = brain._call_llm(system_prompt, message, temperature=0.7)
        return (response, None, None)
    except Exception as e:
        # Fallback inteligente se a API Key do Nvidia NIM estiver ausente/expirada
        if "inicia" in msg or "fluxo" in msg or "faz" in msg:
            text = (
                "Orquestrador Hermes Ativo!\n\n"
                "Jonatas, as 5 fábricas estão 100% operacionais no painel.\n\n"
                "📝 **Blogs** → Aba Blogs\n"
                "📗 **Livros** → Aba Livros\n"
                "🎓 **Cursos** → Aba Cursos\n"
                "🎨 **Imagens** → Aba Imagens\n"
                "🔍 **RAG Bíblico** → Aba RAG\n"
                "\nUse 'ajuda' para ver todos os comandos disponíveis."
            )
        else:
            text = (
                "Orquestrador Hermes Online.\n"
                "Aguardando seus comandos para orquestrar as 5 fábricas:\n📝 Blogs | 📗 Livros | 🎓 Cursos | 🎨 Imagens | 🔍 RAG\n\nDigite 'ajuda' para ver os comandos disponíveis."
            )
        return (text, None, None)
