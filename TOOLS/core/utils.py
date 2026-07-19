from pathlib import Path


def create_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def create_markdown(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text(content, encoding="utf-8")


def log(message):
    print(f"✓ {message}")


def get_next_version(base_path: Path, prefix: str) -> str:
    """
    Returns the next available version directory.
    Example:
        OSP-001
        OSP-002
        OSP-003
    """

    highest = 0

    if base_path.exists():
        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith(prefix):
                try:
                    number = int(item.name.split("-")[1])
                    highest = max(highest, number)
                except (IndexError, ValueError):
                    pass

    return f"{prefix}-{highest + 1:03d}"