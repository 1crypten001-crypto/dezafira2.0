#!/usr/bin/env python3
"""Monta grade dos assets do Bidu e analisa com modelo de visão (OpenRouter).

Uso: python3 scripts/inspect_bidu_kit.py <assets_dir> [modelo]
"""
import base64
import io
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ASSETS = [
    "mascot-front.png", "mascot-happy.png", "mascot-thinking.png",
    "logo-icon.png", "logo-horizontal.png", "favicon.png", "og-image.png",
]

MODEL = "meta-llama/llama-3.2-11b-vision-instruct"


def build_grid(assets_dir: str, cols: int = 4, cell: int = 320) -> Image.Image:
    files = [f for f in ASSETS if os.path.exists(os.path.join(assets_dir, f))]
    rows = (len(files) + cols - 1) // cols
    W, H = cols * cell, rows * (cell + 28)
    grid = Image.new("RGB", (W, H), "#111111")
    draw = ImageDraw.Draw(grid)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for i, f in enumerate(files):
        r, c = divmod(i, cols)
        x, y = c * cell, r * (cell + 28)
        try:
            im = Image.open(os.path.join(assets_dir, f)).convert("RGB")
            im.thumbnail((cell - 16, cell - 16))
            ox, oy = x + 8 + (cell - 16 - im.width) // 2, y + 8 + (cell - 16 - im.height) // 2
            grid.paste(im, (ox, oy))
            draw.text((x + 8, y + cell - 2), f, fill="#ffffff", font=font)
        except Exception as e:
            draw.text((x + 8, y + 10), f"ERRO: {e}", fill="#ff5555", font=font)
    return grid


def to_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    assets_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    model = sys.argv[2] if len(sys.argv) > 2 else MODEL
    grid = build_grid(assets_dir)
    grid_path = os.path.join(assets_dir, "_grid_review.png")
    grid.save(grid_path)
    print(f"Grade salva: {grid_path} ({grid.width}x{grid.height})")

    import httpx

    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        print("OPENROUTER_API_KEY ausente — pulando análise (grade já salva).")
        return

    prompt = (
        "Estas são 7 imagens geradas por IA para o kit de identidade visual de um MiniApp "
        "('Calculadora Basica', mascote definido como robô azul acolhedor segurando um lápis, "
        "estilo Duolingo flat vector). Responda EM PORTUGUÊS, apenas com um JSON válido com estas chaves:\n"
        "{\"personagem_por_imagem\": {\"mascot-front.png\": \"descrição\", ...}, "
        "\"mesmo_personagem\": \"sim/nao + explicação curta\", "
        "\"cores_batem_paleta\": \"sim/nao + quais divergem\", "
        "\"melhor_imagem\": \"arquivo\", \"pior_imagem\": \"arquivo\", "
        "\"correcoes_prompt\": \"lista curta de ajustes\"}\n"
        "Não escreva nada além do JSON."
    )

    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": to_data_url(grid)}},
            ]},
        ],
        "max_tokens": 1200,
    }
    try:
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json=body,
            timeout=120,
        )
        if resp.status_code != 200:
            print(f"Análise falhou: HTTP {resp.status_code}: {resp.text[:300]}")
            return
        data = resp.json()
        print("\n" + "=" * 60)
        print(data["choices"][0]["message"]["content"])
        print("=" * 60)
    except Exception as e:
        print(f"Análise falhou: {e}")


if __name__ == "__main__":
    main()
