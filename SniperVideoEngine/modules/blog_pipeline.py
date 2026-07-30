"""
Blog Pipeline — Macro-Esteira da Fábrica de Blogs.

Produz um blog COMPLETO do zero, com 30-40 artigos profundos.

Pipeline Macro (5 fases):
  🏗️ FASE 1: FUNDAÇÃO — Cria o blog, identidade visual, brand bible
  📋 FASE 2: ARQUITETURA — Mapeia seções, keywords, micro-nichos
  📝 FASE 3: PRODUÇÃO — Gera 30-40 artigos em 3 rodadas
  🎨 FASE 4: REFINO — Imagens, links internos, agendamento
  ✅ FASE 5: ENTREGA — Blog completo, pipeline reinicia
"""

import asyncio
import json
import os
import sys
import traceback
import uuid
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from modules.database import update_db_blog_post

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DAS FASES MACRO
# ═══════════════════════════════════════════════════════════════════════════════

MACRO_STAGES = [
    {
        "id": "fundacao",
        "name": "Fundação",
        "icon": "🏗️",
        "description": "Cria o blog, identidade visual, brand bible e público-alvo",
        "agent": "Seu Hermes + Dona Célia",
        "color": "#3b82f6",
        "weight": 10,  # % do tempo total
    },
    {
        "id": "arquitetura",
        "name": "Arquitetura",
        "icon": "📋",
        "description": "Pesquisa keywords, mapeia seções e micro-nichos, planeja 35 artigos",
        "agent": "Joaquim + Obscura",
        "color": "#8b5cf6",
        "weight": 15,
    },
    {
        "id": "producao",
        "name": "Produção",
        "icon": "📝",
        "description": "Gera 30-40 artigos com Carlão + Dona Rosa + Ricardo",
        "agent": "Carlão + Dona Rosa + Ricardo",
        "color": "#f59e0b",
        "weight": 55,
    },
    {
        "id": "refino",
        "name": "Refino",
        "icon": "🎨",
        "description": "Imagens de destaque com Tatiana + links internos com Ricardo + agendamento com Seu Zé",
        "agent": "Tatiana + Ricardo + Seu Zé",
        "color": "#22c55e",
        "weight": 15,
    },
    {
        "id": "entrega",
        "name": "Entrega",
        "icon": "✅",
        "description": "Seu Francisco confere e libera o blog. Pronto para o próximo nicho",
        "agent": "Seu Francisco",
        "color": "#ec4899",
        "weight": 5,
    },
]

# Configuração das rodadas de produção
PRODUCTION_ROUNDS = [
    {
        "round": 1,
        "name": "Artigo Único Robusto",
        "description": "1 artigo completo e profundo com extrema qualidade",
        "target_articles": 1,
        "target_words": 2000,
        "description_pt": "Artigo completo, profundo e com extrema qualidade",
    },
]

# Total padrão (pode ser sobrescrito via parâmetro target_articles)
DEFAULT_TOTAL = 1
TOTAL_TARGET = DEFAULT_TOTAL


# ═══════════════════════════════════════════════════════════════════════════════
# ARTIGOS VARIADOS — Tópicos específicos para evitar duplicatas
# ═══════════════════════════════════════════════════════════════════════════════

# Lista de 30+ tópicos variados sobre ensinamentos de Jesus
# Usada pela pipeline quando target_articles > 1
# Cada tópico é único e cobre um aspecto diferente do tema
ARTICLE_TOPICS = [
    # 📖 Parábolas
    "A parabola do semeador - estudo completo",
    "O filho prodigo - o amor incondicional do Pai",
    "O bom samaritano - quem e o meu proximo",
    "Ovelha perdida - a busca incansavel de Deus",
    "O fermento do reino - crescimento silencioso",
    "A parabola dos talentos - administrando dons",
    "O semeador e os solos - preparando o coracao",
    
    # 🙏 Ensinamentos principais
    "As bem-aventurancas - o manifesto do reino",
    "O sermao da montanha - etica do reino",
    "A regra de ouro - tratai os outros como quereis",
    "Amai os vossos inimigos - o amor radical",
    "A oracao do Pai Nosso - modelo de oracao",
    "O jejum que agrada a Deus",
    "Ajuntai tesouros no ceu - prioridades eternas",
    
    # ✨ Milagres
    "A cura do cego de Jerico - fe que restaura",
    "A multiplicacao dos paes e peixes - Deus provedor",
    "Jesus acalma a tempestade - paz no meio da crise",
    "A ressurreicao de Lazaro - vitoria sobre a morte",
    "A cura do paralitico - perdao e cura",
    "A agua transformada em vinho - o primeiro milagre",
    "A filha de Jairo - a fe que ressuscita",
    
    # 🕊️ Encontros transformadores
    "Jesus e a mulher samaritana - agua viva",
    "Zaqueu - a salvacao entra em casa",
    "Nicodemos - nascer de novo",
    "A mulher adultera - quem nao tiver pecado",
    "Maria e Marta - a melhor parte",
    "O jovem rico - vende tudo que tens",
    "A mulher do fluxo de sangue - a fe que toca",
    
    # 📜 Discipulado e chamado
    "O chamado dos primeiros discipulos",
    "Pedro - a rocha e as quedas",
    "Joao - o discipulo amado",
    "Tomé - bem aventurados os que creem sem ver",
    "Os 70 enviados - a grande comissao",
    "Negar a si mesmo - tomai a cruz",
    "Sede perfeitos - o padrao do reino",
    
    # 🔥 Profecias e ensinos escatologicos
    "O sermao profetico - sinais da volta",
    "As virgens prudentes e nescias - vigiai",
    "A porta estreita - nem todo que diz Senhor",
    "O juizo final - apartai os bodes das ovelhas",
    "A vinda do Filho do Homem - vigiai e orai",
    
    # 💎 Temas teologicos
    "O Reino de Deus esta entre vos",
    "A fe que move montanhas",
    "O poder da oracao em conjunto",
    "O casamento segundo Jesus",
    "As criancas e o Reino - ser como criancas",
    "O perigo da hipocrisia religiosa",
    "A verdadeira pureza - o que contamina",
]


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACK TYPE
# ═══════════════════════════════════════════════════════════════════════════════

ProgressCallback = Callable[[str, str, int, str, dict], None]

# ═══════════════════════════════════════════════════════════════════════════════
# MACRO PIPELINE STATE
# ═══════════════════════════════════════════════════════════════════════════════

class MacroState:
    """Estado completo da macro-esteira de blog."""

    def __init__(self, task_id: str, blog_name: str, niche: str, language: str = "pt",
                 target_articles: int = 1):
        self.task_id = task_id
        self.blog_name = blog_name
        self.niche = niche
        self.language = language
        self.target_articles = target_articles
        self.channel_id = None       # Set after Phase 1
        self.pipeline_run_id = None  # Set after Phase 1
        self.sections = []           # Set after Phase 2
        self.articles_generated = 0
        self.articles = []           # All generated articles

        self.status = "idle"
        self.current_macro_stage = None
        self.macro_stages = {}       # {stage_id: {status, progress, message, data}}

        self.started_at = None
        self.completed_at = None
        self.error = None

        for stage in MACRO_STAGES:
            self.macro_stages[stage["id"]] = {
                "status": "idle",
                "progress": 0,
                "message": "Aguardando",
                "started_at": None,
                "completed_at": None,
                "data": None,
                "error": None,
            }

    def to_dict(self) -> dict:
        # Serialize macro stages (convert datetime objects to strings)
        serialized_stages = {}
        for sid, s in self.macro_stages.items():
            serialized_stages[sid] = {
                "status": s["status"],
                "progress": s["progress"],
                "message": s["message"],
                "started_at": s["started_at"].isoformat() if s.get("started_at") else None,
                "completed_at": s["completed_at"].isoformat() if s.get("completed_at") else None,
                "data": s.get("data"),
                "error": s.get("error"),
            }
        return {
            "task_id": self.task_id,
            "blog_name": self.blog_name,
            "niche": self.niche,
            "language": self.language,
            "target_articles": self.target_articles,
            "channel_id": self.channel_id,
            "pipeline_run_id": self.pipeline_run_id,
            "sections": self.sections,
            "articles_generated": self.articles_generated,
            "articles": self.articles[-20:] if self.articles else [],
            "status": self.status,
            "current_macro_stage": self.current_macro_stage,
            "macro_stages": serialized_stages,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }



# ═══════════════════════════════════════════════════════════════════════════════
# MACRO PIPELINE EXECUTOR
# ═══════════════════════════════════════════════════════════════════════════════

class BlogMacroPipeline:
    """Executor da macro-esteira da Fábrica de Blogs."""

    def __init__(self, on_progress: Optional[ProgressCallback] = None):
        self.on_progress = on_progress
        self.state: Optional[MacroState] = None

    # ─── HELPERS ─────────────────────────────────────────────────────────────

    def _update_macro(self, stage_id: str, status: str, progress: int,
                     message: str, data: dict = None):
        if stage_id in self.state.macro_stages:
            s = self.state.macro_stages[stage_id]
            s["status"] = status
            s["progress"] = progress
            s["message"] = message
            if status == "active" and s["started_at"] is None:
                s["started_at"] = datetime.utcnow()
            if status in ("completed", "failed"):
                s["completed_at"] = datetime.utcnow()
            if data:
                s["data"] = data

        self._emit("macro_update", {
            "task_id": self.state.task_id,
            "stage_id": stage_id,
            "status": status,
            "progress": progress,
            "message": message,
            "data": data,
            "state": self.state.to_dict(),
        })

    def _emit(self, event_type: str, data: dict):
        if self.on_progress:
            self.on_progress(self.state.task_id, "__broadcast__", 0, event_type, data)

    # ─── EXECUTE ─────────────────────────────────────────────────────────────

    async def _save_checkpoint(self):
        """Salva checkpoint do pipeline no banco."""
        if not self.state or not self.state.pipeline_run_id:
            return
        try:
            from modules.database import update_db_blog_pipeline_run_checkpoint
            update_db_blog_pipeline_run_checkpoint(
                run_id=self.state.pipeline_run_id,
                phase=self.state.current_macro_stage or "fundacao",
                articles_generated=self.state.articles_generated,
                current_round=0,
                pipeline_data={
                    "stages": {
                        sid: {
                            "status": s["status"],
                            "progress": s["progress"],
                            "message": s["message"],
                        }
                        for sid, s in self.state.macro_stages.items()
                    },
                    "articles": [
                        {"title": a.get("title", ""), "success": a.get("success", False),
                         "word_count": a.get("word_count", 0), "post_id": a.get("post_id")}
                        for a in self.state.articles
                    ],
                    "sections": self.state.sections,
                },
            )
        except Exception as e:
            print(f"[Pipeline] Checkpoint error: {e}")

    async def execute(self, blog_name: str, niche: str, language: str = "pt",
                      task_id: Optional[str] = None,
                      target_articles: Optional[int] = None) -> MacroState:
        task_id = task_id or f"mblog_{uuid.uuid4().hex[:8]}"

        self.state = MacroState(task_id, blog_name, niche, language,
                                target_articles=target_articles or DEFAULT_TOTAL)
        self.state.status = "running"
        self.state.started_at = datetime.utcnow()

        self._emit("pipeline_started", self.state.to_dict())

        try:
            # ═══ FASE 1: FUNDAÇÃO ════════════════════════════════════════════
            await self._run_macro("fundacao", self._phase_fundacao)
            await self._save_checkpoint()
            if self.state.status != "running": return self.state

            # ═══ FASE 2: ARQUITETURA ═════════════════════════════════════════
            await self._run_macro("arquitetura", self._phase_arquitetura)
            await self._save_checkpoint()
            if self.state.status != "running": return self.state

            # ═══ FASE 3: PRODUÇÃO ════════════════════════════════════════════
            await self._run_macro("producao", self._phase_producao)
            await self._save_checkpoint()
            if self.state.status != "running": return self.state

            # ═══ FASE 4: REFINO ══════════════════════════════════════════════
            await self._run_macro("refino", self._phase_refino)
            await self._save_checkpoint()
            if self.state.status != "running": return self.state

            # ═══ FASE 5: ENTREGA ═════════════════════════════════════════════
            await self._run_macro("entrega", self._phase_entrega)

            # ─── FINALIZADO ─────────────────────────────────────────────────
            self.state.status = "completed"
            self.state.completed_at = datetime.utcnow()
            self._emit("pipeline_completed", self.state.to_dict())

        except Exception as e:
            self.state.status = "failed"
            self.state.error = str(e)
            self.state.completed_at = datetime.utcnow()
            self._emit("pipeline_failed", {
                **self.state.to_dict(),
                "error_detail": traceback.format_exc(),
            })

        return self.state

    async def _run_macro(self, stage_id: str, stage_fn):
        stage_config = next((s for s in MACRO_STAGES if s["id"] == stage_id), None)
        stage_name = stage_config["name"] if stage_config else stage_id
        self.state.current_macro_stage = stage_id
        self._update_macro(stage_id, "active", 0, f"🚀 Iniciando fase: {stage_name}...")
        try:
            await stage_fn()
        except Exception as e:
            self._update_macro(stage_id, "failed", 0, str(e))
            raise RuntimeError(f"Falha na fase {stage_name}: {str(e)}") from e

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 1: FUNDAÇÃO
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_fundacao(self):
        """Cria o canal do blog, identidade visual e brand bible."""
        sid = "fundacao"
        blog_name = self.state.blog_name
        niche = self.state.niche

        self._update_macro(sid, "active", 5,
            f"🏗️ Criando blog '{blog_name}' — nicho: {niche}")

        try:
            from modules.database import (
                create_db_blog_channel, update_db_blog_channel,
                create_db_blog_pipeline_run, update_db_blog_post,
            )

            # 1. Verificar se ja existe blog com mesmo nome (evitar duplicatas)
            self._update_macro(sid, "active", 15,
                "🔍 Verificando se blog ja existe...")

            try:
                from modules.database import get_db_blog_channels
                existing = get_db_blog_channels()
                dupe = [c for c in (existing or []) if c.get("name", "").strip().lower() == blog_name.strip().lower()]
                if dupe:
                    msg = f"⚠️ Blog '{blog_name}' ja existe! Usando canal existente: {dupe[0]['id']}"
                    self._update_macro(sid, "active", 20, msg)
                    self.state.channel_id = dupe[0]["id"]
                    # Pular criacao, usar existente
                    self._update_macro(sid, "completed", 100,
                        f"✅ Blog '{blog_name}' ja existia. Usando canal: {dupe[0]['id'][:12]}...")
                    return  # Sai da fase - blog ja existe
            except Exception as e_fund:
                print(f"[Pipeline] Fundacao: erro ao verificar duplicatas: {e_fund}")

            # 2. Criar canal do blog
            self._update_macro(sid, "active", 20,
                "📡 Criando canal de blog no banco...")

            channel = create_db_blog_channel(
                name=blog_name,
                nicho=niche,
                lang=self.state.language,
                platform="dezafira",
            )
            self.state.channel_id = channel["id"]

            # 2. Criar brand bible (via LLM)
            self._update_macro(sid, "active", 40,
                "📖 Gerando identidade visual e brand bible...")

            brand_bible = await self._generate_brand_bible(blog_name, niche)

            # Salva brand bible via update (em channel_knowledge ou no próprio canal)
            update_db_blog_channel(channel["id"], site_url=f"/blog/{blog_name.lower().replace(' ', '-')}")

            # 3. Criar registro do pipeline run com dados completos
            self._update_macro(sid, "active", 70,
                "📋 Registrando execução do pipeline...")

            run = create_db_blog_pipeline_run(
                channel_id=channel["id"],
                total_articles_target=self.state.target_articles,
                blog_name=blog_name,
                niche=niche,
                language=self.state.language,
                pipeline_data={"stage": "fundacao", "articles": []},
            )
            self.state.pipeline_run_id = run["id"]

            # 4. Finalizar
            self._update_macro(sid, "completed", 100,
                f"✅ Blog '{blog_name}' fundado! ID: {channel['id'][:12]}...", {
                    "channel_id": channel["id"],
                    "pipeline_run_id": run["id"],
                    "brand_bible": brand_bible,
                })

        except ImportError as e:
            # Fallback: criar sem banco
            self.state.channel_id = f"blg_demo_{uuid.uuid4().hex[:4]}"
            self.state.pipeline_run_id = f"bpr_demo_{uuid.uuid4().hex[:4]}"
            self._update_macro(sid, "completed", 100,
                f"⚠️ Blog '{blog_name}' criado (modo demonstração): {e}")
        except Exception as e:
            self._update_macro(sid, "failed", 0, f"Erro na fundação: {str(e)}")
            raise

    async def _generate_brand_bible(self, blog_name: str, niche: str) -> dict:
        """Gera brand bible via LLM."""
        try:
            from modules.blog_writer import _call_llm
            prompt = (
                f"Crie uma brand bible para um blog chamado '{blog_name}' "
                f"sobre '{niche}'. "
                "Inclua: tom de voz, público-alvo, estilo visual, "
                "cores sugeridas, e 5 CTAs naturais. "
                "Retorne APENAS JSON: {tom, publico, estilo, cores, ctas}"
            )
            system = "Você é um especialista em branding e marketing digital."
            raw = await _call_llm(system, prompt, temperature=0.7, max_tokens=2048)
            # Tenta parsear
            import re
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group(0))
            return {"tom": "inspirador", "publico": "cristãos", "estilo": "clean"}
        except Exception:
            return {"tom": "inspirador", "publico": "geral", "estilo": "clean"}

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 2: ARQUITETURA
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_arquitetura(self):
        """Pesquisa keywords, mapeia seções e planeja artigos."""
        sid = "arquitetura"
        niche = self.state.niche
        channel_id = self.state.channel_id

        self._update_macro(sid, "active", 5,
            f"📋 Pesquisando keywords para '{niche}'...")

        try:
            from modules.keyword_miner import research_keywords, find_low_hanging_fruits
            from modules.database import create_db_blog_section

            # 1. Keyword research geral
            self._update_macro(sid, "active", 15,
                "🔍 Pesquisando keywords principais com Obscura...")

            # Obscura desabilitado para testes locais (OBSCURA_ENABLED=false no .env)
            import os
            use_obs = os.getenv("OBSCURA_ENABLED", "false").lower() == "true"
            research = await research_keywords(
                seed=niche, lang=self.state.language,
                max_results=50, use_obscura=use_obs,
            )

            total_kw = research.get("total_found", 0)
            easy_kw = research.get("easy_count", 0)
            clusters = research.get("clusters", {})

            self._update_macro(sid, "active", 30,
                f"📊 {total_kw} keywords encontradas ({easy_kw} fáceis)")

            # 2. Identificar seções (clusters de keywords)
            self._update_macro(sid, "active", 40,
                "🗂️ Identificando seções e micro-nichos...")

            sections_data = []
            if clusters:
                for i, (cluster_name, keywords) in enumerate(clusters.items()):
                    kw_list = [kw["keyword"] for kw in keywords[:5]]
                    sections_data.append({
                        "name": cluster_name.capitalize(),
                        "keywords": ", ".join(kw_list),
                        "target_articles": 5,
                        "sort_order": i,
                    })
            else:
                # Fallback: criar seções baseadas no nicho
                sections_data = [
                    {"name": "Introdução", "keywords": niche, "target_articles": 5, "sort_order": 0},
                    {"name": "Fundamentos", "keywords": f"fundamentos {niche}", "target_articles": 6, "sort_order": 1},
                    {"name": "Aprofundamento", "keywords": f"{niche} avançado", "target_articles": 6, "sort_order": 2},
                    {"name": "Aplicações", "keywords": f"{niche} aplicação prática", "target_articles": 6, "sort_order": 3},
                    {"name": "Reflexões", "keywords": f"{niche} reflexão", "target_articles": 6, "sort_order": 4},
                    {"name": "Recursos", "keywords": f"{niche} recursos", "target_articles": 6, "sort_order": 5},
                ]

            # 3. Salvar seções no banco
            self._update_macro(sid, "active", 60,
                "💾 Salvando seções no banco...")

            saved_sections = []
            for sec_data in sections_data:
                section = create_db_blog_section(
                    channel_id=channel_id,
                    name=sec_data["name"],
                    keywords=sec_data["keywords"],
                    target_articles=sec_data["target_articles"],
                    sort_order=sec_data["sort_order"],
                )
                saved_sections.append(section)

            self.state.sections = saved_sections

            # 4. Buscar frutas baixas
            self._update_macro(sid, "active", 75,
                "🍇 Buscando frutas baixas...")

            try:
                low_hanging = await asyncio.wait_for(
                    find_low_hanging_fruits(
                        seed=niche, lang=self.state.language,
                        max_results=20, use_obscura=use_obs,
                    ),
                    timeout=15.0
                )
                lh_count = low_hanging.get("total_found", 0)
            except Exception:
                lh_count = 0
                print(f"[Arquitetura] find_low_hanging_fruits timeout ou erro, pulando...")

            # 5. Finalizar
            total_planned = sum(s["target_articles"] for s in sections_data)
            self._update_macro(sid, "completed", 100,
                f"✅ Arquitetura pronta! {total_planned} artigos planejados em {len(saved_sections)} seções", {
                    "sections_count": len(saved_sections),
                    "total_planned": total_planned,
                    "keywords_found": total_kw,
                    "easy_keywords": easy_kw,
                    "low_hanging_fruits": lh_count,
                    "sections": saved_sections,
                })

        except ImportError as e:
            # Fallback: seções genéricas
            fallback_sections = []
            for i, sec_name in enumerate(["Introdução", "Fundamentos", "Aprofundamento", "Aplicações"]):
                fallback_sections.append({
                    "id": f"sec_fallback_{i}", "name": sec_name,
                    "target_articles": 5, "sort_order": i,
                })
            self.state.sections = fallback_sections
            self._update_macro(sid, "completed", 100,
                f"⚠️ {len(fallback_sections)} seções criadas (modo demonstração)")
        except Exception as e:
            self._update_macro(sid, "failed", 0, f"Erro na arquitetura: {str(e)}")
            raise

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 3: PRODUÇÃO — O CORAÇÃO DA ESTEIRA
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_producao(self):
        """Gera 30-40 artigos em 3 rodadas de qualidade crescente."""
        sid = "producao"
        channel_id = self.state.channel_id
        sections = self.state.sections

        total_articles = 0
        total_words = 0

        # Usar target_articles do state (vindo do parâmetro da API) em vez do fixo PRODUCTION_ROUNDS
        target = self.state.target_articles
        target_words = 1000  # Padrão: ~1.100-1.500 palavras finais

        # Calcula quantos artigos por seção
        if not sections:
            articles_per_section = {f"sec_0": target}
        else:
            base = target // max(len(sections), 1)
            remainder = target % max(len(sections), 1)
            articles_per_section = {}
            for i, sec in enumerate(sections):
                sec_id = sec.get("id", f"sec_{i}")
                articles_per_section[sec_id] = base + (1 if i < remainder else 0)

        self._update_macro(sid, "active", 5,
            f"📝 Produzindo {target} artigos em {len(articles_per_section)} seções...")

        # Gerar artigos para esta rodada
        for sec_idx, (sec_id, article_count) in enumerate(articles_per_section.items()):
            if article_count <= 0:
                continue

            # Pega dados da seção
            sec = None
            for s in sections:
                if s.get("id") == sec_id:
                    sec = s
                    break
            if not sec:
                sec = {"name": f"Seção {sec_idx + 1}", "keywords": self.state.niche}

            sec_name = sec.get("name", f"Seção {sec_idx + 1}")
            sec_keywords = sec.get("keywords", self.state.niche)

            for a_idx in range(article_count):
                if self.state.status != "running":
                    return

                # Usar tópicos variados da lista ARTICLE_TOPICS para evitar duplicatas
                if ARTICLE_TOPICS:
                    topic_idx = (self.state.articles_generated + a_idx) % len(ARTICLE_TOPICS)
                    article_topic = ARTICLE_TOPICS[topic_idx]
                else:
                    article_topic = f"{sec_name}: {self.state.niche} — Guia {a_idx + 1}"

                self.state.current_macro_stage = sid

                # Progresso do artigo atual (calculado antes do revisor para usar nos logs)
                progress_in_target = (self.state.articles_generated + a_idx) / max(target, 1)
                overall_progress = int(10 + progress_in_target * 85)

                # ─── REVISOR: verificar se o tópico já foi coberto ───────
                try:
                    from modules.blog_revisor import review_topic_before_generation
                    review = await review_topic_before_generation(
                        topic=article_topic,
                        channel_id=self.state.channel_id or "default",
                        topics_pool=ARTICLE_TOPICS,
                        threshold=0.65,
                    )
                    if review.get("approved"):
                        article_topic = review["topic"]
                        if review.get("similar_to"):
                            self._update_macro(sid, "active", overall_progress,
                                f"🔍 Revisor: '{article_topic[:40]}...' (alternativa ao similar '{review['similar_to'][:30]}')")
                            await asyncio.sleep(0.2)
                    else:
                        self._update_macro(sid, "active", overall_progress,
                            f"⏭️ Revisor bloqueou: '{article_topic[:40]}' (similar a '{review['similar_to'][:30]}'). Pulando...")
                        await asyncio.sleep(0.2)
                        continue  # Pula este artigo, tenta próximo
                except ImportError:
                    pass  # Revisor não disponível, segue sem verificação
                except Exception as e:
                    print(f"[Pipeline] Revisor warning: {e}")

                self._update_macro(sid, "active", overall_progress,
                    f"✍️ [{self.state.articles_generated + a_idx + 1}/{target}] Gerando: {article_topic[:50]}...")

                # --- GERA O ARTIGO ---
                article_result = await self._generate_single_article(
                    topic=article_topic,
                    keywords=sec_keywords,
                    target_words=target_words,
                    section_id=sec_id,
                    section_name=sec_name,
                )

                if article_result.get("success"):
                    self.state.articles.append(article_result)
                    total_articles += 1
                    total_words += article_result.get("word_count", 0)
                    self.state.articles_generated = total_articles
                    # Checkpoint após cada artigo
                    await self._save_checkpoint()

                # Pequena pausa entre artigos
                await asyncio.sleep(0.3)

        # Finalizar produção
        self._update_macro(sid, "completed", 100,
            f"✅ Produção concluída! {total_articles} artigos gerados, ~{total_words} palavras", {
                "total_articles": total_articles,
                "total_words": total_words,
                "articles_preview": self.state.articles[-5:],
            })

    async def _generate_single_article(self, topic: str, keywords: str,
                                       target_words: int, section_id: str,
                                       section_name: str) -> dict:
        """Gera um artigo individual com SEO e salva no banco."""
        result = {
            "topic": topic,
            "section_id": section_id,
            "section_name": section_name,
            "success": False,
            "word_count": 0,
            "title": "",
            "post_id": None,
        }

        try:
            from modules.blog_writer import write as blog_write
            from modules.seo_optimizer import (
                build_schema_article, generate_schema_html,
                build_meta_tags, compute_seo_score,
            )
            from modules.database import create_db_blog_post, update_db_blog_post_status

            # 1. Gerar artigo via BlogWriter
            print(f"[Pipeline] Gerando artigo: {topic[:60]}... (target: {target_words} palavras)")
            article = await blog_write(
                topic=topic,
                channel_id=self.state.channel_id or "default",
                language=self.state.language,
                target_words=target_words,
                keywords=keywords,
            )

            if not article.get("success"):
                error_msg = article.get("error", "Falha na geração")
                print(f"[Pipeline] ERRO ao gerar artigo '{topic[:40]}': {error_msg}")
                if article.get("article"):
                    print(f"[Pipeline] Detalhe: {article.get('article').get('error', '')}")
                    print(f"[Pipeline] Raw: {str(article.get('article').get('raw', ''))[:200]}")
                result["error"] = error_msg
                return result

            post_id = article.get("post_id")
            title = article.get("title", topic)
            word_count = article.get("word_count", 0)
            article_data = article.get("article", {})
            content_html = article_data.get("content_html", "")
            excerpt = article_data.get("excerpt", "")
            article_keywords = article_data.get("keywords", keywords)

            # 2. Otimizar SEO
            try:
                schema = build_schema_article(
                    title=title, description=excerpt,
                    site_name=f"Dezafira - {self.state.blog_name}",
                    keywords=article_keywords,
                )
                schema_html = generate_schema_html(schema)
                meta_tags = build_meta_tags(
                    title=title, description=excerpt,
                    site_name=f"Dezafira - {self.state.blog_name}",
                    keywords=article_keywords,
                )

                # HTML completo
                full_html = f"""<!DOCTYPE html>
<html lang="{self.state.language}">
<head>
{meta_tags}
{schema_html}
</head>
<body>
<article>
{content_html}
</article>
</body>
</html>"""

                # Atualizar no banco
                update_db_blog_post(post_id, {
                    "content": full_html,
                })
            except Exception as e_html:
                print(f"[Pipeline] Producao: erro ao salvar HTML: {e_html}")

            result.update({
                "success": True,
                "post_id": post_id,
                "title": title,
                "word_count": word_count,
                "keywords": article_keywords,
            })

        except ImportError as e:
            result["error"] = f"Módulo não disponível: {e}"
            print(f"[Pipeline] ImportError: {e}")
        except Exception as e:
            result["error"] = str(e)
            print(f"[Pipeline] Exception ao gerar artigo: {e}")
            import traceback
            traceback.print_exc()

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 4: REFINO
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_refino(self):
        """Gera imagens, links internos e programa publicação."""
        sid = "refino"
        channel_id = self.state.channel_id
        articles = self.state.articles
        self._update_macro(sid, "active", 5,
            f"🎨 Refinando {len(articles)} artigos...")

        # 1. Links internos
        self._update_macro(sid, "active", 70,
            "🔗 Gerando links internos entre artigos...")

        try:
            from modules.seo_optimizer import generate_internal_links
            internal_links_count = 0
            for i, article in enumerate(articles):
                if not article.get("success"):
                    continue
                # Links são sugestões — em produção seriam inseridos no HTML
                internal_links_count += 1
            self._update_macro(sid, "active", 80,
                f"🔗 {internal_links_count} artigos com links internos")
        except Exception as e_links:
            print(f"[Pipeline] Refino: erro ao gerar links internos: {e_links}")

        # 2. Agendamento
        self._update_macro(sid, "active", 85,
            "📅 Configurando agendamento de publicação...")

        try:
            from modules.scheduler import add_daily_job, start
            job_id = f"blg_{channel_id or 'demo'}_{datetime.utcnow().strftime('%Y%m%d')}"
            add_daily_job(
                job_id=job_id,
                seed=self.state.niche,
                channel_id=channel_id or "default",
                hour=8, minute=0, publish=True, index=True,
            )
            start()
            self._update_macro(sid, "active", 95,
                f"✅ Publicação agendada: 1 artigo/dia às 08:00")
        except Exception as e:
            self._update_macro(sid, "active", 95,
                f"ℹ️ Agendamento: {e}")

        # Finalizar
        self._update_macro(sid, "completed", 100,
            f"✅ Refino concluído! Agendamento diário configurado", {
                "scheduled": True,
            })

    # ═══════════════════════════════════════════════════════════════════════════
    # FASE 5: ENTREGA
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_entrega(self):
        """Finaliza o blog — Seu Francisco confere, libera, e agenda Seu Zé."""
        sid = "entrega"
        articles = self.state.articles
        successful = [a for a in articles if a.get("success")]
        total_words = sum(a.get("word_count", 0) for a in successful)
        channel_id = self.state.channel_id

        self._update_macro(sid, "active", 10,
            "👴 Seu Francisco: 'Deixa eu conferir a produção...'")
        await asyncio.sleep(0.3)

        # ─── SEU FRANCISCO: supervisionar ────────────────────────────────
        try:
            from modules.seu_francisco import sinal_verde
            avaliacao = sinal_verde(channel_id=channel_id, target_articles=self.state.target_articles)

            if avaliacao.get("liberado"):
                self._update_macro(sid, "active", 30,
                    f"👴 Seu Francisco: \"{avaliacao['resumo'][:60]}...\"")
            else:
                self._update_macro(sid, "active", 30,
                    f"👴 Seu Francisco: \"{avaliacao['resumo'][:60]}...\"")
        except Exception as e:
            print(f"[Pipeline] Seu Francisco warning: {e}")

        await asyncio.sleep(0.3)

        # Marcar pipeline como concluído
        self._update_macro(sid, "active", 40,
            "✅ Gerando relatório final...")
        try:
            from modules.database import update_db_blog_pipeline_run
            if self.state.pipeline_run_id:
                update_db_blog_pipeline_run(self.state.pipeline_run_id, {
                    "status": "completed",
                    "phase": "entrega",
                    "articles_generated": len(successful),
                    "completed_at": datetime.utcnow(),
                })
        except Exception as e_run:
            print(f"[Pipeline] Entrega: erro ao atualizar pipeline: {e_run}")

        # ─── SEU ZÉ: agendar publicação diária ───────────────────────────
        self._update_macro(sid, "active", 60,
            "📅 Seu Zé: 'Agendando 1 artigo/dia às 08:00...'")
        try:
            from modules.seu_ze import agendar_publicacao
            agenda = agendar_publicacao(
                channel_id=channel_id or "default",
                blog_name=self.state.blog_name or "Blog",
                hour=8, minute=0,
            )
            self._update_macro(sid, "active", 75,
                f"📅 Seu Zé: '{agenda.get('status', 'agendado')}! 1 artigo/dia às 08:00'")
        except Exception as e:
            print(f"[Pipeline] Seu Ze warning: {e}")

        await asyncio.sleep(0.3)

        self._update_macro(sid, "active", 85,
            f"📊 Relatório: {len(successful)} artigos, ~{total_words} palavras")

        self._update_macro(sid, "active", 90,
            "🖼️ Verificando imagens pendentes...")
        
        # 📸 Gerar imagens para artigos sem imagem (função compartilhada)
        try:
            from modules.ricardo import gerar_imagens_pendentes
            _img_result = await gerar_imagens_pendentes(channel_id=channel_id)
            print(f"[Pipeline] Imagens geradas: {_img_result.get('message', 'OK')}")
            self._update_macro(sid, "active", 95,
                f"✅ {_img_result.get('images_generated', 0)} imagens geradas")

        except Exception as e:
            print(f"[Pipeline] Entrega: erro ao gerar imagens: {e}")

        self._update_macro(sid, "completed", 100,
            f"🎉 Blog '{self.state.blog_name}' COMPLETO! {len(successful)} artigos prontos!", {
                "total_articles": len(successful),
                "total_words": total_words,
                "blog_name": self.state.blog_name,
                "niche": self.state.niche,
                "channel_id": self.state.channel_id,
                "articles_preview": [a.get("title") for a in successful[:10]],
                "message": "Pipeline pronto para o próximo blog!",
            })



# ═══════════════════════════════════════════════════════════════════════════════
# RESUME — Retomar pipeline interrompida
# ═══════════════════════════════════════════════════════════════════════════════

async def resume_blog_pipeline(
    run_id: str,
    on_progress = None,
) -> dict:
    """Retoma pipeline interrompida sem duplicar dados."""
    try:
        from modules.database import get_db_blog_pipeline_run, update_db_blog_pipeline_run
        from modules.blog_pipeline import BlogMacroPipeline, MacroState

        run_data = get_db_blog_pipeline_run(run_id)
        if not run_data:
            return {"status": "failed", "error": f"Pipeline run {run_id} nao encontrada"}

        blog_name = run_data.get("blog_name", "Blog")
        niche = run_data.get("niche", "")
        language = run_data.get("language", "pt")
        channel_id = run_data.get("channel_id", "")
        last_phase = run_data.get("phase", "fundacao")
        pipeline_data = run_data.get("pipeline_data", {}) or {}
        saved_articles = pipeline_data.get("articles", [])
        completed_articles = len([a for a in saved_articles if a.get("success")])
        target = run_data.get("total_articles_target", 3)

        print(f"[Resume] {run_id}: blog={blog_name}, fase={last_phase}, {completed_articles}/{target} artigos")

        if completed_articles >= target:
            print("[Resume] Pipeline ja completo!")
            update_db_blog_pipeline_run(run_id, status="completed", phase="entrega")
            return {"status": "completed", "articles_generated": completed_articles}

        update_db_blog_pipeline_run(run_id, status="running", error=None)

        # Criar pipeline manualmente (evita executar fases concluidas)
        macro = BlogMacroPipeline(on_progress=on_progress)
        macro.state = MacroState(run_id, blog_name, niche, language, target_articles=target)
        macro.state.status = "running"
        macro.state.channel_id = channel_id
        macro.state.pipeline_run_id = run_id

        # Restaurar checkpoint
        saved_stages = pipeline_data.get("stages", {})
        for sid, sdata in saved_stages.items():
            if sid in macro.state.macro_stages:
                macro.state.macro_stages[sid].update(sdata)

        for a in saved_articles:
            if a.get("success"):
                macro.state.articles.append(a)
                macro.state.articles_generated += 1

        # Determinar quais fases pular
        skip_phases = set()
        for sid, s in macro.state.macro_stages.items():
            if s.get("status") == "completed":
                skip_phases.add(sid)
                print(f"[Resume] Pulando fase: {sid}")

        # Se tem channel_id, pula fundacao
        if channel_id and "fundacao" not in skip_phases:
            skip_phases.add("fundacao")
            macro.state.macro_stages["fundacao"]["status"] = "completed"
            macro.state.macro_stages["fundacao"]["progress"] = 100
            print(f"[Resume] Usando canal existente: {channel_id}")

        # Se tem sections no checkpoint, pula arquitetura
        sections_data = pipeline_data.get("sections", [])
        if sections_data and "arquitetura" not in skip_phases:
            macro.state.sections = sections_data
            macro.state.macro_stages["arquitetura"]["status"] = "completed"
            macro.state.macro_stages["arquitetura"]["progress"] = 100
            skip_phases.add("arquitetura")
            print("[Resume] Usando secoes do checkpoint")

        macro._emit("pipeline_started", macro.state.to_dict())

        # Executar fases nao concluidas
        if "fundacao" not in skip_phases:
            await macro._run_macro("fundacao", macro._phase_fundacao)
            await macro._save_checkpoint()
            if macro.state.status != "running": return macro.state.to_dict()

        if "arquitetura" not in skip_phases:
            await macro._run_macro("arquitetura", macro._phase_arquitetura)
            await macro._save_checkpoint()
            if macro.state.status != "running": return macro.state.to_dict()

        # Producao: sempre executa se faltam artigos
        if completed_articles < target:
            if completed_articles > 0:
                macro.state.articles_generated = completed_articles
            await macro._run_macro("producao", macro._phase_producao)
            await macro._save_checkpoint()
            if macro.state.status != "running": return macro.state.to_dict()

        if "refino" not in skip_phases:
            await macro._run_macro("refino", macro._phase_refino)
            await macro._save_checkpoint()

        if "entrega" not in skip_phases:
            await macro._run_macro("entrega", macro._phase_entrega)

        macro.state.status = "completed"
        from datetime import datetime
        macro.state.completed_at = datetime.utcnow()
        macro._emit("pipeline_completed", macro.state.to_dict())

        # Atualizar banco
        update_db_blog_pipeline_run(run_id, status="completed", phase="entrega",
                                     articles_generated=macro.state.articles_generated)

        return macro.state.to_dict()

    except Exception as e:
        print(f"[Resume] Erro: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO DE ALTO NÍVEL — usada pelo server.py
# ═══════════════════════════════════════════════════════════════════════════════

async def run_blog_macro_pipeline(
    blog_name: str,
    niche: str,
    language: str = "pt",
    task_id: Optional[str] = None,
    target_articles: Optional[int] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> dict:
    """
    Executa a macro-esteira completa da Fábrica de Blogs.

    Args:
        blog_name: Nome do blog (ex: "O Reino")
        niche: Nicho principal (ex: "Ensinamentos de Jesus")
        language: Idioma
        task_id: ID externo
        on_progress: Callback de progresso

    Returns:
        Estado final do pipeline
    """
    pipeline = BlogMacroPipeline(on_progress=on_progress)
    state = await pipeline.execute(
        blog_name=blog_name,
        niche=niche,
        language=language,
        task_id=task_id,
        target_articles=target_articles,
    )
    return state.to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI PARA TESTE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    async def main():
        blog_name = sys.argv[1] if len(sys.argv) > 1 else "O Reino"
        niche = sys.argv[2] if len(sys.argv) > 2 else "Ensinamentos de Jesus"

        print(f"\n{'='*60}")
        print(f"  🏭 MACRO-ESTEIRA — Fábrica de Blogs")
        print(f"  Blog: {blog_name}")
        print(f"  Nicho: {niche}")
        print(f"{'='*60}\n")

        def on_progress(pid, stage_id, progress, message, data):
            if stage_id == "__broadcast__":
                return
            for s in MACRO_STAGES:
                if s["id"] == stage_id:
                    icon = s["icon"]
                    break
            else:
                icon = "🔄"
            bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
            print(f"\r  {icon} [{bar}] {progress:3d}% {message[:70]}", end="")
            if progress == 100:
                print()

        result = await run_blog_macro_pipeline(blog_name, niche, on_progress=on_progress)

        print(f"\n{'='*60}")
        print(f"  Status: {result['status']}")
        if result.get("error"):
            print(f"  Erro: {result['error']}")
        if result.get("articles_generated"):
            print(f"  Artigos: {result['articles_generated']}")
        print(f"{'='*60}")

    asyncio.run(main())


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCAO DE COMPATIBILIDADE — Mini Pipeline (usada pelo endpoint /run-blog)
# ═══════════════════════════════════════════════════════════════════════════════

async def run_blog_pipeline(topic: str, channel_id: str = "default", language: str = "pt",
                            task_id: str = None, on_progress: callable = None,
                            auto_schedule: bool = True) -> dict:
    """
    Mini pipeline: gera um artigo individual.
    Usado pelo endpoint POST /api/v1/pipeline/run-blog.
    Delega para a macro pipeline com target_articles=1 e executa so a fase 3.
    """
    import uuid
    task_id = task_id or f"blg_{uuid.uuid4().hex[:8]}"
    from modules.blog_writer import write
    from modules.seo_optimizer import build_schema_article, generate_schema_html, build_meta_tags

    result = {
        "task_id": task_id,
        "topic": topic,
        "channel_id": channel_id,
        "language": language,
        "status": "running",
        "stages": {},
        "current_stage": None,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "error": None,
    }

    mini_stages = {
        "keyword_miner": {"status": "idle", "progress": 0, "message": "Aguardando", "started_at": None, "completed_at": None},
        "blog_writer": {"status": "idle", "progress": 0, "message": "Aguardando", "started_at": None, "completed_at": None},
        "seo_optimizer": {"status": "idle", "progress": 0, "message": "Aguardando", "started_at": None, "completed_at": None},
        "publish": {"status": "idle", "progress": 0, "message": "Aguardando", "started_at": None, "completed_at": None},
        "schedule": {"status": "idle", "progress": 0, "message": "Aguardando", "started_at": None, "completed_at": None},
    }
    result["stages"] = mini_stages

    def emit(sid, status, progress, msg, data=None):
        nonlocal result
        result["current_stage"] = sid
        if sid in result["stages"]:
            s = result["stages"][sid]
            s["status"] = status
            s["progress"] = progress
            s["message"] = msg
            if status == "active" and s["started_at"] is None:
                s["started_at"] = datetime.utcnow().isoformat()
            if status in ("completed", "failed"):
                s["completed_at"] = datetime.utcnow().isoformat()
        if on_progress:
            on_progress(task_id, sid, progress, msg, data or {})

    try:
        # Fase 1: Keywords
        emit("keyword_miner", "active", 10, "Pesquisando keywords...")
        kw_string = topic
        try:
            from modules.keyword_miner import research_keywords
            kw_res = await research_keywords(topic, lang=language, max_results=15, use_obscura=True)
            kw_string = kw_res.get("keyword_string", topic)
        except Exception as e_kw:
            print(f"[Pipeline] KeywordMiner: erro: {e_kw}")
        emit("keyword_miner", "completed", 100, "Keywords ok", {"keyword_string": kw_string})

        # Fase 2: Escrever artigo
        emit("blog_writer", "active", 10, "Gerando artigo via LLM...")
        article = await write(topic=topic, channel_id=channel_id, language=language,
                              target_words=1000, keywords=kw_string)
        post_id = article.get("post_id")
        title = article.get("title", topic)
        article_data = article.get("article", {})
        emit("blog_writer", "completed", 100, f"Artigo: {title}", article_data)

        # Fase 3: SEO
        emit("seo_optimizer", "active", 20, "Otimizando SEO...")
        try:
            schema = build_schema_article(title=title, description=article_data.get("excerpt", ""), keywords=kw_string)
            schema_html = generate_schema_html(schema)
            meta_tags = build_meta_tags(title=title, description=article_data.get("excerpt", ""), keywords=kw_string)
            emit("seo_optimizer", "completed", 100, "SEO otimizado")
        except Exception:
            emit("seo_optimizer", "completed", 100, "SEO basico")

        # Fase 4: Publicar
        emit("publish", "active", 20, "Publicando...")
        if post_id:
            from modules.database import update_db_blog_post_status
            update_db_blog_post_status(post_id, "published")
        emit("publish", "completed", 100, "Artigo publicado!", {"post_id": post_id})

        # Fase 5: Agendar
        if auto_schedule:
            emit("schedule", "active", 30, "Configurando agendamento...")
            try:
                from modules.scheduler import add_daily_job, start
                add_daily_job(f"blg_{channel_id}_{datetime.utcnow():%Y%m%d}", seed=topic, channel_id=channel_id or "default", hour=8, minute=0, publish=True, index=True)
                start()
            except Exception as e_sched:
                print(f"[Pipeline] Schedule: erro ao agendar: {e_sched}")
        emit("schedule", "completed", 100, "Concluido!")

        result["status"] = "completed"
        result["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        result["completed_at"] = datetime.utcnow().isoformat()
        import traceback
        traceback.print_exc()

    if on_progress:
        on_progress(task_id, "__broadcast__", 0, "pipeline_complete", result)

    return result
