"""
=============================================================================
DEZAFIRA — SalesPageGenerator (Alta Cúpula Copy + Impeccable Design System)
=============================================================================
Gera páginas de vendas de alta conversão de forma totalmente autônoma.
Integra a estrutura de copy de 8 blocos com a estética do Impeccable.style:
- VSL (Video Sales Letter) com liberação temporal (delay) do botão de checkout.
- Marquee animada infinita de benefícios.
- Tabela comparativa "De/Para" (Dores Manuais vs Solução Inteligente).
- Sem cores puras (esquema HSL refinado, dark mode premium).
- Acordeões FAQ interativos.
"""

import os
import json
import re
from typing import Dict, Any, Optional
from agents.llm import query_llm

class SalesPageGenerator:
    def __init__(self):
        # Allowlist de fontes do Google Fonts para o design system
        self.display_fonts = ["Space Grotesk", "Archivo Black", "Sora", "Outfit", "Fraunces"]
        self.body_fonts = ["Inter", "Manrope", "Karla", "Plus Jakarta Sans"]

    async def generate_copy(self, product_name: str, niche: str, target_audience: str, price: str, guarantee_days: int) -> Dict[str, str]:
        """
        Gera a copy dos 8 blocos utilizando o LLM (DeepSeek via cascata unificada).
        """
        system_prompt = (
            "Você é o Seu Hermes + Zé do Traço, a mente por trás das copies mais lucrativas do Brasil (Direct Response Copywriter).\n"
            "Escreva a copy completa de uma página de vendas em formato JSON estruturado.\n"
            "Cada bloco de copy deve ser profundo, persuasivo e em português do Brasil."
        )

        user_prompt = f"""
        Nicho do Produto: {niche}
        Nome do Produto: {product_name}
        Público Alvo: {target_audience}
        Preço do Produto: {price}
        Garantia: {guarantee_days} dias

        Gere a copy da página de vendas dividida exatamente nestes 8 blocos:
        1. lead_headline: Headline principal (Ganho de Alto Impacto).
        2. lead_subheadline: Sub-headline explicando o método/mecanismo.
        3. story_villain: A frustração do trabalho manual, a perda de tempo e as copies ruins que não vendem.
        4. unique_mechanism: Como a IA e o ecossistema Dezafira resolvem isso no piloto automático (nosso mecanismo único).
        5. deliverables_list: Lista com 4 a 5 entregáveis ou recursos incríveis do produto.
        6. value_stack_anchor: O empilhamento de bônus e a ancoragem de preço (mostrando quanto custaria contratar uma equipe vs o preço atual).
        7. risk_reversal: Texto reforçando a garantia incondicional e o risco zero.
        8. faq_items: Array de 4 perguntas e respostas comuns para quebrar objeções (como "não sei programar", "serve pro meu nicho").

        Retorne APENAS um objeto JSON válido no seguinte formato de exemplo (sem blocos de código adicionais ou markdown, apenas o JSON bruto):
        {{
          "headline": "...",
          "subheadline": "...",
          "story": "...",
          "mechanism": "...",
          "deliverables": [
            {{"title": "...", "desc": "..."}},
            {{"title": "...", "desc": "..."}}
          ],
          "value_stack": {{
            "original_value": "R$ 4.997,00",
            "anchor_text": "...",
            "bonus": [
              {{"title": "...", "value": "..."}}
            ]
          }},
          "guarantee": "...",
          "faq": [
            {{"q": "...", "a": "..."}}
          ]
        }}
        """

        try:
            raw_response = await query_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            # Limpar formatações do markdown do JSON se o LLM devolver
            clean_json = raw_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            copy_data = json.loads(clean_json)
            return copy_data
        except Exception as e:
            print(f"[SalesPageGenerator] Erro ao consultar LLM para copy: {e}. Usando fallback.")
            return self._get_fallback_copy(product_name, niche, target_audience, price, guarantee_days)

    def _get_fallback_copy(self, product_name: str, niche: str, target_audience: str, price: str, guarantee_days: int) -> Dict[str, Any]:
        """
        Retorna uma copy de alta conversão estruturada de fallback caso a IA falhe.
        """
        return {
            "headline": f"Como Criar e Escalar uma Máquina de Conteúdo em {niche} Sem Passar o Dia Escrevendo ou Editando",
            "subheadline": f"O ecossistema inteligente que automatiza o seu funil completo de vendas, gerando artigos profundos, e-books 3D e cursos de alta conversão no piloto automático.",
            "story": "A maioria dos empreendedores falha porque passa 90% do tempo fazendo tarefas manuais e repetitivas. Escrever artigos de 2.000 palavras, diagramar ebooks inteiros, criar roteiros de aulas e subir páginas de venda consome sua energia. Você se torna um escravo operacional em vez de focar na escala do seu negócio.",
            "mechanism": f"O {product_name} inverte esse jogo. Nós criamos uma equipe de agentes virtuais baseados no DeepSeek que fazem todo o trabalho operacional para você. Carlão escreve, LiLi revisa, Tatiana gera as mídias e Seu Pereira garante a monetização. Tudo integrado a uma página de vendas com checkout direto.",
            "deliverables": [
                {"title": "Fábrica de Blogs Premium", "desc": "Geração automatizada de artigos SEO completos com imagens prontas para indexação instantânea no AdSense."},
                {"title": "Fábrica de Ebooks 3D", "desc": "Criação de livros digitais profundos com sumários dinâmicos e mockups tridimensionais atraentes."},
                {"title": "Fábrica de Cursos Estruturados", "desc": "Crie módulos e aulas didáticas completas em formato HTML/Markdown prontas para consumo com segurança por tokens."},
                {"title": "Funil de Vendas com Checkout Asaas", "desc": "Página de vendas premium integrada ao processamento de pagamentos seguro por PIX e cartão."}
            ],
            "value_stack": {
                "original_value": "R$ 2.997,00",
                "anchor_text": f"Contratar uma agência de conteúdo ou equipe de copywriters custaria no mínimo R$ 3.000 mensais. Com o {product_name}, você tem um time completo de agentes digitais trabalhando 24 horas por dia por uma fração desse valor.",
                "bonus": [
                    {"title": "Acesso Vitalício ao Grupo de Criadores", "value": "R$ 497,00"},
                    {"title": "Modelo de Página Alta Conversão", "value": "R$ 197,00"}
                ]
            },
            "guarantee": f"Nós assumimos todo o risco por você. Experimente o {product_name} por {guarantee_days} dias. Se você não achar que os agentes inteligentes pouparam pelo menos 20 horas do seu trabalho na primeira semana, basta nos enviar um e-mail e devolveremos 100% do seu dinheiro, sem perguntas.",
            "faq": [
                {"q": "Eu preciso saber programar para usar?", "a": "De forma alguma! A plataforma foi projetada para que você crie tudo em poucos cliques através do seu painel e do chat com o Hermes Agent."},
                {"q": "Como funciona a entrega do produto?", "a": "Assim que a compra for confirmada, o sistema gera um token SHA-256 exclusivo e envia o acesso direto ao leitor seguro para o cliente."},
                {"q": "O checkout é seguro?", "a": "Sim. Toda a transação é processada de ponta a ponta pela Asaas, um dos maiores e mais seguros gateways de pagamento do Brasil."}
            ]
        }

    def render_html(self, copy: Dict[str, Any], video_id: str, cta_url: str, delay_seconds: int = 180, guarantee_days: int = 7, price: str = "R$ 97,00") -> str:
        """
        Gera o código HTML/CSS/JS final aplicando os padrões de design Impeccable (sem cores puras, fontes robustas, marquee e delay de CTA).
        """
        # Seleção de fontes e cores HSL do Impeccable (fundo escuro azulado elegante)
        display_font = "Space Grotesk"
        body_font = "Inter"
        
        # Robust/Defensive key parsing to avoid crashes with LLM key discrepancies
        headline = copy.get("headline") or copy.get("lead_headline") or copy.get("title") or "Página de Vendas"
        subheadline = copy.get("subheadline") or copy.get("lead_subheadline") or ""
        story = copy.get("story") or copy.get("story_villain") or ""
        mechanism = copy.get("mechanism") or copy.get("unique_mechanism") or ""
        deliverables = copy.get("deliverables") or copy.get("deliverables_list") or []
        value_stack = copy.get("value_stack") or copy.get("value_stack_anchor") or {}
        guarantee = copy.get("guarantee") or copy.get("risk_reversal") or ""
        faq = copy.get("faq") or copy.get("faq_items") or []

        # Make sure that subelements are of the correct types and default values
        original_value = value_stack.get("original_value") or "R$ 2.997,00"
        anchor_text = value_stack.get("anchor_text") or ""
        bonus = value_stack.get("bonus") or []

        # Elementos de deliverable HTML
        deliverables_html = ""
        for item in deliverables:
            deliverables_html += f"""
            <div class="card">
                <div class="card-icon">⚡</div>
                <h3>{item.get('title')}</h3>
                <p>{item.get('desc')}</p>
            </div>
            """

        # Bônus do Value Stack
        bonus_html = ""
        for b in bonus:
            bonus_html += f"""
            <div class="bonus-item">
                <span>🎁 {b.get('title')}</span>
                <span class="value-strike">{b.get('value')}</span>
            </div>
            """

        # Accordion FAQ HTML
        faq_html = ""
        for i, f in enumerate(faq):
            faq_html += f"""
            <div class="faq-item">
                <button class="faq-trigger" onclick="toggleFaq({i})">
                    <span>{f.get('q')}</span>
                    <span class="faq-icon" id="faq-icon-{i}">+</span>
                </button>
                <div class="faq-content" id="faq-content-{i}">
                    <p>{f.get('a')}</p>
                </div>
            </div>
            """

        html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{headline[:50]}...</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family={display_font}:wght@500;700;900&family={body_font}:wght@300;400;500;600&display=swap" rel="stylesheet">
    
    <style>
        /* DESIGN SYSTEM IMPECCABLE: Cores baseadas em HSL sofisticados, evitando pretos/brancos puros */
        :root {{
            --bg-main: hsl(222, 47%, 6%);
            --bg-card: hsl(222, 40%, 10%);
            --bg-card-border: hsl(222, 30%, 15%);
            --text-title: hsl(210, 40%, 98%);
            --text-body: hsl(215, 20%, 75%);
            --text-muted: hsl(215, 16%, 57%);
            --primary: hsl(212, 100%, 48%);
            --primary-hover: hsl(212, 100%, 58%);
            --accent: hsl(142, 70%, 45%);
            --accent-glow: hsla(142, 70%, 45%, 0.15);
            --font-display: '{display_font}', sans-serif;
            --font-body: '{body_font}', sans-serif;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-main);
            color: var(--text-body);
            font-family: var(--font-body);
            line-height: 1.6;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
        }}

        h1, h2, h3, h4 {{
            color: var(--text-title);
            font-family: var(--font-display);
            font-weight: 700;
        }}

        /* Seções e Container */
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 24px;
        }}

        header {{
            padding: 40px 0;
            text-align: center;
        }}

        .badge-live {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background-color: hsla(212, 100%, 48%, 0.1);
            color: var(--primary);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 24px;
            border: 1px solid hsla(212, 100%, 48%, 0.2);
        }}

        .badge-live::before {{
            content: '';
            width: 8px;
            height: 8px;
            background-color: var(--primary);
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px var(--primary);
            animation: pulse 1.5s infinite;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(0.95); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.5; }}
        }}

        h1 {{
            font-size: 2.75rem;
            line-height: 1.25;
            letter-spacing: -0.03em;
            margin-bottom: 16px;
            font-weight: 900;
        }}

        .lead-sub {{
            font-size: 1.2rem;
            color: var(--text-muted);
            max-width: 800px;
            margin: 0 auto 32px auto;
            font-weight: 300;
        }}

        /* VSL Section */
        .vsl-container {{
            background-color: var(--bg-card);
            border: 1px solid var(--bg-card-border);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            aspect-ratio: 16/9;
            margin-bottom: 40px;
            position: relative;
        }}

        .vsl-container iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}

        /* Marquee Animado */
        .marquee-wrapper {{
            overflow: hidden;
            width: 100vw;
            position: relative;
            left: 50%;
            right: 50%;
            margin-left: -50vw;
            margin-right: -50vw;
            background: linear-gradient(90deg, var(--bg-card-border) 0%, var(--bg-card) 50%, var(--bg-card-border) 100%);
            border-top: 1px solid var(--bg-card-border);
            border-bottom: 1px solid var(--bg-card-border);
            padding: 14px 0;
            margin-bottom: 60px;
        }}

        .marquee-content {{
            display: flex;
            gap: 40px;
            width: max-content;
            animation: marquee 20s linear infinite;
        }}

        .marquee-item {{
            color: var(--text-title);
            font-family: var(--font-display);
            font-weight: 600;
            font-size: 15px;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        @keyframes marquee {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}

        /* Seção da História e Mecanismo */
        .section-split {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 48px;
            margin-bottom: 80px;
            align-items: center;
        }}

        .section-text h2 {{
            font-size: 2rem;
            margin-bottom: 20px;
            letter-spacing: -0.02em;
        }}

        .section-text p {{
            margin-bottom: 20px;
            color: var(--text-muted);
            font-size: 16px;
        }}

        /* Cards de Entregas */
        .grid-deliverables {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 24px;
            margin-bottom: 80px;
        }}

        .card {{
            background-color: var(--bg-card);
            border: 1px solid var(--bg-card-border);
            padding: 32px;
            border-radius: 12px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}

        .card:hover {{
            transform: translateY(-4px);
            border-color: var(--primary);
        }}

        .card-icon {{
            font-size: 24px;
            color: var(--primary);
            margin-bottom: 16px;
        }}

        .card h3 {{
            font-size: 1.25rem;
            margin-bottom: 12px;
        }}

        .card p {{
            color: var(--text-muted);
            font-size: 14px;
        }}

        /* Tabela Comparativa De/Para */
        .comparison-wrapper {{
            margin-bottom: 80px;
        }}

        .comparison-title {{
            text-align: center;
            margin-bottom: 40px;
        }}

        .comparison-title h2 {{
            font-size: 2rem;
        }}

        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }}

        .comp-column {{
            background-color: var(--bg-card);
            border: 1px solid var(--bg-card-border);
            border-radius: 12px;
            padding: 32px;
        }}

        .comp-column.negative {{
            border-left: 4px solid hsl(0, 70%, 45%);
        }}

        .comp-column.positive {{
            border-left: 4px solid var(--accent);
            box-shadow: 0 0 20px var(--accent-glow);
        }}

        .comp-column h3 {{
            margin-bottom: 24px;
            font-size: 1.4rem;
        }}

        .comp-list-item {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 16px;
            font-size: 15px;
        }}

        .comp-list-item.negative-item {{
            color: hsl(0, 10%, 75%);
        }}

        .comp-list-item.positive-item {{
            color: var(--text-title);
            font-weight: 500;
        }}

        /* Bloco de Oferta com Delay */
        .offer-section {{
            background-color: var(--bg-card);
            border: 1px solid var(--bg-card-border);
            border-radius: 16px;
            padding: 48px;
            text-align: center;
            margin-bottom: 80px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border-top: 4px solid var(--primary);
        }}

        .price-anchor {{
            text-decoration: line-through;
            color: var(--text-muted);
            font-size: 1.2rem;
            margin-bottom: 8px;
        }}

        .price-final {{
            font-size: 3.5rem;
            color: var(--text-title);
            font-family: var(--font-display);
            font-weight: 900;
            margin-bottom: 16px;
            letter-spacing: -0.03em;
        }}

        .anchor-description {{
            color: var(--text-muted);
            max-width: 650px;
            margin: 0 auto 32px auto;
            font-size: 15px;
        }}

        .bonus-stack {{
            max-width: 500px;
            margin: 0 auto 32px auto;
            text-align: left;
            background-color: var(--bg-main);
            border: 1px solid var(--bg-card-border);
            border-radius: 8px;
            padding: 20px;
        }}

        .bonus-item {{
            display: flex;
            justify-content: space-between;
            border-bottom: 1px dashed var(--bg-card-border);
            padding: 8px 0;
            font-size: 14px;
        }}

        .bonus-item:last-child {{
            border-bottom: none;
        }}

        .value-strike {{
            text-decoration: line-through;
            color: var(--text-muted);
        }}

        .btn-cta {{
            display: inline-block;
            background-color: var(--primary);
            color: #fff;
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 18px;
            text-decoration: none;
            padding: 18px 48px;
            border-radius: 8px;
            box-shadow: 0 6px 20px rgba(0, 102, 255, 0.3);
            transition: background-color 0.2s ease, transform 0.1s ease;
        }}

        .btn-cta:hover {{
            background-color: var(--primary-hover);
            transform: translateY(-2px);
        }}

        /* Garantia */
        .guarantee-wrapper {{
            display: grid;
            grid-template-columns: 100px 1fr;
            gap: 24px;
            background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-main) 100%);
            border: 1px solid var(--bg-card-border);
            padding: 32px;
            border-radius: 12px;
            align-items: center;
            margin-bottom: 80px;
            text-align: left;
        }}

        .guarantee-badge {{
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-display);
            font-weight: 900;
            font-size: 22px;
            color: #fff;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}

        .guarantee-text h4 {{
            font-size: 1.25rem;
            margin-bottom: 8px;
        }}

        .guarantee-text p {{
            color: var(--text-muted);
            font-size: 14px;
        }}

        /* FAQ Section Accordion */
        .faq-section {{
            margin-bottom: 80px;
        }}

        .faq-header {{
            text-align: center;
            margin-bottom: 40px;
        }}

        .faq-header h2 {{
            font-size: 2rem;
        }}

        .faq-items {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .faq-item {{
            background-color: var(--bg-card);
            border: 1px solid var(--bg-card-border);
            margin-bottom: 16px;
            border-radius: 8px;
            overflow: hidden;
        }}

        .faq-trigger {{
            width: 100%;
            background: none;
            border: none;
            color: var(--text-title);
            font-family: var(--font-display);
            font-weight: 600;
            font-size: 16px;
            padding: 20px 24px;
            text-align: left;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .faq-icon {{
            font-size: 20px;
            color: var(--primary);
            transition: transform 0.2s ease;
        }}

        .faq-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.2s ease-out, padding 0.2s ease;
            padding: 0 24px;
        }}

        .faq-content p {{
            padding-bottom: 20px;
            color: var(--text-muted);
            font-size: 14px;
        }}

        /* CTA De segurança */
        .cta-security {{
            margin-top: 16px;
            font-size: 12px;
            color: var(--text-muted);
        }}

        /* Responsividade */
        @media (max-width: 768px) {{
            h1 {{ font-size: 2rem; }}
            .section-split, .comparison-grid {{
                grid-template-columns: 1fr;
            }}
            .guarantee-wrapper {{
                grid-template-columns: 1fr;
                text-align: center;
            }}
            .guarantee-badge {{
                margin: 0 auto;
            }}
        }}

        /* Controle do Delay (Checkout ocultado por padrão) */
        #delayed-offer {{
            display: none;
        }}
    </style>
</head>
<body>

    <header>
        <div class="container">
            <div class="badge-live">Exclusivo: Nova Engenharia de Infoproduto</div>
            <h1>{headline}</h1>
            <p class="lead-sub">{subheadline}</p>
        </div>
    </header>

    <main class="container">
        <!-- VSL (Vídeo de Vendas) -->
        <section class="vsl-container">
            <iframe src="https://www.youtube.com/embed/{video_id}?autoplay=0&rel=0&modestbranding=1" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen></iframe>
        </section>

        <!-- Marquee de Benefícios -->
        <div class="marquee-wrapper">
            <div class="marquee-content">
                <span class="marquee-item">🚀 100% Automatizado</span>
                <span class="marquee-item">💎 Agentes Dedicados</span>
                <span class="marquee-item">⚡ Entrega Segura</span>
                <span class="marquee-item">📈 Escalável em Minutos</span>
                <span class="marquee-item">💵 Zero Taxas Ocultas</span>
                <!-- Clonado para efeito infinito -->
                <span class="marquee-item">🚀 100% Automatizado</span>
                <span class="marquee-item">💎 Agentes Dedicados</span>
                <span class="marquee-item">⚡ Entrega Segura</span>
                <span class="marquee-item">📈 Escalável em Minutos</span>
                <span class="marquee-item">💵 Zero Taxas Ocultas</span>
            </div>
        </div>

        <!-- A Dor vs O Mecanismo Único -->
        <section class="section-split">
            <div class="section-text">
                <h2>Por que a criação manual está te matando?</h2>
                <p>{story}</p>
            </div>
            <div class="section-text">
                <h2>A Nova Era: Orquestração Autônoma</h2>
                <p>{mechanism}</p>
            </div>
        </section>

        <!-- Entregáveis (Cards) -->
        <section class="grid-deliverables">
            {deliverables_html}
        </section>

        <!-- Tabela Comparativa De/Para -->
        <section class="comparison-wrapper">
            <div class="comparison-title">
                <h2>O Grande Contraste</h2>
                <p style="color: var(--text-muted); margin-top: 8px;">A diferença entre fazer na mão e colocar os agentes para rodar</p>
            </div>
            <div class="comparison-grid">
                <div class="comp-column negative">
                    <h3>Fazendo Manualmente</h3>
                    <div class="comp-list-item negative-item">❌ Passar semanas escrevendo artigos e ebooks</div>
                    <div class="comp-list-item negative-item">❌ Roteirizar, gravar e editar aulas sem fim</div>
                    <div class="comp-list-item negative-item">❌ Pagar caro a designers para logos e criativos</div>
                    <div class="comp-list-item negative-item">❌ Conectar ferramentas de checkout complexas e travar</div>
                </div>
                <div class="comp-column positive">
                    <h3>Com o Dezafira</h3>
                    <div class="comp-list-item positive-item">✅ Conteúdo robusto gerado por agentes em 5 minutos</div>
                    <div class="comp-list-item positive-item">✅ Cursos formatados em Markdown limpo estruturado</div>
                    <div class="comp-list-item positive-item">✅ Identidade visual e logos dinâmicas geradas pela Agnes</div>
                    <div class="comp-list-item positive-item">✅ Checkout Asaas pronto para receber via PIX no automático</div>
                </div>
            </div>
        </section>

        <!-- Reversão de Risco & Garantia -->
        <section class="guarantee-wrapper">
            <div class="guarantee-badge">{guarantee_days} dias</div>
            <div class="guarantee-text">
                <h4>Garantia de Satisfação Incondicional</h4>
                <p>{guarantee}</p>
            </div>
        </section>

        <!-- Bloco de Oferta Principal (Delayed) -->
        <section class="offer-section" id="delayed-offer">
            <h2 style="font-size: 2rem; margin-bottom: 8px;">Acesso Imediato ao Ecossistema</h2>
            <p class="price-anchor">Valor Real: {original_value}</p>
            <div class="price-final">{price}</div>
            
            <p class="anchor-description">{anchor_text}</p>
            
            <div class="bonus-stack">
                <h4 style="font-size: 14px; margin-bottom: 12px; text-transform: uppercase; color: var(--text-muted)">Bônus Exclusivos Inclusos:</h4>
                {bonus_html}
            </div>

            <a href="{cta_url}" class="btn-cta">⚡ QUERO MEU ACESSO AGORA</a>
            <div class="cta-security">🔒 Checkout Seguro e Criptografado por Asaas. Acesso liberado instantaneamente.</div>
        </section>

        <!-- FAQ Accordion -->
        <section class="faq-section">
            <div class="faq-header">
                <h2>Dúvidas Frequentes</h2>
                <p style="color: var(--text-muted); margin-top: 8px;">Respostas para as perguntas mais comuns</p>
            </div>
            <div class="faq-items">
                {faq_html}
            </div>
        </section>

    </main>

    <footer style="padding: 60px 0; text-align: center; border-top: 1px solid var(--bg-card-border); color: var(--text-muted); font-size: 13px;">
        <div class="container">
            <p>&copy; {headline[:20]} - Todos os direitos reservados.</p>
        </div>
    </footer>

    <script>
        // Lógica de Delay para o Bloco de Oferta (VSL Delay)
        // Ocultado por padrão. Mostra depois de X segundos.
        const delaySeconds = {delay_seconds};
        
        console.log("[VSL Delay] Aguardando " + delaySeconds + " segundos para exibir a oferta...");
        setTimeout(() => {{
            const offerSec = document.getElementById('delayed-offer');
            if (offerSec) {{
                offerSec.style.display = 'block';
                // Scroll suave até a oferta para chamar atenção
                offerSec.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                console.log("[VSL Delay] Oferta liberada!");
            }}
        }}, delaySeconds * 1000);

        // Accordion FAQ toggle
        function toggleFaq(index) {{
            const content = document.getElementById('faq-content-' + index);
            const icon = document.getElementById('faq-icon-' + index);
            if (content.style.maxHeight && content.style.maxHeight !== '0px') {{
                content.style.maxHeight = '0px';
                icon.innerText = '+';
            }} else {{
                content.style.maxHeight = content.scrollHeight + 'px';
                icon.innerText = '-';
            }}
        }}
    </script>
</body>
</html>"""
        return html_template
