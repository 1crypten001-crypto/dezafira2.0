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
4. "logo_initial": As duas primeiras letras iniciais estilizadas para o monograma do logo (Ex: "FI" para Fenômenos Inexplicáveis).
5. "header_symbol": Um emoji ou caractere unicode decorativo adequado para a marca.
6. "logo_svg": O código XML de um logotipo SVG vetorial profissional, ultra limpo e inline. Deve usar as cores do blog, ter viewBox="0 0 180 40". Na esquerda (X=0 a 40), deve projetar um monograma ou símbolo geométrico luxuoso combinando/entrelaçando as duas letras iniciais ("logo_initial"). Use tags `<linearGradient>`, `<rect>`, `<circle>`, `<path>` com efeitos elegantes (glow sutil, opacidades). Na direita (X=48 em diante), posicione o nome completo da marca em uma tag `<text>` elegante, alinhado perfeitamente com a tipografia do tema. Evite logos genéricos simples.
7. "favicon_svg": A URI data URI do favicon SVG usando o mesmo monograma de duas letras centralizado de forma harmônica (Ex: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E...%3C/svg%3E`).

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
            print(f"[Seu Design] Falha ao gerar branding dinamicamente: {e}. Usando fallback premium.")
            import hashlib
            
            palettes = [
                # Teal / Mint (Emerald Luxury)
                {
                    "primary": "#0d9488", "primary_light": "#99f6e4", "primary_dark": "#115e59",
                    "bg": "#f0fdfa", "bg_dark": "#ccfbf1", "dark": "#0f172a", "dark2": "#1e293b",
                    "text": "#1e293b", "text_light": "#64748b", "accent": "#f59e0b", "border": "#e2e8f0"
                },
                # Navy / Blue (Classic Navy)
                {
                    "primary": "#1e40af", "primary_light": "#bfdbfe", "primary_dark": "#1e3a8a",
                    "bg": "#f8fafc", "bg_dark": "#f1f5f9", "dark": "#0f172a", "dark2": "#1e293b",
                    "text": "#334155", "text_light": "#64748b", "accent": "#ea580c", "border": "#cbd5e1"
                },
                # Deep Violet (Royal Violet)
                {
                    "primary": "#6d28d9", "primary_light": "#ddd6fe", "primary_dark": "#5b21b6",
                    "bg": "#faf5ff", "bg_dark": "#f3e8ff", "dark": "#0f172a", "dark2": "#1e293b",
                    "text": "#334155", "text_light": "#64748b", "accent": "#db2777", "border": "#e9d5ff"
                },
                # Warm Terracotta
                {
                    "primary": "#ca8a04", "primary_light": "#fef9c3", "primary_dark": "#854d0e",
                    "bg": "#fefdf0", "bg_dark": "#fef9c3", "dark": "#1c1917", "dark2": "#292524",
                    "text": "#3d3227", "text_light": "#78716c", "accent": "#e11d48", "border": "#fef08a"
                },
                # Slate Rose
                {
                    "primary": "#be185d", "primary_light": "#fbcfe8", "primary_dark": "#9d174d",
                    "bg": "#fff1f2", "bg_dark": "#ffe4e6", "dark": "#0f172a", "dark2": "#1e293b",
                    "text": "#334155", "text_light": "#64748b", "accent": "#0d9488", "border": "#fecdd3"
                }
            ]
            
            # Escolhe paleta baseado no hash do nome do blog para garantir unicidade
            hash_val = int(hashlib.md5(blog_name.encode('utf-8')).hexdigest(), 16)
            palette = palettes[hash_val % len(palettes)]
            
            # Escolhe fonte baseado no nicho
            fonts = {
                "heading": "'Plus Jakarta Sans', sans-serif",
                "body": "'Inter', sans-serif"
            }
            if any(k in niche.lower() for k in ["jesus", "crista", "deus", "fe", "igreja", "historia"]):
                fonts = {
                    "heading": "'Lora', serif",
                    "body": "'Inter', sans-serif"
                }
            
            # Gera iniciais robustas (ex: "Fenômenos Inexplicáveis" -> "FI")
            words = [w for w in blog_name.split() if w]
            if len(words) >= 2:
                initials = (words[0][0] + words[1][0]).upper()
            elif len(words) == 1 and len(words[0]) >= 2:
                initials = words[0][:2].upper()
            else:
                initials = (blog_name[:2] if blog_name else "DE").upper()

            logo_color = palette["primary"]
            logo_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 40" width="180" height="40">
                <g transform="translate(5, 5)">
                    <rect x="0" y="2" width="28" height="28" rx="8" fill="{logo_color}" opacity="0.15"/>
                    <rect x="0" y="2" width="28" height="28" rx="8" fill="none" stroke="{logo_color}" stroke-width="1.5"/>
                    <text x="14" y="20" fill="{logo_color}" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="11" text-anchor="middle">{initials}</text>
                </g>
                <text x="44" y="24" fill="#ffffff" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="15" letter-spacing="-0.3px">{blog_name}</text>
            </svg>"""
            
            favicon_svg = f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23{logo_color.replace('#', '')}'/%3E%3Ctext x='16' y='20' fill='%23fff' font-family='sans-serif' font-weight='bold' font-size='12' text-anchor='middle'%3E{initials}%3C/text%3E%3C/svg%3E"
            
            return {
                "colors": palette,
                "colors_dark": {
                    "bg": "#080c14",
                    "bg_dark": "#0f172a",
                    "dark": "#f8fafc",
                    "dark2": "#e2e8f0",
                    "text": "#cbd5e1",
                    "text_light": "#64748b",
                    "border": "#1e293b",
                    "primary": palette["primary"],
                    "primary_light": palette["primary_light"],
                    "primary_dark": palette["primary_dark"],
                    "accent": palette["accent"],
                },
                "fonts": fonts,
                "logo_initial": initials,
                "header_symbol": "✨",
                "logo_svg": logo_svg,
                "favicon_svg": favicon_svg
            }
