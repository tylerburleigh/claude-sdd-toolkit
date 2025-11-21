"""
Analysis insights data structures for LLM documentation generation.

This module defines data structures for storing extracted codebase analysis
insights that enhance AI-generated documentation. These insights are extracted
from documentation.json and formatted for inclusion in AI consultation prompts.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class AnalysisInsights:
    """
    Container for codebase analysis insights extracted from documentation.json.

    These insights provide high-level codebase metrics and patterns that help
    AI models generate more contextual and accurate documentation.

    Attributes:
        high_complexity_functions: List of function names with high complexity
        most_called_functions: List of dicts with function call statistics
            Format: [{"name": str, "file": str, "call_count": int}, ...]
        most_instantiated_classes: List of dicts with class instantiation statistics
            Format: [{"name": str, "file": str, "instantiation_count": int}, ...]
        entry_points: List of dicts identifying codebase entry points (NEW from consensus)
            Format: [{"name": str, "file": str, "type": str}, ...]
        integration_points: List of dicts with external integration information
            Format: [{"name": str, "type": str, "details": str}, ...]
        cross_module_dependencies: List of dicts mapping module dependencies (NEW from consensus)
            Format: [{"from_module": str, "to_module": str, "dependency_count": int}, ...]
        fan_out_analysis: List of dicts showing function fan-out metrics (NEW from consensus)
            Format: [{"name": str, "file": str, "calls_count": int, "unique_callees": int}, ...]
        language_breakdown: Dict mapping language to statistics
            Format: {"python": {"file_count": int, "line_count": int}, ...}
        module_statistics: Dict with module-level statistics
            Format: {"total_modules": int, "total_functions": int, "total_classes": int, ...}
    """

    high_complexity_functions: List[str] = field(default_factory=list)
    most_called_functions: List[Dict[str, Any]] = field(default_factory=list)
    most_instantiated_classes: List[Dict[str, Any]] = field(default_factory=list)
    entry_points: List[Dict[str, Any]] = field(default_factory=list)
    integration_points: List[Dict[str, Any]] = field(default_factory=list)
    cross_module_dependencies: List[Dict[str, Any]] = field(default_factory=list)
    fan_out_analysis: List[Dict[str, Any]] = field(default_factory=list)
    language_breakdown: Dict[str, Dict[str, int]] = field(default_factory=dict)
    module_statistics: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert insights to dictionary for JSON serialization.

        Returns:
            Dictionary representation of all analysis insights
        """
        return {
            'high_complexity_functions': self.high_complexity_functions,
            'most_called_functions': self.most_called_functions,
            'most_instantiated_classes': self.most_instantiated_classes,
            'entry_points': self.entry_points,
            'integration_points': self.integration_points,
            'cross_module_dependencies': self.cross_module_dependencies,
            'fan_out_analysis': self.fan_out_analysis,
            'language_breakdown': self.language_breakdown,
            'module_statistics': self.module_statistics
        }
