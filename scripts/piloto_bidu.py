#!/usr/bin/env python3
"""Piloto real do Agente Bidu — gera kit de identidade para um MiniApp real via Agnes AI.

Uso: python3 scripts/piloto_bidu.py <app_id>
Lê o record do app na API (X-Service-Key), monta o brand e chama BiduVisualAgent.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.bidu_visual import BiduVisualAgent


async def main(app_id: str) -> None:
    import httpx

    service_key = os.getenv("DEZAFIRA_SERVICE_KEY", "")
    base = "https://dezafiraadm-production.up.railway.app"
    headers = {"X-Service-Key": service_key} if service_key else {}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{base}/api/v1/miniapps/{app_id}", headers=headers)
        if resp.status_code != 200:
            print(f"ERRO: nao achei o app {app_id} (HTTP {resp.status_code})")
            sys.exit(1)
        app = resp.json()

    theme = {}
    if app.get("theme"):
        try:
            theme = json.loads(app["theme"])
        except Exception:
            theme = {}

    brand = {
        "brand_name": app.get("brand_name") or app.get("app_name") or "",
        "brand_voice": app.get("brand_voice") or "",
        "theme": theme,
        "header_symbol": theme.get("emoji", ""),
    }

    print(f"=== PILOTO BIDU ===")
    print(f"App: {app.get('app_name')} (slug: {app.get('slug')})")
    print(f"Dor: {app.get('pain')}")
    print(f"Paleta: {theme.get('primary')} / {theme.get('accent')}")
    print(f"AGNES_API_KEY: {'OK' if os.getenv('AGNES_API_KEY') else 'FALTANDO'}")
    print("Gerando kit (pode levar 2-4 min)...\n")

    agent = BiduVisualAgent()
    result = await agent.generate_assets(
        brand=brand,
        pain=app.get("pain") or "",
        app_name=app.get("app_name") or "",
        slug=app.get("slug") or "",
    )

    print(f"Provider: {result.get('provider')}")
    print(f"Assets dir: {result.get('assets_dir')}")
    print(f"logo_url: {result.get('logo_url')}")
    print(f"banner_url: {result.get('banner_url')}")
    print(f"favicon_url: {result.get('favicon_url')}")
    print(f"og_image_url: {result.get('og_image_url')}")
    print(f"Mascote: {json.dumps(result.get('mascot'), ensure_ascii=False)}")
    brief = result.get("character_brief") or {}
    print(f"\nCharacter brief: species={brief.get('species')} | color={brief.get('color')} "
          f"| emotion={brief.get('emotion')} | pose={brief.get('pose')}")

    out = result.get("assets_dir", "")
    if out and os.path.isdir(out):
        print(f"\nArquivos gerados:")
        for f in sorted(os.listdir(out)):
            size = os.path.getsize(os.path.join(out, f))
            print(f"  {f} ({size//1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/piloto_bidu.py <app_id>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
