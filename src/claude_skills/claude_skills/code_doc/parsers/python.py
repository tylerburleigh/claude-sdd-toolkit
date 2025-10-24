"""
Python language parser using AST analysis.

This module provides a parser for Python files that extracts classes,
functions, imports, and complexity metrics.
"""

import ast
import sys
from pathlib import Path
from typing import List
from collections import defaultdict

from .base import (
    BaseParser,
    Language,
    ParseResult,
    ParsedModule,
    ParsedClass,
    ParsedFunction,
    ParsedParameter,
)


class PythonParser(BaseParser):
    """Parser for Python source files using AST analysis."""

    @property
    def language(self) -> Language:
        """Return Python language."""
        return Language.PYTHON

    @property
    def file_extensions(self) -> List[str]:
        """Python file extensions."""
        return ['py']

    def parse_file(self, file_path: Path) -> ParseResult:
        """
        Parse a Python file and extract structure.

        Args:
            file_path: Path to Python file

        Returns:
            ParseResult containing parsed entities
        """
        result = ParseResult()
        relative_path = self._get_relative_path(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)

            # Create module info
            module = ParsedModule(
                name=file_path.stem,
                file=relative_path,
                language=Language.PYTHON,
                docstring=ast.get_docstring(tree),
                lines=len(source.splitlines())
            )

            # Collect dependencies
            dependencies = []

            # Walk the AST to find top-level definitions
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    class_entity = self._extract_class(node, relative_path)
                    module.classes.append(class_entity.name)
                    result.classes.append(class_entity)

                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    func_entity = self._extract_function(node, relative_path)
                    module.functions.append(func_entity.name)
                    result.functions.append(func_entity)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports = self._extract_imports(node)
                    module.imports.extend(imports)
                    dependencies.extend(imports)

            # Add module to result
            result.modules.append(module)

            # Add dependencies
            if dependencies:
                result.dependencies[relative_path] = dependencies

        except SyntaxError as e:
            error_msg = f"Syntax error in {file_path}: {e}"
            result.errors.append(error_msg)
            print(f"⚠️  {error_msg}", file=sys.stderr)

        except Exception as e:
            error_msg = f"Error analyzing {file_path}: {e}"
            result.errors.append(error_msg)
            print(f"❌ {error_msg}", file=sys.stderr)

        return result

    def _extract_class(self, node: ast.ClassDef, file_path: str) -> ParsedClass:
        """Extract class information from AST node."""
        methods = []
        properties = []

        # Analyze class members
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for @property decorator
                decorators = item.decorator_list if hasattr(item, 'decorator_list') else []
                is_property = any(
                    isinstance(d, ast.Name) and d.id == 'property'
                    for d in decorators
                )
                if is_property:
                    properties.append(item.name)
                else:
                    methods.append(item.name)

        # Extract base classes
        bases = [self._get_name(base) for base in node.bases]

        return ParsedClass(
            name=node.name,
            file=file_path,
            line=node.lineno,
            language=Language.PYTHON,
            docstring=ast.get_docstring(node),
            bases=bases,
            methods=methods,
            properties=properties,
            is_public=not node.name.startswith('_')
        )

    def _extract_function(self, node, file_path: str) -> ParsedFunction:
        """Extract function information from AST node."""
        # Import calculator here to avoid circular dependency
        try:
            from ..calculator import calculate_complexity
        except ImportError:
            from claude_skills.code_doc.calculator import calculate_complexity

        complexity = calculate_complexity(node)

        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param = ParsedParameter(name=arg.arg)
            if hasattr(arg, 'annotation') and arg.annotation:
                param.type = ast.unparse(arg.annotation)
            parameters.append(param)

        # Extract decorators
        decorators = []
        if hasattr(node, 'decorator_list'):
            decorators = [ast.unparse(d) for d in node.decorator_list]

        # Extract return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        return ParsedFunction(
            name=node.name,
            file=file_path,
            line=node.lineno,
            language=Language.PYTHON,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            return_type=return_type,
            complexity=complexity,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_public=not node.name.startswith('_')
        )

    def _extract_imports(self, node) -> List[str]:
        """Extract import statements from AST node."""
        imports = []

        if isinstance(node, ast.Import):
            imports.extend([alias.name for alias in node.names])

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                import_name = f"{module}.{alias.name}" if module else alias.name
                imports.append(import_name)

        return imports

    def _get_name(self, node) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return str(node)
