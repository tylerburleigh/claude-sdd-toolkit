"""
Cross-reference tracking for AST analysis.

This module provides utilities for tracking caller/callee relationships,
class instantiations, and building bidirectional reference graphs during
AST traversal across multiple programming languages.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple
from enum import Enum

from .optimization.indexing import SymbolIndex, ImportIndex


class ReferenceType(Enum):
    """Types of cross-references that can be tracked."""
    FUNCTION_CALL = "function_call"
    METHOD_CALL = "method_call"
    CLASS_INSTANTIATION = "class_instantiation"
    IMPORT = "import"
    INHERITANCE = "inheritance"


class DynamicPattern(Enum):
    """Dynamic patterns that may affect cross-reference accuracy."""
    DECORATOR = "decorator"
    MONKEY_PATCH = "monkey_patch"
    REFLECTION = "reflection"
    DYNAMIC_IMPORT = "dynamic_import"
    EVAL_EXEC = "eval_exec"
    GETATTR_SETATTR = "getattr_setattr"


@dataclass(slots=True)
class CallSite:
    """Represents a location where a function/method is called."""
    caller: str  # Name of the calling function/method
    caller_file: str  # File containing the caller
    caller_line: int  # Line number of the call
    callee: str  # Name of the called function/method
    callee_file: Optional[str] = None  # File containing the callee (if known)
    call_type: ReferenceType = ReferenceType.FUNCTION_CALL
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InstantiationSite:
    """Represents a location where a class is instantiated."""
    class_name: str  # Name of the instantiated class
    instantiator: str  # Name of the function/method doing the instantiation
    instantiator_file: str  # File containing the instantiator
    instantiator_line: int  # Line number of instantiation
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DynamicPatternWarning:
    """Warning about a dynamic pattern that may affect accuracy."""
    pattern_type: DynamicPattern
    location: str  # Function/class/module where pattern was found
    file: str
    line: int
    description: str
    impact: str  # Description of how this affects cross-reference accuracy


class CrossReferenceGraph:
    """
    Bidirectional graph tracking caller/callee relationships and
    class instantiations across the codebase.
    """

    def __init__(self):
        """Initialize empty cross-reference graph."""
        # Function call tracking
        self.calls: List[CallSite] = []  # All call sites
        self.callers: Dict[str, List[CallSite]] = {}  # callee -> call sites
        self.callees: Dict[str, List[CallSite]] = {}  # caller -> call sites

        # Class instantiation tracking
        self.instantiations: List[InstantiationSite] = []  # All instantiation sites
        self.instantiated_by: Dict[str, List[InstantiationSite]] = {}  # class -> instantiation sites
        self.instantiators: Dict[str, List[InstantiationSite]] = {}  # function -> instantiations it performs

        # Import tracking (for reverse dependencies)
        self.imports: Dict[str, Set[str]] = {}  # file -> set of imported modules
        self.imported_by: Dict[str, Set[str]] = {}  # module -> set of files that import it

        # Dynamic pattern warnings
        self.warnings: List[DynamicPatternWarning] = []

        # Statistics
        self.stats = {
            'total_calls': 0,
            'total_instantiations': 0,
            'total_warnings': 0,
            'dynamic_patterns': {},  # pattern_type -> count
        }

    def add_call(self, call_site: CallSite) -> None:
        """
        Add a function/method call to the graph.

        Args:
            call_site: CallSite object describing the call
        """
        self.calls.append(call_site)

        # Add to callers index (reverse lookup: who calls this function?)
        if call_site.callee not in self.callers:
            self.callers[call_site.callee] = []
        self.callers[call_site.callee].append(call_site)

        # Add to callees index (forward lookup: what does this function call?)
        caller_key = f"{call_site.caller_file}:{call_site.caller}"
        if caller_key not in self.callees:
            self.callees[caller_key] = []
        self.callees[caller_key].append(call_site)

        self.stats['total_calls'] += 1

    def add_instantiation(self, inst_site: InstantiationSite) -> None:
        """
        Add a class instantiation to the graph.

        Args:
            inst_site: InstantiationSite object describing the instantiation
        """
        self.instantiations.append(inst_site)

        # Add to instantiated_by index (reverse lookup: where is this class instantiated?)
        if inst_site.class_name not in self.instantiated_by:
            self.instantiated_by[inst_site.class_name] = []
        self.instantiated_by[inst_site.class_name].append(inst_site)

        # Add to instantiators index (forward lookup: what classes does this function instantiate?)
        instantiator_key = f"{inst_site.instantiator_file}:{inst_site.instantiator}"
        if instantiator_key not in self.instantiators:
            self.instantiators[instantiator_key] = []
        self.instantiators[instantiator_key].append(inst_site)

        self.stats['total_instantiations'] += 1

    def add_import(self, file: str, imported_module: str) -> None:
        """
        Add an import relationship.

        Args:
            file: File doing the importing
            imported_module: Module being imported
        """
        # Forward lookup: what does this file import?
        if file not in self.imports:
            self.imports[file] = set()
        self.imports[file].add(imported_module)

        # Reverse lookup: what files import this module?
        if imported_module not in self.imported_by:
            self.imported_by[imported_module] = set()
        self.imported_by[imported_module].add(file)

    def add_warning(self, warning: DynamicPatternWarning) -> None:
        """
        Add a warning about a dynamic pattern.

        Args:
            warning: DynamicPatternWarning object
        """
        self.warnings.append(warning)
        self.stats['total_warnings'] += 1

        # Update pattern statistics
        pattern_name = warning.pattern_type.value
        if pattern_name not in self.stats['dynamic_patterns']:
            self.stats['dynamic_patterns'][pattern_name] = 0
        self.stats['dynamic_patterns'][pattern_name] += 1

    def get_callers(self, function_name: str) -> List[CallSite]:
        """
        Get all places that call a given function.

        Args:
            function_name: Name of the function

        Returns:
            List of CallSite objects
        """
        return self.callers.get(function_name, [])

    def get_callees(self, function_name: str, file: Optional[str] = None) -> List[CallSite]:
        """
        Get all functions called by a given function.

        Args:
            function_name: Name of the function
            file: Optional file path for disambiguation

        Returns:
            List of CallSite objects
        """
        if file:
            key = f"{file}:{function_name}"
            return self.callees.get(key, [])

        # Without file, return all matches
        results = []
        for key, call_sites in self.callees.items():
            if key.endswith(f":{function_name}"):
                results.extend(call_sites)
        return results

    def get_instantiation_sites(self, class_name: str) -> List[InstantiationSite]:
        """
        Get all places where a class is instantiated.

        Args:
            class_name: Name of the class

        Returns:
            List of InstantiationSite objects
        """
        return self.instantiated_by.get(class_name, [])

    def get_instantiators(self, function_name: str, file: Optional[str] = None) -> List[InstantiationSite]:
        """
        Get all classes instantiated by a given function.

        Args:
            function_name: Name of the function
            file: Optional file path for disambiguation

        Returns:
            List of InstantiationSite objects
        """
        if file:
            key = f"{file}:{function_name}"
            return self.instantiators.get(key, [])

        # Without file, return all matches
        results = []
        for key, inst_sites in self.instantiators.items():
            if key.endswith(f":{function_name}"):
                results.extend(inst_sites)
        return results

    def get_imported_by(self, module_name: str) -> Set[str]:
        """
        Get all files that import a given module.

        Args:
            module_name: Name of the module

        Returns:
            Set of file paths
        """
        return self.imported_by.get(module_name, set())

    def get_imports(self, file: str) -> Set[str]:
        """
        Get all modules imported by a given file.

        Args:
            file: File path

        Returns:
            Set of imported module names
        """
        return self.imports.get(file, set())

    def build_indexes(self) -> Tuple[SymbolIndex, ImportIndex]:
        """
        Build SymbolIndex and ImportIndex from the cross-reference graph data.

        Constructs optimized hash-based indexes for O(1) symbol resolution
        from the existing call sites, instantiations, and import relationships.

        Returns:
            Tuple of (SymbolIndex, ImportIndex) built from graph data

        Example:
            >>> graph = CrossReferenceGraph()
            >>> # ... populate graph with calls and instantiations ...
            >>> symbol_idx, import_idx = graph.build_indexes()
            >>> # Now use indexes for fast lookups
        """
        symbol_index = SymbolIndex()
        import_index = ImportIndex()

        # Register all files that appear in call sites (even if not imports)
        # This ensures modules are available for resolution
        all_files_seen = set()
        for call_site in self.calls:
            if call_site.caller_file:
                all_files_seen.add(call_site.caller_file)
            if call_site.callee_file:
                all_files_seen.add(call_site.callee_file)

        for inst_site in self.instantiations:
            if inst_site.instantiator_file:
                all_files_seen.add(inst_site.instantiator_file)

        # Register these files in import_index so they can be looked up
        for file_path in all_files_seen:
            module_name = self._file_to_module(file_path)
            if module_name not in import_index.module_to_file:
                import_index.module_to_file[module_name] = file_path

        # Build import index from graph's import data
        for source_file, imported_modules in self.imports.items():
            # Convert file path to module name (simple heuristic)
            source_module = self._file_to_module(source_file)

            for imported_module in imported_modules:
                # Try to find the imported module's file
                imported_file = None
                for file, modules in self.imports.items():
                    if self._file_to_module(file) == imported_module:
                        imported_file = file
                        break

                import_index.add_import(
                    source_module,
                    imported_module,
                    source_file,
                    imported_file
                )

        # Track which symbols we've seen to avoid duplicates
        seen_functions = set()
        seen_classes = set()
        seen_methods = set()

        # Build symbol index from call sites
        for call_site in self.calls:
            # Add caller as a function (if not already added)
            caller_key = (call_site.caller, call_site.caller_file)
            if caller_key not in seen_functions:
                symbol_index.add_function(call_site.caller, call_site.caller_file)
                seen_functions.add(caller_key)

            # Add callee as a function (if we know its file)
            if call_site.callee_file:
                callee_key = (call_site.callee, call_site.callee_file)
                if callee_key not in seen_functions:
                    # Check if it's a method call
                    if call_site.call_type == ReferenceType.METHOD_CALL:
                        # Extract class name from metadata if available
                        class_name = call_site.metadata.get('class_name')
                        if class_name:
                            method_key = (call_site.callee, class_name, call_site.callee_file)
                            if method_key not in seen_methods:
                                symbol_index.add_method(
                                    call_site.callee,
                                    class_name,
                                    call_site.callee_file
                                )
                                seen_methods.add(method_key)
                    else:
                        symbol_index.add_function(
                            call_site.callee,
                            call_site.callee_file
                        )
                        seen_functions.add(callee_key)

        # Build symbol index from instantiation sites
        for inst_site in self.instantiations:
            # Only add class definition if explicitly provided in metadata
            # Don't infer that a class is defined where it's instantiated
            class_file = inst_site.metadata.get('class_file')
            if class_file:
                class_key = (inst_site.class_name, class_file)
                if class_key not in seen_classes:
                    symbol_index.add_class(inst_site.class_name, class_file)
                    seen_classes.add(class_key)

            # Add the instantiator as a function
            instantiator_key = (inst_site.instantiator, inst_site.instantiator_file)
            if instantiator_key not in seen_functions:
                symbol_index.add_function(
                    inst_site.instantiator,
                    inst_site.instantiator_file
                )
                seen_functions.add(instantiator_key)

        return symbol_index, import_index

    def get_callers_indexed(self, function_name: str, symbol_index: SymbolIndex) -> List[CallSite]:
        """
        Get all places that call a given function using indexed lookup.

        Uses SymbolIndex for O(1) resolution of function locations, then
        filters call sites for matches. More efficient than get_callers()
        when working with large codebases and pre-built indexes.

        Args:
            function_name: Name of the function
            symbol_index: SymbolIndex to use for symbol resolution

        Returns:
            List of CallSite objects where this function is called

        Example:
            >>> symbol_idx, _ = graph.build_indexes()
            >>> callers = graph.get_callers_indexed("parse_ast", symbol_idx)
        """
        # Use index to get all known locations of this function
        function_locations = symbol_index.lookup_function(function_name)

        if not function_locations:
            return []

        # Extract file paths from locations
        function_files = {loc.file_path for loc in function_locations}

        # Return all call sites where the callee matches this function
        # Filter by file if we know the function's location
        results = []
        for call_site in self.callers.get(function_name, []):
            # If we know where the function is defined, filter by that
            if call_site.callee_file and call_site.callee_file not in function_files:
                continue
            results.append(call_site)

        return results

    def get_callees_indexed(
        self,
        function_name: str,
        symbol_index: SymbolIndex,
        file: Optional[str] = None
    ) -> List[CallSite]:
        """
        Get all functions called by a given function using indexed lookup.

        Uses SymbolIndex for O(1) resolution of the caller function location,
        then retrieves call sites. More efficient than get_callees() when
        working with large codebases and pre-built indexes.

        Args:
            function_name: Name of the calling function
            symbol_index: SymbolIndex to use for symbol resolution
            file: Optional file path for disambiguation

        Returns:
            List of CallSite objects representing functions called by this function

        Example:
            >>> symbol_idx, _ = graph.build_indexes()
            >>> callees = graph.get_callees_indexed("process_file", symbol_idx)
        """
        # If file provided, use direct lookup
        if file:
            key = f"{file}:{function_name}"
            return self.callees.get(key, [])

        # Use index to find all locations of this function
        function_locations = symbol_index.lookup_function(function_name)

        if not function_locations:
            return []

        # Collect callees from all known locations
        results = []
        for location in function_locations:
            key = f"{location.file_path}:{function_name}"
            results.extend(self.callees.get(key, []))

        return results

    def _file_to_module(self, file_path: str) -> str:
        """
        Convert a file path to a module name.

        Simple heuristic: removes extension and converts slashes to dots.

        Args:
            file_path: File path

        Returns:
            Module name
        """
        # Remove common prefixes and extension
        module = file_path.replace('/', '.').replace('\\', '.')

        # Remove file extension
        if '.' in module:
            parts = module.rsplit('.', 1)
            if parts[1] in ['py', 'js', 'ts', 'go']:
                module = parts[0]

        # Remove leading dots
        module = module.lstrip('.')

        return module

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert graph to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            'calls': [
                {
                    'caller': call.caller,
                    'caller_file': call.caller_file,
                    'caller_line': call.caller_line,
                    'callee': call.callee,
                    'callee_file': call.callee_file,
                    'call_type': call.call_type.value,
                    **call.metadata
                }
                for call in self.calls
            ],
            'instantiations': [
                {
                    'class_name': inst.class_name,
                    'instantiator': inst.instantiator,
                    'instantiator_file': inst.instantiator_file,
                    'instantiator_line': inst.instantiator_line,
                    **inst.metadata
                }
                for inst in self.instantiations
            ],
            'imports': {
                file: list(modules) for file, modules in self.imports.items()
            },
            'warnings': [
                {
                    'pattern_type': w.pattern_type.value,
                    'location': w.location,
                    'file': w.file,
                    'line': w.line,
                    'description': w.description,
                    'impact': w.impact
                }
                for w in self.warnings
            ],
            'statistics': self.stats
        }


def create_cross_reference_graph() -> CrossReferenceGraph:
    """
    Factory function to create a new CrossReferenceGraph.

    Returns:
        New CrossReferenceGraph instance
    """
    return CrossReferenceGraph()
