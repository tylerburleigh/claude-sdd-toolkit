"""
Utilities for discovering and loading JSON schemas used by SDD skills.

Prefers schemas shipped in the Claude plugin cache and gracefully falls back to
package resources when running from an installed wheel or source checkout.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


_SCHEMA_PACKAGE = "claude_skills.schemas"
_SCHEMA_ENV_OVERRIDE = "CLAUDE_SDD_SCHEMA_CACHE"
_PLUGIN_CACHE_SUBPATH = Path(".claude/plugins/cache/sdd-toolkit/src/claude_skills/schemas")


def _unique(paths: Iterable[Path]) -> List[Path]:
    """Return paths with duplicates removed while preserving order."""

    seen: set[Path] = set()
    ordered: List[Path] = []
    for candidate in paths:
        expanded = candidate.expanduser()
        resolved = expanded.resolve()
        if resolved not in seen:
            seen.add(resolved)
            ordered.append(resolved)
    return ordered


def _candidate_paths(schema_name: str) -> List[Path]:
    """Generate candidate filesystem paths for a schema."""

    candidates: List[Path] = []

    override = os.environ.get(_SCHEMA_ENV_OVERRIDE)
    if override:
        candidates.append(Path(override).expanduser() / schema_name)

    plugin_candidate = Path.home() / _PLUGIN_CACHE_SUBPATH / schema_name
    candidates.append(plugin_candidate)

    # Source checkout fallback (e.g., running from repository)
    local_candidate = Path(__file__).resolve().parent.parent / "schemas" / schema_name
    candidates.append(local_candidate)

    return _unique(candidates)


@lru_cache(maxsize=None)
def load_json_schema(schema_name: str) -> Tuple[Optional[Dict], Optional[str], Optional[str]]:
    """
    Load a JSON schema by name.

    Args:
        schema_name: File name of the schema (e.g., 'sdd-spec-schema.json').

    Returns:
        Tuple of (schema_dict, source_description, error_message).
        If schema_dict is None, error_message will contain the reason.
    """

    errors: List[str] = []

    for candidate in _candidate_paths(schema_name):
        try:
            if candidate.is_file():
                return json.loads(candidate.read_text(encoding="utf-8")), str(candidate), None
        except Exception as exc:  # pragma: no cover - diagnostics only
            errors.append(f"{candidate}: {exc}")

    try:
        schema_resource = resources.files(_SCHEMA_PACKAGE).joinpath(schema_name)
    except (ModuleNotFoundError, AttributeError):
        schema_resource = None

    if schema_resource and schema_resource.is_file():
        try:
            with schema_resource.open("r", encoding="utf-8") as fh:
                return json.load(fh), f"package:{_SCHEMA_PACKAGE}/{schema_name}", None
        except Exception as exc:  # pragma: no cover - diagnostics only
            errors.append(f"{_SCHEMA_PACKAGE}/{schema_name}: {exc}")
    else:
        errors.append(f"Schema '{schema_name}' not found in plugin cache or package resources.")

    error_msg = "; ".join(errors) if errors else "Schema not found"
    return None, None, error_msg
