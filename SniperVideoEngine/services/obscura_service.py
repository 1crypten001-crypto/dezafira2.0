"""
ObscuraService — Telemetria central do motor Obscura.

Todas as chamadas ao Obscura (via obscura_client) passam por aqui para
registrar: agente que chamou, URL, sucesso, latência e erro. Isso alimenta
a página exclusiva "🕵️ Obscura" no painel e o endpoint /api/v1/obscura/status.

Como o motor Obscura não expõe métricas nativas (só CDP), a telemetria é
construída neste serviço: contadores em memória + ring buffer das últimas
chamadas + persistência opcional em obscura_logs no banco.
"""

import threading
import time
from collections import deque
from datetime import datetime


class ObscuraTelemetry:
    """Telemetria em memória (thread-safe) das chamadas ao Obscura."""

    def __init__(self, max_recent: int = 100):
        self._lock = threading.Lock()
        self._max_recent = max_recent
        self._total = 0
        self._ok = 0
        self._fail = 0
        self._retries = 0
        self._latency_sum_ms = 0
        self._latency_count = 0
        self._by_agent = {}          # agent -> {ok, fail, total, latency_sum_ms, via_bridge, via_fallback}
        self._recent = deque(maxlen=max_recent)  # [{agent, url, ok, ms, error, ts}]
        self._started_at = datetime.utcnow().isoformat()
        self._last_call_at = None
        self._last_ping = None       # {ts, online, targets, error}
        self._db_enabled = True

    def log_call(self, agent: str, url: str, ok: bool, ms: float, error: str = "",
                 via: str = "") -> None:
        """Registra uma chamada ao Obscura.

        via: caminho usado — "bridge" (motor real) ou "fallback" (urllib).
        """
        entry = {
            "agent": agent or "unknown",
            "url": (url or "")[:500],
            "ok": bool(ok),
            "ms": int(ms),
            "error": (error or "")[:300],
            "via": (via or "")[:20],
            "ts": datetime.utcnow().isoformat(),
        }
        with self._lock:
            self._total += 1
            if ok:
                self._ok += 1
            else:
                self._fail += 1
            self._latency_sum_ms += int(ms)
            self._latency_count += 1
            self._last_call_at = entry["ts"]

            ag = self._by_agent.setdefault(entry["agent"], {
                "ok": 0, "fail": 0, "total": 0, "latency_sum_ms": 0, "retries": 0,
                "via_bridge": 0, "via_fallback": 0,
            })
            ag["total"] += 1
            ag["ok" if ok else "fail"] += 1
            ag["latency_sum_ms"] += int(ms)
            if entry["via"] == "bridge":
                ag["via_bridge"] += 1
            elif entry["via"] == "fallback":
                ag["via_fallback"] += 1

            self._recent.append(entry)

        # Persistência best-effort (nunca quebra a chamada original)
        if self._db_enabled:
            try:
                from modules.database import create_db_obscura_log
                create_db_obscura_log(agent, url, ok, int(ms), error)
            except Exception:
                # Sem banco disponível — telemetria segue em memória
                pass

    def log_retry(self, agent: str = "unknown") -> None:
        """Registra um retry (falha transitória re-tentada pelo cliente)."""
        with self._lock:
            self._retries += 1
            ag = self._by_agent.setdefault(agent or "unknown", {
                "ok": 0, "fail": 0, "total": 0, "latency_sum_ms": 0, "retries": 0,
                "via_bridge": 0, "via_fallback": 0,
            })
            ag["retries"] += 1

    def set_ping(self, online: bool, targets: int = 0, error: str = "") -> None:
        """Atualiza o último ping de disponibilidade do motor."""
        with self._lock:
            self._last_ping = {
                "online": bool(online),
                "targets": targets,
                "error": (error or "")[:200],
                "ts": datetime.utcnow().isoformat(),
            }

    def build_status(self) -> dict:
        """Monta o payload do endpoint /api/v1/obscura/status e da página."""
        with self._lock:
            by_agent = {}
            for name, d in self._by_agent.items():
                total = max(d["total"], 1)
                by_agent[name] = {
                    "ok": d["ok"],
                    "fail": d["fail"],
                    "total": d["total"],
                    "success_rate": round(100 * d["ok"] / total, 1),
                    "avg_ms": round(d["latency_sum_ms"] / max(d["ok"] + d["fail"], 1), 1),
                    "retries": d.get("retries", 0),
                    "via_bridge": d.get("via_bridge", 0),
                    "via_fallback": d.get("via_fallback", 0),
                }
            recent = list(self._recent)[-self._max_recent:]

            avg_ms = 0
            if self._latency_count:
                avg_ms = round(self._latency_sum_ms / self._latency_count, 1)

            return {
                "started_at": self._started_at,
                "last_call_at": self._last_call_at,
                "total_calls": self._total,
                "ok_calls": self._ok,
                "fail_calls": self._fail,
                "retries": self._retries,
                "success_rate": round(100 * self._ok / max(self._total, 1), 1),
                "avg_latency_ms": avg_ms,
                "by_agent": by_agent,
                "recent_calls": recent,
                "last_ping": self._last_ping,
            }


# Singleton global — todos os módulos importam a mesma instância
obscura_telemetry = ObscuraTelemetry()
