"""Remove remaining dead .cs-icon CSS rules from index.html"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(BASE, "static", "index.html")

with open(path, "r", encoding="utf-8") as f:
    html = f.read()

changes = 0

# Remove BOTH .cs-icon rules (on separate lines)
lines = html.split('\n')
new_lines = []
for line in lines:
    if '.cs-icon' in line and 'filter:grayscale' in line:
        changes += 1
        continue  # skip
    if '.cs-icon' in line and 'iconFloat' in line:
        changes += 1
        continue  # skip
    new_lines.append(line)

html = '\n'.join(new_lines)

with open(path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Fixed CSS: {changes} dead .cs-icon lines removed")
