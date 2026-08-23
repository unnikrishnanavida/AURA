from pathlib import Path
import re
root = Path('.')
empty = []
placeholder = []
tiny = []
for path in sorted(root.rglob('*.py')):
    text = path.read_text(encoding='utf-8', errors='ignore')
    lines = [line for line in text.splitlines() if line.strip() and not line.strip().startswith('#')]
    if not lines:
        empty.append(path)
    elif len(lines) <= 8:
        if re.search(r'placeholder|todo|notimplemented', text, re.I):
            placeholder.append(path)
        else:
            tiny.append((path, len(lines), lines[:15]))
print('empty', len(empty))
print('placeholder', len(placeholder))
print('tiny', len(tiny))
for p in empty[:50]:
    print('E', p)
for p in placeholder[:50]:
    print('P', p)
for p, n, sample in tiny[:50]:
    print('S', n, p)
    for line in sample:
        print('   ', line)
