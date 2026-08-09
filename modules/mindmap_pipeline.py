"""
Fabrica de Mapas Mentais — Macro-pipeline com 6 fases.
Fluxo: Fundacao → Pesquisa → Oferta → Producao → Refino → Entrega
Orquestra a geracao de mapas mentais estruturados in JSON para recorrencia.
"""
import os
import json
import uuid
import traceback
from datetime import datetime
from typing import Optional, Callable, Any
from agents.llm import query_llm

# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO DA PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

class MindMapMacroState:
    """Estado completo da macro-pipeline de mapas mentais."""

    def __init__(self):
        self.task_id: str = ""
        self.mindmap_id: str = ""
        self.niche: str = ""
        self.language: str = "pt"
        self.title: str = ""
        self.style_id: str = "minimalista"
        self.price_cents: int = 1700
        self.status: str = "idle"
        self.current_macro_stage: str = ""
        self.macro_stages: dict = {}
        self.pain_research: dict = {}
        self.offer_data: dict = {}
        self.map_json: str = ""
        self.sales_page_html: str = ""
        self.sales_page_slug: str = ""
        self.checkout_url: str = ""
        self.cover_url: str = ""
        self.pipeline_run_id: str = ""
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "mindmap_id": self.mindmap_id,
            "niche": self.niche,
            "title": self.title,
            "style_id": self.style_id,
            "price_cents": self.price_cents,
            "status": self.status,
            "current_macro_stage": self.current_macro_stage,
            "macro_stages": self.macro_stages,
            "pain_research": self.pain_research,
            "offer_data": self.offer_data,
            "map_json": self.map_json[:500] + "..." if self.map_json else "",
            "sales_page_slug": self.sales_page_slug,
            "checkout_url": self.checkout_url,
            "cover_url": self.cover_url,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MACRO-PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class MindMapMacroPipeline:
    """Pipeline de 6 fases para criacao de mapas mentais."""

    def __init__(self, on_progress: Callable = None):
        self.state = MindMapMacroState()
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
            "title": self.state.title,
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

    async def execute(self, niche: str, title: str = "", style_id: str = "minimalista",
                      price_cents: int = 1700, language: str = "pt",
                      task_id: str = None) -> MindMapMacroState:
        self.state.task_id = task_id or f"mmpipe_{uuid.uuid4().hex[:8]}"
        self.state.niche = niche
        self.state.title = title
        self.state.style_id = style_id
        self.state.price_cents = price_cents
        self.state.language = language
        self.state.status = "running"
        self.state.started_at = datetime.utcnow()

        self._emit("pipeline_started", {
            "task_id": self.state.task_id,
            "niche": niche, "title": title,
        })

        try:
            await self._run_macro("fundacao", "Fundacao", self._phase_fundacao)
            await self._run_macro("pesquisa", "Pesquisa de Dores", self._phase_pesquisa)
            await self._run_macro("oferta", "Criar Oferta", self._phase_oferta)
            await self._run_macro("producao", "Producao do Mapa", self._phase_producao)
            await self._run_macro("refino", "Refino de Estilo", self._phase_refino)
            await self._run_macro("entrega", "Entrega", self._phase_entrega)

            self.state.status = "completed"
            self.state.completed_at = datetime.utcnow()
            self._emit("pipeline_complete", self.state.to_dict())

        except Exception as e:
            self.state.status = "failed"
            self.state.error = str(e)
            self.state.completed_at = datetime.utcnow()
            print(f"[MindMapPipeline] PIPELINE_FAILED: {e}")
            traceback.print_exc()
            self._emit("pipeline_failed", {
                **self.state.to_dict(),
                "error_detail": traceback.format_exc(),
            })

        return self.state

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 1: FUNDACAO — Criar mapa no banco
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_fundacao(self):
        from modules.database import create_db_mindmap, create_db_mindmap_pipeline_run, update_db_mindmap

        sid = "fundacao"
        self._update_macro(sid, "active", 10, "Criando mapa mental no banco...")

        if not self.state.title:
            resp = await query_llm([
                {"role": "system", "content": "Voce e um criador de conteudos educativos."},
                {"role": "user", "content": f"Crie um titulo curto (max 5 palavras) para um mapa mental pratico sobre: {self.state.niche}. Responda APENAS com o titulo."},
            ])
            self.state.title = resp.strip().strip('"').strip("'")

        self._update_macro(sid, "active", 40, f"Titulo definido: {self.state.title}")

        mindmap = create_db_mindmap(
            title=self.state.title,
            topic=self.state.niche,
            niche=self.state.niche,
            price_cents=self.state.price_cents,
        )
        self.state.mindmap_id = mindmap["id"]

        pipeline_run = create_db_mindmap_pipeline_run(self.state.mindmap_id)
        self.state.pipeline_run_id = pipeline_run["id"]

        update_db_mindmap(self.state.mindmap_id,
            style_id=self.state.style_id,
            pipeline_run_id=self.state.pipeline_run_id,
        )

        self._update_macro(sid, "completed", 100, f"Mapa mental criado no banco: {self.state.mindmap_id}", {
            "mindmap_id": self.state.mindmap_id, "title": self.state.title,
        })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 2: PESQUISA — Minerar dúvidas e dores
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_pesquisa(self):
        sid = "pesquisa"
        self._update_macro(sid, "active", 20, "Pesquisando temas quentes de estudos...")

        pain_data = {
            "keywords": [self.state.niche],
            "pain_ranking": [f"Dificuldade em entender {self.state.niche}"],
            "desire_ranking": [f"Dominar {self.state.niche} de forma visual"],
        }

        try:
            from modules.keyword_miner import research_keywords
            kw_result = await research_keywords(self.state.niche, self.state.language, max_results=15)
            if kw_result and kw_result.get("keywords"):
                pain_data["keywords"] = [k.get("keyword", "") for k in kw_result.get("keywords", [])]
        except Exception as e:
            print(f"[MindMapPipeline] Keyword research fallback: {e}")

        # LLM para consolidar os tópicos e termos ideais
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um pesquisador focado em design de aprendizado. "
                "Retorne um JSON com: keywords (lista com 5 termos chave), "
                "frequent_questions (5 maiores duvidas) e common_mistakes (3 maiores erros de estudantes nesse tema). "
                "Responda apenas com o JSON valido."
            )},
            {"role": "user", "content": f"Tema: {self.state.niche}. Palavras-chave brutas: {', '.join(pain_data['keywords'])}"},
        ])

        try:
            cleaned = resp.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            pain_data.update(json.loads(cleaned))
        except Exception:
            pass

        self.state.pain_research = pain_data
        self._update_macro(sid, "completed", 100, "Pesquisa concluida!", {
            "keywords": pain_data.get("keywords"),
        })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 3: OFERTA — Posicionamento do infoproduto recorrente
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_oferta(self):
        sid = "oferta"
        self._update_macro(sid, "active", 30, "Montando copy de oferta...")

        pain_context = json.dumps(self.state.pain_research, ensure_ascii=False)[:2000]

        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um copywriter de infoprodutos recorrentes. "
                "Crie uma oferta estruturada. Retorne um JSON com: "
                "promise (promessa de aprendizado rapido), unique_mechanism (mecanismo visual ex: Metodo Ancoras Visuais), "
                "pricing_anchoring (preco ancorado vs real)."
            )},
            {"role": "user", "content": f"Tema: {self.state.niche}\nPesquisa: {pain_context}"},
        ])

        try:
            cleaned = resp.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            self.state.offer_data = json.loads(cleaned)
        except Exception:
            self.state.offer_data = {
                "promise": f"Domine {self.state.niche} em 7 dias usando memorizacao visual acelerada.",
                "unique_mechanism": "Metodo Ancoras Visuais",
                "pricing_anchoring": "De R$ 97,00 por apenas R$ 19,90/mes"
            }

        self._update_macro(sid, "completed", 100, "Oferta gerada com sucesso!", self.state.offer_data)
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 4: PRODUCAO — Geração do Mapa Mental em JSON Hierárquico
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_producao(self):
        sid = "producao"
        self._update_macro(sid, "active", 10, "Gerando estrutura do Mapa Mental...")

        prompt = f"""Crie um mapa mental aprofundado e altamente estruturado sobre o tema: {self.state.niche}.
O mapa deve focar na clareza didatica e reducao de sobrecarga cognitiva (chunking).

Retorne APENAS um JSON valido no formato abaixo, sem tags de formatacao:
{{
  "id": "raiz",
  "title": "{self.state.title}",
  "description": "Visao geral do mapa sobre {self.state.niche}",
  "children": [
    {{
      "id": "ramo_1",
      "title": "Titulo Curto do Ramo (max 4 palavras)",
      "description": "Explicação detalhada deste ramo (resumo didatico em formato de chunking)",
      "quiz": {{
        "question": "Pergunta objetiva de fixação sobre este ramo especifico",
        "options": ["Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D"],
        "answer": "Alternativa A"
      }},
      "children": [
        {{
          "id": "subramo_1_1",
          "title": "Subtópico Curto",
          "description": "Detalhes concisos deste subramo",
          "quiz": null,
          "children": []
        }}
      ]
    }}
  ]
}}

REGRAS CRITICAS:
1. O JSON deve ser perfeitamente valido e parseavel.
2. Crie de 3 a 5 ramos principais (`children` da raiz).
3. Cada ramo principal deve ter pelo menos 1 ou 2 subramos (`children`).
4. Pelo menos 4 nós no mapa devem conter um objeto `quiz` com pergunta, 4 opcoes e a resposta correta exata.
5. Use explicações curtas e ricas em analogias no campo `description`."""

        resp = await query_llm([
            {"role": "system", "content": "Voce e um Engenheiro de Aprendizagem especializado em mapas mentais interativos."},
            {"role": "user", "content": prompt},
        ], max_tokens=16384)

        try:
            cleaned = resp.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            
            # Validar se é JSON válido
            map_data = json.loads(cleaned)
            self.state.map_json = json.dumps(map_data, ensure_ascii=False)
            
            from modules.database import update_db_mindmap
            update_db_mindmap(self.state.mindmap_id, map_json=self.state.map_json)
            
            self._update_macro(sid, "completed", 100, "Mapa mental gerado com sucesso!", {
                "nodes_count": len(map_data.get("children", [])),
            })
        except Exception as e:
            # Fallback básico em caso de falha de parser
            fallback_map = {
                "id": "raiz",
                "title": self.state.title,
                "description": f"Estudo estruturado sobre {self.state.niche}",
                "children": [
                    {
                        "id": "node_fb_1",
                        "title": "Introdução Conceitual",
                        "description": "Bases conceituais para entender o tema.",
                        "quiz": {
                          "question": f"Qual é o objetivo principal ao estudar {self.state.niche}?",
                          "options": ["Aprender conceitos", "Apenas decorar", "Ignorar a teoria", "Nenhuma"],
                          "answer": "Aprender conceitos"
                        },
                        "children": []
                    },
                    {
                        "id": "node_fb_2",
                        "title": "Pilares Práticos",
                        "description": "Como aplicar a teoria no dia a dia.",
                        "quiz": None,
                        "children": []
                    }
                ]
            }
            self.state.map_json = json.dumps(fallback_map, ensure_ascii=False)
            from modules.database import update_db_mindmap
            update_db_mindmap(self.state.mindmap_id, map_json=self.state.map_json)
            
            self._update_macro(sid, "completed", 100, "Mapa mental gerado com fallback!", {
                "error": str(e)
            })

        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 5: REFINO — Geração da Página de Vendas Recorrente
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_refino(self):
        sid = "refino"
        self._update_macro(sid, "active", 20, "Criando página de vendas do Clube...")

        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um copywriter focado em assinaturas recorrentes (SaaS / Clubes). "
                "Crie uma pagina de vendas HTML reativa (Apenas o body e CSS inline). "
                "Use paleta elegante (#090d16 escuro, #38bdf8 azul de destaque). "
                "Destaque o trial de 7 dias grátis para acessar os mapas mentais interativos com flashcards. "
                "Adicione CTA apontando para o link: /checkout/{mindmap_id}."
            )},
            {"role": "user", "content": (
                f"Titulo: {self.state.title}\n"
                f"Promessa: {self.state.offer_data.get('promise', '')}\n"
                f"Nicho: {self.state.niche}\n"
                f"Mapa ID: {self.state.mindmap_id}"
            )},
        ], max_tokens=16384)

        sales_html = resp.strip()
        if sales_html.startswith("```"):
            sales_html = sales_html.split("\n", 1)[1].rsplit("```", 1)[0]

        self.state.sales_page_html = sales_html
        
        # Gerar slug
        import unicodedata
        slug = unicodedata.normalize("NFKD", self.state.title.lower())
        slug = slug.encode("ascii", "ignore").decode("ascii")
        slug = slug.replace(" ", "-").replace(".", "")[:60].strip("-")
        self.state.sales_page_slug = slug

        from modules.database import update_db_mindmap
        update_db_mindmap(self.state.mindmap_id,
            sales_page_html=sales_html,
            sales_page_slug=slug,
            checkout_url=f"/checkout/{self.state.mindmap_id}"
        )

        self._update_macro(sid, "completed", 100, "Página de vendas refinada!", {
            "slug": slug,
        })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 6: ENTREGA — Lançamento do Mapa
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_entrega(self):
        from modules.database import update_db_mindmap, update_db_mindmap_pipeline_run

        sid = "entrega"
        self._update_macro(sid, "active", 50, "Ativando mapa mental...")

        update_db_mindmap(self.state.mindmap_id, status="published")

        update_db_mindmap_pipeline_run(self.state.pipeline_run_id,
            status="completed",
            phase="entrega",
            completed_at=datetime.utcnow(),
            pipeline_data=json.dumps(self.state.to_dict(), ensure_ascii=False, default=str),
        )

        self._update_macro(sid, "completed", 100, "Mapa mental publicado com sucesso!", {
            "mindmap_id": self.state.mindmap_id,
            "url": f"/mapa-mental/{self.state.sales_page_slug}",
        })
        await self._save_checkpoint()

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECKPOINT
    # ═══════════════════════════════════════════════════════════════════════════

    async def _save_checkpoint(self):
        try:
            from modules.database import update_db_mindmap_pipeline_run
            update_db_mindmap_pipeline_run(self.state.pipeline_run_id,
                phase=self.state.current_macro_stage,
                pipeline_data=json.dumps({
                    "stages": self.state.macro_stages,
                    "pain_research": self.state.pain_research,
                    "offer_data": self.state.offer_data,
                    "map_json": self.state.map_json,
                }, ensure_ascii=False, default=str),
            )
        except Exception as e:
            print(f"[MindMapPipeline] Checkpoint falhou: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCOES DE ALTO NIVEL
# ═══════════════════════════════════════════════════════════════════════════════

async def run_mindmap_macro_pipeline(niche: str, title: str = "", style_id: str = "minimalista",
                                    price_cents: int = 1700, language: str = "pt",
                                    task_id: str = None, on_progress: Callable = None) -> dict:
    pipeline = MindMapMacroPipeline(on_progress=on_progress)
    state = await pipeline.execute(
        niche=niche, title=title, style_id=style_id,
        price_cents=price_cents, language=language, task_id=task_id,
    )
    return state.to_dict()
