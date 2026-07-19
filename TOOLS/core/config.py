from pathlib import Path


PROJECT_NAME = "AURA"
ROOT = Path(__file__).resolve().parents[2]

ROOT_FOLDERS = [
    "01_FOUNDATION",
    "02_KNOWLEDGE",
    "03_RESEARCH",
    "04_INTELLIGENCE",
    "05_ENGINEERING",
    "06_SOURCE_CODE",
    "07_SECURITY",
    "08_INFRASTRUCTURE",
    "09_LABORATORY",
    "10_DATA",
    "11_MODELS",
    "12_DESIGN",
    "13_MANAGEMENT",
    "14_RELEASES",
    "15_ARCHIVE",
]

FOUNDATION = {
    "OSP": {
        "folder": "Architecture",
        "title": "Organization & System Plan",
        "directory": "OSP-001",
        "master": "AURA-OSP-001.md",
        "files": [
            "00-index.md",
            "01-front-matter.md",
            "02-part-i-organization.md",
            "03-part-ii-system.md",
            "04-part-iii-implementation.md",
            "05-appendices.md",
            "AURA-OSP-001.md",
        ],
    },
    "AEA": {
        "folder": "Architecture",
        "title": "Enterprise Architecture",
        "directory": "AEA-001",
        "master": "AURA-AEA-001.md",
        "files": [
            "00-index.md",
            "01-front-matter.md",
            "AURA-AEA-001.md",
        ],
    },
}
