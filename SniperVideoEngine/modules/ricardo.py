"""
📸 Ricardo — Fotógrafo Oficial da Fábrica de Blogs.

Ricardo é o agente que garante que TODO artigo tenha uma imagem de destaque.
Ele nunca falha — se Pexels e Unsplash não responderem, ele gera um placeholder
local em SVG que funciona em 100% dos navegadores.

Responsabilidades:
  1. Gerar imagem de destaque para cada artigo novo
  2. Garantir que artigos antigos sem imagem recebam uma
  3. Manter registro de quais provedores estão funcionando
  4. Fallback absoluto: placeholder SVG inline (sempre funciona)
"""

import os
import random
import base64
import httpx
from typing import Optional


class Ricardo:
    """📸 Ricardo — O Fotógrafo. Gera imagens para artigos sem nunca falhar."""

    def __init__(self):
        self.last_provider = None
        self.stats = {"pexels": 0, "unsplash": 0, "placeholder": 0}

    async def gerar_imagem(self, titulo: str, palavras_chave: str = "",
                           topico: str = "", largura: int = 1200,
                           altura: int = 630) -> dict:
        """
        Gera uma imagem de destaque para um artigo.
        NUNCA falha — sempre retorna uma URL de imagem válida.

        Args:
            titulo: Título do artigo
            palavras_chave: Keywords separadas por vírgula
            topico: Tópico do artigo
            largura, altura: Dimensões da imagem

        Returns:
            dict com image_url, alt_text, provider
        """
        # Monta query de busca
        query = self._montar_query(titulo, palavras_chave, topico)

        # Tentativa 1: Pexels
        pexels_key = os.getenv("PEXELS_API_KEY", "")
        if pexels_key:
            try:
                resultado = await self._buscar_pexels(query, pexels_key, largura, altura)
                if resultado and resultado.get("image_url"):
                    self.last_provider = "pexels"
                    self.stats["pexels"] += 1
                    return resultado
            except Exception:
                pass

        # Tentativa 2: Unsplash
        unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
        if unsplash_key:
            try:
                resultado = await self._buscar_unsplash(query, unsplash_key, largura, altura)
                if resultado and resultado.get("image_url"):
                    self.last_provider = "unsplash"
                    self.stats["unsplash"] += 1
                    return resultado
            except Exception:
                pass

        # Fallback ABSOLUTO: placeholder SVG local (100% garantido)
        self.last_provider = "placeholder"
        self.stats["placeholder"] += 1
        return self._gerar_placeholder(titulo, query, largura, altura)

    def _montar_query(self, titulo: str, keywords: str, topico: str) -> str:
        """Monta a melhor query de busca a partir dos dados do artigo."""
        partes = []
        if titulo:
            # Remove sufixos comuns de seção
            for s in [" - estudo completo", " - guia completo",
                       ": estudo", ": guia", ": o que", ": como"]:
                if s in titulo:
                    titulo = titulo.split(s)[0]
            partes.append(titulo)
        if keywords:
            kws = [k.strip() for k in keywords.split(",")[:3]]
            partes.extend(kws)
        if topico:
            partes.append(topico)
        # Junta e limita a 5 palavras
        texto = " ".join(partes)[:80]
        palavras = texto.split()[:5]
        return " ".join(palavras) if palavras else "blog"

    async def _buscar_pexels(self, query: str, key: str, w: int, h: int) -> Optional[dict]:
        """Busca imagem no Pexels."""
        orientation = "landscape" if w > h else "portrait"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": key},
                params={"query": query, "per_page": 5, "orientation": orientation},
            )
            if r.status_code == 200:
                photos = r.json().get("photos", [])
                if photos:
                    foto = photos[0] if len(photos) == 1 else random.choice(photos[:3])
                    src = foto.get("src", {})
                    return {
                        "image_url": src.get("large") or src.get("medium") or src.get("original"),
                        "alt_text": foto.get("alt", query),
                        "provider": "pexels",
                        "credit": f"Foto por {foto.get('photographer', 'Pexels')}",
                    }
        return None

    async def _buscar_unsplash(self, query: str, key: str, w: int, h: int) -> Optional[dict]:
        """Busca imagem no Unsplash."""
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.unsplash.com/search/photos",
                headers={"Authorization": f"Client-ID {key}"},
                params={"query": query, "per_page": 3},
            )
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    foto = results[0]
                    urls = foto.get("urls", {})
                    return {
                        "image_url": urls.get("regular") or urls.get("small"),
                        "alt_text": foto.get("alt_description", query),
                        "provider": "unsplash",
                        "credit": f"Foto por {foto.get('user', {}).get('name', 'Unsplash')}",
                    }
        return None

    def _gerar_placeholder(self, titulo: str, query: str, w: int, h: int) -> dict:
        """Gera placeholder SVG local — sempre funciona, sem dependência externa."""
        cores = [
            ("#1a1410", "#d4a853"), ("#2a2219", "#f0d68a"),
            ("#3d3227", "#c0392b"), ("#8b2500", "#f0e8d5"),
        ]
        bg, fg = random.choice(cores)
        texto = query[:40] or "Dezafira"

        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        svg += f'<rect width="{w}" height="{h}" fill="{bg}"/>'
        svg += f'<circle cx="{w//2}" cy="{h//2}" r="{min(w,h)//3}" fill="{fg}" opacity="0.12"/>'
        svg += f'<text x="{w//2}" y="{h//2-8}" font-family="sans-serif" font-size="26" fill="{fg}" text-anchor="middle" font-weight="bold">{texto}</text>'
        svg += f'<text x="{w//2}" y="{h//2+28}" font-family="sans-serif" font-size="13" fill="{fg}" text-anchor="middle" opacity="0.5">Dezafira Blog</text>'
        svg += '</svg>'

        return {
            "image_url": f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}",
            "alt_text": titulo or query,
            "provider": "placeholder",
            "credit": "",
        }

    def obter_relatorio(self) -> dict:
        """Retorna estatísticas do Ricardo."""
        return {
            "fotografo": "📸 Ricardo",
            "total_imagens": sum(self.stats.values()),
            "por_provedor": dict(self.stats),
            "ultimo_provedor": self.last_provider,
        }


async def gerar_imagens_pendentes(channel_id: str = None) -> dict:
    """
    Gera imagens para todos os artigos de blog que estão sem.
    Função compartilhada entre o endpoint HTTP e a pipeline.

    Args:
        channel_id: Se fornecido, gera imagens apenas para este canal/blog.
    """
    import asyncio
    from modules.database import SessionLocal, BlogPost

    ricardo = Ricardo()
    db = SessionLocal()
    try:
        query = db.query(BlogPost).filter(
            BlogPost.featured_image_url.is_(None)
        )
        if channel_id:
            query = query.filter(BlogPost.channel_id == channel_id)

        posts = query.all()

        total = len(posts)
        fixed = 0
        errors = 0

        for post in posts:
            try:
                img = await ricardo.gerar_imagem(
                    titulo=post.title or "",
                    palavras_chave=post.keywords or "",
                    topico=post.topic or "",
                )
                if img.get("image_url"):
                    post.featured_image_url = img["image_url"]
                    db.commit()
                    fixed += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                errors += 1
                print(f"[Ricardo] Erro ao gerar imagem: {e}")

        return {
            "success": True,
            "total_articles": total,
            "images_generated": fixed,
            "errors": errors,
            "message": f"{fixed} imagens geradas de {total} artigos",
        }
    finally:
        db.close()
