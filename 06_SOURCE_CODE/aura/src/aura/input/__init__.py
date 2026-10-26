"""Input boundary: validation of untrusted external content.

Phase 1J adds the only genuinely missing seam in the canonical runtime: turning
untrusted uploaded/attached media into bounded, provenance-carrying observations
that reasoning may *reference* but never treat as instructions, verified facts,
or execution authority.

There is deliberately **no** "multimodal engine" here. Modalities the canonical
package genuinely cannot process (image, audio, video) are reported as
``capability unavailable`` by :class:`~aura.input.multimodal.ObservationGate`
rather than being faked. Only text and document-extracted text become
observations, and they never authorize execution.
"""

from aura.input.multimodal import (
    CAPABILITY_UNAVAILABLE,
    SUPPORTED_MODALITIES,
    MediaModality,
    MultimodalObservation,
    ObservationGate,
    RawAttachment,
    input_limits,
    observation_grounding_item,
)

__all__ = [
    "CAPABILITY_UNAVAILABLE",
    "MediaModality",
    "MultimodalObservation",
    "ObservationGate",
    "RawAttachment",
    "SUPPORTED_MODALITIES",
    "input_limits",
    "observation_grounding_item",
]