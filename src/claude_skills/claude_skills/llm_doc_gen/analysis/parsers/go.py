"""
Go language parser using tree-sitter.

This module provides a parser for Go files that extracts packages,
functions, structs, interfaces, and methods.
"""

from pathlib import Path
from typing import List, Optional
import sys

_TREE_SITTER_IMPORT_ERROR: Optional[ImportError] = None

try:
    from tree_sitter import Language, Parser, Node
    import tree_sitter_go as tsgo
    TREE_SITTER_AVAILABLE = True
except ImportError as exc:
    TREE_SITTER_AVAILABLE = False
    _TREE_SITTER_IMPORT_ERROR = ImportError(
        "tree-sitter-go not available. Install with: "
        "pip install tree-sitter tree-sitter-go"
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


class GoParser(BaseParser):
    """Parser for Go files using tree-sitter."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter-go not available. Install with: "
                "pip install tree-sitter tree-sitter-go"
            )

        # Initialize parser with language grammar
        go_lang = Language(tsgo.language())
        self._parser = Parser(go_lang)

        # Initialize tree cache for incremental parsing
        self._tree_cache = TreeCache(max_cache_size=1000)

    @property
    def language(self) -> Lang:
        """Return Go language."""
        return Lang.GO

    @property
    def file_extensions(self) -> List[str]:
        """Go file extensions."""
        return ['go']

    def get_cache_stats(self):
        """Get tree cache statistics."""
        return self._tree_cache.get_stats()

    def clear_cache(self):
        """Clear the tree cache."""
        self._tree_cache.clear()

    def _parse_file_impl(self, file_path: Path) -> ParseResult:
        """
        Parse a Go file.

        Args:
            file_path: Path to Go file

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
                language=Lang.GO,
                lines=len(source_text.splitlines())
            )

            # Extract package name
            package_name = self._extract_package_name(root, source)
            if package_name:
                module.metadata['package'] = package_name

            # Extract top-level entities
            for child in root.children:
                if child.type == 'type_declaration':
                    # Could be struct, interface, or type alias
                    entities = self._extract_type_declaration(child, relative_path, source)
                    for entity in entities:
                        if isinstance(entity, ParsedClass):
                            module.classes.append(entity.name)
                            result.classes.append(entity)

                elif child.type == 'function_declaration':
                    func_entity = self._extract_function(child, relative_path, source)
                    if func_entity:
                        module.functions.append(func_entity.name)
                        result.functions.append(func_entity)

                elif child.type == 'method_declaration':
                    # Methods are functions with receivers
                    method_entity = self._extract_method(child, relative_path, source)
                    if method_entity:
                        result.functions.append(method_entity)

                elif child.type == 'import_declaration':
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

    def _extract_package_name(self, node: 'Node', source: bytes) -> Optional[str]:
        """Extract package name from Go file."""
        for child in node.children:
            if child.type == 'package_clause':
                pkg_id = child.child_by_field_name('name')
                if pkg_id:
                    return self._get_node_text(pkg_id, source)
        return None

    def _extract_type_declaration(self, node: 'Node', file_path: str, source: bytes) -> List:
        """Extract type declarations (struct, interface, type alias)."""
        entities = []

        for child in node.children:
            if child.type == 'type_spec':
                name_node = child.child_by_field_name('name')
                type_node = child.child_by_field_name('type')

                if not name_node or not type_node:
                    continue

                name = self._get_node_text(name_node, source)

                if type_node.type == 'struct_type':
                    # Parse struct
                    struct_entity = self._extract_struct(name, type_node, child, file_path, source)
                    if struct_entity:
                        entities.append(struct_entity)

                elif type_node.type == 'interface_type':
                    # Parse interface
                    interface_entity = self._extract_interface(name, type_node, child, file_path, source)
                    if interface_entity:
                        entities.append(interface_entity)

        return entities

    def _extract_struct(self, name: str, type_node: 'Node', decl_node: 'Node',
                       file_path: str, source: bytes) -> Optional[ParsedClass]:
        """Extract struct information."""
        fields = []

        # Get struct fields
        field_list = type_node.child_by_field_name('fields')
        if field_list:
            for child in field_list.children:
                if child.type == 'field_declaration':
                    field_name_node = child.child_by_field_name('name')
                    if field_name_node:
                        field_name = self._get_node_text(field_name_node, source)
                        fields.append(field_name)

        return ParsedClass(
            name=name,
            file=file_path,
            line=decl_node.start_point[0] + 1,
            language=Lang.GO,
            properties=fields,
            is_public=name[0].isupper() if name else False,
            metadata={'kind': 'struct'}
        )

    def _extract_interface(self, name: str, type_node: 'Node', decl_node: 'Node',
                          file_path: str, source: bytes) -> Optional[ParsedClass]:
        """Extract interface information."""
        methods = []

        # Get interface methods
        method_list = type_node.child_by_field_name('methods')
        if method_list:
            for child in method_list.children:
                if child.type == 'method_spec':
                    method_name_node = child.child_by_field_name('name')
                    if method_name_node:
                        method_name = self._get_node_text(method_name_node, source)
                        methods.append(method_name)

        return ParsedClass(
            name=name,
            file=file_path,
            line=decl_node.start_point[0] + 1,
            language=Lang.GO,
            methods=methods,
            is_public=name[0].isupper() if name else False,
            metadata={'kind': 'interface'}
        )

    def _extract_function(self, node: 'Node', file_path: str, source: bytes) -> Optional[ParsedFunction]:
        """Extract function information."""
        name_node = node.child_by_field_name('name')
        if not name_node:
            return None

        name = self._get_node_text(name_node, source)

        # Extract parameters
        parameters = []
        params_node = node.child_by_field_name('parameters')
        if params_node:
            for child in params_node.children:
                if child.type == 'parameter_declaration':
                    param_name_node = child.child_by_field_name('name')
                    if param_name_node:
                        param_name = self._get_node_text(param_name_node, source)
                        parameters.append(ParsedParameter(name=param_name))

        return ParsedFunction(
            name=name,
            file=file_path,
            line=node.start_point[0] + 1,
            language=Lang.GO,
            parameters=parameters,
            is_public=name[0].isupper() if name else False,
            complexity=self._estimate_complexity(node)
        )

    def _extract_method(self, node: 'Node', file_path: str, source: bytes) -> Optional[ParsedFunction]:
        """Extract method information (function with receiver)."""
        name_node = node.child_by_field_name('name')
        receiver_node = node.child_by_field_name('receiver')

        if not name_node:
            return None

        name = self._get_node_text(name_node, source)
        receiver = ""

        if receiver_node:
            receiver = self._get_node_text(receiver_node, source)

        # Extract parameters
        parameters = []
        params_node = node.child_by_field_name('parameters')
        if params_node:
            for child in params_node.children:
                if child.type == 'parameter_declaration':
                    param_name_node = child.child_by_field_name('name')
                    if param_name_node:
                        param_name = self._get_node_text(param_name_node, source)
                        parameters.append(ParsedParameter(name=param_name))

        return ParsedFunction(
            name=name,
            file=file_path,
            line=node.start_point[0] + 1,
            language=Lang.GO,
            parameters=parameters,
            is_public=name[0].isupper() if name else False,
            complexity=self._estimate_complexity(node),
            metadata={'receiver': receiver, 'is_method': True}
        )

    def _extract_imports(self, node: 'Node', source: bytes) -> List[str]:
        """Extract import statements."""
        imports = []

        for child in node.children:
            if child.type == 'import_spec_list':
                # Handle grouped imports: import ( ... )
                for spec in child.children:
                    if spec.type == 'import_spec':
                        import_path = self._extract_import_path(spec, source)
                        if import_path:
                            imports.append(import_path)
            elif child.type == 'import_spec':
                # Handle single imports: import "fmt"
                import_path = self._extract_import_path(child, source)
                if import_path:
                    imports.append(import_path)

        return imports

    def _extract_import_path(self, spec_node: 'Node', source: bytes) -> str:
        """Extract import path from an import_spec node."""
        # Look for interpreted_string_literal
        for child in spec_node.children:
            if child.type == 'interpreted_string_literal':
                # Get the content (without quotes)
                for subchild in child.children:
                    if subchild.type == 'interpreted_string_literal_content':
                        return self._get_node_text(subchild, source)
        return ""

    def _estimate_complexity(self, node: 'Node') -> int:
        """Estimate cyclomatic complexity by counting decision points."""
        complexity = 1  # Base complexity

        def count_decisions(n: 'Node'):
            nonlocal complexity
            if n.type in ['if_statement', 'for_statement', 'expression_switch_statement',
                          'type_switch_statement', 'select_statement']:
                complexity += 1
            for child in n.children:
                count_decisions(child)

        count_decisions(node)
        return complexity

    def _get_node_text(self, node: 'Node', source: bytes) -> str:
        """Extract text from a tree-sitter node."""
        return source[node.start_byte:node.end_byte].decode('utf-8')
