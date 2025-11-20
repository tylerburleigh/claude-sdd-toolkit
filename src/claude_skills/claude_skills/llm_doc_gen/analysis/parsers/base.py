"""
Abstract base parser interface for multi-language codebase documentation.

This module defines the common interface and data structures that all
language-specific parsers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    HTML = "html"
    CSS = "css"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, extension: str) -> 'Language':
        """
        Detect language from file extension.

        Args:
            extension: File extension (with or without leading dot)

        Returns:
            Language enum value
        """
        ext = extension.lstrip('.').lower()
        mapping = {
            'py': cls.PYTHON,
            'js': cls.JAVASCRIPT,
            'jsx': cls.JAVASCRIPT,
            'ts': cls.TYPESCRIPT,
            'tsx': cls.TYPESCRIPT,
            'go': cls.GO,
            'html': cls.HTML,
            'htm': cls.HTML,
            'css': cls.CSS,
        }
        return mapping.get(ext, cls.UNKNOWN)


@dataclass
class ParsedParameter:
    """Represents a function/method parameter."""
    name: str
    type: Optional[str] = None
    default: Optional[str] = None


@dataclass
class ParsedFunction:
    """Represents a function or method in any language."""
    name: str
    file: str
    line: int
    language: Language
    docstring: Optional[str] = None
    parameters: List[ParsedParameter] = field(default_factory=list)
    return_type: Optional[str] = None
    complexity: int = 1
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_exported: bool = False
    is_public: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'file': self.file,
            'line': self.line,
            'language': self.language.value,
            'docstring': self.docstring,
            'parameters': [
                {
                    'name': p.name,
                    'type': p.type,
                    'default': p.default
                } for p in self.parameters
            ],
            'return_type': self.return_type,
            'complexity': self.complexity,
            'decorators': self.decorators,
            'is_async': self.is_async,
            'is_exported': self.is_exported,
            'is_public': self.is_public,
            **self.metadata
        }


@dataclass
class ParsedClass:
    """Represents a class, struct, or interface in any language."""
    name: str
    file: str
    line: int
    language: Language
    docstring: Optional[str] = None
    bases: List[str] = field(default_factory=list)  # Parent classes/interfaces
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_public: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'file': self.file,
            'line': self.line,
            'language': self.language.value,
            'docstring': self.docstring,
            'bases': self.bases,
            'methods': self.methods,
            'properties': self.properties,
            'is_exported': self.is_exported,
            'is_public': self.is_public,
            **self.metadata
        }


@dataclass
class ParsedModule:
    """Represents a module, file, or compilation unit."""
    name: str
    file: str
    language: Language
    docstring: Optional[str] = None
    classes: List[str] = field(default_factory=list)  # Class names
    functions: List[str] = field(default_factory=list)  # Function names
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    lines: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'file': self.file,
            'language': self.language.value,
            'docstring': self.docstring,
            'classes': self.classes,
            'functions': self.functions,
            'imports': self.imports,
            'exports': self.exports,
            'lines': self.lines,
            **self.metadata
        }


@dataclass
class ParseResult:
    """Result of parsing a file or codebase."""
    modules: List[ParsedModule] = field(default_factory=list)
    classes: List[ParsedClass] = field(default_factory=list)
    functions: List[ParsedFunction] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    cross_references: Optional[Any] = None  # CrossReferenceGraph (Any to avoid circular import)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'modules': [m.to_dict() for m in self.modules],
            'classes': [c.to_dict() for c in self.classes],
            'functions': [f.to_dict() for f in self.functions],
            'dependencies': self.dependencies,
            'errors': self.errors
        }

        # Include cross-references if available
        if self.cross_references and hasattr(self.cross_references, 'to_dict'):
            result['cross_references'] = self.cross_references.to_dict()

        return result

    def merge(self, other: 'ParseResult') -> 'ParseResult':
        """Merge another ParseResult into this one."""
        self.modules.extend(other.modules)
        self.classes.extend(other.classes)
        self.functions.extend(other.functions)
        for file, deps in other.dependencies.items():
            if file in self.dependencies:
                self.dependencies[file].extend(deps)
            else:
                self.dependencies[file] = deps
        self.errors.extend(other.errors)

        # Merge cross-references if both have them
        if self.cross_references and other.cross_references:
            # Merge calls
            self.cross_references.calls.extend(other.cross_references.calls)
            for callee, sites in other.cross_references.callers.items():
                if callee not in self.cross_references.callers:
                    self.cross_references.callers[callee] = []
                self.cross_references.callers[callee].extend(sites)
            for caller, sites in other.cross_references.callees.items():
                if caller not in self.cross_references.callees:
                    self.cross_references.callees[caller] = []
                self.cross_references.callees[caller].extend(sites)

            # Merge instantiations
            self.cross_references.instantiations.extend(other.cross_references.instantiations)
            for class_name, sites in other.cross_references.instantiated_by.items():
                if class_name not in self.cross_references.instantiated_by:
                    self.cross_references.instantiated_by[class_name] = []
                self.cross_references.instantiated_by[class_name].extend(sites)
            for instantiator, sites in other.cross_references.instantiators.items():
                if instantiator not in self.cross_references.instantiators:
                    self.cross_references.instantiators[instantiator] = []
                self.cross_references.instantiators[instantiator].extend(sites)

            # Merge imports
            for file, modules in other.cross_references.imports.items():
                if file not in self.cross_references.imports:
                    self.cross_references.imports[file] = set()
                self.cross_references.imports[file].update(modules)
            for module, files in other.cross_references.imported_by.items():
                if module not in self.cross_references.imported_by:
                    self.cross_references.imported_by[module] = set()
                self.cross_references.imported_by[module].update(files)

            # Merge warnings
            self.cross_references.warnings.extend(other.cross_references.warnings)

            # Update statistics
            self.cross_references.stats['total_calls'] += other.cross_references.stats['total_calls']
            self.cross_references.stats['total_instantiations'] += other.cross_references.stats['total_instantiations']
            self.cross_references.stats['total_warnings'] += other.cross_references.stats['total_warnings']
            for pattern, count in other.cross_references.stats.get('dynamic_patterns', {}).items():
                if pattern not in self.cross_references.stats['dynamic_patterns']:
                    self.cross_references.stats['dynamic_patterns'][pattern] = 0
                self.cross_references.stats['dynamic_patterns'][pattern] += count
        elif other.cross_references:
            self.cross_references = other.cross_references

        return self


class BaseParser(ABC):
    """
    Abstract base class for language-specific parsers.

    All language parsers must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, project_root: Path, exclude_patterns: Optional[List[str]] = None, cache: Optional[Any] = None):
        """
        Initialize the parser.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude from parsing
            cache: Optional PersistentCache instance for caching parse results
        """
        self.project_root = project_root.resolve()
        # Store CWD for computing relative paths in output
        self.cwd = Path.cwd()
        self.exclude_patterns = exclude_patterns or []
        self.cache = cache

    @property
    @abstractmethod
    def language(self) -> Language:
        """Return the language this parser handles."""
        pass

    @property
    @abstractmethod
    def file_extensions(self) -> List[str]:
        """Return list of file extensions this parser handles (without dots)."""
        pass

    @abstractmethod
    def _parse_file_impl(self, file_path: Path) -> ParseResult:
        """
        Parse a single file and return structured results (implementation).

        Subclasses should implement this method. Use parse_file() which wraps
        this with caching logic.

        Args:
            file_path: Path to the file to parse

        Returns:
            ParseResult containing parsed entities
        """
        pass

    def parse_file(self, file_path: Path) -> ParseResult:
        """
        Parse a single file and return structured results.

        Checks cache first if available, otherwise parses and stores in cache.

        Args:
            file_path: Path to the file to parse

        Returns:
            ParseResult containing parsed entities
        """
        # Check cache if available
        if self.cache:
            cached_result = self.cache.get_cached_result(file_path)
            if cached_result is not None:
                return cached_result

        # Parse file
        result = self._parse_file_impl(file_path)

        # Store in cache if available
        if self.cache:
            self.cache.store_result(file_path, result)

        return result

    def find_files(self) -> List[Path]:
        """
        Find all files of this language type in the project.

        Returns:
            List of file paths
        """
        files = []
        for ext in self.file_extensions:
            pattern = f"**/*.{ext}"
            for file_path in self.project_root.rglob(pattern):
                if not self._should_exclude(file_path):
                    files.append(file_path)
        return sorted(files)

    def parse_all(self, verbose: bool = False) -> ParseResult:
        """
        Parse all files of this language in the project.

        Args:
            verbose: Enable verbose output

        Returns:
            Merged ParseResult for all files
        """
        files = self.find_files()
        result = ParseResult()

        if verbose and files:
            print(f"  {self.language.value.upper()}: Found {len(files)} files")

        for i, file_path in enumerate(files, 1):
            if verbose:
                print(f"    [{i}/{len(files)}] {file_path.name}...", end='\r')

            try:
                file_result = self.parse_file(file_path)
                result.merge(file_result)
            except Exception as e:
                error_msg = f"Error parsing {file_path}: {e}"
                result.errors.append(error_msg)
                if verbose:
                    print(f"    ⚠️  {error_msg}")

        if verbose and files:
            print()  # New line after progress

        return result

    def _should_exclude(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded based on patterns.

        Uses path component matching to avoid false positives.
        For example, '.git' will match '.git/' but not '.github/'.

        Args:
            file_path: Path to check

        Returns:
            True if file should be excluded
        """
        path_parts = file_path.parts
        path_str = str(file_path)

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

        return False

    def _get_relative_path(self, file_path: Path) -> str:
        """
        Get path relative to current working directory.

        Args:
            file_path: Absolute file path

        Returns:
            Relative path as string
        """
        try:
            return str(file_path.relative_to(self.cwd))
        except ValueError:
            # If file is not under cwd (e.g., temp directory in tests),
            # use just the filename to keep paths simple and consistent
            return file_path.name
