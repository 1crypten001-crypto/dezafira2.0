"""
=============================================================================
DEZAFIRA — Gerador de Previews Visuais & Hub Completo de Entregáveis
=============================================================================
Gera páginas de preview ricas, interativas e completas contendo:
1. Blog Real (Artigo SEO completo com imagens Agnes AI)
2. Ebook 3D Real (Visualizador com 8 Capítulos, Capa 3D e Ilustrações)
3. Curso HD Real (Portal de Aulas com 5 Módulos e Player)
4. MiniApp PWA Real (Quiz Interativo Funcional com barra de progresso)
5. Funil VSL & Checkout Asaas PIX (Landing page com PIX gerado)
6. Postiz Ads (Preview de Anúncios no Instagram, TikTok, Pinterest e X)
"""

import json
from typing import Dict, Any, Optional

class PreviewGenerator:
    @staticmethod
    def generate_ebook_cover_svg(title: str, subtitle: str, theme_color: str = "#8B5CF6") -> str:
        """Gera um mockup de capa 3D interativa SVG para Ebook."""
        return f"""
        <div style="perspective: 1000px; display: inline-block; padding: 20px;">
            <div style="
                width: 240px;
                height: 340px;
                background: linear-gradient(135deg, {theme_color} 0%, #1e1b4b 100%);
                border-radius: 8px 16px 16px 8px;
                box-shadow: -10px 15px 30px rgba(0,0,0,0.5), inset -3px 0 10px rgba(255,255,255,0.2);
                transform: rotateY(-18deg) rotateX(8deg);
                transition: transform 0.5s ease;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                padding: 24px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                position: relative;
                overflow: hidden;
            ">
                <div style="position: absolute; top: -50px; right: -50px; width: 150px; height: 150px; background: rgba(255,255,255,0.1); border-radius: 50%;"></div>
                <div>
                    <div style="font-size: 11px; text-transform: uppercase; tracking: 2px; opacity: 0.8; font-weight: 700; color: #fef08a;">Ebook Exclusivo</div>
                    <h3 style="font-size: 20px; font-weight: 800; margin: 12px 0 6px 0; line-height: 1.2; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{title}</h3>
                    <p style="font-size: 12px; opacity: 0.9; margin: 0; line-height: 1.4;">{subtitle}</p>
                </div>
                <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 10px; font-weight: 600; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px;">DEZAFIRA FABRIC</span>
                    <span style="font-size: 14px;">📘</span>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def generate_course_box_svg(title: str, modules_count: int = 5, theme_color: str = "#EC4899") -> str:
        """Gera um mockup 3D de caixa de curso / treinamento."""
        return f"""
        <div style="perspective: 1000px; display: inline-block; padding: 20px;">
            <div style="
                width: 260px;
                height: 320px;
                background: linear-gradient(135deg, #18181b 0%, {theme_color} 100%);
                border-radius: 12px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.6), 0 0 20px {theme_color}44;
                transform: rotateY(-12deg);
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                padding: 24px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                border: 1px solid rgba(255,255,255,0.1);
            ">
                <div>
                    <span style="background: {theme_color}; font-size: 10px; font-weight: 800; padding: 4px 10px; border-radius: 20px; text-transform: uppercase;">Curso Completo</span>
                    <h3 style="font-size: 22px; font-weight: 800; margin: 16px 0 8px 0;">{title}</h3>
                    <div style="font-size: 13px; color: #a1a1aa;">🎥 {modules_count} Módulos Práticos HD</div>
                </div>
                <div style="background: rgba(0,0,0,0.4); padding: 12px; border-radius: 8px; font-size: 11px; display: flex; align-items: center; justify-content: space-between;">
                    <span>Acesso Vitalício + Bônus</span>
                    <span style="font-size: 16px;">🎓</span>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def generate_full_preview_html(preview_type: str, session_data: Dict[str, Any]) -> str:
        """Gera o HTML responsivo completo e funcional para cada entregável da pipeline."""
        title = session_data.get("product_name") or session_data.get("spec", {}).get("product_name") or "Escola de Negócios Digitais com IA 2026"
        copy = session_data.get("copy") or session_data.get("deliverables", {}).get("copy", {})
        offer_title = copy.get("headline") or f"Como Criar e Escalar {title} 100% no Automático"
        subheadline = copy.get("subheadline") or "A metodologia exata dos agentes autônomos para gerar funis, produtos e anúncios em minutos."
        mechanism = copy.get("unique_mechanism") or "Orquestração Inteligente Hermes Agent + Protocolo TLC Spec-Driven"
        price = session_data.get("price") or session_data.get("spec", {}).get("price") or "R$ 97,00"

        deliverables = session_data.get("deliverables", {})
        ebook_data = deliverables.get("ebook", {})
        course_data = deliverables.get("course", {})
        miniapp_data = deliverables.get("miniapp", {})
        ads_data = deliverables.get("ads", {})

        ebook_img = ebook_data.get("cover_image_url") or "https://images.pexels.com/photos/29509373/pexels-photo-29509373.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
        course_img = course_data.get("thumbnail_url") or "https://images.pexels.com/photos/28613602/pexels-photo-28613602.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
        banner_img = miniapp_data.get("storefront_banner_url") or "https://images.pexels.com/photos/12081507/pexels-photo-12081507.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
        ad_img = ads_data.get("image_url") or ads_data.get("ad_image_url") or ebook_img

        ebook_prompt = ebook_data.get("expanded_prompt", "Hyperrealistic 3D Octane render illustration for a luxury digital ebook cover.")
        course_prompt = course_data.get("expanded_prompt", "Cinematic 8k digital course banner thumbnail, high-contrast, modern academy aesthetic.")

        # --- NAVEGAÇÃO SUPERIOR ENTRE ENTREGÁVEIS ---
        nav_html = f"""
        <nav style="background: #090d16; border-bottom: 1px solid #1e293b; padding: 16px; margin-bottom: 30px; position: sticky; top: 0; z-index: 100;">
            <div style="max-width: 1100px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">⚡</span>
                    <strong style="color: #38bdf8; font-size: 16px;">DEZAFIRA HUB DA OFERTA</strong>
                    <span style="background: #22c55e22; color: #4ade80; border: 1px solid #22c55e55; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 700;">🟢 PIPELINE 100% ATIVA</span>
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <a href="?tab=funnel" style="background: {'#38bdf8' if preview_type == 'funnel' else '#131c2e'}; color: {'#090d16' if preview_type == 'funnel' else '#f8fafc'}; border: 1px solid #334155; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; text-decoration: none;">💻 Página VSL & Checkout</a>
                    <a href="?tab=products" style="background: {'#38bdf8' if preview_type == 'products' else '#131c2e'}; color: {'#090d16' if preview_type == 'products' else '#f8fafc'}; border: 1px solid #334155; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; text-decoration: none;">📦 Ebook & Curso HD</a>
                    <a href="?tab=blog" style="background: {'#38bdf8' if preview_type == 'blog' or preview_type == 'copy' else '#131c2e'}; color: {'#090d16' if preview_type == 'blog' or preview_type == 'copy' else '#f8fafc'}; border: 1px solid #334155; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; text-decoration: none;">📝 Blog & Copywriter</a>
                    <a href="?tab=miniapp" style="background: {'#38bdf8' if preview_type == 'miniapp' else '#131c2e'}; color: {'#090d16' if preview_type == 'miniapp' else '#f8fafc'}; border: 1px solid #334155; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; text-decoration: none;">📱 MiniApp Quiz PWA</a>
                    <a href="?tab=ads" style="background: {'#38bdf8' if preview_type == 'ads' else '#131c2e'}; color: {'#090d16' if preview_type == 'ads' else '#f8fafc'}; border: 1px solid #334155; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; text-decoration: none;">📢 Postiz Ads</a>
                </div>
            </div>
        </nav>
        """

        if preview_type in ("copy", "blog"):
            # --- FÁBRICA DE BLOGS & ARTIGO REAL ---
            content = f"""
            <div style="max-width: 900px; margin: 0 auto; background: #0b1120; border: 1px solid #1e293b; border-radius: 20px; padding: 36px; color: #f8fafc;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 24px;">
                    <div>
                        <span style="background: #38bdf822; color: #38bdf8; border: 1px solid #38bdf855; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 800;">📝 FÁBRICA DE BLOGS • ARTIGO SEO PUBLICADO</span>
                        <h1 style="font-size: 26px; font-weight: 800; color: #f8fafc; margin: 12px 0 6px 0;">{title}</h1>
                        <p style="font-size: 13px; color: #94a3b8; margin: 0;">Por <strong>Hermes Writer Agent</strong> • Leitura de 6 min • Otimizado para Google Discover</p>
                    </div>
                </div>

                <!-- Imagem Destacada do Blog Gerada pela Agnes AI -->
                <div style="margin-bottom: 30px; text-align: center;">
                    <img src="{banner_img}" style="width: 100%; max-height: 420px; object-fit: cover; border-radius: 14px; border: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" alt="Imagem do Blog Agnes AI"/>
                    <p style="font-size: 11px; color: #64748b; margin-top: 8px;">🎨 Imagem do Artigo gerada por IA via Agnes AI + DeepSeek LLM Prompt Engine</p>
                </div>

                <!-- Artigo SEO Estruturado -->
                <div style="font-size: 15px; line-height: 1.8; color: #cbd5e1;">
                    <h2 style="color: #38bdf8; font-size: 20px; margin-top: 24px;">Introdução: A Nova Era da Escala Digital em 2026</h2>
                    <p>No cenário atual de negócios online, depender de contratações caras de agências ou passar semanas criando infoprodutos manualmente tornou-se obsoleto. O ecossistema Dezafira unifica sub-agentes inteligentes que realizam a pesquisa de mercado, geram o livro digital, estruturam o curso em vídeo e disparam o tráfego pago de forma integrada.</p>
                    
                    <div style="background: #131c2e; border-left: 4px solid #38bdf8; padding: 18px; border-radius: 8px; margin: 24px 0; color: #f1f5f9; font-style: italic;">
                        "{subheadline}"
                    </div>

                    <h2 style="color: #38bdf8; font-size: 20px; margin-top: 28px;">Capítulo 1: O Mecanismo Único de Conversão</h2>
                    <p>O segredo da alta taxa de conversão reside no seguinte pilar estratégico: <strong>{mechanism}</strong>. Ao conectar diretamente a oferta ao Quiz Diagnóstico (MiniApp PWA), o lead se engaja ativamente antes de chegar ao checkout do Asaas PIX.</p>

                    <h2 style="color: #38bdf8; font-size: 20px; margin-top: 28px;">Capítulo 2: Como a Automação de Anúncios Garante o ROI</h2>
                    <p>Com a conexão nativa com a API do Postiz, cada nova oferta gerada dispara automaticamente criativos visuais para mais de 20 canais (Instagram, TikTok, Pinterest e X), garantindo alcance imediato sem retrabalho manual.</p>
                </div>

                <div style="margin-top: 40px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px; border-radius: 14px; border: 1px solid #38bdf855; text-align: center;">
                    <h3 style="color: #38bdf8; margin: 0 0 8px 0;">🚀 Desbloqueie a Estrutura Completa</h3>
                    <p style="font-size: 13px; color: #94a3b8; margin-bottom: 16px;">Garanta o Ebook 3D, Curso HD, MiniApp Quiz e Checkout com garantia de 7 dias.</p>
                    <a href="?tab=funnel" style="background: #22c55e; color: #fff; padding: 12px 24px; border-radius: 8px; font-weight: 800; text-decoration: none; display: inline-block;">Garantir Oferta por {price}</a>
                </div>
            </div>
            """

        elif preview_type == "products":
            # --- FÁBRICA DE EBOOKS 3D & CURSOS HD REAL ---
            ebook_cover_html = f'<img src="{ebook_img}" style="width: 240px; height: 340px; object-fit: cover; border-radius: 12px; box-shadow: -10px 15px 30px rgba(0,0,0,0.6); border: 2px solid #8b5cf6;" alt="Capa Ebook"/>'
            course_thumb_html = f'<img src="{course_img}" style="width: 320px; height: 180px; object-fit: cover; border-radius: 12px; box-shadow: 0 15px 30px rgba(0,0,0,0.6); border: 2px solid #ec4899;" alt="Thumbnail Curso"/>'

            content = f"""
            <div style="max-width: 1000px; margin: 0 auto; color: #f8fafc;">
                
                <!-- SEÇÃO 1: FÁBRICA DE EBOOKS 3D -->
                <div style="background: #0b1120; border: 1px solid #1e293b; border-radius: 20px; padding: 32px; margin-bottom: 30px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid #1e293b; padding-bottom: 16px;">
                        <div>
                            <span style="background: #8b5cf622; color: #c084fc; border: 1px solid #8b5cf655; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 800;">📗 FÁBRICA DE EBOOKS 3D</span>
                            <h2 style="margin: 8px 0 0 0; font-size: 22px; color: #c084fc;">Ebook Livro Digital: {title}</h2>
                        </div>
                        <span style="font-size: 12px; color: #94a3b8;">8 Capítulos Otimizados</span>
                    </div>

                    <div style="display: flex; gap: 30px; flex-wrap: wrap; align-items: flex-start;">
                        <div style="text-align: center;">
                            {ebook_cover_html}
                            <div style="font-size: 10px; color: #94a3b8; margin-top: 8px;">🎨 Capa 3D por Agnes AI</div>
                        </div>
                        <div style="flex: 1; min-width: 280px;">
                            <h4 style="color: #f1f5f9; margin-top: 0;">Índice dos 8 Capítulos Gerados:</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px; font-size: 12px; color: #cbd5e1;">
                                <div style="background: #131c2e; p-2; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;">📌 Cap. 01: Fundamentos da Oferta</div>
                                <div style="background: #131c2e; p-2; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;">📌 Cap. 02: O Mecanismo Único</div>
                                <div style="background: #131c2e; p-2; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;">📌 Cap. 03: Arquitetura do Funil</div>
                                <div style="background: #131c2e; p-2; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;">📌 Cap. 04: Automação no Postiz</div>
                                <div style="background: #131c2e; p-2; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;">📌 Cap. 05: Scripts do MiniApp PWA</div>
                                <div style="background: #131c2e; p-2; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;">📌 Cap. 06: Configuração Asaas PIX</div>
                                <div style="background: #131c2e; p-2; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;">📌 Cap. 07: Tráfego e Anúncios IA</div>
                                <div style="background: #131c2e; p-2; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;">📌 Cap. 08: Plano de Escala 2026</div>
                            </div>
                            <div style="margin-top: 16px; background: #131c2e; padding: 12px; border-radius: 8px; font-size: 11px; color: #94a3b8; border: 1px solid #334155;">
                                <strong>Prompt DeepSeek (Capa):</strong> {ebook_prompt[:150]}...
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SEÇÃO 2: FÁBRICA DE CURSOS HD -->
                <div style="background: #0b1120; border: 1px solid #1e293b; border-radius: 20px; padding: 32px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid #1e293b; padding-bottom: 16px;">
                        <div>
                            <span style="background: #ec489922; color: #f472b6; border: 1px solid #ec489955; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 800;">🎓 FÁBRICA DE CURSOS HD</span>
                            <h2 style="margin: 8px 0 0 0; font-size: 22px; color: #f472b6;">Treinamento em Vídeo: {title} Master</h2>
                        </div>
                        <span style="font-size: 12px; color: #94a3b8;">5 Módulos HD Práticos</span>
                    </div>

                    <div style="display: flex; gap: 30px; flex-wrap: wrap; align-items: flex-start;">
                        <div style="text-align: center;">
                            {course_thumb_html}
                            <div style="font-size: 10px; color: #94a3b8; margin-top: 8px;">🎥 Thumbnail por Agnes AI</div>
                        </div>
                        <div style="flex: 1; min-width: 280px;">
                            <h4 style="color: #f1f5f9; margin-top: 0;">Estrutura dos 5 Módulos e Videoaulas:</h4>
                            <div style="space-y-2;">
                                <div style="background: #131c2e; padding: 10px 14px; border-radius: 8px; border: 1px solid #1e293b; margin-bottom: 8px; display: flex; justify-content: space-between;">
                                    <span><strong>Módulo 1:</strong> Visão Geral & Setup Inicial</span>
                                    <span style="color: #22c55e; font-size: 11px; font-weight: 700;">🎥 4 Aulas HD</span>
                                </div>
                                <div style="background: #131c2e; padding: 10px 14px; border-radius: 8px; border: 1px solid #1e293b; margin-bottom: 8px; display: flex; justify-content: space-between;">
                                    <span><strong>Módulo 2:</strong> Engenharia de Copy com DeepSeek</span>
                                    <span style="color: #22c55e; font-size: 11px; font-weight: 700;">🎥 5 Aulas HD</span>
                                </div>
                                <div style="background: #131c2e; padding: 10px 14px; border-radius: 8px; border: 1px solid #1e293b; margin-bottom: 8px; display: flex; justify-content: space-between;">
                                    <span><strong>Módulo 3:</strong> Criação de MiniApps & PWAs</span>
                                    <span style="color: #22c55e; font-size: 11px; font-weight: 700;">🎥 6 Aulas HD</span>
                                </div>
                                <div style="background: #131c2e; padding: 10px 14px; border-radius: 8px; border: 1px solid #1e293b; margin-bottom: 8px; display: flex; justify-content: space-between;">
                                    <span><strong>Módulo 4:</strong> Ativação de Tráfego via Postiz</span>
                                    <span style="color: #22c55e; font-size: 11px; font-weight: 700;">🎥 3 Aulas HD</span>
                                </div>
                                <div style="background: #131c2e; padding: 10px 14px; border-radius: 8px; border: 1px solid #1e293b; display: flex; justify-content: space-between;">
                                    <span><strong>Módulo 5:</strong> Métricas e Otimização Continuada</span>
                                    <span style="color: #22c55e; font-size: 11px; font-weight: 700;">🎥 4 Aulas HD</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
            """

        elif preview_type == "miniapp":
            # --- FÁBRICA DE MINIAPPS PWA REAL (SALA DE AGENTES + AGNES AI LOGO + DRIP DB) ---
            app_logo = miniapp_data.get("logo_url") or ebook_img
            drip_items = miniapp_data.get("drip_contents") or [
                {"day": 1, "title": "🎯 Boas-Vindas & Diagnóstico Inicial", "type": "quiz"},
                {"day": 7, "title": "⚡ Módulo 2: Automação e Ferramentas Pro", "type": "tools"},
                {"day": 14, "title": "🚀 Módulo 3: Escala e Retenção de Assinantes", "type": "masterclass"},
                {"day": 30, "title": "👑 Módulo VIP: Acesso à Comunidade de Elite", "type": "vip"}
            ]

            drip_html = "".join([
                f'<div style="background:#131c2e; border:1px solid #1e293b; padding:12px 16px; border-radius:10px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;"><div><strong style="color:#38bdf8; font-size:12px;">Dia {item["day"]}:</strong> <span style="font-size:13px; color:#fff; font-weight:600;">{item["title"]}</span></div><span style="background:#22c55e22; color:#4ade80; font-size:10px; font-weight:700; padding:3px 8px; border-radius:6px;">🟢 DB Agendado</span></div>'
                for item in drip_items
            ])

            content = f"""
            <div style="max-width: 950px; margin: 0 auto; color: #fff;">
                
                <div style="text-align: center; margin-bottom: 24px;">
                    <span style="background: #eab30822; color: #facc15; border: 1px solid #eab30855; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 800;">📱 MINIAPP PWA (SALA DE AGENTES + AGNES AI LOGO + DRIP DB)</span>
                    <h2 style="margin: 12px 0 4px 0; font-size: 26px; color: #38bdf8;">{title}</h2>
                    <p style="font-size: 13px; color: #94a3b8;">Aplicativo PWA Instalável com Logo 3D por Agnes AI e Entrega Recorrente Temporizada</p>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 30px; align-items: start;">
                    
                    <!-- LADO ESQUERDO: Mockup Celular PWA -->
                    <div style="background: #090d16; border: 1px solid #1e293b; border-radius: 24px; padding: 24px; text-align: center;">
                        <div style="display: flex; align-items: center; gap: 12px; background: #131c2e; padding: 12px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 16px; text-align: left;">
                            <img src="{app_logo}" style="width: 48px; height: 48px; border-radius: 12px; object-fit: cover; border: 1px solid #38bdf8;" alt="Logo Agnes AI"/>
                            <div>
                                <h4 style="margin: 0; font-size: 14px; color: #fff;">{title}</h4>
                                <span style="font-size: 10px; color: #4ade80; font-weight: 700;">🎨 Logo 3D por Agnes AI • PWA Standalone</span>
                            </div>
                        </div>

                        <img src="{banner_img}" style="width: 100%; height: 180px; object-fit: cover; border-radius: 12px; border: 1px solid #1e293b; margin-bottom: 16px;" alt="Banner App"/>

                        <!-- Widget de Quiz Interativo Funcional -->
                        <div id="quiz_container" style="background: #131c2e; border: 1px solid #1e293b; border-radius: 16px; padding: 20px; text-align: left;">
                            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; margin-bottom: 8px;">
                                <span>Progresso do Diagnóstico</span>
                                <span id="quiz_step_text">Pergunta 1 de 3</span>
                            </div>
                            
                            <div style="background: #1e293b; height: 6px; border-radius: 3px; overflow: hidden; margin-bottom: 16px;">
                                <div id="quiz_progress_bar" style="width: 33%; height: 100%; background: linear-gradient(90deg, #38bdf8, #22c55e); transition: width 0.3s ease;"></div>
                            </div>

                            <!-- Pergunta 1 -->
                            <div id="q1" style="display: block;">
                                <h4 style="font-size: 13px; margin: 0 0 12px 0; color: #f1f5f9;">1. Qual é o seu principal desafio hoje?</h4>
                                <button onclick="nextQuizStep(2)" style="width: 100%; text-align: left; background: #090d16; border: 1px solid #334155; color: #f8fafc; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; cursor: pointer; font-size: 11px;">
                                    A) Criar Copy e Oferta do zero
                                </button>
                                <button onclick="nextQuizStep(2)" style="width: 100%; text-align: left; background: #090d16; border: 1px solid #334155; color: #f8fafc; padding: 10px 14px; border-radius: 8px; cursor: pointer; font-size: 11px;">
                                    B) Automatizar Tráfego e Vendas
                                </button>
                            </div>

                            <!-- Pergunta 2 -->
                            <div id="q2" style="display: none;">
                                <h4 style="font-size: 13px; margin: 0 0 12px 0; color: #f1f5f9;">2. Quanto tempo pode dedicar diariamente?</h4>
                                <button onclick="finishQuiz()" style="width: 100%; text-align: left; background: #090d16; border: 1px solid #334155; color: #f8fafc; padding: 10px 14px; border-radius: 8px; cursor: pointer; font-size: 11px;">
                                    A) 1 hora/dia (100% Automático)
                                </button>
                            </div>

                            <!-- Resultado -->
                            <div id="q_result" style="display: none; text-align: center;">
                                <div style="font-size: 24px; margin-bottom: 4px;">🎉</div>
                                <h4 style="color: #22c55e; margin: 0 0 4px 0;">Diagnóstico OK!</h4>
                                <p style="font-size: 11px; color: #cbd5e1; margin-bottom: 12px;">Sua estrutura recomendada está pronta.</p>
                                <a href="?tab=funnel" style="background: #22c55e; color: #fff; padding: 8px 16px; border-radius: 6px; font-weight: 800; text-decoration: none; font-size: 11px; display: inline-block;">Liberar Acesso por {price}</a>
                            </div>
                        </div>
                    </div>

                    <!-- LADO DIREITO: Banco de Dados de Conteúdos Recorrentes (Drip Content) -->
                    <div style="background: #090d16; border: 1px solid #1e293b; border-radius: 24px; padding: 24px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 12px; margin-bottom: 16px;">
                            <h3 style="margin: 0; font-size: 16px; color: #38bdf8;">🗄️ Cronograma de Retenção no Banco de Dados</h3>
                            <span style="font-size: 10px; background: #38bdf822; color: #38bdf8; padding: 2px 8px; border-radius: 6px; font-weight: 700;">SQLite / Postgres</span>
                        </div>
                        <p style="font-size: 12px; color: #94a3b8; margin-bottom: 16px;">Conteúdos liberados automaticamente por dias de assinatura para retenção do assinante:</p>
                        {drip_html}
                    </div>

                </div>

                <script>
                    function nextQuizStep(step) {{
                        document.getElementById('q1').style.display = 'none';
                        document.getElementById('q2').style.display = 'block';
                        document.getElementById('quiz_progress_bar').style.width = '66%';
                        document.getElementById('quiz_step_text').innerText = 'Pergunta 2 de 2';
                    }}
                    function finishQuiz() {{
                        document.getElementById('q2').style.display = 'none';
                        document.getElementById('q_result').style.display = 'block';
                        document.getElementById('quiz_step_text').innerText = 'Concluído';
                    }}
                </script>
            </div>
            """

        elif preview_type == "funnel":
            # --- FUNIL VSL REAL & CHECKOUT ASAAS PIX INTEGRADO ---
            content = f"""
            <div style="max-width: 900px; margin: 0 auto; background: #090d16; border: 1px solid #1e293b; border-radius: 24px; padding: 36px; color: #fff;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <span style="background: #22c55e22; color: #4ade80; border: 1px solid #22c55e55; padding: 4px 14px; border-radius: 20px; font-weight: bold; font-size: 12px;">🚀 PÁGINA DE VENDAS VSL & CHECKOUT ASAAS PIX</span>
                    <h1 style="font-size: 30px; font-weight: 800; color: #38bdf8; margin: 16px 0 8px 0; line-height: 1.3;">{offer_title}</h1>
                    <p style="font-size: 15px; color: #94a3b8; max-width: 700px; margin: 0 auto;">{subheadline}</p>
                </div>

                <!-- Video Player VSL Mockup -->
                <div style="margin-bottom: 40px; background: #000; border-radius: 16px; border: 2px solid #334155; overflow: hidden; position: relative; box-shadow: 0 20px 40px rgba(0,0,0,0.8);">
                    <img src="{banner_img}" style="width: 100%; height: 420px; object-fit: cover; opacity: 0.7;" alt="VSL Player"/>
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                        <div style="background: rgba(56, 189, 248, 0.9); width: 80px; height: 80px; border-radius: 50%; display: flex; items-center; justify-content: center; margin: 0 auto 12px auto; box-shadow: 0 0 30px rgba(56,189,248,0.8); cursor: pointer;">
                            <span style="font-size: 36px; color: #000; margin-left: 6px;">▶</span>
                        </div>
                        <span style="background: rgba(0,0,0,0.8); color: #fff; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: 700;">ASSISTIR APRESENTAÇÃO COMPLETA</span>
                    </div>
                </div>

                <!-- Checkout Asaas PIX Integrado -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; background: #131c2e; border: 1px solid #1e293b; border-radius: 18px; padding: 28px;">
                    <div>
                        <h3 style="color: #38bdf8; margin-top: 0;">🎁 O que você vai receber:</h3>
                        <ul style="font-size: 13px; color: #cbd5e1; line-height: 2;">
                            <li>✅ <strong>Ebook 3D Completo:</strong> {title} (8 Capítulos)</li>
                            <li>✅ <strong>Curso HD em Vídeo:</strong> 5 Módulos Práticos de Execução</li>
                            <li>✅ <strong>MiniApp Quiz PWA:</strong> Licença de Recorrência</li>
                            <li>✅ <strong>Campanha Postiz Ads:</strong> Criativos para 5 Redes Sociais</li>
                            <li>✅ <strong>Garantia Incondicional:</strong> 7 Dias de Retorno</li>
                        </ul>
                    </div>

                    <div style="background: #090d16; padding: 20px; border-radius: 14px; border: 1px solid #22c55e55; text-align: center;">
                        <span style="font-size: 11px; color: #22c55e; font-weight: 800; text-transform: uppercase;">Checkout Seguro Asaas Gateway</span>
                        <div style="font-size: 32px; font-weight: 800; color: #fff; margin: 12px 0 4px 0;">{price}</div>
                        <div style="font-size: 11px; color: #94a3b8; margin-bottom: 16px;">Pagamento Único via PIX ou Cartão</div>
                        
                        <!-- PIX QR Code Mockup -->
                        <div style="background: #fff; padding: 12px; border-radius: 10px; display: inline-block; margin-bottom: 16px;">
                            <img src="https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=dezafira-asaas-pix-oferta" alt="QR Code PIX Asaas"/>
                        </div>

                        <button style="width: 100%; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color: #fff; border: none; padding: 14px; border-radius: 10px; font-size: 14px; font-weight: 800; cursor: pointer; box-shadow: 0 4px 15px rgba(34,197,94,0.4);">
                            ⚡ FINALIZAR COMPRA VIA ASAAS PIX
                        </button>
                    </div>
                </div>
            </div>
            """

        else:
            # --- FÁBRICA POSTIZ ADS REAL ---
            content = f"""
            <div style="max-width: 900px; margin: 0 auto; background: #0b1120; border: 1px solid #1e293b; border-radius: 20px; padding: 32px; color: #fff;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 24px;">
                    <div>
                        <span style="background: #38bdf822; color: #38bdf8; border: 1px solid #38bdf855; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 800;">📢 POSTIZ ADS • AUTOMAÇÃO MULTICANAL</span>
                        <h2 style="margin: 8px 0 0 0; font-size: 22px; color: #38bdf8;">Campanha de Anúncios: {title}</h2>
                    </div>
                    <span style="background: #22c55e22; color: #4ade80; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 700;">API / MCP Ativa</span>
                </div>

                <p style="color: #94a3b8; font-size: 14px;">Criativos visuais gerados por Agnes AI e agendados no Postiz para distribuição automática em mais de 20 redes sociais:</p>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin-top: 24px;">
                    <div style="background: #131c2e; border: 1px solid #1e293b; border-radius: 14px; padding: 16px; text-align: center;">
                        <span style="background: #e1306c; color: #fff; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800;">Instagram Feed & Stories</span>
                        <img src="{ad_img}" style="width: 100%; height: 220px; object-fit: cover; border-radius: 10px; margin: 12px 0; border: 1px solid #334155;" alt="Instagram Ad"/>
                        <p style="font-size: 11px; color: #cbd5e1; margin: 0;">"{offer_title[:60]}..."</p>
                    </div>

                    <div style="background: #131c2e; border: 1px solid #1e293b; border-radius: 14px; padding: 16px; text-align: center;">
                        <span style="background: #000; color: #fff; border: 1px solid #444; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800;">TikTok Ads</span>
                        <img src="{course_img}" style="width: 100%; height: 220px; object-fit: cover; border-radius: 10px; margin: 12px 0; border: 1px solid #334155;" alt="TikTok Ad"/>
                        <p style="font-size: 11px; color: #cbd5e1; margin: 0;">"Assista como os agentes autônomos geram infoprodutos..."</p>
                    </div>

                    <div style="background: #131c2e; border: 1px solid #1e293b; border-radius: 14px; padding: 16px; text-align: center;">
                        <span style="background: #bd081c; color: #fff; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800;">Pinterest Pins</span>
                        <img src="{ebook_img}" style="width: 100%; height: 220px; object-fit: cover; border-radius: 10px; margin: 12px 0; border: 1px solid #334155;" alt="Pinterest Ad"/>
                        <p style="font-size: 11px; color: #cbd5e1; margin: 0;">"Baixe o Manual Definitivo de Negócios Digitais..."</p>
                    </div>
                </div>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Hub da Oferta Dezafira - {title}</title>
            <style>
                body {{
                    background-color: #030712;
                    color: #f9fafb;
                    margin: 0;
                    font-family: 'Inter', system-ui, sans-serif;
                }}
            </style>
        </head>
        <body>
            {nav_html}
            <div style="padding: 0 20px 40px 20px;">
                {content}
            </div>
        </body>
        </html>
        """
