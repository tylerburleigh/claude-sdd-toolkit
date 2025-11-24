"""
Utilities for bootstrapping `.claude/ai_config.yaml` during project setup.

This helper centralises the logic for copying the packaged AI configuration
template (or falling back to a minimal default) into a target project. The
unified CLI delegates to this module to guarantee `ai_config.yaml` is always
created during setup.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .setup_templates import copy_template_to, get_template

__all__ = ["AIConfigSetupResult", "ensure_ai_config", "copy_ai_config_template"]


_MINIMAL_TEMPLATE = """# Centralized AI Model Consultation Configuration
#
# This file defines default AI tool settings for the SDD Toolkit. You can
# customise tools, model priorities, consensus rules, and per-skill overrides.
# Generated automatically during `sdd-setup`.
#
# Tip: You can override these defaults at run time with CLI flags such as
# `--model gemini=gemini-2.5-flash` or `--model cursor-agent=composer-2`.

tools:
  gemini:
    command: gemini
    enabled: true
    description: Strategic analysis and hypothesis validation
  cursor-agent:
    command: cursor-agent
    enabled: true
    description: Repository-wide pattern discovery
  codex:
    command: codex
    enabled: false
    description: Code-level review and bug fixes

models:
  gemini:
    priority:
      - pro
  cursor-agent:
    priority:
      - composer-1
  codex:
    priority:
      - gpt-5.1-codex

run-tests:
  models:
    overrides:
      failure_type:
        assertion:
          gemini: pro
        timeout:
          cursor-agent: composer-1

sdd-plan-review:
  models:
    overrides:
      review_type:
        full:
          gemini: pro
        quick:
          cursor-agent: composer-1

sdd-render:
  models:
    overrides:
      feature:
        executive_summary:
          gemini: pro
        narrative:
          cursor-agent: composer-1

consensus:
  agents:
    - cursor-agent
    - gemini
    - codex
  auto_trigger:
    default: false
    assertion: true
    exception: true
    fixture: true
    import: false
    timeout: true
    flaky: false
    multi-file: true

consultation:
  timeout_seconds: 600
"""


@dataclass
class AIConfigSetupResult:
    """Structured result describing ai_config bootstrap outcome."""

    success: bool
    message: str
    created: bool
    path: Path
    template_source: Optional[Path] = None

    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation of the result."""
        return {
            "success": self.success,
            "message": self.message,
            "created": self.created,
            "path": str(self.path),
            "template_source": str(self.template_source) if self.template_source else None,
        }


def copy_ai_config_template(destination: Path | str, *, overwrite: bool = False) -> Path:
    """
    Copy the packaged ai_config.yaml template to ``destination``.
    """

    return copy_template_to("ai_config.yaml", destination, overwrite=overwrite)


def ensure_ai_config(project_root: Path | str) -> AIConfigSetupResult:
    """
    Ensure `.claude/ai_config.yaml` exists within a project.

    Args:
        project_root: Path-like pointing at the project where configuration should live.

    Returns:
        AIConfigSetupResult describing whether the file was created.
    """
    project_path = Path(project_root).resolve()
    claude_dir = project_path / ".claude"
    ai_config_path = claude_dir / "ai_config.yaml"

    try:
        claude_dir.mkdir(parents=True, exist_ok=True)

        if ai_config_path.exists():
            return AIConfigSetupResult(
                success=True,
                message="ai_config.yaml already exists",
                created=False,
                path=ai_config_path,
            )

        try:
            template_path = get_template("ai_config.yaml")
        except FileNotFoundError:
            template_path = None

        if template_path and template_path.exists():
            shutil.copy2(template_path, ai_config_path)
            return AIConfigSetupResult(
                success=True,
                message=f"Copied ai_config.yaml from template to {ai_config_path}",
                created=True,
                path=ai_config_path,
                template_source=template_path,
            )

        ai_config_path.write_text(_MINIMAL_TEMPLATE)
        return AIConfigSetupResult(
            success=True,
            message=f"Created minimal ai_config.yaml at {ai_config_path}",
            created=True,
            path=ai_config_path,
        )

    except (OSError, PermissionError) as exc:
        return AIConfigSetupResult(
            success=False,
            message=f"Could not setup ai_config.yaml: {exc}",
            created=False,
            path=ai_config_path,
        )
