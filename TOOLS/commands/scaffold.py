from core.config import ROOT, FOUNDATION
from core.templates import markdown
from core.utils import create_markdown

def build_scaffold():
    """
    Creates the AURA foundation scaffold.
    """

    for folder, files in FOUNDATION.items():
        for filename, title in files:
            create_markdown(
                ROOT / "01_FOUNDATION" / folder / filename,
                markdown(title),
            )

    print("✓ AURA scaffold created successfully.")