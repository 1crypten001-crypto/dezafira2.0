#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DEZAFIRA STUDIO — TEMPLATE SCRIPT PARA VÍDEOS DE PRODUTOS
═══════════════════════════════════════════════════════════

Agnes Diretora Geral de Arte — Pipeline Cinematográfica

Gera peças visuais premium estilo Apple TV+ com:
  • Background cinematográfico gerado por IA (sem fundo branco genérico)
  • Logo oficial Dezafira integrado como watermark
  • Tipografia carregada do Google Fonts pelo Chrome CDP
  • Composição de texto respeitando safe frame e espaços respirados
  • Vídeo 16:9 sem crop, duração configurável, FFMPEG com scale correto
"""

import argparse
import asyncio
import os
import sys
import httpx
from PIL import Image, ImageDraw, ImageFont
import io

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

from modules.art_director import ArtDirector
from modules.agnes_studio import AgnesStudio
from modules.agnes_video import agnes_video_generate_and_wait, agnes_download_video, image_to_base64
from modules.vsl_video import _ffmpeg

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_WATERMARK = os.path.join(BASE_DIR, "assets", "brand", "logo_watermark.png")
LOGO_ICON      = os.path.join(BASE_DIR, "assets", "brand", "logo_icon.png")

AGNES_API_KEY = os.getenv("AGNES_API_KEY", "").strip()


# ── 1. Geração de Background Cinematográfico ──────────────────────────────

async def generate_cinematic_bg(prompt: str, ratio: str = "16:9") -> str:
    """Gera o background via Agnes Image API e retorna a URL."""
    if not AGNES_API_KEY:
        raise ValueError("Chave AGNES_API_KEY não configurada no .env!")

    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt,
        "ratio": ratio,
        "extra_body": {"response_format": "url"},
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        r = await client.post(
            "https://apihub.agnes-ai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {AGNES_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    if r.status_code == 200:
        data = r.json()
        images = data.get("data") or []
        if images and images[0].get("url"):
            return images[0]["url"]
    raise RuntimeError(f"Erro Agnes Image: {r.status_code} — {r.text[:200]}")


# ── 2. Composição do HTML Cinematográfico ─────────────────────────────────

def build_cinematic_html(
    title: str,
    subtitle: str,
    niche: str,
    design: dict,
    http_bg_url: str,
    http_logo_url: str,
    mode: str = "full",   # "full" | "text_only"
) -> str:
    """
    Gera HTML editorial estilo Apple TV+ com:
      - Fundo: imagem cinematográfica gerada por IA (ou transparente em mode='text_only')
      - Logo Dezafira no canto superior esquerdo (watermark)
      - Título em tipografia premium com sombra profunda
      - Subtítulo com breathing room abaixo do título
      - Rodapé com crédito discreto e URL
    """
    c = design["colors"]
    font_name   = design.get("font", "Inter")
    font_sans   = design.get("font_sans", "Inter")
    accent      = c.get("accent", "#00CFFF")
    text_color  = c.get("text",   "#FFFFFF")
    muted_color = c.get("muted",  "#86868b")

    # Google Fonts dinâmico
    fonts_set = set()
    for f in (font_name, font_sans):
        fname = f.split(",")[0].strip().strip("'\"")
        if fname and fname not in ("Arial", "Helvetica", "Georgia", "Segoe UI", "SF Pro"):
            fonts_set.add(fname.replace(" ", "+"))
    if fonts_set:
        family_str = "&".join(f"family={f}:ital,wght@0,300;0,400;0,700;0,900;1,400" for f in fonts_set)
        fonts_html = (
            f'<link rel="preconnect" href="https://fonts.googleapis.com">'
            f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            f'<link href="https://fonts.googleapis.com/css2?{family_str}&display=swap" rel="stylesheet">'
        )
    else:
        fonts_html = ""

    # Background e Logo via URLs HTTP (passadas pelo servidor local temporário)
    # O Chrome CDP bloqueia data: URLs dentro de páginas data: por política de segurança
    bg_img_tag = ""
    if mode == "text_only":
        bg_css = "background: transparent;"
    elif http_bg_url:
        bg_css = "background: #000;"
        bg_img_tag = f'<img src="{http_bg_url}" class="bg-img" alt="" />'
    else:
        bg_css = f"background: linear-gradient(160deg, {c['bg']} 0%, {c.get('bg2', c['bg'])} 100%);"

    logo_img_html = (
        f'<img src="{http_logo_url}" alt="Dezafira" class="logo" />'
        if http_logo_url else
        '<div class="logo-text">DEZAFIRA</div>'
    )

    # Gradient overlay para garantir legibilidade (estilo Apple TV+)
    # Escurece o fundo onde o texto vai aparecer (parte inferior)
    overlay_gradient = (
        "background: linear-gradient("
        "to bottom,"
        "rgba(0,0,0,0.0) 0%,"
        "rgba(0,0,0,0.0) 35%,"
        "rgba(0,0,0,0.55) 60%,"
        "rgba(0,0,0,0.80) 100%"
        ");"
        if mode != "text_only" else ""
    )

    logo_img_html_override = logo_img_html  # already set above from http_logo_url

    sub_html = (
        f'<p class="subtitle">{subtitle}</p>'
        if subtitle else ""
    )

    tag_html = (
        f'<span class="tag">{niche.upper()}</span>'
        if niche else ""
    )

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
{fonts_html}
<style>
  *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1280px;
    height: 720px;
    overflow: hidden;
    font-family: '{font_sans.split(",")[0].strip()}', Helvetica, Arial, sans-serif;
    {bg_css}
    background-repeat: no-repeat;
    background-size: cover;
    position: relative;
  }}

  /* Imagem de fundo posicionada absolutamente para funcionar com data:URL */
  .bg-img {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    z-index: 0;
  }}

  /* Gradient overlay — garante legibilidade do texto sobre qualquer imagem */
  .overlay {{
    position: absolute;
    inset: 0;
    {overlay_gradient}
    pointer-events: none;
  }}

  /* Logo no canto superior esquerdo — watermark discreto */
  .logo {{
    position: absolute;
    top: 36px;
    left: 48px;
    height: 44px;
    width: auto;
    opacity: 0.92;
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.6));
    z-index: 10;
  }}
  .logo-text {{
    position: absolute;
    top: 36px;
    left: 48px;
    font-family: '{font_name.split(",")[0].strip()}', sans-serif;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 4px;
    color: {accent};
    text-shadow: 0 0 20px {accent}88;
    z-index: 10;
  }}

  /* Tag / niche chip */
  .tag {{
    display: inline-block;
    font-family: '{font_sans.split(",")[0].strip()}', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 3px;
    color: {text_color};
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
    padding: 6px 16px;
    border-radius: 999px;
    backdrop-filter: blur(8px);
    margin-bottom: 20px;
  }}

  /* Bloco de texto — posicionado na parte inferior com safe frame */
  .content {{
    position: absolute;
    bottom: 72px;
    left: 64px;
    right: 64px;
    z-index: 5;
  }}

  /* Título — peso máximo, sombra profunda para legibilidade */
  .title {{
    font-family: '{font_name.split(",")[0].strip()}', Helvetica, Arial, sans-serif;
    font-size: 68px;
    font-weight: 900;
    line-height: 1.06;
    letter-spacing: -1.5px;
    color: {text_color};
    text-shadow:
      0 2px 4px rgba(0,0,0,0.9),
      0 8px 24px rgba(0,0,0,0.75),
      0 16px 48px rgba(0,0,0,0.5);
    max-width: 900px;
    margin-bottom: 16px;
  }}

  /* Subtítulo — secundário mas legível */
  .subtitle {{
    font-family: '{font_sans.split(",")[0].strip()}', Helvetica, Arial, sans-serif;
    font-size: 22px;
    font-weight: 400;
    line-height: 1.4;
    color: rgba(255,255,255,0.82);
    text-shadow:
      0 2px 8px rgba(0,0,0,0.85),
      0 4px 16px rgba(0,0,0,0.6);
    max-width: 760px;
    letter-spacing: 0.1px;
  }}

  /* Rodapé — crédito discreto */
  .footer {{
    position: absolute;
    bottom: 28px;
    right: 64px;
    font-family: '{font_sans.split(",")[0].strip()}', sans-serif;
    font-size: 13px;
    font-weight: 400;
    letter-spacing: 2px;
    color: rgba(255,255,255,0.45);
    text-transform: uppercase;
    z-index: 10;
  }}
</style>
</head>
<body>
  {bg_img_tag}
  <div class="overlay"></div>
  {logo_img_html}
  <div class="content">
    {tag_html}
    <h1 class="title">{title}</h1>
    {sub_html}
  </div>
  <div class="footer">dezafira.com.br</div>
</body>
</html>"""
    return html


# ── 3. Overlay FFMPEG corrigido (sem crop) ────────────────────────────────

async def apply_text_overlay_ffmpeg(
    video_path: str,
    text_png_path: str,
    out_mp4: str,
    ffmpeg_exe: str,
) -> bool:
    """
    Mescla vídeo de fundo com PNG de texto transparente.
    O PNG é escalado exatamente para a resolução do vídeo antes do overlay
    para evitar qualquer crop ou corte de elementos.
    """
    import subprocess

    # Primeiro detecta a resolução do vídeo
    probe_cmd = [
        ffmpeg_exe, "-y", "-loglevel", "error",
        "-i", video_path,
        "-frames:v", "1",
        "-f", "null", "-",
    ]

    # Comando FFMPEG com scale explícito do PNG para resolução do vídeo
    # [1:v]scale=W:H força o overlay a ter as mesmas dimensões do vídeo
    cmd = [
        ffmpeg_exe, "-y", "-loglevel", "error",
        "-i", video_path,
        "-i", text_png_path,
        "-filter_complex",
        "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2[bg];"
        "[1:v]scale=1280:720[txt];"
        "[bg][txt]overlay=0:0[out]",
        "-map", "[out]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        out_mp4,
    ]
    try:
        r = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(r.communicate(), timeout=180)
        success = (r.returncode == 0) and os.path.isfile(out_mp4)
        if not success:
            print(f"[FFMPEG] Erro: {stderr.decode('utf-8', errors='replace')[-400:]}")
        return success
    except Exception as e:
        print(f"[FFMPEG] Exceção: {e}")
        return False


# ── 4. Pipeline Principal ─────────────────────────────────────────────────

async def run_generation(
    title: str,
    subtitle: str,
    niche: str,
    vibe_id: str,
    duration: int,
    output_name: str,
):
    print(f"\n{'═'*60}")
    print(f"  AGNES DIRETORA DE ARTE — Pipeline Cinematográfica")
    print(f"  Vibe: {vibe_id.upper()} | Produto: {title}")
    print(f"{'═'*60}\n")

    director = ArtDirector()
    design   = director.generate_brand_kit(vibe_id, niche)

    # ── Passo 1: Super Prompt Cinematográfico ──────────────────────────
    print("[1/6] 🎬 Gerando prompt cinematográfico...")

    vibe_name = vibe_id.upper()
    # Prompt 100% descritivo em terceira pessoa — sem imperativo que vaze como texto
    subject = (
        "dark dramatic stage with a single powerful spotlight from above, "
        "thick atmospheric fog rolling across the floor, "
        "cinematic bokeh light orbs in background, "
        "polished wet reflective stage surface, "
        "professional photography 85mm f1.4 lens, 8K"
    )
    scene = (
        "Mood: powerful, premium, technology-driven, bold. "
        "The lower third of the frame is deep shadow, fading to pure black. "
        "Upper area has dramatic rim lighting with volumetric rays. "
        "No humans, no faces, no text elements, no letters, no symbols, "
        "no product labels, no watermarks — purely abstract cinematic atmosphere."
    )

    image_prompt = director.generate_image_prompt(vibe_id, subject, scene)
    print(f"  Prompt: {image_prompt[:110]}...")

    # ── Passo 2: Gerar Background Cinematográfico por IA ──────────────
    print("[2/6] 🖼️  Gerando background cinematográfico (IA)...")
    try:
        bg_url = await generate_cinematic_bg(image_prompt, ratio="16:9")
        print("  ✓ Background gerado!")
    except Exception as e:
        print(f"  ✗ Falha ao gerar background: {e}")
        return

    # Baixar imagem
    bg_path = os.path.join(BASE_DIR, "outputs", "agnes", f"{output_name}_cinematic_bg.png")
    os.makedirs(os.path.dirname(bg_path), exist_ok=True)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(bg_url)
        if r.status_code == 200:
            with open(bg_path, "wb") as f:
                f.write(r.content)
            print(f"  ✓ Salvo em: {bg_path}")
        else:
            print(f"  ✗ Falha ao baixar imagem: {r.status_code}")
            return

    # ── Passo 3: Renderizar HTML via Chrome CDP com servidor HTTP local ──
    print("[3/6] 🌐 Renderizando layout editorial via Chrome CDP...")

    studio = AgnesStudio()
    full_png_path = os.path.join(BASE_DIR, "outputs", "agnes", f"{output_name}_full.png")
    text_png_path = os.path.join(BASE_DIR, "outputs", "agnes", f"{output_name}_text.png")

    # Sobe um servidor HTTP temporário para servir a imagem de fundo e o logo
    # O Chrome CDP não consegue carregar data: URLs dentro de páginas data:
    import aiohttp
    from aiohttp import web as aio_web
    import random as _rnd

    srv_port = _rnd.randint(19000, 19999)
    served_files = {"bg.png": bg_path, "logo.png": LOGO_ICON}

    async def serve_file(request):
        fpath = served_files.get(request.match_info["name"])
        if fpath and os.path.isfile(fpath):
            return aio_web.FileResponse(fpath)
        return aio_web.Response(status=404)

    app = aio_web.Application()
    app.router.add_get("/{name}", serve_file)
    runner = aio_web.AppRunner(app)
    await runner.setup()
    await aio_web.TCPSite(runner, "127.0.0.1", srv_port).start()
    print(f"  HTTP assets server: http://127.0.0.1:{srv_port}")

    http_bg_url   = f"http://127.0.0.1:{srv_port}/bg.png"
    http_logo_url = f"http://127.0.0.1:{srv_port}/logo.png"

    try:
        for mode_label, out_path, mode_val in [
            ("full", full_png_path, "full"),
            ("text", text_png_path, "text_only"),
        ]:
            html_src = build_cinematic_html(
                title, subtitle, niche, design,
                http_bg_url, http_logo_url, mode=mode_val
            )
            import base64 as b64mod
            data_url = "data:text/html;base64," + b64mod.b64encode(html_src.encode()).decode()
            try:
                from services.obscura_bridge import ObscuraBridge
                bridge = ObscuraBridge()
                await bridge.connect()
                # Injeta HTML via document.write para ter origem http (não data:)
                html_escaped = html_src.replace("\\", "\\\\").replace("`", "\\`")
                await bridge.execute_js(
                    f"document.open(); document.write(`{html_escaped}`); document.close();"
                )
                await asyncio.sleep(2.5)  # aguarda imagens HTTP carregarem
                png_bytes = await bridge.screenshot(1280, 720)
                await bridge.disconnect()
                with open(out_path, "wb") as f:
                    f.write(png_bytes)
                print(f"  ✓ [{mode_label}] renderizado via Chrome CDP")
            except Exception as e:
                print(f"  ⚠ Chrome CDP falhou ({e}), usando fallback Pillow para [{mode_label}]")
                _pillow_fallback(
                    title, subtitle, niche, design, bg_path,
                    LOGO_WATERMARK, out_path, 1280, 720,
                    transparent=(mode_label == "text")
                )
    finally:
        await runner.cleanup()
        print("  HTTP assets server encerrado.")

    # ── Passo 4: Enviar background puro para Agnes Video IA ───────────
    print(f"[4/6] 🎥 Gerando animação de {duration}s com Agnes Video IA...")

    # A IA anima apenas o background limpo (sem texto)
    bg_b64 = image_to_base64(bg_path)
    motion_config = director.generate_video_motion_prompt(vibe_id, title)

    result = await agnes_video_generate_and_wait(
        motion_config["prompt"],
        image=bg_b64,
        poll_interval=10.0,
        timeout=900.0,
        motion=motion_config["motion"],
        aspect_ratio="16:9",
        fps=24,
        negative_prompt=motion_config["negative_prompt"],
        duration=duration,
    )

    if result.get("error") or not result.get("url"):
        print(f"  ✗ Agnes Video falhou: {result.get('error')}")
        return

    # ── Passo 5: Baixar clipe ─────────────────────────────────────────
    print("[5/6] ⬇️  Baixando clipe animado...")
    temp_mp4 = os.path.join(BASE_DIR, "outputs", "vsl", f"{output_name}_raw.mp4")
    os.makedirs(os.path.dirname(temp_mp4), exist_ok=True)
    await agnes_download_video(result["url"], temp_mp4)
    print("  ✓ Clipe baixado!")

    # ── Passo 6: Renderização do Remotion (Motion Design em React) ────
    print("[6/6] 🎞️  Renderizando animações tipográficas via Remotion...")
    import shutil
    import json
    import subprocess

    remotion_studio = os.path.join(BASE_DIR, "remotion-studio")
    public_dir = os.path.join(remotion_studio, "public")
    os.makedirs(public_dir, exist_ok=True)

    # Copia assets para a pasta public do Remotion (bypassa CORS no headless shell)
    shutil.copy2(temp_mp4, os.path.join(public_dir, "bg_video.mp4"))
    shutil.copy2(LOGO_ICON, os.path.join(public_dir, "logo.png"))

    props = {
        "title": title,
        "subtitle": subtitle,
        "niche": niche,
        "bgVideoPath": "bg_video.mp4",
        "logoPath": "logo.png",
        "colors": design["colors"],
        "fontFamily": design.get("font_sans", "Inter"),
        "durationInSeconds": duration
    }

    props_path = os.path.join(remotion_studio, "temp_props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    node_dir = os.path.join(BASE_DIR, ".tools", "node")
    env = os.environ.copy()
    env["PATH"] = node_dir + ";" + env.get("PATH", "")

    final_mp4 = os.path.join(BASE_DIR, "outputs", "vsl", f"{output_name}_promo.mp4")
    os.makedirs(os.path.dirname(final_mp4), exist_ok=True)

    cmd = [
        "npx", "remotion", "render",
        "src/index.ts", "CinematicPromo",
        final_mp4.replace("\\", "/"),
        f"--props={props_path.replace('\\', '/')}",
        "--browser-arg=--no-sandbox",
        "--browser-arg=--disable-setuid-sandbox",
        "--browser-arg=--disable-gpu",
        "--browser-arg=--disable-dev-shm-usage",
        "--y"
    ]

    print("  ⚙️  Invocando Remotion...")
    p = subprocess.run(
        cmd,
        cwd=remotion_studio,
        env=env,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    # Limpa temporários
    try:
        os.unlink(os.path.join(public_dir, "bg_video.mp4"))
        os.unlink(os.path.join(public_dir, "logo.png"))
        os.unlink(props_path)
        os.unlink(temp_mp4)
    except OSError:
        pass

    ok = (p.returncode == 0)
    if not ok:
        print("  ✗ Remotion falhou na renderização!")
        print("--- REMOTION STDERR ---")
        print(p.stderr)
        print("-----------------------")


    if ok:
        print(f"\n{'═'*60}")
        print(f"  ✅  PRODUTO PROMOVIDO COM SUCESSO!")
        print(f"{'═'*60}")
        print(f"  🖼️  Imagem: outputs/agnes/{output_name}_full.png")
        print(f"  🎥  Vídeo:  outputs/vsl/{output_name}_promo.mp4")
        print(f"{'═'*60}\n")
    else:
        print("  ✗ Falha no overlay FFMPEG.")


# ── Fallback Pillow ────────────────────────────────────────────────────────

def _pillow_fallback(
    title, subtitle, niche, design, bg_path, logo_path,
    out_path, W, H, transparent=False
):
    """Renderização Pillow de emergência quando Chrome CDP não está disponível."""
    c = design["colors"]

    if transparent:
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    elif bg_path and os.path.isfile(bg_path):
        img = Image.open(bg_path).convert("RGBA").resize((W, H), Image.LANCZOS)
        # Gradient overlay escuro na parte inferior
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        for y in range(H):
            t = max(0, (y - H * 0.35) / (H * 0.65))
            alpha = int(200 * t)
            ov_draw.line([(0, y), (W, y)], fill=(0, 0, 0, min(alpha, 200)))
        img = Image.alpha_composite(img, overlay)
    else:
        def hex2rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        bg_rgb = hex2rgb(c.get("bg", "#0d1b2a"))
        img = Image.new("RGB", (W, H), bg_rgb).convert("RGBA")

    draw = ImageDraw.Draw(img)

    # Logo watermark
    if logo_path and os.path.isfile(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo_h = 44
            ratio = logo_h / logo.height
            logo_w = int(logo.width * ratio)
            logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
            img.paste(logo, (48, 36), logo)
        except Exception:
            pass

    # Título
    def _fnt(size):
        for name in ["arialbd.ttf", "arial.ttf", "segoeuib.ttf", "segoeui.ttf", "DejaVuSans-Bold.ttf"]:
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return ImageFont.load_default()

    title_font = _fnt(60)
    sub_font   = _fnt(22)

    # Safe frame — texto na parte inferior
    y_title = H - 220
    draw.text((64, y_title), title, font=title_font, fill=(255, 255, 255, 255))
    if subtitle:
        draw.text((64, y_title + 80), subtitle[:90], font=sub_font, fill=(255, 255, 255, 200))

    # Rodapé
    foot_font = _fnt(13)
    draw.text((W - 200, H - 36), "dezafira.com.br", font=foot_font, fill=(255, 255, 255, 100))

    with open(out_path, "wb") as f:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        f.write(buf.getvalue())


# ── Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agnes — Gera capa cinematográfica e vídeo de produto premium."
    )
    parser.add_argument("--title",    required=True, help="Título do produto")
    parser.add_argument("--subtitle", required=True, help="Subtítulo descritivo")
    parser.add_argument("--niche",    default="Geral", help="Nicho do produto")
    parser.add_argument("--vibe",     default="apple",
                        help="Vibe visual: apple, dezafira, linear, claude, stripe, nintendo")
    parser.add_argument("--duration", type=int, default=15,
                        help="Duração do vídeo em segundos")
    parser.add_argument("--output",   default="product_promo",
                        help="Nome base dos arquivos gerados")

    args = parser.parse_args()

    asyncio.run(run_generation(
        title=args.title,
        subtitle=args.subtitle,
        niche=args.niche,
        vibe_id=args.vibe,
        duration=args.duration,
        output_name=args.output,
    ))
