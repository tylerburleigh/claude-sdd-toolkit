"""
CSS language parser using tree-sitter.

This module provides a parser for CSS files that extracts selectors,
rules, variables, and @-rules.
"""

from pathlib import Path
from typing import List, Dict, Optional
import sys

_TREE_SITTER_IMPORT_ERROR: Optional[ImportError] = None

try:
    from tree_sitter import Language, Parser, Node
    import tree_sitter_css as tscss
    TREE_SITTER_AVAILABLE = True
except ImportError as exc:
    TREE_SITTER_AVAILABLE = False
    _TREE_SITTER_IMPORT_ERROR = ImportError(
        "tree-sitter-css not available. Install with: "
        "pip install tree-sitter tree-sitter-css"
    )
    _TREE_SITTER_IMPORT_ERROR.__cause__ = exc

if not TREE_SITTER_AVAILABLE:
    raise _TREE_SITTER_IMPORT_ERROR

from .base import (
    BaseParser,
    Language as Lang,
    ParseResult,
    ParsedModule,
    ParsedFunction,
)
from ..tree_cache import TreeCache


class CSSParser(BaseParser):
    """Parser for CSS files using tree-sitter."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter-css not available. Install with: "
                "pip install tree-sitter tree-sitter-css"
            )

        # Initialize parser with language grammar
        css_lang = Language(tscss.language())
        self._parser = Parser(css_lang)

        # Initialize tree cache for incremental parsing
        self._tree_cache = TreeCache(max_cache_size=1000)

    @property
    def language(self) -> Lang:
        """Return CSS language."""
        return Lang.CSS

    @property
    def file_extensions(self) -> List[str]:
        """CSS file extensions."""
        return ['css']

    def get_cache_stats(self):
        """Get tree cache statistics."""
        return self._tree_cache.get_stats()

    def clear_cache(self):
        """Clear the tree cache."""
        self._tree_cache.clear()

    def _parse_file_impl(self, file_path: Path) -> ParseResult:
        """
        Parse a CSS file.

        Args:
            file_path: Path to CSS file

        Returns:
            ParseResult containing parsed entities
        """
        result = ParseResult()
        relative_path = self._get_relative_path(file_path)

        try:
            with open(file_path, 'rb') as f:
                source = f.read()

            # Check cache for existing tree (incremental parsing)
            cached = self._tree_cache.get(file_path)

            # Parse source code (incremental if cached tree available)
            if cached:
                tree = self._parser.parse(source, old_tree=cached.tree)
            else:
                tree = self._parser.parse(source)
            root = tree.root_node

            # Decode source for further processing
            source_text = source.decode('utf-8')

            # Store in cache for future incremental parsing
            self._tree_cache.put(file_path, tree, source_text)

            # Create module info
            module = ParsedModule(
                name=file_path.stem,
                file=relative_path,
                language=Lang.CSS,
                lines=len(source_text.splitlines())
            )

            # Extract CSS structure
            stats = self._extract_css_structure(root, source)

            # Store metadata
            module.metadata['selector_counts'] = stats['selectors']
            module.metadata['variables'] = stats['variables']
            module.metadata['at_rules'] = stats['at_rules']
            module.metadata['total_rules'] = stats['total_rules']

            # Store as "functions" for documentation purposes
            for selector_type, count in stats['selectors'].items():
                if count > 0:
                    module.functions.append(f"{selector_type} ({count})")

            # Store variables as imports (for reference tracking)
            module.imports.extend(stats['variables'])

            result.modules.append(module)

        except Exception as e:
            error_msg = f"Error parsing {file_path}: {e}"
            result.errors.append(error_msg)
            print(f"❌ {error_msg}", file=sys.stderr)

        return result

    def _extract_css_structure(self, node: 'Node', source: bytes) -> Dict:
        """Extract CSS structure including selectors, variables, and rules."""
        stats = {
            'selectors': {
                'class': 0,
                'id': 0,
                'element': 0,
                'attribute': 0,
                'pseudo-class': 0,
                'pseudo-element': 0,
            },
            'variables': [],
            'at_rules': [],
            'total_rules': 0,
        }

        def traverse(n: 'Node'):
            if n.type == 'rule_set':
                stats['total_rules'] += 1

                # Extract selectors
                for child in n.children:
                    if child.type == 'selectors':
                        self._count_selectors(child, stats['selectors'], source)

            elif n.type == 'declaration':
                # Check for CSS variables (custom properties)
                prop_node = n.child_by_field_name('property')
                if prop_node:
                    prop_name = self._get_node_text(prop_node, source)
                    if prop_name.startswith('--'):
                        if prop_name not in stats['variables']:
                            stats['variables'].append(prop_name)

            elif n.type in ['media_statement', 'keyframes_statement', 'import_statement',
                           'charset_statement', 'supports_statement']:
                # @-rules
                rule_name = self._extract_at_rule_name(n, source)
                if rule_name and rule_name not in stats['at_rules']:
                    stats['at_rules'].append(rule_name)

            # Recurse
            for child in n.children:
                traverse(child)

        traverse(node)
        return stats

    def _count_selectors(self, selectors_node: 'Node', counts: Dict, source: bytes):
        """Count different types of selectors."""
        def count_selector_parts(n: 'Node'):
            if n.type == 'class_selector':
                counts['class'] += 1
            elif n.type == 'id_selector':
                counts['id'] += 1
            elif n.type == 'tag_name':
                counts['element'] += 1
            elif n.type == 'attribute_selector':
                counts['attribute'] += 1
            elif n.type == 'pseudo_class_selector':
                counts['pseudo-class'] += 1
            elif n.type == 'pseudo_element_selector':
                counts['pseudo-element'] += 1

            for child in n.children:
                count_selector_parts(child)

        count_selector_parts(selectors_node)

    def _extract_at_rule_name(self, node: 'Node', source: bytes) -> str:
        """Extract @-rule name."""
        if node.type == 'media_statement':
            return '@media'
        elif node.type == 'keyframes_statement':
            return '@keyframes'
        elif node.type == 'import_statement':
            return '@import'
        elif node.type == 'charset_statement':
            return '@charset'
        elif node.type == 'supports_statement':
            return '@supports'
        return ''

    def _get_node_text(self, node: 'Node', source: bytes) -> str:
        """Extract text from a tree-sitter node."""
        return source[node.start_byte:node.end_byte].decode('utf-8')
