from pathlib import Path

root = Path(r"c:\Users\navid\Desktop\AURA\06_SOURCE_CODE\aura-sdk\aura_sdk")

created = []

for d in sorted(root.rglob('*')):
    if d.is_dir():
        # ignore __pycache__ and hidden
        if d.name == '__pycache__' or d.name.startswith('.'):
            continue
        # find python files other than __init__.py
        py_files = [p for p in d.iterdir() if p.suffix == '.py' and p.name != '__init__.py']
        if not py_files:
            # directory is empty of module files (except maybe __init__)
            init = d / '__init__.py'
            core = d / 'core.py'
            readme = d / 'README.md'
            changed = False
            if not init.exists():
                init.write_text(f'"""AURA SDK package: {d.relative_to(root)}"""\n\nfrom .core import {d.name.title().replace("_","").replace("-","") }Component\n\n__all__ = ["{d.name.title().replace("_","") }Component"]\n', encoding='utf-8')
                changed = True
            if not core.exists():
                cls = ''.join(x.title() for x in d.name.replace('-','_').split('_'))
                core.write_text(f'"""Core placeholder for aura_sdk.{d.name}."""\n\nclass {cls}Component:\n    """Placeholder component for aura_sdk.{d.name}."""\n\n    def execute(self):\n        return "{d.name} executed"\n', encoding='utf-8')
                changed = True
            if not readme.exists():
                readme.write_text(f'# {d.name}\n\nPlaceholder package for aura_sdk.{d.name}', encoding='utf-8')
                changed = True
            if changed:
                created.append(str(d.relative_to(root)))

print('Created placeholders for:', created)
