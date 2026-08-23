"""Telemetry stubs for aura-memory."""

def init_telemetry(enabled: bool = False) -> None:
	if not enabled:
		return
	# Placeholder for OpenTelemetry or similar initialization
	return


__all__ = ["init_telemetry"]
