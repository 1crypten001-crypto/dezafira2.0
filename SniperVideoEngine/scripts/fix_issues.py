"""Fix remaining issues from code review:
1. Remove dead CSS from index.html (.cs-icon, .cs-agent, .cs-action-badge)
2. Fix Seu Zé to use local time instead of UTC
3. Remove unnecessary import time inside while loop
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── 1. FIX INDEX.HTML — Remove dead CSS ───────────────────────────────
html_path = os.path.join(BASE, "static", "index.html")
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

changes_html = 0

# Remove .cs-icon rules (idle + active)
old = ".conveyor-stage.idle .cs-icon{filter:grayscale(1);opacity:.4}\n  .conveyor-stage.active .cs-icon{animation:iconFloat 2s ease-in-out infinite}"
if old in html:
    html = html.replace(old, "")
    changes_html += 1
    print(f"Removed .cs-icon CSS rules")

# Remove iconFloat keyframe
old2 = "  @keyframes iconFloat{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-4px) scale(1.1)}}"
if old2 in html:
    html = html.replace(old2, "")
    changes_html += 1
    print(f"Removed iconFloat keyframe")

# Remove .cs-agent CSS
old3 = "  .cs-agent{font-size:10px;color:#5c6370;margin-bottom:6px}"
if old3 in html:
    html = html.replace(old3, "")
    changes_html += 1
    print(f"Removed .cs-agent CSS")

if changes_html:
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML: {changes_html} changes applied")
else:
    print("HTML: No changes needed")

# ─── 2. FIX SEU ZÉ — Local time + remove import inside loop ──────────
ze_path = os.path.join(BASE, "modules", "seu_ze.py")
with open(ze_path, "r", encoding="utf-8") as f:
    content = f.read()

changes_ze = 0

# Fix: Change datetime.utcnow() to datetime.now() for local time
# But we need to import datetime differently
# _scheduler_loop uses: now = datetime.utcnow()
# Change to: now = datetime.now()
# Also remove now_local = now (line right after)
old_ze1 = "now = datetime.utcnow()\n            now_local = now  # Poderia ajustar fuso, mas vamos usar UTC por simplicidade"
new_ze1 = "now = datetime.now()"
if old_ze1 in content:
    content = content.replace(old_ze1, new_ze1)
    changes_ze += 1
    print(f"Ze: Changed UTC to local time")

# Fix: Remove 'import time as _time' inside the while loop
# and use top-level import instead
old_ze2 = """        # Dorme 60 segundos
        import time as _time
        _time.sleep(60)"""
new_ze2 = """        # Dorme 60 segundos
        import time as _time
        _time.sleep(60)"""
# Actually, let's check if the import is there
if "import time as _time" in content:
    # Count occurrences
    count = content.count("import time as _time")
    if count > 1:
        # There's one at the top level and one inside the loop
        # Remove ONLY the one inside the loop (the second one)
        lines = content.split('\n')
        new_lines = []
        removed_inside = False
        for i, line in enumerate(lines):
            if 'import time as _time' in line and not removed_inside and i > 5:  # Not at top
                removed_inside = True
                continue
            new_lines.append(line)
        if removed_inside:
            content = '\n'.join(new_lines)
            changes_ze += 1
            print(f"Ze: Removed duplicate import time inside loop")
    
if changes_ze:
    with open(ze_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Ze: {changes_ze} changes applied")
else:
    print("Ze: No changes needed")

print("\nDone!")
