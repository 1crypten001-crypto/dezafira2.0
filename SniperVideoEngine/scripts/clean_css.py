"""Remove remaining .cs-icon dead CSS rules."""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(BASE, "static", "index.html")

with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Remove all lines containing .cs-icon that are NOT in JS or HTML (only in <style>)
# We need to be careful to keep the JS that mentions .cs-icon (there shouldn't be any)
lines = html.split('\n')
new_lines = []
removed = 0
for line in lines:
    # Only remove CSS rules (lines that have .cs-icon and CSS syntax)
    if '.cs-icon' in line and ('{' in line or '}' in line or 'filter' in line or 'animation' in line or 'color' in line):
        # Double check it's a CSS rule (inside <style>)
        stripped = line.strip()
        if stripped.startswith('.cs-icon') or '.cs-icon{' in stripped or '.cs-icon ' in stripped:
            removed += 1
            continue
    new_lines.append(line)

html = '\n'.join(new_lines)
with open(path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Removed {removed} .cs-icon CSS lines (dead code)")
