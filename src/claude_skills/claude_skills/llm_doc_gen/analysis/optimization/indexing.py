"""Symbol indexing for fast lookup of functions, classes, and methods.

This module provides hash-based indexing for quick symbol resolution without
scanning the entire codebase. Used for incremental parsing and documentation
generation.
"""

from typing import Dict, List, Tuple, Set, Optional
from pathlib import Path
from collections import defaultdict


class ImportIndex:
    """Fast lookup index for module imports and dependencies.

    Maintains bidirectional mappings for import relationships, enabling quick
    resolution of module dependencies and reverse dependencies.

    Attributes:
        imports: Maps each module to the set of modules it imports
        imported_by: Reverse index mapping each module to modules that import it
        module_to_file: Maps module names to their file paths

    Example:
        >>> index = ImportIndex()
        >>> index.add_import("app.main", "app.config", "/app/main.py", "/app/config.py")
        >>> index.add_import("app.main", "app.utils", "/app/main.py", "/app/utils.py")
        >>>
        >>> imports = index.get_imports("app.main")
        >>> # Returns {"app.config", "app.utils"}
        >>>
        >>> importers = index.get_imported_by("app.config")
        >>> # Returns {"app.main"}
    """

    def __init__(self):
        """Initialize empty import index."""
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.imported_by: Dict[str, Set[str]] = defaultdict(set)
        self.module_to_file: Dict[str, str] = {}

    def add_import(
        self,
        source_module: str,
        imported_module: str,
        source_file: str,
        imported_file: Optional[str] = None
    ) -> None:
        """Add an import relationship to the index.

        Args:
            source_module: Name of the module doing the importing
            imported_module: Name of the module being imported
            source_file: Path to the source module's file
            imported_file: Path to the imported module's file (optional)
        """
        # Add to imports mapping
        self.imports[source_module].add(imported_module)

        # Add to reverse mapping
        self.imported_by[imported_module].add(source_module)

        # Update module-to-file mappings
        self.module_to_file[source_module] = source_file
        if imported_file is not None:
            self.module_to_file[imported_module] = imported_file

    def get_imports(self, module: str) -> Set[str]:
        """Get all modules imported by a given module.

        Args:
            module: Module name

        Returns:
            Set of module names that this module imports (empty if none)
        """
        return self.imports.get(module, set())

    def get_imported_by(self, module: str) -> Set[str]:
        """Get all modules that import a given module.

        Args:
            module: Module name

        Returns:
            Set of module names that import this module (empty if none)
        """
        return self.imported_by.get(module, set())

    def get_file_path(self, module: str) -> Optional[str]:
        """Get the file path for a module.

        Args:
            module: Module name

        Returns:
            File path for the module, or None if not found
        """
        return self.module_to_file.get(module)

    def get_all_modules(self) -> Set[str]:
        """Get set of all indexed module names.

        Returns:
            Set of all module names in the index
        """
        all_modules = set(self.imports.keys())
        all_modules.update(self.imported_by.keys())
        all_modules.update(self.module_to_file.keys())
        return all_modules

    def remove_module(self, module: str) -> None:
        """Remove a module and all its import relationships.

        Args:
            module: Module name to remove
        """
        # Remove from imports (this module imports others)
        if module in self.imports:
            for imported in self.imports[module]:
                # Remove from reverse mapping
                if module in self.imported_by[imported]:
                    self.imported_by[imported].remove(module)
                    if not self.imported_by[imported]:
                        del self.imported_by[imported]
            del self.imports[module]

        # Remove from imported_by (other modules import this one)
        if module in self.imported_by:
            for importer in self.imported_by[module]:
                # Remove from forward mapping
                if module in self.imports[importer]:
                    self.imports[importer].remove(module)
                    if not self.imports[importer]:
                        del self.imports[importer]
            del self.imported_by[module]

        # Remove from module-to-file mapping
        if module in self.module_to_file:
            del self.module_to_file[module]

    def remove_file(self, file_path: str) -> None:
        """Remove all modules from a specific file.

        Args:
            file_path: Path to file whose modules should be removed
        """
        # Find all modules in this file
        modules_to_remove = [
            module for module, path in self.module_to_file.items()
            if path == file_path
        ]

        # Remove each module
        for module in modules_to_remove:
            self.remove_module(module)

    def get_transitive_imports(self, module: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """Get all modules transitively imported by a module.

        Recursively follows import chains to find all dependencies.

        Args:
            module: Module name
            visited: Set of already visited modules (used for cycle detection)

        Returns:
            Set of all modules transitively imported
        """
        if visited is None:
            visited = set()

        if module in visited:
            return set()

        visited.add(module)
        result = set(self.imports.get(module, set()))

        for imported in list(result):
            result.update(self.get_transitive_imports(imported, visited))

        return result

    def get_transitive_importers(self, module: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """Get all modules that transitively import a module.

        Recursively follows reverse import chains.

        Args:
            module: Module name
            visited: Set of already visited modules (used for cycle detection)

        Returns:
            Set of all modules that transitively import this module
        """
        if visited is None:
            visited = set()

        if module in visited:
            return set()

        visited.add(module)
        result = set(self.imported_by.get(module, set()))

        for importer in list(result):
            result.update(self.get_transitive_importers(importer, visited))

        return result

    def has_circular_dependency(self, module: str) -> bool:
        """Check if a module is part of a circular import.

        Args:
            module: Module name to check

        Returns:
            True if module is part of a circular dependency
        """
        def has_cycle(current: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(current)
            rec_stack.add(current)

            for imported in self.imports.get(current, set()):
                if imported not in visited:
                    if has_cycle(imported, visited, rec_stack):
                        return True
                elif imported in rec_stack:
                    return True

            rec_stack.remove(current)
            return False

        return has_cycle(module, set(), set())

    def clear(self) -> None:
        """Clear all indexed imports."""
        self.imports.clear()
        self.imported_by.clear()
        self.module_to_file.clear()

    def __len__(self) -> int:
        """Get total number of indexed modules.

        Returns:
            Total count of unique modules
        """
        return len(self.get_all_modules())

    def __repr__(self) -> str:
        """Get string representation of index."""
        return f"ImportIndex(modules={len(self)})"


class SymbolLocation:
    """Represents a symbol's location in the codebase.

    Attributes:
        name: Symbol name (function, class, or method)
        file_path: Path to file where symbol is defined
        symbol_type: Type of symbol ('function', 'class', or 'method')
        class_name: For methods, the class name; None for functions/classes
    """

    def __init__(self, name: str, file_path: str, symbol_type: str, class_name: Optional[str] = None):
        """Initialize symbol location.

        Args:
            name: Symbol name
            file_path: Path to file where symbol is defined
            symbol_type: Type of symbol ('function', 'class', or 'method')
            class_name: For methods, the class name; None for functions/classes
        """
        self.name = name
        self.file_path = file_path
        self.symbol_type = symbol_type
        self.class_name = class_name

    def __repr__(self) -> str:
        """Get string representation."""
        if self.symbol_type == 'method':
            return f"SymbolLocation({self.class_name}.{self.name}@{self.file_path})"
        return f"SymbolLocation({self.name}@{self.file_path})"

    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, SymbolLocation):
            return False
        return (self.name == other.name and
                self.file_path == other.file_path and
                self.symbol_type == other.symbol_type and
                self.class_name == other.class_name)

    def __hash__(self):
        """Get hash."""
        return hash((self.name, self.file_path, self.symbol_type, self.class_name))


class SymbolIndex:
    """Fast hash-based lookup index for code symbols.

    Maintains mappings from symbol names to their locations in the codebase,
    enabling O(1) lookups for functions, classes, and methods.

    Attributes:
        function_map: Maps function names to list of file paths where they're defined
        class_map: Maps class names to list of file paths where they're defined
        method_map: Maps method names to list of (class_name, file_path) tuples
        functions: Public read-only access to function symbols
        classes: Public read-only access to class symbols

    Example:
        >>> index = SymbolIndex()
        >>> index.add_function("parse_file", "/src/parser.py")
        >>> index.add_class("Parser", "/src/parser.py")
        >>> index.add_method("parse", "Parser", "/src/parser.py")
        >>>
        >>> files = index.find_function("parse_file")
        >>> # Returns ["/src/parser.py"]
        >>>
        >>> locations = index.find_method("parse")
        >>> # Returns [("Parser", "/src/parser.py")]
        >>>
        >>> locs = index.lookup_function("parse_file")
        >>> # Returns [SymbolLocation("parse_file", "/src/parser.py", "function")]
    """

    def __init__(self):
        """Initialize empty symbol index."""
        self.function_map: Dict[str, List[str]] = defaultdict(list)
        self.class_map: Dict[str, List[str]] = defaultdict(list)
        self.method_map: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

    def add_function(self, name: str, file_path: str) -> None:
        """Add a function to the index.

        Args:
            name: Function name
            file_path: Path to file where function is defined
        """
        if file_path not in self.function_map[name]:
            self.function_map[name].append(file_path)

    def add_class(self, name: str, file_path: str) -> None:
        """Add a class to the index.

        Args:
            name: Class name
            file_path: Path to file where class is defined
        """
        if file_path not in self.class_map[name]:
            self.class_map[name].append(file_path)

    def add_method(self, name: str, class_name: str, file_path: str) -> None:
        """Add a method to the index.

        Args:
            name: Method name
            class_name: Name of the class containing this method
            file_path: Path to file where method is defined
        """
        location = (class_name, file_path)
        if location not in self.method_map[name]:
            self.method_map[name].append(location)

    def find_function(self, name: str) -> List[str]:
        """Find all files where a function is defined.

        Args:
            name: Function name to search for

        Returns:
            List of file paths where function is defined (empty if not found)
        """
        return self.function_map.get(name, [])

    def find_class(self, name: str) -> List[str]:
        """Find all files where a class is defined.

        Args:
            name: Class name to search for

        Returns:
            List of file paths where class is defined (empty if not found)
        """
        return self.class_map.get(name, [])

    def find_method(self, name: str) -> List[Tuple[str, str]]:
        """Find all locations where a method is defined.

        Args:
            name: Method name to search for

        Returns:
            List of (class_name, file_path) tuples (empty if not found)
        """
        return self.method_map.get(name, [])

    def lookup_function(self, name: str) -> List['SymbolLocation']:
        """Find all locations where a function is defined (returns SymbolLocation objects).

        Args:
            name: Function name to search for

        Returns:
            List of SymbolLocation objects (empty if not found)
        """
        files = self.function_map.get(name, [])
        return [SymbolLocation(name, file_path, 'function') for file_path in files]

    def lookup_class(self, name: str) -> List['SymbolLocation']:
        """Find all locations where a class is defined (returns SymbolLocation objects).

        Args:
            name: Class name to search for

        Returns:
            List of SymbolLocation objects (empty if not found)
        """
        files = self.class_map.get(name, [])
        return [SymbolLocation(name, file_path, 'class') for file_path in files]

    def lookup_method(self, name: str) -> List['SymbolLocation']:
        """Find all locations where a method is defined (returns SymbolLocation objects).

        Args:
            name: Method name to search for

        Returns:
            List of SymbolLocation objects (empty if not found)
        """
        locations = self.method_map.get(name, [])
        return [SymbolLocation(name, file_path, 'method', class_name)
                for class_name, file_path in locations]

    @property
    def functions(self) -> Dict[str, List[str]]:
        """Public read-only access to function symbol index."""
        return dict(self.function_map)

    @property
    def classes(self) -> Dict[str, List[str]]:
        """Public read-only access to class symbol index."""
        return dict(self.class_map)

    def get_all_functions(self) -> Set[str]:
        """Get set of all indexed function names.

        Returns:
            Set of all function names in the index
        """
        return set(self.function_map.keys())

    def get_all_classes(self) -> Set[str]:
        """Get set of all indexed class names.

        Returns:
            Set of all class names in the index
        """
        return set(self.class_map.keys())

    def get_all_methods(self) -> Set[str]:
        """Get set of all indexed method names.

        Returns:
            Set of all method names in the index
        """
        return set(self.method_map.keys())

    def remove_file(self, file_path: str) -> None:
        """Remove all symbols from a specific file.

        Useful for incremental updates when a file is deleted or needs
        to be re-indexed.

        Args:
            file_path: Path to file whose symbols should be removed
        """
        # Remove from function_map
        for name in list(self.function_map.keys()):
            self.function_map[name] = [
                path for path in self.function_map[name]
                if path != file_path
            ]
            if not self.function_map[name]:
                del self.function_map[name]

        # Remove from class_map
        for name in list(self.class_map.keys()):
            self.class_map[name] = [
                path for path in self.class_map[name]
                if path != file_path
            ]
            if not self.class_map[name]:
                del self.class_map[name]

        # Remove from method_map
        for name in list(self.method_map.keys()):
            self.method_map[name] = [
                (cls, path) for cls, path in self.method_map[name]
                if path != file_path
            ]
            if not self.method_map[name]:
                del self.method_map[name]

    def clear(self) -> None:
        """Clear all indexed symbols."""
        self.function_map.clear()
        self.class_map.clear()
        self.method_map.clear()

    def get_file_symbols(self, file_path: str) -> Dict[str, List[str]]:
        """Get all symbols defined in a specific file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with keys 'functions', 'classes', 'methods' containing
            lists of symbol names defined in that file
        """
        result = {
            'functions': [],
            'classes': [],
            'methods': []
        }

        # Find functions in this file
        for name, paths in self.function_map.items():
            if file_path in paths:
                result['functions'].append(name)

        # Find classes in this file
        for name, paths in self.class_map.items():
            if file_path in paths:
                result['classes'].append(name)

        # Find methods in this file
        for name, locations in self.method_map.items():
            for cls, path in locations:
                if path == file_path:
                    result['methods'].append(f"{cls}.{name}")
                    break

        return result

    def __len__(self) -> int:
        """Get total number of indexed symbols.

        Returns:
            Total count of unique symbols (functions + classes + methods)
        """
        return (len(self.function_map) +
                len(self.class_map) +
                len(self.method_map))

    def __repr__(self) -> str:
        """Get string representation of index."""
        return (f"SymbolIndex("
                f"functions={len(self.function_map)}, "
                f"classes={len(self.class_map)}, "
                f"methods={len(self.method_map)})")


class FastResolver:
    """Fast symbol resolution using pre-built indexes.

    Provides O(1) lookups for function calls and class instantiations by
    leveraging SymbolIndex and ImportIndex instead of scanning through
    all modules with nested loops.

    Attributes:
        symbol_index: Index of functions, classes, and methods
        import_index: Index of module imports and dependencies

    Example:
        >>> symbol_idx = SymbolIndex()
        >>> import_idx = ImportIndex()
        >>> resolver = FastResolver(symbol_idx, import_idx)
        >>>
        >>> # Resolve a function call
        >>> locations = resolver.resolve_call("parse_file", "app.main")
        >>> # Returns list of (file_path, symbol_type) tuples
        >>>
        >>> # Resolve a class instantiation
        >>> locations = resolver.resolve_instantiation("Parser", "app.main")
        >>> # Returns list of (file_path, class_name) tuples
    """

    def __init__(self, symbol_index: SymbolIndex, import_index: ImportIndex):
        """Initialize resolver with indexes.

        Args:
            symbol_index: Pre-built symbol index
            import_index: Pre-built import index
        """
        self.symbol_index = symbol_index
        self.import_index = import_index

    def resolve_call(
        self,
        name: str,
        calling_module: str
    ) -> List[Tuple[str, str]]:
        """Resolve a function or method call to its definition locations.

        Uses index lookups (O(1)) instead of scanning all modules (O(n)).

        Args:
            name: Name of the function or method being called
            calling_module: Module where the call is made

        Returns:
            List of (file_path, symbol_type) tuples where symbol_type is
            'function' or 'method'. Empty list if not found.

        Example:
            >>> locations = resolver.resolve_call("parse_file", "app.main")
            >>> # Returns [("/app/parser.py", "function")]
        """
        results = []

        # Get calling module's file
        calling_file = self.import_index.get_file_path(calling_module)

        # Get imported modules
        imported_modules = self.import_index.get_imports(calling_module)

        # Check if it's a function (can be in current or imported modules)
        functions_in_any_file = self.symbol_index.find_function(name)
        for file_path in functions_in_any_file:
            # Function is available if:
            # 1. It's in the current module, OR
            # 2. Its module is imported
            if file_path == calling_file:
                # Function in same file
                results.append((file_path, "function"))
            else:
                # Check if this file's module is imported
                for module, mod_file in self.import_index.module_to_file.items():
                    if mod_file == file_path and module in imported_modules:
                        results.append((file_path, "function"))
                        break

        # Check if it's a method
        method_locations = self.symbol_index.find_method(name)
        for class_name, file_path in method_locations:
            # Method is available if:
            # 1. It's in the current module, OR
            # 2. Its class is imported
            if file_path == calling_file:
                results.append((file_path, "method"))
            else:
                # Check if the class is imported
                for module, mod_file in self.import_index.module_to_file.items():
                    if mod_file == file_path and module in imported_modules:
                        results.append((file_path, "method"))
                        break

        return results

    def resolve_instantiation(
        self,
        class_name: str,
        calling_module: str
    ) -> List[Tuple[str, str]]:
        """Resolve a class instantiation to its definition location.

        Uses index lookups (O(1)) instead of scanning all modules (O(n)).

        Args:
            class_name: Name of the class being instantiated
            calling_module: Module where the instantiation occurs

        Returns:
            List of (file_path, class_name) tuples. Empty list if not found.

        Example:
            >>> locations = resolver.resolve_instantiation("Parser", "app.main")
            >>> # Returns [("/app/parser.py", "Parser")]
        """
        results = []

        # Find all locations where this class is defined
        class_files = self.symbol_index.find_class(class_name)

        if not class_files:
            return results

        # Get the calling module's file
        calling_file = self.import_index.get_file_path(calling_module)

        # Get imported modules
        imported_modules = self.import_index.get_imports(calling_module)

        for file_path in class_files:
            # Class is accessible if:
            # 1. It's in the current module, OR
            # 2. Its module is imported

            if file_path == calling_file:
                results.append((file_path, class_name))
            else:
                # Check if this file's module is imported
                for module, mod_file in self.import_index.module_to_file.items():
                    if mod_file == file_path and module in imported_modules:
                        results.append((file_path, class_name))
                        break

        return results

    def resolve_symbol(
        self,
        name: str,
        calling_module: str,
        symbol_type: Optional[str] = None
    ) -> List[Tuple[str, str, str]]:
        """Resolve any symbol (function, class, or method) to its location.

        Args:
            name: Symbol name
            calling_module: Module where symbol is referenced
            symbol_type: Optional type hint ('function', 'class', 'method')

        Returns:
            List of (file_path, symbol_type, context) tuples where context
            is either the symbol name (for functions/classes) or
            "ClassName.method_name" (for methods)
        """
        results = []

        if symbol_type is None or symbol_type == 'function':
            # Try resolving as a function
            call_results = self.resolve_call(name, calling_module)
            for file_path, sym_type in call_results:
                if sym_type == 'function':
                    results.append((file_path, 'function', name))

        if symbol_type is None or symbol_type == 'class':
            # Try resolving as a class
            class_results = self.resolve_instantiation(name, calling_module)
            for file_path, cls_name in class_results:
                results.append((file_path, 'class', cls_name))

        if symbol_type is None or symbol_type == 'method':
            # Try resolving as a method
            call_results = self.resolve_call(name, calling_module)
            for file_path, sym_type in call_results:
                if sym_type == 'method':
                    # Find which class this method belongs to
                    method_locations = self.symbol_index.find_method(name)
                    for cls_name, m_file in method_locations:
                        if m_file == file_path:
                            results.append((file_path, 'method', f"{cls_name}.{name}"))
                            break

        return results

    def get_available_symbols(self, module: str) -> Dict[str, Set[str]]:
        """Get all symbols available in a module's scope.

        Includes symbols defined in the module and symbols from imports.

        Args:
            module: Module name

        Returns:
            Dictionary with keys 'functions', 'classes', 'methods' containing
            sets of available symbol names
        """
        result = {
            'functions': set(),
            'classes': set(),
            'methods': set()
        }

        # Get module's own file
        module_file = self.import_index.get_file_path(module)
        if module_file:
            # Add symbols from the module itself
            file_symbols = self.symbol_index.get_file_symbols(module_file)
            result['functions'].update(file_symbols['functions'])
            result['classes'].update(file_symbols['classes'])
            # Extract method names from "ClassName.method_name" format
            for method_ref in file_symbols['methods']:
                if '.' in method_ref:
                    method_name = method_ref.split('.', 1)[1]
                    result['methods'].add(method_name)

        # Add symbols from imported modules
        imported_modules = self.import_index.get_imports(module)
        for imported_module in imported_modules:
            imported_file = self.import_index.get_file_path(imported_module)
            if imported_file:
                file_symbols = self.symbol_index.get_file_symbols(imported_file)
                result['functions'].update(file_symbols['functions'])
                result['classes'].update(file_symbols['classes'])
                for method_ref in file_symbols['methods']:
                    if '.' in method_ref:
                        method_name = method_ref.split('.', 1)[1]
                        result['methods'].add(method_name)

        return result

    def __repr__(self) -> str:
        """Get string representation of resolver."""
        return (f"FastResolver("
                f"symbols={len(self.symbol_index)}, "
                f"modules={len(self.import_index)})")
