"""Fix module headers across the aura_sdk package.

This script finds Python files under the package whose first
non-empty line is plain text (not a comment or a string) and wraps
that line in a triple-quoted module docstring.

Run from the repository root.
"""
import io
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "aura_sdk")

def first_nonempty_line(lines):
    for i, l in enumerate(lines):
        if l.strip():
            return i, l
    return None, None

fixed = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        path = os.path.join(dirpath, fn)
        try:
            with io.open(path, 'r', encoding='utf8') as f:
                lines = f.readlines()
        except Exception:
            continue
        idx, ln = first_nonempty_line(lines)
        if idx is None:
            continue
        s = ln.lstrip()
        if s.startswith('"') or s.startswith("'") or s.startswith('#'):
            continue
        # If the line looks like 'AURA SDK' header, convert it
        if 'AURA SDK' in ln or ln.strip().endswith('.'):
            doc = '"""' + ln.strip() + '\n' + '"""\n'
            # Remove that first line and insert docstring
            new_lines = lines[:idx] + [doc] + lines[idx+1:]
            try:
                with io.open(path, 'w', encoding='utf8') as f:
                    f.writelines(new_lines)
                fixed.append(path)
            except Exception:
                pass

print('Fixed', len(fixed), 'files')
for p in fixed:
    print(p)
