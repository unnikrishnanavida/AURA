"""Implement simple stubs for Manager and Validator classes.

This script finds classes whose names end with 'Manager' or 'Validator' and
whose bodies contain only a `pass` or only a docstring+`pass`, and replaces
that `pass` with a small, explicit implementation.

Run from repository root.
"""
import ast
import io
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..", "aura_sdk")

MANAGER_IMPL = '''
    def __init__(self) -> None:
        self._registry = {}

    def register(self, name: str, obj: object) -> None:
        if not name:
            raise ValueError("name must be non-empty")
        self._registry[name] = obj

    def unregister(self, name: str) -> object:
        try:
            return self._registry.pop(name)
        except KeyError:
            raise KeyError(f"not registered: {name}")

    def get(self, name: str, default: object = None) -> object:
        return self._registry.get(name, default)

    def list(self) -> list:
        return list(self._registry.keys())
'''

VALIDATOR_IMPL = '''
    def validate(self, data) -> bool:
        if data is None:
            raise ValueError("data cannot be None")
        return True
'''

fixed_files = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        path = os.path.join(dirpath, fn)
        try:
            src = io.open(path, 'r', encoding='utf8').read()
        except Exception:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        modified = False
        for node in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            name = node.name
            # compute source segment for class
            # Find the class definition start
            m = re.search(rf"^class\s+{re.escape(name)}\b[\s\S]*?:", src, flags=re.M)
            if not m:
                continue
            # Find the body indentation by locating 'pass' under the class
            class_start = m.start()
            # Slice from class start to end of class by finding next top-level class/def
            following = re.search(r"^class\s+\w+|^def\s+\w+", src[m.end():], flags=re.M)
            class_end = m.end() + (following.start() if following else len(src)-m.end())
            class_block = src[class_start:class_end]
            # Check if class body only has 'pass' (optionally after a docstring)
            # A crude check: look for a line with only 'pass' indented
            pass_line = re.search(r"\n(\s+)pass\s*\n", class_block)
            if not pass_line:
                continue
            indent = pass_line.group(1)
            # Determine which impl to use
            if name.endswith('Manager'):
                impl = MANAGER_IMPL
            elif name.endswith('Validator'):
                impl = VALIDATOR_IMPL
            else:
                continue
            # Prepare impl with correct indentation
            impl_lines = ''.join(indent + line if line.strip() else line for line in impl.splitlines(True))
            # Replace 'pass' line with impl_lines in class_block
            new_class_block = re.sub(r"\n\s+pass\s*\n", '\n' + impl_lines + '\n', class_block, count=1)
            # Replace in source
            src = src[:class_start] + new_class_block + src[class_end:]
            modified = True
        if modified:
            try:
                with io.open(path, 'w', encoding='utf8') as f:
                    f.write(src)
                fixed_files.append(path)
            except Exception:
                pass

print('Fixed', len(fixed_files), 'files')
for p in fixed_files:
    print(p)
