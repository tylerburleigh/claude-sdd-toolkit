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
            docs_path: Path to documentation.json or docs directory
        """
        self.query = DocumentationQuery(docs_path)
        if not self.query.load():
            raise RuntimeError(
                f"Documentation not found at {self.query.docs_path}. "
                "Run code-doc skill first."
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
        Find test files and test coverage context for a module.

        Args:
            module_path: Path to the module

        Returns:
            Dict with test context
        """
        context = {
            'module': module_path,
            'test_files': [],
            'test_functions': [],
            'coverage_estimate': 'unknown'
        }

        # Look for test files
        # Common patterns: test_*.py, *_test.py, tests/*.py
        module_summary = self.query.describe_module(
            module_path,
            include_docstrings=False,
            include_dependencies=True
        )

        module_name = Path(module_summary.get('file', module_path)).stem

        # Search for test functions related to this module
        test_patterns = [
            f'test_{module_name}',
            f'{module_name}_test',
            f'Test{module_name.title()}'
        ]

        for pattern in test_patterns:
            test_funcs = self.query.find_function(pattern, pattern=True)
            test_classes = self.query.find_class(pattern, pattern=True)
            context['test_functions'].extend(test_funcs)
            context['test_functions'].extend(test_classes)

        # Get unique test file paths
        test_files = set()
        for result in context['test_functions']:
            test_files.add(result.data.get('file', ''))

        context['test_files'] = sorted(test_files)

        # Estimate coverage
        total_functions = module_summary.get('statistics', {}).get('function_count', 0)
        test_count = len(context['test_functions'])

        if total_functions > 0:
            coverage_ratio = test_count / total_functions
            if coverage_ratio >= 1.0:
                context['coverage_estimate'] = 'high'
            elif coverage_ratio >= 0.5:
                context['coverage_estimate'] = 'medium'
            elif coverage_ratio > 0:
                context['coverage_estimate'] = 'low'
            else:
                context['coverage_estimate'] = 'none'

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

    def get_impact_analysis(self, module_path: str) -> Dict[str, any]:
        """
        Analyze the impact of changes to a module.

        Args:
            module_path: Path to the module

        Returns:
            Dict with impact analysis
        """
        context = {
            'module': module_path,
            'direct_dependencies': [],
            'reverse_dependencies': [],
            'affected_modules': [],
            'impact_scope': 'unknown',
            'module_summary': self.query.describe_module(
                module_path,
                include_docstrings=False,
                include_dependencies=True
            )
        }

        # Get direct dependencies
        direct_deps = self.query.get_dependencies(module_path, reverse=False)
        context['direct_dependencies'] = [d.name for d in direct_deps]

        # Get reverse dependencies (who depends on this)
        reverse_deps = self.query.get_dependencies(module_path, reverse=True)
        context['reverse_dependencies'] = [d.name for d in reverse_deps]

        # Affected modules include both
        affected = set(context['direct_dependencies'] + context['reverse_dependencies'])
        context['affected_modules'] = sorted(affected)

        # Determine impact scope
        total_affected = len(context['affected_modules'])
        if total_affected == 0:
            context['impact_scope'] = 'isolated'
        elif total_affected <= 3:
            context['impact_scope'] = 'low'
        elif total_affected <= 10:
            context['impact_scope'] = 'medium'
        else:
            context['impact_scope'] = 'high'

        return context

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


def get_impact_analysis(module_path: str, docs_path: Optional[str] = None) -> Dict[str, any]:
    """
    Get impact analysis for a module (convenience function).

    Args:
        module_path: Path to the module
        docs_path: Optional path to documentation

    Returns:
        Dict with impact analysis
    """
    gatherer = SDDContextGatherer(docs_path)
    return gatherer.get_impact_analysis(module_path)


def main():
    """Main CLI entry point for sdd-integration commands."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: sdd-integration <command> [args...]")
        print("\nCommands:")
        print("  task-context <description>     Get context for a task")
        print("  suggest-files <description>    Suggest files for a task")
        print("  similar <feature>              Find similar implementations")
        print("  test-context <module>          Get test context for module")
        print("  impact <module>                Get impact analysis")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'task-context' and len(sys.argv) >= 3:
        task_desc = ' '.join(sys.argv[2:])
        context = get_task_context(task_desc)
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
        module = sys.argv[2]
        context = get_test_context(module)
        print(f"\nTest context for: {module}")
        print(f"Test files: {len(context['test_files'])}")
        for f in context['test_files']:
            print(f"  - {f}")
        print(f"Coverage estimate: {context['coverage_estimate']}")

    elif command == 'impact' and len(sys.argv) >= 3:
        module = sys.argv[2]
        impact = get_impact_analysis(module)
        print(f"\nImpact analysis for: {module}")
        print(f"Impact scope: {impact['impact_scope']}")
        print(f"Affected modules: {len(impact['affected_modules'])}")
        for m in impact['affected_modules']:
            print(f"  - {m}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


# Example usage for SDD tools
if __name__ == '__main__':
    main()
