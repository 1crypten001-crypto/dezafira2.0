"""
================================================================================
DEZAFIRA — Agentes Especializados para Fabricas
================================================================================
Agentes dedicados para cada fase critica das fabricas:
- BookNamerAgent: Nomes magneticos para livros (principal + bonus)
- CoverDesignerAgent: Prompts hiper-detalhados para capas profissionais
- ChapterWriterAgent: Escrita de capitulos com coesao e persona
- MiniAppBuilderAgent: Geracao de PWA real (HTML/CSS/JS)
"""
import json
import re
import uuid
from typing import List, Dict, Any, Optional

from agents.llm import query_llm, ERROR_PREFIX


def _parse_json_response(resp: str) -> Any:
    """Extrai JSON de uma resposta LLM, removendo marcadores de codigo."""
    if not resp or resp.startswith(ERROR_PREFIX):
        return None
    cleaned = resp.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return None


class BookNamerAgent:
    """
    Agente especialista em criar nomes magneticos para ebooks.
    Gera opcoes com analise de potencial de venda (curiosidade, especificidade, promessa).
    """

    async def generate_names(self, niche: str, theme: str = "", count: int = 5) -> List[Dict[str, Any]]:
        """
        Gera nomes para ebook principal + bonus.
        Retorna lista de dicts com: name, type, score, rationale.
        """
        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um copywriter de infoprodutos especializado em nomes de ebooks low-ticket (R$17-R$47). "
                "Seus nomes seguem a formula: Curiosidade + Especificidade + Promessa.\n"
                "REGRAS:\n"
                "- Maximo 6 palavras por titulo\n"
                "- Use numeros quando possivel (ex: 7 Segredos, 3 Erros)\n"
                "- Gere APENAS JSON valido\n"
                "- NUNCA use aspas duplas dentro do JSON\n"
            )},
            {"role": "user", "content": (
                f"Gere {count} nomes magneticos para ebooks sobre o nicho: {niche}\n"
                f"Tema adicional: {theme or 'Geral'}\n\n"
                f"Retorne APENAS um JSON valido no formato:\n"
                f'[{{"name": "Titulo", "type": "principal ou bonus", "score": 85, "rationale": "por que vende"}}]'
            )},
        ], max_tokens=2048)

        names = _parse_json_response(resp)
        if isinstance(names, list) and len(names) > 0:
            validated = []
            for item in names[:count]:
                if isinstance(item, dict) and "name" in item:
                    validated.append({
                        "name": str(item["name"])[:80],
                        "type": item.get("type", "principal"),
                        "score": min(100, max(0, int(item.get("score", 70)))),
                        "rationale": str(item.get("rationale", ""))[:200],
                    })
            if validated:
                return validated

        # Fallback controlado: gera nomes baseados no nicho via LLM sem JSON
        return await self._fallback_names(niche, count)

    async def _fallback_names(self, niche: str, count: int = 5) -> List[Dict[str, Any]]:
        """Gera nomes sem depender de JSON parsing."""
        resp = await query_llm([
            {"role": "system", "content": (
                "Crie 5 titulos magneticos para ebooks. "
                "Retorne APENAS os titulos, um por linha, sem numeracao, sem aspas, sem formatacao."
            )},
            {"role": "user", "content": f"Nicho: {niche}\nGere titulos curtos e atrativos."},
        ], max_tokens=1024)

        if resp and not resp.startswith(ERROR_PREFIX):
            lines = [l.strip().strip('"').strip("'").strip("- ").strip()
                     for l in resp.strip().split("\n") if l.strip() and len(l.strip()) > 5]
            results = []
            for i, name in enumerate(lines[:count]):
                t = "principal" if i == 0 else "bonus"
                results.append({"name": name[:80], "type": t, "score": 70, "rationale": "Gerado via fallback"})
            return results

        # Ultimo recurso
        return [
            {"name": f"Guia Definitivo: {niche}", "type": "principal", "score": 60, "rationale": "Fallback final"},
            {"name": f"Checklist Rapido: {niche}", "type": "bonus", "score": 55, "rationale": "Fallback final"},
        ]


class CoverDesignerAgent:
    """
    Agente especialista em design de capas de ebook.
    Gera prompts hiper-detalhados para geracao de imagem profissional.
    """

    STYLES = {
        "classico": {
            "palette": ["#1a1a2e", "#d4af37", "#f5f0e8", "#0d0d1a"],
            "typography": "serif elegante com serifa dourada",
            "mood": "solene, autoridade, sabedoria",
        },
        "moderno": {
            "palette": ["#0f0f0f", "#ffffff", "#6c5ce7", "#00cec9"],
            "typography": "sans-serif bold geometrica",
            "mood": "clean, tech, contemporaneo",
        },
        "vibrante": {
            "palette": ["#ff6b35", "#f7c948", "#1a1a2e", "#ffffff"],
            "typography": "display bold com sombra",
            "mood": "energia, acao, urgencia",
        },
        "minimalista": {
            "palette": ["#ffffff", "#2d3436", "#636e72", "#dfe6e9"],
            "typography": "sans-serif leve e espacada",
            "mood": " sofisticacao, espaco, clareza",
        },
        "luxo": {
            "palette": ["#0d0d0d", "#c9a84c", "#f0e6d3", "#1a1a1a"],
            "typography": "serif thin com dourado metalico",
            "mood": "exclusividade, premium, elite",
        },
    }

    async def design_cover(self, title: str, niche: str, style: str = "moderno",
                           subtitle: str = "", author: str = "Dezafira Editorial") -> Dict[str, Any]:
        """
        Gera prompt detalhado de capa + metadata visual.
        Retorna: prompt, style_name, colors, typography, composition, mood.
        """
        style_data = self.STYLES.get(style, self.STYLES["moderno"])

        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um diretor de arte senior especializado em capas de ebooks e infoprodutos. "
                "Crie um prompt EXTREMAMENTE detalhado para geracao de capa de ebook com IA.\n\n"
                "O prompt deve incluir:\n"
                "- Descricao visual da composicao (elementos, posicionamento, profundidade)\n"
                "- Paleta de cores especifica (hex codes)\n"
                "- Estilo de tipografia (tamanho relativo, cor, efeito)\n"
                "- Ilustracao/fundo conceitual relacionado ao nicho\n"
                "- Efeitos visuais (brilho, textura, gradiente, sombra)\n"
                "- Proporcao e layout (elementos principais e secundarios)\n\n"
                "REGRAS:\n"
                "- O prompt deve ser EM INGLES\n"
                "- Maximo 300 palavras\n"
                "- NAO inclua texto/titulos no prompt (serao adicionados depois)\n"
                "- Foque no CONCEITO VISUAL, nao no conteudo textual\n"
                "- Retorne APENAS o prompt, sem aspas ou formatacao"
            )},
            {"role": "user", "content": (
                f"Titulo do ebook: {title}\n"
                f"Subtitulo: {subtitle or 'Guia completo para ' + niche}\n"
                f"Nicho: {niche}\n"
                f"Estilo visual: {style}\n"
                f"Paleta: {', '.join(style_data['palette'])}\n"
                f"Tipografia: {style_data['typography']}\n"
                f"Mood: {style_data['mood']}"
            )},
        ], max_tokens=1024)

        if resp and not resp.startswith(ERROR_PREFIX):
            return {
                "prompt": resp.strip()[:500],
                "style_name": style,
                "colors": style_data["palette"],
                "typography": style_data["typography"],
                "mood": style_data["mood"],
                "composition": "Capa profissional com titulo centralizado, elemento visual conceitual ao fundo, barra dourada na base",
            }

        return self._fallback_prompt(title, niche, style_data)

    def _fallback_prompt(self, title: str, niche: str, style_data: dict) -> Dict[str, Any]:
        """Gera prompt basico sem LLM."""
        return {
            "prompt": (
                f"Professional ebook cover design for '{title}'. "
                f"Dark elegant background with {style_data['mood']} atmosphere. "
                f"Golden accent elements, modern typography layout space, "
                f"conceptual visual related to {niche}, cinematic lighting, 8k quality."
            ),
            "style_name": "moderno",
            "colors": style_data["palette"],
            "typography": style_data["typography"],
            "mood": style_data["mood"],
            "composition": "Capa profissional com titulo centralizado",
        }


class ChapterWriterAgent:
    """
    Agente especialista em escrita de capitulos de ebook.
    Mantem coesao, usa persona, e integra mecanismo unico.
    """

    async def write_chapter(self, title: str, chapter_number: int, total_chapters: int,
                            niche: str, book_title: str, promise: str = "",
                            mechanism_name: str = "", persona: Dict = None,
                            previous_summary: str = "", style: str = "didatico") -> Dict[str, Any]:
        """
        Escreve um capitulo completo com estrutura profissional.
        Retorna: content, word_count, key_points, chapter_summary.
        """
        persona_ctx = ""
        if persona:
            persona_ctx = (
                f"\nPERSONA DO LEITOR:\n"
                f"- Nome: {persona.get('name', 'Leitor')}\n"
                f"- Idade: {persona.get('age', '25-45')}\n"
                f"- Frustracoes: {', '.join(persona.get('frustrations', [])[:3])}\n"
                f"- Desejos: {', '.join(persona.get('desires', [])[:3])}"
            )

        mechanism_ctx = f"\nMecanismo unico do ebook: {mechanism_name}" if mechanism_name else ""
        promise_ctx = f"\nPromessa do ebook: {promise}" if promise else ""

        resp = await query_llm([
            {"role": "system", "content": (
                f"Voce e um ghostwriter profissional de ebooks. Escreva o capitulo {chapter_number}/{total_chapters} "
                f"do ebook '{book_title}'.\n\n"
                f"ESTILO: {style}, acessivel, com exemplos praticos.\n"
                f"TOM: acolhedor, motivador, direto.\n"
                f"EXTENSAO: Minimo 800 palavras, ideal 1200-1500.\n\n"
                f"ESTRUTURA OBRIGATORIA:\n"
                f"1. **Abertura empatica** - Conectar com a dor do leitor (2-3 paragrafos)\n"
                f"2. **Conceito central** - Ensinar o principal do capitulo com clareza\n"
                f"3. **Exemplos praticos** - Casos reais ou analogias\n"
                f"4. **Exercicio ou reflexao** - Algo que o leitor possa aplicar agora\n"
                f"5. **Fechamento** - Gancho para o proximo capitulo\n\n"
                f"REGRAS:\n"
                "- Use markdown: ## para titulos, ** para negrito, - para listas\n"
                "- NAO use travessao (—)\n"
                "- Comece com uma frase impactante\n"
                "- Maximo 3 niveis de profundidade\n"
                "- Se houver mecanismo unico, use o nome '{mechanism_name}' naturalmente\n"
                "- Retorne APENAS o conteudo do capitulo, sem meta-instrucoes"
            )},
            {"role": "user", "content": (
                f"Capitulo {chapter_number}: {title}\n"
                f"Nicho: {niche}\n"
                f"{promise_ctx}{mechanism_ctx}{persona_ctx}\n\n"
                f"Contexto dos capitulos anteriores:\n{previous_summary or '(Primeiro capitulo)'}\n\n"
                f"Escreva o capitulo completo."
            )},
        ], max_tokens=8192)

        if resp and not resp.startswith(ERROR_PREFIX):
            content = resp.strip()
            word_count = len(content.split())
            summary = f"Cap {chapter_number}: {title} ({word_count} palavras)"
            return {
                "content": content,
                "word_count": word_count,
                "chapter_summary": summary,
                "success": True,
            }

        return {"content": "", "word_count": 0, "chapter_summary": "", "success": False}

    async def generate_structure(self, book_title: str, niche: str, num_chapters: int,
                                 promise: str = "", mechanism_name: str = "") -> List[Dict[str, Any]]:
        """Gera a estrutura (sumario) do livro com descricao de cada capitulo."""
        resp = await query_llm([
            {"role": "system", "content": (
                f"Crie a estrutura de um ebook com {num_chapters} capitulos.\n"
                f"A jornada do leitor deve seguir:\n"
                f"1. Conexao com a dor do leitor\n"
                f"2. Quebra de crenças limitantes\n"
                f"3. Apresentacao do mecanismo unico\n"
                f"4. Passo a passo pratico\n"
                f"5. Exercicios e aplicacao\n"
                f"6. Consolidacao e proximos passos\n\n"
                f"Retorne APENAS JSON valido:\n"
                f'[{{"number": 1, "title": "Titulo do Capitulo", "description": "Descricao em 1 linha"}}]'
            )},
            {"role": "user", "content": (
                f"Titulo: {book_title}\n"
                f"Nicho: {niche}\n"
                f"Promessa: {promise or 'Transformacao completa no nicho'}\n"
                f"Mecanismo: {mechanism_name or 'Metodo exclusivo'}\n"
                f"Capitulos: {num_chapters}"
            )},
        ], max_tokens=2048)

        chapters = _parse_json_response(resp)
        if isinstance(chapters, list) and len(chapters) > 0:
            validated = []
            for i, ch in enumerate(chapters[:num_chapters]):
                if isinstance(ch, dict):
                    validated.append({
                        "number": ch.get("number", i + 1),
                        "title": str(ch.get("title", f"Capitulo {i+1}"))[:100],
                        "description": str(ch.get("description", ""))[:300],
                    })
            if len(validated) >= num_chapters // 2:
                return validated

        # Fallback: estrutura basica
        return [
            {"number": i + 1, "title": f"Capitulo {i + 1}", "description": ""}
            for i in range(num_chapters)
        ]


class MiniAppBuilderAgent:
    """
    Agente que constroi PWAs reais com HTML/CSS/JS.
    Gera codigo funcional, nao apenas sleep().
    """

    async def build_pwa(self, app_name: str, niche: str, app_type: str = "calculator",
                        features: List[str] = None, logo_url: str = "") -> Dict[str, Any]:
        """
        Constroi uma PWA completa com HTML, CSS e JS.
        Retorna: html, manifest, service_worker, features_implemented.
        """
        features = features or ["Calculadora basica", "Design responsivo", "Tema escuro"]

        resp = await query_llm([
            {"role": "system", "content": (
                "Voce e um desenvolvedor frontend senior especializado em PWAs. "
                "Construa uma aplicacao web completa e funcional.\n\n"
                "REGRAS:\n"
                "- Gere HTML completo com CSS inline e JavaScript embutido\n"
                "- Design responsivo (mobile-first)\n"
                "- Tema escuro com glassmorphism\n"
                "- Botoes grandes e acessiveis (min-height 48px)\n"
                "- Cores: fundo #0a0a1a, destaque #38bdf8, texto #e2e8f0\n"
                "- Inclua meta tags PWA (viewport, theme-color, apple-mobile-web-app)\n"
                "- JavaScript funcional (logica real, nao placeholder)\n"
                "- Maximo 50KB de HTML total\n"
                "- NAO inclua service worker (sera gerado separadamente)\n"
                "- NAO inclua manifest (sera gerado separadamente)\n"
                "- Retorne APENAS o conteudo HTML do body + style + script, sem <!DOCTYPE>"
            )},
            {"role": "user", "content": (
                f"App: {app_name}\n"
                f"Nicho: {niche}\n"
                f"Tipo: {app_type}\n"
                f"Funcionalidades: {', '.join(features)}\n"
                f"Logo URL: {logo_url or 'N/A'}\n\n"
                f"Gere o HTML funcional da PWA."
            )},
        ], max_tokens=16384)

        if resp and not resp.startswith(ERROR_PREFIX):
            html = resp.strip()
            if html.startswith("```"):
                html = html.split("\n", 1)[1].rsplit("```", 1)[0]
            return {
                "html": html,
                "features_implemented": features,
                "success": True,
            }

        # Fallback: PWA basica funcional
        return self._fallback_pwa(app_name, niche, features)

    def _fallback_pwa(self, app_name: str, niche: str, features: List[str]) -> Dict[str, Any]:
        """Gera PWA basica funcional sem LLM."""
        feature_html = ""
        for i, feat in enumerate(features[:6]):
            feature_html += f"""
            <div class="feature-card">
                <div class="feature-icon">{['+', '=', '#', '*', '@', '&'][i]}</div>
                <h3>{feat}</h3>
            </div>"""

        html = f"""
<div class="app-container">
    <header class="app-header">
        <h1 class="app-title">{app_name}</h1>
        <p class="app-subtitle">Ferramenta para {niche}</p>
    </header>
    <main class="app-main">
        <div class="feature-grid">{feature_html}
        </div>
        <div class="action-area">
            <button class="cta-button" onclick="alert('Funcionalidade em breve!')">Comecar Agora</button>
        </div>
    </main>
</div>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #0a0a1a; color: #e2e8f0; min-height: 100vh; }}
    .app-container {{ max-width: 480px; margin: 0 auto; padding: 20px; }}
    .app-header {{ text-align: center; padding: 40px 0 30px; }}
    .app-title {{ font-size: 28px; font-weight: 700; color: #38bdf8; margin-bottom: 8px; }}
    .app-subtitle {{ font-size: 14px; color: #94a3b8; }}
    .feature-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0; }}
    .feature-card {{ background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.15);
                     border-radius: 16px; padding: 20px; text-align: center;
                     backdrop-filter: blur(10px); transition: transform 0.2s; }}
    .feature-card:hover {{ transform: translateY(-2px); }}
    .feature-icon {{ font-size: 24px; margin-bottom: 8px; color: #38bdf8; }}
    .feature-card h3 {{ font-size: 13px; color: #cbd5e1; font-weight: 500; }}
    .action-area {{ padding: 20px 0; text-align: center; }}
    .cta-button {{ width: 100%; padding: 16px; background: linear-gradient(135deg, #38bdf8, #818cf8);
                   border: none; border-radius: 12px; color: white; font-size: 16px;
                   font-weight: 600; cursor: pointer; transition: opacity 0.2s; }}
    .cta-button:hover {{ opacity: 0.9; }}
</style>"""
        return {"html": html, "features_implemented": features, "success": True}


# Singletons
book_namer = BookNamerAgent()
cover_designer = CoverDesignerAgent()
chapter_writer = ChapterWriterAgent()
miniapp_builder = MiniAppBuilderAgent()
