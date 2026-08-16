"""Demo — Vídeo Agnes a partir da imagem de marca Dezafira (agnes-video-v2.0).

A imagem composta (fundo Agnes + tipografia/copy) é enviada como base64 no
campo `image` (a API aceita "public http(s) URL or valid base64 image data").
Faz polling até concluir e baixa o MP4 para outputs/vsl/.

Uso:
    .venv/Scripts/python scripts/agnes_video_demo.py <caminho_do_png>
"""
import asyncio
import glob
import os
import sys
import time

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BASE)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(_BASE, ".env"), override=True)

from modules.agnes_video import (  # noqa: E402
    agnes_video_generate_and_wait,
    agnes_download_video,
    image_to_base64,
)

OUT_DIR = os.path.join(_BASE, "outputs", "vsl")

PROMPT = (
    "Slow cinematic push-in with gentle parallax on a premium dark tech poster, "
    "subtle floating orange light particles and soft glow, smooth camera drift, "
    "high-end commercial motion design, typography stays sharp and stable, "
    "no text distortion, no warping, elegant and premium"
)


async def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    png = args[0] if args else sorted(
        f for f in glob.glob(os.path.join(_BASE, "outputs", "agnes", "dezafira_brand_*.png"))
        if not f.endswith("_bg.png")
    )[-1]
    print(f"[1/3] Imagem: {os.path.basename(png)}")
    b64 = image_to_base64(png)
    print(f"      base64: {len(b64)//1024} KB")

    def on_progress(st):
        print(f"      status={st.get('status')} progress={st.get('progress')}")

    print("[2/3] Enviando para agnes-video-v2.0 (image-to-video)...")
    result = await agnes_video_generate_and_wait(
        PROMPT, image=b64, poll_interval=10.0, timeout=900.0, on_progress=on_progress
    )
    if result.get("error"):
        print("ERRO:", result["error"])
        print("raw:", str(result.get("raw", ""))[:400])
        return
    url = result.get("url") or ""
    print("      status:", result.get("status"), "| url:", (url or "")[:90])

    print("[3/3] Baixando MP4...")
    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, f"dezafira_brand_{time.strftime('%Y%m%d_%H%M%S')}.mp4")
    saved = await agnes_download_video(url, dest)
    if saved:
        size_mb = os.path.getsize(dest) / 1024 / 1024
        print(f"Salvo: outputs/vsl/{os.path.basename(dest)} ({size_mb:.1f} MB)")
        print("URL local: /outputs/vsl/" + os.path.basename(dest))
        print("URL remota:", url)
    else:
        print("Falha ao baixar; URL remota:", url)


if __name__ == "__main__":
    asyncio.run(main())
