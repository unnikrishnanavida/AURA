"""Command-line entry point for aura-core."""

from ._metadata import __version__


def main() -> None:
    print(f"aura-core {__version__}")


if __name__ == "__main__":
    main()
