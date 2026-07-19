from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ARCH_ROOT = ROOT / "01_FOUNDATION" / "Architecture"

ARCHITECTURE = {
    "OSP": [
        "00-index.md",
        "01-document-control.md",
        "02-executive-summary.md",
        "03-vision.md",
        "04-mission.md",
        "05-goals.md",
        "06-scope.md",
        "07-stakeholders.md",
        "08-functional-requirements.md",
        "09-non-functional-requirements.md",
        "10-system-overview.md",
        "11-high-level-architecture.md",
        "12-development-roadmap.md",
        "13-risk-analysis.md",
        "14-future-roadmap.md",
        "15-appendices.md",
        "AURA-OSP-001.md",
    ],

    "AEA": [
        "00-index.md",
        "01-business-architecture.md",
        "02-application-architecture.md",
        "03-data-architecture.md",
        "04-technology-architecture.md",
        "05-security-architecture.md",
        "06-infrastructure-architecture.md",
        "07-integration-architecture.md",
        "08-deployment-architecture.md",
        "AURA-AEA-001.md",
    ],

    "AKA": [
        "00-index.md",
        "01-knowledge-model.md",
        "02-ontology.md",
        "03-memory-model.md",
        "04-vector-knowledge.md",
        "05-retrieval.md",
        "06-reasoning.md",
        "07-learning.md",
        "08-validation.md",
        "AURA-AKA-001.md",
    ],

    "AES": [
        "00-index.md",
        "01-coding-standards.md",
        "02-documentation-standards.md",
        "03-testing-standards.md",
        "04-api-standards.md",
        "05-security-standards.md",
        "06-review-process.md",
        "07-release-process.md",
        "AURA-AES-001.md",
    ],

    "ADS": [
        "00-index.md",
        "01-system-design.md",
        "02-component-design.md",
        "03-database-design.md",
        "04-api-design.md",
        "05-ui-design.md",
        "06-agent-design.md",
        "07-ai-design.md",
        "AURA-ADS-001.md",
    ],

    "ADR": [
        "00-index.md",
        "01-decision-template.md",
        "02-accepted-decisions.md",
        "03-deprecated-decisions.md",
        "AURA-ADR-001.md",
    ],

    "AAR": [
        "00-index.md",
        "01-system-review.md",
        "02-performance-review.md",
        "03-security-review.md",
        "04-quality-review.md",
        "AURA-AAR-001.md",
    ],

    "ARP": [
        "00-index.md",
        "01-research-roadmap.md",
        "02-open-problems.md",
        "03-experiments.md",
        "04-benchmarks.md",
        "05-publications.md",
        "AURA-ARP-001.md",
    ],
}


def create_md(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        title = path.stem.replace("-", " ").title()

        path.write_text(
            f"# {title}\n\n"
            "Status: Draft\n\n"
            "---\n\n",
            encoding="utf-8",
        )


def generate_architecture():

    total = 0

    for doc, files in ARCHITECTURE.items():

        folder = ARCH_ROOT / doc / f"{doc}-001"

        folder.mkdir(parents=True, exist_ok=True)

        for file in files:

            create_md(folder / file)
            total += 1

    print("=" * 50)
    print("AURA Architecture Generated")
    print("=" * 50)
    print(f"Documents : {len(ARCHITECTURE)}")
    print(f"Files      : {total}")
    print(f"Location   : {ARCH_ROOT}")