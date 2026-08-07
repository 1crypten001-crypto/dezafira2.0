"""
Configuração da graça do healthcheck do Obscura (OBSCURA_HEALTH_GRACE).

A graça é o tempo em segundos que o backend tolera o motor Obscura fora do ar
antes de responder 503 no /healthz (o que faz o Railway reiniciar o backend).
Pode ser ajustada em runtime (memória) e persistida no .env para sobreviver
a restarts — sem precisar reiniciar o backend para aplicar.
"""
import os

_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")

# Override em runtime — None = usa o valor do .env/variável de ambiente
_RUNTIME_GRACE = {"seconds": None}

_DEFAULT_GRACE = 300.0


def _read_env_grace() -> float:
    try:
        return float(os.getenv("OBSCURA_HEALTH_GRACE", str(_DEFAULT_GRACE)))
    except (TypeError, ValueError):
        return _DEFAULT_GRACE


def get_grace_seconds() -> float:
    """Grace efetiva: override em runtime > .env/env > default 300s."""
    if _RUNTIME_GRACE["seconds"] is not None:
        return float(_RUNTIME_GRACE["seconds"])
    return _read_env_grace()


def get_grace_source() -> str:
    """De onde vem a graça atual: 'runtime' ou 'env'."""
    return "runtime" if _RUNTIME_GRACE["seconds"] is not None else "env"


def set_grace_seconds(seconds) -> dict:
    """Aplica em runtime E persiste no .env (sobrevive a restart)."""
    try:
        value = max(0.0, float(seconds))
    except (TypeError, ValueError):
        raise ValueError(f"grace_s inválido: {seconds!r}")
    _RUNTIME_GRACE["seconds"] = value
    persisted = _persist_env_grace(value)
    return {"grace_s": int(value), "source": "runtime", "persisted": persisted}


def _persist_env_grace(seconds) -> bool:
    """Escreve OBSCURA_HEALTH_GRACE no .env preservando as demais linhas."""
    line = f"OBSCURA_HEALTH_GRACE={int(seconds)}"
    try:
        if not os.path.exists(_ENV_PATH):
            with open(_ENV_PATH, "w", encoding="utf-8") as f:
                f.write(line + "\n")
            return True
        with open(_ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        out = []
        found = False
        for ln in lines:
            if ln.strip().startswith("OBSCURA_HEALTH_GRACE="):
                out.append(line)
                found = True
            else:
                out.append(ln)
        if not found:
            out.append(line)
        with open(_ENV_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        return True
    except Exception as e:
        print(f"[ObscuraHealth] Falha ao persistir OBSCURA_HEALTH_GRACE no .env: {e}")
        return False
