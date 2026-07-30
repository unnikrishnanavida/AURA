from .semantic_version import SemanticVersion


class VersionManager:
    def __init__(self) -> None:
        self._version = SemanticVersion()

    def current(self) -> SemanticVersion:
        return self._version
