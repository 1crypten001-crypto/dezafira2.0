"""
Fabrica de Cursos — Macro-pipeline com 6 fases.
Fluxo: Fundacao → Pesquisa → Estrutura → Producao → Refino → Entrega
Inspirado na blog_pipeline.py e ebook_pipeline.py, adaptado para cursos online.
"""
import os
import json
import uuid
import traceback
from datetime import datetime
from typing import Optional, Callable, Any


# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO DA PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

class CourseMacroState:
    """Estado completo da macro-pipeline de cursos."""

    def __init__(self):
        self.task_id: str = ""
        self.course_id: str = ""
        self.topic: str = ""
        self.course_title: str = ""
        self.language: str = "pt"
        self.difficulty: str = "iniciante"
        self.price_cents: int = 0
        self.target_modules: int = 4
        self.lessons_per_module: int = 4
        self.status: str = "idle"
        self.current_macro_stage: str = ""
        self.macro_stages: dict = {}
        self.audience_data: dict = {}
        self.structure: list = []
        self.modules_created: list = []
        self.lessons_generated: list = []
        self.total_words: int = 0
        self.total_lessons: int = 0
        self.cover_url: str = ""
        self.lili_scores: list = []
        self.pipeline_run_id: str = ""
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id, "course_id": self.course_id,
            "topic": self.topic, "course_title": self.course_title,
            "difficulty": self.difficulty, "price_cents": self.price_cents,
            "target_modules": self.target_modules,
            "lessons_per_module": self.lessons_per_module,
            "status": self.status,
            "current_macro_stage": self.current_macro_stage,
            "macro_stages": self.macro_stages,
            "audience_data": self.audience_data,
            "modules_created": self.modules_created,
            "lessons_generated": self.lessons_generated[-20:],
            "total_words": self.total_words,
            "total_lessons": self.total_lessons,
            "cover_url": self.cover_url,
            "lili_scores": self.lili_scores[-20:],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MACRO-PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class CourseMacroPipeline:
    """Pipeline de 6 fases para criacao completa de cursos online."""

    def __init__(self, on_progress: Callable = None):
        self.state = CourseMacroState()
        self.on_progress = on_progress or (lambda *a, **k: None)

    def _emit(self, event_type: str, data: dict):
        self.on_progress(self.state.task_id, "__broadcast__", 0, event_type, data)

    def _update_macro(self, stage_id: str, status: str, progress: int,
                      message: str = "", data: dict = None):
        self.state.macro_stages[stage_id] = {
            "status": status, "progress": progress,
            "message": message, "data": data or {},
            "started_at": datetime.utcnow().isoformat() if status == "active" else None,
            "completed_at": datetime.utcnow().isoformat() if status in ("completed", "failed") else None,
        }
        self._emit("macro_update", {
            "stage_id": stage_id, "status": status,
            "progress": progress, "message": message,
            "data": data or {}, "task_id": self.state.task_id,
            "course_title": self.state.course_title,
            "total_words": self.state.total_words,
            "total_lessons": self.state.total_lessons,
        })

    async def _run_macro(self, stage_id: str, stage_name: str, stage_fn):
        self.state.current_macro_stage = stage_id
        self._update_macro(stage_id, "active", 0, f"Iniciando {stage_name}...")
        try:
            await stage_fn()
        except Exception as e:
            self._update_macro(stage_id, "failed", 0, str(e))
            raise RuntimeError(f"Falha na fase {stage_name}: {str(e)}") from e

    def _save_checkpoint(self):
        """Salva estado da pipeline no banco."""
        try:
            from modules.database import update_db_course_pipeline_run
            update_db_course_pipeline_run(
                self.state.pipeline_run_id,
                phase=self.state.current_macro_stage,
                total_lessons_generated=self.state.total_lessons,
                pipeline_data=json.dumps(self.state.to_dict(), default=str),
            )
        except Exception as e:
            print(f"[CoursePipeline] Checkpoint save error: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # EXECUCAO PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════════════

    async def execute(self, topic: str, course_title: str = "",
                      difficulty: str = "iniciante", price_cents: int = 0,
                      target_modules: int = 4, lessons_per_module: int = 4,
                      language: str = "pt", task_id: str = None) -> CourseMacroState:
        self.state.task_id = task_id or f"crpipe_{uuid.uuid4().hex[:8]}"
        self.state.topic = topic
        self.state.course_title = course_title
        self.state.difficulty = difficulty
        self.state.price_cents = price_cents
        self.state.target_modules = target_modules
        self.state.lessons_per_module = lessons_per_module
        self.state.language = language
        self.state.status = "running"
        self.state.started_at = datetime.utcnow()

        self._emit("pipeline_started", {
            "task_id": self.state.task_id,
            "topic": topic, "course_title": course_title,
        })

        try:
            await self._run_macro("fundacao", "Fundacao", self._phase_fundacao)
            self._save_checkpoint()

            await self._run_macro("pesquisa", "Pesquisa de Publico", self._phase_pesquisa)
            self._save_checkpoint()

            await self._run_macro("estrutura", "Estrutura Curricular", self._phase_estrutura)
            self._save_checkpoint()

            await self._run_macro("producao", "Producao de Conteudo", self._phase_producao)
            self._save_checkpoint()

            await self._run_macro("refino", "Refino e Revisao", self._phase_refino)
            self._save_checkpoint()

            await self._run_macro("entrega", "Entrega Final", self._phase_entrega)
            self._save_checkpoint()

            self.state.status = "completed"
            self.state.completed_at = datetime.utcnow()
            self._emit("pipeline_complete", self.state.to_dict())

        except Exception as e:
            self.state.status = "failed"
            self.state.error = str(e)
            self.state.completed_at = datetime.utcnow()
            print(f"[CoursePipeline] PIPELINE_FAILED: {e}")
            traceback.print_exc()
            self._emit("pipeline_failed", {
                **self.state.to_dict(),
                "error_detail": traceback.format_exc(),
            })

        return self.state

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 1: FUNDACAO — Criar curso no banco + titulo
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_fundacao(self):
        from modules.database import (
            create_db_course, create_db_course_pipeline_run, update_db_course
        )
        from agents.course_professor import course_professor

        sid = "fundacao"
        self._update_macro(sid, "active", 10, "Criando curso no banco...")

        # Gerar titulo se nao informado
        if not self.state.course_title:
            self._update_macro(sid, "active", 20, "Gerando titulo via LLM...")
            self.state.course_title = await course_professor.generate_title(
                self.state.topic, self.state.language
            )

        self._update_macro(sid, "active", 40, f"Titulo: {self.state.course_title}")

        # Criar registro no banco
        course = create_db_course(
            title=self.state.course_title,
            topic=self.state.topic,
            description=f"Curso online sobre {self.state.topic}",
            difficulty=self.state.difficulty,
            price_cents=self.state.price_cents,
        )
        self.state.course_id = course["id"]

        # Criar pipeline run
        pipeline_run = create_db_course_pipeline_run(
            self.state.course_id,
            total_modules_target=self.state.target_modules,
        )
        self.state.pipeline_run_id = pipeline_run["id"]

        # Atualizar curso com dados iniciais
        update_db_course(self.state.course_id,
            keywords=self.state.topic,
        )

        self._update_macro(sid, "completed", 100,
            f"Curso criado: {self.state.course_title}",
            data={"course_id": self.state.course_id})

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 2: PESQUISA — Analise de publico e objetivos
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_pesquisa(self):
        from agents.course_professor import course_professor

        sid = "pesquisa"
        self._update_macro(sid, "active", 10, "Analisando publico-alvo...")

        audience = await course_professor.analyze_audience(
            self.state.topic, self.state.language
        )
        self.state.audience_data = audience

        # Ajustar dificuldade se LLM sugeriu diferente
        if audience.get("nivel"):
            self.state.difficulty = audience["nivel"]

        # Ajustar modulo se LLM sugeriu diferente
        if audience.get("num_modulos_recomendado"):
            self.state.target_modules = audience["num_modulos_recomendado"]

        self._update_macro(sid, "active", 60,
            f"Publico: {audience.get('publico_alvo', 'N/A')[:80]}")

        self._update_macro(sid, "completed", 100,
            f"Pesquisa concluida — {len(audience.get('objetivos', []))} objetivos",
            data=audience)

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 3: ESTRUTURA — Gerar modulos e aulas
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_estrutura(self):
        from modules.database import (
            create_db_course_module, create_db_course_lesson, update_db_course
        )
        from agents.course_professor import course_professor

        sid = "estrutura"
        self._update_macro(sid, "active", 10, "Gerando estrutura curricular...")

        structure = await course_professor.generate_structure(
            topic=self.state.topic,
            course_title=self.state.course_title,
            num_modules=self.state.target_modules,
            num_lessons_per_module=self.state.lessons_per_module,
            language=self.state.language,
        )
        self.state.structure = structure

        self._update_macro(sid, "active", 30,
            f"Estrutura: {len(structure)} modulos gerados")

        # Criar modulos e aulas no banco
        total_lessons = 0
        modules_created = []

        for mod_data in structure:
            mod_num = mod_data.get("numero", len(modules_created) + 1)
            mod_title = mod_data.get("titulo", f"Modulo {mod_num}")
            mod_desc = mod_data.get("descricao", "")

            module = create_db_course_module(
                self.state.course_id, mod_num, mod_title, mod_desc
            )

            lessons_in_module = []
            for aula_data in mod_data.get("aulas", []):
                aula_num = aula_data.get("numero", len(lessons_in_module) + 1)
                aula_title = aula_data.get("titulo", f"Aula {aula_num}")
                aula_type = aula_data.get("tipo", "texto")

                lesson = create_db_course_lesson(
                    module["id"], aula_num, aula_title,
                    content="", content_type=aula_type,
                )
                lessons_in_module.append({
                    "id": lesson["id"],
                    "number": aula_num,
                    "title": aula_title,
                    "type": aula_type,
                    "module_id": module["id"],
                })
                total_lessons += 1

            modules_created.append({
                "id": module["id"],
                "number": mod_num,
                "title": mod_title,
                "lessons": lessons_in_module,
            })

        self.state.modules_created = modules_created
        self.state.total_lessons = total_lessons

        # Atualizar contadores no curso
        update_db_course(self.state.course_id,
            total_modules=len(modules_created),
            total_lessons=total_lessons,
            difficulty=self.state.difficulty,
        )

        self._update_macro(sid, "active", 70,
            f"{len(modules_created)} modulos, {total_lessons} aulas criadas no banco")

        self._update_macro(sid, "completed", 100,
            f"Estrutura: {len(modules_created)} modulos, {total_lessons} aulas",
            data={"modules": len(modules_created), "lessons": total_lessons})

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 4: PRODUCAO — Escrever conteudo de cada aula
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_producao(self):
        from modules.database import update_db_course_lesson
        from agents.course_pedagogue import course_pedagogue
        from agents.course_reviewer import revisar_e_corrigir_aula

        sid = "producao"
        total = self.state.total_lessons
        self._update_macro(sid, "active", 0,
            f"Produzindo conteudo de {total} aulas...")

        lessons_generated = []
        idx = 0

        for mod in self.state.modules_created:
            for lesson_data in mod["lessons"]:
                idx += 1
                progress = int((idx / total) * 90)
                self._update_macro(sid, "active", progress,
                    f"Aula {idx}/{total}: {lesson_data['title']}")

                # Escrever conteudo
                if lesson_data.get("type") == "exercicio":
                    result = await course_pedagogue.write_lesson(
                        topic=self.state.topic,
                        module_title=mod["title"],
                        lesson_title=lesson_data["title"],
                        lesson_number=lesson_data["number"],
                        lesson_type="exercicio",
                        module_number=mod["number"],
                        total_modules=len(self.state.modules_created),
                        total_lessons_in_module=len(mod["lessons"]),
                        language=self.state.language,
                    )
                else:
                    result = await course_pedagogue.write_lesson(
                        topic=self.state.topic,
                        module_title=mod["title"],
                        lesson_title=lesson_data["title"],
                        lesson_number=lesson_data["number"],
                        lesson_type="texto",
                        module_number=mod["number"],
                        total_modules=len(self.state.modules_created),
                        total_lessons_in_module=len(mod["lessons"]),
                        language=self.state.language,
                    )

                content = result.get("content", "")

                # LiLi Review
                review = await revisar_e_corrigir_aula(
                    title=lesson_data["title"],
                    content=content,
                    lesson_number=lesson_data["number"],
                )
                final_content = review.get("final_content", content)
                score = review.get("score", 0)

                self.state.lili_scores.append({
                    "lesson": lesson_data["title"],
                    "score": score,
                    "attempts": review.get("attempts", 1),
                })

                # Salvar no banco
                update_db_course_lesson(
                    lesson_data["id"],
                    content=final_content,
                    word_count=len(final_content.split()),
                    estimated_minutes=result.get("estimated_minutes", 10),
                )

                self.state.total_words += len(final_content.split())
                lessons_generated.append({
                    "id": lesson_data["id"],
                    "title": lesson_data["title"],
                    "word_count": len(final_content.split()),
                    "score": score,
                })

        self.state.lessons_generated = lessons_generated
        self._update_macro(sid, "completed", 100,
            f"{len(lessons_generated)} aulas produzidas — {self.state.total_words} palavras",
            data={"lessons": len(lessons_generated), "words": self.state.total_words})

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 5: REFINO — Cover, materiais e quiz
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_refino(self):
        from modules.database import (
            create_db_course_material, create_db_course_quiz, update_db_course
        )
        from agents.course_cover import course_cover
        from agents.course_quizmaster import course_quizmaster

        sid = "refino"
        self._update_macro(sid, "active", 10, "Gerando capa do curso...")

        # Gerar cover
        try:
            cover_url = await course_cover.generate_cover(
                self.state.course_title, self.state.topic
            )
            self.state.cover_url = cover_url
            update_db_course(self.state.course_id, cover_url=cover_url)
        except Exception as e:
            print(f"[CoursePipeline] Cover generation error: {e}")

        self._update_macro(sid, "active", 30, "Gerando quizzes por aula...")

        # Gerar quiz para cada aula
        quizzes_created = 0
        for mod in self.state.modules_created:
            for lesson_data in mod["lessons"]:
                if lesson_data.get("type") == "exercicio":
                    continue

                # Buscar conteudo da aula do banco (ja salvo na fase 4)
                from modules.database import get_db_course_lesson_content
                lesson_content = get_db_course_lesson_content(lesson_data["id"])
                if not lesson_content:
                    continue

                quiz_questions = await course_quizmaster.generate_quiz(
                    topic=self.state.topic,
                    module_title=mod["title"],
                    lesson_title=lesson_data["title"],
                    lesson_content=lesson_content,
                    num_questions=3,
                    language=self.state.language,
                )

                if quiz_questions:
                    create_db_course_quiz(lesson_data["id"], quiz_questions)
                    quizzes_created += 1

        self._update_macro(sid, "active", 60,
            f"{quizzes_created} quizzes criados")

        # Gerar materiais complementares por modulo
        materials_created = 0
        for mod in self.state.modules_created:
            lessons_titles = [l["title"] for l in mod["lessons"]]

            # Resumo do modulo
            from agents.course_pedagogue import course_pedagogue
            summary = await course_pedagogue.write_module_summary(
                self.state.topic, mod["title"], lessons_titles, self.state.language
            )
            if summary:
                # Usar a primeira aula do modulo como referencia
                if mod["lessons"]:
                    create_db_course_material(
                        mod["lessons"][0]["id"],
                        "resumo",
                        f"Resumo do {mod['title']}",
                        summary,
                    )
                    materials_created += 1

        self._update_macro(sid, "active", 80,
            f"{materials_created} materiais criados")

        avg_score = 0
        if self.state.lili_scores:
            avg_score = sum(s["score"] for s in self.state.lili_scores) / len(self.state.lili_scores)

        self._update_macro(sid, "completed", 100,
            f"Refino: {quizzes_created} quizzes, {materials_created} materiais, score medio LiLi: {avg_score:.0f}/100",
            data={"quizzes": quizzes_created, "materials": materials_created, "avg_score": avg_score})

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 6: ENTREGA — Validacao e publicacao
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_entrega(self):
        from modules.database import (
            update_db_course, update_db_course_pipeline_run
        )

        sid = "entrega"
        self._update_macro(sid, "active", 10, "Validando curso...")

        # Validacao final
        validations = []
        if self.state.modules_created:
            validations.append(f"{len(self.state.modules_created)} modulos")
        if self.state.lessons_generated:
            validations.append(f"{len(self.state.lessons_generated)} aulas")
        if self.state.total_words > 0:
            validations.append(f"{self.state.total_words} palavras")
        if self.state.cover_url:
            validations.append("cover OK")

        self._update_macro(sid, "active", 50,
            f"Validacao: {', '.join(validations)}")

        # Publicar curso
        update_db_course(self.state.course_id,
            status="published",
            published_at=datetime.utcnow(),
        )

        # Finalizar pipeline run
        update_db_course_pipeline_run(
            self.state.pipeline_run_id,
            phase="entrega",
            status="completed",
            total_lessons_generated=self.state.total_lessons,
            completed_at=datetime.utcnow(),
            pipeline_data=json.dumps(self.state.to_dict(), default=str),
        )

        self._update_macro(sid, "completed", 100,
            f"Curso publicado: {self.state.course_title}",
            data={
                "course_id": self.state.course_id,
                "modules": len(self.state.modules_created),
                "lessons": self.state.total_lessons,
                "words": self.state.total_words,
            })


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

async def run_course_macro_pipeline(topic: str, course_title: str = "",
                                     difficulty: str = "iniciante",
                                     price_cents: int = 0,
                                     target_modules: int = 4,
                                     lessons_per_module: int = 4,
                                     language: str = "pt",
                                     task_id: str = None,
                                     on_progress: Callable = None) -> dict:
    """Entry point para a macro-pipeline de cursos."""
    pipeline = CourseMacroPipeline(on_progress=on_progress)
    state = await pipeline.execute(
        topic=topic, course_title=course_title,
        difficulty=difficulty, price_cents=price_cents,
        target_modules=target_modules,
        lessons_per_module=lessons_per_module,
        language=language, task_id=task_id,
    )
    return state.to_dict()
