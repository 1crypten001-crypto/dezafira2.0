"""
=============================================================================
DEZAFIRA — BioSiteFactory (Sala de Agentes "Seu Link" + "Seu Design")
=============================================================================
Gera Bio Sites responsivos mobile-first baseados nos templates Impeccable.style
e integrados com controle manual de cores, pixels e recorrência do Asaas.
"""

import json
import uuid
import re
from typing import Dict, Any, List, Optional
from agents.llm import query_llm, ERROR_PREFIX
from modules.database import create_db_bio_site, add_db_bio_link, get_db_bio_site_by_slug

class BioSiteFactory:
    def __init__(self):
        pass

    async def generate_bio_site_spec(self, name: str, niche: str) -> Dict[str, Any]:
        """
        Consulta a IA (Seu Link + Seu Design) para gerar o conteúdo e o visual sugerido para o Bio Site.
        """
        system_prompt = (
            "Você é a união dos agentes 'Seu Link' (estrategista de marketing mobile e copywriter) "
            "e 'Seu Design' (UI/UX designer especialista em páginas de links). "
            "Sua missão é planejar o visual inicial, a descrição persuasiva e os botões estratégicos de conversão para o Bio Site do cliente.\n"
            "Responda APENAS com um objeto JSON válido, sem formatação markdown ou blocos de código."
        )

        user_prompt = f"""
        Nome Comercial do Cliente: "{name}"
        Nicho de Atuação: "{nicho}"

        Gere a estrutura inicial para o Bio Site do cliente contendo:
        1. "name": O nome estilizado do negócio (2 a 4 palavras).
        2. "description": Uma biografia/descrição curta e altamente persuasiva para o cabeçalho (máximo de 150 caracteres).
        3. "theme_config": Configurações de design sugeridas:
           - "template": Escolha um entre: "midnight_aura", "minimalist_glass", "neo_brutalist"
           - "primary_color": Cor primária HSL sugerida (Ex: "262, 80%, 50%" para roxo, "142, 70%, 45%" para verde).
           - "accent_color": Cor de destaque HSL contrastante (Ex: "35, 92%, 50%").
           - "bg_color": Cor de fundo HSL do tema (Midnight usa fundo escuro "222, 47%, 11%"; Glass usa "0, 0%, 98%" ou "220, 15%, 15%"; Brutalist usa amarelo/verde "45, 100%, 75%").
           - "text_color": Cor principal do texto em HSL (Ex: "0, 0%, 100%" ou "220, 10%, 10%").
           - "font_family": Fonte do Google Fonts (Ex: "Space Grotesk", "Outfit", "Inter", "Sora", "Plus Jakarta Sans").
        4. "links": Um array contendo de 3 a 4 botões essenciais sugeridos para este nicho. Para cada botão:
           - "title": O texto persuasivo do botão (Ex: "Agende seu horário no WhatsApp 💬", "Conheça nossos Serviços 🚀", "Ver Localização no Maps 📍").
           - "url": Uma URL fictícia ou de sugestão condizente (Ex: "https://wa.me/5599999999999", "https://maps.google.com").
           - "icon": Um emoji ou caractere unicode decorativo adequado.
           - "animation": Um efeito de movimento para destacar o botão (Ex: "pulse", "shake", "bounce", "none").

        Exemplo de formato de resposta esperado:
        {{
          "name": "Unhas de Rainha",
          "description": "Cuidando do seu bem-estar com alongamento de unhas de alta qualidade e carinho. Agende seu atendimento!",
          "theme_config": {{
            "template": "midnight_aura",
            "primary_color": "322, 81%, 43%",
            "accent_color": "35, 92%, 50%",
            "bg_color": "320, 40%, 8%",
            "text_color": "0, 0%, 100%",
            "font_family": "Outfit"
          }},
          "links": [
            {{"title": "Agendar no WhatsApp", "url": "https://wa.me/5511999999999", "icon": "💬", "animation": "pulse"}},
            {{"title": "Ver Fotos de Trabalhos", "url": "https://instagram.com", "icon": "📸", "animation": "none"}}
          ]
        }}
        """

        try:
            raw_response = await query_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2048,
                temperature=0.6
            )
            clean_json = raw_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            return json.loads(clean_json)
        except Exception as e:
            print(f"[BioSiteFactory] Erro ao consultar LLM: {e}. Usando fallback.")
            return self._get_fallback_spec(name, niche)

    def _get_fallback_spec(self, name: str, niche: str) -> Dict[str, Any]:
        """Retorna uma estrutura básica segura caso a IA falhe."""
        return {
            "name": name,
            "description": f"Bem-vindo à página de links oficiais. Conecte-se conosco no nicho de {niche}.",
            "theme_config": {
                "template": "minimalist_glass",
                "primary_color": "220, 80%, 50%",
                "accent_color": "35, 90%, 50%",
                "bg_color": "220, 15%, 15%",
                "text_color": "0, 0%, 100%",
                "font_family": "Inter"
            },
          "links": [
            {"title": "Falar Conosco no WhatsApp", "url": "https://wa.me/5599999999999", "icon": "💬", "animation": "pulse"},
            {"title": "Acessar nosso Site", "url": "https://www.dezafira.com.br", "icon": "🌐", "animation": "none"}
          ]
        }

    async def create_bio_site_pipeline(self, name: str, niche: str, user_id: str = None) -> Dict[str, Any]:
        """
        Orquestra a geração completa do Bio Site por IA e o persiste no banco de dados com seus links.
        """
        # 1. Obter especificação via IA
        spec = await self.generate_bio_site_spec(name, niche)

        # 2. Gerar slug único
        base_slug = re.sub(r'[^a-z0-9-]', '', spec["name"].lower().replace(' ', '-')) or "bio"
        slug = base_slug
        suffix = 2
        while True:
            existing = get_db_bio_site_by_slug(slug)
            if not existing:
                break
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        # 3. Persistir Bio Site
        theme_json = json.dumps(spec["theme_config"])
        bio_site = create_db_bio_site(
            name=spec["name"],
            niche=niche,
            slug=slug,
            user_id=user_id,
            description=spec["description"],
            theme_config=theme_json,
            status="active"
        )

        # 4. Adicionar links no banco
        for i, link in enumerate(spec.get("links", [])):
            add_db_bio_link(
                bio_site_id=bio_site["id"],
                title=link["title"],
                url=link["url"],
                icon=link.get("icon", ""),
                animation=link.get("animation", "none"),
                position=i
            )

        return {"success": True, "bio_id": bio_site["id"], "slug": slug}

    def render_bio_site_html(self, site: Dict[str, Any], preview_mode: bool = False) -> str:
        """
        Renderiza o HTML do Bio Site aplicando o template e cores.
        Garante a injeção de Pixels e a tela de bloqueio do Asaas.
        """
        # Parsing das configurações do tema
        theme_config = {}
        if site.get("theme_config"):
            try:
                theme_config = json.loads(site["theme_config"]) if isinstance(site["theme_config"], str) else site["theme_config"]
            except Exception:
                pass

        template = theme_config.get("template", "minimalist_glass")
        font_family = theme_config.get("font_family", "Inter")
        
        # Cores HSL seguras
        c_primary = theme_config.get("primary_color", "220, 80%, 50%")
        c_accent = theme_config.get("accent_color", "35, 90%, 50%")
        c_bg = theme_config.get("bg_color", "222, 47%, 11%")
        c_text = theme_config.get("text_color", "0, 0%, 100%")

        # Verifica suspensão da assinatura no Asaas
        is_suspended = site.get("subscription_status") == "unpaid" and not preview_mode

        # Scripts de Rastreamento (Pixels)
        pixel_fb_id = site.get("pixel_facebook", "")
        pixel_ga_id = site.get("google_analytics", "")

        pixel_html = ""
        if pixel_fb_id and not preview_mode:
            pixel_html += f"""
            <!-- Facebook Pixel Code -->
            <script>
            !function(f,b,e,v,n,t,s)
            {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)}}(window, document,'script',
            'https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', '{pixel_fb_id}');
            fbq('track', 'PageView');
            </script>
            <noscript><img height="1" width="1" style="display:none"
            src="https://www.facebook.com/tr?id={pixel_fb_id}&ev=PageView&noscript=1"
            /></noscript>
            <!-- End Facebook Pixel Code -->
            """

        if pixel_ga_id and not preview_mode:
            pixel_html += f"""
            <!-- Global site tag (gtag.js) - Google Analytics -->
            <script async src="https://www.googletagmanager.com/gtag/js?id={pixel_ga_id}"></script>
            <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){{dataLayer.push(arguments);}}
              gtag('js', new Date());
              gtag('config', '{pixel_ga_id}');
            </script>
            """

        # Gerar os botões de link
        links_html = ""
        for link in site.get("links", []):
            anim_class = f"anim-{link.get('animation', 'none')}" if link.get('animation') != 'none' else ""
            icon_span = f'<span class="link-icon">{link.get("icon")}</span>' if link.get("icon") else ""
            
            # Adiciona track de Pixel no clique
            onclick_handler = ""
            if pixel_fb_id and not preview_mode:
                onclick_handler = f"onclick=\"fbq('track', 'Lead', {{content_name: '{link.get('title')}'}});\""

            links_html += f"""
            <a href="{link.get('url')}" target="_blank" rel="noopener noreferrer" class="link-btn {anim_class}" {onclick_handler}>
                {icon_span}
                <span class="link-title">{link.get('title')}</span>
                <span class="link-arrow">→</span>
            </a>
            """

        # Carregar foto de perfil ou gerar avatar com letras iniciais
        profile_img = ""
        name = site.get("name", "Bio Site")
        if site.get("profile_image_url"):
            profile_img = f'<img src="{site.get("profile_image_url")}" class="profile-pic" alt="{name}">'
        else:
            initials = "".join([w[0].upper() for w in name.split() if w][:2])
            profile_img = f'<div class="profile-initials">{initials}</div>'

        # Suspended Screen HTML Overlay
        suspended_overlay = ""
        if is_suspended:
            suspended_overlay = f"""
            <div class="suspended-overlay">
                <div class="suspended-box">
                    <div class="suspended-icon">⚠️</div>
                    <h2>Página Temporariamente Suspensa</h2>
                    <p>O Bio Site do estabelecimento <strong>{name}</strong> está aguardando renovação da assinatura mensal.</p>
                    <p class="small">Se você é o proprietário, realize o pagamento no seu painel ou contate o administrador para reativar seu acesso.</p>
                </div>
            </div>
            """

        # Template-specific CSS classes
        body_class = f"tpl-{template}"

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <meta name="description" content="{site.get('description', '')}">
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family={font_family.replace(' ', '+')}:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    
    {pixel_html}

    <style>
        :root {{
            --primary: hsl({c_primary});
            --accent: hsl({c_accent});
            --bg: hsl({c_bg});
            --text: hsl({c_text});
            --font: '{font_family}', sans-serif;
            
            /* Derivações HSL seguras */
            --primary-light: hsl({c_primary.split(',')[0]}, {c_primary.split(',')[1].replace('%','') or 80}%, 60%);
            --bg-card: hsla({c_bg.split(',')[0]}, {c_bg.split(',')[1].replace('%','') or 40}%, 18%, 0.6);
            --bg-card-hover: hsla({c_bg.split(',')[0]}, {c_bg.split(',')[1].replace('%','') or 40}%, 22%, 0.85);
            --border-color: hsla({c_text.split(',')[0]}, {c_text.split(',')[1].replace('%','') or 10}%, 50%, 0.15);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg);
            color: var(--text);
            font-family: var(--font);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            padding: 40px 20px;
            overflow-x: hidden;
        }}

        .container {{
            width: 100%;
            max-width: 480px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }}

        /* --- Header Section --- */
        .header {{
            margin-bottom: 30px;
            width: 100%;
        }}

        .profile-pic {{
            width: 96px;
            height: 96px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid var(--primary);
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            margin-bottom: 16px;
        }}

        .profile-initials {{
            width: 96px;
            height: 96px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            color: #fff;
            font-size: 32px;
            font-weight: 800;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0 auto 16px auto;
            border: 3px solid rgba(255,255,255,0.1);
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }}

        h1 {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}

        .bio {{
            font-size: 14px;
            opacity: 0.85;
            line-height: 1.5;
            max-width: 360px;
            margin: 0 auto;
        }}

        /* --- Links Section --- */
        .links-wrapper {{
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .link-btn {{
            width: 100%;
            display: flex;
            align-items: center;
            padding: 16px 20px;
            text-decoration: none;
            color: var(--text);
            border-radius: 12px;
            font-weight: 600;
            font-size: 15px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid var(--border-color);
            position: relative;
        }}

        .link-icon {{
            margin-right: 14px;
            font-size: 20px;
            display: flex;
            align-items: center;
        }}

        .link-title {{
            flex-grow: 1;
            text-align: left;
        }}

        .link-arrow {{
            opacity: 0.6;
            transition: transform 0.2s ease;
        }}

        .link-btn:hover .link-arrow {{
            transform: translateX(4px);
            opacity: 1;
        }}

        /* --- TEMPLATE 1: Midnight Aura --- */
        .tpl-midnight_aura .link-btn {{
            background-color: var(--bg-card);
            backdrop-filter: blur(10px);
        }}

        .tpl-midnight_aura .link-btn:hover {{
            background-color: var(--bg-card-hover);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(var(--primary), 0.15);
            border-color: var(--primary);
        }}

        /* --- TEMPLATE 2: Minimalist Glass --- */
        .tpl-minimalist_glass .link-btn {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }}

        .tpl-minimalist_glass .link-btn:hover {{
            background: rgba(255, 255, 255, 0.12);
            transform: scale(1.015);
        }}

        /* --- TEMPLATE 3: Neo-Brutalist --- */
        .tpl-neo_brutalist body {{
            padding: 40px 10px;
        }}

        .tpl-neo_brutalist .profile-pic,
        .tpl-neo_brutalist .profile-initials {{
            border: 3px solid #000;
            box-shadow: 4px 4px 0 #000;
            border-radius: 20px;
        }}

        .tpl-neo_brutalist .link-btn {{
            background-color: #fff;
            color: #000 !important;
            border: 3px solid #000;
            box-shadow: 4px 4px 0 #000;
            border-radius: 4px;
        }}

        .tpl-neo_brutalist .link-btn:hover {{
            transform: translate(-2px, -2px);
            box-shadow: 6px 6px 0 #000;
            background-color: var(--primary);
            color: #fff !important;
        }}

        .tpl-neo_brutalist .link-btn:active {{
            transform: translate(2px, 2px);
            box-shadow: 2px 2px 0 #000;
        }}

        /* --- Animations --- */
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.025); box-shadow: 0 0 15px var(--primary); }}
            100% {{ transform: scale(1); }}
        }}
        .anim-pulse {{
            animation: pulse 2s infinite ease-in-out;
        }}

        @keyframes shake {{
            0%, 100% {{ transform: translateX(0); }}
            10%, 30%, 50%, 70%, 90% {{ transform: translateX(-4px); }}
            20%, 40%, 60%, 80% {{ transform: translateX(4px); }}
        }}
        .anim-shake {{
            animation: shake 1.5s infinite ease-in-out;
        }}

        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-6px); }}
        }}
        .anim-bounce {{
            animation: bounce 1.8s infinite ease-in-out;
        }}

        /* --- Suspended Screen Overlay --- */
        .suspended-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(8px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            padding: 20px;
        }}

        .suspended-box {{
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 30px;
            max-width: 400px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            color: #f8fafc;
        }}

        .suspended-icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}

        .suspended-box h2 {{
            font-size: 20px;
            margin-bottom: 12px;
            font-weight: 700;
        }}

        .suspended-box p {{
            font-size: 14px;
            line-height: 1.6;
            color: #cbd5e1;
            margin-bottom: 16px;
        }}

        .suspended-box p.small {{
            font-size: 12px;
            color: #64748b;
        }}

        /* Footer Branding */
        .footer {{
            margin-top: 50px;
            font-size: 12px;
            opacity: 0.5;
            letter-spacing: 0.5px;
        }}
    </style>
</head>
<body class="{body_class}">
    
    {suspended_overlay}

    <div class="container">
        
        <div class="header">
            {profile_img}
            <h1>{name}</h1>
            <p class="bio">{site.get('description', '')}</p>
        </div>

        <div class="links-wrapper">
            {links_html}
        </div>

        <div class="footer">
            Criado com Dezafira Club
        </div>

    </div>

</body>
</html>
"""
        return html

# Singleton instance
biosite_factory = BioSiteFactory()
