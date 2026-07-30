# -*- coding: utf-8 -*-
"""
LiLi — Revisora de Qualidade da Fábrica de Blogs.

Validacoes realizadas:
  📝 Conteudo: gibberish, encoding, paragrafos vazios, ingles, repeticao
  🖼️ Imagem: URL presente, imagem carregavel
  📊 Relatorio: score geral, acoes corretivas sugeridas
"""

import re
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# PADROES DE PROBLEMAS
# ═══════════════════════════════════════════════════════════════════════════════

BAD_PATTERNS = {
    "exclamacoes_em_massa": {
        "pattern": r"!{5,}",
        "severity": "alta",
        "message": "Sequencia de 5+ exclamacoes encontrada",
        "fix": "Remover exclamacoes extras e completar a frase.",
    },
    "micro_biologia_gibberish": {
        "pattern": r"micro\s*biologia",
        "severity": "alta",
        "message": "Seção sem sentido ('micro biologia') detectada",
        "fix": "Substituir por conclusao coerente com o tema.",
    },
    "english_words": {
        "pattern": r"\b(everything|nothing|someone|something|anyone)\b",
        "severity": "media",
        "message": "Palavra em ingles encontrada (deveria estar em portugues)",
        "fix": "Traduzir para o portugues.",
    },
    "html_garbage": {
        "pattern": r"<[^>]*?[&$#@].*?>",
        "severity": "alta",
        "message": "HTML mal formado ou com caracteres estranhos",
        "fix": "Corrigir ou remover a tag HTML invalida.",
    },
    "paragrafo_curto": {
        "pattern": r"<p>\s*[A-Za-z]{1,15}\s*</p>",
        "severity": "media",
        "message": "Paragrafo muito curto (menos de 15 caracteres)",
        "fix": "Expandir ou fundir com o paragrafo adjacente.",
    },
    "repeticao_frase": {
        "pattern": r"([A-Z][^.!?]{20,}[.!?])\s*\1\s*",
        "severity": "media",
        "message": "Frase repetida consecutivamente",
        "fix": "Remover a repeticao ou variar o texto.",
    },
    "encoding_quebrado": {
        "pattern": r"\\u00ad|\\x[0-9a-f]{2}|discÃ\xad|disc\\u00ad",
        "severity": "alta",
        "message": "Problema de encoding (acentos quebrados)",
        "fix": "Substituir por caracteres Unicode corretos.",
    },
    "secao_vazia": {
        "pattern": r"<h[234][^>]*>\s*</h[234]>",
        "severity": "alta",
        "message": "Cabecalho de secao vazio (sem conteudo)",
        "fix": "Remover cabecalho vazio ou adicionar conteudo.",
    },
    "colon_sequence_double": {
        "pattern": "[A-Z][a-z]+:\s*\"[A-Z][a-z]+:\s*\"",
        "severity": "alta",
        "message": "Sequencia de dois-pontos aninhados com aspas (garbage do LLM)",
        "fix": "Remover a linha corrompida.",
    },
    "colon_sequence_single": {
        'pattern': r"[A-Z][a-z]+:\s*'[A-Z][a-z]+:\s*'",
        "severity": "alta",
        "message": "Sequencia de dois-pontos aninhados com apostrofo (garbage do LLM)",
        "fix": "Remover a linha corrompida.",
    },

}


def _count_words(html_content: str) -> int:
    """Conta palavras removendo tags HTML."""
    text = re.sub(r"<[^>]+>", "", html_content)
    text = re.sub(r"\s+", " ", text).strip()
    return len(text.split())


def _strip_html(html_content: str) -> str:
    """Remove tags HTML para analise de texto puro."""
    return re.sub(r"<[^>]+>", "", html_content)


def _get_paragraphs(html_content: str) -> List[str]:
    """Extrai paragrafos do HTML."""
    paras = re.findall(r"<p[^>]*>(.*?)</p>", html_content, re.DOTALL)
    return [p.strip() for p in paras if p.strip()]


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDACAO DE CONTEUDO
# ═══════════════════════════════════════════════════════════════════════════════

def revisar_conteudo(
    post_id: str,
    title: str,
    content_html: str,
    keywords: str = "",
) -> dict:
    """
    Revisa a qualidade do conteudo de um artigo.

    Args:
        post_id: ID do post no banco
        title: Titulo do artigo
        content_html: HTML completo do conteudo
        keywords: Keywords do artigo

    Returns:
        Dict com resultado da revisao:
        {
            "post_id": str,
            "title": str,
            "approved": bool,
            "score": int,  # 0-100
            "issues": [{"severity", "message", "fix", "location"}],
            "summary": str,
            "stats": {"word_count", "paragraphs", "avg_paragraph_words"},
        }
    """
    issues = []
    text_content = _strip_html(content_html)
    paragraphs = _get_paragraphs(content_html)
    word_count = _count_words(content_html)

    # --- Verificacoes de qualidade ---
    for issue_key, issue_def in BAD_PATTERNS.items():
        matches = list(re.finditer(issue_def["pattern"], content_html, re.IGNORECASE))
        if matches:
            for m in matches[:3]:  # Max 3 ocorrencias por tipo
                start = max(0, m.start() - 30)
                ctx = content_html[start:m.end() + 30]
                issues.append({
                    "tipo": issue_key,
                    "severity": issue_def["severity"],
                    "message": issue_def["message"],
                    "fix": issue_def["fix"],
                    "localizacao": ctx[:80],
                })

    # --- Estatisticas dos paragrafos ---
    if paragraphs:
        para_word_counts = [_count_words(f"<p>{p}</p>") for p in paragraphs]
        avg_words = sum(para_word_counts) / len(para_word_counts)
        short_paras = [wc for wc in para_word_counts if wc < 5]
        for i, wc in enumerate(para_word_counts):
            if wc < 5:
                preview = paragraphs[i][:40]
                issues.append({
                    "tipo": "paragrafo_curto",
                    "severity": "media",
                    "message": f"Paragrafo #{i+1} tem apenas {wc} palavra(s): '{preview}'",
                    "fix": "Expandir ou fundir com paragrafo adjacente.",
                    "localizacao": preview,
                })
    else:
        avg_words = 0
        issues.append({
            "tipo": "sem_paragrafos",
            "severity": "alta",
            "message": "Nenhum paragrafo (<p>) encontrado no HTML",
            "fix": "Envolver o conteudo em tags <p>.",
            "localizacao": "topo do conteudo",
        })

    # --- Palavras minimas ---
    if word_count < 300:
        issues.append({
            "tipo": "poucas_palavras",
            "severity": "alta",
            "message": f"Apenas {word_count} palavras. Minimo recomendado: 800",
            "fix": "Regenerar artigo com mais profundidade.",
            "localizacao": "artigo completo",
        })

    # --- Score ---
    # Calcula score baseado em severidade dos issues
    severity_weights = {"alta": 15, "media": 5, "baixa": 2}
    deductions = sum(
        severity_weights.get(i["severity"], 5)
        for i in issues
    )
    score = max(0, min(100, 100 - deductions))

    # Aprovado se score >= 70 e nenhum issue de severidade 'alta'
    high_severity = [i for i in issues if i["severity"] == "alta"]
    approved = score >= 70 and len(high_severity) == 0

    # Resumo
    n_issues = len(issues)
    n_high = len(high_severity)
    if approved:
        summary = f"Artigo aprovado! Score {score}/100, {n_issues} issue(s) ({n_high} alta)"
    else:
        summary = f"Artigo REPROVADO! Score {score}/100, {n_issues} issue(s) ({n_high} alta)"
        if high_severity:
            summary += f". Correcoes necessarias: {', '.join(i['tipo'] for i in high_severity[:3])}"

    return {
        "post_id": post_id,
        "title": title,
        "approved": approved,
        "score": score,
        "issues": issues,
        "summary": summary,
        "stats": {
            "word_count": word_count,
            "paragraphs": len(paragraphs),
            "avg_paragraph_words": round(avg_words, 1),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDACAO DE IMAGEM
# ═══════════════════════════════════════════════════════════════════════════════

async def verificar_imagem(featured_image_url: Optional[str]) -> dict:
    """
    Verifica se a imagem de destaque existe e e acessivel.

    Args:
        featured_image_url: URL da imagem ou None

    Returns:
        {"ok": bool, "message": str}
    """
    if not featured_image_url or featured_image_url.strip() == "":
        return {"ok": False, "message": "Nenhuma imagem de destaque configurada"}

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(featured_image_url, headers={"Range": "bytes=0-1024"})
            if resp.status_code < 400:
                content_type = resp.headers.get("content-type", "")
                if "image" in content_type:
                    return {"ok": True, "message": "Imagem OK"}
                else:
                    return {"ok": False, "message": f"URL nao retorna imagem: {content_type}"}
            else:
                return {"ok": False, "message": f"HTTP {resp.status_code} ao acessar imagem"}
    except Exception as e:
        return {"ok": False, "message": f"Erro ao verificar imagem: {str(e)[:60]}"}


# ═══════════════════════════════════════════════════════════════════════════════
# REVISAO COMPLETA DO ARTIGO
# ═══════════════════════════════════════════════════════════════════════════════

async def revisar_artigo(post: dict) -> dict:
    """
    Revisao completa de um artigo: conteudo + imagem.

    Args:
        post: Dict do artigo (como retornado por get_db_blog_post)

    Returns:
        Dict com resultado completo da revisao por LiLi
    """
    post_id = post.get("id", "unknown")
    title = post.get("title", "Sem titulo")
    content = post.get("content", "")
    keywords = post.get("keywords", "")
    image_url = post.get("featured_image_url")

    # Revisar conteudo
    content_review = revisar_conteudo(post_id, title, content, keywords)

    # Verificar imagem
    image_check = await verificar_imagem(image_url)

    return {
        "post_id": post_id,
        "title": title,
        "content_review": content_review,
        "image_check": image_check,
        "approved": content_review["approved"] and image_check["ok"],
        "overall_score": content_review["score"] if image_check["ok"] else max(0, content_review["score"] - 10),
        "reviewed_at": datetime.utcnow().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REVISAO EM MASSA (todos os artigos de um blog)
# ═══════════════════════════════════════════════════════════════════════════════

async def revisar_blog(channel_id: str) -> dict:
    """
    Revisa todos os artigos de um blog.

    Args:
        channel_id: ID do canal do blog

    Returns:
        Dict com resumo da revisao do blog
    """
    from modules.database import get_db_blog_posts

    from modules.database import get_db_blog_post
    
    # Get all post IDs for the channel
    posts_meta = get_db_blog_posts(channel_id=channel_id, limit=100)
    if not posts_meta:
        return {
            "channel_id": channel_id,
            "status": "erro",
            "message": "Nenhum artigo encontrado para revisao",
            "total": 0,
        }

    results = []
    approved_count = 0
    total_score = 0
    issues_by_type = {}

    # Fetch full content for each post (get_db_blog_posts doesnt include content field)
    for pm in posts_meta:
        post = get_db_blog_post(pm["id"])
        if not post:
            continue
        review = await revisar_artigo(post)
        results.append(review)
        if review["approved"]:
            approved_count += 1
        total_score += review["overall_score"]

        # Contar issues
        for issue in review["content_review"]["issues"]:
            t = issue["tipo"]
            issues_by_type[t] = issues_by_type.get(t, 0) + 1

    avg_score = round(total_score / len(posts_meta), 1) if posts_meta else 0

    return {
        "channel_id": channel_id,
        "status": "completo",
        "message": f"{approved_count}/{len(posts_meta)} artigos aprovados. Score medio: {avg_score}/100",
        "total": len(posts_meta),
        "approved": approved_count,
        "avg_score": avg_score,
        "issues_by_type": issues_by_type,
        "results": results,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CORRECAO AUTOMATICA DE ISSUES COMUNS
# ═══════════════════════════════════════════════════════════════════════════════

def corrigir_conteudo_automatico(content_html: str) -> str:
    """
    Corrige problemas comuns de conteudo automaticamente.

    Aplica correcoes simples sem precisar de LLM:
    - Remove exclamacoes em massa
    - Remove 'micro biologia' e similares
    - Corrige encoding basico
    - Remove tags vazias

    Args:
        content_html: HTML do artigo

    Returns:
        HTML corrigido
    """
    # 1. Remover exclamacoes em massa (5+ seguidas)
    content_html = re.sub(r"\.!{3,}", ".", content_html)
    content_html = re.sub(r"!{3,}", "", content_html)

    # 2. Remover secoes de micro biologia
    content_html = re.sub(
        r"[^.]*?micro[-\s]?biologia[^.]*\.",
        "A multiplicacao dos paes e peixes nos ensina que Deus e nosso provedor fiel.",
        content_html,
        flags=re.IGNORECASE,
    )

    # 3. Corrigir 'everything' para 'tudo'
    translations = {
        r"\beverything\b": "tudo",
        r"\bnothing\b": "nada",
        r"\bsomeone\b": "alguem",
        r"\bsomething\b": "algo",
        r"\banyone\b": "ninguem",
        r"\banybody\b": "ninguem",
        r"\beverybody\b": "todos",
    }
    for eng_pattern, pt_word in translations.items():
        content_html = re.sub(eng_pattern, pt_word, content_html, flags=re.IGNORECASE)

    # 4. Corrigir 'EJesus' -> 'E Jesus'
    content_html = content_html.replace('"EJesus', '"E Jesus')
    content_html = content_html.replace("'EJesus", "'E Jesus")
    content_html = content_html.replace(">EJesus", ">E Jesus")

    # 5. Remover tags de cabecalho vazias
    content_html = re.sub(r"<h[234][^>]*>\s*</h[234]>", "", content_html, flags=re.IGNORECASE)

    # 6. Remover paragrafos vazios
    content_html = re.sub(r"<p>\s*</p>", "", content_html, flags=re.IGNORECASE)

    # 7. Encoding fixes
    content_html = content_html.replace("\\u00ad", "")
    content_html = content_html.replace("disc\\u00adpulos", "discipulos")
    content_html = re.sub(r"disc[\s]*[Ã\xad][\s]*pulos", "discipulos", content_html)

    return content_html


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCAO DE INTEGRACAO COM A PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

async def lili_review_after_generation(post_id: str) -> dict:
    """
    Chamada apos gerar cada artigo na pipeline.
    Revisa e corrige automaticamente se necessario.

    Args:
        post_id: ID do post recem-gerado

    Returns:
        Dict com resultado da revisao
    """
    from modules.database import get_db_blog_post, update_db_blog_post

    # Buscar o artigo
    post = get_db_blog_post(post_id)
    if not post:
        return {
            "post_id": post_id,
            "status": "erro",
            "message": "Post nao encontrado",
        }

    content = post.get("content", "")

    # 1. Revisar
    review = await revisar_artigo(post)

    # 2. Se tiver issues de conteudo, tentar correcao automatica
    if not review["content_review"]["approved"]:
        corrected = corrigir_conteudo_automatico(content)
        if corrected != content:
            # Salvar versao corrigida
            update_db_blog_post(post_id, content=corrected)

            # Re-revisar
            post["content"] = corrected
            review = await revisar_artigo(post)
            review["auto_corrected"] = True
        else:
            review["auto_corrected"] = False
    else:
        review["auto_corrected"] = False

    # 3. Se nao tiver imagem, marcar para geracao posterior
    if not post.get("featured_image_url"):
        review["needs_image"] = True
    else:
        review["needs_image"] = False

    return review


async def lili_review_all_pending(channel_id: str) -> dict:
    """
    Revisa todos os artigos pendentes de um blog.
    Usado na fase de Entrega.

    Args:
        channel_id: ID do canal

    Returns:
        Resumo da revisao
    """
    return await revisar_blog(channel_id)
