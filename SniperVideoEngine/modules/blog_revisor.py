"""
Blog Revisor — Agente de Qualidade e Prevenção de Duplicatas.

Responsabilidades:
  1. Verificar similaridade entre títulos/tópicos antes de gerar um artigo novo
  2. Sugerir tópicos alternativos se o atual já foi coberto
  3. Validar qualidade mínima do artigo gerado (word count, estrutura)
  4. Manter um registro dos tópicos já usados por canal (evitar repetição entre execuções)
"""

import re
import json
from typing import Optional, List, Dict, Any, Tuple


def _normalize_text(text: str) -> str:
    """Normaliza texto para comparação: lower, remove acentos, pontuação."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _word_overlap(a: str, b: str) -> float:
    """Similaridade por sobreposição de palavras (Jaccard). 0.0 a 1.0."""
    words_a = set(_normalize_text(a).split())
    words_b = set(_normalize_text(b).split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / max(len(union), 1)


def _used_topics_for_channel(channel_id: str) -> List[str]:
    """
    Busca todos os títulos e tópicos já publicados para um canal.
    """
    try:
        from modules.database import get_db_blog_posts
        posts = get_db_blog_posts(channel_id=channel_id, limit=200)
        topics = []
        for p in posts:
            if p.get("title"):
                topics.append(p["title"])
            if p.get("topic"):
                topics.append(p["topic"])
        return topics
    except Exception:
        return []


def find_most_similar(candidate: str, existing_list: List[str], threshold: float = 0.65) -> Tuple[Optional[str], float]:
    """
    Encontra o texto mais similar ao candidate na lista existente.
    Retorna (texto_mais_similar, score).
    Se nenhum passar do threshold, retorna (None, 0.0).
    """
    best_score = 0.0
    best_match = None
    for existing in existing_list:
        score = _word_overlap(candidate, existing)
        if score > best_score:
            best_score = score
            best_match = existing
    if best_score >= threshold:
        return best_match, best_score
    return None, 0.0


def is_duplicate_topic(topic: str, channel_id: str, threshold: float = 0.70) -> Tuple[bool, Optional[str], float]:
    """
    Verifica se um tópico é duplicata em relação aos posts existentes do canal.

    Returns:
        (is_dupe, similar_title, score)
    """
    used = _used_topics_for_channel(channel_id)
    if not used:
        return False, None, 0.0

    match, score = find_most_similar(topic, used, threshold=threshold)
    if match:
        return True, match, score
    return False, None, 0.0


def suggest_alternative_topic(
    original_topic: str,
    channel_id: str,
    topics_pool: List[str],
    threshold: float = 0.65,
) -> str:
    """
    Sugere um tópico alternativo do pool que NÃO seja similar a nada já usado.
    Se todos do pool forem similares, retorna o original com um prefixo de variação.
    """
    used = _used_topics_for_channel(channel_id)
    used_set = set(used)

    # Tentar encontrar um tópico do pool que não seja similar
    for topic in topics_pool:
        if topic.lower().strip() in used_set:
            continue
        is_dupe, _, _ = is_duplicate_topic(topic, channel_id, threshold=threshold)
        if not is_dupe:
            return topic

    # Se todos falharam, retorna variação do original
    variations = [
        f"{original_topic} — uma análise profunda",
        f"Tudo sobre {original_topic.lower()}",
        f"{original_topic}: guia completo",
        f"Entendendo {original_topic.lower()}",
    ]
    for v in variations:
        is_dupe, _, _ = is_duplicate_topic(v, channel_id, threshold=threshold)
        if not is_dupe:
            return v

    return original_topic


def validate_article_quality(article: dict, min_words: int = 800) -> Tuple[bool, List[str]]:
    """
    Valida a qualidade de um artigo gerado.
    Retorna (is_valid, [lista_de_erros]).
    """
    errors = []
    word_count = article.get("word_count", 0)
    title = article.get("title", "")
    content = article.get("content_html") or article.get("content", "")
    excerpt = article.get("excerpt", "")

    if word_count < min_words:
        errors.append(f"Word count insuficiente: {word_count} (mínimo: {min_words})")

    if not title or len(title) < 10:
        errors.append("Título muito curto ou ausente")

    if not content or len(content.strip()) < 200:
        errors.append("Conteúdo muito curto ou ausente")

    if not excerpt or len(excerpt) < 20:
        errors.append("Excerpt muito curto ou ausente")

    # Verificar se o conteúdo tem tags HTML mínimas (h2, p)
    if content:
        has_heading = bool(re.search(r'<h[2-6]', content))
        has_paragraph = bool(re.search(r'<p>', content))
        if not has_heading:
            errors.append("Conteúdo sem headings (<h2>-<h6>)")
        if not has_paragraph:
            errors.append("Conteúdo sem parágrafos (<p>)")

    return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════════
# API de alto nível para uso na pipeline
# ═══════════════════════════════════════════════════════════════════════════════

async def review_topic_before_generation(
    topic: str,
    channel_id: str,
    existing_topics: List[str] = None,
    topics_pool: List[str] = None,
    threshold: float = 0.70,
) -> dict:
    """
    Função principal: revisa um tópico ANTES de gerar o artigo.

    1. Checa se o tópico é duplicata de algo já existente
    2. Se for, sugere alternativa do pool (se disponível)
    3. Se não houver alternativa, retorna o original com aviso

    Returns:
        {
            "approved": bool,       # True se pode gerar, False se bloqueou
            "topic": str,           # Tópico aprovado (pode ser alternativa)
            "original_topic": str,  # Tópico original solicitado
            "reason": str,          # Motivo da decisão
            "similar_to": str|null, # Título similar encontrado
            "similarity_score": float,
        }
    """
    is_dupe, similar_title, score = is_duplicate_topic(topic, channel_id, threshold=threshold)

    if not is_dupe:
        return {
            "approved": True,
            "topic": topic,
            "original_topic": topic,
            "reason": "Tópico aprovado — sem duplicatas encontradas",
            "similar_to": None,
            "similarity_score": 0.0,
        }

    # Se for duplicata e temos pool, tentar alternativa
    if topics_pool:
        alternative = suggest_alternative_topic(topic, channel_id, topics_pool, threshold=threshold)
        if alternative != topic:
            # Verificar se a alternativa também não é duplicata
            alt_dupe, alt_similar, alt_score = is_duplicate_topic(alternative, channel_id, threshold=threshold)
            if not alt_dupe:
                return {
                    "approved": True,
                    "topic": alternative,
                    "original_topic": topic,
                    "reason": f"Tópico original similar a '{similar_title}' ({score:.0%}). Alternativa sugerida: '{alternative}'",
                    "similar_to": similar_title,
                    "similarity_score": score,
                }

    # Bloquear — não tem alternativa disponível
    return {
        "approved": False,
        "topic": topic,
        "original_topic": topic,
        "reason": f"Tópico '{topic}' é muito similar a '{similar_title}' ({score:.0%}) e nenhuma alternativa viável foi encontrada",
        "similar_to": similar_title,
        "similarity_score": score,
    }


async def review_article_after_generation(article: dict, min_words: int = 800) -> dict:
    """
    Revisa um artigo DEPOIS de gerado.
    Valida qualidade e estrutura.

    Returns:
        {
            "approved": bool,
            "errors": [str],
            "warnings": [str],
        }
    """
    is_valid, errors = validate_article_quality(article, min_words=min_words)
    return {
        "approved": is_valid,
        "errors": errors,
        "warnings": [],
    }
