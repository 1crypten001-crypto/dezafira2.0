#!/usr/bin/env python3
"""Teste de img2img da Agnes: a referência segura o personagem? E a cor?

Gera uma base (robô azul), depois variações com a base como ref, com e sem
parâmetro de strength, e com cor em texto vs hex.
"""
import asyncio
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

BASE = "https://apihub.agnes-ai.com/v1"
MODEL = "agnes-image-2.1-flash"


async def gen(client: httpx.AsyncClient, key: str, prompt: str, refs: list[str] | None = None,
              extra: dict | None = None, tag: str = "x") -> None:
    body = {"model": MODEL, "prompt": prompt[:4000], "size": "1024x1024", "ratio": "1:1"}
    if refs:
        body["image"] = refs
    if extra:
        body.update(extra)
    try:
        r = await client.post(f"{BASE}/images/generations", headers={"Authorization": f"Bearer {key}"}, json=body, timeout=180)
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
            print(f"{tag}: HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"{tag}: ERRO {e}")


async def main() -> None:
    key = os.getenv("AGNES_API_KEY", "")
    if not key:
        print("AGNES_API_KEY ausente"); return
    async with httpx.AsyncClient(timeout=180) as client:
        # 1) Base: robô azul (cor em TEXTO, sem hex)
        await gen(client, key,
                  "flat vector mascot, big expressive eyes, one accent color, white background, "
                  "Duolingo-style, no text, no watermark | a friendly BLUE robot mascot, "
                  "round head, determined expression, holding a pencil, for 'Calculadora Basica'",
                  tag="base_blue")

        # 2) Variação happy COM ref + strength alto
        base_path = "/tmp/agnes_test_base_blue.png"
        if os.path.exists(base_path):
            with open(base_path, "rb") as fh:
                ref = "data:image/png;base64," + base64.b64encode(fh.read()).decode()
            await gen(client, key,
                      "same character, happy joyful expression, celebrating, flat vector, white background",
                      refs=[ref], tag="happy_ref")
            await gen(client, key,
                      "same character, happy joyful expression, celebrating, flat vector, white background",
                      refs=[ref], extra={"image_strength": 0.85}, tag="happy_strength")
            await gen(client, key,
                      "same character, thinking curious expression, pondering, flat vector, white background",
                      refs=[ref], extra={"strength": 0.9}, tag="thinking_strength2")
        else:
            print("base não gerada — pulando variações")


if __name__ == "__main__":
    asyncio.run(main())
