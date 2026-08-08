"""
Scheduler — Motor de Automação para a Fábrica de Blogs.

Agenda tarefas automáticas:
  - Diária: pesquisar keywords → gerar artigo → publicar → indexar
  - Semanal: relatório de desempenho
  - Configurável por canal de blog

Usa APScheduler integrado com FastAPI (lifespan).

Uso:
    scheduler = BlogScheduler()
    scheduler.start()
    scheduler.add_daily_job("teologia", channel_id="blg_abc123")
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable

logger = logging.getLogger("scheduler")

# Callbacks injetados pelo server.py
_callbacks = {
    "produce_article": None,   # async (topic, channel_id) -> dict
    "publish_article": None,   # async (post_id) -> dict
    "keyword_research": None,  # async (seed) -> dict
    "notify": None,            # async (text) -> None
}

def set_callback(name: str, cb: Callable):
    """Registra um callback para o scheduler usar."""
    _callbacks[name] = cb


# ═══════════════════════════════════════════════════════════════════════════════
# TAREFAS ASSÍNCRONAS
# ═══════════════════════════════════════════════════════════════════════════════

async def _run_daily_production(seed: str, channel_id: str = "default",
                                 publish: bool = True, index: bool = False) -> dict:
    """
    Pipeline completa agendada:
    1. Keyword research (se seed for nicho, não keyword específica)
    2. Gera artigo
    3. Publica (opcional)
    4. Indexa no Google (opcional)
    """
    from datetime import datetime
    start = datetime.utcnow()
    results = {
        "seed": seed,
        "channel_id": channel_id,
        "started_at": start.isoformat(),
        "steps": [],
        "success": False,
        "error": None,
    }

    try:
        # 1. Keyword Research (se não for uma keyword específica)
        keyword_string = seed
        if _callbacks.get("keyword_research"):
            kw_result = await _callbacks["keyword_research"](seed)
            if kw_result and kw_result.get("success"):
                keyword_string = kw_result.get("keyword_string", seed)
                results["steps"].append({
                    "step": "keyword_research",
                    "status": "ok",
                    "keywords_found": kw_result.get("total_found", 0),
                    "easy_count": kw_result.get("easy_count", 0),
                })
            else:
                results["steps"].append({
                    "step": "keyword_research",
                    "status": "fallback",
                    "note": "Usando seed como keyword",
                })
        else:
            results["steps"].append({
                "step": "keyword_research",
                "status": "skipped",
                "note": "Callback não registrado",
            })

        # 2. Gerar artigo
        if not _callbacks.get("produce_article"):
            raise RuntimeError("Callback produce_article não registrado")

        article = await _callbacks["produce_article"](
            topic=keyword_string or seed,
            channel_id=channel_id,
        )

        if not article or not article.get("success"):
            raise RuntimeError(f"Falha ao gerar artigo: {article.get('error', 'erro desconhecido')}")

        post_id = article["post_id"]
        results["post_id"] = post_id
        results["title"] = article.get("title", seed)
        results["steps"].append({
            "step": "generate_article",
            "status": "ok",
            "post_id": post_id,
            "title": article.get("title", ""),
            "word_count": article.get("word_count", 0),
        })

        # 3. Publicar (opcional)
        if publish and _callbacks.get("publish_article"):
            pub_result = await _callbacks["publish_article"](post_id)
            if pub_result and pub_result.get("ok"):
                results["steps"].append({
                    "step": "publish",
                    "status": "ok",
                    "platform_url": pub_result.get("platform_url", ""),
                })
                results["published_url"] = pub_result.get("platform_url", "")
            else:
                results["steps"].append({
                    "step": "publish",
                    "status": "failed",
                    "error": pub_result.get("error", "erro desconhecido") if pub_result else "sem retorno",
                })

        # 4. Indexar no Google (opcional)
        if index and results.get("published_url") and _callbacks.get("notify"):
            try:
                from modules.google_indexer import notify_url_update
                index_result = await notify_url_update(results["published_url"])
                results["steps"].append({
                    "step": "google_index",
                    "status": "ok" if index_result.get("ok") else "failed",
                })
            except Exception as e:
                results["steps"].append({
                    "step": "google_index",
                    "status": "failed",
                    "error": str(e),
                })

        results["success"] = True
        results["duration_seconds"] = (datetime.utcnow() - start).total_seconds()

    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        logger.error(f"[Scheduler] Erro na produção agendada: {e}")

    # Notificar
    if _callbacks.get("notify"):
        status_icon = "✅" if results["success"] else "❌"
        title = results.get("title", seed)[:50]
        msg = f"{status_icon} *Scheduler:* Artigo '{title}'"
        if results["success"]:
            msg += f"\n📝 ID: {results.get('post_id', '?')}"
            if results.get("published_url"):
                msg += f"\n🔗 {results['published_url']}"
        else:
            msg += f"\n⚠️ Erro: {results.get('error', '?')[:100]}"
        try:
            if asyncio.iscoroutinefunction(_callbacks["notify"]):
                await _callbacks["notify"](msg)
        except Exception:
            pass

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# AGENDADOR (APScheduler)
# ═══════════════════════════════════════════════════════════════════════════════

_scheduler = None
_scheduled_jobs = {}  # {job_id: job_config}


def get_scheduler():
    """Retorna instância do APScheduler (lazy)."""
    global _scheduler
    if _scheduler is None:
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            _scheduler = AsyncIOScheduler()
            logger.info("[Scheduler] AsyncIOScheduler inicializado")
        except ImportError:
            logger.warning("[Scheduler] APScheduler não instalado. Use: pip install apscheduler")
            return None
    return _scheduler


async def run_scheduled_job(job_config: dict):
    """Executa uma tarefa agendada."""
    seed = job_config.get("seed", "")
    channel_id = job_config.get("channel_id", "default")
    publish = job_config.get("publish", True)
    index = job_config.get("index", False)

    logger.info(f"[Scheduler] Executando job: seed='{seed}', channel={channel_id}")
    result = await _run_daily_production(
        seed=seed,
        channel_id=channel_id,
        publish=publish,
        index=index,
    )
    logger.info(f"[Scheduler] Job concluído: success={result['success']}")
    return result


def add_daily_job(job_id: str, seed: str, channel_id: str = "default",
                  hour: int = 8, minute: int = 0,
                  publish: bool = True, index: bool = False) -> dict:
    """
    Agenda produção diária.
    Retorna config do job.
    """
    sched = get_scheduler()
    if sched is None:
        return {"success": False, "error": "APScheduler não instalado"}

    # Remove job existente com mesmo ID
    if job_id in _scheduled_jobs:
        try:
            sched.remove_job(job_id)
        except Exception:
            pass

    job_config = {
        "id": job_id,
        "seed": seed,
        "channel_id": channel_id,
        "publish": publish,
        "index": index,
        "hour": hour,
        "minute": minute,
    }

    sched.add_job(
        run_scheduled_job,
        trigger="cron",
        hour=hour,
        minute=minute,
        args=[job_config],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=3600,  # 1h de tolerância
    )

    _scheduled_jobs[job_id] = job_config
    logger.info(f"[Scheduler] Job '{job_id}' agendado: {seed} diário às {hour:02d}:{minute:02d}")

    return {
        "success": True,
        "job_id": job_id,
        "seed": seed,
        "channel_id": channel_id,
        "schedule": f"{hour:02d}:{minute:02d} diário",
        "publish": publish,
        "index": index,
    }


def remove_job(job_id: str) -> bool:
    """Remove um job agendado."""
    sched = get_scheduler()
    if sched is None:
        return False
    try:
        sched.remove_job(job_id)
        _scheduled_jobs.pop(job_id, None)
        logger.info(f"[Scheduler] Job '{job_id}' removido")
        return True
    except Exception as e:
        logger.error(f"[Scheduler] Erro ao remover job '{job_id}': {e}")
        return False


def list_jobs() -> list:
    """Lista todos os jobs agendados."""
    return list(_scheduled_jobs.values())


def start():
    """Inicia o scheduler."""
    sched = get_scheduler()
    if sched and not sched.running:
        sched.start()
        logger.info("[Scheduler] Iniciado!")
        return True
    return False


def stop():
    """Para o scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Parado.")
    _scheduler = None


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO DISPARO ÚNICO (executa agora, não agendado)
# ═══════════════════════════════════════════════════════════════════════════════

async def run_once(seed: str, channel_id: str = "default",
                   publish: bool = True, index: bool = False) -> dict:
    """Executa a pipeline uma única vez, imediatamente."""
    return await _run_daily_production(
        seed=seed,
        channel_id=channel_id,
        publish=publish,
        index=index,
    )
