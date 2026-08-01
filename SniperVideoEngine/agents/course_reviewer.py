"""
Lili Cursos — Agente revisor de qualidade para aulas de curso.
Adaptado do LiLi original (modules/lili.py) para conteudo de cursos.
"""
import re
from agents.llm import query_llm


# Padroes de problema para aulas de curso
BAD_PATTERNS = {
    "exclamacoes_em_massa": {
        "regex": r"!{3,}",
        "severity": "alta",
        "msg": "3+ exclamacoes seguidas",
    },
    "repeticao_frase": {
        "regex": r"(\b\w+\b)(\s+\1){4,}",
        "severity": "alta",
        "msg": "Mesma palavra repetida 5+ vezes",
    },
    "paragrafo_curto": {
        "regex": r"<p>[^<]{1,20}</p>",
        "severity": "baixa",
        "msg": "Paragrafo muito curto (menos de 20 caracteres)",
    },
    "html_garbage": {
        "regex": r"[&$#@]{3,}",
        "severity": "alta",
        "msg": "Caracteres garbage HTML (& $ # @)",
    },
    "encoding_quebrado": {
        "regex": r"\\u[0-9a-f]{4}",
        "severity": "media",
        "msg": "Encoding quebrado (\\uXXXX)",
    },
    "backslash_dominado": {
        "regex": r"(\\n|\\t|\\\\){3,}",
        "severity": "media",
        "msg": "Multiplas barras invertidas",
    },
    "secao_vazia": {
        "regex": r"<(h[1-6]|p|div)[^>]*>\s*</\1>",
        "severity": "media",
        "msg": "Secao HTML vazia",
    },
    "espacos_extras": {
        "regex": r"  {3,}",
        "severity": "baixa",
        "msg": "Espacos extras consecutivos",
    },
    "conteudo_curto": {
        "regex": None,  # Verificacao manual
        "severity": "alta",
        "msg": "Conteudo com menos de 300 palavras",
    },
    "ingles_no_curso": {
        "regex": r"\b(the|and|for|are|but|not|you|all|can|has|her|was|one|our|out)\b",
        "severity": "media",
        "msg": "Possivel conteudo em ingles detectado",
    },
}


def _auto_fix(content: str) -> str:
    """Correcoes automaticas no conteudo."""
    # Remover exclamacoes em massa
    content = re.sub(r"!{3,}", "!", content)
    # Remover encoding quebrado
    content = re.sub(r"\\u[0-9a-f]{4}", "", content)
    # Remover backslashes excessivos
    content = re.sub(r"(\\n|\\t|\\\\){3,}", "\n", content)
    # Remover secoes HTML vazias
    content = re.sub(r"<(h[1-6]|p|div)[^>]*>\s*</\1>", "", content)
    # Remover espacos extras
    content = re.sub(r"  {3,}", " ", content)
    # Limpar tags HTML com atributos garbage
    content = re.sub(r"<[^>]*[&$#@][^>]*>", "", content)
    return content


async def revisar_aula(title: str, content: str, lesson_number: int = 0) -> dict:
    """
    Revisa o conteudo de uma aula de curso.
    Retorna: {score: 0-100, approved: bool, issues: list, summary: str}
    """
    issues = []
    word_count = len(content.split())

    # Verificacao de conteudo curto
    if word_count < 300:
        issues.append({
            "tipo": "conteudo_curto",
            "severity": "alta",
            "msg": f"Conteudo com apenas {word_count} palavras (minimo 300)",
        })

    # Verificacoes por regex
    for tipo, config in BAD_PATTERNS.items():
        if config["regex"] is None:
            continue
        matches = re.findall(config["regex"], content, re.IGNORECASE)
        if matches:
            issues.append({
                "tipo": tipo,
                "severity": config["severity"],
                "msg": config["msg"],
            })

    # Calcular score (comeca em 100)
    score = 100
    for issue in issues:
        if issue["severity"] == "alta":
            score -= 15
        elif issue["severity"] == "media":
            score -= 5
        else:
            score -= 2

    score = max(0, score)
    has_high = any(i["severity"] == "alta" for i in issues)
    approved = score >= 70 and not has_high

    return {
        "score": score,
        "approved": approved,
        "issues": issues,
        "word_count": word_count,
        "summary": f"Score {score}/100 — {'Aprovado' if approved else 'Reprovado'} ({len(issues)} problemas)",
    }


async def revisar_e_corrigir_aula(title: str, content: str,
                                    lesson_number: int = 0,
                                    max_retries: int = 2) -> dict:
    """
    Revisa, corrige automaticamente e reavalia.
    Retorna: {final_content, score, approved, attempts}
    """
    current_content = content
    attempts = 0

    for attempt in range(max_retries + 1):
        attempts += 1
        review = await revisar_aula(title, current_content, lesson_number)

        if review["approved"]:
            return {
                "final_content": current_content,
                "score": review["score"],
                "approved": True,
                "attempts": attempts,
                "issues": review["issues"],
            }

        # Auto-correcao
        current_content = _auto_fix(current_content)

        # Se ainda reprovado e tem tentativas, usar LLM para melhorar
        if attempt < max_retries and not review["approved"]:
            improved = await _llm_improve(title, current_content, review["issues"])
            if improved:
                current_content = improved

    # Ultima revisao
    final_review = await revisar_aula(title, current_content, lesson_number)
    return {
        "final_content": current_content,
        "score": final_review["score"],
        "approved": final_review["approved"],
        "attempts": attempts,
        "issues": final_review["issues"],
    }


async def _llm_improve(title: str, content: str, issues: list) -> str:
    """Usa LLM para melhorar conteudo com problemas."""
    issues_text = "\n".join([f"- {i['msg']}" for i in issues])
    try:
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um revisor de conteudo educacional. "
                "Melhore o conteudo da aula corrigindo os problemas listados. "
                "Mantenha o estilo didatico e o objetivo da aula. "
                "Retorne APENAS o conteudo melhorado em HTML (sem ```html)."
            )},
            {"role": "user", "content": (
                f"Titulo da aula: {title}\n"
                f"Problemas encontrados:\n{issues_text}\n\n"
                f"Conteudo atual:\n{content[:3000]}\n\n"
                f"Corrija os problemas e retorne o conteudo melhorado."
            )},
        ])
        result = resp.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        return result if len(result) > 100 else None
    except Exception:
        return None
