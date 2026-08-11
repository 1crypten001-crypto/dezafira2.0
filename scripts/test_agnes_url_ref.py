#!/usr/bin/env python3
"""Teste B: img2img da Agnes com URL pública (catbox) em vez de data URL.

Hipótese: o parâmetro image[] com data URL base64 é ignorado (o modelo pega
só o texto), e por isso o personagem muda. URL pública testa o caminho real.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE = "https://apihub.agnes-ai.com/v1"
MODEL = "agnes-image-2.1-flash"


async def upload_catbox(client: httpx.AsyncClient, path: str) -> str:
    with open(path, "rb") as fh:
        files = {"fileToUpload": (os.path.basename(path), fh, "image/png")}
        data = {"reqtype": "fileupload"}
        r = await client.post("https://catbox.moe/user/api.php", data=data, files=files, timeout=120)
    url = r.text.strip()
    print(f"  upload: {url}")
    return url


async def gen(client: httpx.AsyncClient, key: str, prompt: str, refs: list[str] | None,
              extra: dict | None, tag: str) -> None:
    body = {"model": MODEL, "prompt": prompt[:4000], "size": "1024x1024", "ratio": "1:1"}
    if refs:
        body["image"] = refs
    if extra:
        body.update(extra)
    try:
        r = await client.post(f"{BASE}/images/generations",
                              headers={"Authorization": f"Bearer {key}"}, json=body, timeout=180)
        if r.status_code == 200:
            data = r.json()
            url = None
            for k in ("url", "urls", "image", "image_url", "data"):
                v = data.get(k)
                if isinstance(v, str) and v.startswith("http"):
                    url = v; break
                if isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict) and it.get("url"):
                            url = it["url"]; break
                    if url: break
            if url:
                img = await client.get(url, timeout=120)
                path = f"/tmp/agnes_test_{tag}.png"
                with open(path, "wb") as fh:
                    fh.write(img.content)
                print(f"{tag}: OK -> {path} ({len(img.content)//1024} KB)")
            else:
                print(f"{tag}: 200 sem URL: {str(data)[:200]}")
        else:
            print(f"{tag}: HTTP {r.status_code}: {r.text[:250]}")
    except Exception as e:
        print(f"{tag}: ERRO {e}")


async def main() -> None:
    key = os.getenv("AGNES_API_KEY", "")
    if not key:
        print("AGNES_API_KEY ausente"); return
    async with httpx.AsyncClient(timeout=180) as client:
        base_path = "/tmp/agnes_test_base_blue.png"
        if not os.path.exists(base_path):
            print("base não existe — rode test_agnes_img2img.py primeiro"); return
        print("Upload da base para catbox...")
        public_url = await upload_catbox(client, base_path)

        # Variação com URL pública
        await gen(client, key,
                  "same exact character design, happy joyful expression, celebrating, "
                  "flat vector mascot, big eyes, white background, no text",
                  refs=[public_url], extra=None, tag="B_happy_url")

        # Variação com URL pública + prompt reforçando ROBÔ AZUL
        await gen(client, key,
                  "the SAME BLUE ROBOT mascot as the reference image, do not change the species, "
                  "happy joyful expression, celebrating, flat vector, white background, no text",
                  refs=[public_url], extra=None, tag="B_happy_url_restrito")

        # Variação com base64 E prompt restrito (controle)
        import base64 as b64
        with open(base_path, "rb") as fh:
            data_url = "data:image/png;base64," + b64.b64encode(fh.read()).decode()
        await gen(client, key,
                  "the SAME BLUE ROBOT mascot as the reference image, do not change the species, "
                  "thinking curious expression, flat vector, white background, no text",
                  refs=[data_url], extra=None, tag="B_thinking_b64_restrito")


if __name__ == "__main__":
    asyncio.run(main())
