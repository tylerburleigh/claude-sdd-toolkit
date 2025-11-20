"""
Parser factory for multi-language codebase analysis.

This module provides a factory that automatically detects languages
and routes files to appropriate parsers.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Type, Any
from collections import defaultdict

from .base import BaseParser, Language, ParseResult
from ..optimization.parallel import ParallelParser


class ParserFactory:
    """
    Factory for creating and managing language-specific parsers.

    Automatically detects languages in a project and coordinates
    parsing across multiple languages.
    """

    def __init__(
        self,
        project_root: Path,
        exclude_patterns: Optional[List[str]] = None,
        languages: Optional[List[Language]] = None,
        filter_chain: Optional[Dict[str, Any]] = None,
        cache: Optional[Any] = None
    ):
        """
        Initialize the parser factory.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude from analysis
            languages: Specific languages to parse (None = auto-detect all)
            filter_chain: Optional dictionary of filter instances from create_filter_chain().
                Contains 'size_filter', 'count_limiter', and 'sampling' keys.
                If None, no additional filtering is applied (backward compatible).
            cache: Optional PersistentCache instance for caching parse results
        """
        self.project_root = project_root.resolve()
        self.exclude_patterns = exclude_patterns or [
            '__pycache__', '.git', 'node_modules', 'venv', '.venv',
            'build', 'dist', '.egg-info'
        ]
        self.requested_languages = languages
        self.filter_chain = filter_chain
        self.cache = cache
        self._parsers: Dict[Language, BaseParser] = {}
        self._parser_classes: Dict[Language, Type[BaseParser]] = {}

    def register_parser(self, language: Language, parser_class: Type[BaseParser]):
        """
        Register a parser class for a specific language.

        Args:
            language: Language enum value
            parser_class: Parser class (not instance)
        """
        self._parser_classes[language] = parser_class

    def detect_languages(self) -> Set[Language]:
        """
        Auto-detect languages present in the project.

        Returns:
            Set of detected Language enum values
        """
        detected = set()

        # Check for specific file extensions
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and not self._should_exclude(file_path):
                lang = Language.from_extension(file_path.suffix)
                if lang != Language.UNKNOWN:
                    detected.add(lang)

        return detected

    def get_parser(self, language: Language) -> Optional[BaseParser]:
        """
        Get or create a parser for the specified language.

        Args:
            language: Language to parse

        Returns:
            Parser instance or None if not available
        """
        # Return cached parser if exists
        if language in self._parsers:
            return self._parsers[language]

        # Create new parser if class is registered
        if language in self._parser_classes:
            parser_class = self._parser_classes[language]
            parser = parser_class(self.project_root, self.exclude_patterns, self.cache)
            self._parsers[language] = parser
            return parser

        return None

    def parse_all(
        self,
        verbose: bool = False,
        parallel: bool = False,
        num_workers: Optional[int] = None
    ) -> ParseResult:
        """
        Parse all files in the project across all detected languages.

        Args:
            verbose: Enable verbose output
            parallel: Enable parallel parsing using multiprocessing (default: False)
            num_workers: Number of worker processes (auto-detected if None, only used when parallel=True)

        Returns:
            Merged ParseResult containing all parsed entities

        Example:
            >>> # Sequential parsing (default)
            >>> result = factory.parse_all()
            >>>
            >>> # Parallel parsing with auto-detected workers
            >>> result = factory.parse_all(parallel=True)
            >>>
            >>> # Parallel parsing with explicit worker count
            >>> result = factory.parse_all(parallel=True, num_workers=4)
        """
        # Determine which languages to parse
        if self.requested_languages:
            languages_to_parse = set(self.requested_languages)
        else:
            languages_to_parse = self.detect_languages()

        if verbose:
            print(f"📁 Analyzing {self.project_root}...")
            detected_langs = ', '.join(sorted(l.value for l in languages_to_parse))
            print(f"🔍 Detected languages: {detected_langs}")
            if parallel:
                workers = num_workers if num_workers else ParallelParser.get_cpu_count() - 1
                print(f"⚡ Parallel mode enabled with {workers} workers")

        # Delegate to ParallelParser if parallel mode enabled
        if parallel:
            return self._parse_all_parallel(
                languages_to_parse,
                verbose=verbose,
                num_workers=num_workers
            )

        # Sequential parsing (original behavior)
        result = ParseResult()
        for language in sorted(languages_to_parse, key=lambda x: x.value):
            parser = self.get_parser(language)

            if parser is None:
                if verbose:
                    print(f"  ⚠️  {language.value.upper()}: No parser available (skipping)")
                result.errors.append(
                    f"No parser available for {language.value}"
                )
                continue

            # Parse all files for this language
            lang_result = parser.parse_all(verbose=verbose)
            result.merge(lang_result)

        if verbose:
            self._print_summary(result, languages_to_parse)

        return result

    def _parse_all_parallel(
        self,
        languages_to_parse: Set[Language],
        verbose: bool = False,
        num_workers: Optional[int] = None
    ) -> ParseResult:
        """
        Parse all files in parallel using ParallelParser.

        Args:
            languages_to_parse: Set of languages to parse
            verbose: Enable verbose output
            num_workers: Number of worker processes

        Returns:
            Merged ParseResult from all workers
        """
        # Collect all files from all languages with their parsers
        file_tasks: List[tuple[Path, Language]] = []
        language_file_counts: Dict[Language, int] = {}

        for language in sorted(languages_to_parse, key=lambda x: x.value):
            parser = self.get_parser(language)

            if parser is None:
                if verbose:
                    print(f"  ⚠️  {language.value.upper()}: No parser available (skipping)")
                continue

            files = parser.find_files()
            language_file_counts[language] = len(files)

            if verbose and files:
                print(f"  {language.value.upper()}: Found {len(files)} files")

            # Add tasks as (file_path, language) tuples
            for file_path in files:
                file_tasks.append((file_path, language))

        # If no files to parse, return empty result
        if not file_tasks:
            result = ParseResult()
            if verbose:
                self._print_summary(result, languages_to_parse)
            return result

        # Create parallel parser
        parallel_parser = ParallelParser(num_workers=num_workers)

        # Define worker function that parses a single file
        def parse_single_file(task: tuple[Path, Language]) -> ParseResult:
            file_path, language = task
            parser = self.get_parser(language)
            if parser is None:
                return ParseResult(
                    errors=[f"No parser available for {language.value}"]
                )
            return parser.parse_file(file_path)

        # Progress callback for verbose mode
        progress_callback = None
        if verbose:
            total_files = len(file_tasks)
            def progress_callback(completed: int, total: int):
                print(f"    [{completed}/{total}] files parsed...", end='\r')

        # Parse all files in parallel
        results = parallel_parser.parse_files(
            file_tasks,
            parse_single_file,
            progress_callback=progress_callback
        )

        # Clear progress line
        if verbose:
            print(" " * 60, end='\r')

        # Merge all results
        merged_result = ParseResult()
        for result in results:
            merged_result.merge(result)

        if verbose:
            self._print_summary(merged_result, languages_to_parse)

        return merged_result

    def parse_file(self, file_path: Path, verbose: bool = False) -> ParseResult:
        """
        Parse a single file using the appropriate language parser.

        Args:
            file_path: Path to file to parse
            verbose: Enable verbose output

        Returns:
            ParseResult for the file
        """
        language = Language.from_extension(file_path.suffix)

        if language == Language.UNKNOWN:
            result = ParseResult()
            result.errors.append(f"Unknown language for file: {file_path}")
            return result

        parser = self.get_parser(language)
        if parser is None:
            result = ParseResult()
            result.errors.append(f"No parser for {language.value}: {file_path}")
            return result

        return parser.parse_file(file_path)

    def get_language_statistics(self, result: ParseResult) -> Dict[str, Dict]:
        """
        Calculate per-language statistics.

        Args:
            result: ParseResult to analyze

        Returns:
            Dictionary mapping language to statistics
        """
        stats = defaultdict(lambda: {
            'files': 0,
            'lines': 0,
            'classes': 0,
            'functions': 0,
        })

        for module in result.modules:
            lang = module.language.value
            stats[lang]['files'] += 1
            stats[lang]['lines'] += module.lines
            stats[lang]['classes'] += len(module.classes)
            stats[lang]['functions'] += len(module.functions)

        return dict(stats)

    def _should_exclude(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded based on patterns and filters.

        Uses path component matching to avoid false positives.
        For example, '.git' will match '.git/' but not '.github/'.

        Also applies filter_chain if configured (size limits, etc.).
        """
        path_parts = file_path.parts
        path_str = str(file_path)

        # First check pattern-based exclusions
        for pattern in self.exclude_patterns:
            # Check if pattern matches any path component exactly
            if pattern in path_parts:
                return True

            # Handle wildcards (e.g., '*.egg-info')
            if '*' in pattern:
                # Simple wildcard matching for file/directory names
                import fnmatch
                for part in path_parts:
                    if fnmatch.fnmatch(part, pattern):
                        return True

            # Special case for multi-part patterns like '.env.local'
            # Only match if pattern has multiple dots or is clearly a file pattern
            if pattern.count('.') > 1:
                # For patterns like '.env.local', match as substring
                if pattern in path_str:
                    return True

        # Apply filter_chain if configured
        if self.filter_chain is not None:
            # Check size filter
            size_filter = self.filter_chain.get('size_filter')
            if size_filter is not None:
                try:
                    if not size_filter.should_include(file_path):
                        return True  # Exclude files that are too large
                except (FileNotFoundError, OSError):
                    # If we can't access the file, exclude it
                    return True

        return False

    def _print_summary(self, result: ParseResult, languages: Set[Language]):
        """Print summary of parsing results."""
        print(f"\n✅ Analysis complete!")

        # Per-language stats
        lang_stats = self.get_language_statistics(result)
        for lang in sorted(languages, key=lambda x: x.value):
            lang_key = lang.value
            if lang_key in lang_stats:
                stats = lang_stats[lang_key]
                print(f"   {lang_key.upper()}: "
                      f"{stats['files']} files, "
                      f"{stats['classes']} classes, "
                      f"{stats['functions']} functions")

        # Total stats
        print(f"\n   📦 Total: {len(result.modules)} modules")
        print(f"   🏛️  Total: {len(result.classes)} classes")
        print(f"   ⚡ Total: {len(result.functions)} functions")

        if result.errors:
            print(f"   ⚠️  {len(result.errors)} errors encountered")


# Auto-register parsers when they're imported
def _auto_register_parsers(factory: ParserFactory):
    """
    Auto-register all available parsers.

    This function attempts to import and register all known parsers.
    If a parser's dependencies aren't available, it's skipped silently.
    """
    try:
        from .python import PythonParser
        factory.register_parser(Language.PYTHON, PythonParser)
    except ImportError:
        pass

    try:
        from .javascript import JavaScriptParser
        factory.register_parser(Language.JAVASCRIPT, JavaScriptParser)
        factory.register_parser(Language.TYPESCRIPT, JavaScriptParser)
    except ImportError:
        pass

    try:
        from .go import GoParser
        factory.register_parser(Language.GO, GoParser)
    except ImportError:
        pass

    try:
        from .html import HTMLParser
        factory.register_parser(Language.HTML, HTMLParser)
    except ImportError:
        pass

    try:
        from .css import CSSParser
        factory.register_parser(Language.CSS, CSSParser)
    except ImportError:
        pass


def create_parser_factory(
    project_root: Path,
    exclude_patterns: Optional[List[str]] = None,
    languages: Optional[List[Language]] = None,
    filter_chain: Optional[Dict[str, Any]] = None,
    cache: Optional[Any] = None
) -> ParserFactory:
    """
    Create a ParserFactory with all available parsers registered.

    Args:
        project_root: Root directory of project
        exclude_patterns: Patterns to exclude
        languages: Specific languages to parse
        filter_chain: Optional dictionary of filter instances from create_filter_chain()
        cache: Optional PersistentCache instance for caching parse results

    Returns:
        Configured ParserFactory instance
    """
    factory = ParserFactory(project_root, exclude_patterns, languages, filter_chain, cache)
    _auto_register_parsers(factory)
    return factory
