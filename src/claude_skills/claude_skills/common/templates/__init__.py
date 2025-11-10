"""
Resource package marker for setup templates.

By providing this module, the `templates` directory is treated as a proper
Python package, allowing utilities like `importlib.resources` to locate files
bundled under `claude_skills.common.templates`.
"""

from __future__ import annotations

SETUP_TEMPLATE_PACKAGE = f"{__name__}.setup"

__all__ = ["SETUP_TEMPLATE_PACKAGE"]
