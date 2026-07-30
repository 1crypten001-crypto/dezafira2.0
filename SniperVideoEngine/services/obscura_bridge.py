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
        logger.info("[Obscura] Desconectado")

    # ─── COMANDOS CDP ──────────────────────────────────────────────────

    async def _send_cdp(self, method: str, params: dict = None) -> dict:
        """Envia um comando CDP e retorna a resposta."""
        if not self._ws:
            raise ObscuraNotAvailableError("WebSocket não conectado")

        self._message_id += 1
        msg_id = self._message_id

        message = {
            "id": msg_id,
            "method": method,
            "params": params or {},
        }

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
        """Envia comando CDP para o target da página atual."""
        session_id = None
        return await self._send_cdp(method, {
            **(params or {}),
        })

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

        # Navega
        result = await self._send_cdp("Page.enable")
        result = await self._send_cdp("Page.navigate", {"url": url})

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

        result = await self._send_cdp("DOM.getDocument", {"depth": -1})
        node_id = result.get("root", {}).get("nodeId")

        if node_id:
            result = await self._send_cdp("DOM.getOuterHTML", {
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

        result = await self._send_cdp("Runtime.evaluate", {
            "expression": script,
            "returnByValue": True,
        })

        if "result" in result:
            value = result["result"].get("value")
            if value is not None:
                return str(value)
            # Se não tem value, pode ser um objeto — tenta serializar
            if "objectId" in result["result"]:
                props = await self._send_cdp("Runtime.getProperties", {
                    "objectId": result["result"]["objectId"],
                    "ownProperties": True,
                })
                return json.dumps(props.get("result", []), ensure_ascii=False)

        return ""

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

    Esta é a função principal usada pelo KeywordMiner.
    """
    bridge = ObscuraBridge()
    try:
        connected = await bridge.connect()
        if connected:
            data = await bridge.get_serp_data(keyword, lang)
            await bridge.disconnect()
            return data
    except Exception as e:
        logger.warning(f"[Obscura] Fallback acionado: {e}")
        try:
            await bridge.disconnect()
        except Exception:
            pass

    return {
        "html": "",
        "text": "",
        "urls": [],
        "people_also_ask": [],
        "search_url": "",
        "source": "regex_fallback",
    }
