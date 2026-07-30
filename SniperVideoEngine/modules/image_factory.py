"""
ImageFactory — Motor de Geração de Imagens para Artigos.

Gera imagens de destaque para artigos de blog usando:
  1. Pexels API (primário — chave do .env)
  2. Unsplash (fallback gratuito, sem chave)
  3. Placeholder (último recurso)

Uso:
    agent = ImageGeneratorAgent()
    img = await agent.generate(prompt="Jesus ensinando", style="blog")
    print(img["image_url"])
"""
import os
import httpx
import random
import re
from dotenv import load_dotenv
load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")


class ImageGeneratorAgent:
    """Gera imagens para artigos usando Pexels como primário e Unsplash como fallback."""

    def __init__(self):
        self.last_provider = None
        self.last_url = None

    async def generate(self, prompt: str, style: str = "blog", width: int = 1200, height: int = 630) -> dict:
        """
        Gera/reúne uma imagem para o prompt dado.

        Args:
            prompt: Descrição da imagem desejada (ex: "Jesus ensinando a multidão")
            style: Estilo visual (blog, book, course, thumbnail)
            width, height: Dimensões desejadas

        Returns:
            dict com image_url, alt_text, provider, credit
        """
        # Sanitizar prompt para busca
        search_query = self._sanitize_prompt(prompt)

        # Tentativa 1: Pexels
        if PEXELS_API_KEY:
            result = await self._search_pexels(search_query, width, height)
            if result and result.get("image_url"):
                self.last_provider = "pexels"
                return result

        # Tentativa 2: Unsplash
        result = await self._search_unsplash(search_query, width, height)
        if result and result.get("image_url"):
            self.last_provider = "unsplash"
            return result

        # Fallback ABSOLUTO: placeholder local (sempre funciona)
        self.last_provider = "placeholder"
        fallback_url = self._generate_fallback_placeholder(search_query, width, height)
        return {
            "image_url": fallback_url,
            "alt_text": prompt,
            "provider": "placeholder",
            "credit": "",
        }

    def _sanitize_prompt(self, prompt: str) -> str:
        """Converte prompt de artigo em termos de busca."""
        # Remove nomes de seções e palavras genéricas
        prompt = re.sub(r'(Introdução|Conclusão|Seção|Capítulo)\s*[:\-]?\s*', '', prompt, flags=re.IGNORECASE)
        # Pega as primeiras palavras significativas
        words = prompt.split()[:8]
        # Remove palavras muito genéricas
        stopwords = {'sobre', 'para', 'com', 'uma', 'uma', 'dos', 'das', 'nos', 'nas', 'em', 'de', 'da', 'do', 'que', 'é', 'como', 'por', 'ao', 'aos'}
        keywords = [w for w in words if w.lower() not in stopwords]
        return " ".join(keywords[:5]) or prompt

    async def _search_pexels(self, query: str, width: int, height: int) -> dict:
        """Busca imagem no Pexels."""
        try:
            orientation = "landscape" if width > height else "portrait"
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": PEXELS_API_KEY}
            params = {"query": query, "per_page": 5, "orientation": orientation, "page": random.randint(1, 10)}

            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(url, headers=headers, params=params)
                if r.status_code == 200:
                    data = r.json()
                    photos = data.get("photos", [])
                    if photos:
                        # Pega a primeira foto (ou aleatória entre as top 3)
                        photo = photos[0] if len(photos) == 1 else random.choice(photos[:3])
                        src = photo.get("src", {})
                        # Escolhe o tamanho adequado
                        img_url = src.get("large") or src.get("medium") or src.get("original")
                        return {
                            "image_url": img_url,
                            "alt_text": photo.get("alt", query),
                            "provider": "pexels",
                            "credit": f"Photo by {photo.get('photographer', 'Pexels')} on Pexels",
                            "photographer_url": photo.get("photographer_url", ""),
                            "pexels_url": photo.get("url", ""),
                        }
                elif r.status_code == 401:
                    print("[ImageFactory] Pexels: chave inválida")
                else:
                    print(f"[ImageFactory] Pexels: {r.status_code}")
        except Exception as e:
            print(f"[ImageFactory] Pexels error: {e}")
        return None

    async def _search_unsplash(self, query: str, width: int, height: int) -> dict:
        """Busca imagem no Unsplash (via API oficial, ou fallback placehold)."""
        try:
            headers = {}
            if UNSPLASH_ACCESS_KEY:
                headers["Authorization"] = f"Client-ID {UNSPLASH_ACCESS_KEY}"
                url = "https://api.unsplash.com/search/photos"
                params = {"query": query, "per_page": 3, "orientation": "landscape" if width > height else "portrait"}
                async with httpx.AsyncClient(timeout=15) as client:
                    r = await client.get(url, headers=headers, params=params)
                    if r.status_code == 200:
                        data = r.json()
                        results = data.get("results", [])
                        if results:
                            photo = results[0]
                            urls = photo.get("urls", {})
                            img_url = urls.get("regular") or urls.get("small")
                            return {
                                "image_url": img_url,
                                "alt_text": photo.get("alt_description", query),
                                "provider": "unsplash",
                                "credit": f"Photo by {photo.get('user', {}).get('name', 'Unsplash')} on Unsplash",
                                "photographer_url": photo.get("user", {}).get("links", {}).get("html", ""),
                            }
            # Fallback: Unsplash sem chave (via source.unsplash.com) - pode falhar, é normal
            return None
        except Exception as e:
            print(f"[ImageFactory] Unsplash error: {e}")
        return None

    async def generate_for_article(self, title: str, keywords: str = "", topic: str = "") -> dict:
        """
        Gera imagem ideal para um artigo de blog.
        Usa título + keywords para fazer a busca mais relevante.
        """
        # Constrói prompt combinado
        prompt_parts = [title]
        if keywords:
            kw_list = keywords.split(",")[:3]
            prompt_parts.extend(kw_list)
        if topic:
            prompt_parts.append(topic)

        search = " ".join(prompt_parts[:5])
        return await self.generate(prompt=search, style="blog")

    def _generate_fallback_placeholder(self, query: str, width: int, height: int) -> str:
        """Gera um placeholder local que SEMPRE funciona (SVG data URI)."""
        # Cores temáticas
        colors = [
            ("#1a1410", "#d4a853"),  # Dark + Gold
            ("#2a2219", "#f0d68a"),  # Dark2 + Gold light
            ("#3d3227", "#c0392b"),  # Text + Accent
            ("#8b2500", "#f0e8d5"),  # Accent + Cream
        ]
        bg, fg = random.choice(colors)
        
        # Texto para exibir no placeholder
        words = query.split()[:4]
        display_text = " ".join(words) if words else "Imagem"
        
        # Gera SVG como data URI (suportado em 100% dos navegadores)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="{bg}"/>
  <rect x="{(width-200)//2}" y="{(height-200)//2}" width="200" height="200" rx="100" fill="{fg}" opacity="0.15"/>
  <text x="{width//2}" y="{height//2-10}" font-family="serif" font-size="28" fill="{fg}" text-anchor="middle" font-weight="bold">{display_text}</text>
  <text x="{width//2}" y="{height//2+30}" font-family="sans-serif" font-size="14" fill="{fg}" text-anchor="middle" opacity="0.6">Dezafira Blog</text>
</svg>'''
        
        # Codifica como data URI (suportado em todos os navegadores)
        encoded = base64.b64encode(svg.encode('utf-8')).decode('ascii')
        return f"data:image/svg+xml;base64,{encoded}"

    def get_attribution_html(self, result: dict) -> str:
        """Retorna HTML de atribuição para a imagem."""
        provider = result.get("provider", "")
        credit = result.get("credit", "")

        if provider == "pexels":
            return f'<small style="font-size:10px;color:#7a6b5a">{credit}</small>'
        elif provider == "unsplash":
            return f'<small style="font-size:10px;color:#7a6b5a">{credit}</small>'
        return ""
