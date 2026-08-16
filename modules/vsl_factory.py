"""
VSL Factory — geração de roteiro (script) e headlines A/B/C de uma
Video Sales Letter, com fallback determinístico quando a LLM falha.

Usado por:
- `server.py` — POST /api/v1/vsl (fábrica de VSL)
- `modules/blueprint_engine.py` — estágio opcional de VSL do Blueprint
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


_SYSTEM_PROMPT = (
    "Você é um redator publicitário de elite e copywriter especialista em VSL "
    "(Video Sales Letter). Sua missão é gerar um roteiro de vendas completo e "
    "três variações de títulos (headlines A, B e C) de altíssima conversão. "
    "Responda APENAS com JSON válido, sem markdown, com estas chaves exatas: "
    '{"script": string (roteiro completo em parágrafos, com abertura, dor, '
    'promessa, prova, objeções, oferta, urgência e CTA final), "headline_a": '
    'string, "headline_b": string, "headline_c": string}'
)


def _clean_json(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        pass
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    data = json.loads(text[start:i + 1])
                    return data if isinstance(data, dict) else None
                except Exception:
                    return None
    return None


def fallback_vsl(title: str, niche: str, offer_description: str = "") -> Dict[str, str]:
    """Fallback determinístico — nunca deixar a fábrica sem roteiro."""
    offer = offer_description or f"acesso completo ao conteúdo sobre {title}"
    return {
        "script": (
            f"Você já tentou de tudo em {niche} e os resultados não vieram? "
            f"Chega de perder tempo com conteúdo solto e sem direção. "
            f"Apresento o {title}: {offer}. Neste treinamento você vai do zero "
            f"à prática com um passo a passo claro, sem enrolação. São módulos "
            f"objetivos, exemplos reais e um método testado. E tem mais: "
            f"acesso imediato, atualizações inclusas e garantia de reembolso. "
            f"Clique agora e comece hoje mesmo a transformar seus resultados "
            f"em {niche}."
        ),
        "headline_a": f"Descubra Como Obter Sucesso no Nicho de {niche} em Pouco Tempo!",
        "headline_b": f"O Método Revelado Para Dominar {niche} Sem Esforço Extra.",
        "headline_c": f"Apenas Hoje: Assista Ao Vídeo E Mude Sua Trajetória em {niche}.",
    }


async def generate_vsl_content(
    title: str,
    niche: str,
    offer_description: str = "",
    target_audience: str = "",
    cta_url: str = "",
) -> Dict[str, str]:
    """Gera {script, headline_a, headline_b, headline_c} via LLM (cascata).

    Em caso de falha da LLM (ou resposta inválida), cai no fallback
    determinístico. Nunca levanta exceção.
    """
    try:
        from agents.llm import query_llm

        user_prompt = f"""
    Título/Tema da VSL: "{title}"
    Nicho do Produto: "{niche}"
    Oferta: "{offer_description or 'Acesso completo ao produto'}"
    Público-alvo: "{target_audience or niche}"
    URL do CTA (use no final do roteiro): "{cta_url}"

    Gere:
    - script: roteiro completo de vendas (abertura com a dor, promessa,
      prova/benefícios, quebra de objeções, oferta, urgência e CTA final).
    - headline_a: foco na dor principal ou transformação rápida.
    - headline_b: foco em quebrar objeções ou curiosidade.
    - headline_c: foco em ganho financeiro, facilidade ou urgência.
    """
        raw = await query_llm(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1800,
            temperature=0.7,
        )
        data = _clean_json(raw) or {}
        script = (data.get("script") or "").strip()
        result = {
            "script": script,
            "headline_a": (data.get("headline_a") or "").strip(),
            "headline_b": (data.get("headline_b") or "").strip(),
            "headline_c": (data.get("headline_c") or "").strip(),
        }
        if result["script"]:
            return result
    except Exception as e:  # noqa: BLE001
        print(f"[VslFactory] Erro ao consultar IA: {e}")

    return fallback_vsl(title, niche, offer_description)


async def create_vsl(
    title: str,
    niche: str,
    video_url: str = "",
    thumbnail_url: str = "",
    offer_description: str = "",
    target_audience: str = "",
    cta_url: str = "",
    delay_seconds: int = 0,
) -> Dict[str, Any]:
    """Gera o conteúdo (script + headlines) e persiste um registro de VSL."""
    from modules.database import create_db_vsl_video

    content = await generate_vsl_content(
        title, niche, offer_description, target_audience, cta_url
    )
    vsl = create_db_vsl_video(
        title=title,
        video_url=video_url,
        nicho=niche,
        thumbnail_url=thumbnail_url or None,
        delay_seconds=delay_seconds,
        headline_a=content["headline_a"],
        headline_b=content["headline_b"],
        headline_c=content["headline_c"],
        script=content["script"],
        offer_description=offer_description or None,
        target_audience=target_audience or None,
        cta_url=cta_url or None,
    )
    return vsl
