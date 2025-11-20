"""
Codebase Documentation Generator
Modular documentation generation package.
"""

from .parser import CodebaseAnalyzer
from .calculator import calculate_complexity, calculate_statistics
from .formatter import MarkdownGenerator, JSONGenerator
from .generator import DocumentationGenerator

__all__ = [
    'CodebaseAnalyzer',
    'calculate_complexity',
    'calculate_statistics',
    'MarkdownGenerator',
    'JSONGenerator',
    'DocumentationGenerator',
]
