import os
import io
import base64
import uuid
import asyncio
from PIL import Image, ImageDraw, ImageFont

DEFAULT_OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "agnes")
DEFAULT_STYLE = "moderno"

STYLES = {
    "moderno": {
        "colors": {"bg": "#0f0f11", "bg2": "#1a1a24", "accent": "#ff6b00", "text": "#ffffff", "muted": "#8a8a93"},
        "font": "Space Grotesque",
        "font_sans": "Space Grotesque",
        "layout": "default",
    },
    "elegante": {
        "colors": {"bg": "#121212", "bg2": "#1e1e1e", "accent": "#d4af37", "text": "#ffffff", "muted": "#a0a0a0"},
        "font": "Playfair Display",
        "font_sans": "Plus Jakarta Sans",
        "layout": "serif-classic",
    },
    "tech": {
        "colors": {"bg": "#030712", "bg2": "#111827", "accent": "#00ffcc", "text": "#ffffff", "muted": "#6b7280"},
        "font": "Share Tech Mono",
        "font_sans": "Rajdhani",
        "layout": "terminal",
    },
    "minimal": {
        "colors": {"bg": "#ffffff", "bg2": "#f3f4f6", "accent": "#111827", "text": "#111827", "muted": "#4b5563"},
        "font": "Inter",
        "font_sans": "Inter",
        "layout": "clean-white",
    },
    "dark-gold": {
        "colors": {"bg": "#09090b", "bg2": "#18181b", "accent": "#facc15", "text": "#fafafa", "muted": "#71717a"},
        "font": "Cinzel",
        "font_sans": "Montserrat",
        "layout": "luxury",
    }
}

def _esc(text) -> str:
    """Escapa HTML básico para segurança."""
    return str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

class AgnesStudio:
    def __init__(self, outputs_dir: str = None):
        self.outputs_dir = outputs_dir or DEFAULT_OUTPUTS_DIR

    # ─── Design Brief Generator ─────────────────────────────────────────

    def _make_design(self, style_id: str, niche: str = "", brand_kit: dict = None) -> dict:
        """Monta o brief de design de forma DETERMINÍSTICA (por style_id)."""
        from modules.art_director import ArtDirector, VIBES

        vibe_id = (brand_kit or {}).get("vibe_id") or style_id
        if vibe_id in VIBES:
            director = ArtDirector()
            base_design = director.generate_brand_kit(vibe_id, niche)
            design = {
                "style_id": vibe_id,
                "colors": dict(base_design["colors"]),
                "font": base_design["font"],
                "font_sans": base_design["font_sans"],
                "layout": base_design["layout"],
                "elements": ["badge", "author", "credits", "watermark"],
            }
        else:
            style_id = style_id if style_id in STYLES else DEFAULT_STYLE
            style = STYLES[style_id]
            design = {
                "style_id": style_id,
                "colors": dict(style["colors"]),
                "font": style["font"],
                "font_sans": style["font_sans"],
                "layout": style["layout"],
                "elements": ["badge", "author", "credits", "watermark"],
            }
        
        if isinstance(brand_kit, dict):
            kit_colors = brand_kit.get("colors")
            if not isinstance(kit_colors, dict):
                kit_colors = {
                    "bg": brand_kit.get("accent_color") or brand_kit.get("primary_color"),
                    "bg2": brand_kit.get("accent_color"),
                    "accent": brand_kit.get("primary_color"),
                    "text": brand_kit.get("text_color"),
                    "muted": brand_kit.get("muted_color"),
                }
            if isinstance(kit_colors, dict):
                for key in ("bg", "bg2", "accent", "text", "muted"):
                    val = str(kit_colors.get(key) or "").strip()
                    if val.startswith("#") and len(val) in (4, 7):
                        design["colors"][key] = val
            for key in ("font", "font_sans"):
                val = str(brand_kit.get(key) or "").strip()
                if val:
                    design[key] = val
        return design

    def _google_fonts_links(self, design: dict) -> str:
        """Retorna os links de fontes Google Fonts a partir do design brief."""
        fonts_to_load = []
        for key in ("font", "font_sans"):
            f_name = design.get(key)
            if f_name and f_name not in ("SF Pro", "Arial", "Helvetica", "Georgia", "Times New Roman", "Courier New"):
                fonts_to_load.append(f_name.replace(" ", "+"))
        if not fonts_to_load:
            return ""
        family_queries = "&".join(f"family={f}:wght@300;400;700;900" for f in set(fonts_to_load))
        return f"""<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?{family_queries}&display=swap" rel="stylesheet">"""

    # ─── HTML Templates ─────────────────────────────────────────────────

    def _html_course(self, design: dict, title: str, subtitle: str = "",
                     niche: str = "", difficulty: str = "", modules_count: int = 0,
                     author: str = "Dezafira Studio", mode: str = "full") -> str:
        c = design["colors"]
        wm = _esc((niche or "Dezafira")[:1].upper() or "D")
        chips = f'<div class="chip">🎓 {int(modules_count or 0)} módulos</div>' \
                f'<div class="chip">✍ {_esc(author)}</div>'
        sub = f'<div class="subtitle">{_esc(subtitle)}</div>' if subtitle else ""
        
        if mode == "text":
            bg_style = "background: transparent;"
        elif design.get("bg_image"):
            bg_style = f"background-image: url({design['bg_image']}); background-size: cover; background-position: center;"
        else:
            bg_style = f"background:radial-gradient(1200px 600px at 85% -10%,{c['accent']}33,transparent 60%), linear-gradient(135deg,{c['bg']} 0%,{c['bg2']} 100%)"

        fonts_meta = self._google_fonts_links(design)

        style = f"""*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;font-family:{design["font_sans"]}}}
.cover{{width:100%;height:100%;position:relative;color:{c["text"]}; {bg_style}}}
.deco{{position:absolute;inset:0;opacity:.12;
  background-image:radial-gradient({c["accent"]} 1.5px,transparent 1.5px);background-size:34px 34px}}
.bar{{position:absolute;top:0;left:0;right:0;height:6px;background:{c["accent"]}}}
.wm{{position:absolute;right:-40px;bottom:-80px;font-family:{design["font"]};
  font-size:360px;font-weight:900;color:{c["text"]};opacity:.05;line-height:1}}
.top{{position:absolute;top:34px;left:56px;right:56px;display:flex;justify-content:space-between;align-items:center}}
.brand{{font-family:{design["font"]};letter-spacing:4px;font-size:15px;color:{c["muted"]};text-transform:uppercase}}
.brand b{{color:{c["accent"]}}}
.badge{{border:1px solid {c["accent"]}55;color:{c["accent"]};padding:6px 14px;border-radius:999px;
  font-size:13px;letter-spacing:1px;text-transform:uppercase}}
.main{{position:absolute;top:150px;left:56px;right:56px}}
.kicker{{font-size:14px;letter-spacing:3px;text-transform:uppercase;color:{c["accent"]};margin-bottom:16px}}
.title{{font-family:{design["font"]};font-size:64px;line-height:1.08;font-weight:700;max-width:1000px;text-shadow:0 4px 16px rgba(0,0,0,0.65)}}
.subtitle{{font-size:20px;color:{c["muted"]};margin-top:18px;max-width:860px;line-height:1.45;text-shadow:0 2px 8px rgba(0,0,0,0.55)}}
.chips{{position:absolute;bottom:96px;left:56px;display:flex;gap:12px}}
.chip{{border:1px solid {c["text"]}22;background:{c["text"]}0d;padding:8px 16px;border-radius:999px;
  font-size:14px;color:{c["text"]}cc}}
.foot{{position:absolute;bottom:32px;left:56px;right:56px;display:flex;justify-content:space-between;
  align-items:center;color:{c["muted"]};font-size:13px;letter-spacing:2px;text-transform:uppercase}}"""

        if mode == "bg":
            content_html = f'<div class="cover"><div class="bar"></div><div class="wm">{wm}</div></div>'
        elif mode == "text":
            content_html = f"""<div class="cover">
<div class="top"><div class="brand">DEZAFIRA <b>STUDIO</b></div>
<div class="badge">{_esc(niche or "Dezafira")}</div></div>
<div class="main"><div class="kicker">Curso · {_esc(difficulty or "Online")}</div>
<div class="title">{_esc(title)}</div>{sub}</div>
<div class="chips">{chips}</div>
<div class="foot"><span>Dezafira Studio</span><span>dezafira.com.br</span></div>
</div>"""
        else:
            content_html = f"""<div class="cover">
<div class="bar"></div><div class="deco"></div><div class="wm">{wm}</div>
<div class="top"><div class="brand">DEZAFIRA <b>STUDIO</b></div>
<div class="badge">{_esc(niche or "Dezafira")}</div></div>
<div class="main"><div class="kicker">Curso · {_esc(difficulty or "Online")}</div>
<div class="title">{_esc(title)}</div>{sub}</div>
<div class="chips">{chips}</div>
<div class="foot"><span>Dezafira Studio</span><span>dezafira.com.br</span></div>
</div>"""

        return f"<!doctype html><html><head><meta charset='utf-8'>{fonts_meta}<style>{style}</style></head><body>{content_html}</body></html>"

    def _html_blog(self, design: dict, title: str, subtitle: str = "",
                   niche: str = "", blog_name: str = "") -> str:
        c = design["colors"]
        wm = _esc((niche or "Dezafira")[:1].upper() or "D")
        sub = f'<div class="subtitle">{_esc(subtitle)}</div>' if subtitle else ""
        fonts_meta = self._google_fonts_links(design)
        return f"""<!doctype html><html><head><meta charset="utf-8">{fonts_meta}<style>
*{margin:0;padding:0;box-sizing:border-box}
body{{width:1200px;height:630px;overflow:hidden;font-family:{design["font_sans"]}}}
.cover{{width:100%;height:100%;position:relative;color:{c["text"]};
  background:radial-gradient(900px 500px at 90% -20%,{c["accent"]}2e,transparent 60%),
  linear-gradient(120deg,{c["bg"]} 0%,{c["bg2"]} 100%)}}
.edge{{position:absolute;top:0;left:0;bottom:0;width:14px;background:{c["accent"]}}}
.deco{{position:absolute;inset:0;opacity:.10;
  background-image:radial-gradient({c["accent"]} 1.5px,transparent 1.5px);background-size:30px 30px}}
.wm{{position:absolute;right:-30px;bottom:-70px;font-family:{design["font"]};
  font-size:300px;font-weight:900;color:{c["text"]};opacity:.05;line-height:1}}
.top{{position:absolute;top:36px;left:64px;right:64px;display:flex;justify-content:space-between;align-items:center}}
.blog{{font-family:{design["font"]};letter-spacing:3px;font-size:14px;color:{c["muted"]};text-transform:uppercase}}
.blog b{{color:{c["accent"]}}}
.badge{{border:1px solid {c["accent"]}55;color:{c["accent"]};padding:5px 12px;border-radius:999px;
  font-size:12px;letter-spacing:1px;text-transform:uppercase}}
.main{{position:absolute;top:170px;left:64px;right:64px}}
.kicker{{font-size:13px;letter-spacing:3px;text-transform:uppercase;color:{c["accent"]};margin-bottom:14px}}
.title{{font-family:{design["font"]};font-size:52px;line-height:1.12;font-weight:700;max-width:980px;text-shadow:0 4px 16px rgba(0,0,0,0.65)}}
.subtitle{{font-size:19px;color:{c["muted"]};margin-top:16px;max-width:860px;line-height:1.45;text-shadow:0 2px 8px rgba(0,0,0,0.55)}}
.foot{{position:absolute;bottom:30px;left:64px;right:64px;display:flex;justify-content:space-between;
  align-items:center;color:{c["muted"]};font-size:12px;letter-spacing:2px;text-transform:uppercase}}
</style></head><body><div class="cover">
<div class="edge"></div><div class="deco"></div><div class="wm">{wm}</div>
<div class="top"><div class="brand">{_esc(blog_name or "Blog Dezafira")} <b>· DEZAFIRA</b></div>
<div class="badge">{_esc(niche or "Blog")}</div></div>
<div class="main"><div class="kicker">Artigo · Dezafira</div>
<div class="title">{_esc(title)}</div>{sub}</div>
<div class="foot"><span>Dezafira Studio</span><span>dezafira.com.br</span></div>
</div></body></html>"""

    def _html_product(self, design: dict, title: str, subtitle: str = "",
                      niche: str = "", mode: str = "full") -> str:
        c = design["colors"]
        wm = _esc((niche or "Dezafira")[:1].upper() or "D")
        sub = f'<div class="subtitle">{_esc(subtitle)}</div>' if subtitle else ""
        
        if mode == "text":
            bg_style = "background: transparent;"
        elif design.get("bg_image"):
            bg_style = f"background-image: url({design['bg_image']}); background-size: cover; background-position: center;"
        else:
            bg_style = f"background:radial-gradient(900px 600px at 85% -10%,{c['accent']}30,transparent 55%), linear-gradient(135deg,{c['bg']} 0%,{c['bg2']} 100%)"

        fonts_meta = self._google_fonts_links(design)

        style = f"""*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1024px;height:1024px;overflow:hidden;font-family:{design["font_sans"]}}}
.cover{{width:100%;height:100%;position:relative;color:{c["text"]}; {bg_style}}}
.frame{{position:absolute;inset:30px;border:1px solid {c["accent"]}44;pointer-events:none}}
.deco{{position:absolute;inset:0;opacity:.10;
  background-image:radial-gradient({c["accent"]} 1.5px,transparent 1.5px);background-size:34px 34px}}
.wm{{position:absolute;right:-40px;bottom:-80px;font-family:{design["font"]};
  font-size:360px;font-weight:900;color:{c["text"]};opacity:.05;line-height:1}}
.top{{position:absolute;top:42px;left:56px;right:56px;display:flex;justify-content:space-between;align-items:center}}
.brand{{font-family:{design["font"]};letter-spacing:4px;font-size:15px;color:{c["muted"]};text-transform:uppercase}}
.brand b{{color:{c["accent"]}}}
.badge{{border:1px solid {c["accent"]}55;color:{c["accent"]};padding:6px 14px;border-radius:999px;
  font-size:13px;letter-spacing:1px;text-transform:uppercase}}
.main{{position:absolute;top:300px;left:56px;right:56px}}
.kicker{{font-size:14px;letter-spacing:3px;text-transform:uppercase;color:{c["accent"]};margin-bottom:16px}}
.title{{font-family:{design["font"]};font-size:58px;line-height:1.1;font-weight:700;text-shadow:0 4px 16px rgba(0,0,0,0.65)}}
.subtitle{{font-size:19px;color:{c["muted"]};margin-top:18px;line-height:1.5;text-shadow:0 2px 8px rgba(0,0,0,0.55)}}
.foot{{position:absolute;bottom:40px;left:56px;right:56px;display:flex;justify-content:space-between;
  align-items:center;color:{c["muted"]};font-size:13px;letter-spacing:2px;text-transform:uppercase}}"""

        if mode == "bg":
            content_html = f'<div class="cover"><div class="deco"></div><div class="wm">{wm}</div></div>'
        elif mode == "text":
            content_html = f"""<div class="cover">
<div class="frame"></div>
<div class="top"><div class="brand">DEZAFIRA <b>STUDIO</b></div>
<div class="badge">{_esc(niche or "Produto")}</div></div>
<div class="main"><div class="kicker">Produto · Dezafira</div>
<div class="title">{_esc(title)}</div>{sub}</div>
<div class="foot"><span>Dezafira Studio</span><span>dezafira.com.br</span></div>
</div>"""
        else:
            content_html = f"""<div class="cover">
<div class="frame"></div><div class="deco"></div><div class="wm">{wm}</div>
<div class="top"><div class="brand">DEZAFIRA <b>STUDIO</b></div>
<div class="badge">{_esc(niche or "Produto")}</div></div>
<div class="main"><div class="kicker">Produto · Dezafira</div>
<div class="title">{_esc(title)}</div>{sub}</div>
<div class="foot"><span>Dezafira Studio</span><span>dezafira.com.br</span></div>
</div>"""

        return f"<!doctype html><html><head><meta charset='utf-8'>{fonts_meta}<style>{style}</style></head><body>{content_html}</body></html>"

    def _html_ebook(self, design: dict, title: str, subtitle: str = "",
                    author: str = "Dezafira Studio", niche: str = "") -> str:
        c = design["colors"]
        wm = _esc((niche or "Dezafira")[:1].upper() or "D")
        sub = f'<div class="subtitle">{_esc(subtitle)}</div>' if subtitle else ""
        fonts_meta = self._google_fonts_links(design)
        return f"""<!doctype html><html><head><meta charset="utf-8">{fonts_meta}<style>
*{margin:0;padding:0;box-sizing:border-box}
body{{width:1200px;height:1600px;overflow:hidden;font-family:{design["font_sans"]}}}
.cover{{width:100%;height:100%;position:relative;color:{c["text"]};
  background:radial-gradient(1100px 700px at 15% -10%,{c["accent"]}30,transparent 55%),
  linear-gradient(160deg,{c["bg"]} 0%,{c["bg2"]} 100%)}}
.frame{{position:absolute;inset:34px;border:1px solid {c["accent"]}44;pointer-events:none}}
.deco{{position:absolute;inset:0;opacity:.10;
  background-image:radial-gradient({c["accent"]} 1.5px,transparent 1.5px);background-size:36px 36px}}
.wm{{position:absolute;right:-30px;bottom:-80px;font-family:{design["font"]};
  font-size:480px;font-weight:900;color:{c["text"]};opacity:.05;line-height:1}}
.top{{position:absolute;top:64px;left:80px;right:80px;display:flex;justify-content:space-between;align-items:center}}
.brand{{font-family:{design["font"]};letter-spacing:4px;font-size:16px;color:{c["muted"]};text-transform:uppercase}}
.brand b{{color:{c["accent"]}}}
.badge{{border:1px solid {c["accent"]}55;color:{c["accent"]};padding:6px 14px;border-radius:999px;
  font-size:13px;letter-spacing:1px;text-transform:uppercase}}
.main{{position:absolute;top:430px;left:80px;right:80px}}
.kicker{{font-size:15px;letter-spacing:4px;text-transform:uppercase;color:{c["accent"]};margin-bottom:20px}}
.title{{font-family:{design["font"]};font-size:78px;line-height:1.1;font-weight:700;text-shadow:0 4px 16px rgba(0,0,0,0.65)}}
.subtitle{{font-size:24px;color:{c["muted"]};margin-top:22px;line-height:1.5;text-shadow:0 2px 8px rgba(0,0,0,0.55)}}
.author{{position:absolute;bottom:170px;left:80px;font-family:{design["font"]};
  font-size:26px;color:{c["accent"]};letter-spacing:1px}}
.foot{{position:absolute;bottom:60px;left:80px;right:80px;display:flex;justify-content:space-between;
  align-items:center;color:{c["muted"]};font-size:14px;letter-spacing:2px;text-transform:uppercase}}
</style></head><body><div class="cover">
<div class="frame"></div><div class="deco"></div><div class="wm">{wm}</div>
<div class="top"><div class="brand">DEZAFIRA <b>STUDIO</b></div>
<div class="badge">{_esc(niche or "Ebook")}</div></div>
<div class="main"><div class="kicker">Ebook · Dezafira</div>
<div class="title">{_esc(title)}</div>{sub}</div>
<div class="author">✍ {_esc(author)}</div>
<div class="foot"><span>Dezafira Studio</span><span>dezafira.com.br</span></div>
</div></body></html>"""

    # ─── Renderers (Obscura → fallback Pillow) ──────────────────────────

    async def _render(self, html: str, kind: str, design: dict, title: str,
                      subtitle: str, author: str, width: int, height: int, mode: str = "full") -> bytes:
        """Renderiza a capa: Obscura (CDP) primeiro, Pillow como fallback."""
        try:
            return await self._render_via_obscura(html, width, height)
        except Exception as e:
            print(f"[AgnesStudio] Obscura indisponível — fallback Pillow: {e}")
        return self._render_via_pillow(kind, design, title, subtitle, author, width, height, mode=mode)

    async def _render_via_obscura(self, html: str, width: int, height: int) -> bytes:
        """Navega para a data URL do HTML e captura PNG via CDP."""
        from services.obscura_bridge import ObscuraBridge, ObscuraNotAvailableError
        if os.getenv("OBSCURA_ENABLED", "true").lower() not in ("true", "1", "yes"):
            raise ObscuraNotAvailableError("OBSCURA_ENABLED=false — Agnes Studio usa fallback Pillow")
        data_url = "data:text/html;base64," + base64.b64encode(html.encode("utf-8")).decode("ascii")
        
        last_err = None
        for attempt in range(2):
            bridge = ObscuraBridge()
            try:
                await bridge.connect()
                await bridge.navigate(data_url)
                png_bytes = await bridge.screenshot(width, height)
                return png_bytes
            except Exception as e:
                last_err = e
                print(f"[AgnesStudio] Obscura tentativa {attempt + 1} falhou: {e}")
            finally:
                await bridge.disconnect()
            if attempt == 0:
                await asyncio.sleep(1.0)
        raise last_err or RuntimeError("Obscura indisponível")

    def _render_via_pillow(self, kind: str, design: dict, title: str,
                           subtitle: str, author: str, width: int,
                           height: int, mode: str = "full") -> bytes:
        """Fallback local: desenha via Pillow."""
        def _hex(ch: str) -> int:
            return int(ch.lstrip("#"), 16)

        c = design["colors"]
        bg_r, bg_g, bg_b = _hex(c["bg"]) >> 16, (_hex(c["bg"]) >> 8) & 0xFF, _hex(c["bg"]) & 0xFF
        bg2_r, bg2_g, bg2_b = _hex(c["bg2"]) >> 16, (_hex(c["bg2"]) >> 8) & 0xFF, _hex(c["bg2"]) & 0xFF
        ac_r, ac_g, ac_b = _hex(c["accent"]) >> 16, (_hex(c["accent"]) >> 8) & 0xFF, _hex(c["accent"]) & 0xFF
        tx_r, tx_g, tx_b = _hex(c["text"]) >> 16, (_hex(c["text"]) >> 8) & 0xFF, _hex(c["text"]) & 0xFF

        if mode == "text":
            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
        elif design.get("bg_image"):
            try:
                bg_fp = design["bg_image"]
                if bg_fp.startswith("data:image"):
                    header, data_part = bg_fp.split(",", 1)
                    img = Image.open(io.BytesIO(base64.b64decode(data_part)))
                elif os.path.isfile(bg_fp):
                    img = Image.open(bg_fp)
                else:
                    raise FileNotFoundError(f"Caminho nao existe: {bg_fp}")
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                draw = ImageDraw.Draw(img)
            except Exception as e:
                print(f"[AgnesStudio] Falha ao carregar bg_image no Pillow: {e}")
                img = Image.new("RGB", (width, height))
                draw = ImageDraw.Draw(img)
                for y in range(height):
                    t = y / max(height - 1, 1)
                    row = (
                        int(bg_r + (bg2_r - bg_r) * t),
                        int(bg_g + (bg2_g - bg_g) * t),
                        int(bg_b + (bg2_b - bg_b) * t),
                    )
                    draw.line([(0, y), (width, y)], fill=row)
        else:
            img = Image.new("RGB", (width, height))
            draw = ImageDraw.Draw(img)
            for y in range(height):
                t = y / max(height - 1, 1)
                row = (
                    int(bg_r + (bg2_r - bg_r) * t),
                    int(bg_g + (bg2_g - bg_g) * t),
                    int(bg_b + (bg2_b - bg_b) * t),
                )
                draw.line([(0, y), (width, y)], fill=row)

        if mode == "bg":
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()

        def _font(size: int, bold: bool = False):
            candidates = ["arialbd.ttf", "arial.ttf", "segoeuib.ttf", "segoeui.ttf",
                          "georgiab.ttf", "georgia.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]
            for name in candidates:
                try:
                    return ImageFont.truetype(name, size)
                except Exception:
                    continue
            try:
                return ImageFont.load_default(size)
            except TypeError:
                return ImageFont.load_default()

        # Barra de acento
        if mode != "text":
            draw.rectangle([0, 0, width, 6], fill=(ac_r, ac_g, ac_b))

        title_font = _font(max(28, width // 18), bold=True)
        sub_font = _font(max(18, width // 42))
        small_font = _font(max(14, width // 64))

        words = str(title or "Dezafira").split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if draw.textlength(trial, font=title_font) <= width * 0.86:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        y = height * 0.28
        for ln in lines[:4]:
            draw.text((width * 0.07, y), ln, font=title_font, fill=(tx_r, tx_g, tx_b))
            y += int(title_font.size * 1.15)
        if subtitle:
            draw.text((width * 0.07, y + 10), str(subtitle)[:80], font=sub_font,
                      fill=((tx_r + tx_g + tx_b) // 3,) * 3)

        if kind == "ebook":
            draw.text((width * 0.07, height * 0.84), f"✍ {author}", font=sub_font,
                      fill=(ac_r, ac_g, ac_b))
        else:
            draw.text((width * 0.07, height * 0.88), f"✍ {author}", font=small_font,
                      fill=(ac_r, ac_g, ac_b))
        draw.text((width * 0.07, height * 0.93), "Dezafira Studio · dezafira.com.br",
                  font=small_font, fill=((tx_r + tx_g + tx_b) // 2,) * 3)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _slug_for(self, prefix: str, entity_id: str) -> str:
        eid = entity_id or ""
        if eid.startswith(prefix + "_"):
            return f"{prefix}-{eid[len(prefix) + 1:]}"
        if prefix == "ebook" and eid.startswith("book_"):
            return f"book-{eid[5:]}"
        return f"{prefix}-{eid}"

    def _save_cover(self, prefix: str, entity_id: str, png: bytes,
                    design: dict, width: int, height: int, mode: str = "full") -> dict:
        os.makedirs(self.outputs_dir, exist_ok=True)
        slug = self._slug_for(prefix, entity_id)
        filename = f"{slug}_{mode}_{uuid.uuid4().hex[:8]}.png" if mode != "full" else f"{slug}_{uuid.uuid4().hex[:8]}.png"
        fp = os.path.join(self.outputs_dir, filename)
        with open(fp, "wb") as f:
            f.write(png)
        return {
            "cover_url": f"/outputs/agnes/{filename}",
            "filename": filename,
            "design": design,
            "width": width,
            "height": height,
            "provider": "agnes-studio",
        }

    # ─── Public Methods ─────────────────────────────────────────────────

    async def generate_course_cover(self, title: str, subtitle: str = "",
                                    author: str = "Dezafira Studio", niche: str = "",
                                    style_id: str = "moderno", course_id: str = "",
                                    difficulty: str = "", modules_count: int = 0,
                                    design: dict = None, mode: str = "full") -> dict:
        design = design or self._make_design(style_id, niche)
        html = self._html_course(design, title=title, subtitle=subtitle, niche=niche,
                                 difficulty=difficulty, modules_count=modules_count,
                                 author=author, mode=mode)
        png = await self._render(html, "course", design, title, subtitle, author, 1280, 720, mode=mode)
        return self._save_cover("crs", course_id, png, design, 1280, 720, mode=mode)

    async def generate_ebook_cover(self, title: str, subtitle: str = "",
                                   author: str = "Dezafira Studio", niche: str = "",
                                   style_id: str = "moderno", book_id: str = "",
                                   design: dict = None) -> dict:
        design = design or self._make_design(style_id, niche)
        html = self._html_ebook(design, title=title, subtitle=subtitle,
                                author=author or "Dezafira Studio", niche=niche)
        png = await self._render(html, "ebook", design, title, subtitle,
                                 author or "Dezafira Studio", 1200, 1600)
        return self._save_cover("ebook", book_id, png, design, 1200, 1600)

    async def generate_blog_cover(self, title: str, subtitle: str = "",
                                  niche: str = "", style_id: str = "moderno",
                                  post_id: str = "", blog_name: str = "",
                                  design: dict = None) -> dict:
        design = design or self._make_design(style_id, niche)
        html = self._html_blog(design, title=title, subtitle=subtitle, niche=niche,
                               blog_name=blog_name)
        png = await self._render(html, "blog", design, title, subtitle,
                                 "Dezafira Studio", 1200, 630)
        return self._save_cover("post", post_id, png, design, 1200, 630)

    async def generate_product_cover(self, title: str, subtitle: str = "",
                                     niche: str = "", style_id: str = "moderno",
                                     entity_id: str = "", design: dict = None, mode: str = "full") -> dict:
        design = design or self._make_design(style_id, niche)
        html = self._html_product(design, title=title, subtitle=subtitle, niche=niche, mode=mode)
        png = await self._render(html, "product", design, title, subtitle,
                                 "Dezafira Studio", 1024, 1024, mode=mode)
        return self._save_cover("prod", entity_id, png, design, 1024, 1024, mode=mode)
