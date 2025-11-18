"""
Shared helpers for invoking the SDD CLI in integration tests.

This module centralises CLI execution so every test:
* Resolves the project root once
* Ensures the local `claude_skills` package is importable (via PYTHONPATH)
* Applies consistent subprocess defaults (text mode, captured output)
* Handles the `sdd` executable fallback behaviour used throughout tests
* Normalises global CLI flags so invocation order is stable
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Mapping, MutableMapping, Optional, Sequence

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parents[5]
SRC_PACKAGE_DIR = PROJECT_ROOT / "src" / "claude_skills"

# --------------------------------------------------------------------------- #
# CLI argument normalisation
# --------------------------------------------------------------------------- #

_GLOBAL_FLAGS_WITH_VALUES = {
    "--path",
    "--specs-dir",
    "--config",
}

_GLOBAL_FLAGS_BOOLEAN = {
    "--quiet",
    "-q",
    "--json",
    "--debug",
    "--verbose",
    "-v",
    "--no-color",
    "--rich-traceback",
}


def _normalise_cli_args(args: Sequence[object]) -> List[str]:
    """Reorder known global flags so they appear before subcommands."""
    stringified: List[str] = [str(arg) for arg in args]

    global_args: List[str] = []
    remaining_args: List[str] = []
    i = 0

    while i < len(stringified):
        arg = stringified[i]

        if arg in _GLOBAL_FLAGS_WITH_VALUES:
            global_args.append(arg)
            if i + 1 < len(stringified):
                global_args.append(stringified[i + 1])
                i += 2
            else:
                i += 1
        elif arg in _GLOBAL_FLAGS_BOOLEAN:
            global_args.append(arg)
            i += 1
        else:
            remaining_args.append(arg)
            i += 1

    return global_args + remaining_args


# --------------------------------------------------------------------------- #
# Environment helpers
# --------------------------------------------------------------------------- #

def _ensure_pythonpath(env: MutableMapping[str, str]) -> None:
    """Ensure PYTHONPATH contains the local claude_skills package path."""
    src_path = str(SRC_PACKAGE_DIR)
    existing = env.get("PYTHONPATH")
    if existing:
        paths = [entry for entry in existing.split(os.pathsep) if entry]
        if src_path not in paths:
            env["PYTHONPATH"] = os.pathsep.join([src_path] + paths)
    else:
        env["PYTHONPATH"] = src_path


def _build_env(overrides: Optional[Mapping[str, str]] = None) -> MutableMapping[str, str]:
    env: MutableMapping[str, str] = os.environ.copy()
    _ensure_pythonpath(env)
    if overrides:
        env.update(overrides)
    return env


# --------------------------------------------------------------------------- #
# Public helper
# --------------------------------------------------------------------------- #

def run_cli(
    *cli_args: object,
    check: bool = False,
    env: Optional[Mapping[str, str]] = None,
    reorder: bool = True,
    ensure_verbose: bool = True,
    **subprocess_kwargs,
):
    """
    Execute the SDD CLI with consistent defaults across integration tests.

    Args:
        *cli_args: CLI arguments passed to the command (may include Path objects).
        check: Forwarded to ``subprocess.run``.
        env: Optional environment overrides merged with the default environment.
        reorder: Whether to normalise global flag ordering.
        **subprocess_kwargs: Extra keyword arguments for ``subprocess.run``.

    Returns:
        subprocess.CompletedProcess: Result of the CLI execution.
    """

    arg_strings = [str(arg) for arg in cli_args]

    if ensure_verbose:
        has_verbosity_flag = any(
            flag in arg_strings for flag in ("--verbose", "-v", "--quiet", "-q")
        )
        if not has_verbosity_flag:
            arg_strings.insert(0, "--verbose")

    args = _normalise_cli_args(arg_strings) if reorder else arg_strings

    if "capture_output" not in subprocess_kwargs and not any(
        key in subprocess_kwargs for key in ("stdout", "stderr")
    ):
        subprocess_kwargs["capture_output"] = True
    subprocess_kwargs.setdefault("text", True)

    effective_env = _build_env(env)

    if os.environ.get("SDD_TEST_USE_BIN") and shutil.which("sdd"):
        command = ["sdd"] + args
    else:
        command = [sys.executable, "-m", "claude_skills.cli.sdd.__init__"] + args

    return subprocess.run(command, check=check, env=effective_env, **subprocess_kwargs)


__all__ = ["PROJECT_ROOT", "SRC_PACKAGE_DIR", "run_cli"]
