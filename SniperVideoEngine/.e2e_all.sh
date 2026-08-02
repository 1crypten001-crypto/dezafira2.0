#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  E2E DEZAFIRA — runner unificado (1 comando, relatório pass/fail)
#  Cenários:
#    [1/4] pytest unitário (retry, telemetria PAA/Reddit, via counters, grace)
#    [2/4] /healthz E2E: 200 → derruba motor → 503 → religa → 200
#    [3/4] Telemetria via counters (bridge/fallback por agente)
#    [4/4] Config de grace (runtime override + persistência .env)
# ═══════════════════════════════════════════════════════════════════════
cd "$(dirname "$0")"

PASS=0; FAIL=0; TOTAL=0
report() { # $1 nome, $2 status (ok/fail)
  TOTAL=$((TOTAL+1))
  if [ "$2" = "ok" ]; then PASS=$((PASS+1)); echo "  ✅ PASS — $1"; else FAIL=$((FAIL+1)); echo "  ❌ FAIL — $1"; fi
}

echo "══════════════════════════════════════════════"
echo "  E2E DEZAFIRA — Obscura / Healthz / Telemetria"
echo "══════════════════════════════════════════════"

echo; echo "== [1/4] pytest unitário =="
P1=$(python -m pytest tests/ -q 2>&1 | tail -3)
echo "$P1"
if echo "$P1" | grep -qE "passed|no tests ran"; then report "pytest ($(echo "$P1" | grep -oE '[0-9]+ passed' | head -1))" ok; else report "pytest" fail; fi

echo; echo "== [2/4] /healthz E2E (200→503→200) =="
P2=$(timeout 160 bash .e2e_healthz.sh 2>&1 | grep -E '^== 1\)|^== 2\)|^== 3\)|^HTTP|DONE')
echo "$P2"
H1=$(echo "$P2" | grep -A1 '== 1)' | grep -oE 'HTTP [0-9]+' | head -1)
H2=$(echo "$P2" | grep -A1 '== 2)' | grep -oE 'HTTP [0-9]+' | head -1)
H3=$(echo "$P2" | grep -A1 '== 3)' | grep -oE 'HTTP [0-9]+' | head -1)
if [ "$H1" = "HTTP 200" ] && [ "$H2" = "HTTP 503" ] && [ "$H3" = "HTTP 200" ]; then
  report "healthz $H1 → $H2 → $H3" ok
else
  report "healthz ($H1 → $H2 → $H3)" fail
fi

echo; echo "== [3/4] Telemetria via counters (bridge/fallback) =="
P3=$(python - <<'PY' 2>&1 | tail -2
from services.obscura_service import ObscuraTelemetry
t = ObscuraTelemetry(max_recent=20)
t._db_enabled = False
t.log_call("e2e_agente", "https://example.com", True, 100, via="bridge")
t.log_call("e2e_agente", "https://example.com", True, 200, via="fallback")
s = t.build_status()
a = s["by_agent"]["e2e_agente"]
assert a["via_bridge"] == 1 and a["via_fallback"] == 1, a
print(f"VIA_OK bridge={a['via_bridge']} fallback={a['via_fallback']}")
PY
)
echo "$P3"
if echo "$P3" | grep -q "VIA_OK"; then report "via counters ($(echo "$P3" | grep -oE 'bridge=[0-9]+ fallback=[0-9]+'))" ok; else report "via counters" fail; fi

echo; echo "== [4/4] Config de grace (runtime + .env) =="
P4=$(python - <<'PY' 2>&1 | tail -2
import os, tempfile
from services import obscura_health as h
h._RUNTIME_GRACE["seconds"] = None
os.environ.pop("OBSCURA_HEALTH_GRACE", None)
assert h.get_grace_seconds() == 300.0, h.get_grace_seconds()
with tempfile.TemporaryDirectory() as td:
    env_path = os.path.join(td, ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("OBSCURA_ENABLED=false\n")
    h._ENV_PATH = env_path
    r = h.set_grace_seconds(120)
    content = open(env_path, encoding="utf-8").read()
    assert r["persisted"] and "OBSCURA_HEALTH_GRACE=120" in content, content
    assert "OBSCURA_ENABLED=false" in content, content  # preservou outra linha
    assert h.get_grace_seconds() == 120.0 and h.get_grace_source() == "runtime"
print("GRACE_OK runtime=120 persist=true")
PY
)
echo "$P4"
if echo "$P4" | grep -q "GRACE_OK"; then report "grace config ($(echo "$P4" | grep -oE 'runtime=[0-9]+ persist=[a-z]+'))" ok; else report "grace config" fail; fi

echo; echo "══════════════════════════════════════════════"
echo "  RESULTADO: $PASS/$TOTAL PASS · $FAIL FAIL"
echo "══════════════════════════════════════════════"
[ "$FAIL" = "0" ]
