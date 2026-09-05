import pytest
from aura_desktop.capabilities.broker import CapabilityBroker
def test_deny():
 with pytest.raises(PermissionError): CapabilityBroker().require("filesystem.write")
