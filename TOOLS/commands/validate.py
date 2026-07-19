from pathlib import Path
from core.config import ROOT, ROOT_FOLDERS


def validate_repository():

    passed = 0
    warnings = 0
    errors = 0

    print("\n====================================")
    print(" AURA Repository Validator")
    print("====================================\n")

    # -------------------------------
    # Check Root Folders
    # -------------------------------

    print("Checking root folders...\n")

    for folder in ROOT_FOLDERS:

        path = ROOT / folder

        if path.exists():
            print(f"✓ {folder}")
            passed += 1

        else:
            print(f"✗ Missing : {folder}")
            errors += 1

    print()

    # -------------------------------
    # Required Files
    # -------------------------------

    required_files = [
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
    ]

    print("Checking required files...\n")

    for file in required_files:

        path = ROOT / file

        if path.exists():
            print(f"✓ {file}")
            passed += 1

        else:
            print(f"⚠ Missing : {file}")
            warnings += 1

    print()

    # -------------------------------
    # Empty Markdown Files
    # -------------------------------

    print("Checking empty markdown files...\n")

    for md in ROOT.rglob("*.md"):

        if md.stat().st_size == 0:

            print(f"⚠ Empty : {md.relative_to(ROOT)}")
            warnings += 1

        else:
            passed += 1

    print()

    # -------------------------------
    # Summary
    # -------------------------------

    print("====================================")
    print(" Validation Summary")
    print("====================================")

    print(f"Passed   : {passed}")
    print(f"Warnings : {warnings}")
    print(f"Errors   : {errors}")

    print()

    if errors == 0:
        print("✓ Repository Healthy")
    else:
        print("✗ Repository has errors")