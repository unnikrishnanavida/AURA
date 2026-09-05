# AURA — Autonomous Universal Reasoning Architecture

AURA is a coherent, integrated intelligence infrastructure. It is not a
chatbot wrapper and not a collection of disconnected AI engines: memory,
knowledge, reasoning, planning, reflection, learning, execution, security,
observability, replay, and provenance operate as one system with explicit
boundaries and an honest, uncertainty-first epistemology.

```python
from aura import Aura

aura = Aura()

result = aura.reason("is production ready?")
# {'execution_id': 'ex-...', 'answer': 'I do not know', 'confidence': 0.0, ...}
```

## Architecture

```
src/aura/
├─ foundation     ids, errors, results, clocks, lifecycle, cancellation, validation
├─ config         pydantic-typed, validated, layered (defaults → file → env)
├─ core           bootstrap, DI container, component registry, lifecycle mgr, health
├─ memory         working / episodic / semantic / procedural + confidence + provenance
├─ knowledge      claims, evidence, sources, trust, verification, contradictions
├─ reasoning      6 deterministic strategies + consensus + verification, uncertainty-first
├─ research       epistemic ledger, claim passports, reproducibility capsules
├─ planning       goal decomposition, constraints, risk analysis, plan alternatives
├─ reflection     post-execution review, lessons, counterfactuals
├─ learning       validated signal gate, versioned registry, rollback, authorization
├─ execution      WorldState ⊥ ActionInputs, guardrail pipeline, retry, timeout, idempotency
├─ security       capabilities, policies (default deny), safety, autonomy, budgets, guardrails
├─ observability  structured logs, metrics, flight recorder, provenance graph, replay
├─ providers      provider profiles + embedded deterministic provider
├─ brain          cognitive orchestration of the whole lifecycle
├─ sdk            `aura.Aura` public facade
├─ api            dependency-light HTTP service (health/ready/reason/replay/openapi)
└─ cli            doctor | health | ready | config validate | run | replay | security | audit | version
```

## Installation

```bash
pip install -e ".[dev]"
```

Requires Python ≥ 3.11. Runtime dependencies: `pydantic>=2`, `PyYAML>=6`.

## Quick start

```python
from aura import Aura
from aura.planning.models import Goal, Task

aura = Aura()

# memory
aura.remember("deploy", {"status": "green"})

# plan
aura.plan(
    goal=Goal.create(description="ship"),
    tasks=[Task(name="build"), Task(name="ship", prerequisites=("build",))],
)

# replay + provenance
execution_id = aura.reason("why is the sky blue?", facts={"physics": 0.8})["execution_id"]
aura.replay(execution_id)
aura.provenance(execution_id)
```

## CLI

```
aura doctor            environment + import diagnostics
aura health            aggregate engine health
aura ready             readiness probe
aura config validate   validate configuration
aura run "<question>"  one-shot reasoning pass
aura replay <exec_id>  replay a recorded execution
aura audit             tail the audit log
aura version           print version
```

## Security model

- Default-deny permission policy; every decision is explainable.
- Actions require explicit capabilities; safety → autonomy → budget gates
  cannot be bypassed by autonomy or approval.
- Learning is validated and gated; safety-relevant signals require explicit
  authorization and are rollback-able by versioned registry.
- Secrets are typed (`SecretStr`) and redacted everywhere; logs never carry
  passwords, tokens, or keys.
- Audit log is append-only for all security-relevant decisions.

## Testing

```
python -m pytest tests -q        # 156 unit + integration tests
python -m ruff check src tests    # lint
python -m mypy src                # strict typing
```

## Key concepts

- **Uncertainty-first:** with insufficient evidence the answer is
  `"I do not know"` at confidence `0.0` — AURA never invents certainty.
- **Evidence ≠ claim:** knowledge separates claims, evidence, sources,
  verification, and contradiction.
- **RECORDED ≠ RECONSTRUCTED:** replay flags state origin explicitly; no
  false claims of deterministic reconstruction of nondeterministic inputs.
- **WorldState ⊥ ActionInputs:** execution never mixes the world with action
  arguments; effects are declared.

## Limitations

- The embedded reasoning provider is deterministic and offline; external
  provider SDK adapters are interfaces awaiting credentials.
- Persistence is in-memory by default; SQLite/PostgreSQL adapters are future work.
- Kubernetes manifests are intentionally deferred until cluster-validated.

## License

Apache-2.0