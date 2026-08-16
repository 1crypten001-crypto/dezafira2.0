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
OBSCURA_CHROME_PORT = int(os.getenv("OBSCURA_CHROME_PORT", "9223"))
# Host do Chrome real — em produção (Railway) pode ser um serviço separado
# (ex.: chrome.railway.internal); local usa o mesmo host do Obscura.
OBSCURA_CHROME_HOST = os.getenv("OBSCURA_CHROME_HOST", OBSCURA_HOST)
OBSCURA_SERP_DELAY = float(os.getenv("OBSCURA_SERP_DELAY", "1.5"))
OBSCURA_ENABLED = os.getenv("OBSCURA_ENABLED", "true").lower() in ("true", "1", "yes")
OBSCURA_WS_URL = f"ws://{OBSCURA_HOST}:{OBSCURA_PORT}/devtools/browser"


def obscura_enabled() -> bool:
    """Fonte única do gate do Obscura — lê OBSCURA_ENABLED em tempo de chamada.

    Todas as pipelines/agentes devem usar esta função (e não o módulo constante
    OBSCURA_ENABLED, que é lido no import). Assim, trocar o .env em runtime
    (ex.: o card de graça / monitoramento) vale para tudo de uma vez.
    """
    return os.getenv("OBSCURA_ENABLED", "true").lower() in ("true", "1", "yes")


def obscura_proxy() -> dict:
    """Fonte única da config de proxy — lê OBSCURA_PROXY_URL em runtime.

    Retorna {"enabled": bool, "url": str, "masked": str} onde masked esconde
    credenciais (user:pass) pra exibição segura no painel. Usado pelos .bat
    (que passam a flag --proxy/--proxy-server) e pelo status do painel.
    """
    url = (os.getenv("OBSCURA_PROXY_URL") or "").strip().strip('"').strip("'")
    if not url:
        return {"enabled": False, "url": "", "masked": ""}
    masked = url
    if "@" in url:
        scheme, _, rest = url.partition("//")
        cred, _, host = rest.rpartition("@")
        masked = f"{scheme}//***@{host}" if scheme else f"***@{host}"
    return {"enabled": True, "url": url, "masked": masked}


# Cache: uma vez que o Google bloqueou o headless, pula direto pro Bing
_GOOGLE_BLOCKED = {"value": False}

# Rotação de buscadores de fallback (distribui carga e reduz rate-limit)
_SERP_FALLBACK_ENGINES = ["bing", "ddg", "ecosia"]
_SERP_ROTATION = {"i": 0}


def _next_fallback_engine() -> str:
    """Retorna o próximo buscador de fallback em round-robin."""
    engine = _SERP_FALLBACK_ENGINES[_SERP_ROTATION["i"] % len(_SERP_FALLBACK_ENGINES)]
    _SERP_ROTATION["i"] += 1
    return engine

# Cache: porta do motor já resolvida (evita sondar /json/version a cada SERP)
# TTL de 60s: re-sonda periodicamente para detectar o Chrome quando ele subir
# depois do backend (comum no Railway). Sem TTL, o cache ficaria preso no Obscura
# para sempre se o Chrome não estivesse de pé no primeiro boot do backend.
_PICKED_PORT = {"value": None}
_PICKED_HOST_PORT = {"value": None, "ts": 0.0}  # (host, porta) do motor escolhido
_PICKED_HOST_PORT_TTL = float(os.getenv("OBSCURA_PICK_TTL", "60"))  # segundos


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

    async def _resolve_ws_url(self) -> str:
        """Resolve a URL do WebSocket: prefere Chrome real (HTTP /json/version
        com webSocketDebuggerUrl dinâmico), senão usa o path fixo do Obscura.

        Isso permite o MESMO bridge falar com os dois motores:
          - Chrome real (--remote-debugging-port) → /json/version
          - Obscura (engine Rust) → ws://host:port/devtools/browser
        """
        try:
            import urllib.request
            # Chrome 136+ recusa Host com hostname (anti DNS-rebinding)
            ip = await asyncio.to_thread(_resolve_ip, self.host)
            with urllib.request.urlopen(
                f"http://{ip}:{self.port}/json/version", timeout=3
            ) as r:
                info = json.loads(r.read().decode("utf-8", "ignore"))
                ws = info.get("webSocketDebuggerUrl")
                if ws:
                    # O Chrome real anuncia ws://127.0.0.1:9223/... mesmo quando o
                    # serviço está remoto (Railway) — reescreve o host para o
                    # IP real (Host header valido pro Chrome), senão o backend
                    # conectar-se-ia a si mesmo ou seria recusado por hostname.
                    from urllib.parse import urlsplit, urlunsplit
                    parts = urlsplit(str(ws))
                    if parts.hostname and parts.hostname not in ("127.0.0.1", "localhost", "::1"):
                        return str(ws)
                    rewritten = urlunsplit((parts.scheme, f"{ip}:{self.port}",
                                            parts.path, parts.query, parts.fragment))
                    return rewritten
        except Exception:
            pass
        return f"ws://{self.host}:{self.port}/devtools/browser"

    async def connect(self) -> bool:
        """Tenta conectar via WebSocket CDP (Chrome real ou Obscura)."""
        if not self.enabled:
            logger.info("[Obscura] Desabilitado via OBSCURA_ENABLED=false")
            return False

        if self._connected:
            return True

        try:
            import websockets

            self.ws_url = await self._resolve_ws_url()
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

            # Chrome real expõe targets auxiliares (browser_ui/Omnibox) além da
            # página — filtra por type == 'page' pra pegar a aba de verdade.
            page_targets = [t for t in targets if t.get("type") == "page"]

            # Se não houver target de página, cria um
            if not page_targets:
                result = await self._send_cdp("Target.createTarget", {
                    "url": "about:blank",
                })
                self._target_id = result.get("targetId")
            else:
                self._target_id = page_targets[0].get("targetId")

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

    # ─── HTML → PNG (usado pelo Agnes Studio de capas) ───────────────────

    async def screenshot(self, width: int = 1280, height: int = 720,
                         device_scale_factor: int = 1) -> bytes:
        """Renderiza a página atual (ex: data:text/html) como PNG via CDP.

        Usado pelo Agnes Studio para compor capas HTML → PNG. Força o
        viewport no tamanho exato da capa e captura além da viewport para
        não cortar conteúdo flutuante. Retorna os bytes do PNG.
        """
        if not self._connected:
            raise ObscuraNotAvailableError("Obscura não conectado")

        await self._send_cdp_to_target("Emulation.setDeviceMetricsOverride", {
            "width": width,
            "height": height,
            "deviceScaleFactor": device_scale_factor,
            "mobile": False,
        })
        # clip explícito garante o PNG exatamente em width×height mesmo quando o
        # layout da página estoura o viewport (captureBeyondViewport sozinho
        # capturaria o tamanho do conteúdo, ex: com barras de rolagem).
        result = await self._send_cdp_to_target("Page.captureScreenshot", {
            "format": "png",
            "captureBeyondViewport": True,
            "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": device_scale_factor},
        })
        data = result.get("data", "")
        if not data:
            raise RuntimeError("Page.captureScreenshot retornou sem dados")
        import base64
        return base64.b64decode(data)

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

    async def get_serp_data_bing(self, keyword: str, lang: str = "pt") -> dict:
        """
        Extrai SERP REAL do Bing (o Google bloqueia o headless com anti-bot).

        Retorna o mesmo formato de get_serp_data, com source 'obscura_bing'.
        As URLs vêm decodificadas (o Bing usa redirect /ck/a com u=base64)
        e as perguntas relacionadas são extraídas dos títulos/snippets reais.
        """
        from urllib.parse import quote, parse_qs
        import base64

        search_url = (
            f"https://www.bing.com/search?q={quote(keyword)}"
            f"&setlang={'pt-br' if lang == 'pt' else 'en-us'}"
            f"&mkt={'pt-BR' if lang == 'pt' else 'en-US'}"
        )
        html, text = await self.navigate_and_get_html(search_url)

        js = """
        (() => {
            const items = [];
            document.querySelectorAll('#b_results li.b_algo').forEach(li => {
                const a = li.querySelector('h2 a');
                const sn = li.querySelector('.b_caption p, .b_caption, p');
                if (a && a.href && a.href.startsWith('http')) {
                    items.push({
                        title: a.textContent.trim(),
                        url: a.href,
                        snippet: sn ? sn.textContent.trim().slice(0, 200) : ''
                    });
                }
            });
            return JSON.stringify({items: items.slice(0, 10)});
        })()
        """
        out = await self.execute_js(js)
        items = []
        try:
            data = json.loads(out) if out else {}
            items = data.get("items", [])
        except json.JSONDecodeError:
            pass

        # Decodifica as URLs reais do redirect do Bing (u=base64)
        def _real_url(href: str) -> str:
            try:
                qs = parse_qs(href)
                u = qs.get("u", [""])[0]
                if u.startswith("a1") and len(u) > 2:
                    raw = u[2:]
                    padded = raw + "=" * (-len(raw) % 4)
                    decoded = base64.urlsafe_b64decode(padded).decode("utf-8", "ignore")
                    if decoded.startswith("http"):
                        return decoded
            except Exception:
                pass
            return href

        urls, titles, questions = [], [], []
        Q_MARKERS = ("como ", "por que ", "qual ", "quanto ", "quais ",
                     "melhor ", "vale a pena", "dúvida", "erro", "problema",
                     "ajuda", "?", "posso ", "devo ", "quando ")
        for it in items:
            url = _real_url(it.get("url", ""))
            urls.append(url)
            titles.append(it.get("title", ""))
            for fld in (it.get("title", ""), it.get("snippet", "")):
                low = (fld or "").lower()
                if any(m in low for m in Q_MARKERS):
                    q = (it.get("title") or it.get("snippet") or "").strip()[:120]
                    if q and q not in questions:
                        questions.append(q)
                    break

        return {
            "html": html,
            "text": text[:10000],
            "urls": urls,
            "titles": titles,
            "people_also_ask": questions[:10],
            "search_url": search_url,
            "source": "obscura_bing",
        }

    async def get_serp_data_ddg(self, keyword: str, lang: str = "pt") -> dict:
        """
        Extrai SERP REAL do DuckDuckGo (HTML lite) — busca com `site:`
        funciona aqui e a carga é distribuída (round-robin com Bing/Ecosia).
        Source 'obscura_ddg'.
        """
        from urllib.parse import quote

        search_url = (
            f"https://html.duckduckgo.com/html/?q={quote(keyword)}"
            f"&kl={'br-pt' if lang == 'pt' else 'us-en'}"
        )
        html, text = await self.navigate_and_get_html(search_url)

        js = """
        (() => {
            const items = [];
            document.querySelectorAll('.result').forEach(r => {
                const a = r.querySelector('a.result__a');
                const sn = r.querySelector('.result__snippet');
                if (a && a.href) {
                    items.push({
                        title: a.textContent.trim(),
                        url: a.href,
                        snippet: sn ? sn.textContent.trim().slice(0, 200) : ''
                    });
                }
            });
            return JSON.stringify({items: items.slice(0, 10)});
        })()
        """
        out = await self.execute_js(js)
        items = []
        try:
            data = json.loads(out) if out else {}
            items = data.get("items", [])
        except json.JSONDecodeError:
            pass

        def _real_url(href: str) -> str:
            # DDG redireciona via //duckduckgo.com/l/?uddg=<encoded>
            try:
                if "uddg=" in href:
                    from urllib.parse import urlparse, unquote, parse_qs
                    qs = parse_qs(urlparse(href).query)
                    u = qs.get("uddg", [""])[0]
                    if u.startswith("http"):
                        return unquote(u)
            except Exception:
                pass
            return href

        urls, titles, questions = [], [], []
        Q_MARKERS = ("como ", "por que ", "qual ", "quanto ", "quais ",
                     "melhor ", "vale a pena", "dúvida", "erro", "problema",
                     "ajuda", "?", "posso ", "devo ", "quando ")
        for it in items:
            url = _real_url(it.get("url", ""))
            urls.append(url)
            titles.append(it.get("title", ""))
            for fld in (it.get("title", ""), it.get("snippet", "")):
                low = (fld or "").lower()
                if any(m in low for m in Q_MARKERS):
                    q = (it.get("title") or it.get("snippet") or "").strip()[:120]
                    if q and q not in questions:
                        questions.append(q)
                    break

        return {
            "html": html,
            "text": text[:10000],
            "urls": urls,
            "titles": titles,
            "people_also_ask": questions[:10],
            "search_url": search_url,
            "source": "obscura_ddg",
        }

    async def get_serp_data_ecosia(self, keyword: str, lang: str = "pt") -> dict:
        """
        Extrai SERP REAL do Ecosia (usa o índice do Bing, HTML server-rendered).
        Source 'obscura_ecosia'.
        """
        from urllib.parse import quote

        search_url = (
            f"https://www.ecosia.org/search?q={quote(keyword)}"
            f"&language={'pt' if lang == 'pt' else 'en'}"
        )
        html, text = await self.navigate_and_get_html(search_url)

        js = """
        (() => {
            const items = [];
            document.querySelectorAll('.result, .mainline .result').forEach(r => {
                const a = r.querySelector('a[data-test-id="result-title"]') || r.querySelector('a.result__title') || r.querySelector('h2 a');
                const sn = r.querySelector('p[data-test-id="result-snippet"], .result__snippet, .result-snippet');
                if (a && a.href) {
                    items.push({
                        title: a.textContent.trim(),
                        url: a.href,
                        snippet: sn ? sn.textContent.trim().slice(0, 200) : ''
                    });
                }
            });
            return JSON.stringify({items: items.slice(0, 10)});
        })()
        """
        out = await self.execute_js(js)
        items = []
        try:
            data = json.loads(out) if out else {}
            items = data.get("items", [])
        except json.JSONDecodeError:
            pass

        urls, titles, questions = [], [], []
        Q_MARKERS = ("como ", "por que ", "qual ", "quanto ", "quais ",
                     "melhor ", "vale a pena", "dúvida", "erro", "problema",
                     "ajuda", "?", "posso ", "devo ", "quando ")
        for it in items:
            url = it.get("url", "")
            urls.append(url)
            titles.append(it.get("title", ""))
            for fld in (it.get("title", ""), it.get("snippet", "")):
                low = (fld or "").lower()
                if any(m in low for m in Q_MARKERS):
                    q = (it.get("title") or it.get("snippet") or "").strip()[:120]
                    if q and q not in questions:
                        questions.append(q)
                    break

        return {
            "html": html,
            "text": text[:10000],
            "urls": urls,
            "titles": titles,
            "people_also_ask": questions[:10],
            "search_url": search_url,
            "source": "obscura_ecosia",
        }

    async def _serp_fallback_engine(self, keyword: str, lang: str, engine: str) -> dict:
        """Dispatch do fallback rotativo: bing | ddg | ecosia."""
        if engine == "ddg":
            return await self.get_serp_data_ddg(keyword, lang)
        if engine == "ecosia":
            return await self.get_serp_data_ecosia(keyword, lang)
        return await self.get_serp_data_bing(keyword, lang)

    async def get_serp_data(self, keyword: str, lang: str = "pt") -> dict:
        """
        Método especializado para extrair dados SERP do Google.

        O Google bloqueia o headless (anti-bot) — quando isso acontece
        (HTML minúsculo ou falha de navegação), cai automaticamente no
        Bing para continuar entregando SERP REAL (nunca fallback genérico).

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

        # Google já detectado bloqueado → pula direto pro fallback rotativo (evita 2 navegações)
        if _GOOGLE_BLOCKED["value"]:
            engine = _next_fallback_engine()
            logger.info(f"[Obscura] Google já bloqueado — fallback rotativo: {engine}")
            return await self._serp_fallback_engine(keyword, lang, engine)

        html, text = await self.navigate_and_get_html(search_url)

        # Detecta CAPTCHA/anti-bot do Google: redirect /sorry/ OU página minúscula
        blocked = len(html) < 10000
        if not blocked:
            try:
                href = (await self.execute_js("location.href")) or ""
                blocked = "/sorry/" in str(href)
            except Exception:
                pass

        if blocked:
            _GOOGLE_BLOCKED["value"] = True
            engine = _next_fallback_engine()
            logger.info(f"[Obscura] Google bloqueou (anti-bot/captcha) — fallback rotativo: {engine}")
            # Telemetria: registra o bloqueio do Google (fonte real do relatório)
            try:
                from services.obscura_service import obscura_telemetry
                obscura_telemetry.log_serp_block("google")
            except Exception:
                pass
            return await self._serp_fallback_engine(keyword, lang, engine)

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

def _err_detail(e: Exception, host: str, port: int) -> str:
    """Erro de sonda legível: tipo + mensagem + alvo. `str(TimeoutError)` é
    vazio (por isso o healthz mostrava `error: ""` — inútil pra diagnosticar).
    Com o type() e o alvo, dá pra distinguir timeout vs refused vs DNS."""
    try:
        msg = f"{type(e).__name__}: {e}"[:180]
    except Exception:
        msg = type(e).__name__[:180]
    return f"{msg} @ {host}:{port}"


def _resolve_ip(host: str) -> str:
    """Resolve hostname -> IPv4. O Chrome 136+ tem proteção anti DNS-rebinding:
    o servidor DevTools recusa requisições com header Host que não seja IP ou
    localhost (erro "Host header is specified and is not an IP address or
    localhost"). Por isso sondamos e conectamos VIA IP, não via hostname.

    Preferimos IPv4 porque o socat do serviço Chrome binda em 0.0.0.0 (o
    tráfego IPv6 da rede privada do Railway não chegaria nele). Se a resolução
    falhar, devolve o host original (o erro seguinte fica visível no healthz).
    """
    import socket as _socket
    try:
        infos = _socket.getaddrinfo(host, None, _socket.AF_INET)
        if infos:
            return infos[0][4][0]
    except Exception:
        pass
    return host


async def get_obscura_status(host: str = None, port: int = None) -> dict:
    """Verifica se o Obscura está rodando e retorna status detalhado.
    Retorna {online, ws_url, targets, host, port, error} — host/port são os
    alvos reais sondados (útil pra confirmar que o backend aponta pro
    serviço certo via env vars)."""
    bridge = ObscuraBridge(host=host, port=port)
    s_host, s_port = bridge.host, bridge.port
    try:
        connected = await bridge.connect()
        if not connected:
            return {
                "online": False,
                "ws_url": bridge.ws_url,
                "targets": 0,
                "host": s_host,
                "port": s_port,
                "error": "Não conectou (binário parado ou OBSCURA_ENABLED=false)",
            }
        status = await bridge.get_status()
        await bridge.disconnect()
        return {
            "online": True,
            "ws_url": status["ws_url"],
            "targets": status["targets"],
            "host": s_host,
            "port": s_port,
            "proxy": obscura_proxy(),
            "error": "",
        }
    except Exception as e:
        return {
            "online": False,
            "ws_url": bridge.ws_url,
            "targets": 0,
            "host": s_host,
            "port": s_port,
            "error": _err_detail(e, s_host, s_port),
        }


async def get_chrome_status(host: str = None, port: int = None) -> dict:
    """Verifica se o Chrome real (CDP) está acessível — em produção é o
    serviço separado (ex.: chrome.railway.internal:9223). Sonda o mesmo
    endpoint /json/version que o bridge usa, pra saber se o Chrome está de
    pé e pode desbloquear o Google (SERP/PAA reais).

    Retorna {online, ws_url, targets, browser, host, port, error} — browser
    traz a versão do Chrome (prova de que é o Chrome real, não o headless
    Rust); host/port são os alvos reais sondados (se OBSCURA_CHROME_HOST não
    estiver setada, default = OBSCURA_HOST — suspeita da queda atual).
    """
    import urllib.request as _urllib
    import urllib.error as _urlerr
    host = host or OBSCURA_CHROME_HOST
    port = port or OBSCURA_CHROME_PORT
    # Chrome 136+ recusa Host com hostname (anti DNS-rebinding). getaddrinfo e
    # bloqueante e sem timeout — roda em thread pra nao travar o event loop
    # (o wait_for(5s) da sonda nao consegue interromper chamada bloqueante).
    ip = await asyncio.to_thread(_resolve_ip, host)
    ws_url = f"ws://{host}:{port}/devtools/browser"
    try:
        with _urllib.urlopen(f"http://{ip}:{port}/json/version", timeout=3) as r:
            info = json.loads(r.read().decode("utf-8", "ignore"))
        online = bool(info.get("webSocketDebuggerUrl"))
        targets = 1 if online else 0
        return {
            "online": online,
            "ws_url": ws_url,
            "targets": targets,
            "browser": info.get("Browser", "")[:80],
            "host": host,
            "port": port,
            "error": "",
        }
    except _urlerr.HTTPError as e:
        # HTTP 500 do Chrome (ex.: CDP em estado ruim) — captura o corpo da
        # resposta pra ver o que o Chrome devolveu de verdade, em vez de só
        # "HTTP Error 500".
        try:
            body = e.read().decode("utf-8", "ignore").strip()[:120] or ""
        except Exception:
            body = ""
        suffix = f" | body: {body}" if body else ""
        return {
            "online": False,
            "ws_url": ws_url,
            "targets": 0,
            "browser": "",
            "host": host,
            "port": port,
            "error": _err_detail(e, host, port) + suffix,
        }
    except Exception as e:
        return {
            "online": False,
            "ws_url": ws_url,
            "targets": 0,
            "browser": "",
            "host": host,
            "port": port,
            "error": _err_detail(e, host, port),
        }


async def test_proxy_connectivity(proxy_url: str) -> dict:
    """Testa se o proxy configurado está de pé: faz um GET real via proxy
    (api.ipify.org devolve o IP de saída — prova que o tráfego passa pelo
    proxy) e mede latência. Retorna {enabled, ok, ms, ip, error}."""
    import time as _t
    started = _t.perf_counter()
    # urllib só suporta http(s) — socks5 dá falso negativo; avisa em vez de falhar
    if proxy_url.lower().startswith(("socks4://", "socks5://", "socks://")):
        return {
            "enabled": True,
            "ok": None,
            "ms": 0,
            "ip": "",
            "error": "proxy SOCKS: o teste HTTP (urllib) não suporta — confirme manualmente via start_chrome_local.bat",
        }
    try:
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({
            "http": proxy_url,
            "https": proxy_url,
        })
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request(
            "https://api.ipify.org?format=json",
            headers={"User-Agent": "DezafiraObscura/1.0"},
        )
        with opener.open(req, timeout=6) as resp:
            body = resp.read().decode("utf-8", "ignore")[:200]
        ms = int((_t.perf_counter() - started) * 1000)
        ip = ""
        try:
            import json as _json
            ip = (_json.loads(body) or {}).get("ip", "")
        except Exception:
            ip = body[:50]
        return {"enabled": True, "ok": True, "ms": ms, "ip": ip}
    except Exception as e:
        ms = int((_t.perf_counter() - started) * 1000)
        return {"enabled": True, "ok": False, "ms": ms, "error": str(e)[:200], "ip": ""}


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


async def _pick_bridge_port() -> int:
    """Escolhe o motor a usar: Chrome real se estiver de pé via HTTP
    /json/version, senão o Obscura. Retorna APENAS a porta (compat);
    use _pick_bridge_host_port() quando precisar do host também.

    A escolha fica em cache (padrão _GOOGLE_BLOCKED) para não sondar
    /json/version a cada keyword — só resolve de novo se o motor parar.
    """
    host, port = await _pick_bridge_host_port()
    return port


async def _pick_bridge_host_port() -> tuple:
    """Escolhe (host, porta) do motor: Chrome real (OBSCURA_CHROME_HOST:
    OBSCURA_CHROME_PORT) se estiver de pé, senão Obscura (OBSCURA_HOST:
    OBSCURA_PORT). O Chrome pode estar em host separado (Railway: serviço
    chrome.railway.internal); o Obscura segue no OBSCURA_HOST.

    Cache com TTL (_PICKED_HOST_PORT_TTL, default 60s): re-sonda periodicamente
    para detectar o Chrome quando ele subir depois do backend (startup race
    condition comum no Railway). Sem TTL, o cache ficaria preso no Obscura
    para sempre se o Chrome não estivesse de pé no primeiro boot.
    """
    import time as _time
    now = _time.time()
    cached = _PICKED_HOST_PORT["value"]
    if cached is not None and (now - _PICKED_HOST_PORT["ts"]) < _PICKED_HOST_PORT_TTL:
        return cached

    candidates = [
        (OBSCURA_CHROME_HOST, OBSCURA_CHROME_PORT),  # Chrome real primeiro
        (OBSCURA_HOST, OBSCURA_PORT),                # Obscura como fallback
    ]
    for host, port in candidates:
        try:
            import urllib.request
            # Chrome 136+ recusa Host com hostname (anti DNS-rebinding)
            ip = await asyncio.to_thread(_resolve_ip, host)
            with urllib.request.urlopen(
                f"http://{ip}:{port}/json/version", timeout=2
            ) as r:
                info = json.loads(r.read().decode("utf-8", "ignore"))
                if info.get("webSocketDebuggerUrl"):
                    _PICKED_HOST_PORT["value"] = (host, port)
                    _PICKED_HOST_PORT["ts"] = _time.time()
                    chosen = "Chrome" if port == OBSCURA_CHROME_PORT else "Obscura"
                    logger.info(f"[Obscura] Motor escolhido: {chosen} ({host}:{port})")
                    return host, port
        except Exception:
            continue

    # Nenhum motor respondeu — usa Obscura como último recurso e
    # invalida o cache (ts=0) para re-sondar mais cedo na próxima chamada.
    logger.warning("[Obscura] Nenhum motor disponível — fallback Obscura (cache invalidado)")
    _PICKED_HOST_PORT["value"] = (OBSCURA_HOST, OBSCURA_PORT)
    _PICKED_HOST_PORT["ts"] = _time.time() - (_PICKED_HOST_PORT_TTL * 0.75)  # re-sonda em 15s
    return OBSCURA_HOST, OBSCURA_PORT


async def get_serp_with_fallback(keyword: str, lang: str = "pt") -> dict:
    """
    Tenta usar Obscura/Chrome para SERP data. Se falhar, retorna dict vazio
    para que o KeywordMiner use o fallback regex.

    Esta é a função principal usada pelo KeywordMiner (PAA + dificuldade SERP).
    Prefere o Chrome real (desbloqueia o Google); senão o Obscura (Bing).

    Quando a conexão falha (motor caiu depois do boot), invalida o cache de
    motor escolhido para que _pick_bridge_host_port() re-sonda na próxima
    chamada e potencialmente mude para o outro motor.
    """
    from services.obscura_service import obscura_telemetry
    import time as _t

    started = _t.perf_counter()
    ok = False
    error = ""
    data = {}
    host, port = await _pick_bridge_host_port()
    bridge = ObscuraBridge(host=host, port=port)
    try:
        # Delay entre SERPs para não estourar rate-limit dos buscadores
        if OBSCURA_SERP_DELAY > 0:
            await asyncio.sleep(OBSCURA_SERP_DELAY)
        connected = await bridge.connect()
        if connected:
            data = await bridge.get_serp_data(keyword, lang)
            await bridge.disconnect()
            # Distingue o motor na telemetria: Google respondido via Chrome real
            # (destrava o SERP/PAA) vira 'obscura_chrome'; via headless Rust fica
            # 'obscura'. Assim o painel compara as fontes lado a lado.
            if port == OBSCURA_CHROME_PORT and data.get("source") == "obscura":
                data["source"] = "obscura_chrome"
            ok = bool(data)
            error = "" if ok else "serp vazio"
        else:
            error = "nao conectado"
            # Motor não conectou → invalida o cache para re-sondar na próxima rodada.
            # Permite auto-cura: se o Chrome caiu e o Obscura está de pé (ou vice-versa),
            # a próxima chamada descobre o motor alternativo sem precisar reiniciar o backend.
            logger.warning(f"[Obscura] Motor {host}:{port} não conectou — invalidando cache de motor")
            _PICKED_HOST_PORT["value"] = None
    except Exception as e:
        logger.warning(f"[Obscura] Fallback acionado: {e}")
        error = str(e)[:200]
        # Falha de conexão → invalida cache para auto-cura
        _PICKED_HOST_PORT["value"] = None
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
        via="bridge" if ok else "fallback",
    )
    # Registra a fonte real da SERP (rotacao de buscadores) p/ telemetria por rodada.
    # Só conta como sucesso quando veio com URLs — motor bloqueado (0 urls) não
    # deve inflar a estatística de fontes.
    if ok and data.get("urls"):
        obscura_telemetry.log_serp_source(data.get("source") or "desconhecida")
    elif ok:
        obscura_telemetry.log_serp_source(data.get("source") + "_vazio" if data.get("source") else "regex_fallback")
        # Telemetria de bloqueio por fonte: o motor respondeu mas veio vazio
        if data.get("source"):
            engine = data["source"].replace("obscura_", "").replace("obscura", "google")
            obscura_telemetry.log_serp_block(engine)
    else:
        obscura_telemetry.log_serp_source("regex_fallback")
    return data


async def get_google_suggestions(keyword: str, lang: str = "pt") -> list:
    """
    Busca sugestões de autocomplete do Google para descobrir termos cauda longa quentes.
    Bate na API de suggest do Google e retorna uma lista limpa de strings.
    """
    import urllib.parse
    import httpx
    import json
    
    url = f"http://suggestqueries.google.com/complete/search?client=chrome&hl={'pt-BR' if lang == 'pt' else 'en'}&q={urllib.parse.quote(keyword)}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            if r.status_code == 200:
                data = json.loads(r.text)
                if isinstance(data, list) and len(data) > 1:
                    suggestions = data[1]
                    if isinstance(suggestions, list):
                        return [str(s).strip() for s in suggestions[:10]]
    except Exception as e:
        logger.warning(f"[Obscura Suggest] Erro ao buscar auto-suggest para '{keyword}': {e}")
    return []


async def analyze_serp_difficulty_with_forums(keyword: str, lang: str = "pt") -> dict:
    """
    Pesquisa a keyword no Google real e analisa a presença de fóruns (Reddit, Quora, etc.)
    para definir se o termo é uma fruta baixa (Low Hanging Fruit).
    """
    # Usa o get_serp_with_fallback que já roda o Obscura/Chrome com tratamento de cache e auto-cura!
    serp = await get_serp_with_fallback(keyword, lang=lang)
    urls = serp.get("urls", [])
    
    forums = ["reddit.com", "quora.com", "facebook.com", "twitter.com", "linkedin.com", "medium.com", "github.com", "forum"]
    found_forums = []
    for url in urls:
        url_lower = url.lower()
        for f in forums:
            if f in url_lower:
                found_forums.append(url)
                break
                
    has_forums = len(found_forums) > 0
    difficulty = "Fácil" if has_forums else ("Média" if len(urls) < 5 else "Difícil")
    
    return {
        "keyword": keyword,
        "difficulty": difficulty,
        "has_forums": has_forums,
        "forums_found": found_forums[:3],
        "urls": urls[:5]
    }

