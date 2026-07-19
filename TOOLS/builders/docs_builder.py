from pathlib import Path
from core.config import ROOT


def build_docs():

    docs_dir = ROOT / "out" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    markdown_files = sorted(ROOT.rglob("*.md"))

    index_file = docs_dir / "index.md"
    navigation_file = docs_dir / "navigation.md"

    with index_file.open("w", encoding="utf-8") as index:
        index.write("# AURA Documentation Index\n\n")

        for md in markdown_files:

            relative = md.relative_to(ROOT)

            index.write(f"- {relative}\n")

    with navigation_file.open("w", encoding="utf-8") as nav:

        nav.write("# Navigation\n\n")

        for md in markdown_files:

            relative = md.relative_to(ROOT)

            nav.write(f"* {relative}\n")

    print(f"✓ Found {len(markdown_files)} markdown files")
    print("✓ index.md generated")
    print("✓ navigation.md generated")
    print(f"✓ Output: {docs_dir}")