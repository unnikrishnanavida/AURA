import pytest

from aura_mobile.permissions.broker import PermissionBroker


def test_deny() -> None:
    with pytest.raises(PermissionError):
        PermissionBroker().require("camera")
