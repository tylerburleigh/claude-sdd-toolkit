"""
JavaScript and TypeScript language parser using tree-sitter.

This module provides a parser for JavaScript/TypeScript files that extracts
classes, functions, imports, and exports.
"""

from pathlib import Path
from typing import List, Optional
import sys

_TREE_SITTER_IMPORT_ERROR: Optional[ImportError] = None

try:
    from tree_sitter import Language, Parser, Node
    import tree_sitter_javascript as tsjs
    import tree_sitter_typescript as tsts
    TREE_SITTER_AVAILABLE = True
except ImportError as exc:
    TREE_SITTER_AVAILABLE = False
    _TREE_SITTER_IMPORT_ERROR = ImportError(
        "tree-sitter not available. Install with: "
        "pip install tree-sitter tree-sitter-javascript tree-sitter-typescript"
    )
    _TREE_SITTER_IMPORT_ERROR.__cause__ = exc

if not TREE_SITTER_AVAILABLE:
    raise _TREE_SITTER_IMPORT_ERROR

from .base import (
    BaseParser,
    Language as Lang,
    ParseResult,
    ParsedModule,
    ParsedClass,
    ParsedFunction,
    ParsedParameter,
)
from ..tree_cache import TreeCache


class JavaScriptParser(BaseParser):
    """Parser for JavaScript and TypeScript files using tree-sitter."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter not available. Install with: "
                "pip install tree-sitter tree-sitter-javascript tree-sitter-typescript"
            )

        # Initialize parsers with language grammars
        js_lang = Language(tsjs.language())
        ts_lang = Language(tsts.language_typescript())
        self._js_parser = Parser(js_lang)
        self._ts_parser = Parser(ts_lang)

        # Initialize tree cache for incremental parsing
        self._tree_cache = TreeCache(max_cache_size=1000)

    @property
    def language(self) -> Lang:
        """Return JavaScript language (also handles TypeScript)."""
        return Lang.JAVASCRIPT

    @property
    def file_extensions(self) -> List[str]:
        """JavaScript and TypeScript file extensions."""
        return ['js', 'jsx', 'ts', 'tsx', 'mjs', 'cjs']

    def get_cache_stats(self):
        """
        Get tree cache statistics.

        Returns:
            Dictionary with cache performance metrics (hits, misses, size, hit_rate)
        """
        return self._tree_cache.get_stats()

    def clear_cache(self):
        """Clear the tree cache."""
        self._tree_cache.clear()

    def _parse_file_impl(self, file_path: Path) -> ParseResult:
        """
        Parse a JavaScript/TypeScript file.

        Args:
            file_path: Path to JS/TS file

        Returns:
            ParseResult containing parsed entities
        """
        result = ParseResult()
        relative_path = self._get_relative_path(file_path)

        try:
            with open(file_path, 'rb') as f:
                source = f.read()

            # Determine language and parser
            is_typescript = file_path.suffix in ['.ts', '.tsx']
            parser = self._ts_parser if is_typescript else self._js_parser
            lang = Lang.TYPESCRIPT if is_typescript else Lang.JAVASCRIPT

            # Check cache for existing tree (incremental parsing)
            cached = self._tree_cache.get(file_path)

            # Parse source code (incremental if cached tree available)
            if cached:
                tree = parser.parse(source, old_tree=cached.tree)
            else:
                tree = parser.parse(source)
            root = tree.root_node

            # Decode source for further processing
            source_text = source.decode('utf-8')

            # Store in cache for future incremental parsing
            self._tree_cache.put(file_path, tree, source_text)

            # Create module info
            module = ParsedModule(
                name=file_path.stem,
                file=relative_path,
                language=lang,
                lines=len(source_text.splitlines())
            )

            # Extract top-level entities
            for child in root.children:
                if child.type == 'class_declaration':
                    class_entity = self._extract_class(child, relative_path, lang, source)
                    if class_entity:
                        module.classes.append(class_entity.name)
                        result.classes.append(class_entity)

                elif child.type in ['function_declaration', 'arrow_function', 'function']:
                    func_entity = self._extract_function(child, relative_path, lang, source)
                    if func_entity:
                        module.functions.append(func_entity.name)
                        result.functions.append(func_entity)

                elif child.type in ['lexical_declaration', 'variable_declaration']:
                    # Handle arrow functions assigned to variables
                    func_entities = self._extract_variable_functions(child, relative_path, lang, source)
                    for func_entity in func_entities:
                        module.functions.append(func_entity.name)
                        result.functions.append(func_entity)

                elif child.type in ['export_statement', 'export_default_declaration']:
                    exports = self._extract_exports(child, source)
                    module.exports.extend(exports)

                elif child.type in ['import_statement', 'import_declaration']:
                    imports = self._extract_imports(child, source)
                    module.imports.extend(imports)
                    if imports:
                        if relative_path not in result.dependencies:
                            result.dependencies[relative_path] = []
                        result.dependencies[relative_path].extend(imports)

            result.modules.append(module)

        except Exception as e:
            error_msg = f"Error parsing {file_path}: {e}"
            result.errors.append(error_msg)
            print(f"❌ {error_msg}", file=sys.stderr)

        return result

    def _extract_class(self, node: 'Node', file_path: str, lang: Lang, source: bytes) -> Optional[ParsedClass]:
        """Extract class information from tree-sitter node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return None

        name = self._get_node_text(name_node, source)

        methods = []
        properties = []

        # Find class body
        body_node = node.child_by_field_name('body')
        if body_node:
            for child in body_node.children:
                if child.type == 'method_definition':
                    method_name_node = child.child_by_field_name('name')
                    if method_name_node:
                        method_name = self._get_node_text(method_name_node, source)
                        methods.append(method_name)

                elif child.type in ['field_definition', 'public_field_definition']:
                    prop_name_node = child.child_by_field_name('property')
                    if prop_name_node:
                        prop_name = self._get_node_text(prop_name_node, source)
                        properties.append(prop_name)

        # Extract superclass
        bases = []
        # Find class_heritage node among children
        for child in node.children:
            if child.type == 'class_heritage':
                # class_heritage contains 'extends' keyword and identifiers
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        bases.append(self._get_node_text(subchild, source))
                break

        return ParsedClass(
            name=name,
            file=file_path,
            line=node.start_point[0] + 1,
            language=lang,
            bases=bases,
            methods=methods,
            properties=properties,
            is_exported=self._is_exported(node),
            is_public=not name.startswith('_')
        )

    def _extract_function(self, node: 'Node', file_path: str, lang: Lang, source: bytes) -> Optional[ParsedFunction]:
        """Extract function information from tree-sitter node."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            # Anonymous function - try to find identifier
            return None

        name = self._get_node_text(name_node, source)

        # Extract parameters
        parameters = []
        params_node = node.child_by_field_name('parameters')
        if params_node:
            for child in params_node.children:
                if child.type in ['identifier', 'required_parameter', 'optional_parameter']:
                    param_name = self._get_node_text(child, source)
                    # Remove type annotations for display
                    param_name = param_name.split(':')[0].strip()
                    parameters.append(ParsedParameter(name=param_name))

        # Check if async - look for 'async' as a child of the function node
        is_async = False
        for child in node.children:
            if child.type == 'async':
                is_async = True
                break

        return ParsedFunction(
            name=name,
            file=file_path,
            line=node.start_point[0] + 1,
            language=lang,
            parameters=parameters,
            is_async=is_async,
            is_exported=self._is_exported(node),
            is_public=not name.startswith('_'),
            complexity=self._estimate_complexity(node)
        )

    def _extract_variable_functions(self, node: 'Node', file_path: str, lang: Lang, source: bytes) -> List[ParsedFunction]:
        """Extract arrow functions from variable declarations."""
        functions = []

        for child in node.children:
            if child.type == 'variable_declarator':
                name_node = child.child_by_field_name('name')
                value_node = child.child_by_field_name('value')

                if name_node and value_node:
                    # Check if value is an arrow function or function expression
                    if value_node.type in ['arrow_function', 'function', 'function_expression']:
                        name = self._get_node_text(name_node, source)

                        # Extract parameters
                        parameters = []
                        params_node = value_node.child_by_field_name('parameters')
                        if params_node:
                            for param_child in params_node.children:
                                if param_child.type in ['identifier', 'required_parameter', 'optional_parameter']:
                                    param_name = self._get_node_text(param_child, source)
                                    param_name = param_name.split(':')[0].strip()
                                    parameters.append(ParsedParameter(name=param_name))

                        # Check if async - look for 'async' keyword before the declaration
                        is_async = False
                        parent = node.parent
                        if parent:
                            for sibling in parent.children:
                                if sibling.start_byte < node.start_byte and sibling.type == 'async':
                                    is_async = True
                                    break

                        func = ParsedFunction(
                            name=name,
                            file=file_path,
                            line=value_node.start_point[0] + 1,
                            language=lang,
                            parameters=parameters,
                            is_async=is_async,
                            is_exported=self._is_exported(node),
                            is_public=not name.startswith('_'),
                            complexity=self._estimate_complexity(value_node)
                        )
                        functions.append(func)

        return functions

    def _extract_imports(self, node: 'Node', source: bytes) -> List[str]:
        """Extract import statements."""
        imports = []

        source_node = node.child_by_field_name('source')
        if source_node:
            module_name = self._get_node_text(source_node, source).strip('"').strip("'")
            imports.append(module_name)

        return imports

    def _extract_exports(self, node: 'Node', source: bytes) -> List[str]:
        """Extract export statements."""
        exports = []

        # Handle different export types
        for child in node.children:
            if child.type == 'identifier':
                exports.append(self._get_node_text(child, source))
            elif child.type in ['class_declaration', 'function_declaration']:
                name_node = child.child_by_field_name('name')
                if name_node:
                    exports.append(self._get_node_text(name_node, source))

        return exports

    def _is_exported(self, node: 'Node') -> bool:
        """Check if node is exported."""
        parent = node.parent
        while parent:
            if parent.type in ['export_statement', 'export_default_declaration']:
                return True
            parent = parent.parent
        return False

    def _estimate_complexity(self, node: 'Node') -> int:
        """Estimate cyclomatic complexity by counting decision points."""
        complexity = 1  # Base complexity

        def count_decisions(n: 'Node'):
            nonlocal complexity
            if n.type in ['if_statement', 'while_statement', 'for_statement',
                          'switch_case', 'catch_clause', 'ternary_expression']:
                complexity += 1
            for child in n.children:
                count_decisions(child)

        count_decisions(node)
        return complexity

    def _get_node_text(self, node: 'Node', source: bytes) -> str:
        """Extract text from a tree-sitter node."""
        return source[node.start_byte:node.end_byte].decode('utf-8')
