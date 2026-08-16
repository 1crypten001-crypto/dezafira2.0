#!/usr/bin/env python3
"""
Convert 1Convite source data into canonical JSON under data/convite/.

One-time migration helper. Parses the JS data literals from the 1Convite repo
(matriz diaria real embutida no backend Express + datasets do frontend React)
and writes faithful JSON copies. No Node required — pure-Python mini JS-literal
parser that handles '...', "..." and `...` strings, comments and trailing commas.

Usage:
    python scripts/convert_convite_data.py [path-to-1convite-src]
    (default source: /tmp/1convite-src)
"""

import json
import os
import re
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/1convite-src"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "convite")


# ─────────────────────────────────────────────────────────────────────────────
# Mini parser de literais JS (objetos, arrays, strings, numeros, null/bool)
# ─────────────────────────────────────────────────────────────────────────────

class _P:
    def __init__(self, text: str):
        self.t = text
        self.i = 0
        self.n = len(text)

    def _skip_ws(self):
        while self.i < self.n:
            c = self.t[self.i]
            if c in " \t\r\n,":
                self.i += 1
            elif c == "/" and self.i + 1 < self.n and self.t[self.i + 1] == "/":
                j = self.t.find("\n", self.i)
                self.i = self.n if j == -1 else j
            elif c == "/" and self.i + 1 < self.n and self.t[self.i + 1] == "*":
                j = self.t.find("*/", self.i + 2)
                self.i = self.n if j == -1 else j + 2
            else:
                break

    def parse(self):
        self._skip_ws()
        if self.i >= self.n:
            raise ValueError("vazio")
        c = self.t[self.i]
        if c == "[": return self._array()
        if c == "{": return self._object()
        if c in "'\"" or c == "`": return self._string()
        return self._scalar()

    def _array(self):
        self.i += 1  # [
        out = []
        while True:
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("array sem fechamento")
            if self.t[self.i] == "]":
                self.i += 1
                return out
            out.append(self.parse())

    def _object(self):
        self.i += 1  # {
        out = {}
        while True:
            self._skip_ws()
            if self.i >= self.n:
                raise ValueError("objeto sem fechamento")
            if self.t[self.i] == "}":
                self.i += 1
                return out
            # key: quoted ou bare identifier
            if self.t[self.i] in "'\"" or self.t[self.i] == "`":
                key = self._string()
            else:
                m = re.match(r"[A-Za-z_$][A-Za-z0-9_$]*", self.t[self.i:])
                if not m:
                    raise ValueError(f"chave inválida em {self.t[self.i:self.i+20]!r}")
                key = m.group(0)
                self.i += len(key)
            self._skip_ws()
            if self.t[self.i] != ":":
                raise ValueError(f"esperava ':' após chave {key!r}")
            self.i += 1
            out[key] = self.parse()

    def _string(self):
        quote = self.t[self.i]
        self.i += 1
        out = []
        while self.i < self.n:
            c = self.t[self.i]
            if c == "\\":
                nxt = self.t[self.i + 1] if self.i + 1 < self.n else ""
                mapping = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "'": "'",
                           '"': '"', "`": "`", "0": "\0", "b": "\b", "f": "\f", "/": "/"}
                if nxt == "u":
                    hexs = self.t[self.i + 2:self.i + 6]
                    try:
                        out.append(chr(int(hexs, 16)))
                        self.i += 6
                        continue
                    except ValueError:
                        pass
                out.append(mapping.get(nxt, nxt))
                self.i += 2
                continue
            if c == quote:
                self.i += 1
                return "".join(out)
            out.append(c)
            self.i += 1
        raise ValueError("string sem fechamento")

    def _scalar(self):
        m = re.match(r"-?\d+(\.\d+)?([eE][+-]?\d+)?", self.t[self.i:])
        if m:
            self.i += len(m.group(0))
            return float(m.group(0)) if (m.group(1) or m.group(2)) else int(m.group(0))
        for tok in ("true", "false", "null", "undefined"):
            if self.t.startswith(tok, self.i):
                self.i += len(tok)
                return {"true": True, "false": False, "null": None, "undefined": None}[tok]
        raise ValueError(f"token inesperado em {self.t[self.i:self.i+30]!r}")


def parse_js_expr(text: str, start: int = 0):
    """Parseia uma expressão JS a partir de `start` e devolve (valor, posição_final)."""
    p = _P(text[start:])
    value = p.parse()
    return value, start + p.i


def load_const(filepath: str, name: str):
    """Lê `[export] const NAME = <expr>;` de um arquivo JS e devolve o valor."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = re.search(r"(?:export\s+)?const\s+" + re.escape(name) + r"\s*=\s*([\[{])", text)
    if not m:
        raise ValueError(f"'{name}' não encontrado em {filepath}")
    start = m.start(1)
    value, _ = parse_js_expr(text, start)
    return value


def write_json(name: str, data) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[convert] OK {name} ({os.path.getsize(path) / 1024:.1f} KB)")


# ─────────────────────────────────────────────────────────────────────────────
# 1) Matriz diária — dias reais (1–7) embutidos no backend/src/index.js
# ─────────────────────────────────────────────────────────────────────────────
def extract_real_days():
    idx = os.path.join(SRC, "backend", "src", "index.js")
    with open(idx, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = re.search(r"const\s+reais\s*=\s*(\[)", text)
    if not m:
        raise ValueError("'const reais = [' não encontrado no index.js")
    days, _ = parse_js_expr(text, m.start(1))
    if not isinstance(days, list) or len(days) < 7:
        raise ValueError(f"esperava 7 dias reais, achei {len(days) if isinstance(days, list) else 'não-array'}")
    return days


# ─────────────────────────────────────────────────────────────────────────────
# 2) Arcade Bíblico + 3) Trilha do Reino (frontend/src/data/*.js)
# ─────────────────────────────────────────────────────────────────────────────
def main():
    data_dir = os.path.join(SRC, "frontend", "src", "data")

    write_json("matriz_diaria_real.json", {"dias": extract_real_days()})

    arcade = os.path.join(data_dir, "arcadeData.js")
    write_json("arcade_quiz.json", {"perguntas": load_const(arcade, "ARCADE_QUIZ_QUESTIONS")})
    write_json("arcade_charadas.json", {"perguntas": load_const(arcade, "ARCADE_CHARADAS_QUESTIONS")})
    write_json("arcade_forca.json", {"palavras": load_const(arcade, "ARCADE_FORCA_WORDS")})
    write_json("arcade_caca_palavras.json", {"palavras": load_const(arcade, "ARCADE_CACA_PALAVRAS_LIST")})

    trail = os.path.join(data_dir, "trailData.js")
    write_json("trilha_reino.json", {
        "config": load_const(trail, "TRAIL_CONFIG"),
        "acoes": load_const(trail, "TRAIL_ACTIONS"),
        "plan_18m": load_const(trail, "PLAN_18M"),
        "book_names": load_const(trail, "BOOK_NAMES"),
        "devocionais": load_const(trail, "DEVOCIONAIS"),
    })

    print("\n[convert] Conteúdo do 1Convite convertido para JSON canônico em data/convite/.")


if __name__ == "__main__":
    main()
