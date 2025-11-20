"""
Documentation generation orchestration module.
Coordinates parsing, analysis, and formatting to generate documentation.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Handle both direct execution and module import
try:
    from .parsers import create_parser_factory, Language, ParseResult
    from .calculator import calculate_statistics
    from .formatter import MarkdownGenerator, JSONGenerator
    from .schema import (
        enhance_function_with_cross_refs,
        enhance_class_with_usage_tracking,
        CallReference,
        InstantiationReference,
        ImportReference,
        SCHEMA_VERSION
    )
    from .ast_analysis import CrossReferenceGraph
    from .optimization.filters import FilterProfile, create_filter_chain
except ImportError:
    from parsers import create_parser_factory, Language, ParseResult
    from calculator import calculate_statistics
    from formatter import MarkdownGenerator, JSONGenerator
    from schema import (
        enhance_function_with_cross_refs,
        enhance_class_with_usage_tracking,
        CallReference,
        InstantiationReference,
        ImportReference,
        SCHEMA_VERSION
    )
    from ast_analysis import CrossReferenceGraph
    from optimization.filters import FilterProfile, create_filter_chain


class DocumentationGenerator:
    """
    Main orchestrator for documentation generation.
    Coordinates all stages: parsing, analysis, calculation, and formatting.
    Supports multiple programming languages.
    """

    def __init__(
        self,
        project_dir: Path,
        project_name: str,
        version: str = "1.0.0",
        exclude_patterns: Optional[list] = None,
        languages: Optional[List[Language]] = None,
        filter_profile: Optional[FilterProfile] = None
    ):
        """
        Initialize the documentation generator.

        Args:
            project_dir: Root directory of the project to document
            project_name: Name of the project
            version: Project version
            exclude_patterns: List of patterns to exclude from analysis
            languages: Specific languages to parse (None = auto-detect all)
            filter_profile: Optional filter profile (FAST, BALANCED, COMPLETE).
                If None, no additional filtering is applied (backward compatible).
                Use FilterProfile.FAST for large codebases, FilterProfile.BALANCED
                for typical projects, or FilterProfile.COMPLETE for comprehensive analysis.
        """
        self.project_dir = project_dir.resolve()
        self.project_name = project_name
        self.version = version
        self.exclude_patterns = exclude_patterns or []
        self.languages = languages
        self.filter_profile = filter_profile

        # Create filter chain if profile is specified
        filter_chain = None
        if filter_profile is not None:
            filter_chain = create_filter_chain(filter_profile)

        # Initialize components
        self.parser_factory = create_parser_factory(
            project_dir,
            self.exclude_patterns,
            languages,
            filter_chain
        )
        self.md_generator = MarkdownGenerator(project_name, version)
        self.json_generator = JSONGenerator(project_name, version)

    def generate(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Generate complete documentation analysis.

        Args:
            verbose: Enable verbose output

        Returns:
            Dictionary containing analysis results and statistics
        """
        # Parse codebase using ParserFactory
        parse_result = self.parser_factory.parse_all(verbose=verbose)

        # Resolve cross-references
        self._resolve_references(parse_result)

        # Convert ParseResult to dictionary format for backward compatibility
        analysis = self._convert_parse_result(parse_result)

        # Calculate statistics
        statistics = calculate_statistics(
            analysis['modules'],
            analysis['functions']
        )

        return {
            'analysis': analysis,
            'statistics': statistics
        }

    def _resolve_references(self, parse_result: ParseResult):
        """
        Resolve unknown file references in the cross-reference graph.
        Uses name matching, context, and imports to resolve call targets.

        Args:
            parse_result: The parse result containing functions, modules, and graph
        """
        import builtins
        
        if not parse_result.cross_references:
            return

        graph = parse_result.cross_references

        # 1. Build lookup maps
        # Function name -> list of files defining it
        function_map = {}
        for func in parse_result.functions:
            if func.name not in function_map:
                function_map[func.name] = []
            function_map[func.name].append(func.file)

        # Class name -> list of files defining it
        class_map = {}
        for cls in parse_result.classes:
            if cls.name not in class_map:
                class_map[cls.name] = []
            class_map[cls.name].append(cls.file)
            
        # Method name -> list of (file, class_name) defining it
        method_map = {}
        for cls in parse_result.classes:
            for method in cls.methods:
                if method not in method_map:
                    method_map[method] = []
                method_map[method].append((cls.file, cls.name))

        # 2. Resolve function calls
        for call in graph.calls:
            if call.callee_file:
                continue

            # Strategy 0: Built-ins
            # Check if it's a Python built-in (e.g., len, str, any)
            if call.callee in dir(builtins):
                call.callee_file = "built-in"
                continue

            # Get candidates (functions or classes/constructors)
            candidates = function_map.get(call.callee, [])
            if not candidates:
                candidates = class_map.get(call.callee, [])

            # Get imports for the caller file
            imports = graph.imports.get(call.caller_file, set())

            if candidates:
                # Strategy A: Exact match
                if len(candidates) == 1:
                    call.callee_file = candidates[0]
                    continue

                # Strategy B: Same file (local call)
                if call.caller_file in candidates:
                    call.callee_file = call.caller_file
                    continue

                # Strategy C: Check imports (enhanced)
                # Check if any candidate file stem matches an imported name
                found_import = False
                for candidate_file in candidates:
                    # Extract simple name from file path (e.g., "utils.py" -> "utils")
                    candidate_name = Path(candidate_file).stem
                    
                    for imp in imports:
                        # Check exact match or suffix (e.g., import utils -> matches utils)
                        if imp == candidate_name or imp.endswith(f".{candidate_name}"):
                            call.callee_file = candidate_file
                            found_import = True
                            break
                        
                        # Check if candidate is a module in the import path
                        # e.g. from utils import func -> imp="utils.func" (matches utils.py)
                        if f".{candidate_name}." in f".{imp}.":
                            call.callee_file = candidate_file
                            found_import = True
                            break
                            
                    if found_import:
                        break
            
            # Strategy D: Method Resolution
            # If it's a method call, check if the method belongs to an imported class
            if not call.callee_file and call.call_type.value == "method_call":
                method_candidates = method_map.get(call.callee, [])
                for candidate_file, candidate_class in method_candidates:
                    # Check if the class defining this method is imported in the caller file
                    for imp in imports:
                        # Match class name (e.g. "PrettyPrinter") against imports
                        # import ...PrettyPrinter or from ... import PrettyPrinter
                        if imp.endswith(f".{candidate_class}") or imp == candidate_class:
                            call.callee_file = candidate_file
                            break
                    if call.callee_file:
                        break
            
            # Strategy E: External Import Resolution
            # If still unresolved, check if it matches an external import
            if not call.callee_file:
                for imp in imports:
                    # Check if callee matches an imported name (alias or suffix)
                    if imp.endswith(f".{call.callee}"):
                        # It's likely an external import (e.g. argparse.ArgumentParser)
                        module = imp.rsplit(".", 1)[0]
                        call.callee_file = f"external://{module}"
                        break
                    elif imp == call.callee:
                        call.callee_file = f"external://{imp}"
                        break
            
            # Strategy F: Built-in Method Resolution (Heuristic)
            # If still unresolved, check if it's a common method of a built-in type
            # (e.g. str.endswith, list.append, file.write)
            if not call.callee_file:
                COMMON_BUILTIN_METHODS = {
                    # String
                    'split', 'strip', 'join', 'replace', 'format', 'startswith', 
                    'endswith', 'lower', 'upper', 'find', 'count', 'encode', 'decode',
                    # List/Set/Dict
                    'append', 'extend', 'pop', 'remove', 'add', 'get', 'items', 
                    'keys', 'values', 'update', 'clear', 'copy', 'sort', 'reverse',
                    # IO / Context Managers
                    'read', 'write', 'close', 'flush', 'open', '__enter__', '__exit__',
                    # Path
                    'exists', 'is_file', 'is_dir', 'resolve', 'glob', 'rglob'
                }
                if call.callee in COMMON_BUILTIN_METHODS:
                    call.callee_file = "built-in"

    def _convert_parse_result(self, result: ParseResult) -> Dict[str, Any]:
        """
        Convert ParseResult to dictionary format with cross-reference enhancement.

        Args:
            result: ParseResult from parser factory

        Returns:
            Dictionary with modules, classes, functions, dependencies, and cross-references
        """
        # Get cross-reference graph if available
        xref_graph: Optional[CrossReferenceGraph] = result.cross_references

        # Enhanced functions with cross-reference data
        enhanced_functions = []
        for func in result.functions:
            if xref_graph:
                # Get callers for this function
                caller_sites = xref_graph.get_callers(func.name)
                callers = [
                    CallReference(
                        name=site.caller,
                        file=site.caller_file,
                        line=site.caller_line,
                        call_type=site.call_type.value
                    )
                    for site in caller_sites
                ]

                # Get calls made by this function
                callee_sites = xref_graph.get_callees(func.name, func.file)
                calls = [
                    CallReference(
                        name=site.callee,
                        file=site.callee_file or "unknown",
                        line=site.caller_line,  # Line where the call is made
                        call_type=site.call_type.value
                    )
                    for site in callee_sites
                ]

                # Use enhancement function to add cross-refs
                enhanced_func = enhance_function_with_cross_refs(
                    func,
                    callers=callers,
                    calls=calls,
                    call_count=len(callers) if callers else None
                )
                enhanced_functions.append(enhanced_func)
            else:
                # No cross-references available, use basic schema
                enhanced_functions.append(func.to_dict())

        # Enhanced classes with usage tracking
        enhanced_classes = []
        for cls in result.classes:
            if xref_graph:
                # Get instantiation sites for this class
                inst_sites = xref_graph.get_instantiation_sites(cls.name)
                instantiated_by = [
                    InstantiationReference(
                        instantiator=site.instantiator,
                        file=site.instantiator_file,
                        line=site.instantiator_line,
                        context=site.metadata.get('context')
                    )
                    for site in inst_sites
                ]

                # Get imports of this class
                # Use class file as module identifier
                imported_by_files = xref_graph.get_imported_by(cls.file)
                imported_by = [
                    ImportReference(
                        importer=importer_file,
                        line=0,  # Line number not available from current tracking
                        import_type="unknown",  # Type not tracked yet
                        alias=None
                    )
                    for importer_file in imported_by_files
                ]

                # Use enhancement function to add usage tracking
                enhanced_cls = enhance_class_with_usage_tracking(
                    cls,
                    instantiated_by=instantiated_by,
                    imported_by=imported_by,
                    instantiation_count=len(instantiated_by) if instantiated_by else None
                )
                enhanced_classes.append(enhanced_cls)
            else:
                # No cross-references available, use basic schema
                enhanced_classes.append(cls.to_dict())

        return {
            'modules': [m.to_dict() for m in result.modules],
            'classes': enhanced_classes,
            'functions': enhanced_functions,
            'dependencies': result.dependencies,
            'errors': result.errors
        }

    def save_markdown(
        self,
        output_path: Path,
        analysis: Dict[str, Any],
        statistics: Dict[str, Any],
        verbose: bool = False
    ):
        """
        Generate and save Markdown documentation.

        Args:
            output_path: Path to save the Markdown file
            analysis: Analyzed codebase data
            statistics: Calculated statistics
            verbose: Enable verbose output
        """
        if verbose:
            print("📝 Generating Markdown documentation...")

        markdown = self.md_generator.generate(analysis, statistics)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        if verbose:
            print(f"✅ Markdown: {output_path}")

    def save_json(
        self,
        output_path: Path,
        analysis: Dict[str, Any],
        statistics: Dict[str, Any],
        verbose: bool = False
    ):
        """
        Generate and save JSON documentation.

        Args:
            output_path: Path to save the JSON file
            analysis: Analyzed codebase data
            statistics: Calculated statistics
            verbose: Enable verbose output
        """
        if verbose:
            print("📋 Generating JSON documentation...")

        json_doc = self.json_generator.generate(analysis, statistics)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_doc, f, indent=2)

        if verbose:
            print(f"✅ JSON: {output_path}")

    def generate_all(
        self,
        output_dir: Path,
        format_type: str = 'both',
        verbose: bool = False
    ) -> None:
        """
        Generate documentation in specified format(s).

        Args:
            output_dir: Directory to save documentation files
            format_type: Output format ('markdown', 'json', or 'both')
            verbose: Enable verbose output
        """
        # Generate analysis
        result = self.generate(verbose=verbose)
        analysis = result['analysis']
        statistics = result['statistics']

        # Save in requested format(s)
        if format_type in ['markdown', 'both']:
            md_path = output_dir / 'DOCUMENTATION.md'
            self.save_markdown(md_path, analysis, statistics, verbose=verbose)

        if format_type in ['json', 'both']:
            json_path = output_dir / 'documentation.json'
            self.save_json(json_path, analysis, statistics, verbose=verbose)

        if verbose:
            print(f"\n🎉 Documentation generation complete!")
            print(f"   Output directory: {output_dir.absolute()}")
