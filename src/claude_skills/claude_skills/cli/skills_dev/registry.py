"""Plugin registration for skills development utilities."""

from __future__ import annotations

import argparse
from typing import Any

from claude_skills.common import PrettyPrinter


def register_all_subcommands(subparsers: Any, parent_parser: argparse.ArgumentParser) -> None:
    """Register all skills-dev subcommands.

    This is a placeholder for future native skills-dev commands.
    The legacy dev_tools commands have been removed.
    """
    if not isinstance(
        subparsers, argparse._SubParsersAction
    ):  # pragma: no cover - defensive
        raise TypeError("subparsers must be an argparse._SubParsersAction")

    # Placeholder for future native commands
    # Native commands can be registered here when implemented
