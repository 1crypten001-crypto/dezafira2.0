"""
ImageFactory — Motor de Geração de Imagens para Artigos.

Cascata de provedores:
  1. 🤖 FLUX (Pollinations.ai) — geração por IA, 100% gratuito, sem chave
  2. 🎨 Gemini Imagen (Google) — geração por IA, usa GEMINI_API_KEY do .env
  3. 🖼️ Pexels API — busca de fotos, usa PEXELS_API_KEY do .env
  4. 🖼️ Unsplash — busca de fotos, usa UNSPLASH_ACCESS_KEY do .env (opcional)
  5. 🎭 SVG Placeholder — fallback garantido, gerado localmente

NUNCA termina sem imagem. A cascata tenta cada provedor em ordem.
"""
import os
import base64
import httpx
import random
import re
import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Prompt de estilo visual por nicho
NICHE_STYLE_PROMPTS = {
    "cristao": "dramatic biblical scene, golden divine light, ethereal atmosphere, cinematic, 8k, hyperrealistic",
    "reino": "dramatic biblical scene, golden divine light, ethereal atmosphere, cinematic, 8k, hyperrealistic",
    "jesus": "spiritual scene, soft divine glow, peaceful atmosphere, photorealistic, cinematic lighting",
    "financ": "modern financial concept, clean 3D render, glassmorphism, blue gradient, professional, minimalist, 8k",
    "invest": "modern financial concept, clean 3D render, glassmorphism, blue gradient, professional, minimalist, 8k",
    "dinheiro": "money concept, elegant financial art, dark background with gold accents, 8k, cinematic",
    "saude": "health and wellness concept, bright clean aesthetic, modern medical, 8k",
    "default": "professional blog hero image, cinematic, 8k, hyperrealistic, beautiful composition",
}


def _get_niche_style(niche: str, title: str) -> str:
    """Detecta o nicho e retorna o prompt de estilo visual adequado."""
    combined = (niche + " " + title).lower()
    for key, style in NICHE_STYLE_PROMPTS.items():
        if key in combined:
            return style
    return NICHE_STYLE_PROMPTS["default"]


class ImageGeneratorAgent:
    """
    Gera imagens com cascata inteligente priorizando IA: Gemini Imagen -> Flux -> Pexels -> Unsplash -> SVG.
    Nunca retorna sem imagem.
    """

    def __init__(self):
        self.last_provider = None
        self.last_url = None

    async def _expand_prompt_with_llm(self, title: str, niche: str) -> str:
        """
        Usa o Gemini LLM para traduzir e expandir o título em um prompt
        de imagem detalhado, conceitual e fotográfico em inglês.
        """
        if not GEMINI_API_KEY:
            return f"Professional high-quality blog hero image, highly detailed, realistic, beautiful composition: {title}"
            
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
            
            system_instruction = (
                "You are an expert visual director and photographer. Your task is to translate and expand "
                "the given article title and niche into a highly descriptive image prompt in English.\n"
                "RULES:\n"
                "1. Output ONLY the raw prompt string in English (no json, no explanations, no markdown, no quotes).\n"
                "2. Focus on realistic photography, cinematic lighting (like rim light, volumetric lighting), "
                "composition (close-up, wide-angle), and rich textures.\n"
                "3. Crucial: The prompt MUST NOT contain any text, words, labels, signatures, or watermarks to be rendered.\n"
                "4. Keep it clean, modern, and aesthetic. Do not use generic words like 'photorealistic' or 'hyperrealistic', "
                "instead describe the details (e.g. 'sharp focus, fine details, natural textures')."
            )
            
            payload = {
                "contents": [{"parts": [{"text": f"Niche: {niche}\nArticle Title: {title}"}]}],
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200}
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(url, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        expanded = text.strip()
                        if expanded:
                            print(f"[ImageFactory] Prompt expandido com sucesso: {expanded}")
                            return expanded
                print(f"[ImageFactory] Falha ao chamar LLM para expandir prompt, HTTP {r.status_code}")
        except Exception as e:
            print(f"[ImageFactory] Erro ao expandir prompt via LLM: {e}")
            
        return f"Professional high-quality blog hero image, highly detailed, realistic, beautiful composition: {title}"

    async def generate_image_for_post(
        self,
        prompt_idea: str,
        niche: str = "",
        post_id: str = None,
        width: int = 1200,
        height: int = 630,
    ) -> dict:
        """
        Gera imagem para um post, com cascata completa de provedores.

        Returns:
            dict com image_url, provider, alt_text, credit
        """
        print(f"[ImageFactory] Expandindo prompt para: '{prompt_idea}' (Nicho: {niche})")
        expanded_prompt = await self._expand_prompt_with_llm(prompt_idea, niche)
        search_query = self._sanitize_for_search(prompt_idea)

        # === 1. Gemini Imagen (Google) ===
        if GEMINI_API_KEY:
            result = await self._gemini_imagen(expanded_prompt, width, height)
            if result:
                self.last_provider = "gemini"
                return result

        # === 2. FLUX via Pollinations.ai (IA gratuita) ===
        result = await self._flux_pollinations(expanded_prompt, width, height)
        if result:
            self.last_provider = "flux"
            return result

        # === 3. Pexels (busca de fotos) ===
        if PEXELS_API_KEY:
            result = await self._search_pexels(search_query, width, height)
            if result:
                self.last_provider = "pexels"
                return result

        # === 4. Unsplash (busca de fotos) ===
        result = await self._search_unsplash(search_query, width, height)
        if result:
            self.last_provider = "unsplash"
            return result

        # === 5. SVG Placeholder (NUNCA falha) ===
        self.last_provider = "placeholder"
        return {
            "image_url": self._generate_svg_placeholder(prompt_idea, width, height),
            "alt_text": prompt_idea,
            "provider": "placeholder",
            "credit": "Dezafira",
        }

    # ── método legado para compatibilidade ──────────────────────────────────
    async def generate(self, prompt: str, style: str = "blog", width: int = 1200, height: int = 630) -> dict:
        return await self.generate_image_for_post(prompt_idea=prompt, width=width, height=height)

    async def generate_for_article(self, title: str, keywords: str = "", topic: str = "", is_discover: bool = False) -> dict:
        combined = title
        if keywords:
            combined += " - Keywords: " + " ".join(keywords.split(",")[:3])
            
        width = 1200
        height = 675 if is_discover else 630
        
        niche_info = "Google Discover Viral" if is_discover else "Blog Post"
        return await self.generate_image_for_post(prompt_idea=combined, niche=niche_info, width=width, height=height)

    # ── PROVEDOR 1: FLUX via Pollinations.ai ────────────────────────────────

    async def _flux_pollinations(self, prompt: str, width: int, height: int) -> Optional[dict]:
        """
        Gera imagem via FLUX no Pollinations.ai (gratuito, sem chave).
        Endpoint: https://image.pollinations.ai/prompt/{encoded_prompt}?width=W&height=H&model=flux
        """
        try:
            import urllib.parse
            clean_prompt = re.sub(r"[^\w\s,.-]", "", prompt)[:500]
            encoded = urllib.parse.quote(clean_prompt)
            # Usa um seed aleatório para variar a imagem gerada
            seed = random.randint(1, 999999)
            url = (
                f"https://image.pollinations.ai/prompt/{encoded}"
                f"?width={width}&height={height}&model=flux&seed={seed}&nologo=true"
            )
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                r = await client.get(url)
                if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
                    return {
                        "image_url": str(r.url),
                        "alt_text": clean_prompt[:150],
                        "provider": "flux",
                        "credit": "Gerada por FLUX (Pollinations.ai)",
                    }
                print(f"[ImageFactory/Flux] HTTP {r.status_code}")
        except Exception as e:
            print(f"[ImageFactory/Flux] Erro: {e}")
        return None

    # ── PROVEDOR 2: Gemini Imagen ────────────────────────────────────────────

    async def _gemini_imagen(self, prompt: str, width: int, height: int) -> Optional[dict]:
        """
        Gera imagem via Google Imagen 3 (imagen-3.0-generate-002) usando endpoint predict.
        Retorna a imagem como data URI base64.
        """
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"imagen-3.0-generate-002:predict"
                f"?key={GEMINI_API_KEY}"
            )
            # Escolhe o aspect ratio mais próximo
            ratio = "16:9" if width > height else "3:4"
            if abs((width/height) - 1.0) < 0.15:
                ratio = "1:1"
                
            payload = {
                "instances": [{"prompt": prompt[:500]}],
                "parameters": {
                    "sampleCount": 1,
                    "outputMimeType": "image/jpeg",
                    "aspectRatio": ratio
                }
            }
            async with httpx.AsyncClient(timeout=90.0) as client:
                r = await client.post(url, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    predictions = data.get("predictions", [])
                    if predictions and len(predictions) > 0:
                        b64 = predictions[0].get("bytesBase64Encoded", "")
                        if b64:
                            data_uri = f"data:image/jpeg;base64,{b64}"
                            return {
                                "image_url": data_uri,
                                "alt_text": prompt[:150],
                                "provider": "gemini",
                                "credit": "Gerada por Gemini Imagen (Google)",
                            }
                print(f"[ImageFactory/Gemini] HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[ImageFactory/Gemini] Erro: {e}")
        return None

    # ── PROVEDOR 3: Pexels ───────────────────────────────────────────────────

    async def _search_pexels(self, query: str, width: int, height: int) -> Optional[dict]:
        try:
            orientation = "landscape" if width > height else "portrait"
            headers = {"Authorization": PEXELS_API_KEY}
            params = {"query": query, "per_page": 5, "orientation": orientation, "page": random.randint(1, 8)}
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get("https://api.pexels.com/v1/search", headers=headers, params=params)
                if r.status_code == 200:
                    photos = r.json().get("photos", [])
                    if photos:
                        photo = random.choice(photos[:3]) if len(photos) >= 3 else photos[0]
                        src = photo.get("src", {})
                        img_url = src.get("large2x") or src.get("large") or src.get("medium")
                        return {
                            "image_url": img_url,
                            "alt_text": photo.get("alt", query),
                            "provider": "pexels",
                            "credit": f"Foto por {photo.get('photographer','Pexels')} no Pexels",
                            "photographer_url": photo.get("photographer_url", ""),
                        }
        except Exception as e:
            print(f"[ImageFactory/Pexels] Erro: {e}")
        return None

    # ── PROVEDOR 4: Unsplash ─────────────────────────────────────────────────

    async def _search_unsplash(self, query: str, width: int, height: int) -> Optional[dict]:
        if not UNSPLASH_ACCESS_KEY:
            return None
        try:
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
            params = {"query": query, "per_page": 3, "orientation": "landscape" if width > height else "portrait"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get("https://api.unsplash.com/search/photos", headers=headers, params=params)
                if r.status_code == 200:
                    results = r.json().get("results", [])
                    if results:
                        photo = results[0]
                        urls = photo.get("urls", {})
                        img_url = urls.get("regular") or urls.get("small")
                        return {
                            "image_url": img_url,
                            "alt_text": photo.get("alt_description", query),
                            "provider": "unsplash",
                            "credit": f"Foto por {photo.get('user',{}).get('name','Unsplash')} no Unsplash",
                        }
        except Exception as e:
            print(f"[ImageFactory/Unsplash] Erro: {e}")
        return None

    # ── PROVEDOR 5: SVG Placeholder (NUNCA falha) ────────────────────────────

    def _generate_svg_placeholder(self, text: str, width: int, height: int) -> str:
        themes = [
            ("#0d1117", "#f0c040"),
            ("#1a1410", "#d4a853"),
            ("#0a1628", "#4f8ef7"),
            ("#10151f", "#8b5cf6"),
        ]
        bg, accent = random.choice(themes)
        words = " ".join(text.split()[:5]) if text else "Dezafira"
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{bg}"/>
      <stop offset="100%" style="stop-color:{accent}22"/>
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#g)"/>
  <circle cx="{width//2}" cy="{height//2}" r="{min(width,height)//3}" fill="{accent}" opacity="0.07"/>
  <text x="{width//2}" y="{height//2-10}" font-family="Georgia,serif" font-size="30" fill="{accent}"
        text-anchor="middle" font-weight="bold" opacity="0.9">{words}</text>
  <text x="{width//2}" y="{height//2+35}" font-family="sans-serif" font-size="14" fill="{accent}"
        text-anchor="middle" opacity="0.5">dezafira.com.br</text>
</svg>'''
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _sanitize_for_search(self, text: str) -> str:
        text = re.sub(r"(Introdução|Conclusão|Seção|Capítulo)\s*[:\-]?\s*", "", text, flags=re.IGNORECASE)
        stopwords = {"sobre","para","com","uma","dos","das","nos","nas","em","de","da","do","que","é","como","por","ao"}
        words = [w for w in text.split()[:8] if w.lower() not in stopwords]
        return " ".join(words[:5]) or text

    def get_attribution_html(self, result: dict) -> str:
        provider = result.get("provider", "")
        credit = result.get("credit", "")
        if provider in ("pexels", "unsplash"):
            return f'<small style="font-size:10px;color:#7a6b5a">{credit}</small>'
        if provider == "flux":
            return '<small style="font-size:10px;color:#7a6b5a">⚡ Imagem gerada por IA (FLUX)</small>'
        if provider == "gemini":
            return '<small style="font-size:10px;color:#7a6b5a">🎨 Imagem gerada por IA (Gemini)</small>'
        return ""
