"""
ObscuraBridge — Integração com o motor headless Obscura.

Obscura é um headless browser engine em Rust (~30MB RAM).
Repo: https://github.com/h4ckf0r0day/obscura
Licença: Apache 2.0

Funcionalidades:
  - Conexão via Chrome DevTools Protocol (CDP) WebSocket
  - Navegação em páginas JavaScript-heavy
  - Execução de JavaScript na página
  - Extração de HTML renderizado
  - Fallback automático se Obscura não estiver disponível

Uso:
    bridge = ObscuraBridge()
    async with bridge:
        html = await bridge.navigate_and_get_html("https://google.com/search?q=teste")
        # ou
        result = await bridge.execute_js("document.title")

Configuração via env vars:
  OBSCURA_HOST=127.0.0.1 (default)
  OBSCURA_PORT=9222 (default)
  OBSCURA_ENABLED=true (default)
"""

import asyncio
import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger("obscura")

# Configuração via env vars
OBSCURA_HOST = os.getenv("OBSCURA_HOST", "127.0.0.1")
OBSCURA_PORT = int(os.getenv("OBSCURA_PORT", "9222"))
OBSCURA_ENABLED = os.getenv("OBSCURA_ENABLED", "true").lower() in ("true", "1", "yes")
OBSCURA_WS_URL = f"ws://{OBSCURA_HOST}:{OBSCURA_PORT}/devtools/browser"


class ObscuraNotAvailableError(Exception):
    """Obscura não está disponível ou não respondeu."""
    pass


class ObscuraBridge:
    """
    Bridge para o Obscura headless browser via CDP.

    Gerencia conexão WebSocket, envia comandos CDP,
    e fornece métodos de alto nível para scraping.
    """

    def __init__(self, host: str = None, port: int = None,
                 enabled: bool = None, timeout: int = 15):
        self.host = host or OBSCURA_HOST
        self.port = port or OBSCURA_PORT
        self.enabled = enabled if enabled is not None else OBSCURA_ENABLED
        self.timeout = timeout
        self.ws_url = f"ws://{self.host}:{self.port}/devtools/browser"
        self._ws = None
        self._target_id = None
        self._session_id = None
        self._message_id = 0
        self._pending_responses = {}
        self._connected = False

    # ─── CONTEXT MANAGER ───────────────────────────────────────────────

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()

    # ─── CONEXÃO ───────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """Tenta conectar ao Obscura via WebSocket CDP."""
        if not self.enabled:
            logger.info("[Obscura] Desabilitado via OBSCURA_ENABLED=false")
            return False

        if self._connected:
            return True

        try:
            import websockets

            logger.info(f"[Obscura] Conectando a {self.ws_url}...")
            self._ws = await asyncio.wait_for(
                websockets.connect(self.ws_url, max_size=10_000_000),
                timeout=5,
            )
            self._connected = True

            # Pega o target da página (cria uma nova página)
            result = await self._send_cdp("Target.getTargets")
            targets = result.get("targetInfos", [])
            logger.info(f"[Obscura] Conectado! Targets encontrados: {len(targets)}")

            # Se não houver target, cria um
            if not targets:
                result = await self._send_cdp("Target.createTarget", {
                    "url": "about:blank",
                })
                self._target_id = result.get("targetId")
            else:
                self._target_id = targets[0].get("targetId")

            # Comandos de página exigem uma SESSÃO CDP anexada ao target
            # (sem isso o motor responde "No page for session").
            try:
                attach = await self._send_cdp("Target.attachToTarget", {
                    "targetId": self._target_id,
                    "flatten": True,
                })
                self._session_id = attach.get("sessionId")
                logger.info(f"[Obscura] Sessão anexada ao target: {self._session_id}")
            except Exception as e:
                logger.warning(f"[Obscura] Sem sessão anexada (fallback direto): {e}")
                self._session_id = None

            logger.info(f"[Obscura] Usando target: {self._target_id}")
            return True

        except ImportError:
            logger.warning("[Obscura] websockets não instalado. pip install websockets")
            return False
        except asyncio.TimeoutError:
            logger.warning(f"[Obscura] Timeout ao conectar em {self.ws_url}")
            return False
        except Exception as e:
            logger.warning(f"[Obscura] Não disponível: {e}")
            return False

    async def disconnect(self):
        """Fecha a conexão WebSocket."""
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
        self._ws = None
        self._connected = False
        self._target_id = None
        self._session_id = None
        logger.info("[Obscura] Desconectado")

    # ─── COMANDOS CDP ──────────────────────────────────────────────────

    async def _send_cdp(self, method: str, params: dict = None,
                        session_id: str = None) -> dict:
        """Envia um comando CDP e retorna a resposta.

        Comandos de página (Page.*, Runtime.*, DOM.*, LP.*) devem ser
        roteados com session_id da sessão anexada ao target.
        """
        if not self._ws:
            raise ObscuraNotAvailableError("WebSocket não conectado")

        self._message_id += 1
        msg_id = self._message_id

        message = {
            "id": msg_id,
            "method": method,
            "params": params or {},
        }
        if session_id:
            message["sessionId"] = session_id

        await self._ws.send(json.dumps(message))

        # Aguarda resposta
        while True:
            response = await asyncio.wait_for(
                self._ws.recv(),
                timeout=self.timeout,
            )
            data = json.loads(response)

            if "id" in data and data["id"] == msg_id:
                if "error" in data:
                    raise RuntimeError(
                        f"CDP error [{method}]: {data['error']}"
                    )
                return data.get("result", {})
            elif "method" in data:
                # Evento não solicitado — ignora
                continue

    async def _send_cdp_to_target(self, method: str, params: dict = None) -> dict:
        """Envia comando CDP para a página, usando a sessão anexada."""
        return await self._send_cdp(method, params, session_id=self._session_id)

    # ─── NAVEGAÇÃO ─────────────────────────────────────────────────────

    async def navigate(self, url: str, wait_until: str = "networkidle") -> dict:
        """
        Navega para uma URL e espera carregar.

        Args:
            url: URL para navegar
            wait_until: "load", "domcontentloaded", "networkidle"

        Returns:
            dict com status da navegação
        """
        if not self._connected:
            raise ObscuraNotAvailableError("Obscura não conectado")

        # Navega (comandos de página vão pela sessão anexada)
        result = await self._send_cdp_to_target("Page.enable")
        result = await self._send_cdp_to_target("Page.navigate", {"url": url})

        # Aguarda carregamento
        if wait_until == "networkidle":
            await asyncio.sleep(3)  # Aguarda rede estabilizar
        elif wait_until == "load":
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)

        return result

    async def get_html(self) -> str:
        """Retorna o HTML completo da página atual."""
        if not self._connected:
            raise ObscuraNotAvailableError("Obscura não conectado")

        result = await self._send_cdp_to_target("DOM.getDocument", {"depth": -1})
        node_id = result.get("root", {}).get("nodeId")

        if node_id:
            result = await self._send_cdp_to_target("DOM.getOuterHTML", {
                "nodeId": node_id,
            })
            return result.get("outerHTML", "")

        # Fallback: via JavaScript
        return await self.execute_js("document.documentElement.outerHTML")

    async def execute_js(self, script: str) -> str:
        """
        Executa JavaScript na página e retorna o resultado como string.
        """
        if not self._connected:
            raise ObscuraNotAvailableError("Obscura não conectado")

        result = await self._send_cdp_to_target("Runtime.evaluate", {
            "expression": script,
            "returnByValue": True,
        })

        if "result" in result:
            value = result["result"].get("value")
            if value is not None:
                return str(value)
            # Se não tem value, pode ser um objeto — tenta serializar
            if "objectId" in result["result"]:
                props = await self._send_cdp_to_target("Runtime.getProperties", {
                    "objectId": result["result"]["objectId"],
                    "ownProperties": True,
                })
                return json.dumps(props.get("result", []), ensure_ascii=False)

        return ""

    async def get_markdown_native(self) -> str:
        """Extrai markdown via método CDP nativo do Obscura (LP.getMarkdown).
        Se o motor não suportar, cai no get_markdown JS."""
        if not self._connected:
            raise ObscuraNotAvailableError("Obscura não conectado")
        try:
            result = await self._send_cdp_to_target("LP.getMarkdown")
            if result:
                md = result.get("markdown") or result.get("text") or ""
                if md:
                    return str(md)
        except Exception:
            pass
        return await self.get_markdown()

    async def get_markdown(self) -> str:
        """Tenta extrair conteúdo como Markdown (se Obscura suportar)."""
        try:
            return await self.execute_js("""
                (() => {
                    // Simple HTML to Markdown converter inline
                    const article = document.querySelector('article') ||
                                    document.querySelector('[role="main"]') ||
                                    document.body;
                    const clone = article.cloneNode(true);
                    // Remove scripts, styles, nav
                    clone.querySelectorAll('script, style, nav, footer, header').forEach(el => el.remove());
                    let text = clone.innerText || clone.textContent || '';
                    return text.trim().substring(0, 50000);
                })()
            """)
        except Exception:
            return await self.get_html()

    # ─── INTERAÇÃO COM A PÁGINA (DOM) ───────────────────────────────────

    async def click(self, selector: str) -> bool:
        """Clica no primeiro elemento que casa com o seletor CSS."""
        script = (
            "(() => {"
            f"  const el = document.querySelector({json.dumps(selector)});"
            "  if(!el) return 'NOT_FOUND';"
            "  el.click();"
            "  return 'OK';"
            "})()"
        )
        res = await self.execute_js(script)
        return res == "OK"

    async def type_text(self, selector: str, text: str) -> bool:
        """Digita texto em um input/textarea (dispara eventos reais)."""
        script = (
            "(() => {"
            f"  const el = document.querySelector({json.dumps(selector)});"
            "  if(!el) return 'NOT_FOUND';"
            "  el.focus();"
            "  const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;"
            "  const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;"
            f"  setter.call(el, {json.dumps(text)});"
            "  el.dispatchEvent(new Event('input', {bubbles:true}));"
            "  el.dispatchEvent(new Event('change', {bubbles:true}));"
            "  return 'OK';"
            "})()"
        )
        res = await self.execute_js(script)
        return res == "OK"

    async def wait_for_selector(self, selector: str, timeout: float = 10.0) -> bool:
        """Espera o elemento aparecer na página (polling via JS)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            res = await self.execute_js(
                f"!!document.querySelector({json.dumps(selector)})"
            )
            if str(res).strip().lower() in ("true", "1"):
                return True
            await asyncio.sleep(0.3)
        return False

    async def get_status(self) -> dict:
        """Status do motor: conectado, targets/sessões ativas e URL."""
        status = {
            "connected": bool(self._connected),
            "ws_url": self.ws_url,
            "targets": 0,
        }
        if self._connected:
            try:
                result = await self._send_cdp("Target.getTargets")
                status["targets"] = len(result.get("targetInfos", []))
            except Exception:
                pass
        return status

    # ─── MÉTODOS DE ALTO NÍVEL ─────────────────────────────────────────

    async def navigate_and_get_html(self, url: str) -> tuple:
        """
        Navega para URL e retorna (html, markdown).

        Método principal usado pelo KeywordMiner.
        Retorna tupla (html_completo, texto_limpo).
        """
        try:
            await self.navigate(url)
            html = await self.get_html()
            text = await self.get_markdown()
            return html, text
        except Exception as e:
            logger.error(f"[Obscura] Erro ao navegar para {url}: {e}")
            return "", ""

    async def get_serp_data(self, keyword: str, lang: str = "pt") -> dict:
        """
        Método especializado para extrair dados SERP do Google.

        Retorna dict com:
          - html: HTML completo da SERP
          - text: Texto limpo
          - urls: Lista de URLs dos resultados
          - paas: Perguntas do People Also Ask
          - search_url: URL da busca
        """
        from urllib.parse import quote

        search_url = (
            f"https://www.google.com/search?q={quote(keyword)}"
            f"&hl={'pt-BR' if lang == 'pt' else 'en'}"
        )

        html, text = await self.navigate_and_get_html(search_url)

        # Extrai URLs dos resultados via JS (mais confiável que regex)
        urls_json = await self.execute_js("""
            (() => {
                const links = Array.from(document.querySelectorAll('a[href^="/url?"]'));
                return JSON.stringify(links.map(a => {
                    const u = new URLSearchParams(a.getAttribute('href').split('?')[1]);
                    return u.get('q') || a.href;
                }).filter(Boolean));
            })()
        """)

        urls = []
        try:
            urls = json.loads(urls_json) if urls_json else []
        except json.JSONDecodeError:
            pass

        # Extrai PAA via JS
        paas_json = await self.execute_js("""
            (() => {
                const questions = [];
                // Tenta vários seletores do Google
                const selectors = [
                    '[data-q]',
                    '.related-question-pair',
                    '[jsname="CPKxLb"]',
                    '.gL9Hy',
                    '[role="heading"][aria-level="2"]',
                    '[role="heading"][aria-level="3"]',
                    // Blocos de PAA
                    '.wWOJcd',
                    'div[jsname] span[style]',
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        const text = el.textContent?.trim();
                        if (text && text.length > 5 && !questions.includes(text)) {
                            questions.push(text);
                        }
                    });
                });
                return JSON.stringify(questions.slice(0, 10));
            })()
        """)

        paas = []
        try:
            paas = json.loads(paas_json) if paas_json else []
        except json.JSONDecodeError:
            pass

        return {
            "html": html,
            "text": text[:10000],
            "urls": urls,
            "people_also_ask": paas,
            "search_url": search_url,
            "source": "obscura",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFICAÇÃO DE DISPONIBILIDADE
# ═══════════════════════════════════════════════════════════════════════════════

async def get_obscura_status(host: str = None, port: int = None) -> dict:
    """Verifica se o Obscura está rodando e retorna status detalhado."""
    bridge = ObscuraBridge(host=host, port=port)
    try:
        connected = await bridge.connect()
        if not connected:
            return {
                "online": False,
                "ws_url": bridge.ws_url,
                "targets": 0,
                "error": "Não conectou (binário parado ou OBSCURA_ENABLED=false)",
            }
        status = await bridge.get_status()
        await bridge.disconnect()
        return {
            "online": True,
            "ws_url": status["ws_url"],
            "targets": status["targets"],
        }
    except Exception as e:
        return {"online": False, "ws_url": bridge.ws_url, "targets": 0, "error": str(e)[:200]}


async def is_obscura_available(host: str = None, port: int = None) -> bool:
    """Verifica se o Obscura está rodando e acessível."""
    bridge = ObscuraBridge(host=host, port=port)
    try:
        result = await bridge.connect()
        if result:
            await bridge.disconnect()
        return result
    except Exception:
        return False


async def get_serp_with_fallback(keyword: str, lang: str = "pt") -> dict:
    """
    Tenta usar Obscura para SERP data. Se falhar, retorna dict vazio
    para que o KeywordMiner use o fallback regex.

    Esta é a função principal usada pelo KeywordMiner (PAA + dificuldade SERP).
    """
    from services.obscura_service import obscura_telemetry
    import time as _t

    started = _t.perf_counter()
    ok = False
    error = ""
    data = {}
    bridge = ObscuraBridge()
    try:
        connected = await bridge.connect()
        if connected:
            data = await bridge.get_serp_data(keyword, lang)
            await bridge.disconnect()
            ok = bool(data)
            error = "" if ok else "serp vazio"
        else:
            error = "nao conectado"
    except Exception as e:
        logger.warning(f"[Obscura] Fallback acionado: {e}")
        error = str(e)[:200]
        try:
            await bridge.disconnect()
        except Exception:
            pass

    if not ok:
        data = {
            "html": "",
            "text": "",
            "urls": [],
            "people_also_ask": [],
            "search_url": "",
            "source": "regex_fallback",
        }

    ms = int((_t.perf_counter() - started) * 1000)
    obscura_telemetry.log_call(
        "keyword_miner_serp",
        f"https://www.google.com/search?q={keyword}&hl={'pt-BR' if lang == 'pt' else 'en'}",
        ok, ms, error,
    )
    return data
