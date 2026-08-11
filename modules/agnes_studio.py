"""
AgnesStudio — Estudio de capas via Agnes AI (apihub.agnes-ai.com, $0/imagem).
Corrige os endpoints de capa (courses / ebooks / blog post) que importavam
modules.agnes_studio inexistente (eram 500). Sempre retorna um cover_url,
nunca levanta: se o Agnes falhar, recai em um SVG decente local.
"""
import logging
import os
import time

from modules.agnes_client import AgnesClient

logger = logging.getLogger("agnes_studio")
logger.setLevel(logging.INFO)

_STYLE_PROMPTS = {
    "moderno": "modern minimal design, vibrant accent, clean composition, professional",
    "classico": "elegant classic design, gold accents, dark background, premium",
    "tipografico": "bold typography, solid colors, sophisticated, clean layout",
    "natureza": "natural elements, earthy tones, warm lighting, organic",
}


def _style_prompt(style_id: str) -> str:
    return _STYLE_PROMPTS.get(style_id, _STYLE_PROMPTS["moderno"])


class AgnesStudio:
    """Gera capas profissionais (16:9) com Agnes AI + fallback SVG local."""

    def __init__(self, client: AgnesClient | None = None):
        self.client = client or AgnesClient()

    def _out_dir(self) -> str:
        d = os.path.join("outputs", "agnes")
        os.makedirs(d, exist_ok=True)
        return d

    def _save_path(self, entity: str, entity_id: str) -> str:
        ts = int(time.time())
        safe_id = entity_id.replace("-", "_").replace("/", "_")
        return os.path.join(self._out_dir(), f"{entity}_{safe_id}_{ts}.png")

    def _prompt(self, title: str, subtitle: str, niche: str, style: str) -> str:
        parts = [title[:120]]
        if subtitle:
            parts.append(subtitle[:120])
        if niche:
            parts.append(niche[:80])
        subject = " | ".join(parts)
        return (
            f"Professional cover art for an online product. {subject}. "
            f"{style}. Cinematic lighting, high contrast, no text, no watermark, clean composition."
        )

    def _svg_fallback(self, title: str, niche: str) -> str:
        """SVG decente (PNG local via base64 do proprio render) quando Agnes falha."""
        import base64 as _b64
        bg, accent = "#0d1117", "#f0c040"
        words = " ".join(title.split()[:6]) if title else "Dezafira"
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">'
            f'<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'<stop offset="0%" stop-color="{bg}"/><stop offset="100%" stop-color="{accent}33"/>'
            f'</linearGradient></defs>'
            f'<rect width="1280" height="720" fill="url(#g)"/>'
            f'<circle cx="640" cy="360" r="240" fill="{accent}" opacity="0.08"/>'
            f'<text x="640" y="350" font-family="Georgia,serif" font-size="48" fill="{accent}" '
            f'text-anchor="middle" font-weight="bold">{words}</text>'
            f'<text x="640" y="410" font-family="sans-serif" font-size="20" fill="{accent}" '
            f'text-anchor="middle" opacity="0.6">{niche or "Dezafira"}</text>'
            f'</svg>'
        )
        return "data:image/svg+xml;base64," + _b64.b64encode(svg.encode("utf-8")).decode("ascii")

    def _cover_url(self, path: str) -> str:
        rel = path.replace("\\", "/")
        if rel.startswith("outputs/"):
            return "/" + rel
        if rel.startswith("/outputs/"):
            return rel
        return "/" + rel

    async def _generate(self, title: str, subtitle: str, niche: str,
                        style_id: str, entity: str, entity_id: str,
                        design: dict | None = None) -> dict:
        """Pipeline comum: Agnes 16:9 -> PNG local; fallback SVG se falhar."""
        style = _style_prompt(style_id)
        if isinstance(design, dict) and design:
            style = f"{style}. {design.get('style_hint', '')}".strip()
        prompt = self._prompt(title, subtitle, niche, style)

        path = self._save_path(entity, entity_id)
        design_out = {
            "prompt": prompt,
            "style_id": style_id,
            "title": title,
            "niche": niche,
        }
        try:
            result = await self.client.generate_image(
                prompt, size="1792x1024", ratio="16:9", output_path=path
            )
            if result and os.path.exists(path):
                return {
                    "cover_url": self._cover_url(path),
                    "local_path": path,
                    "design": design_out,
                    "provider": "agnes",
                }
        except Exception as e:
            logger.warning("[AgnesStudio] Agnes falhou: %s — usando fallback SVG", e)
        return {
            "cover_url": self._svg_fallback(title, niche),
            "design": design_out,
            "provider": "fallback_svg",
        }

    async def generate_course_cover(self, title, subtitle, author, niche,
                                    style_id, course_id, difficulty, modules_count,
                                    design=None) -> dict:
        """Capa de curso (16:9) — assinatura exata que server.py já chama."""
        return await self._generate(title, subtitle, niche, style_id,
                                    "course", course_id, design)

    async def generate_ebook_cover(self, title, subtitle, author, niche,
                                   style_id, book_id, design=None) -> dict:
        """Capa de ebook (16:9) — assinatura exata que server.py já chama."""
        return await self._generate(title, subtitle, niche, style_id,
                                    "book", book_id, design)

    async def generate_blog_cover(self, title, subtitle, niche, style_id,
                                  post_id, blog_name) -> dict:
        """Imagem de destaque de post (16:9) — assinatura exata que server.py já chama."""
        return await self._generate(title, subtitle, niche, style_id,
                                    "post", post_id, None)


agnes_studio = AgnesStudio()
