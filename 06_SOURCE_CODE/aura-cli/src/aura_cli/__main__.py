"""AURA CLI — real operations with stable behavior.

Usage:
    aura doctor | health | config validate | version | run <question>
    aura knowledge | plan <goal> | security audit [--yes] [--output json]

Stable exit codes (see ``aura_cli.core.result.ExitCode``), human-readable text
or JSON output, non-interactive mode, and confirmation-gated dangerous
operations.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from aura_cli import __version__
from aura_cli.app.commands import CommandDispatcher
from aura_cli.config.profiles import ProfileLoader
from aura_cli.core.result import CommandResult, ExitCode
from aura_cli.integrations.aura.runtime import RuntimeAdapter
from aura_cli.output.render import render_json, render_text
from aura_cli.security.gate import ConfirmationGate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aura", description="AURA intelligence platform CLI")
    parser.add_argument("--profile", default="default", help="configuration profile name")
    parser.add_argument("--output", choices=("text", "json"), default="text", help="output format")
    parser.add_argument("--non-interactive", action="store_true", help="fail closed on confirmation")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="environment and subsystem diagnostics")
    sub.add_parser("health", help="runtime + subsystem health")
    sub.add_parser("knowledge", help="exercise the aura-knowledge engine")
    sub.add_parser("version", help="print version")

    config_p = sub.add_parser("config", help="configuration operations")
    config_sub = config_p.add_subparsers(dest="config_action", required=True)
    config_sub.add_parser("validate", help="validate the active configuration profile")

    run_p = sub.add_parser("run", help="one-shot reasoning pass")
    run_p.add_argument("question", nargs="+")

    plan_p = sub.add_parser("plan", help="create a plan via the canonical planning engine")
    plan_p.add_argument("goal", nargs="+")

    audit_p = sub.add_parser("security", help="security operations")
    audit_sub = audit_p.add_subparsers(dest="security_action", required=True)
    audit_cmd = audit_sub.add_parser("audit", help="tail the security audit log")
    audit_cmd.add_argument("--yes", action="store_true", help="confirm dangerous operation")

    return parser


def _render(result: CommandResult, *, output_format: str) -> str:
    if output_format == "json":
        return render_json(result.to_dict())
    header = "ok" if result.exit_code == ExitCode.OK else f"failed (exit={result.exit_code})"
    return render_text(header, result.human_lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse uses exit code 2 for usage errors (unknown commands/options)
        return int(exc.code) if isinstance(exc.code, int) else ExitCode.FAILED

    try:
        profile = ProfileLoader().load(args.profile) if args.profile != "default" else None
    except Exception as exc:  # noqa: BLE001 - invalid profile -> stable exit code 2
        print(f"invalid configuration: {exc}", file=sys.stderr)
        return ExitCode.CONFIG_INVALID

    non_interactive = args.non_interactive or bool(profile and profile.non_interactive)
    gate = ConfirmationGate(non_interactive=non_interactive)
    dispatcher = CommandDispatcher(
        runtime=RuntimeAdapter(),
        profiles=ProfileLoader(),
        gate=gate,
    )

    command = args.command
    if command in ("doctor", "health", "knowledge", "version"):
        if command == "doctor":
            result = dispatcher.doctor()
        elif command == "health":
            result = dispatcher.health()
        elif command == "knowledge":
            result = dispatcher.knowledge()
        else:
            result = dispatcher.version(__version__)
    elif command == "config" and args.config_action == "validate":
        result = dispatcher.config_validate(args.profile)
    elif command == "run":
        result = dispatcher.run(" ".join(args.question))
    elif command == "plan":
        result = dispatcher.plan(" ".join(args.goal))
    elif command == "security" and args.security_action == "audit":
        result = dispatcher.security_audit(confirmed=args.yes)
    else:
        parser.print_help()
        return ExitCode.OK

    output = _render(result, output_format=args.output or "text")
    if result.exit_code == ExitCode.OK:
        print(output)
    else:
        print(output, file=sys.stderr)
    return result.exit_code


__all__ = ["build_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())