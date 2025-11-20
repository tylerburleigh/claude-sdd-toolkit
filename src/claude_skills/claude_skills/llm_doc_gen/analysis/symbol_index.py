"""Symbol indexing for fast lookup of functions, classes, and methods.

This module provides hash-based indexing for quick symbol resolution without
scanning the entire codebase. Used for incremental parsing and documentation
generation.
"""

from typing import Dict, List, Tuple, Set, Optional
from pathlib import Path
from collections import defaultdict


class SymbolIndex:
    """Fast hash-based lookup index for code symbols.

    Maintains mappings from symbol names to their locations in the codebase,
    enabling O(1) lookups for functions, classes, and methods.

    Attributes:
        function_map: Maps function names to list of file paths where they're defined
        class_map: Maps class names to list of file paths where they're defined
        method_map: Maps method names to list of (class_name, file_path) tuples

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
