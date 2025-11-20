"""
AST parsing and codebase analysis module.
Handles Python file discovery, parsing, and structure extraction.
"""

import ast
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class CodebaseAnalyzer:
    """Analyzes Python codebase and extracts structure."""

    def __init__(self, project_root: Path, exclude_patterns: List[str] = None):
        self.project_root = project_root
        self.exclude_patterns = exclude_patterns or ['__pycache__', '.git', 'venv', '.env']
        self.modules = []
        self.all_classes = []
        self.all_functions = []
        self.dependencies = defaultdict(set)

    def analyze(self, verbose: bool = False) -> Dict[str, Any]:
        """Main analysis method."""
        if verbose:
            print(f"📁 Analyzing {self.project_root}...")

        # Find all Python files
        py_files = self._find_python_files()

        if verbose:
            print(f"📄 Found {len(py_files)} Python files")

        for i, py_file in enumerate(py_files, 1):
            if verbose:
                print(f"  [{i}/{len(py_files)}] Processing {py_file.name}...", end='\r')
            self._analyze_file(py_file)

        if verbose:
            print()  # New line after progress

        return self._create_result()

    def _find_python_files(self) -> List[Path]:
        """Find all Python files, excluding patterns."""
        files = []
        for py_file in self.project_root.rglob('*.py'):
            # Check if file should be excluded
            if any(pattern in str(py_file) for pattern in self.exclude_patterns):
                continue
            files.append(py_file)
        return sorted(files)

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            relative_path = str(file_path.relative_to(self.project_root))

            module_info = {
                'name': file_path.stem,
                'file': relative_path,
                'docstring': ast.get_docstring(tree),
                'classes': [],
                'functions': [],
                'imports': [],
                'lines': len(source.splitlines())
            }

            # Analyze AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._extract_class(node, relative_path)
                    module_info['classes'].append(class_info['name'])
                    self.all_classes.append(class_info)

                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    func_info = self._extract_function(node, relative_path)
                    module_info['functions'].append(func_info['name'])
                    self.all_functions.append(func_info)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports = self._extract_imports(node)
                    module_info['imports'].extend(imports)
                    for imp in imports:
                        self.dependencies[relative_path].add(imp)

            self.modules.append(module_info)

        except SyntaxError as e:
            print(f"⚠️  Syntax error in {file_path}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}", file=sys.stderr)

    def _extract_class(self, node: ast.ClassDef, file_path: str) -> Dict:
        """Extract class information."""
        methods = []
        properties = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                # Check decorators safely
                decorators = item.decorator_list if hasattr(item, 'decorator_list') else []
                is_property = any(
                    isinstance(d, ast.Name) and d.id == 'property'
                    for d in decorators
                )
                if is_property:
                    properties.append(item.name)
                else:
                    methods.append(item.name)

        return {
            'name': node.name,
            'file': file_path,
            'line': node.lineno,
            'docstring': ast.get_docstring(node),
            'bases': [self._get_name(base) for base in node.bases],
            'methods': methods,
            'properties': properties
        }

    def _extract_function(self, node: ast.FunctionDef, file_path: str) -> Dict:
        """Extract function information."""
        try:
            from .calculator import calculate_complexity
        except ImportError:
            from calculator import calculate_complexity

        complexity = calculate_complexity(node)

        # Extract parameter details
        parameters = []
        for arg in node.args.args:
            param_info = {'name': arg.arg}
            if hasattr(arg, 'annotation') and arg.annotation:
                param_info['type'] = ast.unparse(arg.annotation)
            parameters.append(param_info)

        # Extract decorators safely
        decorators = []
        if hasattr(node, 'decorator_list'):
            decorators = [ast.unparse(d) for d in node.decorator_list]

        return {
            'name': node.name,
            'file': file_path,
            'line': node.lineno,
            'docstring': ast.get_docstring(node),
            'parameters': parameters,
            'return_type': ast.unparse(node.returns) if node.returns else None,
            'decorators': decorators,
            'complexity': complexity,
            'is_async': isinstance(node, ast.AsyncFunctionDef)
        }

    def _extract_imports(self, node) -> List[str]:
        """Extract import statements."""
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

    def _create_result(self) -> Dict[str, Any]:
        """Create the final result dictionary."""
        return {
            'modules': self.modules,
            'classes': self.all_classes,
            'functions': self.all_functions,
            'dependencies': {k: list(v) for k, v in self.dependencies.items()}
        }
