"""
Documentation generation orchestration module.
Coordinates parsing, analysis, and formatting to generate documentation.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Handle both direct execution and module import
try:
    from .parsers import create_parser_factory, Language, ParseResult
    from .calculator import calculate_statistics
    from .formatter import MarkdownGenerator, JSONGenerator
except ImportError:
    from parsers import create_parser_factory, Language, ParseResult
    from calculator import calculate_statistics
    from formatter import MarkdownGenerator, JSONGenerator


class DocumentationGenerator:
    """
    Main orchestrator for documentation generation.
    Coordinates all stages: parsing, analysis, calculation, and formatting.
    Supports multiple programming languages.
    """

    def __init__(
        self,
        project_dir: Path,
        project_name: str,
        version: str = "1.0.0",
        exclude_patterns: Optional[list] = None,
        languages: Optional[List[Language]] = None
    ):
        """
        Initialize the documentation generator.

        Args:
            project_dir: Root directory of the project to document
            project_name: Name of the project
            version: Project version
            exclude_patterns: List of patterns to exclude from analysis
            languages: Specific languages to parse (None = auto-detect all)
        """
        self.project_dir = project_dir
        self.project_name = project_name
        self.version = version
        self.exclude_patterns = exclude_patterns or []
        self.languages = languages

        # Initialize components
        self.parser_factory = create_parser_factory(
            project_dir,
            self.exclude_patterns,
            languages
        )
        self.md_generator = MarkdownGenerator(project_name, version)
        self.json_generator = JSONGenerator(project_name, version)

    def generate(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Generate complete documentation analysis.

        Args:
            verbose: Enable verbose output

        Returns:
            Dictionary containing analysis results and statistics
        """
        # Parse codebase using ParserFactory
        parse_result = self.parser_factory.parse_all(verbose=verbose)

        # Convert ParseResult to dictionary format for backward compatibility
        analysis = self._convert_parse_result(parse_result)

        # Calculate statistics
        statistics = calculate_statistics(
            analysis['modules'],
            analysis['functions']
        )

        return {
            'analysis': analysis,
            'statistics': statistics
        }

    def _convert_parse_result(self, result: ParseResult) -> Dict[str, Any]:
        """
        Convert ParseResult to dictionary format for backward compatibility.

        Args:
            result: ParseResult from parser factory

        Returns:
            Dictionary with modules, classes, functions, dependencies
        """
        return {
            'modules': [m.to_dict() for m in result.modules],
            'classes': [c.to_dict() for c in result.classes],
            'functions': [f.to_dict() for f in result.functions],
            'dependencies': result.dependencies,
            'errors': result.errors
        }

    def save_markdown(
        self,
        output_path: Path,
        analysis: Dict[str, Any],
        statistics: Dict[str, Any],
        verbose: bool = False
    ):
        """
        Generate and save Markdown documentation.

        Args:
            output_path: Path to save the Markdown file
            analysis: Analyzed codebase data
            statistics: Calculated statistics
            verbose: Enable verbose output
        """
        if verbose:
            print("📝 Generating Markdown documentation...")

        markdown = self.md_generator.generate(analysis, statistics)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        if verbose:
            print(f"✅ Markdown: {output_path}")

    def save_json(
        self,
        output_path: Path,
        analysis: Dict[str, Any],
        statistics: Dict[str, Any],
        verbose: bool = False
    ):
        """
        Generate and save JSON documentation.

        Args:
            output_path: Path to save the JSON file
            analysis: Analyzed codebase data
            statistics: Calculated statistics
            verbose: Enable verbose output
        """
        if verbose:
            print("📋 Generating JSON documentation...")

        json_doc = self.json_generator.generate(analysis, statistics)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_doc, f, indent=2)

        if verbose:
            print(f"✅ JSON: {output_path}")

    def generate_all(
        self,
        output_dir: Path,
        format_type: str = 'both',
        verbose: bool = False
    ) -> None:
        """
        Generate documentation in specified format(s).

        Args:
            output_dir: Directory to save documentation files
            format_type: Output format ('markdown', 'json', or 'both')
            verbose: Enable verbose output
        """
        # Generate analysis
        result = self.generate(verbose=verbose)
        analysis = result['analysis']
        statistics = result['statistics']

        # Save in requested format(s)
        if format_type in ['markdown', 'both']:
            md_path = output_dir / 'DOCUMENTATION.md'
            self.save_markdown(md_path, analysis, statistics, verbose=verbose)

        if format_type in ['json', 'both']:
            json_path = output_dir / 'documentation.json'
            self.save_json(json_path, analysis, statistics, verbose=verbose)

        if verbose:
            print(f"\n🎉 Documentation generation complete!")
            print(f"   Output directory: {output_dir.absolute()}")
