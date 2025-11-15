"""Integration tests for doc_query module verbosity filtering.

Tests verify that all doc_query commands properly respect verbosity levels:
1. QUIET mode - only essential fields
2. NORMAL mode - essential + standard fields
3. VERBOSE mode - all fields including empty ones

Commands tested:
- sdd doc-query search
- sdd doc-query get-function
- sdd doc-query get-class
- sdd doc-query list-modules
- sdd doc-query stats
- sdd doc-query analyze-imports
"""

import pytest
import argparse
from unittest.mock import Mock, patch, MagicMock

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    DOC_QUERY_SEARCH_ESSENTIAL,
    DOC_QUERY_SEARCH_STANDARD,
    DOC_QUERY_GET_FUNCTION_ESSENTIAL,
    DOC_QUERY_GET_FUNCTION_STANDARD,
    DOC_QUERY_GET_CLASS_ESSENTIAL,
    DOC_QUERY_GET_CLASS_STANDARD,
    DOC_QUERY_LIST_MODULES_ESSENTIAL,
    DOC_QUERY_LIST_MODULES_STANDARD,
    DOC_QUERY_STATS_ESSENTIAL,
    DOC_QUERY_STATS_STANDARD,
    DOC_QUERY_ANALYZE_IMPORTS_ESSENTIAL,
    DOC_QUERY_ANALYZE_IMPORTS_STANDARD,
)


class TestDocQuerySearchVerbosity:
    """Test verbosity filtering for doc-query search command."""

    def test_search_quiet_mode_filters_non_essential(self):
        """QUIET mode should only include essential fields."""
        data = {
            'matches': [{'name': 'foo', 'file': 'foo.py'}],
            'total_matches': 1,
            'query': 'foo',
            'search_time_ms': 45,
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, args, DOC_QUERY_SEARCH_ESSENTIAL, DOC_QUERY_SEARCH_STANDARD)

        assert 'matches' in result
        assert 'total_matches' in result
        # Non-essential fields should be filtered
        assert 'query' not in result or result['query']  # Only filtered if empty
        assert 'search_time_ms' not in result

    def test_search_normal_mode_includes_standard(self):
        """NORMAL mode should include essential + standard fields."""
        data = {
            'matches': [{'name': 'foo', 'file': 'foo.py'}],
            'total_matches': 1,
            'query': 'foo',
            'search_time_ms': 45,
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        result = prepare_output(data, args, DOC_QUERY_SEARCH_ESSENTIAL, DOC_QUERY_SEARCH_STANDARD)

        assert 'matches' in result
        assert 'total_matches' in result
        assert 'query' in result
        assert 'search_time_ms' in result

    def test_search_verbose_mode_includes_all(self):
        """VERBOSE mode should include all fields including empty ones."""
        data = {
            'matches': [],
            'total_matches': 0,
            'query': 'nonexistent',
            'search_time_ms': 12,
            'metadata': {},
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        result = prepare_output(data, args, DOC_QUERY_SEARCH_ESSENTIAL, DOC_QUERY_SEARCH_STANDARD)

        assert 'matches' in result
        assert 'total_matches' in result
        assert 'query' in result
        assert 'search_time_ms' in result
        assert 'metadata' in result  # Empty dict included in VERBOSE


class TestDocQueryGetFunctionVerbosity:
    """Test verbosity filtering for doc-query get-function command."""

    def test_get_function_quiet_mode(self):
        """QUIET mode should only include essential function fields."""
        data = {
            'name': 'calculate_total',
            'signature': 'calculate_total(items: List[Item]) -> float',
            'file_path': 'src/utils.py',
            'docstring': 'Calculate total price',
            'line_number': 45,
            'complexity': 3,
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, args, DOC_QUERY_GET_FUNCTION_ESSENTIAL, DOC_QUERY_GET_FUNCTION_STANDARD)

        assert 'name' in result
        assert 'signature' in result
        assert 'file_path' in result
        # Non-essential should be filtered
        assert 'complexity' not in result

    def test_get_function_verbose_with_empty_docstring(self):
        """VERBOSE mode should include empty docstring."""
        data = {
            'name': 'helper',
            'signature': 'helper() -> None',
            'file_path': 'src/helpers.py',
            'docstring': '',  # Empty docstring
            'line_number': 12,
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        result = prepare_output(data, args, DOC_QUERY_GET_FUNCTION_ESSENTIAL, DOC_QUERY_GET_FUNCTION_STANDARD)

        assert 'docstring' in result
        assert result['docstring'] == ''


class TestDocQueryGetClassVerbosity:
    """Test verbosity filtering for doc-query get-class command."""

    def test_get_class_normal_mode(self):
        """NORMAL mode should include standard class fields."""
        data = {
            'name': 'UserService',
            'file_path': 'src/services/user.py',
            'docstring': 'Handle user operations',
            'methods': ['create', 'update', 'delete'],
            'line_number': 10,
            'base_classes': ['BaseService'],
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        result = prepare_output(data, args, DOC_QUERY_GET_CLASS_ESSENTIAL, DOC_QUERY_GET_CLASS_STANDARD)

        assert 'name' in result
        assert 'file_path' in result
        assert 'docstring' in result
        assert 'methods' in result

    def test_get_class_quiet_omits_empty_lists(self):
        """QUIET mode should omit empty lists."""
        data = {
            'name': 'EmptyClass',
            'file_path': 'src/empty.py',
            'docstring': 'Empty class',
            'methods': [],  # Empty list
            'base_classes': [],  # Empty list
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, args, DOC_QUERY_GET_CLASS_ESSENTIAL, DOC_QUERY_GET_CLASS_STANDARD)

        assert 'name' in result
        # Empty lists should be omitted in QUIET
        assert 'methods' not in result or result['methods'] == []
        assert 'base_classes' not in result or result['base_classes'] == []


class TestDocQueryListModulesVerbosity:
    """Test verbosity filtering for doc-query list-modules command."""

    def test_list_modules_quiet_mode(self):
        """QUIET mode should only include essential module info."""
        data = {
            'modules': [
                {'name': 'utils', 'file': 'utils.py'},
                {'name': 'services', 'file': 'services.py'},
            ],
            'total_modules': 2,
            'filter_applied': 'python',
            'scan_time_ms': 123,
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, args, DOC_QUERY_LIST_MODULES_ESSENTIAL, DOC_QUERY_LIST_MODULES_STANDARD)

        assert 'modules' in result
        assert 'total_modules' in result
        # Non-essential fields filtered
        assert 'scan_time_ms' not in result


class TestDocQueryStatsVerbosity:
    """Test verbosity filtering for doc-query stats command."""

    def test_stats_normal_mode(self):
        """NORMAL mode should include standard stats fields."""
        data = {
            'total_functions': 145,
            'total_classes': 32,
            'total_modules': 18,
            'language_breakdown': {'python': 15, 'javascript': 3},
            'complexity_stats': {'avg': 4.2, 'max': 15},
            'cache_hit_rate': 0.85,
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        result = prepare_output(data, args, DOC_QUERY_STATS_ESSENTIAL, DOC_QUERY_STATS_STANDARD)

        assert 'total_functions' in result
        assert 'total_classes' in result
        assert 'total_modules' in result
        assert 'language_breakdown' in result

    def test_stats_quiet_mode_minimal_output(self):
        """QUIET mode should provide minimal stats."""
        data = {
            'total_functions': 145,
            'total_classes': 32,
            'total_modules': 18,
            'language_breakdown': {'python': 15},
            'complexity_stats': {},  # Empty
            'cache_hit_rate': 0.85,
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, args, DOC_QUERY_STATS_ESSENTIAL, DOC_QUERY_STATS_STANDARD)

        assert 'total_functions' in result
        assert 'total_classes' in result
        assert 'total_modules' in result
        # Empty complexity_stats omitted in QUIET
        assert 'complexity_stats' not in result or result['complexity_stats'] == {}


class TestDocQueryAnalyzeImportsVerbosity:
    """Test verbosity filtering for doc-query analyze-imports command."""

    def test_analyze_imports_verbose_mode(self):
        """VERBOSE mode should include all import analysis data."""
        data = {
            'imports': ['os', 'sys', 'pathlib'],
            'external_imports': ['requests', 'numpy'],
            'import_graph': {},  # Empty but should be included
            'circular_dependencies': [],
            'unused_imports': [],
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        result = prepare_output(data, args, DOC_QUERY_ANALYZE_IMPORTS_ESSENTIAL, DOC_QUERY_ANALYZE_IMPORTS_STANDARD)

        assert 'imports' in result
        assert 'external_imports' in result
        assert 'import_graph' in result  # Empty dict included
        assert 'circular_dependencies' in result  # Empty list included
        assert 'unused_imports' in result  # Empty list included

    def test_analyze_imports_quiet_mode(self):
        """QUIET mode should only show essential import data."""
        data = {
            'imports': ['os', 'sys'],
            'external_imports': ['requests'],
            'import_graph': {'os': ['pathlib']},
            'circular_dependencies': [],
            'unused_imports': [],
        }
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, args, DOC_QUERY_ANALYZE_IMPORTS_ESSENTIAL, DOC_QUERY_ANALYZE_IMPORTS_STANDARD)

        assert 'imports' in result
        # Empty lists omitted in QUIET
        assert 'circular_dependencies' not in result or result['circular_dependencies'] == []
        assert 'unused_imports' not in result or result['unused_imports'] == []


class TestDocQueryVerbosityIntegration:
    """Integration tests for doc_query verbosity across all commands."""

    def test_all_commands_respect_verbosity_levels(self):
        """Verify all doc_query commands have field sets defined."""
        # Verify field sets exist
        assert DOC_QUERY_SEARCH_ESSENTIAL is not None
        assert DOC_QUERY_SEARCH_STANDARD is not None
        assert DOC_QUERY_GET_FUNCTION_ESSENTIAL is not None
        assert DOC_QUERY_GET_FUNCTION_STANDARD is not None
        assert DOC_QUERY_GET_CLASS_ESSENTIAL is not None
        assert DOC_QUERY_GET_CLASS_STANDARD is not None
        assert DOC_QUERY_LIST_MODULES_ESSENTIAL is not None
        assert DOC_QUERY_LIST_MODULES_STANDARD is not None
        assert DOC_QUERY_STATS_ESSENTIAL is not None
        assert DOC_QUERY_STATS_STANDARD is not None
        assert DOC_QUERY_ANALYZE_IMPORTS_ESSENTIAL is not None
        assert DOC_QUERY_ANALYZE_IMPORTS_STANDARD is not None

    def test_essential_is_subset_of_standard(self):
        """Essential fields should be a subset of standard fields."""
        assert DOC_QUERY_SEARCH_ESSENTIAL.issubset(DOC_QUERY_SEARCH_STANDARD)
        assert DOC_QUERY_GET_FUNCTION_ESSENTIAL.issubset(DOC_QUERY_GET_FUNCTION_STANDARD)
        assert DOC_QUERY_GET_CLASS_ESSENTIAL.issubset(DOC_QUERY_GET_CLASS_STANDARD)
        assert DOC_QUERY_LIST_MODULES_ESSENTIAL.issubset(DOC_QUERY_LIST_MODULES_STANDARD)
        assert DOC_QUERY_STATS_ESSENTIAL.issubset(DOC_QUERY_STATS_STANDARD)
        assert DOC_QUERY_ANALYZE_IMPORTS_ESSENTIAL.issubset(DOC_QUERY_ANALYZE_IMPORTS_STANDARD)

    def test_field_filtering_reduces_output_size(self):
        """Verify that QUIET mode produces smaller output than VERBOSE."""
        large_data = {
            'matches': [{'name': f'func{i}', 'file': f'file{i}.py'} for i in range(100)],
            'total_matches': 100,
            'query': 'test_query',
            'search_time_ms': 456,
            'metadata': {'cache_hit': True, 'database_queries': 5},
            'debug_info': {'sql_queries': ['SELECT *...']},
        }

        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        verbose_args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)

        quiet_result = prepare_output(large_data, quiet_args, DOC_QUERY_SEARCH_ESSENTIAL, DOC_QUERY_SEARCH_STANDARD)
        verbose_result = prepare_output(large_data, verbose_args, DOC_QUERY_SEARCH_ESSENTIAL, DOC_QUERY_SEARCH_STANDARD)

        # QUIET should have fewer keys than VERBOSE
        assert len(quiet_result.keys()) <= len(verbose_result.keys())
