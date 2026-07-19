from core.config import ROOT, FOUNDATION
from core.templates import markdown
from core.utils import create_markdown, get_next_version

def create_document(doc_type: str):
    doc_type = doc_type.upper()

    if doc_type not in FOUNDATION:
        print(f"Unknown document: {doc_type}")
        return

    doc = FOUNDATION[doc_type]

    parent = ROOT / "01_FOUNDATION" / doc["folder"]

    # Get the next version directory
    directory = get_next_version(parent, doc_type)
    base = parent / directory

    # Create all required markdown files
    version = directory.split("-")[1]

    for filename in doc["files"]:

     if filename.startswith("AURA-"):
        filename = f"AURA-{doc_type}-{version}.md"

    title = filename.replace(".md", "").replace("-", " ").title()

    create_markdown(
        base / filename,
        markdown(title),
    )

    print(f"✓ {doc_type} created successfully.")
