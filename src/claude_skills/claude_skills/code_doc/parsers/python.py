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
from ..ast_analysis import (
    CrossReferenceGraph,
    CallSite,
    InstantiationSite,
    ReferenceType,
    DynamicPattern,
    DynamicPatternWarning,
    create_cross_reference_graph,
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

    class _CallTracker(ast.NodeVisitor):
        """
        AST visitor that tracks function calls and builds cross-reference graph.

        Walks the entire AST tree to find function/method calls, maintaining
        context about which function is currently being analyzed (the caller).
        """

        def __init__(self, graph: CrossReferenceGraph, file_path: str):
            """
            Initialize call tracker.

            Args:
                graph: CrossReferenceGraph to populate with calls
                file_path: Path to file being analyzed (for caller_file)
            """
            self.graph = graph
            self.file_path = file_path
            self.context_stack = []  # Stack of (type, name) tuples for current context
            self.current_function = None  # Name of current function being analyzed
            self.current_class = None  # Name of current class being analyzed

        def _push_context(self, context_type: str, name: str):
            """Push a new context onto the stack."""
            self.context_stack.append((context_type, name))
            if context_type == 'function':
                self.current_function = name
            elif context_type == 'class':
                self.current_class = name

        def _pop_context(self):
            """Pop context from stack and update current function/class."""
            if self.context_stack:
                self.context_stack.pop()

            # Update current_function to the most recent function in stack
            self.current_function = None
            self.current_class = None
            for context_type, name in reversed(self.context_stack):
                if context_type == 'function' and self.current_function is None:
                    self.current_function = name
                elif context_type == 'class' and self.current_class is None:
                    self.current_class = name

        def visit_FunctionDef(self, node: ast.FunctionDef):
            """Track entry into a function definition and check for decorators."""
            # Check for decorators (dynamic pattern warning)
            if node.decorator_list:
                for decorator in node.decorator_list:
                    decorator_name = self._extract_decorator_name(decorator)
                    location = f"{self.current_class}.{node.name}" if self.current_class else node.name
                    warning = DynamicPatternWarning(
                        pattern_type=DynamicPattern.DECORATOR,
                        location=location,
                        file=self.file_path,
                        line=node.lineno,
                        description=f"Function '{node.name}' has decorator: @{decorator_name}",
                        impact="Decorator may modify function behavior, add wrappers, or change call signatures, affecting cross-reference accuracy"
                    )
                    self.graph.add_warning(warning)

            self._push_context('function', node.name)
            self.generic_visit(node)  # Visit children
            self._pop_context()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            """Track entry into an async function definition and check for decorators."""
            # Check for decorators (dynamic pattern warning)
            if node.decorator_list:
                for decorator in node.decorator_list:
                    decorator_name = self._extract_decorator_name(decorator)
                    location = f"{self.current_class}.{node.name}" if self.current_class else node.name
                    warning = DynamicPatternWarning(
                        pattern_type=DynamicPattern.DECORATOR,
                        location=location,
                        file=self.file_path,
                        line=node.lineno,
                        description=f"Async function '{node.name}' has decorator: @{decorator_name}",
                        impact="Decorator may modify function behavior, add wrappers, or change call signatures, affecting cross-reference accuracy"
                    )
                    self.graph.add_warning(warning)

            self._push_context('function', node.name)
            self.generic_visit(node)  # Visit children
            self._pop_context()

        def visit_ClassDef(self, node: ast.ClassDef):
            """Track entry into a class definition."""
            self._push_context('class', node.name)
            self.generic_visit(node)  # Visit children
            self._pop_context()

        def visit_Call(self, node: ast.Call):
            """Track function/method calls, class instantiations, and dynamic patterns."""
            # Extract callee name from the call node
            callee_name = self._extract_callee_name(node.func)

            if callee_name:
                # Determine caller name (function or module-level)
                caller_name = self.current_function if self.current_function else '<module>'

                # Check for dynamic patterns that affect cross-reference accuracy
                # Priority: eval/exec (highest risk) > getattr/setattr > dynamic imports

                # Check for eval/exec (high-risk dynamic code execution)
                if callee_name in ('eval', 'exec'):
                    warning = DynamicPatternWarning(
                        pattern_type=DynamicPattern.EVAL_EXEC,
                        location=caller_name,
                        file=self.file_path,
                        line=node.lineno,
                        description=f"Use of {callee_name}() detected in '{caller_name}'",
                        impact=f"{callee_name}() executes arbitrary code that cannot be analyzed statically, leading to incomplete cross-references"
                    )
                    self.graph.add_warning(warning)

                # Check for getattr/setattr/hasattr/delattr (dynamic attribute access)
                elif callee_name in ('getattr', 'setattr', 'hasattr', 'delattr'):
                    warning = DynamicPatternWarning(
                        pattern_type=DynamicPattern.GETATTR_SETATTR,
                        location=caller_name,
                        file=self.file_path,
                        line=node.lineno,
                        description=f"Use of {callee_name}() for dynamic attribute access in '{caller_name}'",
                        impact="Dynamic attribute access bypasses static analysis, may miss attribute references and method calls"
                    )
                    self.graph.add_warning(warning)

                # Check for __import__ (dynamic module import)
                elif callee_name == '__import__':
                    warning = DynamicPatternWarning(
                        pattern_type=DynamicPattern.DYNAMIC_IMPORT,
                        location=caller_name,
                        file=self.file_path,
                        line=node.lineno,
                        description=f"Use of __import__() for dynamic module import in '{caller_name}'",
                        impact="Dynamic imports cannot be statically determined, missing import dependencies"
                    )
                    self.graph.add_warning(warning)

                # Check for importlib.import_module (dynamic import)
                elif callee_name == 'import_module':
                    warning = DynamicPatternWarning(
                        pattern_type=DynamicPattern.DYNAMIC_IMPORT,
                        location=caller_name,
                        file=self.file_path,
                        line=node.lineno,
                        description=f"Use of importlib.import_module() for dynamic import in '{caller_name}'",
                        impact="Dynamic imports cannot be statically determined, missing import dependencies"
                    )
                    self.graph.add_warning(warning)

                # Detect potential class instantiation (starts with uppercase)
                # Note: This is a heuristic - not all uppercase calls are class instantiations,
                # but it captures the most common Python convention. Method calls (via attributes)
                # are explicitly excluded to avoid false positives.
                if callee_name and callee_name[0].isupper() and not isinstance(node.func, ast.Attribute):
                    # This is likely a class instantiation
                    inst_site = InstantiationSite(
                        class_name=callee_name,
                        instantiator=caller_name,
                        instantiator_file=self.file_path,
                        instantiator_line=node.lineno,
                        metadata={
                            'in_class': self.current_class,
                            'context': [name for _, name in self.context_stack],
                            'is_heuristic': True  # Flag that this was detected heuristically
                        }
                    )
                    self.graph.add_instantiation(inst_site)
                else:
                    # Function or method call (existing logic)
                    call_type = ReferenceType.METHOD_CALL if isinstance(node.func, ast.Attribute) else ReferenceType.FUNCTION_CALL

                    # Create CallSite object
                    call_site = CallSite(
                        caller=caller_name,
                        caller_file=self.file_path,
                        caller_line=node.lineno,
                        callee=callee_name,
                        callee_file=None,  # Unknown at parse time, resolved later
                        call_type=call_type,
                        metadata={
                            'in_class': self.current_class,
                            'context': [name for _, name in self.context_stack]
                        }
                    )

                    # Add to graph
                    self.graph.add_call(call_site)

            # Continue visiting children
            self.generic_visit(node)

        def _extract_callee_name(self, node) -> str:
            """
            Extract the callee name from a call node.

            Handles:
            - Simple function calls: foo()
            - Method calls: obj.method()
            - Chained calls: obj.foo().bar() (extracts 'bar')
            - Attribute access: module.submodule.func()

            Args:
                node: AST node representing the function being called

            Returns:
                Callee name as string, or None if cannot extract
            """
            if isinstance(node, ast.Name):
                # Simple function call: foo()
                return node.id

            elif isinstance(node, ast.Attribute):
                # Method call or attribute access: obj.method()
                # For now, just return the method name
                return node.attr

            elif isinstance(node, ast.Call):
                # Chained call: foo().bar()
                # Recursively extract from the result of inner call
                return self._extract_callee_name(node.func)

            # For complex expressions (subscripts, lambda, etc.), skip for now
            return None

        def _extract_decorator_name(self, decorator) -> str:
            """
            Extract decorator name from decorator node.

            Args:
                decorator: AST node representing the decorator

            Returns:
                Decorator name as string
            """
            if isinstance(decorator, ast.Name):
                # Simple decorator: @decorator_name
                return decorator.id
            elif isinstance(decorator, ast.Attribute):
                # Attribute decorator: @module.decorator_name
                return ast.unparse(decorator)
            elif isinstance(decorator, ast.Call):
                # Decorator with arguments: @decorator_name(args)
                return ast.unparse(decorator.func)
            else:
                # Fallback for complex decorators
                return ast.unparse(decorator)

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

            # Create cross-reference graph and tracker
            graph = create_cross_reference_graph()
            tracker = self._CallTracker(graph, relative_path)

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

                    # Track imports in cross-reference graph for bidirectional lookup
                    for import_name in imports:
                        graph.add_import(relative_path, import_name)

            # Walk the entire AST to track function calls
            tracker.visit(tree)

            # Add cross-reference graph to result
            result.cross_references = graph

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
