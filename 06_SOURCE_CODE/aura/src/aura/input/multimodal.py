"""Canonical untrusted multimodal input seam (Phase 1J).

Every uploaded/attached modality is **untrusted data**. This module owns the
responsibility that did not exist anywhere in the canonical package: validating
an external attachment and mapping supported content onto a bounded, attributable
:class:`MultimodalObservation` that reasoning may reference but never elevate to
verified fact or execution authority.

Design rules:

- **Honest capability**: :data:`SUPPORTED_MODALITIES` is only what the canonical
  runtime genuinely knows how to turn into text observations -- ``text`` and
  ``document`` (the latter only via *caller-supplied* extracted text; AURA does
  not parse raw PDF/office binaries). Image/audio/video/other return
  ``capability_unavailable`` / ``unsupported_media_type`` instead of fabricating
  understanding.
- **Boundaries preserved**: :class:`~aura.security.prompt_injection.ContentPolicy`
  is the single choke point, so instruction-like attachment text is treated as
  data, never instructions -- it is blocked, not fed to reasoning.
- **Observation != fact**: observations carry ``verified=False`` and a confidence
  below :data:`~aura.reasoning.models.OBSERVED_BELIEF`, so they ground an
  answer's attribution but are never promoted to a logical premise.
- **No authority**: accepting an observation never grants a capability. The
  caller must already hold the scope; media cannot request permissions.
- **Cancellable**: the canonical :class:`~aura.foundation.cancellation.CancellationToken`
  is honoured; a cancelled request yields a ``cancelled`` verdict per attachment.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from aura.foundation.cancellation import CancellationToken
from aura.reasoning.models import OBSERVED_BELIEF, GroundingItem
from aura.security.prompt_injection import ContentPolicy, ContentTrust

#: Text and document are the only modalities the canonical runtime genuinely
#: turns into bounded text observations. Everything else is honest "capability
#: unavailable" (no vision/OCR/audio/speech processor exists in the package).
SUPPORTED_MODALITIES: frozenset[str] = frozenset({"text", "document"})

#: The string reported when a modality has no canonical processor. Kept as a
#: named constant so the API and tests share one honest phrasing.
CAPABILITY_UNAVAILABLE = "capability_unavailable"

#: Content-model limits. Text becomes bytes for the size gate; anything above the
#: hard byte bound is rejected before any parsing is attempted.
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MiB
DEFAULT_MAX_CONTENT_CHARS = 8000
DEFAULT_MAX_OBSERVATIONS = 8

#: Substring-derived observation confidence. Stays below OBSERVED_BELIEF *even*
#: at a perfect score, so an untrusted observation is attributable but can never
#: become a reasoning premise or a verified fact.
OBSERVATION_CONFIDENCE = 0.3
OBSERVATION_SCORE = 0.4

# Recognized media-type (MIME-style) prefixes, used only for modality detection.
_IMAGE_PREFIX = "image/"
_AUDIO_PREFIX = "audio/"
_VIDEO_PREFIX = "video/"

_TEXT_TYPES = frozenset(
    {
        "text/plain",
        "text/markdown",
        "text/x-markdown",
        "text/csv",
        "text/html",
        "application/xhtml+xml",
    }
)
_DOCUMENT_TYPES = frozenset(
    {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/rtf",
        "application/json",
    }
)
class MediaModality(StrEnum):
    """The modality an attachment claims or is detected as."""

    TEXT = "text"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "other"


class IngestVerdict(StrEnum):
    """One outcome for a single attachment, reported honestly to the caller."""

    ACCEPTED = "accepted"
    CAPABILITY_UNAVAILABLE = CAPABILITY_UNAVAILABLE
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    OVERSIZED = "oversized"
    MALFORMED = "malformed"
    DOCUMENT_PARSE_UNAVAILABLE = "document_parse_unavailable"
    UNAUTHORIZED = "unauthorized"
    INJECTION_BLOCKED = "injection_blocked"
    CANCELLED = "cancelled"
    TOO_MANY = "too_many"


def _modality_for(media_type: str) -> MediaModality:
    """Detect the modality from a client-declared media type string."""
    mt = (media_type or "").strip().lower()
    if not mt:
        return MediaModality.OTHER
    if mt in _TEXT_TYPES:
        return MediaModality.TEXT
    if mt in _DOCUMENT_TYPES:
        return MediaModality.DOCUMENT
    if mt.startswith(_IMAGE_PREFIX):
        return MediaModality.IMAGE
    if mt.startswith(_AUDIO_PREFIX):
        return MediaModality.AUDIO
    if mt.startswith(_VIDEO_PREFIX):
        return MediaModality.VIDEO
    return MediaModality.OTHER


@dataclass(frozen=True, slots=True)
class InputLimits:
    """Hard bounds applied to one attachment / one request."""

    max_bytes: int = DEFAULT_MAX_BYTES
    max_content_chars: int = DEFAULT_MAX_CONTENT_CHARS
    max_observations: int = DEFAULT_MAX_OBSERVATIONS

    def __post_init__(self) -> None:
        for name in ("max_bytes", "max_content_chars", "max_observations"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be >= 1, got {getattr(self, name)}")


def input_limits(*, max_bytes: int = DEFAULT_MAX_BYTES) -> InputLimits:
    """Default limits for the runtime input boundary."""
    return InputLimits(max_bytes=max_bytes)


@dataclass(frozen=True, slots=True)
class RawAttachment:
    """Untrusted content as it arrives at the boundary (before validation).

    ``source_id`` is the attachment/source identity for provenance. For text,
    content is in :attr:`content`. For a document, AURA accepts only
    *caller-extracted* :attr:`extracted_text` -- the system does not parse raw
    binaries, and reports ``DOCUMENT_PARSE_UNAVAILABLE`` if only bytes are given.
    """

    source_id: str
    media_type: str
    size_bytes: int
    owner_scope: str
    content: str = ""
    extracted_text: str = ""
    declared_modality: str | None = None
    file_name: str | None = None


@dataclass(frozen=True, slots=True)
class MultimodalObservation:
    """A bounded, attributable observation derived from validated content.

    Always ``verified=False``: it describes what the content *says*, never proof
    of what is true, and it carries no capability/execution authority.
    """

    observation_id: str
    modality: MediaModality
    source: str
    owner_scope: str
    content: str
    trust: ContentTrust
    captured_at: str
    provenance: dict[str, Any] = field(default_factory=dict)
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "modality": self.modality.value,
            "source": self.source,
            "owner_scope": self.owner_scope,
            "content": self.content,
            "verified": self.verified,
            "trust": self.trust.value,
            "captured_at": self.captured_at,
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Honest outcome for one attachment through the observation gate."""

    verdict: IngestVerdict
    modality: MediaModality = MediaModality.OTHER
    reason: str = ""
    observation_id: str | None = None
    observation: MultimodalObservation | None = None

    @property
    def accepted(self) -> bool:
        return self.verdict is IngestVerdict.ACCEPTED

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.verdict.value,
            "modality": self.modality.value,
            "reason": self.reason,
        }
        if self.observation_id is not None:
            payload["observation_id"] = self.observation_id
        return payload


class ObservationGate:
    """Single choke point for untrusted multimodal input.

    Order of checks (each fails closed, each attributable): cancellation,
    authorization, size, modality/format, content acquisition, then prompt
    injection. An accepted observation is built with full provenance and
    ``verified=False``; rejected attachments are reported, never fabricated.
    """

    def __init__(self, *, policy: ContentPolicy | None = None, limits: InputLimits | None = None) -> None:
        self._policy = policy or ContentPolicy()
        self._limits = limits or InputLimits()

    @property
    def limits(self) -> InputLimits:
        return self._limits

    def ingest(
        self,
        attachment: RawAttachment,
        *,
        authorized: bool,
        request_id: str | None = None,
        token: CancellationToken | None = None,
        now: str | None = None,
    ) -> IngestionResult:
        """Validate one attachment and, when supported, return one observation."""
        if token is not None and token.cancelled:
            return IngestionResult(
                IngestVerdict.CANCELLED,
                modality=_modality_for(attachment.media_type),
                reason="cancellation requested before processing",
            )
        if not authorized:
            return IngestionResult(
                IngestVerdict.UNAUTHORIZED,
                modality=_modality_for(attachment.media_type),
                reason="caller is not authorized to attach this content to the request",
            )
        if attachment.size_bytes < 0 or attachment.size_bytes > self._limits.max_bytes:
            return IngestionResult(
                IngestVerdict.OVERSIZED,
                modality=_modality_for(attachment.media_type),
                reason=(
                    f"attachment size {attachment.size_bytes} bytes exceeds the "
                    f"limit of {self._limits.max_bytes} bytes"
                ),
            )

        modality = _modality_for(attachment.media_type)
        if modality is MediaModality.OTHER:
            return IngestionResult(
                IngestVerdict.UNSUPPORTED_MEDIA_TYPE,
                modality=modality,
                reason=f"media type {attachment.media_type!r} is not recognized",
            )
        if modality.value not in SUPPORTED_MODALITIES:
            return IngestionResult(
                IngestVerdict.CAPABILITY_UNAVAILABLE,
                modality=modality,
                reason=(
                    f"no canonical processor exists for {modality.value!r}; "
                    "capability unavailable (never fabricated)"
                ),
            )

        # Content acquisition: text directly; documents via caller-extracted text.
        if modality is MediaModality.TEXT:
            text = (attachment.content or attachment.extracted_text or "").strip()
            if not text:
                return IngestionResult(
                    IngestVerdict.MALFORMED,
                    modality=modality,
                    reason="text attachment carried no readable content",
                )
        else:  # DOCUMENT
            text = (attachment.extracted_text or "").strip()
            if not text:
                return IngestionResult(
                    IngestVerdict.DOCUMENT_PARSE_UNAVAILABLE,
                    modality=modality,
                    reason=(
                        "a raw document binary was supplied, but AURA has no "
                        "document parser; pass caller-extracted text or the "
                        "capability stays unavailable"
                    ),
                )
        bounded = text[: self._limits.max_content_chars]

        # Untrusted-content choke point (data, not instructions).
        decision = self._policy.check(bounded, source=attachment.source_id)
        if not decision.allowed:
            return IngestionResult(
                IngestVerdict.INJECTION_BLOCKED,
                modality=modality,
                reason=decision.reason,
            )

        observation = MultimodalObservation(
            observation_id=f"obs-{uuid.uuid4().hex[:16]}",
            modality=modality,
            source=attachment.source_id,
            owner_scope=attachment.owner_scope,
            content=bounded,
            trust=decision.trust,
            captured_at=now or datetime.now(UTC).isoformat(),
            provenance={
                "source": attachment.source_id,
                "modality": modality.value,
                "media_type": attachment.media_type,
                "size_bytes": attachment.size_bytes,
                "request_id": request_id,
                "file_name": attachment.file_name,
                "stage": "input.validation|multimodal.observation|context|reasoning",
            },
            verified=False,
        )
        return IngestionResult(
            IngestVerdict.ACCEPTED,
            modality=modality,
            reason="accepted as an untrusted, non-authorizing observation",
            observation_id=observation.observation_id,
            observation=observation,
        )

    def ingest_many(
        self,
        attachments: Iterable[RawAttachment],
        *,
        authorized: bool,
        request_id: str | None = None,
        token: CancellationToken | None = None,
        now: str | None = None,
    ) -> tuple[list[IngestionResult], list[MultimodalObservation]]:
        """Validate a batch, capping the number of accepted observations.

        Returns ``(results, accepted)`` so the caller can both report every
        attachment honestly (including rejections) and forward only accepted
        observations to reasoning.
        """
        results: list[IngestionResult] = []
        accepted: list[MultimodalObservation] = []
        for attachment in attachments:
            if len(accepted) >= self._limits.max_observations:
                results.append(
                    IngestionResult(
                        IngestVerdict.TOO_MANY,
                        modality=_modality_for(attachment.media_type),
                        reason=f"at most {self._limits.max_observations} observations are permitted per request",
                    )
                )
                continue
            result = self.ingest(
                attachment,
                authorized=authorized,
                request_id=request_id,
                token=token,
                now=now,
            )
            results.append(result)
            if result.accepted and result.observation is not None:
                accepted.append(result.observation)
        return results, accepted


def observation_grounding_item(observation: MultimodalObservation) -> GroundingItem:
    """Map one observation onto the canonical grounding contract.

    ``source`` is ``"observation"`` (distinct from ``memory``/``knowledge``),
    ``verified`` is always ``False``, and confidence is pinned below
    :data:`~aura.reasoning.models.OBSERVED_BELIEF` so the observation can be
    attributed in an answer but can never become a logical premise -- media is
    referenced, never treated as proof.
    """
    return GroundingItem(
        source="observation",
        reference=observation.observation_id,
        text=observation.content,
        score=OBSERVATION_SCORE,
        confidence=OBSERVATION_CONFIDENCE,
        verified=False,
        contradicted=False,
        scope=observation.owner_scope,
        provenance={
            **dict(observation.provenance),
            "observation_id": observation.observation_id,
            "modality": observation.modality.value,
        },
    )


#: Assert the invariant that makes observations non-authoritative.
assert OBSERVATION_CONFIDENCE * OBSERVATION_SCORE < OBSERVED_BELIEF


__all__ = [
    "CAPABILITY_UNAVAILABLE",
    "DEFAULT_MAX_BYTES",
    "DEFAULT_MAX_CONTENT_CHARS",
    "DEFAULT_MAX_OBSERVATIONS",
    "IngestVerdict",
    "IngestionResult",
    "InputLimits",
    "MediaModality",
    "MultimodalObservation",
    "OBSERVATION_CONFIDENCE",
    "OBSERVATION_SCORE",
    "ObservationGate",
    "RawAttachment",
    "SUPPORTED_MODALITIES",
    "input_limits",
    "observation_grounding_item",
]