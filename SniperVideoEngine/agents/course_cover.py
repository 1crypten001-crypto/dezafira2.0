"""
Cover — Agente de capa e thumbnail para cursos.
Usa a cascade de imagens existente (FLUX/Gemini/Pexels/Unsplash/SVG).
"""
import os
import httpx
from agents.llm import query_llm


class CourseCover:
    """Gera capas e thumbnails para cursos."""

    async def generate_cover(self, title: str, topic: str,
                              style: str = "moderno") -> str:
        """
        Gera cover image do curso.
        Cascade: Pollinations FLUX → Gemini Imagen → Pexels → SVG placeholder.
        Retorna: URL ou path local da imagem.
        """
        prompt = await self._build_cover_prompt(title, topic, style)

        # 1. Pollinations FLUX (gratis, sem key)
        try:
            path = await self._pollinations_generate(prompt)
            if path:
                return path
        except Exception:
            pass

        # 2. Gemini Imagen
        try:
            path = await self._gemini_generate(prompt)
            if path:
                return path
        except Exception:
            pass

        # 3. Pexels (busca por foto stock)
        try:
            url = await self._pexels_search(topic)
            if url:
                return url
        except Exception:
            pass

        # 4. SVG placeholder (fallback absoluto)
        return self._svg_placeholder(title, topic)

    async def _build_cover_prompt(self, title: str, topic: str,
                                   style: str) -> str:
        """Construi prompt detalhado para a capa."""
        resp = await query_llm([
            {"role": "system", "content": (
                "Gere um prompt de imagem curto (max 100 palavras) para uma capa de curso online. "
                "O prompt deve descrever uma cena visual profissional e atrativa. "
                "Retorne APENAS o prompt, sem aspas, sem pontuacao extra."
            )},
            {"role": "user", "content": (
                f"Curso: {title}\nTopico: {topic}\nEstilo: {style}\n"
                f"Gere o prompt visual para a capa."
            )},
        ])
        return resp.strip()

    async def _pollinations_generate(self, prompt: str) -> str:
        """Gera imagem via Pollinations FLUX (gratis)."""
        import uuid as _uuid
        encoded = prompt.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&seed={_uuid.uuid4().hex[:8]}&width=1280&height=720"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 1000:
                os.makedirs("outputs", exist_ok=True)
                filename = f"outputs/course_cover_{_uuid.uuid4().hex[:8]}.png"
                with open(filename, "wb") as f:
                    f.write(resp.content)
                return filename
        return None

    async def _gemini_generate(self, prompt: str) -> str:
        """Gera imagem via Gemini Imagen."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        import uuid as _uuid
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": f"Generate an image: {prompt}"}]}],
                    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        import base64
                        img_data = base64.b64decode(part["inlineData"]["data"])
                        os.makedirs("outputs", exist_ok=True)
                        filename = f"outputs/course_cover_{_uuid.uuid4().hex[:8]}.png"
                        with open(filename, "wb") as f:
                            f.write(img_data)
                        return filename
        return None

    async def _pexels_search(self, query: str) -> str:
        """Busca imagem stock no Pexels."""
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return None
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": api_key},
                params={"query": query, "per_page": 1, "orientation": "landscape"},
            )
            if resp.status_code == 200:
                data = resp.json()
                photos = data.get("photos", [])
                if photos:
                    return photos[0]["src"]["large2x"]
        return None

    def _svg_placeholder(self, title: str, topic: str) -> str:
        """Gera SVG placeholder como fallback absoluto."""
        colors = ["#1E3A5F", "#2563EB", "#7C3AED", "#059669", "#DC2626"]
        color = hash(topic) % len(colors)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">
  <rect width="1280" height="720" fill="{colors[color]}"/>
  <text x="640" y="320" text-anchor="middle" fill="white" font-size="48" font-family="Arial">{title[:50]}</text>
  <text x="640" y="400" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="24" font-family="Arial">Curso Online</text>
</svg>'''
        os.makedirs("outputs", exist_ok=True)
        import uuid as _uuid
        filename = f"outputs/course_cover_{_uuid.uuid4().hex[:8]}.svg"
        with open(filename, "w") as f:
            f.write(svg)
        return filename

    async def generate_thumbnail(self, title: str, topic: str) -> str:
        """Gera thumbnail (versao menor da cover)."""
        return await self.generate_cover(title, topic, style="thumbnail")


# Singleton
course_cover = CourseCover()
