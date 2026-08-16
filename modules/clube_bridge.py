"""
Clube Bridge — Camada única de comunicação Adm → DezafiraClube.

Centraliza as chamadas da ponte (import-product, sync-blog, member-course)
e da CLI API do Clube (landing-pages) usadas pelo Blueprint e pelas fábricas.

Auth:
  - Ponte: header `x-import-key` == IMPORT_API_KEY do Clube (CLUBE_IMPORT_KEY no Adm)
  - CLI:   header `Authorization: Bearer CLI_TOKEN` (token gerado em admin/cli do Clube)
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


def clube_base_url() -> str:
    return os.getenv("CLUBE_PUBLIC_URL", "https://www.dezafira.com.br").rstrip("/")


def import_key() -> str:
    return os.getenv("CLUBE_IMPORT_KEY", "")


def cli_token() -> str:
    return os.getenv("CLI_TOKEN", "")


def _import_headers() -> Dict[str, str]:
    return {"Content-Type": "application/json", "x-import-key": import_key()}


async def _post(path: str, payload: Dict[str, Any], headers: Dict[str, str],
                timeout: float = 60.0) -> Dict[str, Any]:
    """POST na API do Clube com tratamento uniforme de erro."""
    if not import_key() and "x-import-key" in headers:
        return {"success": False, "error": "CLUBE_IMPORT_KEY não configurado no Adm."}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{clube_base_url()}{path}", json=payload, headers=headers)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:300]}
        if r.status_code in (200, 201):
            return {"success": True, **data}
        return {"success": False, "error": data.get("error") or data.get("detail") or f"Clube HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Falha ao conectar no Clube: {str(e)}"}


async def bridge_import_product(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/import/product — cria produto no catálogo do Clube."""
    return await _post("/api/import/product", payload, _import_headers())


async def bridge_sync_blog(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/import/sync-blog — cria posts + banners + vínculo de produto."""
    return await _post("/api/import/sync-blog", payload, _import_headers())


async def bridge_member_course(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/import/member-course — cria curso/aulas na área de membros do Clube."""
    return await _post("/api/import/member-course", payload, _import_headers())


async def cli_create_landing(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/cli/landing-pages — cria/publica landing no Clube (Bearer CLI_TOKEN)."""
    token = cli_token()
    if not token:
        return {"success": False, "error": "CLI_TOKEN não configurado no Adm (gere em admin/cli do Clube)."}
    return await _post(
        "/api/cli/landing-pages",
        payload,
        {"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )


def backend_url() -> str:
    """URL pública do backend Adm — usada nos links de entrega dos produtos."""
    return os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
