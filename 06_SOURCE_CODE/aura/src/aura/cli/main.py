"""AURA CLI implementation (argparse-based, no framework dependency)."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from aura import __version__
from aura.config.loader import load_settings
from aura.foundation.errors import ConfigurationError
from aura.sdk.client import Aura


class _Cmd:
    def __init__(self) -> None:
        self.aura = Aura()

    def doctor(self) -> int:
        import importlib.util

        checks: list[tuple[str, bool, str]] = []
        for name in ["yaml", "pytest", "mypy", "ruff"]:
            checks.append((f"{name} available", importlib.util.find_spec(name) is not None, name))
        modules = {
            "foundation": "aura.foundation",
            "config": "aura.config",
            "memory": "aura.memory",
            "knowledge": "aura.knowledge",
            "reasoning": "aura.reasoning",
            "planning": "aura.planning",
            "reflection": "aura.reflection",
            "learning": "aura.learning",
            "brain": "aura.brain",
            "sdk": "aura.sdk",
        }
        for _label, module in modules.items():
            try:
                __import__(module)
                checks.append((f"{module} imports", True, ""))
            except Exception as exc:
                checks.append((f"{module} imports", False, str(exc)))
        for label, ok, detail in checks:
            status = "ok" if ok else "MISSING"
            print(f"{'[ok]' if ok else '[--]'} {label}: {status} {detail}")
        return 0 if all(ok for _, ok, _ in checks) else 1

    def health(self) -> int:
        print(json.dumps(self.aura.health(), indent=2, sort_keys=True))
        return 0

    def ready(self) -> int:
        health = self.aura.health()
        ready = health["status"] == "ok"
        store = getattr(getattr(getattr(self.aura, "brain", None), "memory", None), "store", None)
        count: object = "unknown"
        probe = getattr(store, "count", None)
        if callable(probe):
            try:
                count = probe()
            except Exception as exc:  # noqa: BLE001 - a dead backend means not ready
                ready = False
                count = f"unavailable: {exc}"
        print(json.dumps({"status": "ready" if ready else "not_ready", "store_entries": count}, sort_keys=True))
        return 0 if ready else 1

    def config_validate(self) -> int:
        try:
            cfg = load_settings()
        except ConfigurationError as exc:
            print(f"invalid configuration: {exc}", file=sys.stderr)
            return 1
        print("configuration valid")
        print(f"  environment={cfg.environment.value}")
        print(f"  instance_id={cfg.instance_id}")
        print(f"  reasoning_seed={cfg.engines.reasoning_seed}")
        print(f"  max_actions={cfg.budgets.max_actions}")
        return 0

    def run(self, question: str) -> int:
        result = self.aura.reason(question)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    def replay(self, execution_id: str) -> int:
        try:
            print(json.dumps(self.aura.replay(execution_id), indent=2, sort_keys=True))
            return 0
        except Exception as exc:
            print(f"replay failed: {exc}", file=sys.stderr)
            return 1

    def security_status(self) -> int:
        health = self.aura.health()
        learning_health = self.aura.brain.learning.health()
        profile = self.aura.provider_profile
        print("AURA security posture (real runtime state)")
        print(f"  engine health: {health.get('status')} ({health.get('recorded_events', 0)} recorded events)")
        print(f"  learning registry: {learning_health.get('active_changes', 0)} active applied change(s)")
        print(f"  provider: {profile.name} (local={profile.local}, privacy_approved={profile.privacy_approved})")
        if not profile.local:
            print("  note: configured provider is remote; live connectivity is NOT verified by this command")
        return 0

    def audit(self, limit: int) -> int:
        from aura.security.audit import audit_log

        entries = audit_log().entries()[-limit:]
        for entry in entries:
            print(json.dumps(entry.to_dict(), sort_keys=True))
        return 0

    def version(self) -> int:
        print(__version__)
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aura", description="AURA intelligence platform")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("doctor", help="environment and import diagnostics")
    sub.add_parser("health", help="aggregate engine health")
    sub.add_parser("ready", help="readiness probe")
    sub.add_parser("config", help="validate configuration").add_argument("action", choices=["validate"])
    sub.add_parser("version", help="print version")
    run_p = sub.add_parser("run", help="one-shot reasoning pass")
    run_p.add_argument("question", nargs="+")
    replay_p = sub.add_parser("replay", help="replay a recorded execution")
    replay_p.add_argument("execution_id")
    sub.add_parser("security", help="security posture").add_argument("action", choices=["status"])
    audit_p = sub.add_parser("audit", help="tail audit entries")
    audit_p.add_argument("--limit", type=int, default=20)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = _Cmd()

    command = getattr(args, "command", None)
    if command == "doctor":
        return cmd.doctor()
    if command == "health":
        return cmd.health()
    if command == "ready":
        return cmd.ready()
    if command == "config":
        return cmd.config_validate()
    if command == "version":
        return cmd.version()
    if command == "run":
        question = " ".join(args.question)
        return cmd.run(question)
    if command == "replay":
        return cmd.replay(args.execution_id)
    if command == "security":
        return cmd.security_status()
    if command == "audit":
        return cmd.audit(args.limit)
    parser.print_help()
    return 0


__all__ = ["build_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
