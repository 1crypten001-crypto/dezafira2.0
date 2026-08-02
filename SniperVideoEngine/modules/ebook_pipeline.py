"""
Fabrica de Ebooks — Macro-pipeline com 6 fases.
Fluxo: Fundacao → Pesquisa → Oferta → Producao → Refino → Entrega
Inspirado na blog_pipeline.py, adaptado para ebooks de baixo ticket.
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

class EbookMacroState:
    """Estado completo da macro-pipeline de ebooks."""

    def __init__(self):
        self.task_id: str = ""
        self.book_id: str = ""
        self.blog_channel_id: str = ""
        self.niche: str = ""
        self.language: str = "pt"
        self.book_title: str = ""
        self.style_id: str = "minimalista"
        self.price_cents: int = 1700
        self.target_chapters: int = 8
        self.status: str = "idle"
        self.current_macro_stage: str = ""
        self.macro_stages: dict = {}
        self.pain_research: dict = {}
        self.offer_data: dict = {}
        self.persona: dict = {}
        self.chapters_structure: list = []
        self.chapters_generated: list = []
        self.total_words: int = 0
        self.lili_score: int = 0
        self.sales_page_html: str = ""
        self.checkout_url: str = ""
        self.cover_url: str = ""
        self.pipeline_run_id: str = ""
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id, "book_id": self.book_id,
            "blog_channel_id": self.blog_channel_id, "niche": self.niche,
            "book_title": self.book_title, "style_id": self.style_id,
            "price_cents": self.price_cents, "target_chapters": self.target_chapters,
            "status": self.status, "current_macro_stage": self.current_macro_stage,
            "macro_stages": self.macro_stages,
            "pain_research": self.pain_research,
            "offer_data": self.offer_data,
            "persona": self.persona,
            "chapters_structure": self.chapters_structure,
            "chapters_generated": self.chapters_generated[-10:],
            "total_words": self.total_words, "lili_score": self.lili_score,
            "cover_url": self.cover_url,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MACRO-PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class EbookMacroPipeline:
    """Pipeline de 6 fases para criacao completa de ebooks."""

    def __init__(self, on_progress: Callable = None):
        self.state = EbookMacroState()
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
            "book_title": self.state.book_title,
            "total_words": self.state.total_words,
        })

    async def _run_macro(self, stage_id: str, stage_name: str, stage_fn):
        self.state.current_macro_stage = stage_id
        self._update_macro(stage_id, "active", 0, f"Iniciando {stage_name}...")
        try:
            await stage_fn()
        except Exception as e:
            self._update_macro(stage_id, "failed", 0, str(e))
            raise RuntimeError(f"Falha na fase {stage_name}: {str(e)}") from e

    # ═══════════════════════════════════════════════════════════════════════════
    # EXECUCAO PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════════════

    async def execute(self, niche: str, book_title: str = "", blog_channel_id: str = "",
                style_id: str = "minimalista", price_cents: int = 1700,
                target_chapters: int = 8, language: str = "pt",
                task_id: str = None) -> EbookMacroState:
        self.state.task_id = task_id or f"ebpipe_{uuid.uuid4().hex[:8]}"
        self.state.niche = niche
        self.state.book_title = book_title
        self.state.blog_channel_id = blog_channel_id
        self.state.style_id = style_id
        self.state.price_cents = price_cents
        self.state.target_chapters = target_chapters
        self.state.language = language
        self.state.status = "running"
        self.state.started_at = datetime.utcnow()

        self._emit("pipeline_started", {
            "task_id": self.state.task_id,
            "niche": niche, "book_title": book_title,
        })

        try:
            await self._run_macro("fundacao", "Fundacao", self._phase_fundacao)
            await self._run_macro("pesquisa", "Pesquisa de Dores", self._phase_pesquisa)
            await self._run_macro("oferta", "Criar Oferta", self._phase_oferta)
            await self._run_macro("producao", "Producao", self._phase_producao)
            await self._run_macro("refino", "Refino", self._phase_refino)
            await self._run_macro("entrega", "Entrega", self._phase_entrega)

            self.state.status = "completed"
            self.state.completed_at = datetime.utcnow()
            self._emit("pipeline_complete", self.state.to_dict())

        except Exception as e:
            self.state.status = "failed"
            self.state.error = str(e)
            self.state.completed_at = datetime.utcnow()
            print(f"[EbookPipeline] PIPELINE_FAILED: {e}")
            traceback.print_exc()
            self._emit("pipeline_failed", {
                **self.state.to_dict(),
                "error_detail": traceback.format_exc(),
            })

        return self.state

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 1: FUNDACAO — Criar ebook no banco + branding
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_fundacao(self):
        from modules.database import create_db_book, create_db_ebook_pipeline_run, update_db_book
        from agents.llm import query_llm

        sid = "fundacao"
        self._update_macro(sid, "active", 10, "Criando ebook no banco...")

        # Gerar titulo se nao informado
        if not self.state.book_title:
            resp = await query_llm([
                {"role": "system", "content": "Voce e um copywriter de infoprodutos."},
                {"role": "user", "content": f"Crie um titulo magnetico (max 5 palavras) para um ebook low-ticket sobre: {self.state.niche}. Responda APENAS com o titulo."},
            ])
            self.state.book_title = resp.strip().strip('"').strip("'")

        self._update_macro(sid, "active", 30, f"Titulo: {self.state.book_title}")

        # Criar registro no banco
        book = create_db_book(
            title=self.state.book_title,
            topic=self.state.niche,
            description=f"Ebook low-ticket sobre {self.state.niche}",
            price_cents=self.state.price_cents,
        )
        self.state.book_id = book["id"]

        # Criar pipeline run
        pipeline_run = create_db_ebook_pipeline_run(self.state.book_id)
        self.state.pipeline_run_id = pipeline_run["id"]

        # Salvar dados iniciais no banco
        update_db_book(self.state.book_id,
            style_id=self.state.style_id,
            blog_channel_id=self.state.blog_channel_id,
            niche=self.state.niche,
            pipeline_run_id=self.state.pipeline_run_id,
        )

        self._update_macro(sid, "active", 60, "Gerando branding...")

        # Gerar brief da capa via LLM
        resp = await query_llm([
            {"role": "system", "content": "Voce e um designer de ebooks. Descreva em 2 frases o estilo visual ideal para um ebook."},
            {"role": "user", "content": f"Estilo: {self.state.style_id}. Nicho: {self.state.niche}. Titulo: {self.state.book_title}"},
        ])
        cover_brief = resp.strip()

        self._update_macro(sid, "completed", 100, f"Ebook criado: {self.state.book_id}", {
            "book_id": self.state.book_id, "book_title": self.state.book_title,
        })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 2: PESQUISA — Minerar dores reais do publico
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_pesquisa(self):
        from agents.llm import query_llm

        sid = "pesquisa"
        self._update_macro(sid, "active", 5, "Iniciando pesquisa de mercado...")

        pain_data = {
            "reddit_questions": [],
            "youtube_comments": [],
            "people_also_ask": [],
            "keywords": [],
            "pain_ranking": [],
            "desire_ranking": [],
            "objections": [],
            "recurring_questions": [],
            "audience_language": [],
            "hidden_pains": [],
        }

        # 1. Reddit mining
        self._update_macro(sid, "active", 15, "Buscando dores no Reddit...")
        try:
            from modules.blog_pipeline import get_reddit_questions
            reddit_qs = await get_reddit_questions(self.state.niche, self.state.language)
            pain_data["reddit_questions"] = reddit_qs
            self._update_macro(sid, "active", 25, f"Reddit: {len(reddit_qs)} perguntas encontradas")
        except Exception as e:
            print(f"[EbookPipeline] Reddit fallback: {e}")
            pain_data["reddit_questions"] = [
                f"Como resolver problemas com {self.state.niche}?",
                f"Quais sao as maiores dificuldades em {self.state.niche}?",
                f"Por que e tao dificil lidar com {self.state.niche}?",
            ]

        # 2. Google People Also Ask
        self._update_macro(sid, "active", 35, "Buscando People Also Ask...")
        try:
            from modules.keyword_miner import research_keywords
            kw_result = await research_keywords(self.state.niche, self.state.language, max_results=30)
            pain_data["keywords"] = [k.get("keyword", "") for k in kw_result.get("keywords", [])]
            pain_data["people_also_ask"] = kw_result.get("people_also_ask", [])
            self._update_macro(sid, "active", 50,
                f"Keywords: {len(pain_data['keywords'])} | PAA: {len(pain_data['people_also_ask'])}")
        except Exception as e:
            print(f"[EbookPipeline] KeywordMiner fallback: {e}")

        # 3. Analise de dores via LLM
        self._update_macro(sid, "active", 60, "Analisando dores do publico...")

        context_parts = []
        if pain_data["reddit_questions"]:
            context_parts.append("PERGUNTAS DO REDDIT:\n" + "\n".join(
                f"- {q}" for q in pain_data["reddit_questions"][:10]))
        if pain_data["people_also_ask"]:
            context_parts.append("PEOPLE ALSO ASK:\n" + "\n".join(
                f"- {q}" for q in pain_data["people_also_ask"][:10]))
        if pain_data["keywords"]:
            context_parts.append("KEYWORDS:\n" + ", ".join(pain_data["keywords"][:15]))

        context_text = "\n\n".join(context_parts) if context_parts else f"Nicho: {self.state.niche}"

        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um pesquisador de mercado especializado em mineração de dores. "
                "Analise os dados e retorne APENAS um JSON valido com as seguintes chaves: "
                "pain_ranking (lista dos 10 maiores dores), desire_ranking (10 desejos), "
                "objections (5 objecoes), recurring_questions (5 perguntas), "
                "audience_language (5 expressoes do publico), hidden_pains (3 dores ocultas). "
                "Cada item deve ser uma string curta."
            )},
            {"role": "user", "content": f"Nicho: {self.state.niche}\n\n{context_text}"},
        ])

        try:
            # Tentar parsear JSON
            cleaned = resp.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            analysis = json.loads(cleaned)
            pain_data.update(analysis)
        except (json.JSONDecodeError, Exception) as e:
            print(f"[EbookPipeline] Erro ao parsear analise LLM: {e}")
            pain_data["pain_ranking"] = [
                f"Dificuldade com {self.state.niche}",
                "Falta de orientacao clara",
                "Sensacao de estar perdido",
                "Falta de tempo",
                "Informacao fragmentada",
            ]
            pain_data["desire_ranking"] = [
                "Ter um passo a passo claro",
                "Resolver o problema rapidamente",
                "Economizar tempo",
                "Sentir seguranca",
                "Ter resultados",
            ]

        self.state.pain_research = pain_data
        self._update_macro(sid, "completed", 100, "Pesquisa concluida!", {
            "pain_count": len(pain_data.get("pain_ranking", [])),
            "desire_count": len(pain_data.get("desire_ranking", [])),
        })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 3: OFERTA — Criar proposta de valor + mecanismo unico
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_oferta(self):
        from agents.llm import query_llm
        from modules.database import update_db_book

        sid = "oferta"
        self._update_macro(sid, "active", 10, "Criando oferta...")

        pain_context = json.dumps(self.state.pain_research, ensure_ascii=False)[:3000]

        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um copywriter experiente em infoprodutos low-ticket (R$17-R$47). "
                "Crie a oferta completa do ebook. Retorne APENAS um JSON valido com: "
                "product_name (max 4 palavras), "
                "pain_structure: {emotion, obstacle, desire}, "
                "promise (promessa transformadora com mecanismo unico, niveis 3-4 de Schwartz), "
                "unique_mechanism: {name, description}, "
                "bonus_ideas (lista de 2 bônus), "
                "evaluation: {demand (0-100), latent_pain (0-100), specificity (0-100), unique_mechanism (0-100)}. "
                "O mecanismo unico deve ter nome proprio (ex: Protocolo 3x7, Fórmula Cérebro Slim). "
                "Use estilo MrBeast na promessa: curiosidade extrema, quebra de padrao."
            )},
            {"role": "user", "content": f"Nicho: {self.state.niche}\n\nDADOS DA PESQUISA:\n{pain_context}"},
        ])

        try:
            cleaned = resp.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            offer = json.loads(cleaned)
        except (json.JSONDecodeError, Exception) as e:
            print(f"[EbookPipeline] Erro ao parsear oferta: {e}")
            offer = {
                "product_name": self.state.book_title or f"Guia {self.state.niche}",
                "pain_structure": {
                    "emotion": "frustracao",
                    "obstacle": "falta de direcao",
                    "desire": "ter clareza e resultados",
                },
                "promise": f"O metodo definitivo para resolver problemas de {self.state.niche} sem complicacao",
                "unique_mechanism": {
                    "name": f"Metodo Dezafira",
                    "description": f"Abordagem unica para {self.state.niche}",
                },
                "bonus_ideas": [
                    {"name": "Checklist Rapido", "value_cents": 2700},
                    {"name": "Templates Prontos", "value_cents": 3700},
                ],
                "evaluation": {"demand": 70, "latent_pain": 65, "specificity": 60, "unique_mechanism": 55},
            }

        self.state.offer_data = offer

        # Atualizar titulo do ebook se o copywriter gerou um melhor
        if offer.get("product_name"):
            self.state.book_title = offer["product_name"]
            update_db_book(self.state.book_id, title=offer["product_name"])

        # Calcular score medio da avaliacao
        eval_scores = offer.get("evaluation", {})
        avg_score = sum(eval_scores.values()) / max(len(eval_scores), 1)

        self._update_macro(sid, "completed", 100,
            f"Oferta criada: {offer.get('product_name', '?')} | Score: {avg_score:.0f}%", {
                "product_name": offer.get("product_name"),
                "promise": offer.get("promise", "")[:100],
                "avg_score": avg_score,
            })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 4: PRODUCAO — Gerar conteudo capitulo por capitulo
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_producao(self):
        from agents.llm import query_llm
        from modules.database import create_db_book_chapter, update_db_book, get_db_book
        from modules.lili import lili_review_after_generation

        sid = "producao"
        target = self.state.target_chapters
        self._update_macro(sid, "active", 5, f"Gerando {target} capitulos...")

        # 1. Gerar persona
        self._update_macro(sid, "active", 8, "Definindo persona...")
        offer_context = json.dumps(self.state.offer_data, ensure_ascii=False)[:2000]
        pain_context = json.dumps(self.state.pain_research, ensure_ascii=False)[:2000]

        persona_resp = await query_llm([
            {"role": "system", "content": (
                "Crie uma persona detalhada para o ebook. Retorne JSON com: "
                "name, age, context, fears (lista), frustrations (lista), "
                "desires (lista), already_tried (lista). Max 200 tokens."
            )},
            {"role": "user", "content": f"Nicho: {self.state.niche}\nOferta: {offer_context}\nDores: {pain_context}"},
        ])
        try:
            cleaned = persona_resp.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            self.state.persona = json.loads(cleaned)
        except Exception:
            self.state.persona = {"name": "Leitor", "age": "25-45", "frustrations": ["falta de direcao"]}

        # 2. Gerar estrutura (sumario)
        self._update_macro(sid, "active", 15, "Criando sumario...")
        offer_data = self.state.offer_data
        mechanism = offer_data.get("unique_mechanism", {})
        promise = offer_data.get("promise", "")

        sumario_resp = await query_llm([
            {"role": "system", "content": (
                f"Crie a estrutura de um ebook com {target} capitulos. "
                "A jornada deve seguir: conexao com dor → clareza → quebra de crenças → "
                "mecanismo unico → passo a passo → exercicios → consolidacao. "
                "Retorne APENAS uma lista JSON de capitulos: "
                '[{"number": 1, "title": "...", "description": "..."}]'
            )},
            {"role": "user", "content": (
                f"Titulo: {self.state.book_title}\n"
                f"Promessa: {promise}\n"
                f"Mecanismo: {mechanism.get('name', 'Metodo')}\n"
                f"Persona: {json.dumps(self.state.persona, ensure_ascii=False)[:500]}"
            )},
        ])

        try:
            cleaned = sumario_resp.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            self.state.chapters_structure = json.loads(cleaned)
        except Exception:
            self.state.chapters_structure = [
                {"number": i + 1, "title": f"Capitulo {i + 1}", "description": ""}
                for i in range(target)
            ]

        self._update_macro(sid, "active", 20, f"Sumario: {len(self.state.chapters_structure)} capitulos")

        # 3. Gerar cada capitulo
        total_words = 0
        all_scores = []
        previous_summary = ""

        for idx, ch in enumerate(self.state.chapters_structure):
            if self.state.status != "running":
                return

            ch_num = ch.get("number", idx + 1)
            ch_title = ch.get("title", f"Capitulo {ch_num}")
            ch_desc = ch.get("description", "")
            progress = 20 + int(60 * (idx / max(len(self.state.chapters_structure), 1)))

            self._update_macro(sid, "active", progress,
                f"[{idx + 1}/{len(self.state.chapters_structure)}] Escrevendo: {ch_title[:50]}...")

            # Gerar conteudo do capitulo
            chapter_resp = await query_llm([
                {"role": "system", "content": (
                    f"Voce e um ghostwriter profissional. Escreva o capitulo {ch_num} "
                    f"do ebook '{self.state.book_title}'.\n"
                    f"Estilo: didatico, acessivel, com exemplos praticos.\n"
                    f"Tom: acolhedor, motivador, direto.\n"
                    f"Minimo 1000 palavras.\n"
                    f"Estrutura obrigatoria: abertura empatica → conceito central → "
                    f"exemplos praticos → exercicio/reflexao → fechamento.\n"
                    f"Use markdown: ## para titulos, ** para negrito, - para listas.\n"
                    f"Nao use travessao (—).\n"
                    f"Se houver mecanismo unico, explique com nome proprio: {mechanism.get('name', '')}"
                )},
                {"role": "user", "content": (
                    f"Capitulo: {ch_title}\n"
                    f"Descricao: {ch_desc}\n"
                    f"Contexto dos capitulos anteriores:\n{previous_summary}\n\n"
                    f"Promessa do ebook: {promise}\n"
                    f"Persona: {json.dumps(self.state.persona, ensure_ascii=False)[:400]}"
                )},
            ], max_tokens=8192)

            # Salvar capitulo no banco
            ch_result = create_db_book_chapter(
                self.state.book_id, ch_num, ch_title, chapter_resp
            )

            if "error" not in ch_result:
                total_words += ch_result.get("word_count", 0)
                self.state.chapters_generated.append({
                    "chapter_number": ch_num, "title": ch_title,
                    "word_count": ch_result.get("word_count", 0),
                    "post_id": ch_result.get("id"),
                    "success": True,
                })
                previous_summary += f"\nCap {ch_num}: {ch_title}\n"

            # Checkpoint a cada 2 capitulos
            if (idx + 1) % 2 == 0:
                await self._save_checkpoint()

        self.state.total_words = total_words

        # 4. Gerar capa
        self._update_macro(sid, "active", 85, "Gerando capa...")
        try:
            from agents.image_factory import image_agent
            cover_result = await image_agent.generate_cover(
                self.state.book_title, self.state.niche, self.state.style_id
            )
            if cover_result and cover_result.get("url"):
                self.state.cover_url = cover_result["url"]
                from modules.database import update_db_book
                update_db_book(self.state.book_id, cover_url=cover_result["url"])
        except Exception as e:
            print(f"[EbookPipeline] Capa fallback: {e}")

        # 5. Salvar dados da producao
        update_db_book(self.state.book_id,
            total_words=total_words,
            persona=json.dumps(self.state.persona, ensure_ascii=False),
            pain_research=json.dumps(self.state.pain_research, ensure_ascii=False),
            offer_data=json.dumps(self.state.offer_data, ensure_ascii=False),
        )

        self._update_macro(sid, "completed", 100,
            f"Producao concluida! {len(self.state.chapters_generated)} capitulos, ~{total_words} palavras", {
                "chapters": len(self.state.chapters_generated),
                "total_words": total_words,
            })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 5: REFINO — Diagramacao + Pagina de vendas
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_refino(self):
        from agents.llm import query_llm
        from modules.database import update_db_book, get_db_book

        sid = "refino"
        self._update_macro(sid, "active", 10, "Gerando HTML do ebook...")

        # Buscar capítulos do banco
        book_data = get_db_book(self.state.book_id)
        chapters = book_data.get("chapters", [])

        # 1. Gerar HTML do ebook formatado
        chapters_html = ""
        for ch in chapters:
            content = ch.get("content", "")
            paragraphs = "".join(
                f"<p>{p.strip()}</p>" for p in content.split("\n\n") if p.strip()
            )
            chapters_html += f"""
            <div class="chapter" id="cap-{ch['chapter_number']}">
                <h2>Capitulo {ch['chapter_number']}: {ch['title']}</h2>
                {paragraphs}
            </div>"""

        ebook_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self.state.book_title}</title>
<style>
  body {{ font-family: Georgia, serif; line-height: 1.8; max-width: 700px;
         margin: 0 auto; padding: 40px 20px; color: #1a1a1a; }}
  h1 {{ text-align: center; font-size: 28px; margin-bottom: 10px; }}
  h2 {{ font-size: 22px; margin-top: 40px; color: #2d3436; border-bottom: 2px solid #d4af37; padding-bottom: 8px; }}
  p {{ margin-bottom: 16px; text-indent: 1.5em; }}
  .chapter {{ page-break-before: always; }}
  .cover {{ text-align: center; padding: 60px 20px; page-break-after: always; }}
  .cover h1 {{ font-size: 36px; margin-bottom: 20px; }}
  .subtitle {{ font-style: italic; color: #636e72; font-size: 18px; }}
  blockquote {{ border-left: 4px solid #d4af37; padding: 12px 20px; margin: 20px 0;
               background: #f9f6f0; font-style: italic; }}
</style>
</head>
<body>
<div class="cover">
  <h1>{self.state.book_title}</h1>
  <p class="subtitle">{self.state.offer_data.get('promise', '')[:100]}</p>
  <p>por {book_data.get('author', 'Dezafira Editorial')}</p>
</div>
{chapters_html}
</body>
</html>"""

        update_db_book(self.state.book_id, sales_page_html=ebook_html)
        self._update_macro(sid, "active", 40, "Ebook HTML gerado!")

        # 2. Gerar pagina de vendas
        self._update_macro(sid, "active", 50, "Montando pagina de vendas...")
        offer = self.state.offer_data

        sales_resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um copywriter de paginas de vendas de alta conversao para ebooks low-ticket. "
                "Gere o HTML completo da pagina de vendas (Apenas o conteudo do body, sem <html> ou <head>). "
                "Use CSS inline. Mobile-first. Sections: "
                "1. Hero com headline gigante + subheadline + botao CTA "
                "2. O que voce vai desbloquear (6 cards) "
                "3. Secao emocional (dor do avatar) "
                "4. Bônus (2 cards) "
                "5. Stack da oferta com preco ancorado "
                "6. FAQ (6 perguntas) "
                "7. CTA final "
                "8. Disclaimer + footer "
                "Botoes grandes (min-height 48px), cores: #d4af37 (dourado) + #1a1a2e (escuro). "
                "Max 500KB. Fonte: Google Fonts (Inter). "
                "O link de checkout deve ser: /checkout/{book_id}"
            )},
            {"role": "user", "content": (
                f"Titulo: {self.state.book_title}\n"
                f"Promessa: {offer.get('promise', '')}\n"
                f"Mecanismo: {offer.get('unique_mechanism', {}).get('name', '')}\n"
                f"Bônus: {json.dumps(offer.get('bonus_ideas', []), ensure_ascii=False)}\n"
                f"Preco: R${self.state.price_cents // 100},00\n"
                f"Book ID: {self.state.book_id}"
            )},
        ], max_tokens=16384)

        # Limpar possiveis marcadores de codigo
        sales_html = sales_resp.strip()
        if sales_html.startswith("```"):
            sales_html = sales_html.split("\n", 1)[1].rsplit("```", 1)[0]

        self.state.sales_page_html = sales_html
        import unicodedata
        slug = unicodedata.normalize("NFKD", self.state.book_title.lower())
        slug = slug.encode("ascii", "ignore").decode("ascii")
        slug = slug.replace(" ", "-").replace(".", "")[:60].strip("-")
        self.state.sales_page_slug = slug

        update_db_book(self.state.book_id,
            sales_page_html=sales_html,
            sales_page_slug=slug,
        )

        self._update_macro(sid, "completed", 100, "Refino concluido!", {
            "slug": slug,
        })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 6: ENTREGA — Validacao final + checkout + publicacao
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_entrega(self):
        from modules.database import (
            update_db_book, update_db_ebook_pipeline_run, create_db_product,
            get_db_book
        )

        sid = "entrega"
        self._update_macro(sid, "active", 10, "Validacao final...")

        book = get_db_book(self.state.book_id)

        # Validacoes
        issues = []
        if not book.get("cover_url"):
            issues.append("Sem capa")
        if book.get("total_words", 0) < 3000:
            issues.append(f"Poucas palavras: {book.get('total_words', 0)}")
        if not self.state.sales_page_html:
            issues.append("Sem pagina de vendas")

        if len(issues) > 0:
            self._update_macro(sid, "active", 30, f"Avisos: {', '.join(issues)}")

        # Criar produto para checkout
        self._update_macro(sid, "active", 50, "Criando produto para checkout...")
        product = create_db_product(
            book_id=self.state.book_id,
            name=self.state.book_title,
            price_cents=self.state.price_cents,
            description=self.state.offer_data.get("promise", "")[:200],
        )

        checkout_url = f"/checkout/{product['id']}"
        self.state.checkout_url = checkout_url

        update_db_book(self.state.book_id,
            checkout_url=checkout_url,
            status="published",
        )

        # Atualizar pipeline run
        update_db_ebook_pipeline_run(self.state.pipeline_run_id,
            status="completed",
            phase="entrega",
            completed_at=datetime.utcnow(),
            pipeline_data=json.dumps(self.state.to_dict(), ensure_ascii=False, default=str),
        )

        self._update_macro(sid, "completed", 100,
            f"Entrega concluida! Checkout: {checkout_url}", {
                "product_id": product["id"],
                "checkout_url": checkout_url,
                "sales_page": f"/ebook/{self.state.sales_page_slug}/venda",
            })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECKPOINT
    # ═══════════════════════════════════════════════════════════════════════════

    async def _save_checkpoint(self):
        try:
            from modules.database import update_db_ebook_pipeline_run
            update_db_ebook_pipeline_run(self.state.pipeline_run_id,
                phase=self.state.current_macro_stage,
                pipeline_data=json.dumps({
                    "stages": self.state.macro_stages,
                    "chapters": self.state.chapters_generated,
                    "pain_research": self.state.pain_research,
                    "offer_data": self.state.offer_data,
                    "persona": self.state.persona,
                    "total_words": self.state.total_words,
                }, ensure_ascii=False, default=str),
            )
        except Exception as e:
            print(f"[EbookPipeline] Checkpoint falhou: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCOES DE ALTO NIVEL
# ═══════════════════════════════════════════════════════════════════════════════

async def run_ebook_macro_pipeline(niche: str, book_title: str = "",
                             blog_channel_id: str = "", style_id: str = "minimalista",
                             price_cents: int = 1700, target_chapters: int = 8,
                             language: str = "pt", task_id: str = None,
                             on_progress: Callable = None) -> dict:
    pipeline = EbookMacroPipeline(on_progress=on_progress)
    state = await pipeline.execute(
        niche=niche, book_title=book_title,
        blog_channel_id=blog_channel_id, style_id=style_id,
        price_cents=price_cents, target_chapters=target_chapters,
        language=language, task_id=task_id,
    )
    return state.to_dict()
