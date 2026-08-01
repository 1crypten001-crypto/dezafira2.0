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
# TOPICOS DINAMICOS — Gerados por LLM por nicho
# ═══════════════════════════════════════════════════════════════════════════════

# Cache de topicos por nicho (evita gerar repetidamente)
_TOPICS_CACHE = {}

async def get_reddit_questions(niche: str, lang: str = "pt") -> list:
    """
    Busca no Google usando Obscura por discussões do Reddit sobre o nicho
    e extrai as 10 principais perguntas/dúvidas.
    """
    from services.obscura_bridge import ObscuraBridge
    from urllib.parse import quote
    import json
    
    query = f'site:reddit.com "{niche}" ("como" OR "por que" OR "vale a pena" OR "dúvida" OR "melhor" OR "erro" OR "problema" OR "ajuda")'
    if lang == "en":
        query = f'site:reddit.com "{niche}" ("how" OR "why" OR "worth it" OR "question" OR "best" OR "error" OR "problem" OR "help")'
        
    search_url = f"https://www.google.com/search?q={quote(query)}&hl={'pt-BR' if lang == 'pt' else 'en'}"
    print(f"[Seu Reddit] Buscando discussões em: {search_url}")
    
    bridge = ObscuraBridge()
    questions = []
    try:
        connected = await bridge.connect()
        if connected:
            await bridge.navigate_and_get_html(search_url)
            js_code = """
                (() => {
                    const links = Array.from(document.querySelectorAll('a'));
                    const results = [];
                    links.forEach(a => {
                        const href = a.getAttribute('href') || '';
                        if (href.includes('reddit.com') && !href.includes('google.com')) {
                            const h3 = a.querySelector('h3');
                            if (h3) {
                                const txt = h3.textContent.trim();
                                if (txt && !results.includes(txt) && txt.length > 8) {
                                    results.push(txt);
                                }
                            }
                        }
                    });
                    if (results.length === 0) {
                        document.querySelectorAll('h3').forEach(h3 => {
                            const txt = h3.textContent.trim();
                            if (txt && txt.length > 12 && !results.includes(txt)) {
                                results.push(txt);
                            }
                        });
                    }
                    return JSON.stringify(results.slice(0, 10));
                })()
            """
            res_json = await bridge.execute_js(js_code)
            await bridge.disconnect()
            if res_json:
                questions = json.loads(res_json)
    except Exception as e:
        print(f"[Seu Reddit] Erro ao extrair dúvidas do Reddit: {e}")
        try:
            await bridge.disconnect()
        except Exception:
            pass
            
    # Fallback caso não encontre nada ou Obscura esteja desativado
    if not questions:
        questions = [
            f"Como escolher o melhor {niche} para começar?",
            f"Quais os erros mais comuns ao trabalhar com {niche}?",
            f"Qual o custo-benefício de {niche} hoje em dia?",
            f"Dicas práticas de {niche} para iniciantes",
            f"Como resolver o problema principal de {niche}?",
            f"Vale a pena investir em {niche} atualmente?",
            f"O que ninguém te conta sobre {niche}?",
            f"Comparativo completo: as melhores opções de {niche}",
            f"Como otimizar meus resultados com {niche}?",
            f"Guia definitivo de dúvidas frequentes sobre {niche}"
        ]
    return questions

async def _generate_dynamic_topics(niche: str, count: int = 35, language: str = "pt", is_affiliate: bool = False, is_discover: bool = False) -> list:
    """
    Gera topicos de artigos variados usando LLM, especificos para o nicho.
    Usa cache para nao regenerar os mesmos topicos.
    """
    cache_key = f"{niche.lower().strip()}:{language}:aff={is_affiliate}:disc={is_discover}"
    if cache_key in _TOPICS_CACHE and len(_TOPICS_CACHE[cache_key]) >= count:
        return _TOPICS_CACHE[cache_key][:count]
    
    try:
        from modules.blog_writer import _call_llm
        if is_affiliate and is_discover:
            prompt = (
                f"Crie uma lista de {count} pautas virais para um formato de ADVERTORIAL (Notícia Curiosa que vende produto) "
                f"sobre o nicho: '{niche}'.\n"
                f"O objetivo é atrair tráfego massivo do Google Discover (Curiosidade, Polêmica, Click-Gap) e vender um produto de afiliado.\n"
                f"As pautas devem ser manchetes magnéticas e chocantes, mas focadas na resolução de uma dor com um produto.\n"
                f"Exemplos:\n"
                f"- 'O segredo bizarro que os mecânicos escondem para arrumar o motor em casa (Custa 20 reais)'\n"
                f"- 'Por que todo mundo está jogando fora suas panelas velhas e usando isso?'\n"
                f"Regras:\n"
                f"- Curiosidade extrema e conexão com e-commerce (Amazon, Shopee).\n"
                f"- Idioma: {language}\n"
                f"\n"
                f"Retorne APENAS a lista numerada, um tópico por linha, sem marcadores extras."
            )
            system = f"Você é o Joaquim, um copywriter genial de advertoriais focado no nicho {niche}."
        elif is_affiliate:
            prompt = (
                f"Crie uma lista de {count} pautas e tópicos para artigos de blog altamente focados em conversão de AFILIADOS (vendas de produtos físicos ou digitais) "
                f"sobre o nicho: '{niche}'.\n"
                f"As pautas devem ser de 3 tipos principais:\n"
                f"1. REVIEWS INDIVIDUAIS de produtos populares ou lançamentos (ex: 'Review completo: vale a pena comprar o produto X?').\n"
                f"2. LISTAS/RANKINGS (ex: 'Os 5 melhores produtos X para comprar em 2026').\n"
                f"3. COMPARATIVOS (ex: 'Produto X vs Produto Y: qual o melhor custo-benefício?').\n"
                f"Regras:\n"
                f"- Escolha produtos reais e populares desse nicho que possam ser vendidos na Amazon, Shopee ou Mercado Livre.\n"
                f"- Foco total em intenção de compra comercial (comprar, vale a pena, melhor, comparativo).\n"
                f"- Idioma: {language}\n"
                f"\n"
                f"Retorne APENAS a lista numerada, um tópico por linha, sem marcadores extras."
            )
            system = f"Você é o Joaquim, um copywriter de vendas especialista em blogs de afiliados sobre o nicho {niche}."
        elif is_discover:
            prompt = (
                f"Crie uma lista de {count} títulos VIRAIS e MAGNÉTICOS para o Google Discover "
                f"sobre o nicho: '{niche}'.\n"
                f"A monetização é AdSense, então o foco é no CLIQUE POR CURIOSIDADE.\n"
                f"As manchetes precisam de 'Click-Gap' forte (provocar curiosidade revelando que falta uma informação).\n"
                f"Exemplos:\n"
                f"- 'Cientistas encontram detalhe assustador oculto nessa pintura e tentaram esconder'\n"
                f"- 'Se você faz isso de manhã, pare agora mesmo (Os médicos alertam)'\n"
                f"Regras:\n"
                f"- Foco total em curiosidade absurda, bizarra ou chocante.\n"
                f"- Nada de 'Guia Prático' ou títulos de SEO normais.\n"
                f"- Idioma: {language}\n"
                f"\n"
                f"Retorne APENAS a lista numerada, um tópico por linha, sem marcadores extras."
            )
            system = f"Você é o Joaquim, um redator-chefe de portal de fofocas e curiosidades sobre o nicho {niche}."
        else:
            prompt = (
                f"Crie uma lista de {count} topicos variados e especificos para artigos de blog "
                f"sobre o nicho: '{niche}'.\n"
                f"Cada topico deve ser um micro-tema UNICO, especifico e bem segmentado.\n"
                f"Regras:\n"
                f"- VARIEDADE absoluta: nenhum topico pode tratar do mesmo assunto\n"
                f"- Seja ESPECIFICO: ao inves de 'dicas de financas', use 'como negociar descontos em boletos'\n"
                f"- Misture tipos: guias praticos, explicacoes, listas, comparacoes, estudos de caso\n"
                f"- Cada topico deve render um artigo de ~1200 palavras\n"
                f"- Idioma: {language}\n"
                f"\n"
                f"Retorne APENAS uma lista numerada, um topico por linha, sem marcadores extras.\n"
                f"Exemplo:\n"
                f"1. Como criar um orcamento mensal infalivel\n"
                f"2. Os 5 maiores erros financeiros dos brasileiros\n"
                f"3. Investimento em CDB vs Tesouro Direto: qual escolher\n"
            )
            system = f"Você é um editor-chefe especialista em criar pautas para blogs sobre {niche}."
        raw = await _call_llm(system, prompt, temperature=0.8, max_tokens=4096)
        
        # Parse: extrair linhas numeradas
        import re
        topics = []
        for line in raw.split('\n'):
            line = line.strip()
            # Remove numeracao: "1. " ou "1) " ou "- "
            cleaned = re.sub(r'^[\d\-]+[.)\]\s]+', '', line)
            cleaned = re.sub(r'^[\*\-•]\s*', '', cleaned)
            if cleaned and len(cleaned) > 15:
                topics.append(cleaned)
        
        if len(topics) >= 5:
            # Cache
            _TOPICS_CACHE[cache_key] = topics
            return topics[:count]
    except Exception as e:
        print(f"[Pipeline] Erro ao gerar topicos dinâmicos: {e}")
    
    # Fallback: topicos genericos baseados no nicho
    fallback = [
        f"Guia completo sobre {niche} — parte {i+1}"
        for i in range(count)
    ]
    return fallback


# Lista de fallback para topicos de ensinamentos de Jesus (mantida para compatibilidade)
ARTICLE_TOPICS = [
    "A parabola do semeador - estudo completo",
    "O filho prodigo - o amor incondicional do Pai",
    "O bom samaritano - quem e o meu proximo",
    "Ovelha perdida - a busca incansavel de Deus",
    "O fermento do reino - crescimento silencioso",
    "A parabola dos talentos - administrando dons",
    "O semeador e os solos - preparando o coracao",
    "As bem-aventurancas - o manifesto do reino",
    "O sermao da montanha - etica do reino",
    "A regra de ouro - tratai os outros como quereis",
    "Amai os vossos inimigos - o amor radical",
    "A oracao do Pai Nosso - modelo de oracao",
    "O jejum que agrada a Deus",
    "Ajuntai tesouros no ceu - prioridades eternas",
    "A cura do cego de Jerico - fe que restaura",
    "A multiplicacao dos paes e peixes - Deus provedor",
    "Jesus acalma a tempestade - paz no meio da crise",
    "A ressurreicao de Lazaro - vitoria sobre a morte",
    "A cura do paralitico - perdao e cura",
    "A agua transformada em vinho - o primeiro milagre",
    "A filha de Jairo - a fe que ressuscita",
    "Jesus e a mulher samaritana - agua viva",
    "Zaqueu - a salvacao entra em casa",
    "Nicodemos - nascer de novo",
    "A mulher adultera - quem nao tiver pecado",
    "Maria e Marta - a melhor parte",
    "O jovem rico - vende tudo que tens",
    "A mulher do fluxo de sangue - a fe que toca",
    "O chamado dos primeiros discipulos",
    "Pedro - a rocha e as quedas",
    "O sermao profetico - sinais da volta",
    "As virgens prudentes e nescias - vigiai",
    "A porta estreita - nem todo que diz Senhor",
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
                 target_articles: int = 1, is_affiliate: bool = False, is_discover: bool = False):
        self.task_id = task_id
        self.blog_name = blog_name
        self.niche = niche
        self.language = language
        self.target_articles = target_articles
        self.is_affiliate = is_affiliate
        self.is_discover = is_discover
        self.reddit_questions = []
        self.channel_id = None       # Set after Phase 1
        self.pipeline_run_id = None  # Set after Phase 1
        self.sections = []           # Set after Phase 2
        self.articles_generated = 0
        self._consecutive_rejections = 0  # FIX 4: reprovacoes consecutivas da LiLi
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
        def _to_iso(val):
            if not val:
                return None
            if isinstance(val, str):
                return val
            try:
                return val.isoformat()
            except AttributeError:
                return str(val)

        # Serialize macro stages (convert datetime objects to strings)
        serialized_stages = {}
        for sid, s in self.macro_stages.items():
            serialized_stages[sid] = {
                "status": s["status"],
                "progress": s["progress"],
                "message": s["message"],
                "started_at": _to_iso(s.get("started_at")),
                "completed_at": _to_iso(s.get("completed_at")),
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
            "started_at": _to_iso(self.started_at),
            "completed_at": _to_iso(self.completed_at),
            "error": self.error,
            "reddit_questions": self.reddit_questions,
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
                    "reddit_questions": getattr(self.state, "reddit_questions", []),
                },
            )
        except Exception as e:
            print(f"[Pipeline] Checkpoint error: {e}")

    async def execute(self, blog_name: str, niche: str, language: str = "pt",
                      task_id: Optional[str] = None,
                      target_articles: Optional[int] = None,
                      is_affiliate: bool = False, is_discover: bool = False) -> MacroState:
        task_id = task_id or f"mblog_{uuid.uuid4().hex[:8]}"

        self.state = MacroState(task_id, blog_name, niche, language,
                                target_articles=target_articles or DEFAULT_TOTAL,
                                is_affiliate=is_affiliate, is_discover=is_discover)
        self.state.status = "running"
        self.state.started_at = datetime.utcnow()

        # ─── VERIFICAR ARTIGOS EXISTENTES ──────────────────────────────
        # Se o blog ja existe, contar artigos atuais e ajustar target
        try:
            from modules.database import get_db_blog_channels, get_db_blog_posts
            existing_channels = get_db_blog_channels()
            for ch in (existing_channels or []):
                if ch.get("name", "").strip().lower() == blog_name.strip().lower():
                    # target_articles = quantos NOVOS artigos gerar (nao total)
                    existing_posts = get_db_blog_posts(channel_id=ch["id"], limit=1000)
                    existing_count = len(existing_posts) if existing_posts else 0
                    print(f"[Pipeline] Blog '{blog_name}' ja tem {existing_count} artigos. "
                          f"Target de {self.state.target_articles} NOVOS artigos.")
                    if self.state.target_articles <= 0:
                        print(f"[Pipeline] Target = 0. Nada a gerar.")
                        self.state.status = "completed"
                        self.state.completed_at = datetime.utcnow()
                        self._emit("pipeline_completed", self.state.to_dict())
                        return self.state
                    break
        except Exception as e:
            print(f"[Pipeline] Erro ao verificar artigos existentes: {e}")

        # Inclui stage_id e status no evento inicial para que a UI saia de "starting"
        start_data = {
            **self.state.to_dict(),
            "stage_id": "fundacao",
            "status": "running",
        }
        self._emit("pipeline_started", start_data)

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
            print(f"[Pipeline] PIPELINE_FAILED: {e}")
            traceback.print_exc()
            # FIX 1: persistir failed no banco (evita run zumbi 'running')
            try:
                from modules.database import update_db_blog_pipeline_run
                if self.state.pipeline_run_id:
                    update_db_blog_pipeline_run(
                        self.state.pipeline_run_id,
                        status="failed",
                        phase=self.state.current_macro_stage or "producao",
                        error=str(e)[:500],
                        completed_at=datetime.utcnow(),
                    )
                    print("[Pipeline] Run persistida como failed no banco (except geral).")
            except Exception as e_persist:
                print(f"[Pipeline] Erro ao persistir failed no except: {e_persist}")
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
            print(f"[Pipeline] Fase '{stage_name}' falhou: {e}")
            traceback.print_exc()
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
                    # Se o canal existente nao tiver brand_config, gerar e salvar retroativamente
                    if not dupe[0].get("brand_config"):
                        self._update_macro(sid, "active", 22, "🎨 Canal existente sem branding. Seu Design gerando identidade visual...")
                        try:
                            from modules.brand_designer import BrandingDesignerAgent
                            designer = BrandingDesignerAgent()
                            brand_config = await designer.generate_branding(
                                blog_name=blog_name,
                                niche=niche,
                                is_affiliate=getattr(self.state, "is_affiliate", False)
                            )
                            import json
                            brand_config_str = json.dumps(brand_config)
                            update_db_blog_channel(dupe[0]["id"], brand_config=brand_config_str)
                            print(f"[Pipeline] Branding gerado com sucesso para blog existente: {blog_name}")
                        except Exception as e_brand:
                            print(f"[Pipeline] Erro ao gerar branding para canal existente: {e_brand}")

                    self._update_macro(sid, "completed", 100,
                        f"✅ Blog '{blog_name}' ja existia. Usando canal: {dupe[0]['id'][:12]}...")
                    return  # Sai da fase - blog ja existe
            except Exception as e_fund:
                print(f"[Pipeline] Fundacao: erro ao verificar duplicatas: {e_fund}")

            # 2. Criar canal do blog
            self._update_macro(sid, "active", 20,
                "📡 Criando canal de blog no banco...")

            # Gerar subdomain
            import re
            subdomain = re.sub(r'[^a-z0-9-]', '', blog_name.lower().replace(' ', '-'))[:20]
            
            # Gerar branding personalizado via Seu Design
            self._update_macro(sid, "active", 25, "🎨 Agente Seu Design criando branding e identidade visual exclusiva...")
            brand_config_str = None
            try:
                from modules.brand_designer import BrandingDesignerAgent
                designer = BrandingDesignerAgent()
                brand_config = await designer.generate_branding(
                    blog_name=blog_name,
                    niche=niche,
                    is_affiliate=getattr(self.state, "is_affiliate", False)
                )
                import json
                brand_config_str = json.dumps(brand_config)
            except Exception as e_brand:
                print(f"[Pipeline] Erro ao gerar branding: {e_brand}")
            
            channel = create_db_blog_channel(
                name=blog_name,
                nicho=niche,
                lang=self.state.language,
                platform="dezafira",
                subdomain=subdomain,
                is_affiliate=getattr(self.state, "is_affiliate", False),
                is_discover=getattr(self.state, "is_discover", False),
                brand_config=brand_config_str,
            )
            self.state.channel_id = channel["id"]

            # 2. Criar brand bible (via LLM)
            self._update_macro(sid, "active", 40,
                "📖 Gerando identidade visual e brand bible...")

            brand_bible = await self._generate_brand_bible(blog_name, niche)

            # Salva brand bible via update (em channel_knowledge ou no próprio canal)
            from modules.database import get_db_blog_by_subdomain
            update_db_blog_channel(channel["id"], site_url=f"https://dezafira.com.br/blog/{blog_name.lower().replace(' ', '-')}")

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

            # 1. Pesquisa de discussões do Reddit (Seu Reddit)
            self._update_macro(sid, "active", 10,
                "🤖 Agente Seu Reddit pesquisando dores e dúvidas reais dos usuários...")
            try:
                reddit_qs = await get_reddit_questions(niche, self.state.language)
                self.state.reddit_questions = reddit_qs
                self._update_macro(sid, "active", 12,
                    f"✓ Seu Reddit encontrou {len(reddit_qs)} dúvidas no Reddit!",
                    data={"reddit_questions": reddit_qs})
            except Exception as e_red:
                print(f"[Arquitetura] Erro ao obter dúvidas do Reddit: {e_red}")

            # 2. Keyword research geral
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
                    "reddit_questions": getattr(self.state, "reddit_questions", []),
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

        # Usar target_articles do state
        target = self.state.target_articles
        target_words = 1000

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

        # ─── SE TARGET FOR 0, PULAR PRODUCAO ──────────────────────────
        if target <= 0:
            self._update_macro(sid, "completed", 100,
                "✅ Blog ja completo! Nenhum artigo adicional necessario")
            return

        self._update_macro(sid, "active", 5,
            f"📝 Produzindo {target} artigos em {len(articles_per_section)} seções...")

        # ─── GERAR TÓPICOS DINÂMICOS POR NICHOS ─────────────────────
        self._update_macro(sid, "active", 7,
            "🧠 Gerando tópicos variados específicos para o nicho...")
        # Verificar se é blog de afiliado para ajustar geração de tópicos
        is_affiliate = False
        from modules.database import SessionLocal, BlogChannel
        db = SessionLocal()
        try:
            channel = db.query(BlogChannel).filter(BlogChannel.id == channel_id).first()
            if channel and channel.is_affiliate:
                is_affiliate = True
        except Exception as e_db:
            print(f"[Pipeline] Erro ao buscar is_affiliate: {e_db}")
        finally:
            db.close()

        dynamic_topics = await _generate_dynamic_topics(
            niche=self.state.niche,
            count=max(target * 2, 30),
            language=self.state.language,
            is_affiliate=is_affiliate,
            is_discover=getattr(self.state, "is_discover", False),
        )
        self._update_macro(sid, "active", 10,
            f"📋 {len(dynamic_topics)} tópicos gerados para o nicho '{self.state.niche[:30]}...'")

        # Guardar para referência
        self.state._dynamic_topics = dynamic_topics

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

            # Loop com RETRY: so avanca quando o artigo passa imagem + LiLi
            _approved_in_sec = 0
            _max_attempts = max(article_count * 4, 8)
            _attempts = 0
            while _approved_in_sec < article_count and _attempts < _max_attempts:
                _attempts += 1
                a_idx = _attempts - 1
                if self.state.status != "running":
                    return

                # Usar tópicos dinâmicos PRIORITARIAMENTE; fallback para ARTICLE_TOPICS
                if dynamic_topics:
                    topic_idx = (self.state.articles_generated + a_idx) % len(dynamic_topics)
                    article_topic = dynamic_topics[topic_idx]
                elif ARTICLE_TOPICS:
                    topic_idx = (self.state.articles_generated + a_idx) % len(ARTICLE_TOPICS)
                    article_topic = ARTICLE_TOPICS[topic_idx]
                else:
                    article_topic = f"{sec_name}: {self.state.niche} — Guia {a_idx + 1}"

                self.state.current_macro_stage = sid

                # Progresso do artigo atual
                progress_in_target = (self.state.articles_generated + a_idx) / max(target, 1)
                overall_progress = int(10 + progress_in_target * 85)

                # ─── REVISOR DE TÓPICO ────────────────────────────────
                try:
                    from modules.blog_revisor import review_topic_before_generation
                    review = await review_topic_before_generation(
                        topic=article_topic,
                        channel_id=self.state.channel_id or "default",
                        topics_pool=dynamic_topics or ARTICLE_TOPICS,
                        threshold=0.65,
                    )
                    if review.get("approved"):
                        article_topic = review.get("topic", article_topic)
                    else:
                        self._update_macro(sid, "active", overall_progress,
                            f"⏭️ Revisor bloqueou tópico. Pulando...")
                        await asyncio.sleep(0.2)
                        continue
                except ImportError:
                    pass
                except Exception as e:
                    print(f"[Pipeline] Revisor warning: {e}")

                self._update_macro(sid, "active", overall_progress,
                    f"✍️ [{_approved_in_sec + 1}/{target}] Gerando: {article_topic[:50]}...")

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

                    # ─── IMAGEM: Gerar IMEDIATAMENTE após o artigo ────
                    post_id = article_result.get("post_id")
                    if post_id and not article_result.get("featured_image_url"):
                        try:
                            from modules.image_factory import ImageGeneratorAgent
                            from modules.database import update_db_blog_post
                            img_agent = ImageGeneratorAgent()
                            img = await img_agent.generate_for_article(
                                title=article_result.get("title", ""),
                                keywords=article_result.get("keywords", ""),
                                topic=article_result.get("topic", ""),
                                is_discover=getattr(self.state, "is_discover", False),
                            )
                            if img.get("image_url"):
                                update_db_blog_post(post_id, featured_image_url=img["image_url"])
                                print(f"[Pipeline] Imagem gerada para artigo {post_id[:12]}... ({img.get('provider')})")
                            else:
                                print(f"[Pipeline] BLOQUEADO: Artigo {post_id[:12]}... sem imagem. Artigo nao contado.")
                                article_result["success"] = False
                                continue
                        except Exception as e_img:
                            print(f"[Pipeline] BLOQUEADO: Falha ao gerar imagem: {e_img}. Artigo nao contado.")
                            article_result["success"] = False
                            continue

                    # ─── LILI: Revisar artigo recém-gerado (BLOQUEANTE) ────
                    if post_id:
                        try:
                            from modules.lili import lili_review_after_generation
                            from modules.database import delete_db_blog_post
                            lili_result = await lili_review_after_generation(post_id)
                            if lili_result.get("status") != "erro":
                                lili_approved = lili_result.get("approved", False)
                                lili_score = lili_result.get("overall_score", 0)
                                lili_corrected = lili_result.get("auto_corrected", False)
                                title_preview = (article_result.get("title") or "")[:40]

                                if lili_approved:
                                    # FIX 4: reset contador de rejeicoes consecutivas
                                    self.state._consecutive_rejections = 0
                                    self._update_macro(
                                        sid, "active", overall_progress,
                                        f"🌸 LiLi aprovou: score {lili_score}/100",
                                        {"lili_score": lili_score, "lili_approved": True, "article_title": article_result.get("title", "")})
                                    if lili_corrected:
                                        self._update_macro(
                                            sid, "active", overall_progress,
                                            f"🌸 LiLi corrigiu e aprovou: '{title_preview}' score {lili_score}/100",
                                            {"lili_score": lili_score, "lili_approved": True, "lili_corrected": True, "article_title": article_result.get("title", "")})
                                    article_result["lili_review"] = {
                                        "approved": True,
                                        "score": lili_score,
                                        "auto_corrected": lili_corrected,
                                    }
                                else:
                                    # BLOQUEANTE: artigo reprovado mesmo apos correcao
                                    self._update_macro(
                                        sid, "active", overall_progress,
                                        f"🚫 LiLi REPROVOU: '{title_preview}' score {lili_score}/100. Deletando...",
                                        {"lili_score": lili_score, "lili_approved": False, "article_title": article_result.get("title", "")})
                                    delete_db_blog_post(post_id)
                                    article_result["success"] = False
                                    print(f"[Pipeline] BLOQUEADO: LiLi reprovou artigo {post_id[:12]}... (score {lili_score}/100). Artigo deletado.")
                                    # FIX 4: limite inteligente — 4 rejeicoes consecutivas = problema sistemico
                                    self.state._consecutive_rejections = getattr(self.state, '_consecutive_rejections', 0) + 1
                                    print(f"[Pipeline] LiLi reprovou {self.state._consecutive_rejections}x consecutivas.")
                                    if self.state._consecutive_rejections >= 4:
                                        _warn_rej = f"🚫 Produção interrompida: LiLi reprovou {self.state._consecutive_rejections} artigos seguidos (último score {lili_score}/100). Qualidade do LLM/prompt comprometida."
                                        self._update_macro(sid, "failed", overall_progress, _warn_rej)
                                        print(f"[Pipeline] {_warn_rej}")
                                        self.state.status = "failed"
                                        try:
                                            from modules.database import update_db_blog_pipeline_run
                                            if self.state.pipeline_run_id:
                                                update_db_blog_pipeline_run(
                                                    self.state.pipeline_run_id,
                                                    status="failed", phase="producao",
                                                    error=_warn_rej[:500],
                                                    completed_at=datetime.utcnow(),
                                                )
                                        except Exception as e_persist:
                                            print(f"[Pipeline] Erro ao persistir failed (rejeicoes): {e_persist}")
                                        return
                                    continue
                            await asyncio.sleep(0.1)
                        except ImportError:
                            pass  # Lili não disponível
                        except Exception as e_lili:
                            print(f"[Pipeline] Lili warning: {e_lili}")

                    # Checkpoint após cada artigo
                    await self._save_checkpoint()
                    _approved_in_sec += 1

                # Pequena pausa entre artigos
                await asyncio.sleep(0.3)

        # Finalizar produção
        # Guard baseado em APROVADOS (success) — total_articles conta geracoes
        # que escreveram (antes dos gates de imagem/LiLi) e pode superar o
        # target com retries mesmo com 0 aprovados.
        _approved = len([a for a in self.state.articles if a.get("success")])
        if _approved < target:
            partial = _approved > 0
            _warn = f"⚠️ Produção {'parcial' if partial else 'não atingiu o alvo'}: {_approved}/{target} aprovados (LiLi bloqueou os demais)"
            self._update_macro(sid, "completed" if partial else "failed", 100, _warn, {
                "total_articles": _approved,
                "total_words": total_words,
                "target_articles": target,
            })
            print(f"[Pipeline] {_warn}")
            if not partial:
                self.state.status = "failed"
                print("[Pipeline] Produção zerada. Esteira interrompida (nada para refinar/entregar).")
                # FIX 1: persistir failed no banco para a UI nao ficar 'running' para sempre
                try:
                    from modules.database import update_db_blog_pipeline_run
                    if self.state.pipeline_run_id:
                        update_db_blog_pipeline_run(
                            self.state.pipeline_run_id,
                            status="failed",
                            phase="producao",
                            error=_warn[:500],
                            completed_at=datetime.utcnow(),
                        )
                        print("[Pipeline] Run persistida como failed no banco (produção zerada).")
                except Exception as e_persist:
                    print(f"[Pipeline] Erro ao persistir failed (produção zerada): {e_persist}")
            return
        self._update_macro(sid, "completed", 100,
            f"✅ Produção concluída! {total_articles} artigos gerados, ~{total_words} palavras", {
                "total_articles": total_articles,
                "total_words": total_words,
                "articles_preview": self.state.articles[-5:],
                "dynamic_topics_count": len(dynamic_topics),
                "lili_reviews": len([a for a in self.state.articles if a.get("lili_review")]),
            })

    # ═══════════════════════════════════════════════════════════════════════════════
    # FASE 4: REFINO
    # ═══════════════════════════════════════════════════════════════════════════

    async def _phase_refino(self):
        """Gera imagens, links internos e programa publicação."""
        sid = "refino"
        channel_id = self.state.channel_id
        articles = self.state.articles
        self._update_macro(sid, "active", 5,
            f"🎨 Refinando {len(articles)} artigos...")

        # 1. Processar CTAs de afiliado se for blog de afiliado
        self._update_macro(sid, "active", 30,
            "🛒 Convertendo marcações de CTA para links de afiliados...")
        from modules.database import SessionLocal, BlogPost, BlogChannel
        db = SessionLocal()
        try:
            channel = db.query(BlogChannel).filter(BlogChannel.id == channel_id).first()
            is_affiliate = channel.is_affiliate if channel else False
            
            if is_affiliate:
                processed_ctas = 0
                for article in articles:
                    if not article.get("success") or not article.get("post_id"):
                        continue
                    post_id = article["post_id"]
                    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
                    if post and post.content:
                        new_content = render_affiliate_ctas(post.content, post.slug or post.id)
                        post.content = new_content
                        processed_ctas += 1
                db.commit()
                print(f"[Pipeline] Refino: processados CTAs para {processed_ctas} artigos.")
        except Exception as e_ctas:
            print(f"[Pipeline] Refino: erro ao processar CTAs de afiliado: {e_ctas}")
        finally:
            db.close()

        # 2. Links internos
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

        # --- Lili: Revisao final de todos os artigos pendentes ---
        self._update_macro(sid, "active", 45,
            "🌸 Lili: revisando qualidade de todos os artigos...")
        try:
            from modules.lili import lili_review_all_pending
            lili_final = await lili_review_all_pending(channel_id=channel_id)
            if lili_final.get("status") == "completo":
                self._update_macro(sid, "active", 50,
                    f"🌸 Lili: {lili_final.get('approved',0)}/{lili_final.get('total',0)} artigos aprovados, score medio {lili_final.get('avg_score',0)}/100")
        except ImportError:
            pass
        except Exception as e_lili:
            print(f"[Pipeline] Lili warning: {e_lili}")

        self._update_macro(sid, "active", 40,
            "✅ Gerando relatório final...")
        try:
            from modules.database import update_db_blog_pipeline_run
            if self.state.pipeline_run_id:
                update_db_blog_pipeline_run(self.state.pipeline_run_id, **{
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
                update_db_blog_post(post_id, content=full_html)
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

def render_affiliate_ctas(content: str, post_slug: str) -> str:
    import re
    import urllib.parse
    
    pattern = r'\[CTA:\s*(amazon|shopee|mercadolivre)\s*\|\s*([^\]]+)\]'
    
    def replace_cta(match):
        provider = match.group(1).lower().strip()
        product_name = match.group(2).strip()
        encoded_prod = urllib.parse.quote_plus(product_name)
        
        # Estilos baseados no provedor
        if provider == "amazon":
            label = "Amazon"
            bg = "#FF9900"
            grad_start = "#FF9900"
            grad_end = "#FFB84D"
            text_color = "#ffffff"
        elif provider == "shopee":
            label = "Shopee"
            bg = "#EE4D2D"
            grad_start = "#EE4D2D"
            grad_end = "#F1755B"
            text_color = "#ffffff"
        else: # mercadolivre
            label = "Mercado Livre"
            bg = "#FFE600"
            grad_start = "#FFE600"
            grad_end = "#FFEB33"
            text_color = "#2D3277"
            
        btn_text_color = text_color
            
        card_html = f'''<div class="affiliate-card" style="border: 1px solid var(--border); background: var(--bg-dark); padding: 20px; border-radius: 12px; margin: 24px 0; display: flex; flex-direction: column; gap: 12px; box-shadow: var(--shadow, 0 4px 12px rgba(0,0,0,0.03));">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <span style="font-weight: 700; font-size: 16px; color: var(--dark);">{product_name}</span>
        <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: {bg}; color: {btn_text_color}; padding: 3px 8px; border-radius: 6px;">{label}</span>
    </div>
    <p style="font-size: 13px; color: var(--text-light); margin: 0; line-height: 1.5;">Confira o preço atualizado, avaliações reais de outros compradores e garanta a melhor oferta no link abaixo:</p>
    <a href="/go/{post_slug}/{provider}?prod={encoded_prod}" target="_blank" style="display: inline-block; text-align: center; text-decoration: none; padding: 10px 18px; background: linear-gradient(135deg, {grad_start}, {grad_end}); color: {btn_text_color}; border-radius: 8px; font-weight: 700; font-size: 13px; transition: all 0.2s ease;">Ver Preço na {label}</a>
</div>'''
        return card_html

    return re.sub(pattern, replace_cta, content, flags=re.IGNORECASE)

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
        _aff, _disc = False, False
        try:
            from modules.database import SessionLocal, BlogChannel
            _db = SessionLocal()
            try:
                _ch = _db.query(BlogChannel).filter(BlogChannel.id == channel_id).first() if channel_id else None
                _aff = bool(getattr(_ch, "is_affiliate", False)) if _ch else False
                _disc = bool(getattr(_ch, "is_discover", False)) if _ch else False
            finally:
                _db.close()
        except Exception:
            _aff, _disc = False, False
        macro.state = MacroState(run_id, blog_name, niche, language, target_articles=target,
                                 is_affiliate=_aff, is_discover=_disc)
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

        # Inclui stage_id para que a UI saia de "starting"
        resume_data = {
            **macro.state.to_dict(),
            "stage_id": "fundacao",
            "status": "running",
        }
        macro._emit("pipeline_started", resume_data)

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
    is_affiliate: bool = False,
    is_discover: bool = False,
) -> dict:
    """
    Executa a macro-esteira completa da Fábrica de Blogs.
    """
    pipeline = BlogMacroPipeline(on_progress=on_progress)
    state = await pipeline.execute(
        blog_name=blog_name,
        niche=niche,
        language=language,
        task_id=task_id,
        target_articles=target_articles,
        is_affiliate=is_affiliate,
        is_discover=is_discover,
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

ACTIVE_PIPELINE_TASKS = {}


async def run_blog_pipeline(topic: str, channel_id: str = "default", language: str = "pt",
                            task_id: str = None, on_progress: callable = None,
                            auto_schedule: bool = True, mine_hype: bool = False) -> dict:
    """
    Mini pipeline: gera um artigo individual.
    Usado pelo endpoint POST /api/v1/pipeline/run-blog e pela esteira do Hype.
    Delega para a macro pipeline com target_articles=1 e executa so a fase 3.
    """
    import uuid
    task_id = task_id or f"blg_{uuid.uuid4().hex[:8]}"
    from modules.blog_writer import write
    from modules.seo_optimizer import build_schema_article, generate_schema_html, build_meta_tags
    from modules.database import get_db_blog_channel, update_db_blog_post

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
    ACTIVE_PIPELINE_TASKS[task_id] = result

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
        ACTIVE_PIPELINE_TASKS[task_id] = result
        if on_progress:
            on_progress(task_id, sid, progress, msg, data or {})

    try:
        nicho = "Finanças"
        blog_info = get_db_blog_channel(channel_id)
        if blog_info:
            nicho = blog_info.get("nicho", "Finanças")

        # Fase 1: Mineração de Hype & Keywords
        kw_string = topic
        if mine_hype:
            emit("keyword_miner", "active", 10, "Buscando tendências quentes no Google...")
            try:
                from modules.blog_pipeline import mine_google_hype
                pauta = await mine_google_hype(nicho, language)
                topic = pauta["topic"]
                kw_string = pauta["keywords"]
                result["topic"] = topic
                emit("keyword_miner", "active", 50, f"Tendência: {topic}", {"topic": topic})
            except Exception as e_hype:
                print(f"[Pipeline] Erro ao minerar hype: {e_hype}")
                emit("keyword_miner", "active", 50, f"Pesquisando termos em alta para {nicho}")
        else:
            emit("keyword_miner", "active", 30, "Pesquisando keywords de apoio...")

        try:
            from modules.keyword_miner import research_keywords
            kw_res = await research_keywords(topic, lang=language, max_results=15, use_obscura=True)
            kw_string = kw_res.get("keyword_string", kw_string)
        except Exception as e_kw:
            print(f"[Pipeline] KeywordMiner: erro: {e_kw}")
            
        emit("keyword_miner", "completed", 100, f"Pauta definida: {topic}", {"keyword_string": kw_string})

        # Fase 2: Escrever artigo (mínimo 1.200 a 2.000 palavras)
        emit("blog_writer", "active", 10, "Carlão redigindo o artigo (1.200 a 2.000 palavras)...")
        article = await write(topic=topic, channel_id=channel_id, language=language,
                              target_words=1500, keywords=kw_string)
        post_id = article.get("post_id")
        title = article.get("title", topic)
        article_data = article.get("article", {})
        
        # Fase 2.5: Qualidade & Auto-correção (LiLi)
        emit("blog_writer", "active", 85, "LiLi auditando e corrigindo o texto do Carlão...")
        try:
            from modules.lili import corrigir_conteudo_automatico, revisar_conteudo
            from modules.database import update_db_blog_post
            raw_body = article_data.get("body", "")
            
            # Aplica correção da LiLi
            corrected_body = corrigir_conteudo_automatico(raw_body)
            review = revisar_conteudo(post_id, title, corrected_body, kw_string)
            
            # Se o score for baixo ou reprovado, dá uma chance de regeneração
            if not review["approved"] or review["score"] < 80:
                print(f"[LiLi/Pipeline] Artigo REPROVADO (Score: {review['score']}/100). Regenerando...")
                article = await write(topic=topic, channel_id=channel_id, language=language,
                                      target_words=1500, keywords=kw_string)
                post_id = article.get("post_id")
                title = article.get("title", topic)
                article_data = article.get("article", {})
                raw_body = article_data.get("body", "")
                corrected_body = corrigir_conteudo_automatico(raw_body)
                review = revisar_conteudo(post_id, title, corrected_body, kw_string)
            
            # Atualiza no banco o conteúdo limpo de forma definitiva!
            update_db_blog_post(post_id, content=corrected_body)
            article_data["body"] = corrected_body
            emit("blog_writer", "completed", 100, f"Escrito por Carlão (Auditado pela LiLi: {review['score']}/100)", article_data)
        except Exception as e_lili:
            print(f"[Pipeline] Erro na auditoria da LiLi: {e_lili}")
            emit("blog_writer", "completed", 100, f"Escrito por Carlão: {title}", article_data)

        # Fase 3: SEO & Injeção de Tags
        emit("seo_optimizer", "active", 20, "Otimizando SEO do post...")
        try:
            schema = build_schema_article(title=title, description=article_data.get("excerpt", ""), keywords=kw_string)
            schema_html = generate_schema_html(schema)
            meta_tags = build_meta_tags(title=title, description=article_data.get("excerpt", ""), keywords=kw_string)
            emit("seo_optimizer", "completed", 100, "SEO e Tags prontos")
        except Exception:
            emit("seo_optimizer", "completed", 100, "SEO básico configurado")

        # Fase 4: Geração Obrigatória de Imagem & Publicação
        emit("publish", "active", 10, "Tatiana rodando a cascata de imagens (Flux → Gemini → Pexels)...")
        featured_image_url = None
        image_provider = "placeholder"
        
        try:
            from modules.image_factory import ImageGeneratorAgent
            img_agent = ImageGeneratorAgent()
            # A cascata já é garantida — nunca retorna None
            # Modo Discover: capa panorâmica 16:9 (1200x675) + prompt viral de choque/curiosidade
            if blog_info and bool(blog_info.get("is_discover", False)):
                img_res = await img_agent.generate_for_article(
                    title=title, keywords=kw_string, topic=topic, is_discover=True
                )
            else:
                img_res = await img_agent.generate_image_for_post(
                    prompt_idea=title,
                    niche=nicho,
                    post_id=post_id
                )
            featured_image_url = img_res["image_url"]
            image_provider = img_res.get("provider", "placeholder")
            provider_label = {
                "flux": "⚡ FLUX (IA)",
                "gemini": "🎨 Gemini IA",
                "pexels": "📷 Pexels",
                "unsplash": "📷 Unsplash",
                "placeholder": "🎭 SVG local",
            }.get(image_provider, image_provider)
            
            # Salva imagem + provedor no banco
            update_db_blog_post(post_id, featured_image_url=featured_image_url, image_provider=image_provider)
            emit("publish", "active", 60, f"Imagem gerada por {provider_label}!")
        except Exception as e_img:
            # Segurança extra: gera SVG local como último recurso
            print(f"[Pipeline] Cascata de imagem falhou ({e_img}). Gerando SVG local como backstop.")
            from modules.image_factory import ImageGeneratorAgent
            fallback_agent = ImageGeneratorAgent()
            _is_disc = bool(blog_info and blog_info.get("is_discover", False))
            svg_url = fallback_agent._generate_svg_placeholder(title, 1200, 675 if _is_disc else 630)
            featured_image_url = svg_url
            image_provider = "placeholder"
            update_db_blog_post(post_id, featured_image_url=svg_url, image_provider="placeholder")
            emit("publish", "active", 60, "Imagem SVG gerada como backup!")

        # Publica o post no banco de dados
        if post_id:
            from modules.database import update_db_blog_post_status
            update_db_blog_post_status(post_id, "published")
            
        emit("publish", "completed", 100, "Artigo e imagem publicados!", {
            "post_id": post_id,
            "featured_image_url": featured_image_url,
            "image_provider": image_provider,
        })

        # Fase 5: Agendamento & Indexação
        if auto_schedule:
            emit("schedule", "active", 30, "Configurando agendamento da esteira...")
            try:
                from modules.scheduler import add_daily_job, start
                add_daily_job(f"blg_{channel_id}_{datetime.utcnow():%Y%m%d}", seed=topic, channel_id=channel_id or "default", hour=8, minute=0, publish=True, index=True)
                start()
            except Exception as e_sched:
                print(f"[Pipeline] Schedule: erro ao agendar: {e_sched}")
        emit("schedule", "completed", 100, "Esteira concluída com sucesso!")

        result["status"] = "completed"
        result["completed_at"] = datetime.utcnow().isoformat()
        ACTIVE_PIPELINE_TASKS[task_id] = result

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        result["completed_at"] = datetime.utcnow().isoformat()
        ACTIVE_PIPELINE_TASKS[task_id] = result
        import traceback
        traceback.print_exc()

    if on_progress:
        on_progress(task_id, "__broadcast__", 0, "pipeline_complete", result)

    return result


async def mine_google_hype(niche: str, language: str = "pt") -> dict:
    """
    Minera palavras-chave e tópicos em alta no Google Autocomplete para o nicho,
    e usa a LLM para gerar um título de artigo inédito e autoral.
    """
    from modules.keyword_miner import KeywordMiner
    from modules.blog_writer import _call_llm
    import json
    import re
    
    # 1. Sugere sementes de busca baseadas no nicho
    prompt_seed = (
        f"Com base no nicho de blog '{niche}', sugira 3 termos de pesquisa curtos (1 a 3 palavras) "
        f"que as pessoas usariam no Google para buscar novidades, dúvidas ou notícias quentes sobre o assunto.\n"
        f"Retorne apenas os termos separados por vírgula, sem explicações ou numeração."
    )
    system_seed = "Você é um especialista em SEO e tendências de busca na web."
    try:
        raw_seeds = await _call_llm(system_seed, prompt_seed, temperature=0.6, max_tokens=100)
        seeds = [s.strip().replace('"', '').replace("'", "") for s in raw_seeds.split(",") if s.strip()]
    except Exception:
        seeds = [niche]

    if not seeds:
        seeds = [niche]

    # 2. Minera o Autocomplete do Google para cada semente
    miner = KeywordMiner(use_obscura=False)
    hot_suggestions = []
    try:
        for seed in seeds[:3]:
            suggestions = await miner._fetch_suggestions(seed, lang=language)
            if suggestions:
                hot_suggestions.extend(suggestions[:5])
    finally:
        await miner.close()

    # 3. Se não houver sugestões, usa termos gerais do nicho
    if not hot_suggestions:
        hot_suggestions = [
            f"novidades sobre {niche}",
            f"tendências em {niche}",
            f"dicas de {niche}"
        ]

    # 4. Envia as sugestões para a LLM criar o título e keywords
    prompt_hype = (
        f"Com base nas seguintes buscas reais que estão em alta no Google sobre o nicho '{niche}':\n"
        f"{', '.join(hot_suggestions[:12])}\n\n"
        f"Escolha a tendência mais relevante e crie um título de artigo de blog INÉDITO, altamente engajador, "
        f"autoral e otimizado para SEO.\n"
        f"Além disso, forneça uma lista curta de palavras-chave separadas por vírgula para focar no SEO do artigo.\n"
        f"Retorne APENAS um objeto JSON no formato:\n"
        f"{{\n"
        f"  \"title\": \"Título Inédito Criado\",\n"
        f"  \"keywords\": \"palavra-chave 1, palavra-chave 2, palavra-chave 3\"\n"
        f"}}"
    )
    system_hype = f"Você é o editor-chefe de um portal de notícias especialista em {niche}."
    
    try:
        raw_json = await _call_llm(system_hype, prompt_hype, temperature=0.8, max_tokens=500)
        json_clean = re.sub(r'```json\s*|\s*```', '', raw_json).strip()
        data = json.loads(json_clean)
        return {
            "topic": data.get("title", f"Novidades em {niche}"),
            "keywords": data.get("keywords", niche)
        }
    except Exception as e:
        print(f"[HypeEngine] Erro ao obter pauta da IA: {e}")
        return {
            "topic": f"Tendências quentes e novidades sobre {niche}",
            "keywords": niche
        }
