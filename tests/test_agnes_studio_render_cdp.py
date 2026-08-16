"""Teste do render HTML → PNG REAL via Chrome (CDP).

Sobe um Chrome headless local (--remote-debugging-port), valida o
ObscuraBridge.screenshot (dimensões exatas via clip) e gera uma capa real
do Agnes Studio de ponta a ponta. Pula automaticamente quando não há
Chrome/Edge no sistema (ou defina CHROME_PATH).

Uso:
    .venv/Scripts/python -m pytest tests/test_agnes_studio_render_cdp.py -q
"""

import asyncio
import base64
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request

import pytest

import io


def _find_chrome():
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


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _wait_debug(port: int, timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2):
                return True
        except Exception:
            time.sleep(0.4)
    return False


CHROME = _find_chrome()
pytestmark = pytest.mark.skipif(
    CHROME is None,
    reason="Chrome/Edge não encontrado (defina CHROME_PATH para rodar o teste CDP)",
)


@pytest.fixture(scope="module")
def chrome_cdp():
    """Sobe um Chrome headless com CDP e mata ao final."""
    port = _free_port()
    user_data = tempfile.mkdtemp(prefix="agnes_test_chrome_")
    proc = subprocess.Popen(
        [CHROME, "--headless=new", f"--remote-debugging-port={port}",
         f"--user-data-dir={user_data}", "--no-first-run",
         "--no-default-browser-check", "--disable-gpu", "--disable-extensions",
         "--disable-background-networking", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    assert _wait_debug(port), "Chrome não respondeu no endpoint de debug (CDP)"
    yield port
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    shutil.rmtree(user_data, ignore_errors=True)


async def _connect_with_retry(bridge, tries: int = 4):
    """Chrome pode recusar conexões transitoriamente logo após subir (WinError 1225)."""
    for _ in range(tries):
        if await bridge.connect():
            return True
        await asyncio.sleep(1.0)
    return False


def test_screenshot_cdp_dimensoes_exatas(chrome_cdp):
    """Page.captureScreenshot com clip → PNG exatamente em width×height."""
    from services.obscura_bridge import ObscuraBridge

    async def run():
        bridge = ObscuraBridge(host="127.0.0.1", port=chrome_cdp, timeout=20)
        ok = await _connect_with_retry(bridge)
        assert ok, "bridge não conectou"
        try:
            html = ("<!doctype html><html><body style='margin:0;background:#0f172a;"
                    "color:#f59e0b;font:bold 60px Georgia'><div style='padding:40px'>"
                    "DEZAFIRA — CDP TESTE</div></body></html>")
            data_url = "data:text/html;base64," + base64.b64encode(html.encode("utf-8")).decode("ascii")
            await bridge.navigate(data_url, wait_until="load")
            await asyncio.sleep(0.6)
            png = await bridge.screenshot(width=800, height=400)
            assert png[:8] == b"\x89PNG\r\n\x1a\n"
            from PIL import Image
            img = Image.open(io.BytesIO(png))
            try:
                assert img.size == (800, 400), f"dimensão inesperada: {img.size}"
            finally:
                img.close()
        finally:
            await bridge.disconnect()

    asyncio.run(run())


def test_capa_real_agnes_via_chrome(chrome_cdp, monkeypatch):
    """Gera uma capa real do Agnes Studio pelo caminho Obscura (HTML→PNG)."""
    import services.obscura_bridge as bridge_mod

    # Aponta o default do bridge (usado por _render_via_obscura) pro Chrome local
    monkeypatch.setattr(bridge_mod, "OBSCURA_HOST", "127.0.0.1")
    monkeypatch.setattr(bridge_mod, "OBSCURA_PORT", chrome_cdp)
    monkeypatch.setenv("OBSCURA_ENABLED", "true")

    from modules.agnes_studio import AgnesStudio
    from PIL import Image

    async def run():
        studio = AgnesStudio()
        res = await studio.generate_course_cover(
            title="Curso CDP Teste", subtitle="Render real via Chrome",
            niche="Teologia", style_id="elegante", course_id="crs_cdp_test",
        )
        return res

    res = asyncio.run(run())
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "agnes")
    fp = os.path.join(out_dir, res["filename"])
    try:
        assert os.path.isfile(fp), "capa não foi salva"
        img = Image.open(fp)
        try:
            assert img.size == (1280, 720), f"dimensão da capa inesperada: {img.size}"
        finally:
            img.close()  # libera o handle antes do remove (Windows)
    finally:
        try:
            os.remove(fp)
        except Exception:
            pass
