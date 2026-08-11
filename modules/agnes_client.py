"""
AgnesClient — cliente OpenAI-compativel para a Agnes AI (apihub.agnes-ai.com).
Gera imagens (modelo agnes-image-2.1-flash) com suporte a img2img (referencias)
e retry com backoff. Quando um output_path e informado, baixa a imagem gerada
e salva como PNG local; caso contrario, retorna os bytes crus.

Chave: AGNES_API_KEY do ambiente (.env). Nunca loga a chave.
"""
import asyncio
import base64
import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("agnes_client")
logger.setLevel(logging.INFO)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_IMAGE_MODEL = "agnes-image-2.1-flash"


class AgnesClient:
    """Cliente OpenAI-compatível para apihub.agnes-ai.com/v1 (imagens, $0)."""

    BASE_URL = "https://apihub.agnes-ai.com/v1"
    IMAGE_MODEL = _IMAGE_MODEL

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("AGNES_API_KEY", "")
        if not self.api_key:
            logger.warning("[AgnesClient] AGNES_API_KEY ausente — geracao Agnes indisponivel")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        ratio: str = "1:1",
        ref_images: list[str] | None = None,
        timeout: float = 90.0,
        output_path: str | None = None,
    ) -> str | None:
        """POST /images/generations → baixa a imagem e salva em output_path (PNG).

        Args:
            prompt: descricao da imagem a gerar.
            size: resolucao upscaled (ex.: '1024x1024').
            ratio: proporcao da imagem (1:1 | 16:9 | 9:16 | 3:4).
            ref_images: lista de URLs ou base64 (img2img — consistencia de identidade).
            timeout: timeout de rede em segundos.
            output_path: caminho local para salvar a imagem PNG.

        Returns:
            Caminho local do PNG salvo (se output_path definido) ou os bytes crus
            codificados (caso contrario). None em caso de falha.
        """
        if not self.api_key:
            return None
        body: dict = {
            "model": self.IMAGE_MODEL,
            "prompt": prompt[:4000],
            "size": size,
            "ratio": ratio,
        }
        if ref_images:
            body["image"] = ref_images

        url = f"{self.BASE_URL}/images/generations"
        for attempt in range(3):  # tentativa inicial + 2 retries
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, headers=self._headers(), json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    image_url = self._extract_url(data)
                    if not image_url:
                        logger.warning("[AgnesClient] Resposta 200 sem URL de imagem")
                        return await self._maybe_bytes(data)
                    return await self._download(image_url, output_path, timeout)
                if resp.status_code in _RETRYABLE_STATUS:
                    logger.warning("[AgnesClient] HTTP %s — retry %d/2", resp.status_code, attempt + 1)
                else:
                    logger.warning("[AgnesClient] HTTP %s: %s", resp.status_code, resp.text[:200])
                    return None
            except (httpx.HTTPError, asyncio.TimeoutError, OSError) as e:
                logger.warning("[AgnesClient] Falha na tentativa %d: %s", attempt + 1, e)
                if attempt == 2:
                    return None
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
        return None

    @staticmethod
    def _extract_url(data: dict) -> str | None:
        """Extrai a URL da imagem da resposta padrao OpenAI (/v1/images)."""
        for key in ("url", "urls", "image", "image_url", "data"):
            val = data.get(key)
            if isinstance(val, str) and (val.startswith("http") or val.startswith("/")):
                return val
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        for sub in ("url", "b64_json", "image_url"):
                            v = item.get(sub)
                            if isinstance(v, str) and v:
                                if sub == "url":
                                    return v
                                return v
        return None

    @staticmethod
    async def _maybe_bytes(data: dict) -> str | None:
        """Recupera bytes base64 direto da resposta, se o provedor retornar inline."""
        url = AgnesClient._extract_url(data)
        if url and (url.startswith("data:") or "base64" in url):
            return url
        b64 = data.get("b64_json") or data.get("image_base64")
        if b64:
            return "data:image/png;base64," + b64
        return None

    async def _download(self, image_url: str, output_path: str | None, timeout: float):
        """Baixa o PNG e salva em output_path, retornando bytes se nao houver caminho."""
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(image_url)
                if resp.status_code != 200:
                    logger.warning("[AgnesClient] Download HTTP %s", resp.status_code)
                    return None
                content = resp.content
        except (httpx.HTTPError, asyncio.TimeoutError, OSError) as e:
            logger.warning("[AgnesClient] Falha no download: %s", e)
            return None

        if output_path:
            dirname = os.path.dirname(output_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(output_path, "wb") as fh:
                fh.write(content)
            return output_path
        return content
