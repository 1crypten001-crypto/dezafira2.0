"""
Image Factory — Gera imagens para blogs, livros e cursos.
Usa Hugging Face Inference API (FLUX.1) + Pexels API (stock).
"""
import os
import httpx
from typing import Optional


class ImageGeneratorAgent:
    """Agente de imagens — unifica geracao IA + stock."""

    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")
        os.makedirs("outputs", exist_ok=True)

    async def generate_cover(self, title: str, topic: str, style: str = "classico") -> Optional[str]:
        """Gera capa de livro. Tenta FLUX.1 (HF) primeiro, depois Pexels como fallback."""
        # Tenta FLUX via Hugging Face
        prompt_map = {
            "classico": f"Professional book cover, {topic}, elegant classic design, gold accents, dark background, title '{title}', high quality, 4k, premium publishing",
            "moderno": f"Modern book cover design, {topic}, minimalist, vibrant colors, clean typography, title '{title}', high quality, 4k",
            "natureza": f"Book cover with natural elements, {topic}, earthy tones, warm lighting, title '{title}', high quality",
            "tipografico": f"Typography-focused book cover, {topic}, bold letters, solid colors, sophisticated, title '{title}', high quality",
        }
        prompt = prompt_map.get(style, prompt_map["classico"])
        if self.hf_token:
            url = await self._hf_generate(prompt, "black-forest-labs/FLUX.1-schnell")
            if url:
                return url
        # Fallback: Pexels
        return await self._pexels_search(f"{topic} book cover")

    async def generate_blog_image(self, topic: str, keywords: str = "") -> Optional[str]:
        """Gera imagem de destaque para blog. Tenta Pexels primeiro, depois FLUX."""
        # Tenta Pexels primeiro (fotos reais, mais adequadas)
        url = await self._pexels_search(topic)
        if url:
            return url
        # Fallback: FLUX
        prompt = f"Beautiful blog featured image, {topic}, warm lighting, professional photography, high quality, 4k"
        return await self._hf_generate(prompt, "black-forest-labs/FLUX.1-schnell")

    async def generate_course_thumbnail(self, title: str, topic: str) -> Optional[str]:
        """Gera thumbnail para curso. Tenta FLUX.1 (HF) primeiro, depois Pexels como fallback."""
        # Tenta FLUX via Hugging Face
        prompt = f"Course thumbnail, educational, {topic}, title '{title}', professional design, vibrant colors, high quality, 16:9"
        if self.hf_token:
            url = await self._hf_generate(prompt, "black-forest-labs/FLUX.1-schnell")
            if url:
                return url
        # Fallback: Pexels
        return await self._pexels_search(f"{topic} course")

    async def _hf_generate(self, prompt: str, model: str, width: int = 1024, height: int = 768) -> Optional[str]:
        """Gera imagem via Hugging Face Inference API."""
        if not self.hf_token:
            return None
        try:
            api_url = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {self.hf_token}", "Content-Type": "application/json"}
            payload = {"inputs": prompt, "parameters": {"width": width, "height": height}}
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    # Salva imagem como arquivo temporario
                    import uuid
                    filename = f"outputs/gen_{uuid.uuid4().hex[:8]}.png"
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    return f"/{filename}"
                print(f"[ImageAgent] HF error {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"[ImageAgent] HF exception: {str(e)}")
        return None

    async def _pexels_search(self, query: str, per_page: int = 3) -> Optional[str]:
        """Busca imagem gratuita no Pexels."""
        if not self.pexels_key:
            return None
        try:
            headers = {"Authorization": self.pexels_key}
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.pexels.com/v1/search",
                    headers=headers,
                    params={"query": query, "per_page": per_page, "orientation": "landscape"},
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("photos"):
                        return data["photos"][0]["src"]["large"]
        except Exception as e:
            print(f"[ImageAgent] Pexels error: {str(e)}")
        return None


# Singleton
image_agent = ImageGeneratorAgent()
