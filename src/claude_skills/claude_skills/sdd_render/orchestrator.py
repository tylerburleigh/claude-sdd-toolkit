"""AI-Enhanced Spec Rendering Orchestrator

This module provides the orchestration layer for AI-enhanced spec rendering.
Currently delegates to basic SpecRenderer; future phases will add:

Phase 2 (AI Analysis Engine):
- Priority ranking and complexity scoring (task-2-2, task-2-3)
- Insight generation (task-2-4)
- Dependency graph visualization (task-2-5)
- Intelligent task grouping (task-2-6)

Phase 3 (AI Enhancement Layer):
- Executive summaries (task-3-1)
- Progressive disclosure (task-3-2)
- Enhanced visualizations (task-3-3)
- Narrative enhancement (task-3-4)
- AI prompt templates (task-3-5)

Phase 4 (Enhanced Output):
- Multiple output formats: HTML, PDF (planned)
- Template system for custom styling (planned)
- Smart filtering and focused views (planned)

Current Status:
    The orchestrator currently wraps SpecRenderer and produces identical output.
    AI enhancement features are placeholder methods with TODO markers for future
    implementation.

Usage:
    >>> from claude_skills.sdd_render import AIEnhancedRenderer
    >>> import json
    >>>
    >>> # Load spec data
    >>> with open('specs/active/my-spec.json') as f:
    >>>     spec_data = json.load(f)
    >>>
    >>> # Create orchestrator
    >>> renderer = AIEnhancedRenderer(spec_data)
    >>>
    >>> # Render (currently same as basic rendering)
    >>> markdown = renderer.render()
    >>>
    >>> # Future: Enable AI enhancements (not yet implemented)
    >>> # markdown = renderer.render(enable_ai=True)
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging
from .renderer import SpecRenderer
from .spec_analyzer import SpecAnalyzer
from .priority_ranker import PriorityRanker
from .complexity_scorer import ComplexityScorer
from .insight_generator import InsightGenerator
from .dependency_graph import DependencyGraphGenerator, GraphStyle
from .task_grouper import TaskGrouper
from .markdown_parser import MarkdownParser
from .markdown_enhancer import MarkdownEnhancer, EnhancementOptions

# Initialize logger
logger = logging.getLogger(__name__)


def validate_spec_path(spec_path: Path) -> bool:
    """Validate that spec file exists and is readable.

    Args:
        spec_path: Path to spec JSON file

    Returns:
        True if valid

    Raises:
        FileNotFoundError: If spec file doesn't exist
        ValueError: If spec_path is not a file
    """
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
    if not spec_path.is_file():
        raise ValueError(f"Spec path is not a file: {spec_path}")
    return True


class AIEnhancedRenderer:
    """Orchestrates AI-enhanced spec rendering pipeline.

    This class provides the framework for multi-stage spec rendering with
    AI enhancements. Currently it delegates to SpecRenderer for basic markdown
    generation. Future phases will add AI analysis and enhancement features.

    Architecture:
        The rendering pipeline has four stages:

        1. Base Rendering (Current)
           - Generates markdown using SpecRenderer
           - Progress indicators, task hierarchy, dependencies

        2. AI Analysis (Phase 2 - Planned)
           - Priority ranking based on dependencies and impact
           - Complexity scoring for accurate estimates
           - Automated insight generation
           - Dependency graph visualization
           - Intelligent task grouping by functional areas

        3. AI Enhancement (Phase 3 - Planned)
           - Executive summaries for quick overviews
           - Progressive disclosure UI for better navigation
           - Rich visualizations (Gantt charts, burndown, etc.)
           - Narrative enhancement for better flow
           - AI prompt templates for spec analysis

        4. Output Formatting (Phase 4 - Planned)
           - Multiple formats: Markdown, HTML, PDF, JSON
           - Template system for custom branding
           - Smart filtering by status, phase, priority

    Attributes:
        spec_data: Complete JSON spec dictionary
        base_renderer: SpecRenderer instance for basic markdown generation

    Example:
        >>> renderer = AIEnhancedRenderer(spec_data)
        >>> markdown = renderer.render()
        >>>
        >>> # Future: with AI enhancements
        >>> # markdown = renderer.render(enable_ai=True, output_format='html')
    """

    def __init__(self, spec_data: Dict[str, Any], *, model_override: Any = None):
        """Initialize orchestrator with spec data.

        Args:
            spec_data: Complete JSON spec dictionary containing hierarchy,
                      metadata, and task information
        """
        self.spec_data = spec_data
        self.base_renderer = SpecRenderer(spec_data)
        self.model_override = model_override

    def _generate_base_markdown(self) -> str:
        """Generate base markdown using SpecRenderer.

        This method delegates to the existing SpecRenderer to create
        well-formatted markdown with:
        - Spec header with progress
        - Phase breakdown
        - Task details with status icons
        - Dependencies and blockers
        - Verification steps

        Returns:
            Base markdown without AI enhancements
        """
        return self.base_renderer.to_markdown()

    def _analyze_with_ai(self) -> Optional[Dict[str, Any]]:
        """Run AI analysis on spec to extract insights and recommendations.

        Integrates the AI Analysis Engine modules to provide:
        - Critical path and bottleneck detection
        - Priority ranking based on multiple factors
        - Complexity scoring for each task
        - Actionable insights and recommendations
        - Dependency graph visualizations
        - Alternative task groupings

        Returns:
            Dictionary containing comprehensive analysis results, or None if analysis fails.

        Return Format:
            {
                'critical_path': List[str],  # Task IDs on critical path
                'bottlenecks': List[Tuple[str, int]],  # (task_id, dependent_count)
                'parallel_waves': List[List[str]],  # Groups of parallelizable tasks
                'stats': Dict,  # Overall spec statistics
                'ranked_tasks': List[Tuple[str, TaskPriority]],  # Prioritized tasks
                'top_priorities': List,  # Top 5 priority tasks
                'complexity_scores': List,  # All tasks with complexity scores
                'high_complexity': List,  # Tasks with complexity >= 7.0
                'complexity_stats': Dict,  # Complexity distribution stats
                'insights': List[Insight],  # All generated insights
                'critical_insights': List[Insight],  # Critical severity insights only
                'dependency_graph': str,  # Mermaid diagram
                'critical_path_graph': str,  # Critical path visualization
                'file_groups': Dict,  # Tasks grouped by file
                'category_groups': Dict,  # Tasks grouped by category
                'risk_groups': Dict  # Tasks grouped by risk level
            }
        """
        logger.info("Starting AI analysis pipeline...")
        results = {}

        try:
            # Initialize core analyzer
            logger.debug("Initializing SpecAnalyzer...")
            analyzer = SpecAnalyzer(self.spec_data)

            # Critical path and bottleneck analysis
            try:
                results['critical_path'] = analyzer.get_critical_path()
                logger.debug(f"Found critical path with {len(results['critical_path'])} tasks")
            except Exception as e:
                logger.warning(f"Critical path analysis failed: {e}")
                results['critical_path'] = []

            try:
                results['bottlenecks'] = analyzer.get_bottlenecks(min_dependents=3)
                logger.debug(f"Identified {len(results['bottlenecks'])} bottleneck tasks")
            except Exception as e:
                logger.warning(f"Bottleneck detection failed: {e}")
                results['bottlenecks'] = []

            try:
                results['parallel_waves'] = analyzer.get_parallelizable_tasks()
                logger.debug(f"Found {len(results['parallel_waves'])} waves of parallel tasks")
            except Exception as e:
                logger.warning(f"Parallel task analysis failed: {e}")
                results['parallel_waves'] = []

            try:
                results['stats'] = analyzer.get_stats()
            except Exception as e:
                logger.warning(f"Stats calculation failed: {e}")
                results['stats'] = {}

            # Priority ranking
            try:
                logger.debug("Initializing PriorityRanker...")
                ranker = PriorityRanker(self.spec_data, analyzer)
                results['ranked_tasks'] = ranker.rank_tasks(pending_only=True)
                results['top_priorities'] = ranker.get_top_priorities(5)
                logger.debug(f"Ranked {len(results['ranked_tasks'])} tasks by priority")
            except Exception as e:
                logger.warning(f"Priority ranking failed: {e}")
                results['ranked_tasks'] = []
                results['top_priorities'] = []

            # Complexity scoring
            try:
                logger.debug("Initializing ComplexityScorer...")
                scorer = ComplexityScorer(self.spec_data, analyzer)
                results['complexity_scores'] = scorer.score_all_tasks()
                results['high_complexity'] = scorer.get_high_complexity_tasks(threshold=7.0)
                results['complexity_stats'] = scorer.get_complexity_stats()
                logger.debug(f"Scored {len(results['complexity_scores'])} tasks for complexity")
            except Exception as e:
                logger.warning(f"Complexity scoring failed: {e}")
                results['complexity_scores'] = []
                results['high_complexity'] = []
                results['complexity_stats'] = {}

            # Insight generation
            try:
                logger.debug("Initializing InsightGenerator...")
                generator = InsightGenerator(self.spec_data, analyzer, ranker, scorer)
                results['insights'] = generator.generate_all_insights()
                results['critical_insights'] = generator.get_critical_insights()
                logger.debug(f"Generated {len(results['insights'])} insights ({len(results['critical_insights'])} critical)")
            except Exception as e:
                logger.warning(f"Insight generation failed: {e}")
                results['insights'] = []
                results['critical_insights'] = []

            # Dependency graph generation
            try:
                logger.debug("Initializing DependencyGraphGenerator...")
                graph_gen = DependencyGraphGenerator(self.spec_data, analyzer)
                results['dependency_graph'] = graph_gen.generate_graph(
                    style=GraphStyle.FLOWCHART,
                    highlight_critical_path=True,
                    show_status=True
                )
                results['critical_path_graph'] = graph_gen.generate_critical_path_graph()
                logger.debug("Generated dependency visualizations")
            except Exception as e:
                logger.warning(f"Dependency graph generation failed: {e}")
                results['dependency_graph'] = ""
                results['critical_path_graph'] = ""

            # Task grouping
            try:
                logger.debug("Initializing TaskGrouper...")
                grouper = TaskGrouper(self.spec_data, analyzer)
                results['file_groups'] = grouper.group_by_file()
                results['category_groups'] = grouper.group_by_category()
                results['risk_groups'] = grouper.group_by_risk()
                logger.debug("Generated alternative task groupings")
            except Exception as e:
                logger.warning(f"Task grouping failed: {e}")
                results['file_groups'] = {}
                results['category_groups'] = {}
                results['risk_groups'] = {}

            logger.info("AI analysis pipeline completed successfully")
            return results

        except Exception as e:
            logger.error(f"AI analysis pipeline failed: {e}")
            return None

    def _enhance_with_ai(
        self,
        base_markdown: str,
        analysis: Optional[Dict],
        enhancement_level: str = 'full'
    ) -> str:
        """Enhance markdown with AI-generated insights and visualizations.

        Parses base markdown and injects AI enhancements based on the analysis results:
        - Executive summaries with key metrics
        - Critical insights and recommendations
        - Dependency visualizations (Mermaid diagrams)
        - Narrative transitions between phases
        - Progressive disclosure for better navigation
        - Priority and complexity annotations

        Args:
            base_markdown: Base markdown from SpecRenderer
            analysis: AI analysis results dictionary (or None to fall back)
            enhancement_level: Level of enhancement ('summary', 'standard', 'full')
                - summary: Executive summary and critical insights only
                - standard: Adds visualizations and narratives (no progressive disclosure)
                - full: All enhancements including collapsible sections

        Returns:
            Enhanced markdown with AI-generated content, or base_markdown if enhancement fails

        Enhancement Process:
            1. Parse base markdown into structured sections
            2. Configure enhancement options based on level
            3. Inject AI content (summaries, insights, graphs)
            4. Add narrative transitions
            5. Apply progressive disclosure (full mode only)
            6. Return enhanced markdown
        """
        # Fallback if no analysis results
        if not analysis:
            logger.warning("No AI analysis results available, returning base markdown")
            return base_markdown

        try:
            logger.info(f"Starting AI enhancement pipeline (level: {enhancement_level})...")

            # Parse base markdown
            logger.debug("Parsing base markdown structure...")
            parser = MarkdownParser(base_markdown)
            parsed_spec = parser.parse()
            logger.debug(f"Parsed {len(parsed_spec.phases)} phases from markdown")

            # Configure enhancement options based on level
            if enhancement_level == 'summary':
                options = EnhancementOptions(
                    include_executive_summary=True,
                    include_visualizations=False,
                    include_narrative_transitions=False,
                    include_insights=True,  # Critical only
                    include_progressive_disclosure=False,
                    max_insights=3
                )
                logger.debug("Using 'summary' enhancement level (exec summary + critical insights)")
            elif enhancement_level == 'standard':
                options = EnhancementOptions(
                    include_executive_summary=True,
                    include_visualizations=True,
                    include_narrative_transitions=True,
                    include_insights=True,
                    include_progressive_disclosure=False,
                    max_insights=5
                )
                logger.debug("Using 'standard' enhancement level (no progressive disclosure)")
            else:  # full
                options = EnhancementOptions(
                    include_executive_summary=True,
                    include_visualizations=True,
                    include_narrative_transitions=True,
                    include_insights=True,
                    include_progressive_disclosure=True,
                    max_insights=10
                )
                logger.debug("Using 'full' enhancement level (all features)")

            # Enhance markdown
            logger.debug("Applying AI enhancements...")
            enhancer = MarkdownEnhancer(
                spec_data=self.spec_data,
                parsed_spec=parsed_spec,
                options=options,
                model_override=self.model_override,
            )
            enhanced_markdown = enhancer.enhance()
            logger.info("AI enhancement pipeline completed successfully")

            return enhanced_markdown

        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            logger.warning("Falling back to base markdown")
            return base_markdown

    def _format_output(self, enhanced_markdown: str, format: str = 'markdown') -> str:
        """Format output to desired format (Phase 4 - Not yet implemented).

        This placeholder method will handle multiple output formats when
        implemented in Phase 4.

        Planned Output Formats:
            Markdown (Current):
                - Standard GitHub-flavored markdown
                - Compatible with all markdown processors
                - Default format

            HTML (Planned):
                - Styled HTML with CSS
                - Interactive elements (collapsible sections)
                - Embedded visualizations (SVG, charts)
                - Responsive design

            PDF (Planned):
                - Professional PDF output
                - Custom branding and styling
                - Table of contents and bookmarks
                - Print-optimized layout

            JSON (Planned):
                - Machine-readable export
                - Programmatic access to enhanced data
                - Include all analysis results
                - API-friendly format

        Template System (Planned):
            - Customizable output templates
            - Corporate branding options
            - Team-specific layouts
            - Client vs internal views
            - Themed styling

        Smart Filtering (Planned):
            - Filter by status (pending, in_progress, completed)
            - Filter by phase or task type
            - Filter by file path or developer
            - Filter by priority or complexity

        Args:
            enhanced_markdown: Markdown with AI enhancements
            format: Output format ('markdown', 'html', 'pdf', 'json')

        Returns:
            Formatted output (currently only markdown is supported)

        Raises:
            NotImplementedError: If format other than 'markdown' is requested
        """
        # TODO: Implement in Phase 4
        # - Add HTML output with styling
        # - Add PDF generation
        # - Add JSON export
        # - Implement template system
        # - Add smart filtering

        if format != 'markdown':
            raise NotImplementedError(
                f"Output format '{format}' is not yet supported. "
                f"Only 'markdown' is currently available. "
                f"HTML, PDF, and JSON formats will be added in Phase 4."
            )

        return enhanced_markdown

    def render(
        self,
        output_format: str = 'markdown',
        enable_ai: bool = False,
        enhancement_level: str = 'full'
    ) -> str:
        """Orchestrate complete rendering pipeline.

        Main entry point for spec rendering. Orchestrates all stages from base
        markdown generation through AI analysis and enhancement to final output.

        Pipeline Stages:
            1. Base Rendering (✅ Implemented)
               Generate well-formatted markdown with progress tracking

            2. AI Analysis (✅ Implemented)
               Analyze spec for priority, complexity, insights, dependencies

            3. AI Enhancement (✅ Implemented)
               Add summaries, visualizations, progressive disclosure

            4. Output Formatting (⏳ Partial - markdown only)
               Convert to requested format (HTML, PDF, JSON planned for Phase 4)

        Args:
            output_format: Desired output format ('markdown', 'html', 'pdf', 'json')
                          Default: 'markdown' (only markdown currently supported)
            enable_ai: Enable AI enhancements (analysis + enhancement features)
                      Default: False
            enhancement_level: Level of AI enhancement when enable_ai=True
                              - 'summary': Executive summary and critical insights only
                              - 'standard': Adds visualizations and narratives
                              - 'full': All enhancements including progressive disclosure
                              Default: 'full'

        Returns:
            Rendered output in requested format

        Raises:
            NotImplementedError: If output_format is not 'markdown'

        Examples:
            >>> renderer = AIEnhancedRenderer(spec_data)
            >>>
            >>> # Basic rendering (no AI features)
            >>> markdown = renderer.render()
            >>>
            >>> # Full AI enhancements
            >>> markdown = renderer.render(enable_ai=True, enhancement_level='full')
            >>>
            >>> # Summary level (quick status check)
            >>> markdown = renderer.render(enable_ai=True, enhancement_level='summary')
        """
        # Stage 1: Base rendering
        logger.debug("Stage 1: Generating base markdown...")
        base_markdown = self._generate_base_markdown()

        # Stage 2: AI analysis
        analysis = None
        if enable_ai:
            logger.debug("Stage 2: Running AI analysis...")
            analysis = self._analyze_with_ai()
        else:
            logger.debug("Stage 2: Skipping AI analysis (enable_ai=False)")

        # Stage 3: AI enhancement
        if enable_ai and analysis:
            logger.debug(f"Stage 3: Applying AI enhancements (level={enhancement_level})...")
            enhanced = self._enhance_with_ai(base_markdown, analysis, enhancement_level)
        else:
            logger.debug("Stage 3: Skipping AI enhancement")
            enhanced = base_markdown

        # Stage 4: Output formatting
        logger.debug(f"Stage 4: Formatting output (format={output_format})...")
        output = self._format_output(enhanced, output_format)

        return output

    def get_pipeline_status(self) -> Dict[str, bool]:
        """Get status of pipeline stages (useful for debugging/testing).

        Returns dictionary indicating which pipeline stages are implemented.

        Returns:
            Dictionary with stage names and implementation status

        Example:
            >>> renderer = AIEnhancedRenderer(spec_data)
            >>> status = renderer.get_pipeline_status()
            >>> print(status)
            {
                'base_rendering': True,
                'ai_analysis': True,
                'ai_enhancement': True,
                'multi_format_output': False
            }
        """
        return {
            'base_rendering': True,           # ✅ Implemented (SpecRenderer)
            'ai_analysis': True,              # ✅ Implemented (Phase 2)
            'ai_enhancement': True,           # ✅ Implemented (Phase 3)
            'multi_format_output': False       # ⏳ Phase 4 (markdown only, HTML/PDF/JSON planned)
        }
