"""List aura-memory / aura-learning files that have meaningful logic (>=5 logic nodes)."""
import ast
import pathlib
import subprocess

ROOT = pathlib.Path(r"C:\Users\navid\Desktop\AURA")


def logic_files(prefix: str, min_nodes: int = 5) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", prefix],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    hits = []
    for rel in out:
        p = ROOT / rel
        try:
            tree = ast.parse(p.read_bytes().decode("utf-8", "replace"))
        except SyntaxError:
            continue
        n = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, (ast.Assign, ast.Call, ast.While, ast.For, ast.If, ast.ClassDef))
        )
        if n >= min_nodes:
            hits.append((rel, n))
    return hits


def main() -> None:
    for prefix in ["06_SOURCE_CODE/aura-memory", "06_SOURCE_CODE/aura-learning"]:
        hits = logic_files(prefix)
        print(f"== {prefix}: {len(hits)} files with >=5 logic nodes ==")
        for rel, n in sorted(hits, key=lambda x: -x[1])[:120]:
            print(f"  {n:>4}  {rel}")


if __name__ == "__main__":
    main()