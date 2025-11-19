"""Plugin registration for skills development utilities."""

from __future__ import annotations

import argparse
from typing import Any

from claude_skills.common import PrettyPrinter


def register_all_subcommands(subparsers: Any, parent_parser: argparse.ArgumentParser) -> None:
    """Register all skills-dev subcommands.

    Provides development utilities for maintaining the claude_skills package.
    """
    if not isinstance(
        subparsers, argparse._SubParsersAction
    ):  # pragma: no cover - defensive
        raise TypeError("subparsers must be an argparse._SubParsersAction")

    # Import and register all skills-dev commands
    from .start_helper import register_start_helper
    from .setup_permissions import register_setup_permissions
    from .gendocs import register_gendocs
    from .migrate import register_migrate
    from .install_helper import register_install_helper

    # Register commands
    register_start_helper(subparsers, parent_parser)
    register_setup_permissions(subparsers, parent_parser)
    register_gendocs(subparsers, parent_parser)
    register_migrate(subparsers, parent_parser)
    register_install_helper(subparsers, parent_parser)
