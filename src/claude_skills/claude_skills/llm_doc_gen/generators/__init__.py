"""
Documentation generators for LLM-based documentation.

This package contains specialized generators for different documentation types:
- overview_generator: Project overview and executive summary
- architecture_generator: Architecture and design documentation
- component_generator: Component and module documentation
"""

from .overview_generator import OverviewGenerator, ProjectData
from .architecture_generator import ArchitectureGenerator, ArchitectureData
from .component_generator import ComponentGenerator, ComponentData

__all__ = [
    # Generators
    "OverviewGenerator",
    "ArchitectureGenerator",
    "ComponentGenerator",
    # Data classes
    "ProjectData",
    "ArchitectureData",
    "ComponentData",
]
