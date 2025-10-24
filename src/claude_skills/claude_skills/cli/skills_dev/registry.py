"""Plugin registration for skills development utilities."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import runpy
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from claude_skills.common import PrettyPrinter


@dataclass
class LegacyCommand:
    name: str
    help: str
    entry_point: str
    passthrough: bool = True
    deprecated: bool = False


LEGACY_COMMANDS: list[LegacyCommand] = [
    LegacyCommand(
        name="gendocs",
        help="Generate SKILL.md documentation from CLI definitions",
        entry_point="claude_skills.dev_tools.generate_docs",
    ),
    LegacyCommand(
        name="start-helper",
        help="Run sdd-start helper utilities",
        entry_point="claude_skills.dev_tools.sdd_start_helper",
    ),
    LegacyCommand(
        name="setup-permissions",
        help="Setup SDD project permissions",
        entry_point="claude_skills.dev_tools.setup_project_permissions",
    ),
]


def _run_legacy_main(
    module_name: str, argv: Sequence[str], printer: PrettyPrinter
) -> int:
    """Execute a legacy CLI module's main() while preserving sys.argv."""
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:  # pragma: no cover - defensive
        printer.error(f"Legacy command '{module_name}' is unavailable: {exc}")
        return 1

    if not hasattr(module, "main"):
        printer.error(
            f"Legacy module '{module_name}' does not expose a main() function"
        )
        return 1

    original_argv = sys.argv
    sys.argv = [module_name.replace(".", "-")] + list(argv)
    try:
        result = module.main()
        return int(result or 0)
    except SystemExit as exc:
        # Some legacy scripts still call sys.exit
        return int(getattr(exc, "code", 0) or 0)
    finally:
        sys.argv = original_argv


def _configure_passthrough(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to the legacy command",
    )


def _make_wrapper(cmd: LegacyCommand):
    def _handler(args: argparse.Namespace, printer: PrettyPrinter) -> int:
        if cmd.deprecated:
            printer.warning(
                f"Command '{cmd.name}' is deprecated and may be removed in a future release."
            )

        passthrough_args = getattr(args, "args", [])
        if passthrough_args and passthrough_args[0] == "--":
            passthrough_args = passthrough_args[1:]

        printer.info(
            "Delegating to legacy entry point '%s' with %d argument(s)"
            % (cmd.entry_point, len(passthrough_args))
        )
        return _run_legacy_main(cmd.entry_point, passthrough_args, printer)

    return _handler


def register_all_subcommands(subparsers: Any, parent_parser: argparse.ArgumentParser) -> None:
    """Register all skills-dev subcommands."""
    if not isinstance(
        subparsers, argparse._SubParsersAction
    ):  # pragma: no cover - defensive
        raise TypeError("subparsers must be an argparse._SubParsersAction")

    for cmd in LEGACY_COMMANDS:
        parser = subparsers.add_parser(cmd.name, parents=[parent_parser], help=cmd.help)
        if cmd.passthrough:
            _configure_passthrough(parser)
        parser.set_defaults(func=_make_wrapper(cmd))

    # Placeholder for future native commands
    placeholder = subparsers.add_parser(
        "migrate",
        parents=[parent_parser],
        help="Show migration guidance for legacy skills development commands",
    )
    placeholder.set_defaults(func=_show_migration_info)


def _show_migration_info(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    printer.header("Skills-Dev CLI Migration")
    printer.detail(
        "Legacy commands are now available under the unified 'skills-dev' CLI."
    )
    printer.blank()
    for cmd in LEGACY_COMMANDS:
        legacy_name = cmd.entry_point.split(".")[-1]
        printer.item(f"skills-dev {cmd.name} -- → {legacy_name}")
    printer.blank()
    printer.detail("Pass legacy arguments after '--'. Example:")
    printer.detail("skills-dev gendocs -- sdd-validate --sections commands", indent=1)
    return 0
