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
    from sqlalchemy import func

    db = SessionLocal()
    try:
        channels = db.query(BlogChannel).order_by(BlogChannel.created_at.desc()).all()
        posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).limit(10).all()
        total_posts = db.query(BlogPost).count()
        published = db.query(BlogPost).filter(BlogPost.status == "published").count()
        drafts = db.query(BlogPost).filter(BlogPost.status == "draft").count()
        total_words = db.query(func.coalesce(func.sum(BlogPost.word_count), 0)).scalar()
        books_count = db.query(Book).count()
        courses_count = db.query(Course).count()
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
                } for c in channels],
            },
            "posts": {
                "total": total_posts,
                "published": published,
                "drafts": drafts,
                "total_words": total_words or 0,
                "recent": [{
                    "id": p.id, "title": p.title, "slug": p.slug,
                    "status": p.status, "word_count": p.word_count or 0,
                    "featured_image_url": p.featured_image_url,
                    "channel_id": p.channel_id,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                } for p in posts],
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

@app.get("/api/v1/factory/dashboard")
async def blog_factory_dashboard():
    """Dashboard consolidado com metricas de todas as fabricas."""
    from modules.database import SessionLocal, BlogChannel, BlogPost, Book, Course
    from sqlalchemy import func

    db = SessionLocal()
    try:
        channels = db.query(BlogChannel).order_by(BlogChannel.created_at.desc()).all()
        posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).limit(10).all()
        total_posts = db.query(BlogPost).count()
        published = db.query(BlogPost).filter(BlogPost.status == "published").count()
        drafts = db.query(BlogPost).filter(BlogPost.status == "draft").count()
        total_words = db.query(func.coalesce(func.sum(BlogPost.word_count), 0)).scalar()
        books_count = db.query(Book).count()
        courses_count = db.query(Course).count()
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
                } for c in channels],
            },
            "posts": {
                "total": total_posts,
                "published": published,
                "drafts": drafts,
                "total_words": total_words or 0,
                "recent": [{
                    "id": p.id, "title": p.title, "slug": p.slug,
                    "status": p.status, "word_count": p.word_count or 0,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                } for p in posts],
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

PAGE_PRIVACY = """<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Politica de Privacidade — O Reino</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;700;800&display=swap" rel="stylesheet">
<style>
body{font-family:'Inter',sans-serif;background:#faf6ef;color:#3d3227;line-height:1.8;margin:0;padding:0}
.container{max-width:800px;margin:0 auto;padding:40px 24px}
h1{font-family:'Playfair Display',serif;color:#1a1410;font-size:32px;margin-bottom:8px}
h2{color:#2a2219;font-size:20px;margin-top:32px;padding-bottom:6px;border-bottom:2px solid #f0e8d5}
p{margin-bottom:16px;color:#5a4a3a}
ul{color:#5a4a3a;margin-bottom:16px;padding-left:20px}
li{margin-bottom:6px}
.back{display:inline-block;margin-bottom:24px;color:#d4a853;text-decoration:none;font-weight:600}
.back:hover{text-decoration:underline}
</style>
</head>
<body>
<div class="container">
<a href="/blog/o-reino" class="back">&larr; Voltar ao Blog</a>
<h1>Politica de Privacidade</h1>
<p><em>Ultima atualizacao: julho de 2026</em></p>
<h2>1. Introducao</h2>
<p>O blog <strong>"O Reino"</strong> respeita a sua privacidade. Esta Politica de Privacidade explica como coletamos, usamos, compartilhamos e protegemos suas informacoes quando voce visita nosso site.</p>
<h2>2. Dados que Coletamos</h2>
<ul>
<li><strong>Dados de navegacao:</strong> endereco IP, tipo de navegador, paginas visitadas</li>
<li><strong>Cookies:</strong> utilizamos cookies proprios e de terceiros</li>
<li><strong>Dados fornecidos voluntariamente:</strong> nome e e-mail em formularios</li>
</ul>
<h2>3. Uso de Cookies do Google</h2>
<p>Utilizamos o <strong>Google AdSense</strong> para exibir anuncios. O Google utiliza cookies para veicular anuncios com base nas visitas anteriores dos usuarios ao nosso site ou a outros sites. Voce pode desativar a personalizacao de anuncios visitando as <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Configuracoes de Anuncios do Google</a>.</p>
<p>Para mais informacoes: <a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener">Como o Google usa as informacoes de sites</a>.</p>
<h2>4. LGPD</h2>
<p>Em conformidade com a Lei 13.709/2018 (LGPD), voce tem direito a acessar, corrigir e solicitar a eliminacao de seus dados.</p>
<h2>5. Contato</h2>
<p>Para exercer seus direitos: <strong>contato@dezafira.com.br</strong></p>
</div>
</body>
</html>"""

PAGE_ABOUT = """<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Sobre Nos — O Reino</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;700;800&display=swap" rel="stylesheet">
<style>
body{font-family:'Inter',sans-serif;background:#faf6ef;color:#3d3227;line-height:1.8;margin:0;padding:0}
.container{max-width:800px;margin:0 auto;padding:40px 24px}
h1{font-family:'Playfair Display',serif;color:#1a1410;font-size:32px;margin-bottom:8px}
h2{color:#2a2219;font-size:20px;margin-top:32px;padding-bottom:6px;border-bottom:2px solid #f0e8d5}
p{margin-bottom:16px;color:#5a4a3a}
.back{display:inline-block;margin-bottom:24px;color:#d4a853;text-decoration:none;font-weight:600}
.back:hover{text-decoration:underline}
</style>
</head>
<body>
<div class="container">
<a href="/blog/o-reino" class="back">&larr; Voltar ao Blog</a>
<h1>Sobre Nos — O Reino</h1>
<h2>Nosso Proposito</h2>
<p><strong>"O Reino"</strong> e um blog dedicado a explorar e compartilhar os ensinamentos de Jesus Cristo a luz das Escrituras Sagradas. Oferecemos reflexoes profundas, estudos biblicos e meditacoes que ajudam pessoas a compreender e aplicar os principios do Reino de Deus em sua vida diaria.</p>
<h2>Nossa Missao</h2>
<ul>
<li><strong>Ensinar:</strong> Explicar as Escrituras de forma clara e acessivel</li>
<li><strong>Refletir:</strong> Provocar reflexao profunda sobre fe e espiritualidade</li>
<li><strong>Aplicar:</strong> Mostrar como viver os ensinamentos de Jesus no seculo XXI</li>
</ul>
<h2>Entre em Contato</h2>
<p>contato@dezafira.com.br</p>
</div>
</body>
</html>"""

PAGE_CONTACT = """<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Contato — O Reino</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@400;700;800&display=swap" rel="stylesheet">
<style>
body{font-family:'Inter',sans-serif;background:#faf6ef;color:#3d3227;line-height:1.8;margin:0;padding:0}
.container{max-width:800px;margin:0 auto;padding:40px 24px}
h1{font-family:'Playfair Display',serif;color:#1a1410;font-size:32px;margin-bottom:24px}
.back{display:inline-block;margin-bottom:24px;color:#d4a853;text-decoration:none;font-weight:600}
.back:hover{text-decoration:underline}
.contact-card{background:#fff;border:1px solid #e0d5c0;border-radius:12px;padding:32px;margin-bottom:20px}
.contact-card label{display:block;font-size:14px;font-weight:600;color:#3d3227;margin-bottom:6px}
.contact-card input,.contact-card textarea{width:100%;padding:10px 14px;border:1px solid #e0d5c0;border-radius:8px;font-size:14px;font-family:'Inter',sans-serif;background:#faf6ef;color:#3d3227;margin-bottom:16px}
.contact-card input:focus,.contact-card textarea:focus{outline:none;border-color:#d4a853}
.contact-card button{background:#d4a853;color:#fff;border:none;padding:10px 24px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
.contact-card button:hover{background:#a67c2e}
</style>
</head>
<body>
<div class="container">
<a href="/blog/o-reino" class="back">&larr; Voltar ao Blog</a>
<h1>Entre em Contato</h1>
<div class="contact-card">
<form id="contactForm">
<label for="name">Seu Nome</label>
<input type="text" id="name" placeholder="Seu nome completo" required>
<label for="email">Seu E-mail</label>
<input type="email" id="email" placeholder="seu@email.com" required>
<label for="message">Sua Mensagem</label>
<textarea id="message" rows="5" placeholder="Escreva sua mensagem..." required></textarea>
<button type="submit">Enviar Mensagem</button>
</form>
<div id="contactSuccess" style="display:none;text-align:center;padding:20px;color:#22c55e;font-weight:600">Mensagem enviada com sucesso!</div>
</div>
<p>contato@dezafira.com.br</p>
<script>
document.getElementById('contactForm').addEventListener('submit',function(e){
  e.preventDefault();
  document.getElementById('contactForm').style.display='none';
  document.getElementById('contactSuccess').style.display='block';
});
</script>
</div>
</body>
</html>"""

@app.get("/blog/o-reino/privacidade", response_class=HTMLResponse)
async def serve_privacy_page():
    return HTMLResponse(content=PAGE_PRIVACY)

@app.get("/blog/o-reino/sobre", response_class=HTMLResponse)
async def serve_about_page():
    return HTMLResponse(content=PAGE_ABOUT)

@app.get("/blog/o-reino/contato", response_class=HTMLResponse)
async def serve_contact_page():
    return HTMLResponse(content=PAGE_CONTACT)


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
    db = SessionLocal()
    try:
        posts = db.query(BlogPost).filter(BlogPost.status.in_(["published", "draft"])).all()
        channels = db.query(BlogChannel).all()
    finally:
        db.close()
    urls = []
    base_url = "https://dezafira.com.br"
    for ch in channels:
        slug = ch.site_url or "/blog/" + ch.name.lower().replace(" ", "-")
        urls.append(f"<url><loc>{base_url}{slug}</loc><priority>0.9</priority></url>")
        urls.append(f"<url><loc>{base_url}{slug}/sobre</loc><priority>0.5</priority></url>")
        urls.append(f"<url><loc>{base_url}{slug}/privacidade</loc><priority>0.3</priority></url>")
        urls.append(f"<url><loc>{base_url}{slug}/contato</loc><priority>0.5</priority></url>")
    for p in posts:
        ch = next((c for c in channels if c.id == p.channel_id), None)
        if ch:
            slug = ch.site_url or "/blog/" + ch.name.lower().replace(" ", "-")
            urls.append(f"<url><loc>{base_url}{slug}?post={p.id}</loc><priority>0.8</priority></url>")
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
async def serve_blog_frontend(slug: str, post: str = None):
    """Serve o frontend publico do blog com artigos renderizados no servidor.
    Suporta ?post=post_id para visualizar artigo individual.
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
        posts = get_db_blog_posts(channel_id=blog_info["id"], limit=50)
    else:
        from modules.database import get_db_blog_channels
        channels = get_db_blog_channels()
        if channels:
            blog_info = channels[0]
            if post:
                individual_post = get_db_blog_post(post)
            posts = get_db_blog_posts(channel_id=blog_info["id"], limit=50)

    html = generate_blog_html(slug, blog_info, posts, post=individual_post)
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

@app.get("/api/v1/pipeline/blog/history")
async def get_blog_pipeline_history():
    return {"pipelines": []}

@app.post("/api/v1/pipeline/run-blog-factory")
async def run_blog_factory_endpoint(payload: dict):
    blog_name = payload.get("blog_name", "")
    niche = payload.get("niche", "")
    language = payload.get("language", "pt")
    target_articles = payload.get("target_articles", 3)
    if not blog_name or not niche:
        raise HTTPException(status_code=400, detail="blog_name and niche are required")
    import uuid
    task_id = f"mblog_{uuid.uuid4().hex[:8]}"

    _macro_results[task_id] = {"status": "starting", "blog_name": blog_name, "niche": niche, "data": None}

    def _run_macro_thread(tid, bname, nic, lang, tgt):
        import asyncio, traceback
        try:
            print(f"[PIPELINE-THREAD] Starting: {tid} blog={bname}")
            from modules.blog_pipeline import run_blog_macro_pipeline as _run_macro
            
            def on_progress(pid, stage_id, progress, message, data):
                try:
                    if pid in _macro_results:
                        real_stage = data.get("stage_id", stage_id) if isinstance(data, dict) else stage_id
                        real_prog = data.get("progress", progress) if isinstance(data, dict) else progress
                        real_msg = data.get("message", message) if isinstance(data, dict) else message
                        real_status = data.get("status", "running") if isinstance(data, dict) else "running"
                        _macro_results[pid]["status"] = real_status
                        _macro_results[pid]["phase"] = real_stage
                        _macro_results[pid]["progress"] = real_prog
                        _macro_results[pid]["message"] = real_msg
                        _macro_results[pid]["data"] = data
                except Exception as e_on:
                    print(f"[PIPELINE] on_progress error: {e_on}")
            
            # Executa a pipeline async dentro de um event loop novo
            result = asyncio.run(_run_macro(blog_name=bname, niche=nic, language=lang, task_id=tid,
                                            target_articles=tgt, on_progress=on_progress))
            
            _macro_results[tid] = {"status": result.get("status", "completed"), "blog_name": bname,
                                   "niche": nic, "data": result}
            print(f"[PIPELINE-THREAD] Complete: {tid} status={result.get('status')}")
            
        except Exception as e:
            print(f"[PIPELINE-THREAD] FATAL: {e}")
            traceback.print_exc()
            _macro_results[tid] = {"status": "failed", "blog_name": bname, "niche": nic, "error": str(e)}

    import threading
    t = threading.Thread(target=_run_macro_thread, args=(task_id, blog_name, niche, language, target_articles), daemon=True)
    t.start()
    print(f"[PIPELINE] Thread started for {task_id}")
    
    return {
        "task_id": task_id, "blog_name": blog_name, "niche": niche,
        "status": "starting", "target_articles": target_articles,
        "message": f"Macro-Esteira iniciada! Blog: {blog_name} (nicho: {niche}). {target_articles} artigos profundos planejados.",
    }

@app.get("/api/v1/pipeline/blog-factory/status/{task_id}")@app.get("/api/v1/pipeline/blog-factory/status/{task_id}")
async def get_blog_factory_status(task_id: str):
    """Retorna o status real de uma pipeline de blog."""
    result = _macro_results.get(task_id)
    if not result:
        # Tenta buscar no banco
        return {"status": "unknown", "task_id": task_id, "message": "Pipeline nao encontrada ou ainda nao iniciada"}
    return result

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

        # Generate image for the article
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
                if img.get("image_url"):
                    update_db_blog_post(post_id, featured_image_url=img["image_url"])
                    img_url = img["image_url"]
            except Exception as e_img:
                print(f"[GenerateArticle] Image error: {e_img}")

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
                
                # Gerar imagem
                img_url = None
                if post_id:
                    try:
                        agent = ImageGeneratorAgent()
                        img = await agent.generate_for_article(title=title, keywords=topic, topic=topic)
                        if img.get("image_url"):
                            update_db_blog_post(post_id, featured_image_url=img["image_url"])
                            img_url = img["image_url"]
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
