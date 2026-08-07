"""
================================================================================
DEZAFIRA — Fabrica de Ebooks Tripla (Ebook Principal + 2 Bonus Exclusivos)
================================================================================
Gera um pacote de 3 Ebooks completos com Capas profissionais:
1. Ebook Principal: Guia de Autoridade (8 Capitulos)
2. Ebook Bonus 1: Manual de Prompts & Estrategia (5 Capitulos)
3. Ebook Bonus 2: Checklist & Roteiro de Escala (5 Capitulos)

Agentes especializados:
- BookNamerAgent: Nomes magneticos com score de potencial
- CoverDesignerAgent: Prompts hiper-detalhados para capas
- ChapterWriterAgent: Conteudo real capitulo por capitulo
"""
import os
import json
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from modules.image_factory import ImageGeneratorAgent
from agents.specialists import book_namer, cover_designer, chapter_writer

logger = logging.getLogger("ebook_factory")
logger.setLevel(logging.INFO)

# ═══════════════════════════════════════════════════════════════════════════════
# TASK TRACKER — Progresso em tempo real
# ═══════════════════════════════════════════════════════════════════════════════

_ebook_tasks: Dict[str, Dict[str, Any]] = {}


def get_ebook_task(task_id: str) -> Optional[Dict[str, Any]]:
    return _ebook_tasks.get(task_id)


def list_ebook_tasks() -> List[Dict[str, Any]]:
    return sorted(_ebook_tasks.values(), key=lambda t: t.get("started_at", 0), reverse=True)


class TripleEbookFactory:
    def __init__(self):
        self.image_agent = ImageGeneratorAgent()

    async def generate_triple_pack(self, main_title: str, niche: str = "Geral",
                                    task_id: str = None) -> Dict[str, Any]:
        """
        Gera um pacote com 3 Ebooks completos usando agentes especializados.
        Suporta progresso via task_id.
        """
        import uuid
        tid = task_id or f"ebk_{uuid.uuid4().hex[:8]}"

        _ebook_tasks[tid] = {
            "task_id": tid,
            "status": "running",
            "phase": "init",
            "progress": 0,
            "message": "Iniciando fabrica de ebooks...",
            "started_at": time.time(),
            "pack": None,
            "phases": {},
        }

        def _update(phase: str, progress: int, message: str):
            _ebook_tasks[tid].update({
                "phase": phase, "progress": progress, "message": message,
                "updated_at": time.time(),
            })
            _ebook_tasks[tid]["phases"][phase] = {
                "status": "completed" if progress >= 100 else "running",
                "progress": progress, "message": message,
            }
            logger.info(f"[EbookFactory][{tid}] {phase}: {progress}% - {message}")

        try:
            _update("names", 5, "Gerando nomes magneticos via BookNamerAgent...")
            clean_title = main_title.replace("Criar Ebook:", "").strip() or "Negocios Digitais com IA"

            # === FASE 1: Nomes ===
            names = await book_namer.generate_names(niche, clean_title, count=5)
            _update("names", 100, f"Nomes gerados: {len(names)} opcoes")

            principal_name = clean_title
            bonus_names = []
            for n in names:
                if n["type"] == "bonus" and len(bonus_names) < 2:
                    bonus_names.append(n["name"])
            while len(bonus_names) < 2:
                bonus_names.append(f"Guia Extra: {niche}")

            # === FASE 2: Capas ===
            _update("covers", 10, "Gerando prompts de capa via CoverDesignerAgent...")
            cover_main = await cover_designer.design_cover(principal_name, niche, "moderno")
            _update("covers", 30, "Prompt da capa principal pronto. Gerando imagem...")
            cover_bonus1 = await cover_designer.design_cover(bonus_names[0], niche, "minimalista")
            _update("covers", 50, "Prompt capa bonus 1 pronto. Gerando imagem...")
            cover_bonus2 = await cover_designer.design_cover(bonus_names[1], niche, "minimalista")
            _update("covers", 70, "Prompts prontos. Gerando imagens via cascata...")

            main_img = await self.image_agent.generate_for_ebook(cover_main["prompt"])
            _update("covers", 80, "Imagem capa principal gerada. Gerando bonus...")
            bonus1_img = await self.image_agent.generate_for_ebook(cover_bonus1["prompt"])
            _update("covers", 90, "Imagem capa bonus 1 gerada...")
            bonus2_img = await self.image_agent.generate_for_ebook(cover_bonus2["prompt"])
            _update("covers", 100, "Todas as capas geradas!")

            # === FASE 3: Capitulos Ebook Principal (8 capitulos) ===
            _update("chapters_main", 0, f"Escrevendo 8 capitulos do ebook principal...")
            chapters_main = await self._generate_book_chapters(
                principal_name, niche, 8, "guia definitivo",
                cover_main.get("mood", ""), "",
                on_progress=lambda i, total: _update("chapters_main", int(100 * i / total),
                    f"Ebook Principal: capitulo {i}/{total} - '{principal_name[:40]}...'")
            )
            _update("chapters_main", 100, f"Ebook principal: {len(chapters_main)} capitulos")

            # === FASE 4: Capitulos Bonus 1 (5 capitulos) ===
            _update("chapters_bonus1", 0, f"Escrevendo 5 capitulos do bonus 1...")
            chapters_bonus1 = await self._generate_book_chapters(
                bonus_names[0], niche, 5, "prompts e estrategias",
                cover_bonus1.get("mood", ""), "",
                on_progress=lambda i, total: _update("chapters_bonus1", int(100 * i / total),
                    f"Bonus 1: capitulo {i}/{total}")
            )
            _update("chapters_bonus1", 100, f"Bonus 1: {len(chapters_bonus1)} capitulos")

            # === FASE 5: Capitulos Bonus 2 (5 capitulos) ===
            _update("chapters_bonus2", 0, f"Escrevendo 5 capitulos do bonus 2...")
            chapters_bonus2 = await self._generate_book_chapters(
                bonus_names[1], niche, 5, "checklist e escala",
                cover_bonus2.get("mood", ""), "",
                on_progress=lambda i, total: _update("chapters_bonus2", int(100 * i / total),
                    f"Bonus 2: capitulo {i}/{total}")
            )
            _update("chapters_bonus2", 100, f"Bonus 2: {len(chapters_bonus2)} capitulos")

            # === MONTAR RESULTADO ===
            _update("done", 100, "Pacote de ebooks pronto!")

            ebook_main = {
                "id": "ebk_main", "type": "principal",
                "badge": "📘 EBOOK PRINCIPAL DA OFERTA",
                "title": principal_name,
                "subtitle": f"O guia completo de {niche}",
                "cover_url": main_img.get("image_url", ""),
                "cover_style": cover_main,
                "chapters_count": len(chapters_main),
                "chapters": chapters_main,
            }
            ebook_bonus1 = {
                "id": "ebk_bonus1", "type": "bonus",
                "badge": "🎁 BONUS EXCLUSIVO #01",
                "title": bonus_names[0],
                "subtitle": "50 Prompts validados para criar copys que vendem",
                "cover_url": bonus1_img.get("image_url", ""),
                "cover_style": cover_bonus1,
                "chapters_count": len(chapters_bonus1),
                "chapters": chapters_bonus1,
            }
            ebook_bonus2 = {
                "id": "ebk_bonus2", "type": "bonus",
                "badge": "🎁 BONUS EXCLUSIVO #02",
                "title": bonus_names[1],
                "subtitle": "O passo a passo para escalar resultados",
                "cover_url": bonus2_img.get("image_url", ""),
                "cover_style": cover_bonus2,
                "chapters_count": len(chapters_bonus2),
                "chapters": chapters_bonus2,
            }

            result = {
                "main_title": principal_name,
                "niche": niche,
                "total_ebooks": 3,
                "pack": [ebook_main, ebook_bonus1, ebook_bonus2],
                "status": "ready",
            }

            _ebook_tasks[tid].update({
                "status": "completed",
                "progress": 100,
                "message": "Pacote pronto!",
                "pack": result,
                "completed_at": time.time(),
            })

            return result

        except Exception as e:
            logger.error(f"[EbookFactory][{tid}] ERRO: {e}")
            _ebook_tasks[tid].update({
                "status": "failed",
                "message": f"Erro: {str(e)}",
                "error": str(e),
                "completed_at": time.time(),
            })
            raise

    async def _generate_book_chapters(self, book_title: str, niche: str,
                                       num_chapters: int, book_type: str,
                                       mood: str, mechanism: str,
                                       on_progress: Callable = None) -> List[Dict[str, Any]]:
        """Gera capitulos reais usando o ChapterWriterAgent."""
        chapters = []
        previous_summary = ""

        for i in range(num_chapters):
            if on_progress:
                on_progress(i, num_chapters)

            result = await chapter_writer.write_chapter(
                title=f"Capitulo {i + 1}",
                chapter_number=i + 1,
                total_chapters=num_chapters,
                niche=niche,
                book_title=book_title,
                promise=f"Transformacao completa em {niche}",
                mechanism_name=mechanism,
                previous_summary=previous_summary,
                style="didatico",
            )
            if result["success"]:
                chapters.append({
                    "num": i + 1,
                    "title": f"Capitulo {i + 1}",
                    "content": result["content"],
                    "word_count": result["word_count"],
                })
                previous_summary += result["chapter_summary"] + "\n"
            else:
                chapters.append({
                    "num": i + 1,
                    "title": f"Capitulo {i + 1}",
                    "content": f"Conteudo do capitulo {i + 1} sobre {book_type} no nicho de {niche}.",
                    "word_count": 0,
                })

        if on_progress:
            on_progress(num_chapters, num_chapters)

        return chapters


triple_ebook_factory = TripleEbookFactory()
