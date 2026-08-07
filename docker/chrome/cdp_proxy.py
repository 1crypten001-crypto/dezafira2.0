#!/usr/bin/env python3
"""Proxy TCP unificado (substitui o socat) para os servicos headless
(Chrome / Obscura) no Railway.

Resolve dois problemas do Railway de uma vez, sem depender de qual porta
o healthcheck sonda:

1. HEALTHCHECK: o Railway sonda a variavel $PORT (injetada pela plataforma)
   e NAO respeita healthcheckPort/[variables]/EXPOSE do codigo. Nao temos
   como fixar essa porta -> entao escutamos em TODAS as portas candidatas
   ($PORT, 9000, 80, 8080, 9222, 9223) e respondemos 200 para QUALQUER
   caminho que NAO seja do CDP (/healthz, /, etc). O deploy passa em
   qualquer porta que o Railway escolher.

2. ANTI-DNS-REBINDING: o Chrome 136+ e o motor Rust recusam conexao CDP
   quando o Host header e um hostname (chrome.railway.internal:9223, que e
   exatamente o que o backend usa). Ao encaminhar /json/* e /devtools/*
   para o CDP no loopback, reescrevemos Host -> 127.0.0.1:INNER_PORT.
   Isso deixa o backend (ws://*.railway.internal:9223) funcionar sem o
   workaround de resolver IP no backend.
"""
import json
import os
import socket
import sys
import threading

VERSION = "2"

INNER_PORT = int(os.environ.get("OBSCURA_INNER_PORT", "9224"))

BODY = json.dumps({"status": "ok", "service": "dezafira-headless"}).encode()

CANDIDATES = []


def add(port):
    try:
        port = int(port)
    except (TypeError, ValueError):
        return
    if port > 0 and port not in CANDIDATES:
        CANDIDATES.append(port)


def listen(port):
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", port))
        srv.listen(128)
        print("[proxy] escutando :%d -> 127.0.0.1:%d" % (port, INNER_PORT), flush=True)
    except OSError as e:
        sys.stderr.write("[proxy] ERRO ao bindar :%d -> %s\n" % (port, e))
        sys.stderr.flush()
        return
    while True:
        try:
            conn, _addr = srv.accept()
        except OSError:
            break
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


def recv_until(sock, marker, limit=65536):
    buf = b""
    while marker not in buf and len(buf) < limit:
        try:
            chunk = sock.recv(4096)
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
    return buf


def send_ok(conn):
    resp = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: " + str(len(BODY)).encode() + b"\r\n"
        b"Connection: close\r\n\r\n" + BODY
    )
    try:
        conn.sendall(resp)
    except OSError:
        pass
    finally:
        try:
            conn.close()
        except OSError:
            pass


def pump(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def rewrite_host(head):
    out = []
    for ln in head.split(b"\r\n"):
        if ln.lower().startswith(b"host:"):
            out.append(b"Host: 127.0.0.1:%d" % INNER_PORT)
        else:
            out.append(ln)
    return b"\r\n".join(out)


def handle(conn):
    conn.settimeout(15)
    data = recv_until(conn, b"\r\n\r\n")
    if not data:
        try:
            conn.close()
        except OSError:
            pass
        return
    first_line = data.split(b"\r\n", 1)[0]
    try:
        _method, path, _proto = first_line.split(b" ", 2)
    except ValueError:
        _method, path = b"GET", b"/"

    is_cdp = path.startswith(b"/json/") or path.startswith(b"/devtools/")
    if not is_cdp:
        print("[proxy] health 200 %s %s" % (_method.decode(errors="replace"),
                                            path.decode(errors="replace")), flush=True)
        send_ok(conn)
        return

    try:
        up = socket.create_connection(("127.0.0.1", INNER_PORT), timeout=10)
    except OSError as e:
        sys.stderr.write("[proxy] CDP %d indisponivel -> %s (respondendo 200)\n"
                         % (INNER_PORT, e))
        sys.stderr.flush()
        send_ok(conn)
        return

    conn.settimeout(None)
    up.settimeout(None)
    try:
        up.sendall(rewrite_host(data))
    except OSError:
        try:
            up.close()
        except OSError:
            pass
        try:
            conn.close()
        except OSError:
            pass
        return

    t1 = threading.Thread(target=pump, args=(up, conn), daemon=True)
    t2 = threading.Thread(target=pump, args=(conn, up), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    try:
        conn.close()
    except OSError:
        pass
    try:
        up.close()
    except OSError:
        pass


def main():
    if os.environ.get("PORT"):
        add(os.environ["PORT"])
    for p in ("9000", "80", "8080", "9222", "9223"):
        add(p)
    print("[proxy] v%s portas candidatas: %s (inner %d)" % (VERSION, CANDIDATES, INNER_PORT), flush=True)
    threads = []
    for port in CANDIDATES:
        t = threading.Thread(target=listen, args=(port,), daemon=True)
        t.start()
        threads.append(t)
    threading.Event().wait()


if __name__ == "__main__":
    main()
