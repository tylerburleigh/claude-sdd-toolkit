"""
HTML language parser using tree-sitter.

This module provides a parser for HTML files that extracts elements,
custom components, HTMX attributes, and data attributes.
"""

from pathlib import Path
from typing import List, Dict, Optional
import sys

_TREE_SITTER_IMPORT_ERROR: Optional[ImportError] = None

try:
    from tree_sitter import Language, Parser, Node
    import tree_sitter_html as tshtml
    TREE_SITTER_AVAILABLE = True
except ImportError as exc:
    TREE_SITTER_AVAILABLE = False
    _TREE_SITTER_IMPORT_ERROR = ImportError(
        "tree-sitter-html not available. Install with: "
        "pip install tree-sitter tree-sitter-html"
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


class HTMLParser(BaseParser):
    """Parser for HTML files using tree-sitter."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter-html not available. Install with: "
                "pip install tree-sitter tree-sitter-html"
            )

        # Initialize parser with language grammar
        html_lang = Language(tshtml.language())
        self._parser = Parser(html_lang)

        # Initialize tree cache for incremental parsing
        self._tree_cache = TreeCache(max_cache_size=1000)

        # HTMX attributes to track
        self.htmx_attributes = {
            'hx-get', 'hx-post', 'hx-put', 'hx-patch', 'hx-delete',
            'hx-trigger', 'hx-target', 'hx-swap', 'hx-select',
            'hx-include', 'hx-push-url', 'hx-boost', 'hx-confirm',
            'hx-vals', 'hx-headers', 'hx-indicator'
        }

    @property
    def language(self) -> Lang:
        """Return HTML language."""
        return Lang.HTML

    @property
    def file_extensions(self) -> List[str]:
        """HTML file extensions."""
        return ['html', 'htm']

    def get_cache_stats(self):
        """Get tree cache statistics."""
        return self._tree_cache.get_stats()

    def clear_cache(self):
        """Clear the tree cache."""
        self._tree_cache.clear()

    def _parse_file_impl(self, file_path: Path) -> ParseResult:
        """
        Parse an HTML file.

        Args:
            file_path: Path to HTML file

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
                language=Lang.HTML,
                lines=len(source_text.splitlines())
            )

            # Extract HTML structure
            stats = self._extract_html_structure(root, source)

            # Store metadata about the HTML file
            module.metadata['element_counts'] = stats['elements']
            module.metadata['htmx_usage'] = stats['htmx_attrs']
            module.metadata['custom_attributes'] = stats['custom_attrs']
            module.metadata['scripts'] = stats['scripts']
            module.metadata['styles'] = stats['styles']

            # Store as "functions" for documentation purposes
            for element_type, count in stats['elements'].items():
                if count > 0:
                    module.functions.append(f"{element_type} ({count})")

            result.modules.append(module)

        except Exception as e:
            error_msg = f"Error parsing {file_path}: {e}"
            result.errors.append(error_msg)
            print(f"❌ {error_msg}", file=sys.stderr)

        return result

    def _extract_html_structure(self, node: 'Node', source: bytes) -> Dict:
        """Extract HTML structure and attributes."""
        stats = {
            'elements': {},
            'htmx_attrs': [],
            'custom_attrs': [],
            'scripts': 0,
            'styles': 0,
        }

        def traverse(n: 'Node'):
            if n.type == 'element':
                # Get tag name
                tag_node = n.child_by_field_name('start_tag')
                if tag_node:
                    tag_name_node = tag_node.child_by_field_name('tag_name')
                    if tag_name_node:
                        tag_name = self._get_node_text(tag_name_node, source)

                        # Count element
                        if tag_name not in stats['elements']:
                            stats['elements'][tag_name] = 0
                        stats['elements'][tag_name] += 1

                        # Count scripts and styles
                        if tag_name == 'script':
                            stats['scripts'] += 1
                        elif tag_name == 'style':
                            stats['styles'] += 1

                # Extract attributes
                attributes = self._extract_attributes(n, source)
                for attr_name in attributes:
                    # Check for HTMX
                    if attr_name in self.htmx_attributes:
                        if attr_name not in stats['htmx_attrs']:
                            stats['htmx_attrs'].append(attr_name)

                    # Check for custom data attributes
                    elif attr_name.startswith('data-'):
                        if attr_name not in stats['custom_attrs']:
                            stats['custom_attrs'].append(attr_name)

            # Recurse
            for child in n.children:
                traverse(child)

        traverse(node)
        return stats

    def _extract_attributes(self, element_node: 'Node', source: bytes) -> List[str]:
        """Extract attribute names from an element."""
        attributes = []

        start_tag = element_node.child_by_field_name('start_tag')
        if not start_tag:
            return attributes

        for child in start_tag.children:
            if child.type == 'attribute':
                attr_name_node = child.child_by_field_name('attribute_name')
                if attr_name_node:
                    attr_name = self._get_node_text(attr_name_node, source)
                    attributes.append(attr_name)

        return attributes

    def _get_node_text(self, node: 'Node', source: bytes) -> str:
        """Extract text from a tree-sitter node."""
        return source[node.start_byte:node.end_byte].decode('utf-8')
