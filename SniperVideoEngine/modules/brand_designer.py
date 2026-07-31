import json
import re
import os
from modules.blog_writer import _call_llm

class BrandingDesignerAgent:
    """
    Agente 'Seu Design' — Especializado em design, branding e identidade visual de blogs.
    Gera paletas de cores, combinações tipográficas e logos/favicons SVG sob medida.
    """

    async def generate_branding(self, blog_name: str, niche: str, is_affiliate: bool = False) -> dict:
        print(f"[Seu Design] Planejando identidade visual para '{blog_name}' ({niche})...")
        
        system_prompt = (
            "Você é o 'Seu Design', um diretor de arte e UI/UX Designer sênior premiado internacionalmente. "
            "Sua especialidade é criar identidades visuais minimalistas, elegantes, modernas e de altíssimo impacto para marcas e blogs. "
            "Você sempre responde fornecendo APENAS um JSON válido contendo toda a especificação de design."
        )

        user_prompt = f"""
Crie a identidade visual e o branding completo para o blog abaixo:
Nome do Blog: "{blog_name}"
Nicho: "{niche}"
Modo de Monetização: {"Afiliados (CRO e Conversão)" if is_affiliate else "Normal (AdSense)"}

Você deve gerar um JSON estruturado contendo:
1. "colors": Objeto com cores hexadecimais harmoniosas adaptadas ao nicho (psicologia das cores):
   - "primary": Cor principal (Ex: #059669 para finanças, #3b82f6 para tecnologia, #d4a853 para fé). Deve ter alto contraste.
   - "primary_light": Versão mais clara da primária.
   - "primary_dark": Versão mais escura da primária.
   - "bg": Cor de fundo das páginas (Ex: #f8fafc ou #faf6ef).
   - "bg_dark": Cor de fundo de cartões/seções secundárias.
   - "dark": Cor primária do texto (quase preto/cinza muito escuro).
   - "dark2": Cor secundária do texto.
   - "text": Cor do texto do corpo.
   - "text_light": Cor de textos secundários.
   - "accent": Cor de destaque chamativa (Ex: laranja, vermelho ou roxo).
   - "border": Cor para bordas sutis.
2. "colors_dark": Objeto equivalente a "colors" para o tema Dark Mode automático do blog.
3. "fonts": Objeto contendo famílias tipográficas do Google Fonts ideais:
   - "heading": Ex: "'Playfair Display', serif" para temas clássicos, ou "'Plus Jakarta Sans', sans-serif" para modernos, ou "'Outfit', sans-serif".
   - "body": Ex: "'Inter', sans-serif" ou "'Lora', serif".
4. "logo_initial": A letra inicial estilizada para o logotipo.
5. "header_symbol": Um emoji ou caractere unicode decorativo adequado para a marca.
6. "logo_svg": O código XML de um logotipo SVG vetorial profissional, limpo e inline. Deve usar as cores primárias do blog, ter um viewBox="0 0 120 40", conter o símbolo geométrico estilizado na esquerda e o nome da marca na direita com uma tipografia vetorial em tags `<text>`. Deve ser extremamente limpo, moderno e bonito. Exemplo de estrutura:
   `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40" width="120" height="40"><rect width="120" height="40" rx="6" fill="#1e293b"/><circle cx="20" cy="20" r="10" fill="#3b82f6"/><text x="40" y="25" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="14">BlogName</text></svg>`
7. "favicon_svg": A URI data URI do favicon SVG (Ex: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E...%3C/svg%3E`).

Retorne APENAS o JSON válido sem blocos de código markdown ou texto explicativo extra.
"""
        
        try:
            raw_response = await _call_llm(system_prompt, user_prompt, temperature=0.6, max_tokens=2548)
            clean = raw_response.strip()
            if clean.startswith("```"):
                lines = clean.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean = "\n".join(lines).strip()
            
            data = json.loads(clean)
            print(f"[Seu Design] Identidade visual gerada com sucesso para '{blog_name}'!")
            return data
        except Exception as e:
            print(f"[Seu Design] Falha ao gerar branding dinamicamente: {e}. Usando fallback.")
            from modules.brand_themes import detect_theme
            theme = detect_theme(niche)
            return {
                "colors": theme["colors"],
                "colors_dark": theme.get("colors_dark", theme["colors"]),
                "fonts": theme["fonts"],
                "logo_initial": theme.get("logo_initial", blog_name[0] if blog_name else "B"),
                "header_symbol": theme.get("header_symbol", "💡"),
                "logo_svg": f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40" width="120" height="40">
                    <rect width="120" height="40" rx="8" fill="{theme['colors']['primary']}"/>
                    <text x="20" y="25" fill="#ffffff" font-family="sans-serif" font-weight="bold" font-size="16">{blog_name[:10]}</text>
                </svg>""",
                "favicon_svg": f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23{theme['colors']['primary'].replace('#', '')}'/%3E%3Ctext x='16' y='23' font-size='18' text-anchor='middle' fill='%23fff'%3E{blog_name[0] if blog_name else 'B'}%3C/text%3E%3C/svg%3E"
            }
