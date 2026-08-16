"""Demo — Imagem de marca Dezafira com Agnes AI.

Fluxo:
  1. Fundo 16:9 gerado pela Agnes (agnes-image-2.1-flash) com o branding Dezafira
     (petróleo #0f1a21 + laranja #FF5B06).
  2. Composição HTML com tipografia + copy (headline, sub, CTA, watermark).
  3. Render via Chrome CDP (ObscuraBridge) → PNG em outputs/agnes/.

Uso:
    .venv/Scripts/python scripts/agnes_brand_demo.py
"""
import asyncio
import base64
import json
import os
import sys
import time
import urllib.request
import ssl
import uuid

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BASE)

# Obscura (Chrome CDP) é o renderizador da tipografia — a demo exige ele,
# então força OBSCURA_ENABLED=true ANTES de importar o bridge (lido no import).
os.environ["OBSCURA_ENABLED"] = "true"

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(_BASE, ".env"), override=False)

API_KEY = os.getenv("AGNES_API_KEY", "").strip()
AGNES_BASE = "https://apihub.agnes-ai.com"
OUT_DIR = os.path.join(_BASE, "outputs", "agnes")

# ── Branding Dezafira (globals.css do admin) ────────────────────────────────
INK = "#0f1a21"
PAPER = "#e8edf2"
DIM = "#7a97a8"
BLAZE = "#FF5B06"
BLAZE_HOVER = "#ff7833"


def _agnes_image(prompt: str, width: int = 1280, height: int = 720) -> str:
    """Gera o fundo com a Agnes (imagem 2.1 flash) e devolve a URL pública."""
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt[:1000],
        "size": "2K",
        "ratio": "16:9",
        "extra_body": {"response_format": "url"},
    }
    req = urllib.request.Request(
        AGNES_BASE + "/v1/images/generations",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as r:
        data = json.loads(r.read().decode())
    imgs = data.get("data") or []
    if not imgs or not imgs[0].get("url"):
        raise RuntimeError(f"Resposta Agnes sem URL: {json.dumps(data)[:300]}")
    return imgs[0]["url"]


def _fetch(url: str, dest: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as r:
        raw = r.read()
    with open(dest, "wb") as f:
        f.write(raw)


def _build_html(bg_url: str) -> str:
    """HTML da composição editorial com o branding Dezafira."""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"/>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  html,body{{width:1280px;height:720px;overflow:hidden}}
  body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;color:{PAPER};background:{INK}}}
  .stage{{position:relative;width:1280px;height:720px;background:url("{bg_url}") center/cover no-repeat}}
  .scrim{{position:absolute;inset:0;background:
    linear-gradient(100deg,rgba(10,16,22,.92) 0%,rgba(10,16,22,.62) 42%,rgba(10,16,22,.18) 68%,rgba(10,16,22,.35) 100%),
    linear-gradient(0deg,rgba(7,12,17,.85) 0%,transparent 22%)}}
  .grain{{position:absolute;inset:0;opacity:.5;mix-blend-mode:overlay;background-image:radial-gradient(rgba(255,255,255,.06) 1px,transparent 1px);background-size:3px 3px}}
  .logo{{position:absolute;top:42px;left:56px;display:flex;align-items:center;gap:14px}}
  .logo-mark{{width:46px;height:46px;border-radius:12px;background:linear-gradient(135deg,{BLAZE},{BLAZE_HOVER});display:flex;align-items:center;justify-content:center;font-weight:800;font-size:24px;color:{INK};box-shadow:0 8px 30px rgba(255,91,6,.45)}}
  .logo-word{{font-size:21px;font-weight:800;letter-spacing:.32em;color:{PAPER}}}
  .logo-sub{{font-size:10px;letter-spacing:.42em;color:{DIM};margin-top:2px}}
  .badge{{position:absolute;top:128px;left:56px;display:inline-flex;align-items:center;gap:9px;background:rgba(255,91,6,.14);border:1px solid rgba(255,91,6,.55);color:{BLAZE_HOVER};font-size:13px;font-weight:700;letter-spacing:.18em;padding:9px 18px;border-radius:999px;text-transform:uppercase}}
  .badge .dot{{width:8px;height:8px;border-radius:50%;background:{BLAZE};box-shadow:0 0 12px {BLAZE}}}
  .copy{{position:absolute;left:56px;top:196px;width:760px}}
  h1{{font-size:56px;line-height:1.08;font-weight:800;letter-spacing:-.01em;margin-bottom:22px}}
  h1 .accent{{color:transparent;background:linear-gradient(90deg,{BLAZE_HOVER},{BLAZE});-webkit-background-clip:text;background-clip:text}}
  .sub{{font-size:21px;line-height:1.55;color:{PAPER};opacity:.88;margin-bottom:36px;max-width:680px}}
  .cta-row{{display:flex;gap:16px;align-items:center}}
  .cta{{display:inline-flex;align-items:center;gap:10px;background:linear-gradient(135deg,{BLAZE},{BLAZE_HOVER});color:{INK};font-size:18px;font-weight:800;padding:16px 30px;border-radius:14px;box-shadow:0 14px 40px rgba(255,91,6,.4)}}
  .cta-ghost{{display:inline-flex;align-items:center;gap:10px;border:1.5px solid rgba(232,237,242,.4);color:{PAPER};font-size:17px;font-weight:700;padding:15px 26px;border-radius:14px}}
  .meta{{position:absolute;left:56px;bottom:30px;display:flex;gap:26px;font-size:12.5px;letter-spacing:.14em;color:{DIM};text-transform:uppercase}}
  .meta b{{color:{PAPER};font-weight:700}}
  .frame{{position:absolute;inset:0;pointer-events:none;border:1px solid rgba(232,237,242,.14)}}
</style>
</head>
<body>
  <div class="stage">
    <div class="scrim"></div>
    <div class="grain"></div>
    <div class="frame"></div>
    <div class="logo">
      <div class="logo-mark">D</div>
      <div>
        <div class="logo-word">DEZAFIRA</div>
        <div class="logo-sub">AI ECOSYSTEM</div>
      </div>
    </div>
    <span class="badge"><span class="dot"></span>Agnes AI · Fábrica Completa</span>
    <div class="copy">
      <h1>Do roteiro ao checkout.<br/>Tudo criado <span class="accent">por IA.</span></h1>
      <p class="sub">Ebooks, cursos, VSLs com voz, landings que vendem e capas de impacto — a Dezafira gera a receita inteira do seu produto, do conteúdo às imagens e ao vídeo.</p>
      <div class="cta-row">
        <div class="cta">COMECE AGORA →</div>
        <div class="cta-ghost">VER A DEMO</div>
      </div>
    </div>
    <div class="meta">
      <span><b>Dezafira Studio</b></span>
      <span>Gerado com <b>Agnes AI</b></span>
      <span>Imagem + Vídeo · agnes-video-v2.0</span>
    </div>
  </div>
</body>
</html>"""


async def _render_html_to_png(html: str, width: int, height: int) -> bytes:
    """Renderiza o HTML via Chrome CDP (ObscuraBridge), com fallback Pillow."""
    from services.obscura_bridge import ObscuraBridge

    data_url = "data:text/html;base64," + base64.b64encode(html.encode("utf-8")).decode("ascii")
    bridge = ObscuraBridge(timeout=30)
    try:
        connected = await bridge.connect()
        if not connected:
            raise RuntimeError("bridge.connect() falhou")
        await bridge.navigate(data_url, wait_until="load")
        await asyncio.sleep(1.2)
        png = await bridge.screenshot(width=width, height=height)
        if not png:
            raise RuntimeError("screenshot vazio")
        return png
    finally:
        await bridge.disconnect()


def _pillow_fallback(bg_path: str, out_path: str, width: int = 1280, height: int = 720) -> None:
    """Fallback: fundo + textos simples com Pillow (sem Chrome)."""
    from PIL import Image, ImageDraw, ImageFont

    bg = Image.open(bg_path).convert("RGB").resize((width, height))
    overlay = Image.new("RGBA", (width, height), (10, 16, 22, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(height):
        a = int(210 * (1 - i / height)) if i < height // 2 else 0
        d.line([(0, i), (width, i)], fill=(10, 16, 22, a))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(bg)
    try:
        f_big = ImageFont.truetype("arialbd.ttf", 52)
        f_mid = ImageFont.truetype("arial.ttf", 24)
        f_small = ImageFont.truetype("arial.ttf", 16)
    except Exception:  # noqa: BLE001
        f_big = f_mid = f_small = ImageFont.load_default()
    d.text((56, 120), "DEZAFIRA  ·  AI ECOSYSTEM", fill="#FF5B06", font=f_mid)
    d.text((56, 220), "Do roteiro ao checkout.", fill="#e8edf2", font=f_big)
    d.text((56, 290), "Tudo criado por IA.", fill="#e8edf2", font=f_big)
    d.text((56, 420), "Ebooks, cursos, VSLs, landings e capas — a receita inteira", fill="#c7d3dd", font=f_mid)
    d.text((56, 640), "Dezafira Studio · Gerado com Agnes AI", fill="#7a97a8", font=f_small)
    bg.save(out_path, "PNG")


async def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    slug = f"dezafira_brand_{stamp}"

    print("[1/3] Gerando fundo com Agnes AI (agnes-image-2.1-flash)...")
    prompt = (
        "Dark premium 3D abstract fintech ecosystem, deep teal navy background (#0f1a21) "
        "with vivid orange (#FF5B06) glowing light streaks and floating glass panels, "
        "particles of data, cinematic depth of field, soft bokeh, ultra detailed, "
        "high-end editorial, wide 16:9, darker area on the left side, no text, no letters"
    )
    bg_url = _agnes_image(prompt)
    print("      fundo:", bg_url[:100] + "...")

    bg_path = os.path.join(OUT_DIR, f"{slug}_bg.png")
    _fetch(bg_url, bg_path)

    print("[2/3] Compondo tipografia + copy (Chrome CDP)...")
    html = _build_html(bg_url)
    try:
        png = await _render_html_to_png(html, 1280, 720)
        out_path = os.path.join(OUT_DIR, f"{slug}.png")
        with open(out_path, "wb") as f:
            f.write(png)
        engine = "cdp"
    except Exception as e:  # noqa: BLE001
        print(f"      CDP falhou ({e}) — fallback Pillow")
        out_path = os.path.join(OUT_DIR, f"{slug}.png")
        _pillow_fallback(bg_path, out_path)
        engine = "pillow"

    print(f"[3/3] Salvo: outputs/agnes/{os.path.basename(out_path)} (engine={engine})")
    print("URL local : /outputs/agnes/" + os.path.basename(out_path))
    print("Fundo URL :", bg_url)


if __name__ == "__main__":
    asyncio.run(main())
