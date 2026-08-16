"""
VSL Video — transforma o roteiro de uma VSL em vídeo real:

  1. Divide o script em cenas (parágrafos, máx. 8).
  2. Renderiza cada cena como slide editorial (HTML → PNG via Chrome CDP,
     fallback Pillow) usando o mesmo design/estilo do Agnes Studio.
  3. Narra cada cena com TTS (edge-tts — voz pt-BR, sem chave).
  4. Monta o MP4 com ffmpeg (binário estático do imageio-ffmpeg).

Degradação graciosa: sem Chrome → slides Pillow; TTS falhou → cena silenciosa
com duração mínima; sem ffmpeg → retorna as cenas sem o vídeo. Nunca 500.
"""

from __future__ import annotations

import asyncio
import base64
import html as html_mod
import os
import re
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from modules.agnes_studio import AgnesStudio, _esc
from modules.art_director import ArtDirector, VIBES

VSL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "vsl")
DEFAULT_VOICE = "pt-BR-FranciscaNeural"
MAX_SCENES = 8
MIN_SCENE_SECONDS = 3.0


def _split_scenes(script: str) -> List[str]:
    """Divide o roteiro em cenas (parágrafos), máx. MAX_SCENES."""
    raw = [p.strip() for p in re.split(r"\n\s*\n", script or "") if p.strip()]
    scenes: List[str] = []
    for p in raw:
        # Quebra parágrafos longos em frases de ~360 chars
        while len(p) > 360:
            cut = p.rfind(". ", 200, 360)
            if cut == -1:
                cut = 360
            scenes.append(p[: cut + 1].strip())
            p = p[cut + 1:].strip()
        if p:
            scenes.append(p)
        if len(scenes) >= MAX_SCENES:
            break
    if not scenes:
        scenes = [script or "Conteúdo"]
    return scenes[:MAX_SCENES]


def _scene_html(text: str, title: str, design: dict, index: int, total: int, transparent: bool = False) -> str:
    """Slide editorial da cena (mesma linguagem visual das capas Agnes)."""
    c = design.get("colors", {})
    fonts = design.get("fonts", {})
    font = fonts.get("font") or "Georgia, serif"
    font_sans = fonts.get("font_sans") or "'Segoe UI', sans-serif"
    accent = c.get("accent", "#38bdf8")
    if transparent:
        bg_style = "background: transparent;"
    else:
        bg = c.get("bg", "#0b1220")
        bg2 = c.get("bg2", "#16233d")
        bg_style = f"background: linear-gradient(160deg, {bg} 0%, {bg2} 100%);"
    text_c = c.get("text", "#ffffff")
    muted = c.get("muted", "#8aa2c0")
    body = _esc(text)
    brand = _esc(title)
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    width:1280px; height:720px; overflow:hidden;
    font-family:{font_sans};
    {bg_style}
    color:{text_c}; display:flex; flex-direction:column;
    padding:64px 72px; position:relative;
  }}
  .top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:48px; }}
  .brand {{ font-family:{font}; font-weight:700; font-size:26px; letter-spacing:.02em; }}
  .brand b {{ color:{accent}; }}
  .counter {{ font-size:15px; color:{muted}; letter-spacing:.25em; font-weight:700; }}
  .scene {{ flex:1; display:flex; flex-direction:column; justify-content:center; }}
  .scene p {{ font-family:{font}; font-size:40px; line-height:1.45; font-weight:700; }}
  .bar {{ width:84px; height:6px; border-radius:999px; background:{accent}; margin-bottom:28px; }}
  .foot {{ display:flex; justify-content:space-between; align-items:center; margin-top:40px; color:{muted}; font-size:15px; }}
</style></head><body>
  <div class="top">
    <div class="brand">Dezafira<b>Club</b></div>
    <div class="counter">{index:02d} / {total:02d}</div>
  </div>
  <div class="scene"><div class="bar"></div><p>{body}</p></div>
  <div class="foot"><span>{brand}</span><span>Dezafira Studio</span></div>
</body></html>"""


def _render_scene_pillow(text: str, design: dict, width: int, height: int, transparent: bool = False) -> bytes:
    """Fallback local das cenas: gradiente + texto quebrado (sem browser).
    Retorna bytes PNG prontos para gravar."""
    import io
    from PIL import Image, ImageDraw, ImageFont

    def _hex(ch: str) -> int:
        return int(ch.lstrip("#"), 16)

    c = design.get("colors", {})
    text_c = c.get("text", "#ffffff")
    muted = c.get("muted", "#8aa2c0")
    accent = c.get("accent", "#38bdf8")

    if transparent:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
    else:
        bg = c.get("bg", "#0b1220")
        bg2 = c.get("bg2", "#16233d")
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)
        r0, g0, b0 = (_hex(bg) >> 16), ((_hex(bg) >> 8) & 0xFF), (_hex(bg) & 0xFF)
        r1, g1, b1 = (_hex(bg2) >> 16), ((_hex(bg2) >> 8) & 0xFF), (_hex(bg2) & 0xFF)
        for y in range(height):
            t = y / max(height - 1, 1)
            draw.line([(0, y), (width, y)], fill=(
                int(r0 + (r1 - r0) * t),
                int(g0 + (g1 - g0) * t),
                int(b0 + (b1 - b0) * t),
            ))

    def _font(size: int, bold: bool = False):
        names = ["arialbd.ttf", "arial.ttf", "segoeuib.ttf", "segoeui.ttf",
                 "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if bold else \
                ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]
        for name in names:
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        try:
            return ImageFont.load_default(size)
        except TypeError:
            return ImageFont.load_default()

    f_brand = _font(26, bold=True)
    f_body = _font(40, bold=True)
    draw.text((72, 56), "DezafiraClub", font=f_brand, fill=text_c)
    draw.rectangle([72, 118, 156, 124], fill=accent)

    # Quebra de texto simples
    words = (text or "").split()
    lines: List[str] = []
    line = ""
    for w in words:
        trial = f"{line} {w}".strip()
        if draw.textlength(trial, font=f_body) <= width - 144:
            line = trial
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    lines = lines[:6]

    y = 220
    for ln in lines:
        draw.text((72, y), ln, font=f_body, fill=text_c)
        y += 62
    draw.text((72, height - 80), "Dezafira Studio", font=_font(15), fill=muted)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def render_scene_png(text: str, title: str, design: dict, index: int,
                           total: int, out_path: str, transparent: bool = False) -> bool:
    """Renderiza a cena → PNG (Chrome CDP; fallback Pillow). Salva no caminho."""
    html = _scene_html(text, title, design, index, total, transparent=transparent)
    png: Optional[bytes] = None
    try:
        studio = AgnesStudio()
        png = await studio._render_via_obscura(html, 1280, 720)
    except Exception as e:  # noqa: BLE001
        print(f"[VslVideo] Chrome indisponível para cena {index} — fallback Pillow: {e}")
    if png is None:
        png = _render_scene_pillow(text, design, 1280, 720, transparent=transparent)
    with open(out_path, "wb") as f:
        f.write(png)
    return True


async def synthesize_audio(text: str, out_mp3: str, voice: str = DEFAULT_VOICE) -> bool:
    """Narra o texto com edge-tts (pt-BR). Retorna False se falhar."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate="+0%")
        await communicate.save(out_mp3)
        return os.path.getsize(out_mp3) > 1000
    except Exception as e:  # noqa: BLE001
        print(f"[VslVideo] TTS falhou: {e}")
        return False


def _ffmpeg() -> Optional[str]:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001
        return None


async def _build_segment(scene_png: str, scene_mp3: Optional[str],
                         out_mp4: str, ffmpeg: str) -> bool:
    """Concatena imagem + áudio → segmento MP4 (loop estático)."""
    if scene_mp3 and os.path.isfile(scene_mp3):
        cmd = [ffmpeg, "-y", "-loglevel", "error",
               "-loop", "1", "-i", scene_png, "-i", scene_mp3,
               "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
               "-r", "24", "-c:a", "aac", "-b:a", "128k", "-shortest", out_mp4]
    else:
        # Cena sem áudio: duração mínima fixa
        cmd = [ffmpeg, "-y", "-loglevel", "error",
               "-loop", "1", "-i", scene_png,
               "-t", str(MIN_SCENE_SECONDS),
               "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
               "-r", "24", "-an", out_mp4]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=120)
        return r.returncode == 0 and os.path.isfile(out_mp4)
    except Exception as e:  # noqa: BLE001
        print(f"[VslVideo] ffmpeg segmento falhou: {e}")
        return False


async def _build_segment_overlay(video_path: str, transparent_png_path: str,
                                 scene_mp3: Optional[str], out_mp4: str, ffmpeg: str) -> bool:
    """Mescla um vídeo de fundo (MP4) com uma camada de texto transparente (PNG)
    e opcionalmente adiciona áudio MP3 (narração/som)."""
    if scene_mp3 and os.path.isfile(scene_mp3):
        cmd = [ffmpeg, "-y", "-loglevel", "error",
               "-i", video_path, "-i", transparent_png_path, "-i", scene_mp3,
               "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
               "-map", "[v]", "-map", "2:a",
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-shortest", out_mp4]
    else:
        cmd = [ffmpeg, "-y", "-loglevel", "error",
               "-i", video_path, "-i", transparent_png_path,
               "-filter_complex", "[0:v][1:v]overlay=0:0",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", out_mp4]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=120)
        return r.returncode == 0 and os.path.isfile(out_mp4)
    except Exception as e:  # noqa: BLE001
        print(f"[VslVideo] ffmpeg segment overlay falhou: {e}")
        return False


async def _concat_segments(segments: List[str], out_mp4: str, ffmpeg: str) -> bool:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for s in segments:
            f.write(f"file '{s.replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'\n")
        list_path = f.name
    try:
        cmd = [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
               "-i", list_path, "-c", "copy", out_mp4]
        r = subprocess.run(cmd, capture_output=True, timeout=180)
        return r.returncode == 0 and os.path.isfile(out_mp4)
    except Exception as e:  # noqa: BLE001
        print(f"[VslVideo] ffmpeg concat falhou: {e}")
        return False
    finally:
        try:
            os.unlink(list_path)
        except OSError:
            pass


async def generate_vsl_video(vsl_id: str, script: str, title: str, niche: str,
                             style_id: str = "moderno", brand_kit: dict = None,
                             voice: str = DEFAULT_VOICE) -> Dict[str, Any]:
    """Gera o vídeo da VSL (cenas + narração TTS) e salva em outputs/vsl/.

    Retorna {status, video_url?, scenes[], errors[]}. Nunca levanta.
    """
    os.makedirs(VSL_DIR, exist_ok=True)
    scenes = _split_scenes(script)
    result: Dict[str, Any] = {"status": "generating", "scenes": [], "errors": []}
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        result.update({"status": "no-ffmpeg", "errors": ["ffmpeg não disponível"]})
        return result

    director = ArtDirector()
    vibe_id = (brand_kit or {}).get("vibe_id") or style_id
    if vibe_id in VIBES:
        design = director.generate_brand_kit(vibe_id, niche)
    else:
        studio = AgnesStudio()
        design = studio._make_design(style_id, niche, brand_kit=brand_kit)
    total = len(scenes)
    segment_paths: List[str] = []

    for i, scene_text in enumerate(scenes, start=1):
        png_path = os.path.join(VSL_DIR, f"{vsl_id}_scene_{i:02d}.png")
        mp3_path = os.path.join(VSL_DIR, f"{vsl_id}_scene_{i:02d}.mp3")
        seg_path = os.path.join(VSL_DIR, f"{vsl_id}_seg_{i:02d}.mp4")
        try:
            await render_scene_png(scene_text, title, design, i, total, png_path)
            await synthesize_audio(scene_text, mp3_path, voice)
            ok = await _build_segment(png_path, mp3_path if os.path.isfile(mp3_path) else None, seg_path, ffmpeg)
            if not ok:
                result["errors"].append(f"cena {i}: ffmpeg não gerou segmento")
                continue
            segment_paths.append(seg_path)
            result["scenes"].append({
                "index": i, "text": scene_text[:120],
                "png": f"/outputs/vsl/{os.path.basename(png_path)}",
                "mp3": f"/outputs/vsl/{os.path.basename(mp3_path)}" if os.path.isfile(mp3_path) else None,
            })
        except Exception as e:  # noqa: BLE001
            result["errors"].append(f"cena {i}: {e}")

    if not segment_paths:
        result["status"] = "failed"
        result["errors"].append("Nenhuma cena gerada")
        return result

    out_mp4 = os.path.join(VSL_DIR, f"{vsl_id}.mp4")
    if await _concat_segments(segment_paths, out_mp4, ffmpeg):
        result.update({"status": "ok", "video_url": f"/outputs/vsl/{vsl_id}.mp4"})
    else:
        result["status"] = "partial"
        result["errors"].append("Concatenação falhou — cenas geradas")
    return result
