"""
Multi-language parsers for codebase documentation generation.

This package provides abstract base classes and language-specific parsers
for analyzing codebases in multiple programming languages.
"""

from .base import (
    BaseParser,
    Language,
    ParsedParameter,
    ParsedFunction,
    ParsedClass,
    ParsedModule,
    ParseResult,
)
from .factory import ParserFactory, create_parser_factory
from .python import PythonParser

# Optional parsers (may not be available if tree-sitter not installed).
# Individual modules raise ImportError with installation guidance when
# dependencies are missing so auto-discovery can safely skip them.
try:
    from .javascript import JavaScriptParser
except ImportError:
    JavaScriptParser = None

try:
    from .go import GoParser
except ImportError:
    GoParser = None

try:
    from .html import HTMLParser
except ImportError:
    HTMLParser = None

try:
    from .css import CSSParser
except ImportError:
    CSSParser = None

__all__ = [
    'BaseParser',
    'Language',
    'ParsedParameter',
    'ParsedFunction',
    'ParsedClass',
    'ParsedModule',
    'ParseResult',
    'ParserFactory',
    'create_parser_factory',
    'PythonParser',
    'JavaScriptParser',
    'GoParser',
    'HTMLParser',
    'CSSParser',
]
