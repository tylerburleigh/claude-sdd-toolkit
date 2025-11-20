"""
Parser wrapper for LLM-based documentation generation.

This module provides a lightweight wrapper around existing code-doc parsers
with a "deep scan" mode for comprehensive file discovery and parsing.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass
import sys

# Import analysis parser infrastructure
try:
    from claude_skills.llm_doc_gen.analysis.parsers.factory import create_parser_factory
    from claude_skills.llm_doc_gen.analysis.parsers.base import Language, ParseResult
except ImportError:
    # Support running from source directory during development
    parent_path = Path(__file__).parent.parent.parent / "src" / "claude_skills"
    sys.path.insert(0, str(parent_path.parent))
    from claude_skills.llm_doc_gen.analysis.parsers.factory import create_parser_factory
    from claude_skills.llm_doc_gen.analysis.parsers.base import Language, ParseResult


@dataclass
class ScanConfig:
    """Configuration for deep scan mode."""
    project_root: Path
    exclude_patterns: Optional[List[str]] = None
    languages: Optional[List[Language]] = None
    max_files_per_language: Optional[int] = None
    verbose: bool = False


@dataclass
class ScanResult:
    """Result of a deep scan operation."""
    parse_result: ParseResult
    files_scanned: int
    files_skipped: int
    languages_detected: Set[Language]
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'parse_result': self.parse_result.to_dict(),
            'files_scanned': self.files_scanned,
            'files_skipped': self.files_skipped,
            'languages_detected': [lang.value for lang in self.languages_detected],
            'errors': self.errors
        }


class DeepScanParser:
    """
    Wrapper around code-doc parsers with deep scan capabilities.

    Provides:
    - Multi-language file discovery
    - Comprehensive parsing with progress tracking
    - Configurable exclusions and language filtering
    - Detailed scan statistics
    """

    def __init__(self, config: ScanConfig):
        """
        Initialize the deep scan parser.

        Args:
            config: Scan configuration
        """
        self.config = config
        self.project_root = config.project_root.resolve()

        # Default exclusions for documentation generation
        default_exclusions = [
            '__pycache__', '.git', 'node_modules', 'venv', '.venv',
            'build', 'dist', '.egg-info', 'test', 'tests',
            '.pytest_cache', 'coverage', '.coverage',
            'specs', '.claude', '.agents', 'AGENTS.md', 'CLAUDE.md'
        ]

        self.exclude_patterns = config.exclude_patterns or default_exclusions

        # Create parser factory with our configuration
        self.factory = create_parser_factory(
            project_root=self.project_root,
            exclude_patterns=self.exclude_patterns,
            languages=config.languages
        )

    def scan(self) -> ScanResult:
        """
        Perform a deep scan of the project.

        Returns:
            ScanResult with parsed entities and scan statistics
        """
        if self.config.verbose:
            print(f"🔍 Deep scanning {self.project_root}...")

        # Detect languages present in the project
        languages_detected = self.factory.detect_languages()

        if not languages_detected:
            return ScanResult(
                parse_result=ParseResult(),
                files_scanned=0,
                files_skipped=0,
                languages_detected=set(),
                errors=["No supported languages detected in project"]
            )

        if self.config.verbose:
            lang_names = ', '.join(sorted(l.value for l in languages_detected))
            print(f"   Detected: {lang_names}")

        # Parse all files using the factory
        parse_result = self.factory.parse_all(verbose=self.config.verbose)

        # Calculate statistics
        files_scanned = len(parse_result.modules)
        files_skipped = len([e for e in parse_result.errors if 'skipped' in e.lower()])

        result = ScanResult(
            parse_result=parse_result,
            files_scanned=files_scanned,
            files_skipped=files_skipped,
            languages_detected=languages_detected,
            errors=parse_result.errors
        )

        if self.config.verbose:
            self._print_scan_summary(result)

        return result

    def scan_file(self, file_path: Path) -> ParseResult:
        """
        Scan a single file.

        Args:
            file_path: Path to file to scan

        Returns:
            ParseResult for the file
        """
        return self.factory.parse_file(file_path, verbose=self.config.verbose)

    def get_language_statistics(self, result: ScanResult) -> Dict[str, Dict]:
        """
        Get per-language statistics from scan result.

        Args:
            result: Scan result to analyze

        Returns:
            Dictionary mapping language names to statistics
        """
        return self.factory.get_language_statistics(result.parse_result)

    def _print_scan_summary(self, result: ScanResult):
        """Print summary of scan results."""
        print(f"\n✅ Deep scan complete!")
        print(f"   📄 Files scanned: {result.files_scanned}")

        if result.files_skipped > 0:
            print(f"   ⏭️  Files skipped: {result.files_skipped}")

        # Show per-language breakdown
        lang_stats = self.get_language_statistics(result)
        for lang in sorted(result.languages_detected, key=lambda x: x.value):
            if lang.value in lang_stats:
                stats = lang_stats[lang.value]
                print(f"   {lang.value.upper()}: "
                      f"{stats['files']} files, "
                      f"{stats['classes']} classes, "
                      f"{stats['functions']} functions")

        # Show total counts
        pr = result.parse_result
        print(f"\n   📦 Total modules: {len(pr.modules)}")
        print(f"   🏛️  Total classes: {len(pr.classes)}")
        print(f"   ⚡ Total functions: {len(pr.functions)}")

        if result.errors:
            print(f"   ⚠️  Errors: {len(result.errors)}")


def create_deep_scanner(
    project_root: Path,
    exclude_patterns: Optional[List[str]] = None,
    languages: Optional[List[Language]] = None,
    verbose: bool = False
) -> DeepScanParser:
    """
    Create a deep scan parser instance.

    Args:
        project_root: Root directory to scan
        exclude_patterns: Patterns to exclude from scanning
        languages: Specific languages to scan (None = auto-detect all)
        verbose: Enable verbose output

    Returns:
        Configured DeepScanParser instance
    """
    config = ScanConfig(
        project_root=project_root,
        exclude_patterns=exclude_patterns,
        languages=languages,
        verbose=verbose
    )
    return DeepScanParser(config)


# Convenience function for quick scanning
def quick_scan(
    project_path: str,
    exclude: Optional[List[str]] = None,
    verbose: bool = True
) -> ScanResult:
    """
    Perform a quick deep scan of a project.

    Args:
        project_path: Path to project directory
        exclude: Additional patterns to exclude
        verbose: Enable verbose output

    Returns:
        ScanResult with parsed entities

    Example:
        >>> result = quick_scan("/path/to/project", verbose=True)
        >>> print(f"Scanned {result.files_scanned} files")
        >>> print(f"Found {len(result.parse_result.classes)} classes")
    """
    scanner = create_deep_scanner(
        project_root=Path(project_path),
        exclude_patterns=exclude,
        verbose=verbose
    )
    return scanner.scan()


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse

    parser = argparse.ArgumentParser(description="Deep scan a project for documentation")
    parser.add_argument("project_path", help="Path to project to scan")
    parser.add_argument("--exclude", action="append", help="Pattern to exclude")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")

    args = parser.parse_args()

    result = quick_scan(
        args.project_path,
        exclude=args.exclude,
        verbose=not args.quiet
    )

    print(f"\n📊 Scan Results:")
    print(f"   Files: {result.files_scanned}")
    print(f"   Classes: {len(result.parse_result.classes)}")
    print(f"   Functions: {len(result.parse_result.functions)}")

    if result.errors:
        print(f"\n⚠️  Encountered {len(result.errors)} errors")
        sys.exit(1)
