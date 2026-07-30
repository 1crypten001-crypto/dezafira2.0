"""
📅 Seu Zé — Scheduler de Publicação da Fábrica de Blogs.

Responsabilidades:
  1. Publicar 1 artigo/dia às 08:00 para cada blog ativo
  2. Manter fila de artigos publicados vs pendentes
  3. Notificar quando o estoque de artigos está acabando
  4. Integrar com o Seu Francisco — se o blog não está completo, não publica
"""

import asyncio
import json
import os
from datetime import datetime, time, timedelta
from typing import Optional, List, Dict, Any
import threading

# ─── Thread safety ────────────────────────────────────────────────────────
_jobs_lock = threading.Lock()

# Jobs ativos: {job_id: {"channel_id": ..., "hour": 8, "minute": 0, "active": bool}}
_active_jobs: Dict[str, dict] = {}
_scheduler_thread: Optional[threading.Thread] = None
_scheduler_running = False


def agendar_publicacao(
    channel_id: str,
    blog_name: str,
    hour: int = 8,
    minute: int = 0,
) -> dict:
    """
    Agenda a publicação diária de 1 artigo para um blog.
    O Seu Zé vai publicar 1 artigo por dia no horário definido.

    Returns:
        {
            "job_id": str,
            "channel_id": str,
            "blog_name": str,
            "schedule": f"{hour:02d}:{minute:02d}",
            "status": "agendado" | "ja_existia",
        }
    """
    global _active_jobs
    job_id = f"ze_{channel_id}"
    with _jobs_lock:
        if job_id in _active_jobs:
            return {
                "job_id": job_id,
                "channel_id": channel_id,
                "blog_name": blog_name,
                "schedule": f"{hour:02d}:{minute:02d}",
                "status": "ja_existia",
            }

        _active_jobs[job_id] = {
            "channel_id": channel_id,
            "blog_name": blog_name,
            "hour": hour,
            "minute": minute,
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
            "articles_published": 0,
            "last_published_at": None,
        }

    _ensure_scheduler_running()

    return {
        "job_id": job_id,
        "channel_id": channel_id,
        "blog_name": blog_name,
        "schedule": f"{hour:02d}:{minute:02d}",
        "status": "agendado",
    }


def _ensure_scheduler_running():
    """Garante que o loop do Seu Zé está rodando em background."""
    global _scheduler_thread, _scheduler_running
    if _scheduler_running:
        return
    _scheduler_running = True
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()
    print("[Seu Ze] Scheduler iniciado! Verificando a cada 60 segundos...")


def _scheduler_loop():
    """Loop principal do Seu Zé — verifica a cada 60s se é hora de publicar."""
    while _scheduler_running:
        try:
            now = datetime.now()

            with _jobs_lock:
                jobs_snapshot = list(_active_jobs.items())
            for job_id, job in jobs_snapshot:
                if not job.get("active"):
                    continue

                # Verifica se está na hora certa
                if now.hour == job["hour"] and now.minute == job["minute"]:
                    # Verifica se já publicou hoje
                    last = job.get("last_published_at")
                    if last:
                        last_dt = datetime.fromisoformat(last)
                        if last_dt.date() == now.date():
                            continue  # Já publicou hoje

                    # Tenta publicar
                    try:
                        result = _publicar_um_artigo(job["channel_id"], job["blog_name"])
                        if result.get("success"):
                            with _jobs_lock:
                                # Re-obter referência atualizada do job sob lock
                                current_job = _active_jobs.get(job_id)
                                if current_job:
                                    current_job["articles_published"] = current_job.get("articles_published", 0) + 1
                                    current_job["last_published_at"] = now.isoformat()
                            print(f"[Seu Ze] Publicado: {result.get('title')} em {job['blog_name']}")
                        elif result.get("estoque_vazio"):
                            print(f"[Seu Ze] Blog {job['blog_name']} sem artigos pendentes. Notificando...")
                            _notificar_estoque_vazio(job["channel_id"], job["blog_name"])
                    except Exception as e:
                        print(f"[Seu Ze] Erro ao publicar para {job['blog_name']}: {e}")

        except Exception as e:
            print(f"[Seu Ze] Erro no loop: {e}")

        # Dorme 60 segundos
        import time as _time
        _time.sleep(60)


def _publicar_um_artigo(channel_id: str, blog_name: str) -> dict:
    """
    Publica o artigo mais antigo que ainda está como 'draft' no banco.
    Retorna o resultado da publicação.
    """
    try:
        from modules.database import SessionLocal, BlogPost

        db = SessionLocal()
        try:
            # Busca o draft mais antigo
            post = db.query(BlogPost).filter(
                BlogPost.channel_id == channel_id,
                BlogPost.status == "draft",
            ).order_by(BlogPost.created_at.asc()).first()

            if not post:
                return {
                    "success": False,
                    "estoque_vazio": True,
                    "message": f"Nenhum artigo draft encontrado para {blog_name}",
                }

            # Publica
            post.status = "published"
            post.published_at = datetime.utcnow()
            db.commit()

            return {
                "success": True,
                "post_id": post.id,
                "title": post.title,
                "word_count": post.word_count,
                "message": f"'{post.title}' publicado com sucesso!",
            }
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "error": str(e)}


def _notificar_estoque_vazio(channel_id: str, blog_name: str):
    """
    Notifica que o estoque de artigos acabou.
    Poderia enviar email, notificação na UI, disparar pipeline, etc.
    """
    print(f"[Seu Ze] ATENCAO: Blog '{blog_name}' esta sem artigos para publicar!")
    # TODO: Integrar com notificações do sistema
    # TODO: Disparar pipeline de reposição automaticamente


def status_publicacao(channel_id: str = None) -> List[dict]:
    """
    Retorna o status de todos os jobs de publicação.
    """
    with _jobs_lock:
        if channel_id:
            job_id = f"ze_{channel_id}"
            job = _active_jobs.get(job_id)
            if not job:
                return []
            return [_job_to_dict(job_id, job)]
        return [_job_to_dict(jid, j) for jid, j in _active_jobs.items()]


def _job_to_dict(job_id: str, job: dict) -> dict:
    return {
        "job_id": job_id,
        "channel_id": job["channel_id"],
        "blog_name": job["blog_name"],
        "schedule": f"{job['hour']:02d}:{job['minute']:02d}",
        "active": job["active"],
        "articles_published": job.get("articles_published", 0),
        "last_published_at": job.get("last_published_at"),
    }


def resumo_geral() -> dict:
    """
    Resumo geral do Seu Zé para exibir na UI.
    """
    with _jobs_lock:
        if not _active_jobs:
            return {
                "status": "ocioso",
                "blogs_agendados": 0,
                "total_publicados": 0,
                "mensagem": "📅 Seu Zé: \"Nada agendado ainda. Me chama quando tiver blog pronto!\"",
            }

        total_pub = sum(j.get("articles_published", 0) for j in _active_jobs.values())
        return {
            "status": "ativo",
            "blogs_agendados": len(_active_jobs),
            "total_publicados": total_pub,
            "jobs": [_job_to_dict(jid, j) for jid, j in _active_jobs.items()],
            "mensagem": f"📅 Seu Zé: \"{total_pub} artigos publicados! Todo dia às 08:00, igual pão quente.\"",
        }
