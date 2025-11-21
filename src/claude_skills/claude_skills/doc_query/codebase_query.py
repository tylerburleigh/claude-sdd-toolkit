#!/usr/bin/env python3
"""
CodebaseQuery: LLM-friendly interface for querying codebase analysis.

This module extends DocumentationQuery to provide formatted responses
specifically designed for inclusion in LLM prompts during documentation
generation.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from .doc_query_lib import DocumentationQuery, QueryResult


class CodebaseQuery:
    """
    Query interface for codebase analysis with LLM-formatted responses.

    Wraps DocumentationQuery to provide formatted strings suitable for
    inclusion in AI documentation generation prompts.

    Features:
    - Auto-detects codebase.json in docs/ directory
    - Returns formatted text responses for LLM prompts
    - Supports complexity queries, call graphs, and instantiation queries

    Example:
        >>> query = CodebaseQuery()
        >>> result = query.get_complex_functions_in_module("src/main.py", top_n=5)
        >>> print(result)  # Formatted string ready for LLM prompt
    """

    def __init__(self, docs_path: Optional[str] = None):
        """
        Initialize codebase query interface.

        Args:
            docs_path: Path to codebase.json or its directory.
                      If None, auto-detects in common locations.
        """
        self.query = DocumentationQuery(docs_path)
        self._loaded = False

    def load(self) -> bool:
        """
        Load the codebase analysis data.

        Returns:
            True if successful, False otherwise
        """
        self._loaded = self.query.load()
        return self._loaded

    def _ensure_loaded(self):
        """Ensure documentation is loaded."""
        if not self._loaded:
            if not self.load():
                raise RuntimeError(
                    f"Codebase analysis not found at {self.query.docs_path}. "
                    "Run `sdd doc generate` to create it."
                )

    def get_complex_functions_in_module(
        self,
        module: str,
        top_n: int = 10,
        threshold: int = 5
    ) -> str:
        """
        Get N most complex functions in a module, formatted for LLM prompts.

        Args:
            module: Module file path (e.g., "src/main.py")
            top_n: Number of functions to return (default: 10)
            threshold: Minimum complexity threshold (default: 5)

        Returns:
            Formatted string suitable for LLM prompts

        Example:
            >>> query.get_complex_functions_in_module("src/processor.py", top_n=5)
            '''
            **Most Complex Functions in src/processor.py:**

            1. process_data (complexity: 15)
               File: src/processor.py:42
               Purpose: Main data processing pipeline

            2. validate_input (complexity: 12)
               File: src/processor.py:89
               Purpose: Input validation with multiple checks
            '''
        """
        self._ensure_loaded()

        # Get high complexity functions filtered by module
        results = self.query.get_high_complexity(threshold=threshold, module=module)

        if not results:
            return f"No complex functions found in {module} (threshold: {threshold})"

        # Limit to top N
        results = results[:top_n]

        # Format for LLM
        lines = [f"**Most Complex Functions in {module}:**", ""]

        for i, result in enumerate(results, 1):
            func = result.data
            complexity = func.get('complexity', 0)
            file_path = func.get('file', '')
            line = func.get('line', '')
            docstring = func.get('docstring', '')

            lines.append(f"{i}. {result.name} (complexity: {complexity})")
            lines.append(f"   File: {file_path}:{line}")

            # Add docstring excerpt if available
            if docstring:
                excerpt = docstring.split('\n')[0].strip()
                if excerpt:
                    lines.append(f"   Purpose: {excerpt}")

            lines.append("")

        return "\n".join(lines)

    def get_function_callers(
        self,
        function_name: str,
        include_context: bool = True
    ) -> str:
        """
        Get functions that call the specified function, formatted for LLM prompts.

        Args:
            function_name: Name of the function to query
            include_context: Include file paths and line numbers (default: True)

        Returns:
            Formatted string suitable for LLM prompts

        Example:
            >>> query.get_function_callers("process_data")
            '''
            **Functions calling process_data:**

            - main (src/main.py:25)
            - handle_request (src/api/routes.py:102)
            - batch_processor (src/batch.py:45)

            Total: 3 callers
            '''
        """
        self._ensure_loaded()

        callers = self.query.get_callers(
            function_name,
            include_file=include_context,
            include_line=include_context
        )

        if not callers:
            return f"No callers found for function: {function_name}"

        # Format for LLM
        lines = [f"**Functions calling {function_name}:**", ""]

        for caller in callers:
            name = caller['name']
            if include_context:
                file_path = caller.get('file', '')
                line = caller.get('line', '')
                lines.append(f"- {name} ({file_path}:{line})")
            else:
                lines.append(f"- {name}")

        lines.append("")
        lines.append(f"Total: {len(callers)} caller{'s' if len(callers) != 1 else ''}")

        return "\n".join(lines)

    def get_instantiated_classes_in_file(
        self,
        file_path: str,
        top_n: Optional[int] = None
    ) -> str:
        """
        Get classes instantiated in the specified file, formatted for LLM prompts.

        Args:
            file_path: Path to the file (e.g., "src/main.py")
            top_n: Limit to top N most instantiated (default: no limit)

        Returns:
            Formatted string suitable for LLM prompts

        Example:
            >>> query.get_instantiated_classes_in_file("src/main.py")
            '''
            **Classes instantiated in src/main.py:**

            1. DataProcessor (25 instantiations)
               Location: src/processor.py:15
               Purpose: Main data processing class

            2. Validator (18 instantiations)
               Location: src/validators.py:8
               Purpose: Input validation
            '''
        """
        self._ensure_loaded()

        # Get all classes
        all_classes = self.query.data.get('classes', [])

        # Filter classes with instantiation data
        instantiated_classes = []
        for cls in all_classes:
            inst_count = cls.get('instantiation_count', 0)
            if inst_count and inst_count > 0:
                instantiated_classes.append(cls)

        if not instantiated_classes:
            return f"No instantiation data available for {file_path}"

        # Sort by instantiation count
        instantiated_classes.sort(
            key=lambda x: x.get('instantiation_count', 0),
            reverse=True
        )

        # Apply top_n limit if specified
        if top_n:
            instantiated_classes = instantiated_classes[:top_n]

        # Format for LLM
        lines = [f"**Classes instantiated in {file_path}:**", ""]

        for i, cls in enumerate(instantiated_classes, 1):
            name = cls.get('name', '')
            count = cls.get('instantiation_count', 0)
            cls_file = cls.get('file', '')
            cls_line = cls.get('line', '')
            docstring = cls.get('docstring', '')

            lines.append(f"{i}. {name} ({count} instantiation{'s' if count != 1 else ''})")
            lines.append(f"   Location: {cls_file}:{cls_line}")

            # Add docstring excerpt if available
            if docstring:
                excerpt = docstring.split('\n')[0].strip()
                if excerpt:
                    lines.append(f"   Purpose: {excerpt}")

            lines.append("")

        return "\n".join(lines)

    def get_module_summary(
        self,
        module_path: str,
        include_complexity: bool = True,
        include_dependencies: bool = True
    ) -> str:
        """
        Get comprehensive module summary formatted for LLM prompts.

        Args:
            module_path: Path to the module
            include_complexity: Include complexity metrics (default: True)
            include_dependencies: Include dependency info (default: True)

        Returns:
            Formatted string suitable for LLM prompts
        """
        self._ensure_loaded()

        module_info = self.query.describe_module(
            module_path,
            top_functions=10,
            include_docstrings=True,
            include_dependencies=include_dependencies
        )

        if not module_info:
            return f"Module not found: {module_path}"

        # Format for LLM
        lines = [f"**Module: {module_info.get('name', module_path)}**", ""]

        # Module docstring
        docstring_excerpt = module_info.get('docstring_excerpt', '')
        if docstring_excerpt:
            lines.append(f"*{docstring_excerpt}*")
            lines.append("")

        # Statistics
        stats = module_info.get('statistics', {})
        lines.append("**Statistics:**")
        lines.append(f"- Classes: {stats.get('class_count', 0)}")
        lines.append(f"- Functions: {stats.get('function_count', 0)}")

        if include_complexity:
            lines.append(f"- Avg Complexity: {stats.get('avg_complexity', 0)}")
            lines.append(f"- Max Complexity: {stats.get('max_complexity', 0)}")
            lines.append(f"- High Complexity Functions: {stats.get('high_complexity_count', 0)}")

        if include_dependencies:
            dep_count = stats.get('dependency_count', 0)
            reverse_dep_count = stats.get('reverse_dependency_count', 0)
            lines.append(f"- Dependencies: {dep_count}")
            lines.append(f"- Reverse Dependencies: {reverse_dep_count}")

        lines.append("")

        # Top complex functions
        functions = module_info.get('functions', [])
        if functions and include_complexity:
            lines.append("**Top Complex Functions:**")
            for func in functions[:5]:  # Top 5
                name = func.get('name', '')
                complexity = func.get('complexity', 0)
                excerpt = func.get('docstring_excerpt', '')
                lines.append(f"- {name} (complexity: {complexity})")
                if excerpt:
                    lines.append(f"  {excerpt}")
            lines.append("")

        return "\n".join(lines)

    def get_call_graph_summary(
        self,
        function_name: str,
        direction: str = "both",
        max_depth: int = 2
    ) -> str:
        """
        Get call graph summary formatted for LLM prompts.

        Args:
            function_name: Starting function for the graph
            direction: Direction to traverse ("callers", "callees", or "both")
            max_depth: Maximum recursion depth (default: 2)

        Returns:
            Formatted string suitable for LLM prompts
        """
        self._ensure_loaded()

        graph = self.query.build_call_graph(
            function_name,
            direction=direction,
            max_depth=max_depth,
            include_metadata=True
        )

        if not graph['nodes']:
            return f"Function not found: {function_name}"

        # Format for LLM
        lines = [f"**Call Graph for {function_name}:**", ""]
        lines.append(f"Direction: {direction}")
        lines.append(f"Max Depth: {max_depth}")
        lines.append(f"Total Nodes: {len(graph['nodes'])}")
        lines.append(f"Total Edges: {len(graph['edges'])}")

        if graph['truncated']:
            lines.append("*Note: Graph truncated at max depth*")

        lines.append("")

        # Group edges by direction
        if direction in ["callers", "both"]:
            callers = [e for e in graph['edges'] if e['to'] == function_name]
            if callers:
                lines.append("**Callers (who calls this):**")
                for edge in callers:
                    lines.append(f"- {edge['from']} → {function_name}")
                lines.append("")

        if direction in ["callees", "both"]:
            callees = [e for e in graph['edges'] if e['from'] == function_name]
            if callees:
                lines.append("**Callees (what this calls):**")
                for edge in callees:
                    lines.append(f"- {function_name} → {edge['to']}")
                lines.append("")

        return "\n".join(lines)

    def format_for_prompt(
        self,
        query_type: str,
        **kwargs
    ) -> str:
        """
        Generic method to execute a query and format for LLM prompts.

        Args:
            query_type: Type of query to execute
                - "complex_functions": Get complex functions in module
                - "callers": Get function callers
                - "instantiated_classes": Get instantiated classes
                - "module_summary": Get module summary
                - "call_graph": Get call graph
            **kwargs: Arguments specific to the query type

        Returns:
            Formatted string suitable for LLM prompts

        Raises:
            ValueError: If query_type is not recognized
        """
        query_methods = {
            "complex_functions": self.get_complex_functions_in_module,
            "callers": self.get_function_callers,
            "instantiated_classes": self.get_instantiated_classes_in_file,
            "module_summary": self.get_module_summary,
            "call_graph": self.get_call_graph_summary
        }

        if query_type not in query_methods:
            raise ValueError(
                f"Unknown query type: {query_type}. "
                f"Available: {', '.join(query_methods.keys())}"
            )

        method = query_methods[query_type]
        return method(**kwargs)


def create_codebase_query(docs_path: Optional[str] = None) -> CodebaseQuery:
    """
    Convenience function to create and load a CodebaseQuery instance.

    Args:
        docs_path: Path to codebase.json or its directory

    Returns:
        Loaded CodebaseQuery instance
    """
    query = CodebaseQuery(docs_path)
    query.load()
    return query
