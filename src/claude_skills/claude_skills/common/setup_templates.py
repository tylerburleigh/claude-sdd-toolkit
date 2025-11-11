"""
Helpers for working with packaged setup templates.

This module provides a small facade around ``importlib.resources`` so callers
can discover, load, and copy the bundled setup templates that live under
``claude_skills.common.templates.setup``.  It keeps a stable filesystem path
for each template (even when the package is installed as a zip) and exposes
utility helpers for common access patterns.
"""

from __future__ import annotations

import atexit
import json
import shutil
from contextlib import ExitStack
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from .templates import SETUP_TEMPLATE_PACKAGE


_exit_stack = ExitStack()
atexit.register(_exit_stack.close)

_TEMPLATE_CACHE: dict[str, Path] = {}


def _resolve_template_resource(template_name: str) -> resources.abc.Traversable:
    resource = resources.files(SETUP_TEMPLATE_PACKAGE).joinpath(template_name)
    if not resource.is_file():
        raise FileNotFoundError(
            f"No setup template named '{template_name}' found in "
            f"{SETUP_TEMPLATE_PACKAGE}"
        )
    return resource


def get_template(template_name: str) -> Path:
    """
    Return a filesystem ``Path`` to the packaged template.

    The first time a template is requested it is materialised via
    ``importlib.resources.as_file`` and cached so subsequent callers receive a
    stable path without repeatedly creating temporary files.
    """

    if template_name not in _TEMPLATE_CACHE:
        resource = _resolve_template_resource(template_name)
        cached_path = _exit_stack.enter_context(resources.as_file(resource))
        _TEMPLATE_CACHE[template_name] = Path(cached_path)
    return _TEMPLATE_CACHE[template_name]


def load_json_template(template_name: str) -> Any:
    """
    Load a JSON template into native Python data structures.
    """

    path = get_template(template_name)
    with path.open(encoding="utf-8") as template_file:
        return json.load(template_file)


def load_yaml_template(template_name: str) -> Any:
    """
    Load a YAML template into native Python data structures.
    """

    path = get_template(template_name)
    with path.open(encoding="utf-8") as template_file:
        return yaml.safe_load(template_file)


def strip_template_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """
    Remove template metadata fields from a dictionary.

    Template metadata fields are keys that start with an underscore (_). These
    fields are used to document templates (e.g., _comment, _description,
    _enabled_description) but should not be copied into actual configuration
    files.

    Args:
        data: Dictionary potentially containing metadata fields

    Returns:
        New dictionary with metadata fields removed
    """
    return {k: v for k, v in data.items() if not k.startswith("_")}


def load_json_template_clean(template_name: str) -> Any:
    """
    Load a JSON template and strip metadata fields.

    This is a convenience wrapper around load_json_template() that automatically
    removes fields starting with underscore (_) which are used for template
    documentation but should not appear in actual configuration files.

    Args:
        template_name: Name of the template file to load

    Returns:
        Template data with metadata fields removed
    """
    data = load_json_template(template_name)
    if isinstance(data, dict):
        return strip_template_metadata(data)
    return data


def copy_template_to(
    template_name: str, destination: Path | str, *, overwrite: bool = False
) -> Path:
    """
    Copy a packaged template to ``destination``.

    ``destination`` may be a directory (in which case the template filename is
    appended) or a full path to the target file.  When ``overwrite`` is False
    (the default) an existing file will raise ``FileExistsError``.
    """

    source_path = get_template(template_name)
    target_path = Path(destination)
    if target_path.is_dir():
        target_path = target_path / source_path.name

    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists():
        if not overwrite:
            raise FileExistsError(
                f"Destination file '{target_path}' already exists. "
                "Pass overwrite=True to replace it."
            )
        if target_path.is_file():
            target_path.unlink()

    shutil.copy2(source_path, target_path)
    return target_path


__all__ = [
    "get_template",
    "load_json_template",
    "load_json_template_clean",
    "load_yaml_template",
    "strip_template_metadata",
    "copy_template_to",
]
