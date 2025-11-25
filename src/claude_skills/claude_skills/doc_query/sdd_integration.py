#!/usr/bin/env python3
"""
SDD (Spec-Driven Development) integration helpers for doc-query.

This module provides functions that SDD tools (sdd-plan, sdd-next, sdd-update)
can use to gather relevant context from codebase documentation.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from .doc_query_lib import DocumentationQuery, QueryResult


class SDDContextGatherer:
    """Helper class for gathering context for SDD tasks."""

    def __init__(self, docs_path: Optional[str] = None):
        """
        Initialize the context gatherer.

        Args:
            docs_path: Path to codebase.json or docs directory
        """
        self.query = DocumentationQuery(docs_path)
        if not self.query.load():
            raise RuntimeError(
                f"Documentation not found at {self.query.docs_path}. "
                "Run `sdd doc generate` first."
            )

    def get_task_context(self, task_description: str) -> Dict[str, any]:
        """
        Smart context gathering based on task description.

        Analyzes the task description and gathers relevant:
        - Classes
        - Functions
        - Modules
        - Dependencies

        Args:
            task_description: Description of the task to implement

        Returns:
            Dict with context organized by entity type
        """
        # Extract keywords from task description
        keywords = self._extract_keywords(task_description)

        stats_payload = self.query.get_stats()
        statistics = stats_payload.get('statistics', {}) if isinstance(stats_payload, dict) else {}
        metadata = stats_payload.get('metadata', {}) if isinstance(stats_payload, dict) else {}

        context = {
            'task_description': task_description,
            'keywords': keywords,
            'relevant_classes': [],
            'relevant_functions': [],
            'relevant_modules': [],
            'dependencies': [],
            'suggested_files': [],
            'module_summaries': [],
            'statistics': statistics,
            'metadata': metadata
        }

        # Search for each keyword
        for keyword in keywords:
            # Try to find relevant entities
            classes = self.query.find_class(keyword, pattern=True)
            functions = self.query.find_function(keyword, pattern=True)
            modules = self.query.find_module(keyword, pattern=True)

            context['relevant_classes'].extend(classes)
            context['relevant_functions'].extend(functions)
            context['relevant_modules'].extend(modules)

        # Deduplicate results
        context['relevant_classes'] = self._deduplicate_results(context['relevant_classes'])
        context['relevant_functions'] = self._deduplicate_results(context['relevant_functions'])
        context['relevant_modules'] = self._deduplicate_results(context['relevant_modules'])

        # Get dependencies for relevant modules
        module_summaries = []
        seen_modules = set()
        for module in context['relevant_modules']:
            module_key = module.data.get('file') or module.name

            summary = self.query.describe_module(
                module_key,
                top_functions=5,
                include_docstrings=False,
                include_dependencies=True
            )

            resolved = summary.get('file', module_key)
            if resolved in seen_modules:
                continue
            seen_modules.add(resolved)

            deps = self.query.get_dependencies(resolved, reverse=False)
            context['dependencies'].extend(deps)
            summary['relevance_score'] = module.relevance_score
            module_summaries.append(summary)

        context['module_summaries'] = sorted(
            module_summaries,
            key=lambda m: (-(m.get('statistics', {}).get('high_complexity_count', 0) or 0),
                           -(m.get('relevance_score', 0) or 0))
        )

        # Build suggested files list
        suggested_files = set()
        for cls in context['relevant_classes']:
            suggested_files.add(cls.data.get('file', ''))
        for func in context['relevant_functions']:
            suggested_files.add(func.data.get('file', ''))
        for summary in module_summaries:
            suggested_files.add(summary.get('file', summary.get('name', '')))

        context['suggested_files'] = sorted(suggested_files)

        return context

    def suggest_files_for_task(self, task_description: str) -> List[str]:
        """
        Suggest relevant files for a task.

        Args:
            task_description: Description of the task

        Returns:
            List of file paths
        """
        context = self.get_task_context(task_description)
        return context['suggested_files']

    def find_similar_implementations(self, feature_name: str) -> List[QueryResult]:
        """
        Find similar existing implementations.

        Useful for finding patterns to follow when implementing new features.

        Args:
            feature_name: Name or pattern of the feature

        Returns:
            List of similar entities
        """
        results = self.query.search_entities(feature_name)
        return results

    def get_test_context(self, module_path: str) -> Dict[str, any]:
        """
        Find test files and functions related to a module.

        Args:
            module_path: Path to the module

        Returns:
            Dict with test context including:
            - module: The module path queried
            - test_files: List of test file paths
            - test_functions: List of test function/method names (strings)
            - test_classes: List of test class names
        """
        context = {
            'module': module_path,
            'test_files': [],
            'test_functions': [],
            'test_classes': [],
        }

        # Look for test files
        # Common patterns: test_*.py, *_test.py, tests/*.py
        module_summary = self.query.describe_module(
            module_path,
            include_docstrings=False,
            include_dependencies=True
        )

        module_name = Path(module_summary.get('file', module_path)).stem

        # Search for test functions and classes related to this module
        test_patterns = [
            f'test_{module_name}',
            f'{module_name}_test',
            f'Test{module_name.title()}'
        ]

        test_func_results = []
        test_class_results = []

        for pattern in test_patterns:
            test_funcs = self.query.find_function(pattern, pattern=True)
            test_classes = self.query.find_class(pattern, pattern=True)
            test_func_results.extend(test_funcs)
            test_class_results.extend(test_classes)

        # Extract test function names (strings)
        test_function_names = set()
        for result in test_func_results:
            func_name = result.name
            # Only include functions that start with 'test_' (actual test functions)
            if func_name.startswith('test_'):
                test_function_names.add(func_name)

        # Extract test class names and their test methods
        test_class_names = set()
        for result in test_class_results:
            class_name = result.name
            test_class_names.add(class_name)

            # Get methods from the test class that start with 'test_'
            class_data = result.data
            methods = class_data.get('methods', [])
            for method in methods:
                method_name = method.get('name', '') if isinstance(method, dict) else str(method)
                if method_name.startswith('test_'):
                    # Include as ClassName.method_name for clarity
                    test_function_names.add(f"{class_name}.{method_name}")

        context['test_functions'] = sorted(test_function_names)
        context['test_classes'] = sorted(test_class_names)

        # Get unique test file paths
        test_files = set()
        for result in test_func_results:
            file_path = result.data.get('file', '')
            if file_path:
                test_files.add(file_path)
        for result in test_class_results:
            file_path = result.data.get('file', '')
            if file_path:
                test_files.add(file_path)

        context['test_files'] = sorted(test_files)

        return context

    def get_refactoring_candidates(self, threshold: int = 5) -> List[QueryResult]:
        """
        Get functions that might need refactoring based on complexity.

        Args:
            threshold: Complexity threshold (default: 5)

        Returns:
            List of high-complexity functions
        """
        return self.query.get_high_complexity(threshold=threshold)

    def get_complexity_hotspots(
        self,
        file_path: Optional[str] = None,
        threshold: int = 5
    ) -> Dict[str, any]:
        """
        Get complexity hotspots for a specific file or entire codebase.

        Identifies high-complexity functions that may need careful attention
        during implementation or refactoring.

        Args:
            file_path: Optional path to filter results to a specific file
            threshold: Complexity threshold (default: 5)

        Returns:
            Dict with complexity hotspot information:
            - file_path: The file path filter (if provided)
            - threshold: The complexity threshold used
            - hotspots: List of {name, complexity, line, file} dicts
            - total_count: Total number of hotspots found

        Example:
            >>> gatherer = SDDContextGatherer()
            >>> result = gatherer.get_complexity_hotspots(
            ...     file_path="src/auth.py",
            ...     threshold=5
            ... )
            >>> for hotspot in result['hotspots']:
            ...     print(f"{hotspot['name']}: complexity {hotspot['complexity']}")
        """
        result = {
            'file_path': file_path,
            'threshold': threshold,
            'hotspots': [],
            'total_count': 0
        }

        # Get high complexity functions
        high_complexity = self.query.get_high_complexity(threshold=threshold)

        # Filter by file if specified
        if file_path:
            high_complexity = [
                r for r in high_complexity
                if r.data.get('file', '') == file_path
            ]

        # Convert to output format
        hotspots = []
        for func in high_complexity:
            hotspots.append({
                'name': func.name,
                'complexity': func.data.get('complexity', 0),
                'line': func.data.get('line'),
                'file': func.data.get('file', '')
            })

        # Sort by complexity (highest first)
        hotspots.sort(key=lambda x: -x['complexity'])

        result['hotspots'] = hotspots
        result['total_count'] = len(hotspots)

        return result

    def get_call_context(
        self,
        function_name: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Get call graph context for a function.

        Gathers caller/callee information using the underlying documentation
        query methods. Useful for understanding function relationships and
        impact analysis during implementation.

        Args:
            function_name: Name of the function to query. If provided alone,
                searches for functions matching this name.
            file_path: Path to file to focus on. If provided with function_name,
                finds functions in that file matching the name. If provided alone,
                returns call context for all functions in the file.

        Returns:
            Dict with call context:
            - function_name: The queried function name (if single function)
            - file_path: The file path (if provided)
            - callers: List of dicts with {name, file, line}
            - callees: List of dicts with {name, file, line}
            - functions_found: List of function names found (if multiple)

        Raises:
            ValueError: If neither function_name nor file_path is provided

        Example:
            >>> gatherer = SDDContextGatherer()
            >>> context = gatherer.get_call_context(function_name="process_data")
            >>> print(f"Callers: {len(context['callers'])}")
            >>> print(f"Callees: {len(context['callees'])}")
        """
        if not function_name and not file_path:
            raise ValueError("Either function_name or file_path must be provided")

        result = {
            'function_name': function_name,
            'file_path': file_path,
            'callers': [],
            'callees': [],
            'functions_found': []
        }

        # Determine which functions to query
        functions_to_query = []

        if function_name:
            # Find functions matching the name
            matches = self.query.find_function(function_name, pattern=False)
            if file_path:
                # Filter to only functions in the specified file
                matches = [m for m in matches if m.data.get('file', '') == file_path]
            functions_to_query = [m.name for m in matches]
        elif file_path:
            # Find all functions in the file
            # Use describe_module to get functions in the file
            module_info = self.query.describe_module(
                file_path,
                top_functions=100,  # Get all functions
                include_docstrings=False,
                include_dependencies=False
            )
            functions_to_query = [
                f.get('name', '') for f in module_info.get('top_functions', [])
                if f.get('name')
            ]

        result['functions_found'] = functions_to_query

        # Gather call context for each function
        seen_callers = set()
        seen_callees = set()

        for func_name in functions_to_query:
            # Get callers
            callers = self.query.get_callers(func_name, include_file=True, include_line=True)
            for caller in callers:
                key = (caller.get('name', ''), caller.get('file', ''), caller.get('line'))
                if key not in seen_callers:
                    seen_callers.add(key)
                    result['callers'].append({
                        'name': caller.get('name', ''),
                        'file': caller.get('file', ''),
                        'line': caller.get('line')
                    })

            # Get callees
            callees = self.query.get_callees(func_name, include_file=True, include_line=True)
            for callee in callees:
                key = (callee.get('name', ''), callee.get('file', ''), callee.get('line'))
                if key not in seen_callees:
                    seen_callees.add(key)
                    result['callees'].append({
                        'name': callee.get('name', ''),
                        'file': callee.get('file', ''),
                        'line': callee.get('line')
                    })

        return result

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Remove common words
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with', 'add', 'create',
            'implement', 'fix', 'update', 'refactor', 'change', 'modify'
        }

        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())

        # Filter stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Return unique keywords
        return list(set(keywords))

    def _deduplicate_results(self, results: List[QueryResult]) -> List[QueryResult]:
        """Remove duplicate results based on name and file."""
        seen = set()
        unique = []

        for result in results:
            key = (result.name, result.data.get('file', ''))
            if key not in seen:
                seen.add(key)
                unique.append(result)

        return unique


# Convenience functions for direct use

def get_task_context(task_description: str, docs_path: Optional[str] = None) -> Dict[str, any]:
    """
    Get context for a task (convenience function).

    Args:
        task_description: Description of the task
        docs_path: Optional path to documentation

    Returns:
        Dict with task context
    """
    gatherer = SDDContextGatherer(docs_path)
    return gatherer.get_task_context(task_description)


def suggest_files_for_task(task_description: str, docs_path: Optional[str] = None) -> List[str]:
    """
    Suggest files for a task (convenience function).

    Args:
        task_description: Description of the task
        docs_path: Optional path to documentation

    Returns:
        List of suggested file paths
    """
    gatherer = SDDContextGatherer(docs_path)
    return gatherer.suggest_files_for_task(task_description)


def find_similar_implementations(feature_name: str, docs_path: Optional[str] = None) -> List[QueryResult]:
    """
    Find similar implementations (convenience function).

    Args:
        feature_name: Feature name or pattern
        docs_path: Optional path to documentation

    Returns:
        List of similar entities
    """
    gatherer = SDDContextGatherer(docs_path)
    return gatherer.find_similar_implementations(feature_name)


def get_test_context(module_path: str, docs_path: Optional[str] = None) -> Dict[str, any]:
    """
    Get test context for a module (convenience function).

    Args:
        module_path: Path to the module
        docs_path: Optional path to documentation

    Returns:
        Dict with test context
    """
    gatherer = SDDContextGatherer(docs_path)
    return gatherer.get_test_context(module_path)


def get_call_context(
    function_name: Optional[str] = None,
    file_path: Optional[str] = None,
    docs_path: Optional[str] = None
) -> Dict[str, any]:
    """
    Get call graph context for a function (convenience function).

    Args:
        function_name: Name of the function to query
        file_path: Path to file to focus on
        docs_path: Optional path to documentation

    Returns:
        Dict with call context including callers and callees

    Raises:
        ValueError: If neither function_name nor file_path is provided
    """
    gatherer = SDDContextGatherer(docs_path)
    return gatherer.get_call_context(function_name=function_name, file_path=file_path)


def get_complexity_hotspots(
    file_path: Optional[str] = None,
    threshold: int = 5,
    docs_path: Optional[str] = None
) -> Dict[str, any]:
    """
    Get complexity hotspots for a file (convenience function).

    Args:
        file_path: Optional path to filter results to a specific file
        threshold: Complexity threshold (default: 5)
        docs_path: Optional path to documentation

    Returns:
        Dict with complexity hotspot information
    """
    gatherer = SDDContextGatherer(docs_path)
    return gatherer.get_complexity_hotspots(file_path=file_path, threshold=threshold)


def main():
    """Main CLI entry point for sdd-integration commands."""
    import sys
    import argparse

    if len(sys.argv) < 2:
        print("Usage: sdd-integration <command> [args...]")
        print("\nCommands:")
        print("  task-context <description> [--file-path PATH] [--spec-id ID] [--json]")
        print("               Get context for a task with optional file/spec focus")
        print("  call-context [--function NAME] [--file PATH] [--json]")
        print("               Get call graph context (callers/callees) for a function or file")
        print("  complexity [--file PATH] [--threshold N] [--json]")
        print("               Get complexity hotspots for a file or entire codebase")
        print("  suggest-files <description>    Suggest files for a task")
        print("  similar <feature>              Find similar implementations")
        print("  test-context <module> [--json] Get test context for module")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'task-context' and len(sys.argv) >= 3:
        # Parse task-context with optional flags
        parser = argparse.ArgumentParser(description='Get task context from documentation')
        parser.add_argument('command', help='Command (task-context)')
        parser.add_argument('description', nargs='+', help='Task description')
        parser.add_argument('--file-path', type=str, help='Optional file path to focus context on')
        parser.add_argument('--spec-id', type=str, help='Optional spec ID for additional context')
        parser.add_argument('--json', action='store_true', help='Output in JSON format')

        args = parser.parse_args()
        task_desc = ' '.join(args.description)

        # Get context from SDDContextGatherer
        gatherer = SDDContextGatherer()
        context = gatherer.get_task_context(task_desc)

        # Add file path and spec id to context if provided
        if args.file_path:
            context['target_file'] = args.file_path
        if args.spec_id:
            context['spec_id'] = args.spec_id

        if args.json:
            # Convert QueryResult objects to dicts for JSON serialization
            import json

            # Convert relevant_classes, relevant_functions, relevant_modules to dicts
            serializable_context = {
                'task_description': context['task_description'],
                'keywords': context['keywords'],
                'relevant_classes': [r.data for r in context['relevant_classes']],
                'relevant_functions': [r.data for r in context['relevant_functions']],
                'relevant_modules': [r.data for r in context['relevant_modules']],
                'dependencies': [d.data if hasattr(d, 'data') else str(d) for d in context['dependencies']],
                'suggested_files': context['suggested_files'],
                'module_summaries': context['module_summaries'],
                'statistics': context.get('statistics', {}),
                'metadata': context.get('metadata', {})
            }

            # Add optional fields if present
            if args.file_path:
                serializable_context['target_file'] = args.file_path
            if args.spec_id:
                serializable_context['spec_id'] = args.spec_id

            print(json.dumps(serializable_context, indent=2))
        else:
            # Original text format
            print(f"\nTask: {task_desc}")
            print(f"\nSuggested files ({len(context['suggested_files'])}):")
            for f in context['suggested_files']:
                print(f"  - {f}")

    elif command == 'suggest-files' and len(sys.argv) >= 3:
        task_desc = ' '.join(sys.argv[2:])
        files = suggest_files_for_task(task_desc)
        print(f"\nSuggested files for: {task_desc}")
        for f in files:
            print(f"  - {f}")

    elif command == 'similar' and len(sys.argv) >= 3:
        feature = sys.argv[2]
        results = find_similar_implementations(feature)
        print(f"\nSimilar implementations for: {feature}")
        for r in results[:10]:  # Top 10
            print(f"  - {r.name} ({r.entity_type}) in {r.data.get('file', 'unknown')}")

    elif command == 'test-context' and len(sys.argv) >= 3:
        # Parse test-context with optional flags
        parser = argparse.ArgumentParser(description='Get test context from documentation')
        parser.add_argument('command', help='Command (test-context)')
        parser.add_argument('module', help='Module path to analyze')
        parser.add_argument('--json', action='store_true', help='Output in JSON format')

        args = parser.parse_args()

        import json as json_module

        try:
            gatherer = SDDContextGatherer()
            context = gatherer.get_test_context(args.module)

            if args.json:
                print(json_module.dumps(context, indent=2))
            else:
                print(f"\nTest context for: {args.module}")
                print(f"Test files: {len(context['test_files'])}")
                for f in context['test_files']:
                    print(f"  - {f}")
                print(f"Test functions: {len(context['test_functions'])}")
                for func in context['test_functions'][:10]:  # Show first 10
                    print(f"  - {func}")
                if len(context['test_functions']) > 10:
                    print(f"  ... and {len(context['test_functions']) - 10} more")
                print(f"Test classes: {len(context['test_classes'])}")
                for cls in context['test_classes']:
                    print(f"  - {cls}")
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == 'call-context':
        # Parse call-context with optional flags
        parser = argparse.ArgumentParser(description='Get call graph context from documentation')
        parser.add_argument('command', help='Command (call-context)')
        parser.add_argument('--function', type=str, help='Function name to query callers/callees for')
        parser.add_argument('--file', type=str, help='File path to get call context for all functions')
        parser.add_argument('--json', action='store_true', help='Output in JSON format')

        args = parser.parse_args()

        if not args.function and not args.file:
            print("Error: Either --function or --file must be provided", file=sys.stderr)
            sys.exit(1)

        import json as json_module

        try:
            gatherer = SDDContextGatherer()
            context = gatherer.get_call_context(
                function_name=args.function,
                file_path=args.file
            )

            if args.json:
                print(json_module.dumps(context, indent=2))
            else:
                # Text format output
                if args.function:
                    print(f"\nCall context for function: {args.function}")
                elif args.file:
                    print(f"\nCall context for file: {args.file}")

                print(f"\nFunctions found: {len(context['functions_found'])}")
                for f in context['functions_found']:
                    print(f"  - {f}")

                print(f"\nCallers ({len(context['callers'])}):")
                for caller in context['callers']:
                    line = f":{caller['line']}" if caller.get('line') else ""
                    print(f"  - {caller['name']} ({caller['file']}{line})")

                print(f"\nCallees ({len(context['callees'])}):")
                for callee in context['callees']:
                    line = f":{callee['line']}" if callee.get('line') else ""
                    print(f"  - {callee['name']} ({callee['file']}{line})")
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == 'complexity':
        # Parse complexity with optional flags
        parser = argparse.ArgumentParser(description='Get complexity hotspots from documentation')
        parser.add_argument('command', help='Command (complexity)')
        parser.add_argument('--file', type=str, help='File path to filter results to')
        parser.add_argument('--threshold', type=int, default=5, help='Complexity threshold (default: 5)')
        parser.add_argument('--json', action='store_true', help='Output in JSON format')

        args = parser.parse_args()

        import json as json_module

        try:
            gatherer = SDDContextGatherer()
            result = gatherer.get_complexity_hotspots(
                file_path=args.file,
                threshold=args.threshold
            )

            if args.json:
                print(json_module.dumps(result, indent=2))
            else:
                # Text format output
                if args.file:
                    print(f"\nComplexity hotspots for: {args.file}")
                else:
                    print(f"\nComplexity hotspots (threshold >= {args.threshold})")

                print(f"\nFound {result['total_count']} hotspots:")
                for hotspot in result['hotspots'][:20]:  # Show first 20
                    line = f":{hotspot['line']}" if hotspot.get('line') else ""
                    print(f"  - {hotspot['name']} (complexity: {hotspot['complexity']}) in {hotspot['file']}{line}")
                if result['total_count'] > 20:
                    print(f"  ... and {result['total_count'] - 20} more")
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


# Example usage for SDD tools
if __name__ == '__main__':
    main()
