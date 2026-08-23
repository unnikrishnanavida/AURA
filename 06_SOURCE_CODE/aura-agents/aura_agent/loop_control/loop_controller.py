"""Loop control: detects repetition, oscillation, and stagnation.

Loop control is a distinct concern from recovery: recovery decides what to do
about a *single* failed action; loop control detects that the *agent* is
repeating itself without making progress and forces a strategy change or
termination.

Detection is deterministic and based purely on recorded action history.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["LoopSignal", "LoopController", "LoopReason"]


class LoopReason:
    """Enum-like constants for loop-detection reasons."""

    REPETITION = "repetition"
    OSCILLATION = "oscillation"
    STAGNATION = "stagnation"
    EXCESSIVE_RETRIES = "excessive_retries"


@dataclass(frozen=True)
class LoopSignal:
    """A detection signal identifying a loop condition."""

    reason: str
    detail: str


@dataclass
class LoopController:
    """Tracks action history and raises :class:`LoopDetected` when the
    strategy loop is not making progress."""

    max_repetitions: int = 3
    max_oscillations: int = 3
    max_same_failures: int = 3
    history: list[str] = field(default_factory=list)

    def reset(self) -> None:
        self.history.clear()

    def record(self, action_signature: str) -> list[LoopSignal]:
        """Record an executed action and return any loop signals.

        A signature is a unique string for a *trying the same thing*, e.g.
        ``"tool:write_file,path=/tmp/x"``. Signatures are produced by the
        caller (the cognitive loop).
        """
        self.history.append(action_signature)
        signals: list[LoopSignal] = []

        # repetition: same action N times in a row
        if len(self.history) >= self.max_repetitions and all(
            s == action_signature
            for s in self.history[-self.max_repetitions :]
        ):
            signals.append(
                LoopSignal(
                    LoopReason.REPETITION,
                    f"same action repeated {self.max_repetitions} times: {action_signature!r}",
                )
            )

        # oscillation: alternating between two actions
        if len(self.history) >= 4:
            tail = self.history[-4:]
            if tail[0] == tail[2] and tail[1] == tail[3] and tail[0] != tail[1]:
                signals.append(
                    LoopSignal(
                        LoopReason.OSCILLATION,
                        f"oscillation detected over the last 4 steps {tail!r}",
                    )
                )
        return signals
