"""
ObscuraClient — Cliente real do motor Obscura (substitui o stub).

Todos os spiders/agentes devem usar este cliente como porta de entrada
única para navegação e scraping. Ele:

  1. Tenta usar o Obscura real (via ObscuraBridge/CDP) se disponível;
  2. Registra telemetria em services.obscura_service (página 🕵️ Obscura);
  3. Cai em fallback (urllib + cookie CONSENT) se o motor estiver offline,
     para nunca quebrar as pipelines.

Uso (compatível com o padrão atual dos spiders):
    html = await asyncio.to_thread(obscura_client.fetch_html, url, "networkidle0", 30, True)
"""

import asyncio
import os
import time
from urllib.parse import quote

from services.obscura_service import obscura_telemetry

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _obscura_enabled() -> bool:
    return os.getenv("OBSCURA_ENABLED", "true").lower() in ("true", "1", "yes")


class ObscuraClient:
    """Cliente real do Obscura com telemetria e fallback seguro."""

    def __init__(self, agent: str = "obscura"):
        self.agent = agent

    # ─── CORE: fetch_html (compatível com spiders existentes) ────────────

    def fetch_html(self, url: str, wait_until: str = "networkidle0",
                   timeout: int = 30, stealth: bool = True) -> str:
        """Busca o HTML renderizado de uma URL.

        Síncrono (roda o loop interno) para ser chamado via asyncio.to_thread
        pelos spiders. Usa Obscura real quando disponível; fallback urllib.
        Falhas transitórias (rede/timeout/resultado vazio) são re-tentadas
        2x com backoff exponencial (1.5s, 3.0s) antes de contar como falha
        na telemetria.

        ⚠️ Chame SEMPRE via asyncio.to_thread — este método roda asyncio.run()
        internamente e levantaria RuntimeError se chamado dentro de um event
        loop já em execução.
        """
        started = time.perf_counter()
        ok = False
        error = ""
        html = ""
        via = ""
        max_attempts = 3  # 1 tentativa + 2 retries

        for attempt in range(max_attempts):
            try:
                if _obscura_enabled():
                    html = self._fetch_via_bridge(url, wait_until, timeout)
                if not html:
                    html = self._fallback_urllib(url, timeout)
                    ok = bool(html)
                    error = "" if ok else "fallback vazio"
                    via = "fallback" if ok else ""
                else:
                    ok = True
                    via = "bridge"
            except Exception as e:
                error = str(e)[:300]
                print(f"[ObscuraClient] Erro em fetch_html (tentativa {attempt + 1}/{max_attempts}): {error}")
                html = ""

            if ok:
                break

            # Falha transitória → retry com backoff exponencial (1.5s, 3.0s)
            if attempt < max_attempts - 1:
                obscura_telemetry.log_retry(self.agent)
                wait = 1.5 * (2 ** attempt)
                print(f"[ObscuraClient] Retry em {wait:.1f}s (tentativa {attempt + 1}/{max_attempts})...")
                time.sleep(wait)

        ms = int((time.perf_counter() - started) * 1000)
        obscura_telemetry.log_call(self.agent, url, ok, ms, error, via=via)
        return html

    def fetch_markdown(self, url: str, wait_until: str = "networkidle0",
                       timeout: int = 30) -> str:
        """Busca a página e retorna markdown limpo (via Obscura nativo).
        Também com retry 2x + backoff exponencial (1.5s, 3.0s)."""
        started = time.perf_counter()
        ok = False
        error = ""
        md = ""
        via = ""
        max_attempts = 3  # 1 tentativa + 2 retries

        for attempt in range(max_attempts):
            try:
                if _obscura_enabled():
                    md = self._fetch_markdown_via_bridge(url, wait_until, timeout)
                if not md:
                    html = self._fallback_urllib(url, timeout)
                    md = self._html_to_text(html)
                    ok = bool(md)
                    via = "fallback" if ok else ""
                else:
                    ok = True
                    via = "bridge"
            except Exception as e:
                error = str(e)[:300]
                md = ""

            if ok:
                break

            if attempt < max_attempts - 1:
                obscura_telemetry.log_retry(self.agent)
                wait = 1.5 * (2 ** attempt)
                print(f"[ObscuraClient] Retry markdown em {wait:.1f}s (tentativa {attempt + 1}/{max_attempts})...")
                time.sleep(wait)

        ms = int((time.perf_counter() - started) * 1000)
        obscura_telemetry.log_call(self.agent, url, ok, ms, error, via=via)
        return md

    # ─── BRIDGE (Obscura real) ───────────────────────────────────────────

    def _fetch_via_bridge(self, url: str, wait_until: str, timeout: int) -> str:
        """Navega com o Obscura real e retorna o HTML renderizado."""
        from services.obscura_bridge import ObscuraBridge

        async def _run():
            bridge = ObscuraBridge(timeout=timeout)
            try:
                connected = await bridge.connect()
                if not connected:
                    return ""
                await bridge.navigate(url, wait_until=wait_until)
                html = await bridge.get_html()
                await bridge.disconnect()
                return html or ""
            except Exception as e:
                print(f"[ObscuraClient] Bridge falhou: {e}")
                try:
                    await bridge.disconnect()
                except Exception:
                    pass
                return ""

        return asyncio.run(_run())

    def _fetch_markdown_via_bridge(self, url: str, wait_until: str, timeout: int) -> str:
        from services.obscura_bridge import ObscuraBridge

        async def _run():
            bridge = ObscuraBridge(timeout=timeout)
            try:
                connected = await bridge.connect()
                if not connected:
                    return ""
                await bridge.navigate(url, wait_until=wait_until)
                md = await bridge.get_markdown_native()
                await bridge.disconnect()
                return md or ""
            except Exception as e:
                print(f"[ObscuraClient] Bridge markdown falhou: {e}")
                try:
                    await bridge.disconnect()
                except Exception:
                    pass
                return ""

        return asyncio.run(_run())

    # ─── FALLBACK ────────────────────────────────────────────────────────

    def _fallback_urllib(self, url: str, timeout: int) -> str:
        """Fallback sem Obscura: urllib + cookie CONSENT (evita consentimento)."""
        import urllib.request
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": DEFAULT_UA,
                # Cookie CONSENT evita a página de consentimento do YouTube/Google
                "Cookie": "CONSENT=YES+cb.20210328-17-p0.en+FX+417",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[ObscuraClient] Fallback urllib falhou: {e}")
            return ""

    @staticmethod
    def _html_to_text(html: str) -> str:
        """Conversão simples HTML -> texto (fallback de markdown)."""
        import re
        html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<[^>]+>", " ", html)
        html = re.sub(r"\s+", " ", html)
        return html.strip()[:50000]


# Instância padrão usada por todos os spiders
obscura_client = ObscuraClient()
