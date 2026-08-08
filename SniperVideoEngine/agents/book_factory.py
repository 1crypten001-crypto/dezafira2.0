"""
Book Factory — Agentes especialistas em producao de livros.
Gera livros completos com capitulos, capa, formatacao ePUB/PDF.
"""
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from agents.llm import query_llm


class BookWriterAgent:
    """Agente escritor - gera conteudo de livros capitulo por capitulo."""

    async def generate_book_structure(self, topic: str, num_chapters: int = 8) -> list:
        """Gera a estrutura do livro (titulos dos capitulos)."""
        prompt = (
            f"Crie um livro cristao sobre: {topic}.\n\n"
            f"Gere {num_chapters} capitulos. Para cada capitulo, forneca:\n"
            f"- Numero do capitulo\n"
            f"- Titulo do capitulo\n\n"
            f"Formato: CAPITULO 1|Titulo do Capitulo\nCAPITULO 2|Titulo..."
        )
        resp = await query_llm([
            {"role": "system", "content": "Voce e um escritor cristao especializado em teologia e ensinamentos biblicos."},
            {"role": "user", "content": prompt},
        ])
        chapters = []
        for line in resp.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 1)
                if len(parts) == 2:
                    try:
                        num = int(parts[0].replace("CAPITULO", "").strip())
                        chapters.append({"chapter_number": num, "title": parts[1].strip()})
                    except ValueError:
                        continue
        if not chapters:
            for i in range(num_chapters):
                chapters.append({"chapter_number": i + 1, "title": f"Capitulo {i + 1}"})
        return chapters

    async def write_chapter(self, topic: str, chapter_title: str, chapter_number: int,
                            previous_chapters: str = "", style: str = "devocional") -> str:
        """Escreve o conteudo de um capitulo."""
        prompt = (
            f"Escreva o capitulo {chapter_number} - '{chapter_title}' de um livro cristao sobre: {topic}.\n\n"
            f"Estilo: {style}\n"
            f"Tom: Profundo, biblico, acessivel\n"
            f"Extensao: 800-1500 palavras\n\n"
            f"Contexto dos capitulos anteriores:\n{previous_chapters}\n\n"
            f"Escreva o conteudo completo do capitulo com:{chr(10)}"
            f"- Introducao envolvente{chr(10)}"
            f"- Desenvolvimento com base biblica{chr(10)}"
            f"- Aplicacao pratica{chr(10)}"
            f"- Conclusao e reflexao"
        )
        return await query_llm([
            {"role": "system", "content": "Voce e um escritor cristao. Escreva em portugues brasileiro."},
            {"role": "user", "content": prompt},
        ], max_tokens=4096)

    async def generate_book_content(self, topic: str, book_title: str, num_chapters: int = 8,
                                    style: str = "devocional") -> list:
        """Gera o livro completo."""
        chapters_structure = await self.generate_book_structure(topic, num_chapters)
        chapters = []
        previous = ""
        for ch in chapters_structure:
            content = await self.write_chapter(
                topic, ch["title"], ch["chapter_number"], previous, style
            )
            chapters.append({
                "chapter_number": ch["chapter_number"],
                "title": ch["title"],
                "content": content,
                "word_count": len(content.split()),
            })
            previous += f"\nCapitulo {ch['chapter_number']}: {ch['title']}\n"
        return chapters


class BookFormatterAgent:
    """Agente formatador - prepara livro para ePUB/PDF."""

    def generate_epub_html(self, book_title: str, author: str, chapters: list) -> str:
        """Gera HTML completo do livro (base para ePUB)."""
        chapters_html = ""
        for ch in chapters:
            paragraphs = "".join(
                f"<p>{p}</p>" for p in ch["content"].split("\n\n") if p.strip()
            )
            chapters_html += f"""
            <div class="chapter">
                <h2>{ch["chapter_number"]}. {ch["title"]}</h2>
                {paragraphs}
            </div>
            """
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>{book_title}</title>
<style>
  body {{ font-family: Georgia, serif; line-height: 1.8; max-width: 700px; margin: 0 auto; padding: 40px 20px; }}
  h1 {{ text-align: center; font-size: 28px; margin-bottom: 40px; }}
  h2 {{ font-size: 20px; margin-top: 40px; color: #1a1a2e; }}
  p {{ margin-bottom: 16px; text-indent: 1.5em; }}
  .chapter {{ page-break-before: always; }}
</style>
</head><body>
<h1>{book_title}</h1>
<p style="text-align:center;font-style:italic;">por {author}</p>
{chapters_html}
</body></html>"""
        return html


class BookCoverAgent:
    """Agente de capa - gera descricao para criacao de capa."""

    def generate_cover_brief(self, title: str, subtitle: str, topic: str) -> dict:
        """Gera brief para criacao de capa (para usar com IA de imagem)."""
        styles = {
            "classico": "Fundo escuro, letras douradas, moldura ornamental, aspecto classico e solene",
            "moderno": "Design minimalista, cores vibrantes, tipografia sans-serif, aspecto contemporaneo",
            "natureza": "Elementos naturais, paisagens, tons terrosos, luz natural",
            "tipografico": "Foco na tipografia, cores solidas, design limpo e sofisticado",
        }
        style = "classico" if "jesus" in topic.lower() else "moderno"
        return {
            "title": title,
            "subtitle": subtitle,
            "style": style,
            "description": styles[style],
            "colors": ["#1a1a2e", "#d4af37", "#f5f0e8"] if style == "classico" else ["#2d3436", "#6c5ce7", "#dfe6e9"],
            "prompt": f"Capa de livro cristao: '{title}'. Estilo {style}. {styles[style]}.",
        }
