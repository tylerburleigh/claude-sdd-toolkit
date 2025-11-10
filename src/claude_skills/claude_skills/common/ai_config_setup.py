"""
Utilities for bootstrapping `.claude/ai_config.yaml` during project setup.

This helper centralises the logic for copying the packaged AI configuration
template (or falling back to a minimal default) into a target project. Both
the legacy `dev_tools.setup_project_permissions` script and the unified CLI
delegate to this module so we guarantee `ai_config.yaml` is always created.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import shutil


__all__ = ["AIConfigSetupResult", "ensure_ai_config"]


_MINIMAL_TEMPLATE = """# Centralized AI Model Consultation Configuration
#
# This file defines default AI tool settings for the SDD Toolkit. You can
# customise tools, model priorities, consensus rules, and per-skill overrides.
# Generated automatically during `sdd-setup`.

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
      - gemini-2.5-pro
  cursor-agent:
    priority:
      - composer-1
  codex:
    priority:
      - gpt-5-codex

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


def _find_packaged_template() -> Optional[Path]:
    """
    Locate the packaged ai_config template, if available.

    Returns:
        Path to the template or None when not present in the install.
    """
    # 1. Development/editable installs keep templates under src/claude_skills/.claude/
    package_root = Path(__file__).resolve().parents[2]
    candidate = package_root / ".claude" / "ai_config.yaml"
    if candidate.exists():
        return candidate

    # 2. Installed wheel distributions place the package under site-packages/claude_skills/
    try:
        import claude_skills  # type: ignore

        installed_root = Path(claude_skills.__file__).resolve().parent
        candidate = installed_root.parent / ".claude" / "ai_config.yaml"
        if candidate.exists():
            return candidate
    except (ImportError, AttributeError):
        pass

    return None


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

        template_path = _find_packaged_template()
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
