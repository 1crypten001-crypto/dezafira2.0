"""
Entrypoint do backend na Railway.

Problema resolvido aqui:
- O Railway injeta a var PORT (ex: 8085) e o healthcheck interno sonda essa porta.
- O domínio público (edge) encaminha para a Target Port configurada na Networking
  (neste projeto: 8080). Se a app ouvir só na $PORT, o público recebe 502 e o
  navegador reporta erro de CORS (502 chega sem headers CORS).

Solução: uvicorn escuta na $PORT (healthcheck interno) E, quando $PORT != 8080,
um proxy TCP mínimo encaminha a porta 8080 -> 127.0.0.1:$PORT (domínio público).
Tudo no mesmo processo (uma única instância do app, baixo custo de memória).

Suporta HTTP e WebSocket (é um forwarder TCP puro).
"""
import asyncio
import os


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


async def _tcp_proxy(listen_port: int, dst_host: str, dst_port: int):
    """Encaminha listen_port -> dst_host:dst_port (TCP puro, bidirecional)."""
    async def _pump(src, dst):
        try:
            while True:
                data = await src.read(65536)
                if not data:
                    break
                dst.write(data)
                await dst.drain()
        except Exception:
            pass
        finally:
            try:
                dst.close()
            except Exception:
                pass

    async def _handle(reader, writer):
        try:
            r2, w2 = await asyncio.open_connection(dst_host, dst_port)
            await asyncio.gather(_pump(reader, w2), _pump(r2, writer))
        except Exception as e:
            print(f"[proxy] {listen_port}->{dst_host}:{dst_port} erro: {e}", flush=True)
        finally:
            try:
                writer.close()
            except Exception:
                pass

    server = await asyncio.start_server(_handle, "0.0.0.0", listen_port)
    print(f"[entrypoint] Proxy TCP: 0.0.0.0:{listen_port} -> {dst_host}:{dst_port}", flush=True)
    async with server:
        await server.serve_forever()


async def main():
    port = _int_env("PORT", 8080)
    import uvicorn

    config = uvicorn.Config(
        "server:app",
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)

    tasks = [server.serve()]
    # Porta pública do edge da Railway: 8080 (Target Port da Networking).
    if port != 8080:
        tasks.append(_tcp_proxy(8080, "127.0.0.1", port))
    else:
        print("[entrypoint] PORT == 8080: sem proxy adicional.", flush=True)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
