"""
Blueprint Engine — Motor da Fábrica de Blueprints (Dezafira).

Um Blueprint é uma "receita de produto": tema + nicho + preço → a IA gera
TODOS os artefatos (produto, blog/banners, landing, funil, área de membros,
miniapp) com revisão visual de imagens (super prompt + upload + zoom) e a
ponte publica tudo no DezafiraClube.

Estágios (persistidos em blueprints.stage/status):
  0. fundacao   — nome, slug, descrição, copy, CTAs, FAQ (LLM cascade)
  1. conteudo   — dispara pipelines existentes (ebook/curso/app/blog)
  2. assets     — gera todas as imagens (Agnes AI → cascata) + super prompts
  3. landing    — monta blocos via template registry (draft)
  4. funil      — order bump + upsell/downsell
  5. revisao    — status=review (UI mostra os AssetSlots)
  6. publicacao — ponte Adm → Clube (disparada por /publish)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from modules.database import get_db_blueprint, update_db_blueprint

# Raiz do projeto (mesmo padrão de modules/agnes_studio.py)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Registro de tasks em memória (espelha PRODUCT_TASKS do product_factory)
BLUEPRINT_TASKS: Dict[str, Dict[str, Any]] = {}

STAGE_ORDER = ["fundacao", "conteudo", "assets", "landing", "funil", "revisao"]

STAGE_LABELS = {
    "fundacao": "Fundação",
    "conteudo": "Conteúdo",
    "assets": "Assets de imagem",
    "landing": "Landing page",
    "funil": "Funil (bump/upsell/downsell)",
    "revisao": "Revisão visual",
    "publicacao": "Publicação no Clube",
}


def _slugify(text: str) -> str:
    """Gera slug simples (sem acentos, espaços → hífens)."""
    text = (text or "").lower()
    for a, b in (("á", "a"), ("à", "a"), ("â", "a"), ("ã", "a"), ("ä", "a"),
                 ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"),
                 ("í", "i"), ("ì", "i"), ("î", "i"), ("ï", "i"),
                 ("ó", "o"), ("ò", "o"), ("ô", "o"), ("õ", "o"), ("ö", "o"),
                 ("ú", "u"), ("ù", "u"), ("û", "u"), ("ü", "u"), ("ç", "c")):
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:80] or "produto"


def _parse_llm_json(raw: str) -> Optional[Dict[str, Any]]:
    """Extrai um objeto JSON de uma resposta LLM (tolerante a cercas/código)."""
    if not raw:
        return None
    text = raw.strip()
    # Remove code fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        pass
    # Fallback: primeiro {...} balanceado
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


def blueprint_task_status(bp_id: str) -> Optional[Dict[str, Any]]:
    """Status da task em memória (se existir); fallback: estado persistido."""
    task = BLUEPRINT_TASKS.get(bp_id)
    if task:
        return dict(task)
    bp = get_db_blueprint(bp_id)
    if not bp:
        return None
    return {
        "bp_id": bp_id,
        "status": bp.get("status"),
        "stage": bp.get("stage"),
        "message": STAGE_LABELS.get(bp.get("stage"), ""),
        "error": bp.get("error"),
    }


async def _set_stage(bp_id: str, stage: str, status: str, message: str = "", **fields) -> None:
    """Persiste estágio/status/mensagem + campos extras do blueprint."""
    if bp_id in BLUEPRINT_TASKS:
        BLUEPRINT_TASKS[bp_id].update({"stage": stage, "status": status, "message": message})
    update_db_blueprint(
        bp_id,
        stage=stage,
        status=status,
        error=None if status != "failed" else (fields.pop("error", None) or message or None),
        **{k: v for k, v in fields.items() if v is not None},
    )


# ── Estágio 0 · FUNDAÇÃO ─────────────────────────────────────────────────────

_FUNDACAO_SYSTEM = (
    "Você é o estrategista de produtos digitais da Dezafira. Gere a fundação de um "
    "produto digital em português do Brasil. Responda APENAS com JSON válido, sem "
    "markdown, com estas chaves exatas: "
    '{"name": string, "slug": string, "description": string (1-2 frases), '
    '"pitch": string (uma frase de venda), "cta_primary": string, '
    '"cta_secondary": string, "faq": [{"q": string, "a": string}] (3 a 5 itens)}'
)


async def _stage_fundacao(bp: Dict[str, Any]) -> Dict[str, Any]:
    """Estágio 0 — Fundação: gera identidade do produto via LLM (fallback determinístico)."""
    theme = (bp.get("theme") or "").strip()
    niche = (bp.get("niche") or "Geral").strip()
    price = bp.get("price_cents") or 0
    slug = _slugify(theme)

    fallback = {
        "name": theme,
        "slug": slug,
        "description": f"Produto {theme} — focado no nicho {niche}, gerado pelo Blueprint Dezafira.",
        "pitch": f"Tudo o que você precisa saber sobre {theme}.",
        "cta_primary": "Quero acesso agora",
        "cta_secondary": "Ver conteúdo",
        "faq": [
            {"q": "Como recebo o acesso?", "a": "Na hora, após a confirmação do pagamento."},
            {"q": "E se eu não gostar?", "a": "Você pode pedir reembolso em até 7 dias."},
            {"q": "Por quanto tempo tenho acesso?", "a": "Acesso vitalício ao conteúdo."},
        ],
    }

    try:
        from agents.llm import query_llm, ERROR_PREFIX
        user = (
            f"Tema: {theme}\nNicho: {niche}\nPreço sugerido: R$ {price / 100:.2f}\n"
            f"Público-alvo: iniciantes no nicho {niche}.\n"
            "Gere o JSON da fundação do produto."
        )
        raw = await query_llm(
            [{"role": "system", "content": _FUNDACAO_SYSTEM}, {"role": "user", "content": user}],
            max_tokens=800,
            temperature=0.6,
        )
        if raw and ERROR_PREFIX not in raw:
            parsed = _parse_llm_json(raw)
            if parsed:
                for key in ("name", "slug", "description", "pitch", "cta_primary", "cta_secondary"):
                    if isinstance(parsed.get(key), str) and parsed[key].strip():
                        fallback[key] = parsed[key].strip()
                if isinstance(parsed.get("faq"), list) and parsed["faq"]:
                    faq = []
                    for item in parsed["faq"][:5]:
                        if isinstance(item, dict) and item.get("q") and item.get("a"):
                            faq.append({"q": str(item["q"])[:200], "a": str(item["a"])[:500]})
                    if faq:
                        fallback["faq"] = faq
                fallback["slug"] = _slugify(fallback.get("slug") or fallback["name"]) or slug
    except Exception as e:  # noqa: BLE001
        print(f"[Blueprint] Fundação via LLM falhou, usando fallback: {e}")

    return fallback


# ── Estágio 1 · CONTEÚDO ─────────────────────────────────────────────────────

def _deliverable_link(fmt: str, artifact: Dict[str, Any]) -> str:
    """Monta o link de entrega do artefato no backend Adm."""
    from modules.clube_bridge import backend_url
    base = backend_url()
    artifact_id = artifact.get("id") or ""
    if fmt == "curso":
        return f"{base}/curso/{artifact_id}"
    if fmt == "app":
        if artifact.get("app_type") == "miniapp":
            return f"{base}/miniapps/{artifact.get('app_id') or artifact_id}/view"
        return f"{base}/mindmap/{artifact_id}"
    # ebook / padrão
    return f"{base}/api/v1/ebooks/{artifact_id}"


async def _run_format_for_bp(bp_id: str, fmt: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Dispara a pipeline do formato e retorna o artefato produzido (ou erro)."""
    task_id = f"bp_{bp_id[-8:]}"
    price = int(config.get("price_cents") or 0)
    try:
        if fmt == "ebook":
            from modules.ebook_pipeline import run_ebook_macro_pipeline

            def cb(tid, *args, **kwargs):
                data = args[3] if len(args) > 3 else {}
                if isinstance(data, dict):
                    _set_stage(bp_id, "conteudo", "generating",
                               f"Ebook: {data.get('message', '')[:90] or 'gerando...'}")
            asyncio.create_task(_set_stage(bp_id, "conteudo", "generating", "Ebook: gerando capítulos..."))
            result = await run_ebook_macro_pipeline(
                niche=config.get("niche", ""),
                book_title=config.get("title", ""),
                blog_channel_id=config.get("blog_channel_id", ""),
                style_id=config.get("style_id", "minimalista"),
                price_cents=price,
                target_chapters=int(config.get("target_chapters") or 8),
                task_id=task_id,
                on_progress=cb,
            )
            book_id = (result or {}).get("book_id") or (result or {}).get("id") or ""
            return {
                "format": "ebook", "id": book_id,
                "title": (result or {}).get("title") or config.get("title") or "",
                "cover_url": (result or {}).get("cover_url") or "",
                "price_cents": price,
                "external_link": _deliverable_link("ebook", {"id": book_id}) if book_id else "",
                "status": "completed" if (result or {}).get("status") != "failed" and book_id else "failed",
                "error": (result or {}).get("error") or "",
            }

        if fmt == "curso":
            from modules.course_pipeline import run_course_macro_pipeline

            def cb(tid, *args, **kwargs):
                data = args[3] if len(args) > 3 else {}
                if isinstance(data, dict):
                    _set_stage(bp_id, "conteudo", "generating",
                               f"Curso: {data.get('message', '')[:90] or 'gerando...'}")
            await _set_stage(bp_id, "conteudo", "generating", "Curso: gerando módulos e aulas...")
            result = await run_course_macro_pipeline(
                topic=config.get("topic", "") or config.get("title", ""),
                course_title=config.get("title", ""),
                difficulty=config.get("difficulty", "iniciante"),
                price_cents=price,
                target_modules=int(config.get("target_modules") or 4),
                lessons_per_module=int(config.get("lessons_per_module") or 4),
                task_id=task_id,
                on_progress=cb,
            )
            course_id = (result or {}).get("course_id") or ""
            return {
                "format": "curso", "id": course_id,
                "title": (result or {}).get("course_title") or config.get("title") or "",
                "cover_url": (result or {}).get("cover_url") or "",
                "price_cents": price,
                "external_link": _deliverable_link("curso", {"id": course_id}) if course_id else "",
                "status": "completed" if course_id else "failed",
                "error": (result or {}).get("error") or "",
            }

        if fmt == "app":
            app_type = (config.get("app_type") or "mindmap").lower()
            if app_type == "miniapp":
                from modules.miniapp_factory import miniapp_factory
                from modules.database import create_db_miniapp
                prompt = (config.get("title") or config.get("theme") or "App de Recorrência").strip()
                niche = config.get("niche") or "Geral"
                slug = miniapp_factory._ensure_unique_slug(miniapp_factory._slug_from_prompt(prompt))
                placeholder = create_db_miniapp(app_name=prompt[:48], niche=niche, status="creating", slug=slug)
                app_id = placeholder["id"]
                await _set_stage(bp_id, "conteudo", "generating", "MiniApp: sala de agentes gerando PWA...")
                await miniapp_factory.create_miniapp_with_room(prompt, niche, app_id=app_id)
                return {
                    "format": "app", "id": app_id, "app_type": "miniapp", "app_id": app_id,
                    "title": prompt, "cover_url": "",
                    "price_cents": price,
                    "external_link": _deliverable_link("app", {"id": app_id, "app_type": "miniapp"}),
                    "status": "completed", "error": "",
                }
            from modules.mindmap_pipeline import run_mindmap_macro_pipeline
            await _set_stage(bp_id, "conteudo", "generating", "Mapa Mental: gerando conteúdo e quiz...")
            result = await run_mindmap_macro_pipeline(
                niche=config.get("niche", ""),
                title=config.get("title", ""),
                style_id=config.get("style_id", "minimalista"),
                price_cents=price,
                task_id=task_id,
            )
            mm_id = (result or {}).get("mindmap_id") or ""
            return {
                "format": "app", "id": mm_id, "app_type": "mindmap",
                "title": (result or {}).get("title") or config.get("title") or "",
                "cover_url": (result or {}).get("cover_url") or "",
                "price_cents": price,
                "external_link": _deliverable_link("app", {"id": mm_id}) if mm_id else "",
                "status": "completed" if mm_id else "failed",
                "error": (result or {}).get("error") or "",
            }

        if fmt == "blog":
            from modules.blog_pipeline import run_blog_macro_pipeline
            blog_name = config.get("title") or config.get("theme") or f"Blog {config.get('niche', '')}"
            await _set_stage(bp_id, "conteudo", "generating",
                             f"Blog {blog_name}: gerando artigos...")
            result = await run_blog_macro_pipeline(
                blog_name=blog_name,
                niche=config.get("niche", ""),
                language=config.get("language", "pt"),
                task_id=task_id,
                target_articles=int(config.get("artigos") or 3) if config.get("artigos") else None,
            )
            return {
                "format": "blog",
                "id": (result or {}).get("channel_id") or "",
                "title": blog_name,
                "cover_url": (result or {}).get("banner_url") or "",
                "price_cents": price,
                "external_link": "",
                "status": "completed" if (result or {}).get("status") != "failed" else "failed",
                "error": (result or {}).get("error") or "",
                "articles_generated": (result or {}).get("articles_generated") or 0,
            }
    except Exception as e:  # noqa: BLE001
        print(f"[Blueprint] Falha ao rodar formato {fmt}: {e}")
        return {"format": fmt, "id": "", "title": "", "status": "failed", "error": str(e)}
    return {"format": fmt, "id": "", "title": "", "status": "failed", "error": "Formato desconhecido"}


async def _stage_conteudo(bp_id: str, bp: Dict[str, Any], fundacao: Dict[str, Any]) -> Dict[str, Any]:
    """Estágio 1 — Conteúdo: roda as pipelines de cada formato da receita."""
    formats = [f for f in (bp.get("formats") or []) if isinstance(f, str)]
    config = dict(bp.get("config") or {})
    config.setdefault("title", fundacao.get("name") or bp.get("theme"))
    config.setdefault("niche", bp.get("niche"))
    config.setdefault("theme", bp.get("theme"))
    config.setdefault("price_cents", bp.get("price_cents") or 0)

    artifacts: List[Dict[str, Any]] = []
    for fmt in formats:
        artifact = await _run_format_for_bp(bp_id, fmt, config)
        artifacts.append(artifact)
        update_db_blueprint(bp_id, content={"fundacao": fundacao, "conteudo": {"formats": formats, "artifacts": list(artifacts)}})

    return {"formats": formats, "artifacts": artifacts}


# ── Estágio 2 · ASSETS ───────────────────────────────────────────────────────

def _build_slot_defs(content: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Define os slots de imagem do blueprint (key, label, dims, prompt)."""
    fund = content.get("fundacao") or {}
    conteudo = content.get("conteudo") or {}
    funil = content.get("funil") or {}
    formats = conteudo.get("formats") or []
    name = fund.get("name") or config.get("title") or "Produto"
    niche = config.get("niche") or "Geral"
    slug = fund.get("slug") or "produto"
    n_posts = sum(int(a.get("articles_generated") or 0) for a in conteudo.get("artifacts") or [] if a.get("format") == "blog")

    slots: List[Dict[str, Any]] = [
        {
            "key": "product_image", "label": "Capa do produto",
            "width": 1024, "height": 1024,
            "prompt": f"Capa quadrada premium do produto '{name}', nicho {niche}, arte digital clean, sem texto",
        },
        {
            "key": "product_image_agnes", "label": "Capa do produto (Agnes Studio)",
            "width": 1024, "height": 1024,
            "prompt": f"Capa editorial do produto '{name}', nicho {niche}",
            "agnes_only": True,  # gerada pelo Agnes Studio (tipografia + créditos)
        },
        {
            "key": "landing_hero", "label": "Hero da landing",
            "width": 1200, "height": 630,
            "prompt": f"Hero banner 16:9 para a landing do produto '{name}', nicho {niche}, cinematográfico, sem texto",
        },
        {
            "key": "landing_offer", "label": "Imagem da oferta",
            "width": 1200, "height": 630,
            "prompt": f"Imagem de oferta/conteúdo do produto '{name}', nicho {niche}, clean, sem texto",
        },
    ]

    if "blog" in formats or n_posts > 0:
        slots.append({
            "key": "blog_banner_sidebar", "label": "Banner sidebar do blog",
            "width": 600, "height": 600,
            "prompt": f"Banner quadrado de divulgação do produto '{name}', nicho {niche}, chamativo, sem texto",
        })
        slots.append({
            "key": "blog_banner_inline", "label": "Banner inline dos posts",
            "width": 1200, "height": 630,
            "prompt": f"Banner 16:9 inline de posts para '{name}', nicho {niche}, editorial, sem texto",
        })
        for i in range(min(n_posts, 6)):
            slots.append({
                "key": f"post_cover_{i}", "label": f"Capa do artigo {i + 1}",
                "width": 1200, "height": 630,
                "prompt": f"Capa 16:9 de artigo de blog sobre {name}, nicho {niche}, editorial profissional, sem texto",
            })

    if "curso" in formats:
        slots.append({
            "key": "member_cover", "label": "Capa do curso (área de membros)",
            "width": 1280, "height": 720,
            "prompt": f"Thumbnail 16:9 de curso sobre '{name}', nicho {niche}, estética moderna, sem texto",
        })

    if "app" in formats and (config.get("app_type") or "mindmap").lower() == "miniapp":
        slots.append({
            "key": "miniapp_logo", "label": "Logo do MiniApp",
            "width": 1024, "height": 1024,
            "prompt": f"Logo 3D do MiniApp '{name}', nicho {niche}, ícone arredondado, sem texto",
        })

    upsell = funil.get("upsell")
    if upsell and upsell.get("name"):
        slots.append({
            "key": "upsell_image", "label": "Imagem do upsell",
            "width": 1200, "height": 630,
            "prompt": f"Imagem 16:9 da oferta de upsell '{upsell.get('name')}', nicho {niche}, persuasiva, sem texto",
        })
    downsell = funil.get("downsell")
    if downsell and downsell.get("name"):
        slots.append({
            "key": "downsell_image", "label": "Imagem do downsell",
            "width": 1200, "height": 630,
            "prompt": f"Imagem 16:9 da oferta de downsell '{downsell.get('name')}', nicho {niche}, amigável, sem texto",
        })

    return slots


async def _stage_assets(bp_id: str, bp: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
    """Estágio 2 — Assets: gera cada slot via Agnes AI (cascata) com super prompt."""
    from modules.image_factory import ImageGeneratorAgent

    config = bp.get("config") or {}
    slot_defs = _build_slot_defs(content, config)
    existing = dict(bp.get("assets") or {})
    agent = ImageGeneratorAgent()

    async def _gen_slot(slot: Dict[str, Any]) -> None:
        key = slot["key"]
        cur = existing.get(key) or {}
        # Upload manual tem prioridade — nunca sobrescreve
        if cur.get("source") == "upload":
            return
        try:
            res = await agent.generate_image_for_post(
                prompt_idea=slot["prompt"],
                niche=bp.get("niche") or "Geral",
                width=slot["width"],
                height=slot["height"],
            )
            new_asset = {
                "url": res.get("image_url") or "",
                "super_prompt": res.get("expanded_prompt") or slot["prompt"],
                "provider": res.get("provider") or "unknown",
                "source": "ai",
                "width": slot["width"],
                "height": slot["height"],
            }
            new_asset["history"] = _snapshot_into_history(existing, key, new_asset)
            existing[key] = new_asset
        except Exception as e:  # noqa: BLE001
            existing[key] = {
                "url": "", "super_prompt": slot["prompt"], "provider": "error",
                "source": "ai", "width": slot["width"], "height": slot["height"],
                "error": str(e),
            }

    if slot_defs:
        update_db_blueprint(bp_id, content={**content, "assets": {"slots": slot_defs}})

    # Slots regulares: lotes paralelos de geração (imagem), sem escrita concorrente
    regular = [s for s in slot_defs if not s.get("agnes_only")]
    for i in range(0, len(regular), 3):
        batch = regular[i:i + 3]
        await asyncio.gather(*[_gen_slot(s) for s in batch])

    # Slots Agnes Studio (capa editorial automática — ex: product_image_agnes):
    # fora do lote paralelo, reusa generate_agnes_cover_asset (escrita sequencial)
    for slot in slot_defs:
        if not slot.get("agnes_only"):
            continue
        key = slot["key"]
        try:
            res = await generate_agnes_cover_asset(bp_id, key, style_id="moderno")
            new_asset = {k: v for k, v in res.items() if k != "slot"}
            new_asset["history"] = _snapshot_into_history(existing, key, new_asset)
            existing[key] = new_asset
        except Exception as e:  # noqa: BLE001
            existing[key] = {
                "url": "", "super_prompt": slot.get("prompt") or "",
                "provider": "error", "source": "ai",
                "width": slot.get("width"), "height": slot.get("height"), "error": str(e),
            }

    # Persistência única ao final (evita lock de escrita concorrente no SQLite)
    update_db_blueprint(bp_id, assets=dict(existing))

    return {"slots": slot_defs, "generated": len([k for k, v in existing.items() if v.get("url")])}


# ── Vídeo promocional opcional (config.video.enabled) ───────────────────────

async def _stage_promo_video(bp: Dict[str, Any], content: Dict[str, Any],
                             assets: Dict[str, Any]) -> Dict[str, Any]:
    """Estágio 2c — Vídeo promocional do produto via Agnes & Remotion (Apple TV+ 15s).
    """
    import shutil
    import json
    import subprocess
    import httpx
    from modules.database import update_db_blueprint
    from modules.art_director import ArtDirector, VIBES
    from modules.image_factory import ImageGeneratorAgent
    
    fund = content.get("fundacao") or {}
    name = fund.get("name") or bp.get("theme") or "Produto"
    subtitle = fund.get("description") or ""
    niche = bp.get("niche") or "Geral"
    bp_id = bp.get("id") or "prod"
    existing = dict(bp.get("assets") or {})
    slot_defs = list(((content.get("assets") or {}).get("slots") or []))
    
    # 1. Obter as imagens para o storyboard de 3 cenas
    avatar_url = bp.get("avatar_1_url") or bp.get("avatar_2_url")
    
    factory = ImageGeneratorAgent()
    
    async def get_and_download_image(url_source: Optional[str], prompt: str, local_name: str) -> str:
        dest_path = os.path.join(_BASE_DIR, "remotion-studio", "public", local_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        if url_source and url_source.startswith("http"):
            try:
                async with httpx.AsyncClient(timeout=40.0) as client:
                    r = await client.get(url_source)
                    if r.status_code == 200:
                        with open(dest_path, "wb") as f:
                            f.write(r.content)
                        return local_name
            except Exception as e:
                print(f"[Blueprint Video] Erro ao baixar url {url_source}: {e}")
                
        print(f"[Blueprint Video] Gerando imagem limpa para {local_name}...")
        res = await factory._agnes_generate(prompt, width=1920, height=1080)
        if not res or not res.get("image_url"):
            res = await factory._gemini_imagen(prompt, width=1920, height=1080)
            
        if res and res.get("image_url"):
            try:
                async with httpx.AsyncClient(timeout=40.0) as client:
                    r = await client.get(res["image_url"])
                    if r.status_code == 200:
                        with open(dest_path, "wb") as f:
                            f.write(r.content)
                        return local_name
            except Exception as e:
                print(f"[Blueprint Video] Erro ao baixar imagem gerada: {e}")
                
        return ""

    p1 = (
        f"Cinematic 8k movie poster close-up portrait of an elegant confident presenter for {niche}, "
        "dramatic soft studio rim lighting, deep cinematic shadows, dark minimalist background with subtle volumetric cyan and violet atmospheric light, "
        "shot on 85mm Zeiss lens, f/1.4, extreme photographic realism, Dolby Vision HDR, high-fashion aesthetic, "
        "completely clean background, absolutely NO text, NO typography, NO watermark, NO letters, NO words"
    )
    p2 = (
        f"Cinematic ultra-detailed floating dark glass prisms and holographic data streams for {name}, "
        "subtle neon cyan and violet volumetric laser rays, deep navy black background, 8k, photorealistic, "
        "completely clean, absolutely NO text, NO typography, NO watermark, NO letters, NO words"
    )
    p3 = (
        "Epic dark minimalist horizon with electric cyan and purple atmospheric glow, subtle floating ambient bokeh lights, "
        "sleek dark reflective polished floor, premium high-end Apple presentation aesthetic, 8k, "
        "completely clean, absolutely NO text, NO typography, NO watermark, NO letters, NO words"
    )
    
    img1 = await get_and_download_image(avatar_url, p1, "scene1.png")
    img2 = await get_and_download_image(None, p2, "scene2.png")
    img3 = await get_and_download_image(None, p3, "scene3.png")
    
    logo_src = os.path.join(_BASE_DIR, "assets", "brand", "logo_icon.png")
    logo_dest = os.path.join(_BASE_DIR, "remotion-studio", "public", "logo.png")
    if os.path.isfile(logo_src):
        shutil.copy2(logo_src, logo_dest)
        
    props = {
        "bgImages": ["scene1.png", "scene2.png", "scene3.png"],
        "logoPath": "logo.png",
        "colors": {
            "bg": "#0a0a0c",
            "primary": "#00CFFF",
            "secondary": "#7B4FD6"
        },
        "durationInSeconds": 15
    }
    
    props_path = os.path.join(_BASE_DIR, "remotion-studio", "temp_props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)
        
    subprocess.run(
        'powershell -Command "Get-Process -Name chrome -ErrorAction SilentlyContinue | Stop-Process -Force; Get-Process -Name chrome-headless-shell -ErrorAction SilentlyContinue | Stop-Process -Force"',
        shell=True,
        capture_output=True
    )
    
    final_video_path = os.path.join(_BASE_DIR, "outputs", "vsl", f"bp_{bp_id[-8:]}_promo.mp4")
    os.makedirs(os.path.dirname(final_video_path), exist_ok=True)
    
    node_dir = os.path.join(_BASE_DIR, ".tools", "node")
    env = os.environ.copy()
    env["PATH"] = node_dir + ";" + env.get("PATH", "")
    
    cmd = [
        "npx.cmd", "remotion", "render",
        "src/index.ts", "CinematicPromo",
        final_video_path.replace("\\", "/"),
        f"--props={props_path.replace('\\', '/')}",
        "--browser-arg=--no-sandbox",
        "--browser-arg=--disable-setuid-sandbox",
        "--browser-arg=--disable-gpu",
        "--browser-arg=--disable-dev-shm-usage",
        "--y"
    ]
    
    print(f"[Blueprint Video] Iniciando renderização Remotion: {final_video_path}")
    p = subprocess.run(
        cmd,
        cwd=os.path.join(_BASE_DIR, "remotion-studio"),
        env=env,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    
    if p.returncode == 0 and os.path.isfile(final_video_path):
        print(f"[Blueprint Video] Renderização concluída com sucesso: {final_video_path}")
        local_url = "/outputs/vsl/" + os.path.basename(final_video_path)
    else:
        print(f"[Blueprint Video] Erro na renderização Remotion. Retorno: {p.returncode}\nStderr: {p.stderr}")
        local_url = ""
        
    try:
        os.unlink(props_path)
    except OSError:
        pass
        
    if not local_url:
        return {"generated": False, "error": "Remotion render falhou"}
        
    new_asset = {
        "url": local_url,
        "provider": "remotion-apple-tv",
        "source": "ai",
        "video": True,
        "width": 1280, "height": 720,
        "duration": "15.0",
        "remote_url": ""
    }
    new_asset["history"] = _snapshot_into_history(existing, "promo_video", new_asset)
    existing["promo_video"] = new_asset
    
    # Slot visível na UI de assets (video=True → AssetSlot renderiza <video>)
    if not any(s.get("key") == "promo_video" for s in slot_defs):
        slot_defs.append({
            "key": "promo_video", "label": "🎬 Vídeo promocional",
            "video": True, "width": 1280, "height": 720,
        })
        
    update_db_blueprint(bp.get("id"), assets=dict(existing),
                        content={**content, "assets": {"slots": slot_defs}})
    return {
        "generated": True, "url": local_url, "remote_url": url,
        "duration": new_asset["duration"], "video_id": result.get("video_id"),
    }


# ── VSL opcional (entre assets e landing) ────────────────────────────────────

async def _stage_vsl(bp: Dict[str, Any], content: Dict[str, Any],
                     assets: Dict[str, Any]) -> Dict[str, Any]:
    """Gera a VSL do blueprint (script + headlines + thumbnail) quando
    `config.vsl.enabled`. Usa a fundação do blueprint como oferta; a thumbnail
    sai da capa editorial do produto (product_image_agnes) ou da imagem por
    prompt (product_image). Nunca falha: usa o fallback determinístico."""
    from modules.vsl_factory import create_vsl

    fund = content.get("fundacao") or {}
    config = bp.get("config") or {}
    vsl_cfg = config.get("vsl") or {}
    niche = bp.get("niche") or "Geral"
    title = fund.get("name") or bp.get("theme") or "Produto"
    thumbnail = ((assets.get("product_image_agnes") or {}).get("url")
                 or (assets.get("product_image") or {}).get("url") or "")
    video_url = (vsl_cfg.get("video_url") or "").strip()

    try:
        vsl = await create_vsl(
            title=title,
            niche=niche,
            video_url=video_url,
            thumbnail_url=thumbnail,
            offer_description=fund.get("description") or "",
            target_audience=niche,
            cta_url=f"/product/{fund.get('slug') or config.get('slug') or 'produto'}",
        )
    except Exception as e:  # noqa: BLE001
        print(f"[Blueprint] Erro ao gerar VSL: {e}")
        return {"error": str(e), "generated": False}

    return {
        "generated": True,
        "vsl_id": vsl.get("id"),
        "title": vsl.get("title"),
        "script": vsl.get("script"),
        "headline_a": vsl.get("headline_a"),
        "headline_b": vsl.get("headline_b"),
        "headline_c": vsl.get("headline_c"),
        "thumbnail_url": vsl.get("thumbnail_url"),
        "video_url": vsl.get("video_url") or "",
    }


# ── Estágio 3 · LANDING ──────────────────────────────────────────────────────

async def _stage_landing(bp_id: str, bp: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
    """Estágio 3 — Landing: monta os blocos do template (draft) para a CLI do Clube."""
    from modules.landing_templates import build_landing_blocks

    config = bp.get("config") or {}
    assets = bp.get("assets") or {}
    template = config.get("template_landing") or "dezafira"
    try:
        blocks = build_landing_blocks(template, content, config, assets)
    except Exception as e:  # noqa: BLE001
        print(f"[Blueprint] Erro ao montar landing: {e}")
        blocks = []
    return {"template": template, "blocks": blocks, "published": False, "public_url": None}


# ── Estágio 4 · FUNIL ────────────────────────────────────────────────────────

async def _stage_funil(bp: Dict[str, Any]) -> Dict[str, Any]:
    """Estágio 4 — Funil: order bump + upsell/downsell (definições da receita)."""
    config = bp.get("config") or {}
    funil_cfg = config.get("funil") or {}

    def _clean_child(raw: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, dict) or not raw.get("name"):
            return None
        return {
            "name": str(raw["name"])[:200],
            "price_cents": max(0, int(raw.get("price_cents") or 0)),
            "slug": _slugify(raw.get("slug") or raw["name"]),
        }

    order_bump = None
    if isinstance(funil_cfg.get("order_bump"), dict) and funil_cfg["order_bump"].get("title"):
        ob = funil_cfg["order_bump"]
        order_bump = {
            "title": str(ob["title"])[:200],
            "price_cents": max(0, int(ob.get("price_cents") or 0)),
            "description": str(ob.get("description") or "")[:500],
        }

    # Combo/pacote nativo (fase 2): bundle com os produtos da oferta
    bundle_cfg = funil_cfg.get("bundle") or {}
    bundle = None
    if bundle_cfg.get("enabled"):
        fund = (bp.get("content") or {}).get("fundacao") or {}
        main_slug = fund.get("slug") or _slugify(bp.get("theme") or "produto")
        bundle = {
            "enabled": True,
            "name": str(bundle_cfg.get("name") or "")[:200] or None,
            "discount_pct": max(0, min(90, int(bundle_cfg.get("discount_pct") or 0))),
            "include_upsell": bool(bundle_cfg.get("include_upsell", True)),
            "include_downsell": bool(bundle_cfg.get("include_downsell", True)),
            # Slug determinístico (o Clube usa se estiver livre) — a landing
            # já nasce apontando pro combo quando habilitado
            "slug": f"{main_slug}-pacote",
        }

    return {
        "order_bump": order_bump,
        "upsell": _clean_child(funil_cfg.get("upsell")),
        "downsell": _clean_child(funil_cfg.get("downsell")),
        "bundle": bundle,
    }


# ── Orquestrador do motor ────────────────────────────────────────────────────

async def run_blueprint(bp_id: str) -> Dict[str, Any]:
    """Executa os estágios 0-5 e persiste o progresso (polling via GET blueprint)."""
    bp = get_db_blueprint(bp_id)
    if not bp:
        raise ValueError(f"Blueprint não encontrado: {bp_id}")

    BLUEPRINT_TASKS[bp_id] = {
        "bp_id": bp_id, "status": "generating", "stage": "fundacao",
        "message": STAGE_LABELS["fundacao"], "started_at": datetime.utcnow().isoformat(),
    }
    await _set_stage(bp_id, "fundacao", "generating", STAGE_LABELS["fundacao"])

    try:
        content = dict(bp.get("content") or {})
        assets = dict(bp.get("assets") or {})

        # 0. Fundação
        fundacao = await _stage_fundacao(bp)
        content["fundacao"] = fundacao
        await _set_stage(bp_id, "conteudo", "generating", STAGE_LABELS["conteudo"], content=dict(content))

        # 1. Conteúdo
        conteudo = await _stage_conteudo(bp_id, bp, fundacao)
        content["conteudo"] = conteudo
        await _set_stage(bp_id, "assets", "generating", STAGE_LABELS["assets"], content=dict(content))

        # 2. Assets
        bp = get_db_blueprint(bp_id) or bp  # conteúdo recarregado
        assets_info = await _stage_assets(bp_id, bp, content)
        content["assets"] = assets_info
        # Os assets já foram persistidos slot a slot pelo _stage_assets
        await _set_stage(bp_id, "landing", "generating", STAGE_LABELS["landing"],
                         content=dict(content))

        # 2b. Vídeo promocional opcional (config.video.enabled) — Agnes agnes-video-v2.0
        bp = get_db_blueprint(bp_id) or bp
        if (bp.get("config") or {}).get("video", {}).get("enabled"):
            content["video"] = await _stage_promo_video(bp, content, assets)
            update_db_blueprint(bp_id, content=dict(content))

        # 2c. VSL opcional (config.vsl.enabled) — usa a capa do produto como thumbnail
        bp = get_db_blueprint(bp_id) or bp
        if (bp.get("config") or {}).get("vsl", {}).get("enabled"):
            content["vsl"] = await _stage_vsl(bp, content, assets)
            update_db_blueprint(bp_id, content=dict(content))

        # 3. Landing
        bp = get_db_blueprint(bp_id) or bp
        landing = await _stage_landing(bp_id, bp, content)
        content["landing"] = landing
        await _set_stage(bp_id, "funil", "generating", STAGE_LABELS["funil"], content=dict(content))

        # 4. Funil
        bp = get_db_blueprint(bp_id) or bp
        funil = await _stage_funil(bp)
        content["funil"] = funil
        await _set_stage(bp_id, "revisao", "review", STAGE_LABELS["revisao"], content=dict(content))

        # 5. Revisão
        if bp_id in BLUEPRINT_TASKS:
            BLUEPRINT_TASKS[bp_id].update({"status": "review", "stage": "revisao"})
        return {"bp_id": bp_id, "status": "review", "stage": "revisao"}

    except Exception as e:  # noqa: BLE001
        await _set_stage(bp_id, bp.get("stage") or "", "failed", f"Erro no motor: {str(e)}", error=str(e))
        if bp_id in BLUEPRINT_TASKS:
            BLUEPRINT_TASKS[bp_id].update({"status": "failed", "error": str(e)})
        return {"bp_id": bp_id, "status": "failed", "error": str(e)}


def start_blueprint_run(bp_id: str) -> Dict[str, Any]:
    """Dispara o motor em background (asyncio task) — padrão do product_factory."""
    asyncio.create_task(run_blueprint(bp_id))
    return {"bp_id": bp_id, "status": "starting", "stage": "fundacao"}


# ── Assets: regenerar / upload ───────────────────────────────────────────────

def get_slot_def(bp: Dict[str, Any], slot_key: str) -> Optional[Dict[str, Any]]:
    """Localiza a definição do slot (dimensões/prompt) no content do blueprint."""
    slots = ((bp.get("content") or {}).get("assets") or {}).get("slots") or []
    for s in slots:
        if s.get("key") == slot_key:
            return s
    return None


_MAX_HISTORY = 8


def _snapshot_into_history(assets: Dict[str, Any], slot_key: str,
                           new_asset: Dict[str, Any]) -> list:
    """Empurra a versão atual do slot para o histórico antes de sobrescrever
    (apenas se a URL mudou) e RETORNA o histórico (o chamador deve anexá-lo
    ao novo asset — o dict antigo é substituído). Máx. _MAX_HISTORY entradas."""
    cur = assets.get(slot_key) or {}
    history = list(cur.get("history") or [])
    if cur.get("url") and cur.get("url") != new_asset.get("url"):
        import datetime as _dt
        version = {k: v for k, v in cur.items() if k != "history"}
        version["ts"] = _dt.datetime.utcnow().isoformat()
        history.append(version)
    return history[-_MAX_HISTORY:]


async def restore_asset_version(bp_id: str, slot_key: str, index: int) -> Dict[str, Any]:
    """Restaura uma versão do histórico para o slot (a atual volta pro histórico)."""
    bp = get_db_blueprint(bp_id)
    if not bp:
        raise ValueError("Blueprint não encontrado")
    assets = dict(bp.get("assets") or {})
    cur = assets.get(slot_key) or {}
    history = list(cur.get("history") or [])
    if index < 0 or index >= len(history):
        raise ValueError(f"Versão inválida: {index} (histórico tem {len(history)})")
    version = dict(history[index])
    version.pop("ts", None)

    # Snapshot da atual antes de restaurar
    if cur.get("url") and cur.get("url") != version.get("url"):
        snapshot = {k: v for k, v in cur.items() if k != "history"}
        snapshot["ts"] = version.get("ts") or datetime.utcnow().isoformat()
        history = [snapshot] + [h for i, h in enumerate(history) if i != index]
    else:
        history = [h for i, h in enumerate(history) if i != index]

    restored = dict(version)
    restored["history"] = history[-_MAX_HISTORY:]
    restored["source"] = "ai" if restored.get("source") != "upload" else "upload"
    assets[slot_key] = restored
    update_db_blueprint(bp_id, assets=assets)
    return {"slot": slot_key, **restored}


async def regenerate_asset(bp_id: str, slot_key: str) -> Dict[str, Any]:
    """Regenera a imagem de um slot (nova seed via Agnes/cascata)."""
    from modules.image_factory import ImageGeneratorAgent

    bp = get_db_blueprint(bp_id)
    if not bp:
        raise ValueError("Blueprint não encontrado")
    slot_def = get_slot_def(bp, slot_key)
    if not slot_def:
        raise ValueError(f"Slot não encontrado: {slot_key}")

    assets = dict(bp.get("assets") or {})
    if (assets.get(slot_key) or {}).get("source") == "upload":
        raise ValueError("Slot com imagem enviada por upload — use upload para substituir.")

    # Slot Agnes Studio → regenera pela capa editorial (mantém o brand kit do config)
    if slot_def.get("agnes_only"):
        res = await generate_agnes_cover_asset(
            bp_id, slot_key, style_id=(assets.get(slot_key) or {}).get("agnes_style") or "moderno")
        new_asset = {k: v for k, v in res.items() if k != "slot"}
        new_asset["history"] = _snapshot_into_history(assets, slot_key, new_asset)
        assets[slot_key] = new_asset
        update_db_blueprint(bp_id, assets=assets)
        return {"slot": slot_key, **assets[slot_key]}

    agent = ImageGeneratorAgent()
    res = await agent.generate_image_for_post(
        prompt_idea=slot_def.get("prompt", slot_key),
        niche=bp.get("niche") or "Geral",
        width=int(slot_def.get("width") or 1200),
        height=int(slot_def.get("height") or 630),
    )
    new_asset = {
        "url": res.get("image_url") or "",
        "super_prompt": res.get("expanded_prompt") or slot_def.get("prompt", ""),
        "provider": res.get("provider") or "unknown",
        "source": "ai",
        "width": int(slot_def.get("width") or 1200),
        "height": int(slot_def.get("height") or 630),
    }
    new_asset["history"] = _snapshot_into_history(assets, slot_key, new_asset)
    assets[slot_key] = new_asset
    update_db_blueprint(bp_id, assets=assets)
    return {"slot": slot_key, **assets[slot_key]}


# ── Assets: capa editorial Agnes Studio ──────────────────────────────────────

def _slot_to_agnes_kind(slot_key: str, slot_def: Dict[str, Any]) -> tuple:
    """Mapeia o slot do blueprint para o tipo de capa do Agnes Studio.

    Retorna (kind, width, height): product → capa quadrada; member_cover →
    curso 16:9; demais (posts, hero, oferta, banners, upsell/downsell) → blog.
    """
    w = int(slot_def.get("width") or 1200)
    h = int(slot_def.get("height") or 630)
    if slot_key == "product_image":
        return "product", 1024, 1024
    if slot_key == "member_cover":
        return "course", 1280, 720
    return "blog", w, h


async def _generate_agnes_cover(bp: Dict[str, Any], slot_def: Dict[str, Any],
                                style_id: str) -> Dict[str, Any]:
    """Gera a capa editorial do slot via Agnes Studio (sem persistir).
    Usado por generate_agnes_cover_asset (persiste) e pelas variantes."""
    from modules.agnes_studio import AgnesStudio

    from modules.art_director import VIBES
    valid_styles = ("moderno", "elegante", "tech", "minimal", "dark-gold") + tuple(VIBES.keys())
    style_id = style_id if style_id in valid_styles else "moderno"
    slot_key = slot_def.get("key", "")
    bp_id = bp.get("id", "")
    fund = (bp.get("content") or {}).get("fundacao") or {}
    config = bp.get("config") or {}
    niche = bp.get("niche") or "Geral"
    title = fund.get("name") or bp.get("theme") or slot_def.get("prompt") or "Produto"
    subtitle = fund.get("description") or ""
    kind, width, height = _slot_to_agnes_kind(slot_key, slot_def)
    author = "Dezafira Studio"
    entity = f"bp_{bp_id[-8:]}"

    # Brand kit do blueprint (cores/fontes customizadas) sobrepõe o estilo base
    from modules.art_director import ArtDirector, VIBES
    director = ArtDirector()
    brand_kit = config.get("brand_kit")
    vibe_id = (brand_kit or {}).get("vibe_id") or style_id
    if vibe_id in VIBES:
        design = director.generate_brand_kit(vibe_id, niche)
    else:
        studio = AgnesStudio()
        design = studio._make_design(style_id, niche, brand_kit=brand_kit)

    if kind == "product":
        res = await studio.generate_product_cover(
            title=title, subtitle=subtitle, niche=niche, style_id=style_id,
            entity_id=entity, design=design)
    elif kind == "course":
        res = await studio.generate_course_cover(
            title=title, subtitle=subtitle, author=author, niche=niche,
            style_id=style_id, course_id=entity, design=design)
    else:
        res = await studio.generate_blog_cover(
            title=title, subtitle=subtitle, niche=niche, style_id=style_id,
            post_id=entity, blog_name="Dezafira Studio", design=design)
    res["style_id"] = style_id
    res["title"] = title
    return res


async def generate_agnes_cover_asset(bp_id: str, slot_key: str,
                                     style_id: str = "moderno") -> Dict[str, Any]:
    """Gera a capa EDITORIAL do slot via Agnes Studio (tipografia + autor +
    créditos), ao lado da imagem por prompt. Persiste no asset com
    provider="agnes-studio" e o style usado (para regenerar mantendo identidade)."""
    bp = get_db_blueprint(bp_id)
    if not bp:
        raise ValueError("Blueprint não encontrado")
    slot_def = get_slot_def(bp, slot_key)
    if not slot_def:
        raise ValueError(f"Slot não encontrado: {slot_key}")

    res = await _generate_agnes_cover(bp, slot_def, style_id)
    style_id = res.get("style_id") or "moderno"
    title = res.get("title") or slot_def.get("prompt") or "Produto"
    width = int(slot_def.get("width") or 1200)
    height = int(slot_def.get("height") or 630)

    assets = dict(bp.get("assets") or {})
    new_asset = {
        "url": res.get("cover_url") or "",
        "super_prompt": f"Capa editorial Agnes Studio (estilo {style_id}): {title}",
        "provider": "agnes-studio",
        "source": "ai",
        "width": res.get("width") or width,
        "height": res.get("height") or height,
        "agnes_style": style_id,
    }
    new_asset["history"] = _snapshot_into_history(assets, slot_key, new_asset)
    assets[slot_key] = new_asset
    update_db_blueprint(bp_id, assets=assets)
    return {"slot": slot_key, **assets[slot_key]}


async def generate_agnes_variants(bp_id: str, slot_key: str,
                                  styles: Optional[List[str]] = None) -> Dict[str, Any]:
    """Gera N variantes do slot (um arquivo por estilo) SEM persistir no asset
    — a UI compara lado a lado e aplica a escolhida via apply_agnes_variant."""
    bp = get_db_blueprint(bp_id)
    if not bp:
        raise ValueError("Blueprint não encontrado")
    slot_def = get_slot_def(bp, slot_key)
    if not slot_def:
        raise ValueError(f"Slot não encontrado: {slot_key}")

    styles = [s for s in (styles or ["moderno", "elegante", "tech", "minimal", "dark-gold"]) if s]
    variants: List[Dict[str, Any]] = []
    for st in styles:
        try:
            res = await _generate_agnes_cover(bp, slot_def, st)
            variants.append({
                "style_id": st,
                "cover_url": res.get("cover_url") or "",
                "filename": res.get("filename") or "",
                "width": res.get("width"),
                "height": res.get("height"),
            })
        except Exception as e:  # noqa: BLE001
            variants.append({"style_id": st, "error": str(e)})
    return {"slot": slot_key, "variants": variants}


async def apply_agnes_variant(bp_id: str, slot_key: str, filename: str,
                              style_id: str = "moderno") -> Dict[str, Any]:
    """Aplica uma variante já gerada (arquivo em outputs/agnes) ao asset do slot
    sem regenerar — o comparador escolhe e esta função persiste."""
    bp = get_db_blueprint(bp_id)
    if not bp:
        raise ValueError("Blueprint não encontrado")
    slot_def = get_slot_def(bp, slot_key)
    if not slot_def:
        raise ValueError(f"Slot não encontrado: {slot_key}")
    if not filename or ".." in filename or "/" in filename or "\\" in filename or not filename.lower().endswith(".png"):
        raise ValueError("filename inválido")

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "outputs", "agnes")
    if not os.path.isfile(os.path.join(out_dir, filename)):
        raise ValueError("Variante não encontrada em outputs/agnes")

    from modules.art_director import VIBES
    valid_styles = ("moderno", "elegante", "tech", "minimal", "dark-gold") + tuple(VIBES.keys())
    style_id = style_id if style_id in valid_styles else "moderno"
    assets = dict(bp.get("assets") or {})
    new_asset = {
        "url": f"/outputs/agnes/{filename}",
        "super_prompt": f"Capa editorial Agnes Studio (estilo {style_id})",
        "provider": "agnes-studio",
        "source": "ai",
        "width": int(slot_def.get("width") or 1200),
        "height": int(slot_def.get("height") or 630),
        "agnes_style": style_id,
    }
    new_asset["history"] = _snapshot_into_history(assets, slot_key, new_asset)
    assets[slot_key] = new_asset
    update_db_blueprint(bp_id, assets=assets)
    return {"slot": slot_key, **assets[slot_key]}


async def upload_asset(bp_id: str, slot_key: str, data_url: str) -> Dict[str, Any]:
    """Salva upload manual de imagem no slot (data URL base64)."""
    import base64

    bp = get_db_blueprint(bp_id)
    if not bp:
        raise ValueError("Blueprint não encontrado")
    slot_def = get_slot_def(bp, slot_key)
    if not slot_def:
        raise ValueError(f"Slot não encontrado: {slot_key}")

    if not data_url or "," not in data_url:
        raise ValueError("data_url inválido")
    header, b64 = data_url.split(",", 1)
    mime = header.replace("data:", "").replace(";base64", "") or "image/png"
    ext = "png" if "png" in mime else ("webp" if "webp" in mime else "jpg")

    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "blueprints", bp_id
    )
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{slot_key}.{ext}"
    filepath = os.path.join(out_dir, filename)
    with open(filepath, "wb") as f:
        f.write(base64.b64decode(b64))

    assets = dict(bp.get("assets") or {})
    new_asset = {
        "url": f"/outputs/blueprints/{bp_id}/{filename}",
        "super_prompt": (assets.get(slot_key) or {}).get("super_prompt")
        or (slot_def.get("prompt") or ""),
        "provider": "upload",
        "source": "upload",
        "width": int(slot_def.get("width") or 1200),
        "height": int(slot_def.get("height") or 630),
    }
    new_asset["history"] = _snapshot_into_history(assets, slot_key, new_asset)
    assets[slot_key] = new_asset
    update_db_blueprint(bp_id, assets=assets)
    return {"slot": slot_key, **assets[slot_key]}


# ── Estágio 6 · PUBLICAÇÃO (ponte Adm → Clube) ───────────────────────────────

def _funil_child_payload(child: Dict[str, Any], assets: Dict[str, Any], slot_key: str,
                         description: str = "") -> Dict[str, Any]:
    img = (assets.get(slot_key) or {}).get("url") or ""
    return {
        "name": child.get("name"),
        "price_cents": child.get("price_cents") or 0,
        "resource_type": "link",
        "external_link": "/checkout",
        "image_url": img or None,
        "description": description or None,
    }


def _main_product_payload(bp: Dict[str, Any], content: Dict[str, Any], assets: Dict[str, Any],
                          upsell_id: Optional[int], downsell_id: Optional[int]) -> Dict[str, Any]:
    fund = content.get("fundacao") or {}
    conteudo = content.get("conteudo") or {}
    funil = content.get("funil") or {}
    config = bp.get("config") or {}
    slug = fund.get("slug") or config.get("slug") or "produto"

    # Artefato principal: primeiro não-blog concluído
    main = None
    for a in conteudo.get("artifacts") or []:
        if a.get("format") != "blog" and a.get("status") == "completed" and a.get("external_link"):
            main = a
            break

    payload: Dict[str, Any] = {
        "name": fund.get("name") or bp.get("theme"),
        "slug": slug,
        "description": fund.get("description") or "",
        "price_cents": bp.get("price_cents") or 0,
        "resource_type": "link",
        "external_link": (main or {}).get("external_link") or "/checkout",
        "image_url": (assets.get("product_image") or {}).get("url") or None,
        "youtube_video_url": config.get("youtube_video_url")
        or (content.get("vsl") or {}).get("video_url") or None,
        "category": config.get("category") or None,
    }
    ob = funil.get("order_bump")
    if ob:
        payload.update({
            "has_extra_service": 1,
            "extra_service_title": ob.get("title"),
            "extra_service_price_cents": ob.get("price_cents") or 0,
            "extra_service_description": ob.get("description") or None,
        })
    if upsell_id:
        payload["upsell_product_id"] = upsell_id
    if downsell_id:
        payload["downsell_product_id"] = downsell_id
    return payload


async def publish_blueprint(bp_id: str) -> Dict[str, Any]:
    """Estágio 6 — Publica o blueprint no Clube via ponte, com log por etapa.

    Ordem: 1) filhos (upsell/downsell) → 2) produto principal (com ids da
    esteira) → 3) blog/banners (sync-blog) → 4) landing (CLI) → 5) área de
    membros (member-course).
    """
    from modules.clube_bridge import (
        bridge_import_product, bridge_sync_blog, bridge_member_course, cli_create_landing,
    )

    bp = get_db_blueprint(bp_id)
    if not bp:
        raise ValueError(f"Blueprint não encontrado: {bp_id}")

    content = dict(bp.get("content") or {})
    assets = dict(bp.get("assets") or {})
    funil = content.get("funil") or {}
    publish_log: Dict[str, Any] = {}
    update_db_blueprint(bp_id, status="publishing", publish_log=publish_log)

    def _log(step: str, status: str, detail: str = "", **extra) -> None:
        publish_log[step] = {"status": status, "detail": detail[:400], "ts": datetime.utcnow().isoformat(), **extra}
        update_db_blueprint(bp_id, publish_log=dict(publish_log))

    try:
        # 1. Filhos da esteira (upsell/downsell) — criados primeiro
        upsell_id: Optional[int] = None
        downsell_id: Optional[int] = None
        if funil.get("upsell"):
            r = await bridge_import_product(
                _funil_child_payload(funil["upsell"], assets, "upsell_image",
                                     description=f"Oferta exclusiva pós-compra: {funil['upsell'].get('name')}"))
            if r.get("success") and r.get("product_id"):
                upsell_id = int(r["product_id"])
                _log("upsell", "ok", f"Produto de upsell criado (id {upsell_id})")
            else:
                _log("upsell", "failed", r.get("error") or "Falha ao criar upsell")
        if funil.get("downsell"):
            r = await bridge_import_product(
                _funil_child_payload(funil["downsell"], assets, "downsell_image",
                                     description=f"Oferta de downsell: {funil['downsell'].get('name')}"))
            if r.get("success") and r.get("product_id"):
                downsell_id = int(r["product_id"])
                _log("downsell", "ok", f"Produto de downsell criado (id {downsell_id})")
            else:
                _log("downsell", "failed", r.get("error") or "Falha ao criar downsell")

        # 2. Produto principal
        main_payload = _main_product_payload(bp, content, assets, upsell_id, downsell_id)
        r = await bridge_import_product(main_payload)
        if not r.get("success"):
            _log("produto", "failed", r.get("error") or "Falha ao criar produto")
            update_db_blueprint(bp_id, status="failed", publish_log=dict(publish_log))
            return {"bp_id": bp_id, "status": "failed", "publish_log": publish_log}
        product_id = r.get("product_id")
        product_slug = r.get("slug") or main_payload.get("slug")
        _log("produto", "ok", f"Produto criado (id {product_id}, /product/{product_slug})", product_id=product_id, slug=product_slug)

        # 2b. Combo/pacote nativo (se habilitado no funil)
        bundle = funil.get("bundle")
        if bundle and bundle.get("enabled"):
            # Itens do bundle: produto principal + upsell/downsell (conforme config)
            bundle_items: list = [int(product_id)] if product_id else []
            bundle_parts: list = []
            prices: list = []
            bundle_parts.append({"name": main_payload["name"], "price_cents": bp.get("price_cents") or 0})
            prices.append(bp.get("price_cents") or 0)
            if bundle.get("include_upsell") and funil.get("upsell") and upsell_id:
                bundle_items.append(int(upsell_id))
                bundle_parts.append({"name": funil["upsell"]["name"], "price_cents": funil["upsell"]["price_cents"] or 0})
                prices.append(funil["upsell"]["price_cents"] or 0)
            if bundle.get("include_downsell") and funil.get("downsell") and downsell_id:
                bundle_items.append(int(downsell_id))
                bundle_parts.append({"name": funil["downsell"]["name"], "price_cents": funil["downsell"]["price_cents"] or 0})
                prices.append(funil["downsell"]["price_cents"] or 0)

            if len(bundle_items) >= 2:
                discount = bundle.get("discount_pct") or 0
                total = sum(prices)
                bundle_price = int(total * (1 - discount / 100.0))
                bundle_name = bundle.get("name") or f"Pacote {main_payload['name']}"
                bundle_desc = "Este pacote inclui: " + ", ".join(p["name"] for p in bundle_parts) + "."
                bundle_payload = {
                    "name": bundle_name,
                    "slug": bundle.get("slug") or None,
                    "price_cents": bundle_price,
                    "resource_type": "link",
                    "external_link": main_payload.get("external_link") or "/checkout",
                    "image_url": main_payload.get("image_url"),
                    "description": bundle_desc,
                    "category": main_payload.get("category"),
                    "bundle_items": bundle_items,
                }
                rb = await bridge_import_product(bundle_payload)
                if rb.get("success") and rb.get("product_id"):
                    bundle_id = int(rb["product_id"])
                    bundle_slug = rb.get("slug") or ""
                    content["funil"] = {**funil, "bundle": {
                        **bundle, "product_id": bundle_id, "slug": bundle_slug,
                        "items": bundle_items, "price_cents": bundle_price,
                        "total_without_discount": total,
                    }}
                    update_db_blueprint(bp_id, content=content)
                    _log("bundle", "ok",
                         f"Combo criado (id {bundle_id}, R$ {bundle_price / 100:.2f}, {len(bundle_items)} itens, -{discount}%)",
                         product_id=bundle_id, slug=bundle_slug, items=bundle_items)
                else:
                    _log("bundle", "failed", rb.get("error") or "Falha ao criar combo")
            else:
                _log("bundle", "skipped", "Combo precisa de ao menos 2 produtos")
        else:
            _log("bundle", "skipped", "Combo desabilitado no funil")

        # 3. Blog + banners (se houver posts)
        conteudo = content.get("conteudo") or {}
        blog_artifacts = [a for a in conteudo.get("artifacts") or [] if a.get("format") == "blog"]
        if blog_artifacts:
            # Artigos do canal do blog ficam no Adm; sincroniza os slugs/capas do artefato
            sync_payload = {
                "product_slug": product_slug,
                "posts": [
                    {"title": a.get("title") or "", "slug": a.get("slug") or "", "cover_image": a.get("cover_url") or "", "content": a.get("content") or ""}
                    for a in blog_artifacts if a.get("slug")
                ],
                "ads": [
                    {"name": f"Banner {main_payload['name']} Sidebar", "placement": "sidebar", "type": "image",
                     "image_url": (assets.get("blog_banner_sidebar") or {}).get("url") or "",
                     "link_url": f"/product/{product_slug}", "weight": 10},
                    {"name": f"Banner {main_payload['name']} Inline", "placement": "post_inline", "type": "image",
                     "image_url": (assets.get("blog_banner_inline") or {}).get("url") or "",
                     "link_url": f"/product/{product_slug}", "weight": 5},
                ],
            }
            r = await bridge_sync_blog(sync_payload)
            if r.get("success"):
                _log("blog", "ok", f"Blog sincronizado: {r.get('summary', {}).get('posts_inserted', 0)} posts, {r.get('summary', {}).get('ads_created', 0)} banners")
            else:
                _log("blog", "failed", r.get("error") or "Falha ao sincronizar blog")
        else:
            _log("blog", "skipped", "Blueprint sem formato blog")

        # 4. Landing via CLI
        landing = content.get("landing") or {}
        blocks = landing.get("blocks") or []
        if blocks:
            r = await cli_create_landing({
                "title": main_payload["name"],
                "slug": product_slug,
                "status": "published",
                "blocks": blocks,
            })
            if r.get("success"):
                _log("landing", "ok", f"Landing em /p/{r.get('slug') or product_slug}", public_url=r.get("public_url"))
                landing["published"] = True
                landing["public_url"] = r.get("public_url") or f"/p/{product_slug}"
                content["landing"] = landing
                update_db_blueprint(bp_id, content=content)
            else:
                _log("landing", "failed", r.get("error") or "Falha ao criar landing")
        else:
            _log("landing", "skipped", "Sem blocos de landing")

        # 5. Área de membros (curso)
        curso = next((a for a in conteudo.get("artifacts") or [] if a.get("format") == "curso" and a.get("status") == "completed"), None)
        if curso:
            r = await bridge_member_course({
                "title": curso.get("title") or main_payload["name"],
                "description": main_payload.get("description") or "",
                "cover_image": (assets.get("member_cover") or {}).get("url") or None,
                "price_cents": curso.get("price_cents") or 0,
                "published": 1,
                "lessons": [],
            })
            if r.get("success"):
                _log("membros", "ok", f"Curso na área de membros (id {r.get('course_id')})")
            else:
                _log("membros", "failed", r.get("error") or "Falha ao criar curso na área de membros")
        else:
            _log("membros", "skipped", "Blueprint sem curso")

        update_db_blueprint(bp_id, status="published", publish_log=dict(publish_log))
        if bp_id in BLUEPRINT_TASKS:
            BLUEPRINT_TASKS[bp_id].update({"status": "published", "stage": "publicacao"})
        return {"bp_id": bp_id, "status": "published", "product_id": product_id, "product_slug": product_slug, "publish_log": publish_log}

    except Exception as e:  # noqa: BLE001
        _log("erro", "failed", str(e))
        update_db_blueprint(bp_id, status="failed", publish_log=dict(publish_log))
        return {"bp_id": bp_id, "status": "failed", "publish_log": publish_log}
