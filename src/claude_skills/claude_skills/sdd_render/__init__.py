"""sdd_render - Render JSON specs to human-readable markdown.

This module provides functionality to convert JSON specification files
into comprehensive, human-readable markdown documentation.

Components:
    SpecRenderer: Basic markdown rendering (current functionality)
    AIEnhancedRenderer: AI-enhanced rendering orchestrator (phases 2-4)
    SpecAnalyzer: Spec analysis engine for critical paths and bottlenecks
    PriorityRanker: Multi-factor priority scoring for intelligent task ordering
    ComplexityScorer: Task complexity scoring (1-10 scale) for adaptive formatting
    InsightGenerator: Actionable insights and recommendations from spec analysis
    DependencyGraphGenerator: Mermaid diagram generation for dependency visualization
"""

from .renderer import SpecRenderer
from .orchestrator import AIEnhancedRenderer
from .spec_analyzer import SpecAnalyzer
from .priority_ranker import PriorityRanker
from .complexity_scorer import ComplexityScorer, ComplexityScore
from .insight_generator import InsightGenerator
from .dependency_graph import DependencyGraphGenerator, GraphStyle
from .task_grouper import TaskGrouper
from .progressive_disclosure import DetailLevelCalculator, DetailContext, DetailLevel

__all__ = [
    'SpecRenderer',
    'AIEnhancedRenderer',
    'SpecAnalyzer',
    'PriorityRanker',
    'ComplexityScorer',
    'ComplexityScore',
    'InsightGenerator',
    'DependencyGraphGenerator',
    'GraphStyle',
    'TaskGrouper',
    'DetailLevelCalculator',
    'DetailContext',
    'DetailLevel'
]
