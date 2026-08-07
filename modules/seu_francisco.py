"""
👴 Seu Francisco — Supervisor de Produção da Fábrica de Blogs.

Responsabilidades:
  1. Conferir o estoque: articles_generated >= target_articles?
  2. Verificar qualidade junto com a Dona Rosa (Revisor)
  3. Dar sinal verde quando o blog está completo
  4. Impedir criação de novo blog enquanto o atual não estiver 100%
  5. Gerar relatório executivo para a UI
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple


def conferir_estoque(channel_id: str) -> dict:
    """
    Verifica quantos artigos um blog tem vs quantos foram planejados.
    
    Returns:
        {
            "blog_name": str,
            "channel_id": str,
            "articles_existing": int,
            "articles_target": int,
            "articles_remaining": int,
            "percent_complete": float,
            "is_complete": bool,
            "last_pipeline_run": dict or None,
        }
    """
    try:
        from modules.database import (
            get_db_blog_posts, get_db_blog_channel,
            get_db_blog_pipeline_run,
        )

        channel = get_db_blog_channel(channel_id)
        if not channel:
            return {
                "channel_id": channel_id,
                "error": "Canal não encontrado",
                "is_complete": False,
            }

        posts = get_db_blog_posts(channel_id=channel_id, limit=500)
        articles_existing = len(posts)

        # Buscar pipeline runs recentes para saber o target
        from modules.database import SessionLocal, BlogPipelineRun
        db = SessionLocal()
        try:
            run = db.query(BlogPipelineRun).filter(
                BlogPipelineRun.channel_id == channel_id
            ).order_by(BlogPipelineRun.started_at.desc()).first()
            target = run.total_articles_target if run else 35
            run_data = {
                "id": run.id,
                "status": run.status,
                "phase": run.phase,
                "articles_generated": run.articles_generated,
                "started_at": run.started_at.isoformat() if run.started_at else None,
            } if run else None
        finally:
            db.close()

        remaining = max(0, target - articles_existing)
        percent = (articles_existing / max(target, 1)) * 100

        return {
            "blog_name": channel.get("name", "?"),
            "channel_id": channel_id,
            "articles_existing": articles_existing,
            "articles_target": target,
            "articles_remaining": remaining,
            "percent_complete": round(percent, 1),
            "is_complete": articles_existing >= target,
            "last_pipeline_run": run_data,
        }

    except Exception as e:
        return {
            "channel_id": channel_id,
            "error": str(e),
            "is_complete": False,
        }


def autorizar_proximo_artigo(
    channel_id: str,
    articles_generated: int,
    target_articles: int,
    rejected_count: int = 0,
) -> Tuple[bool, str]:
    """
    Decide se o pipeline pode gerar o próximo artigo.
    
    Regras do Seu Francisco:
    - Se já atingiu o target → BLOQUEAR (blog completo)
    - Se tem rejeitados demais (>30%) → BLOQUEAR (qualidade baixa)
    - Se ainda faltam artigos → AUTORIZAR
    
    Returns:
        (autorizado: bool, motivo: str)
    """
    if articles_generated >= target_articles:
        return False, f"🎯 Target de {target_articles} artigos já foi atingido! Blog completo."

    if target_articles > 0 and rejected_count / max(target_articles, 1) > 0.3:
        return False, f"⚠️ Muitos artigos rejeitados ({rejected_count}). Qualidade abaixo do esperado."

    remaining = target_articles - articles_generated
    return True, f"👍 Pode continuar! Faltam {remaining} artigos."


def sinal_verde(channel_id: str, target_articles: int = 35) -> dict:
    """
    Avaliação final: o blog pode ser considerado completo?
    Usado na Fase 5 (Entrega) para decidir se libera o próximo blog.
    
    Returns:
        {
            "liberado": bool,
            "blog_name": str,
            "resumo": str,
            "detalhes": dict,
        }
    """
    estoque = conferir_estoque(channel_id)
    if estoque.get("error"):
        return {
            "liberado": False,
            "resumo": f"Erro ao conferir: {estoque['error']}",
            "detalhes": estoque,
        }

    blog_name = estoque["blog_name"]
    existentes = estoque["articles_existing"]
    target = estoque["articles_target"]

    if estoque["is_complete"]:
        return {
            "liberado": True,
            "blog_name": blog_name,
            "resumo": (
                f"👴 Seu Francisco: \"{blog_name} COMPLETO! "
                f"{existentes} de {target} artigos. Tudo em ordem! "
                f"Pode lançar o próximo blog, rapaziada!\""
            ),
            "detalhes": estoque,
        }
    else:
        restantes = estoque["articles_remaining"]
        return {
            "liberado": False,
            "blog_name": blog_name,
            "resumo": (
                f"👴 Seu Francisco: \"Calma lá! O '{blog_name}' ainda "
                f"tem {existentes} de {target} artigos. "
                f"Faltam {restantes}! Volta pra produção!\""
            ),
            "detalhes": estoque,
        }


def relatorio_executivo(channel_id: str) -> dict:
    """
    Gera um relatório completo para exibir na UI.
    """
    estoque = conferir_estoque(channel_id)

    # Buscar artigos para métricas adicionais
    palavras_totais = 0
    com_imagem = 0
    publicados = 0
    try:
        from modules.database import get_db_blog_posts
        posts = get_db_blog_posts(channel_id=channel_id, limit=500)
        for p in posts:
            palavras_totais += p.get("word_count", 0) or 0
            if p.get("featured_image_url"):
                com_imagem += 1
            if p.get("status") == "published":
                publicados += 1
    except Exception:
        pass

    return {
        **estoque,
        "total_palavras": palavras_totais,
        "artigos_com_imagem": com_imagem,
        "artigos_publicados": publicados,
        "media_palavras": round(palavras_totais / max(estoque.get("articles_existing", 1), 1)),
    }


def listar_blogs_para_supervisionar() -> List[dict]:
    """
    Lista todos os blogs ativos para o Seu Francisco supervisionar.
    Cada um com seu status.
    """
    try:
        from modules.database import get_db_blog_channels
        canais = get_db_blog_channels()
        relatorios = []
        for c in canais:
            if c.get("status") == "active":
                rel = relatorio_executivo(c["id"])
                relatorios.append(rel)
        return relatorios
    except Exception as e:
        return [{"error": str(e)}]
