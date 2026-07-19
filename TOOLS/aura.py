import argparse

from commands.scaffold import build_scaffold
from commands.document import create_document
from commands.validate import validate_repository
from builders.docs_builder import build_docs
from commands.generate_architecture import generate_architecture

def banner():
    print("=" * 50)
    print("AURA Developer CLI")
    print("Version 2.0")
    print("=" * 50)


def main():
    banner()

    parser = argparse.ArgumentParser(
        prog="aura",
        description="AURA Developer CLI"
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("architecture")

    # init command
    subparsers.add_parser("init")

    # new command
    new_parser = subparsers.add_parser("new")
    new_parser.add_argument("document")

    # validate command
    subparsers.add_parser("validate")

    # version command
    subparsers.add_parser("version")

    # info command
    subparsers.add_parser("info")

    # build command
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument(
        "target",
        choices=["docs", "pdf", "website", "release"]
    )

    args = parser.parse_args()

    if args.command == "init":
        build_scaffold()

    elif args.command == "new":
        create_document(args.document)

    elif args.command == "validate":
        validate_repository()

    elif args.command == "version":
        print("AURA CLI v2.0")

    elif args.command == "info":
        print("AURA Developer Toolkit")

    elif args.command == "build":
        if args.target == "docs":
            build_docs()
        elif args.target == "pdf":
            print("PDF builder coming soon.")
        elif args.target == "website":
            print("Website builder coming soon.")
        elif args.target == "release":
            print("Release builder coming soon.")

    elif args.command == "architecture":
        generate_architecture()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
