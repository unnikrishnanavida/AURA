"""Small deterministic route for clear conversational intents."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConversationReply:
    intent: str
    answer: str


@dataclass(frozen=True, slots=True)
class MemoryCommand:
    action: str
    text: str


def route_memory(question: str) -> MemoryCommand | None:
    """Recognize explicit remember and recall requests without guessing intent."""
    normalized = question.strip()
    remember_match = re.fullmatch(r"(?:please\s+)?remember(?:\s+that)?\s+(.+?)[.!?]*", normalized, re.IGNORECASE)
    if remember_match:
        text = remember_match.group(1).strip()
        return MemoryCommand("remember", text) if text else None

    recall_match = re.fullmatch(
        r"(?:what\s+do\s+you\s+remember|what\s+do\s+you\s+recall)(?:\s+about\s+(.+?))?[.!?]*",
        normalized,
        re.IGNORECASE,
    )
    if recall_match:
        return MemoryCommand("recall", (recall_match.group(1) or "").strip())
    return None


def route_conversation(question: str) -> ConversationReply | None:
    """Answer only greetings and AURA identity/capability questions locally."""
    normalized = " ".join(re.sub(r"[^\w\s']", " ", question.casefold()).split())
    if normalized.endswith(" aura"):
        normalized = normalized[:-5].strip()

    if normalized in {"hi", "hello", "hey", "hiya", "good morning", "good afternoon", "good evening"}:
        return ConversationReply("greeting", "Hello! I'm AURA. What can I help you with?")
    if normalized in {"how are you", "how are you doing"}:
        return ConversationReply("greeting", "I'm here and ready to help. What would you like to work on?")
    if normalized in {"thanks", "thank you", "thanks a lot"}:
        return ConversationReply("thanks", "You're welcome. What would you like to explore next?")
    if normalized in {"who are you", "what are you"}:
        return ConversationReply(
            "identity",
            "I'm AURA, the Autonomous Unified Reasoning Architecture. I can help you explore questions and use the capabilities available in this workspace.",
        )
    if normalized in {"what can you do", "what can you help me with", "what are your capabilities"}:
        return ConversationReply(
            "capabilities",
            "I can help explore questions, work through reasoning, run research, recall saved memories, search AURA's knowledge, and work with your documents. For broader factual answers, I use a configured model provider; if one isn't available, I'll say so rather than guess.",
        )
    return None


__all__ = ["ConversationReply", "MemoryCommand", "route_conversation", "route_memory"]