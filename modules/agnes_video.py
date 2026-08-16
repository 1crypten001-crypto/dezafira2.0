"""Agnes AI — Geração de VÍDEO (agnes-video-v2.0).

A assinatura Agnes (plano com cota diária) inclui vídeo além de imagens.
API OpenAI-compatível:
  POST /v1/videos        → cria task assíncrona  {id, status: queued, ...}
  GET  /v1/videos/{task} → status da task        {status, progress, url?}

Entrada de imagem (campo `image`): URL pública http(s) **ou** base64 válido
("image must be a public http(s) URL or valid base64 image data.").

Uso:
    from modules.agnes_video import agnes_video_generate, agnes_video_status
    task = await agnes_video_generate("câmera lenta...", image_b64_or_url)
    # ... polling ...
    final = await agnes_video_status(task["task_id"])
"""
import asyncio
import base64
import os
import time
from typing import Any, Dict, Optional

import httpx

AGNES_VIDEO_API_KEY = os.getenv("AGNES_API_KEY", "").strip()
AGNES_VIDEO_BASE = os.getenv("AGNES_VIDEO_BASE", "https://apihub.agnes-ai.com").rstrip("/")
AGNES_VIDEO_MODEL = os.getenv("AGNES_VIDEO_MODEL", "agnes-video-v2.0")

_TIMEOUT = httpx.Timeout(60.0, connect=20.0)


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {AGNES_VIDEO_API_KEY}",
        "Content-Type": "application/json",
    }


def image_to_base64(path_or_bytes, mime: str = "image/png") -> str:
    """Converte um arquivo local em data URL base64 (aceita caminho ou bytes)."""
    if isinstance(path_or_bytes, bytes):
        raw = path_or_bytes
    else:
        with open(path_or_bytes, "rb") as f:
            raw = f.read()
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


async def agnes_video_generate(
    prompt: str,
    image: Optional[str] = None,
    model: Optional[str] = None,
    **extra,
) -> Dict[str, Any]:
    """Dispara a geração de vídeo (assíncrona). Retorna a task dict.

    `image`: URL pública http(s) OU base64/data URL. Obrigatório para
    image-to-video; sem ele o modelo anima a partir do prompt (se suportar).
    """
    if not AGNES_VIDEO_API_KEY:
        return {"error": "AGNES_API_KEY não configurado no Adm."}
    if isinstance(image, (bytes, bytearray)):
        image = image_to_base64(bytes(image))
    elif image and not (image.startswith("http") or image.startswith("data:")):
        image = image_to_base64(image)
    payload: Dict[str, Any] = {
        "model": model or AGNES_VIDEO_MODEL,
        "prompt": prompt[:2000],
    }
    if image:
        payload["image"] = image
    for k in ("duration", "fps", "motion", "aspect_ratio", "negative_prompt"):
        if extra.get(k) is not None:
            payload[k] = extra[k]
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{AGNES_VIDEO_BASE}/v1/videos", headers=_headers(), json=payload
            )
        if r.status_code == 200:
            data = r.json()
            task_id = data.get("task_id") or data.get("id") or data.get("video_id") or ""
            return {
                "task_id": task_id,
                "status": data.get("status", "queued"),
                "progress": data.get("progress", 0),
                "raw": data,
            }
        return {"error": f"Agnes vídeo HTTP {r.status_code}: {r.text[:300]}"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"Agnes vídeo erro: {e}"}


async def agnes_video_status(task_id: str) -> Dict[str, Any]:
    """Consulta o status da task de vídeo (polling)."""
    if not AGNES_VIDEO_API_KEY:
        return {"error": "AGNES_API_KEY não configurado no Adm."}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(
                f"{AGNES_VIDEO_BASE}/v1/videos/{task_id}", headers=_headers()
            )
        if r.status_code == 200:
            data = r.json()
            # Formato comum de conclusão: status completed + url/video_url/output
            url = (
                data.get("url")
                or data.get("video_url")
                or data.get("output")
                or (data.get("data") or {}).get("url")
                or ((data.get("metadata") or {}).get("url") or "")
                or ""
            )
            return {
                "task_id": task_id,
                "status": data.get("status", ""),
                "progress": data.get("progress", 0),
                "url": url,
                "raw": data,
            }
        return {"error": f"Agnes status HTTP {r.status_code}: {r.text[:300]}"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"Agnes status erro: {e}"}


async def agnes_video_generate_and_wait(
    prompt: str,
    image: Optional[str] = None,
    poll_interval: float = 8.0,
    timeout: float = 600.0,
    on_progress=None,
    **extra,
) -> Dict[str, Any]:
    """Gera e faz polling até concluir (ou timeout). Nunca levanta: devolve dict.

    `on_progress(status_dict)` é chamado a cada poll (útil para logs/UI).
    """
    task = await agnes_video_generate(prompt, image=image, **extra)
    if task.get("error") or not task.get("task_id"):
        return task
    task_id = task["task_id"]
    started = time.time()
    while time.time() - started < timeout:
        st = await agnes_video_status(task_id)
        if st.get("error"):
            return st
        status = (st.get("status") or "").lower()
        if on_progress:
            try:
                on_progress(st)
            except Exception:  # noqa: BLE001
                pass
        if status in ("completed", "succeeded", "done", "success"):
            if st.get("url"):
                st["video_id"] = task_id
                return st
            return {**st, "error": "Task concluída sem URL de vídeo"}
        if status in ("failed", "error", "cancelled", "canceled"):
            return {**st, "error": f"Task de vídeo terminou com status '{status}'"}
        await asyncio.sleep(poll_interval)
    return {**task, "error": f"Timeout aguardando vídeo ({int(timeout)}s)"}


async def agnes_download_video(url: str, dest: str, timeout: float = 300.0) -> Optional[str]:
    """Baixa o MP4 (ou qualquer asset) para `dest`. Retorna dest ou None."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            r = await client.get(url, follow_redirects=True)
        if r.status_code == 200 and r.content:
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            with open(dest, "wb") as f:
                f.write(r.content)
            return dest
        print(f"[AgnesVideo] Download HTTP {r.status_code}")
    except Exception as e:  # noqa: BLE001
        print(f"[AgnesVideo] Download erro: {e}")
    return None
