"""
Valida o render HTML → PNG REAL do Agnes Studio via Chrome (CDP).

Sobe um Chrome headless local com --remote-debugging-port, conecta pelo
ObscuraBridge.screenshot (mesmo caminho que o Agnes Studio usa em produção)
e gera uma capa de ponta a ponta, conferindo dimensões do PNG.

Uso:
    .venv/Scripts/python scripts/agnes_studio_render_check.py
    CHROME_PATH=/caminho/do/chrome .venv/Scripts/python scripts/agnes_studio_render_check.py
"""

import asyncio
import base64
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

# Garante que o root do projeto esteja no sys.path (script roda de scripts/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# O Agnes Studio conecta no Obscura via OBSCURA_HOST/OBSCURA_PORT — aponte
# para o Chrome local que este script sobe (mesmo caminho do Railway).
PORT = int(os.getenv("AGNES_CDP_PORT", "9333"))
os.environ.setdefault("OBSCURA_HOST", "127.0.0.1")
os.environ.setdefault("OBSCURA_PORT", str(PORT))
os.environ["OBSCURA_ENABLED"] = "true"
OUTPUTS_AGNES = os.path.join(_PROJECT_ROOT, "outputs", "agnes")


def find_chrome() -> str | None:
    candidates = [
        os.getenv("CHROME_PATH", ""),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def wait_debug(port: int, timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2):
                return True
        except Exception:
            time.sleep(0.5)
    return False


async def main() -> dict:
    from PIL import Image

    from modules.agnes_studio import AgnesStudio
    from services.obscura_bridge import ObscuraBridge

    # 1. Screenshot direto (HTML → PNG via CDP Page.captureScreenshot)
    bridge = ObscuraBridge(host="127.0.0.1", port=PORT, timeout=20)
    connected = await bridge.connect()
    if not connected:
        raise RuntimeError("ObscuraBridge não conectou no Chrome")
    html = ("<!doctype html><html><head><meta charset='utf-8'></head>"
            "<body style='margin:0;background:#0f172a;color:#f59e0b;"
            "font:bold 60px Georgia'><div style='padding:40px'>"
            "DEZAFIRA — TESTE HTML→PNG</div></body></html>")
    data_url = "data:text/html;base64," + base64.b64encode(html.encode("utf-8")).decode("ascii")
    await bridge.navigate(data_url, wait_until="load")
    await asyncio.sleep(0.8)
    png = await bridge.screenshot(width=800, height=400)
    img = Image.open(io.BytesIO(png))
    print(f"[1] screenshot direto: OK ({len(png)} bytes, {img.size})")
    assert img.size == (800, 400), f"dimensão inesperada: {img.size}"
    await bridge.disconnect()

    # 2. Capa real de ponta a ponta (mesmo caminho dos endpoints /agnes-cover)
    studio = AgnesStudio()
    res = await studio.generate_course_cover(
        title="Curso Render Real",
        subtitle="Validacao HTML → PNG via Chrome CDP",
        niche="Teologia",
        style_id="elegante",
        course_id="crs_render_check",
    )
    fp = os.path.join(studio.outputs_dir, res["filename"])
    img2 = Image.open(fp)
    print(f"[2] capa real: OK {res['filename']} {img2.size} provider={res['provider']}")
    assert img2.size == (1280, 720), f"dimensão da capa inesperada: {img2.size}"
    return res


if __name__ == "__main__":
    chrome = find_chrome()
    if not chrome:
        print("❌ Chrome/Edge não encontrado. Defina CHROME_PATH para o executável.")
        sys.exit(2)

    user_data = tempfile.mkdtemp(prefix="agnes_chrome_")
    proc = subprocess.Popen(
        [chrome, "--headless=new", f"--remote-debugging-port={PORT}",
         f"--user-data-dir={user_data}", "--no-first-run",
         "--no-default-browser-check", "--disable-gpu", "--disable-extensions",
         "--disable-background-networking", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    result = None
    try:
        if not wait_debug(PORT):
            raise SystemExit("❌ Chrome não respondeu no endpoint de debug (CDP)")
        result = asyncio.run(main())
        print("[OK] RENDER HTML->PNG REAL VALIDADO -", result["cover_url"])
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        shutil.rmtree(user_data, ignore_errors=True)
        if result:
            try:
                os.remove(os.path.join(OUTPUTS_AGNES, result["filename"]))
            except Exception:
                pass
