"""Verbosity filtering tests for doc_query field sets.

These tests validate that the doc_query-specific field classifications in
`claude_skills.cli.sdd.output_utils` behave as expected in QUIET/NORMAL/VERBOSE
verbosity levels. Each test uses a representative payload that mirrors the
per-entity dictionaries returned by the doc_query CLI commands.
"""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    SEARCH_ESSENTIAL,
    SEARCH_STANDARD,
    FIND_FUNCTION_ESSENTIAL,
    FIND_FUNCTION_STANDARD,
    FIND_CLASS_ESSENTIAL,
    FIND_CLASS_STANDARD,
    LIST_CLASSES_ESSENTIAL,
    LIST_CLASSES_STANDARD,
    LIST_MODULES_ESSENTIAL,
    LIST_MODULES_STANDARD,
    STATS_DOC_QUERY_ESSENTIAL,
    STATS_DOC_QUERY_STANDARD,
    DEPENDENCIES_ESSENTIAL,
    DEPENDENCIES_STANDARD,
)


class TestDocQuerySearchVerbosity:
    """Tests for the doc-query `search` command field filtering."""

    def test_search_quiet_filters_non_standard_fields(self):
        """QUIET mode should keep only the scored entity fields."""
        data = {
            'name': 'UserController',
            'entity_type': 'class',
            'file': 'src/controllers/user.py',
            'line': 128,
            'relevance_score': 0.92,
            'docstring': 'Handles user endpoints',
            'metadata': {'module': 'controllers'},
        }
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, quiet_args, SEARCH_ESSENTIAL, SEARCH_STANDARD)

        assert set(result.keys()) == SEARCH_ESSENTIAL
        assert 'docstring' not in result
        assert 'metadata' not in result

    def test_search_verbose_preserves_optional_fields(self):
        """VERBOSE mode should include all fields, even optional ones."""
        data = {
            'name': 'UserController',
            'entity_type': 'class',
            'file': 'src/controllers/user.py',
            'line': 128,
            'relevance_score': 0.92,
            'docstring': '',
            'metadata': {'module': 'controllers'},
        }
        verbose_args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        result = prepare_output(data, verbose_args, SEARCH_ESSENTIAL, SEARCH_STANDARD)

        assert 'docstring' in result and result['docstring'] == ''
        assert 'metadata' in result


class TestDocQueryFindFunctionVerbosity:
    """Tests for the doc-query `find-function` command."""

    def test_find_function_quiet_mode(self):
        """QUIET mode should include only essential function identifiers."""
        data = {
            'name': 'calculate_total',
            'entity_type': 'function',
            'file': 'src/utils/maths.py',
            'line': 42,
            'signature': 'calculate_total(items: List[Item]) -> float',
            'complexity': 5,
        }
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, quiet_args, FIND_FUNCTION_ESSENTIAL, FIND_FUNCTION_STANDARD)

        assert set(result.keys()) == FIND_FUNCTION_ESSENTIAL
        assert 'signature' not in result
        assert 'complexity' not in result

    def test_find_function_verbose_mode(self):
        """VERBOSE mode should keep optional metadata for debugging."""
        data = {
            'name': 'calculate_total',
            'entity_type': 'function',
            'file': 'src/utils/maths.py',
            'line': 42,
            'signature': 'calculate_total(items: List[Item]) -> float',
            'complexity': 5,
        }
        verbose_args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        result = prepare_output(data, verbose_args, FIND_FUNCTION_ESSENTIAL, FIND_FUNCTION_STANDARD)

        assert 'signature' in result
        assert 'complexity' in result


class TestDocQueryFindClassVerbosity:
    """Tests for the doc-query `find-class` command."""

    def test_find_class_normal_mode_reports_location_only(self):
        """NORMAL mode should only include identifier/location data."""
        data = {
            'name': 'UserService',
            'entity_type': 'class',
            'file': 'src/services/user.py',
            'line': 15,
            'docstring': 'Service for user logic',
            'methods': ['create_user'],
        }
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        result = prepare_output(data, normal_args, FIND_CLASS_ESSENTIAL, FIND_CLASS_STANDARD)

        assert set(result.keys()) == FIND_CLASS_ESSENTIAL
        assert 'docstring' not in result
        assert 'methods' not in result

    def test_find_class_quiet_matches_normal_output(self):
        """QUIET mode should be identical since only minimal fields are standard."""
        data = {
            'name': 'EmptyService',
            'entity_type': 'class',
            'file': 'src/services/empty.py',
            'line': 1,
        }
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, quiet_args, FIND_CLASS_ESSENTIAL, FIND_CLASS_STANDARD)

        assert set(result.keys()) == FIND_CLASS_ESSENTIAL


class TestDocQueryListClassesVerbosity:
    """Tests for the doc-query `list-classes` command."""

    def test_list_classes_quiet_mode_keeps_structure(self):
        """QUIET mode should retain class structure fields."""
        data = {
            'name': 'InvoiceService',
            'file': 'src/services/invoice.py',
            'line': 50,
            'methods': ['generate', 'send'],
            'bases': ['BaseService'],
            'docstring': 'Invoice helpers',
        }
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, quiet_args, LIST_CLASSES_ESSENTIAL, LIST_CLASSES_STANDARD)

        assert 'methods' in result
        assert 'bases' in result
        assert 'docstring' not in result

    def test_list_classes_quiet_drops_empty_lists(self):
        """Empty method/base lists should be omitted in QUIET mode."""
        data = {
            'name': 'Placeholder',
            'file': 'src/services/placeholder.py',
            'line': 5,
            'methods': [],
            'bases': [],
        }
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, quiet_args, LIST_CLASSES_ESSENTIAL, LIST_CLASSES_STANDARD)

        assert 'methods' not in result
        assert 'bases' not in result


class TestDocQueryListModulesVerbosity:
    """Tests for the doc-query `list-modules` command."""

    def test_list_modules_quiet_mode(self):
        """QUIET mode keeps only the module summary fields."""
        data = {
            'name': 'services.payments',
            'file': 'src/services/payments/__init__.py',
            'classes': ['PaymentService'],
            'functions': ['process_payment'],
            'docstring': 'Payment module helpers',
        }
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, quiet_args, LIST_MODULES_ESSENTIAL, LIST_MODULES_STANDARD)

        assert 'docstring' not in result
        assert set(result.keys()) == LIST_MODULES_ESSENTIAL


class TestDocQueryStatsVerbosity:
    """Tests for the doc-query `stats` command."""

    def test_stats_normal_mode_includes_extended_metrics(self):
        """NORMAL mode should include the extended statistics."""
        data = {
            'total_files': 50,
            'total_modules': 12,
            'total_classes': 30,
            'total_functions': 180,
            'generated_at': '2025-11-15T10:00:00Z',
            'metadata': {'project_name': 'sample', 'version': '1.0.0'},
            'statistics': {'languages': ['python']},
            'total_lines': 12000,
            'avg_complexity': 4.1,
            'max_complexity': 12,
            'high_complexity_count': 6,
        }
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        result = prepare_output(data, normal_args, STATS_DOC_QUERY_ESSENTIAL, STATS_DOC_QUERY_STANDARD)

        assert 'total_lines' in result
        assert 'avg_complexity' in result
        assert 'max_complexity' in result
        assert 'high_complexity_count' in result

    def test_stats_quiet_mode_strips_optional_metrics(self):
        """QUIET mode should omit derived metrics while keeping aggregates."""
        data = {
            'total_files': 50,
            'total_modules': 12,
            'total_classes': 30,
            'total_functions': 180,
            'generated_at': '2025-11-15T10:00:00Z',
            'metadata': {'project_name': 'sample', 'version': '1.0.0'},
            'statistics': {'languages': ['python']},
            'total_lines': 12000,
            'avg_complexity': 4.1,
            'max_complexity': 12,
            'high_complexity_count': 6,
        }
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, quiet_args, STATS_DOC_QUERY_ESSENTIAL, STATS_DOC_QUERY_STANDARD)

        assert 'total_lines' not in result
        assert 'avg_complexity' not in result
        assert 'max_complexity' not in result
        assert 'high_complexity_count' not in result
        assert 'metadata' in result


class TestDocQueryDependenciesVerbosity:
    """Tests for the doc-query `dependencies` command."""

    def test_dependencies_quiet_mode(self):
        """QUIET mode should keep only imports/imported_by information."""
        data = {
            'name': 'src/services/payments.py',
            'entity_type': 'module',
            'file': 'src/services/payments.py',
            'imports': ['src.utils.currency', 'src.models.invoice'],
            'imported_by': ['src/routes/payments'],
            'external_imports': ['requests'],
        }
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, quiet_args, DEPENDENCIES_ESSENTIAL, DEPENDENCIES_STANDARD)

        assert 'imports' in result
        assert 'imported_by' in result
        assert 'external_imports' not in result

    def test_dependencies_verbose_mode(self):
        """VERBOSE mode includes optional dependency metadata."""
        data = {
            'name': 'src/services/payments.py',
            'entity_type': 'module',
            'file': 'src/services/payments.py',
            'imports': ['src.utils.currency', 'src.models.invoice'],
            'imported_by': ['src/routes/payments'],
            'external_imports': ['requests'],
        }
        verbose_args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        result = prepare_output(data, verbose_args, DEPENDENCIES_ESSENTIAL, DEPENDENCIES_STANDARD)

        assert 'external_imports' in result


class TestDocQueryVerbosityIntegration:
    """Lightweight integration checks for doc_query field sets."""

    def test_field_sets_defined(self):
        """Ensure constants exist for the key doc_query commands."""
        assert SEARCH_ESSENTIAL
        assert FIND_FUNCTION_ESSENTIAL
        assert FIND_CLASS_ESSENTIAL
        assert LIST_MODULES_ESSENTIAL
        assert STATS_DOC_QUERY_ESSENTIAL
        assert DEPENDENCIES_ESSENTIAL

    def test_essential_subset_of_standard(self):
        """Essential fields should always be a subset of the standard fields."""
        assert SEARCH_ESSENTIAL.issubset(SEARCH_STANDARD)
        assert FIND_FUNCTION_ESSENTIAL.issubset(FIND_FUNCTION_STANDARD)
        assert FIND_CLASS_ESSENTIAL.issubset(FIND_CLASS_STANDARD)
        assert LIST_MODULES_ESSENTIAL.issubset(LIST_MODULES_STANDARD)
        assert STATS_DOC_QUERY_ESSENTIAL.issubset(STATS_DOC_QUERY_STANDARD)
        assert DEPENDENCIES_ESSENTIAL.issubset(DEPENDENCIES_STANDARD)

    def test_quiet_vs_verbose_size_difference(self):
        """QUIET mode should yield fewer keys than VERBOSE mode for doc_query entries."""
        data = {
            'name': 'NotificationService',
            'entity_type': 'class',
            'file': 'src/services/notifications.py',
            'line': 77,
            'relevance_score': 0.81,
            'docstring': 'Handles notification dispatching',
            'metadata': {'module': 'notifications'},
        }
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        verbose_args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)

        quiet_result = prepare_output(data, quiet_args, SEARCH_ESSENTIAL, SEARCH_STANDARD)
        verbose_result = prepare_output(data, verbose_args, SEARCH_ESSENTIAL, SEARCH_STANDARD)

        assert len(quiet_result) < len(verbose_result)
