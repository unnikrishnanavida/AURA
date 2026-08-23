"""Security helpers for aura-memory."""

def sanitize_text(s: str) -> str:
	return s.replace("<", "&lt;").replace(">", "&gt;")


__all__ = ["sanitize_text"]
