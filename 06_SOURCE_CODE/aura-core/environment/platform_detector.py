import platform


def detect() -> str:
    return platform.system()
