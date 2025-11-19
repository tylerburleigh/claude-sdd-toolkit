"""
Documentation generators for LLM-based documentation.

This package contains specialized generators for different documentation types:
- overview_generator: Project overview and executive summary
- architecture_generator: Architecture and design documentation
- component_generator: Component and module documentation
"""

from .overview_generator import OverviewGenerator

__all__ = ["OverviewGenerator"]
