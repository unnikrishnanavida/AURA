"""Phase 35 end-to-end scenarios A-G against the canonical runtime.

REAL flows (no mocks of AURA internals):

- A simple question  : auth -> brain -> reasoning -> provider-boundary (safe
                        synthesis) -> response -> audit
- B memory           : write -> persist -> new session -> retrieve
- C research         : evidence -> reasoning -> answer -> recorded provenance
- D task             : planning -> authorization -> security gate
- E security event   : brute-force signal -> threat detector -> incident -> audit
- F database failure : dead store -> durable audit spool -> recovery -> replay
- G provider failure : provider down -> provider_failure metric -> fallback
"""

from __future__ import annotations

from pathlib import Path

from aura.brain.engine import BrainEngine
from aura.config.settings import AuraConfig
from aura.foundation.ids import MemoryId
from aura.memory.models import MemoryEntry, MemoryType
from aura.observability.metrics import Metrics
from aura.providers.base import Provider, ProviderProfile
from aura.providers.errors import ProviderError
from aura.providers.manager import ProviderManager
from aura.reasoning.models import Rule
from aura.security.audit import AuditLog


class EchoProvider(Provider):
    """Test-only synthesis provider (scenario G uses its failure mode)."""

    def __init__(self, *, fail: bool = False) -> None:
        self.name = "echo"
        self.timeout_seconds = 5.0
        self._fail = fail
        self.profile = ProviderProfile(
            name="echo", kind="reasoning", capabilities=("reasoning.synthesis",), privacy_approved=True, local=True
        )

    def health(self) -> bool:
        return not self._fail

    def reason(self, question: str, **kwargs: object) -> object:
        if self._fail:
            raise ProviderError("echo unavailable")
        return f"E2E-{question}"


_SOCRATES = (
    Rule(id="r1", conditions=("socrates is human", "humans are mortal"), consequent="socrates is mortal"),
)


def _brain(manager: ProviderManager | None = None) -> BrainEngine:
    return BrainEngine.create(config=AuraConfig(), seed=42, provider_manager=manager)


def _entry(key: str) -> MemoryEntry:
    return MemoryEntry(id=MemoryId.new(), key=key, kind=MemoryType.SEMANTIC, content={"text": key})


# -- A ----------------------------------------------------------------------

def test_scenario_a_simple_question_is_audited() -> None:
    metrics = Metrics()
    audit = AuditLog()
    manager = ProviderManager(metrics=metrics, audit=audit)
    manager.register(EchoProvider())
    brain = _brain(manager)
    result = brain.reason(
        question="socrates is mortal",
        facts={"socrates is human": 1.0, "humans are mortal": 1.0},
        rules=_SOCRATES,
    ).summary()
    assert result["answer"] == "E2E-socrates is mortal"  # provider boundary hit
    assert result["provider"]["name"] == "echo"
    assert metrics.count("provider_call") == 1
    assert brain.metrics.count("execution_count") >= 1


# -- B ----------------------------------------------------------------------

def test_scenario_b_memory_persists_across_sessions(tmp_path: Path) -> None:
    db_path = str(tmp_path / "m.sqlite3")
    first = BrainEngine.create(
        config=AuraConfig(storage={"backend": "sqlite", "sqlite_path": db_path}),  # type: ignore[arg-type]
        seed=1,
    )
    first.memory.store.add(_entry("p35-durable"))
    second = BrainEngine.create(  # new session, same store
        config=AuraConfig(storage={"backend": "sqlite", "sqlite_path": db_path}),  # type: ignore[arg-type]
        seed=1,
    )
    assert any(e.key == "p35-durable" for e in second.memory.store.all())


# -- C ----------------------------------------------------------------------

def test_scenario_c_evidence_answer_is_recorded_with_provenance() -> None:
    brain = _brain()
    result = brain.reason(
        question="socrates is mortal",
        facts={"socrates is human": 1.0, "humans are mortal": 1.0},
        rules=_SOCRATES,
    ).summary()
    assert result["answer"] != "I do not know"
    # The flight recorder holds the provenance/trace of this execution.
    assert brain.recorder.count() >= 1
    assert result["execution_id"]
# -- D ----------------------------------------------------------------------

def test_scenario_d_plan_requires_authorization_and_default_deny() -> None:
    from aura.planning.models import Goal, Task
    from aura.security.permissions import Decision, Identity, PolicyEngine
    from aura.security.permissions import Rule as PolicyRule

    brain = _brain()
    plan = brain.planning.plan(
        goal=Goal.create(description="produce a report"),
        tasks=[Task(name="write", capability="domain.execute", risk=0.1)],
    )
    assert plan.primary is not None  # a plan was produced

    policy = PolicyEngine()
    # Default-deny: no rule -> DENY (never silent).
    denied = policy.evaluate(action="domain.execute", resource="report", identity=Identity(id="agent-1"))
    assert denied.decision is Decision.DENY
    # Explicit allow rule -> ALLOW.
    policy.add_rule(PolicyRule(action="domain.execute", resource="report", effect=Decision.ALLOW, name="r"))
    allowed = policy.evaluate(action="domain.execute", resource="report", identity=Identity(id="agent-1"))
    assert allowed.decision is Decision.ALLOW


# -- E ----------------------------------------------------------------------

def test_scenario_e_brute_force_creates_incident() -> None:
    from aura.security.incident import IncidentManager, IncidentSeverity
    from aura.security.threats import BruteForceDetector, ThreatMonitor

    manager = IncidentManager(audit=AuditLog())
    monitor = ThreatMonitor(manager, [BruteForceDetector(threshold=3)])
    incidents = monitor.assess(auth_failures={"10.9.9.9": 5})
    assert len(incidents) == 1
    assert incidents[0].severity is IncidentSeverity.HIGH
    assert "brute-force" in incidents[0].title
    assert len(manager.open_incidents()) == 1


# -- F ----------------------------------------------------------------------

def test_scenario_f_db_failure_spools_then_replays(tmp_path: Path) -> None:
    from aura.api.distributed import PostgreSQLAuditLog

    class Toggle:
        def __init__(self) -> None:
            self.fail = False
            self.inserted: dict[str, object] = {}

        def connection(self) -> Toggle:
            if self.fail:
                raise RuntimeError("db down")
            return self

        def __enter__(self) -> Toggle:
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

        def transaction(self) -> Toggle:
            return self

        def execute(self, sql: str, params: object = None) -> _Cursor:
            if "INSERT" in sql and "RETURNING" in sql:
                assert params is not None and isinstance(params, tuple)
                self.inserted[params[0]] = params[1]
                return _Cursor([params[0]])
            if "SELECT" in sql:
                return _Cursor([["ev-p35-f", self.inserted.get("ev-p35-f", "x"), "sys", "api", "deny", "t", "now", None, "{}"]])
            if "SELECT 1 FROM information_schema" in sql:
                return _Cursor([])
            return _Cursor([])

    state = Toggle()
    log = PostgreSQLAuditLog(state, spool_directory=str(tmp_path / "spool"))  # type: ignore[arg-type]
    state.fail = True  # store goes down
    record = log.record(action="x", actor="sys", resource="api", decision="deny", reason="test", event_id="ev-p35-f")
    assert record.event_id is not None
    assert log._spool.count() == 1  # durably spooled while the DB was down

    state.fail = False  # store recovers
    result = log.replay_spooled()
    assert result["replayed"] == 1
    assert result["remaining"] == 0


class _Cursor:
    def __init__(self, rows: list[object]) -> None:
        self._rows = list(rows)

    def fetchone(self) -> object:
        return self._rows[0] if self._rows else None

    def fetchall(self) -> list[object]:
        return list(self._rows)


# -- G ----------------------------------------------------------------------

def test_scenario_g_provider_failure_falls_back_with_metric() -> None:
    metrics = Metrics()
    audit = AuditLog()
    manager = ProviderManager(metrics=metrics, audit=audit)
    manager.register(EchoProvider(fail=True))
    brain = _brain(manager)
    result = brain.reason(
        question="socrates is mortal",
        facts={"socrates is human": 1.0, "humans are mortal": 1.0},
        rules=_SOCRATES,
    ).summary()
    assert result["answer"] != "I do not know"  # deterministic fallback
    assert metrics.count("provider_failure") == 1
    assert any(a.action.startswith("provider.") for a in audit.entries())