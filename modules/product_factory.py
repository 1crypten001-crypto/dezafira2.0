"""
Módulo product_factory — Motor ÚNICO de Fábrica de Produtos (Dezafira).

Consolida as pipelines de Ebook, App de Recorrência (mapa mental + miniapp)
e Curso numa única fachada com "receitas" por formato. Os endpoints antigos
(/api/v1/pipeline/run-*-factory) continuam funcionando; este módulo é o
caminho novo e único usado pelo frontend (Fábrica de Produtos).

Fluxo unificado:
  POST /api/v1/products/run   {format: ebook|app|curso, ...} -> task_id
  GET  /api/v1/products/task/{task_id}  -> status unificado
  GET  /api/v1/products/history         -> execuções de todas as fábricas
  GET  /api/v1/products                 -> catálogo unificado (todos os entregáveis)
  POST /api/v1/products/send-to-clube   -> ponte Adm -> Clube (reusa a ponte existente)

Formatos (receitas):
  ebook  -> EbookMacroPipeline (nomes, capas, capítulos)
  app    -> App de Recorrência: content_type = "mindmap" | "miniapp"
            (mapa mental = conteúdo + quiz; miniapp = PWA com drip content)
  curso  -> CourseMacroPipeline (módulos, aulas)
"""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Registro de tarefas unificado (cross-format)
# ---------------------------------------------------------------------------

PRODUCT_TASKS: Dict[str, Dict[str, Any]] = {}

# Aceita nomes antigos e novos; normaliza para os formatos canônicos
FORMAT_ALIASES = {
    "ebook": "ebook",
    "mindmap": "app",
    "miniapp": "app",
    "app": "app",
    "curso": "curso",
    "course": "curso",
}

FORMAT_LABELS = {
    "ebook": "Ebook",
    "app": "App de Recorrência",
    "curso": "Curso",
}

REQUIRED_FIELD = {
    "ebook": "niche",
    "app": "niche",
    "curso": "topic",
}


def _new_task(task_format: str, payload: Dict[str, Any]) -> str:
    task_id = f"prod_{uuid.uuid4().hex[:10]}"
    PRODUCT_TASKS[task_id] = {
        "task_id": task_id,
        "format": task_format,
        "format_label": FORMAT_LABELS.get(task_format, task_format),
        "payload": payload,
        "status": "starting",
    }
    return task_id


def _set_status(task_id: str, data: Dict[str, Any]) -> None:
    if task_id in PRODUCT_TASKS:
        PRODUCT_TASKS[task_id].update(data)


# ---------------------------------------------------------------------------
# Disparo das receitas (cada uma chama o motor de pipeline correspondente)
# ---------------------------------------------------------------------------

async def _run_ebook(task_id: str, payload: Dict[str, Any]) -> None:
    try:
        from modules.ebook_pipeline import run_ebook_macro_pipeline

        def _cb(tid, *args, **kwargs):
            data = args[3] if len(args) > 3 else {}
            if isinstance(data, dict):
                _set_status(task_id, data)

        result = await run_ebook_macro_pipeline(
            niche=payload.get("niche", ""),
            book_title=payload.get("title", ""),
            blog_channel_id=payload.get("blog_channel_id", ""),
            style_id=payload.get("style_id", "minimalista"),
            price_cents=payload.get("price_cents", 1700),
            target_chapters=payload.get("target_chapters", 8),
            task_id=task_id,
            on_progress=_cb,
        )
        _set_status(task_id, result or {"status": "completed"})
    except Exception as e:  # noqa: BLE001
        _set_status(task_id, {"status": "failed", "error": str(e)})


async def _run_mindmap(task_id: str, payload: Dict[str, Any]) -> None:
    try:
        from modules.mindmap_pipeline import run_mindmap_macro_pipeline

        def _cb(tid, *args, **kwargs):
            data = args[3] if len(args) > 3 else {}
            if isinstance(data, dict):
                _set_status(task_id, data)

        result = await run_mindmap_macro_pipeline(
            niche=payload.get("niche", ""),
            title=payload.get("title", ""),
            style_id=payload.get("style_id", "minimalista"),
            price_cents=payload.get("price_cents", 1990),
            task_id=task_id,
            on_progress=_cb,
        )
        _set_status(task_id, result or {"status": "completed"})
    except Exception as e:  # noqa: BLE001
        _set_status(task_id, {"status": "failed", "error": str(e)})


async def _run_miniapp(task_id: str, payload: Dict[str, Any]) -> None:
    """App de recorrência tipo miniapp: placeholder no banco + Sala de Agentes."""
    try:
        from modules.miniapp_factory import miniapp_factory
        from modules.database import create_db_miniapp, update_db_miniapp

        prompt = (payload.get("prompt") or payload.get("title") or "").strip() or "App de Recorrência"
        niche = payload.get("niche") or "Geral"

        provisional_slug = miniapp_factory._ensure_unique_slug(miniapp_factory._slug_from_prompt(prompt))
        placeholder = create_db_miniapp(app_name=prompt[:48], niche=niche, status="creating", slug=provisional_slug)
        app_id = placeholder["id"]
        _set_status(task_id, {"status": "creating", "app_id": app_id, "message": "Sala de Agentes iniciada"})

        try:
            await miniapp_factory.create_miniapp_with_room(prompt, niche, app_id=app_id)
            _set_status(task_id, {"status": "completed", "app_id": app_id})
        except Exception as e:  # noqa: BLE001
            update_db_miniapp(app_id, status="error", pwa_check=f'{{"error": "{str(e)[:500]}"}}')
            _set_status(task_id, {"status": "failed", "error": str(e)})
    except Exception as e:  # noqa: BLE001
        _set_status(task_id, {"status": "failed", "error": str(e)})


async def _run_curso(task_id: str, payload: Dict[str, Any]) -> None:
    try:
        from modules.course_pipeline import run_course_macro_pipeline

        def _cb(tid, *args, **kwargs):
            data = args[3] if len(args) > 3 else {}
            if isinstance(data, dict):
                _set_status(task_id, data)

        result = await run_course_macro_pipeline(
            topic=payload.get("topic", ""),
            course_title=payload.get("title", ""),
            difficulty=payload.get("difficulty", "iniciante"),
            price_cents=payload.get("price_cents", 0),
            target_modules=payload.get("target_modules", 4),
            lessons_per_module=payload.get("lessons_per_module", 4),
            task_id=task_id,
            on_progress=_cb,
        )
        _set_status(task_id, result or {"status": "completed"})
    except Exception as e:  # noqa: BLE001
        _set_status(task_id, {"status": "failed", "error": str(e)})


async def run_product(raw_format: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Dispara a receita do formato. Retorna {task_id, status, format}."""
    task_format = FORMAT_ALIASES.get((raw_format or "").lower(), "")
    if not task_format:
        raise ValueError(
            f"Formato inválido: {raw_format!r}. Use: ebook, app (mindmap/miniapp) ou curso."
        )

    required = REQUIRED_FIELD[task_format]
    if not (payload.get(required) or "").strip():
        raise ValueError(f"Campo obrigatório ausente para {task_format}: '{required}'")

    task_id = _new_task(task_format, payload)
    asyncio.create_task({
        "ebook": _run_ebook,
        "app": _run_app,
        "curso": _run_curso,
    }[task_format](task_id, payload))
    return {"task_id": task_id, "status": "starting", "format": task_format}


async def _run_app(task_id: str, payload: Dict[str, Any]) -> None:
    app_type = (payload.get("app_type") or payload.get("content_type") or "mindmap").lower()
    if app_type == "miniapp":
        await _run_miniapp(task_id, payload)
    else:
        await _run_mindmap(task_id, payload)


def product_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Status unificado: junta o registro do motor com o payload da tarefa."""
    task = PRODUCT_TASKS.get(task_id)
    if not task:
        return None
    return task


def product_history() -> Dict[str, Any]:
    """Execuções de todas as fábricas (persistidas no banco) + tarefas em memória."""
    runs: List[Dict[str, Any]] = []
    try:
        from modules.database import (
            get_db_course_pipeline_runs,
            get_db_ebook_pipeline_runs,
            get_db_mindmap_pipeline_runs,
        )

        for fmt, fn in (
            ("ebook", get_db_ebook_pipeline_runs),
            ("app", get_db_mindmap_pipeline_runs),
            ("curso", get_db_course_pipeline_runs),
        ):
            try:
                for run in fn() or []:
                    item = dict(run)
                    item["format"] = fmt
                    item["format_label"] = FORMAT_LABELS.get(fmt, fmt)
                    runs.append(item)
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass

    for task in PRODUCT_TASKS.values():
        runs.append(
            {
                "task_id": task.get("task_id"),
                "format": task.get("format"),
                "format_label": task.get("format_label"),
                "status": task.get("status"),
                "message": task.get("message", ""),
                "started_at": task.get("started_at"),
            }
        )
    runs.sort(key=lambda r: r.get("started_at") or r.get("created_at") or "", reverse=True)
    return {"runs": runs[:100]}


def product_catalog() -> Dict[str, Any]:
    """Catálogo unificado: tudo que as fábricas já produziram, pronto pra vender."""
    items: List[Dict[str, Any]] = []
    try:
        from modules.database import get_db_books, get_db_mindmaps, get_db_miniapps

        for book in get_db_books() or []:
            item = dict(book)
            item["format"] = "ebook"
            item["format_label"] = FORMAT_LABELS["ebook"]
            items.append(item)

        for mm in get_db_mindmaps() or []:
            item = dict(mm)
            item["format"] = "app"
            item["format_label"] = FORMAT_LABELS["app"]
            item["app_type"] = "mindmap"
            items.append(item)

        for app in get_db_miniapps() or []:
            item = dict(app)
            item["format"] = "app"
            item["format_label"] = FORMAT_LABELS["app"]
            item["app_type"] = "miniapp"
            items.append(item)
    except Exception:  # noqa: BLE001
        pass

    return {"products": items, "total": len(items)}


# ---------------------------------------------------------------------------
# Ponte Adm -> Clube (reusa a mesma lógica de /api/v1/clube/import-product)
# ---------------------------------------------------------------------------

async def send_product_to_clube(
    name: str,
    price_cents: int = 0,
    description: str = "",
    external_link: str = "",
    image_url: str = "",
    resource_type: str = "link",
) -> Dict[str, Any]:
    """Cria o produto no catálogo do Clube via ponte (/api/import/product)."""
    import httpx

    clube_url = os.getenv("CLUBE_PUBLIC_URL", "https://www.dezafira.com.br").rstrip("/")
    import_key = os.getenv("CLUBE_IMPORT_KEY", "")
    if not import_key:
        return {"success": False, "error": "CLUBE_IMPORT_KEY não configurado no Adm."}

    payload: Dict[str, Any] = {
        "name": name,
        "price_cents": price_cents,
        "resource_type": resource_type,
    }
    if description:
        payload["description"] = description
    if external_link:
        payload["external_link"] = external_link
    if image_url:
        payload["image_url"] = image_url

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.post(
                f"{clube_url}/api/import/product",
                json=payload,
                headers={"Content-Type": "application/json", "x-import-key": import_key},
            )
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            data = {"raw": r.text[:300]}
        if r.status_code in (200, 201):
            return {"success": True, **data}
        return {"success": False, "error": data.get("error") or f"Erro do Clube: HTTP {r.status_code}"}
    except Exception as e:  # noqa: BLE001
        return {"success": False, "error": f"Falha ao conectar no Clube: {str(e)}"}
