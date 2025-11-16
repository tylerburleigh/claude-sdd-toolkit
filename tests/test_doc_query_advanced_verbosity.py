"""Verbosity tests for advanced doc_query field sets."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    COMPLEXITY_ESSENTIAL,
    COMPLEXITY_STANDARD,
    FIND_MODULE_ESSENTIAL,
    FIND_MODULE_STANDARD,
    DESCRIBE_MODULE_ESSENTIAL,
    DESCRIBE_MODULE_STANDARD,
    LIST_FUNCTIONS_ESSENTIAL,
    LIST_FUNCTIONS_STANDARD,
    CALLERS_ESSENTIAL,
    CALLERS_STANDARD,
    CALLEES_ESSENTIAL,
    CALLEES_STANDARD,
    CALL_GRAPH_ESSENTIAL,
    CALL_GRAPH_STANDARD,
    CONTEXT_DOC_QUERY_ESSENTIAL,
    CONTEXT_DOC_QUERY_STANDARD,
    TRACE_ENTRY_ESSENTIAL,
    TRACE_ENTRY_STANDARD,
    TRACE_DATA_ESSENTIAL,
    TRACE_DATA_STANDARD,
    IMPACT_ESSENTIAL,
    IMPACT_STANDARD,
    REFACTOR_CANDIDATES_ESSENTIAL,
    REFACTOR_CANDIDATES_STANDARD,
)


def _args(level):
    return argparse.Namespace(verbosity_level=level)


class TestComplexityVerbosity:
    def test_complexity_quiet_mode(self):
        data = {
            'name': 'calculate_total',
            'complexity': 8,
            'entity_type': 'function',
            'file': 'src/utils/math.py',
            'line': 40,
            'module': 'utils.math',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), COMPLEXITY_ESSENTIAL, COMPLEXITY_STANDARD)
        assert 'module' not in result
        assert set(result.keys()) == COMPLEXITY_ESSENTIAL


class TestFindModuleVerbosity:
    def test_find_module_quiet_mode(self):
        data = {
            'name': 'utils',
            'entity_type': 'module',
            'file': 'src/utils/__init__.py',
            'line': 1,
            'docstring': 'Utility helpers',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), FIND_MODULE_ESSENTIAL, FIND_MODULE_STANDARD)
        assert 'docstring' not in result


class TestDescribeModuleVerbosity:
    def test_describe_module_quiet_mode(self):
        data = {
            'name': 'services.users',
            'file': 'src/services/users/__init__.py',
            'classes': ['UserService'],
            'functions': ['create_user'],
            'imports': ['src.db'],
            'docstring': 'User services',
            'line_count': 200,
            'complexity': 3.1,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), DESCRIBE_MODULE_ESSENTIAL, DESCRIBE_MODULE_STANDARD)
        assert set(result.keys()) == DESCRIBE_MODULE_ESSENTIAL


class TestCallersVerbosity:
    def test_callers_quiet_mode(self):
        data = {
            'name': 'calculate_total',
            'entity_type': 'function',
            'file': 'src/utils/math.py',
            'line': 42,
            'call_chain': ['api.orders', 'services.billing'],
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), CALLERS_ESSENTIAL, CALLERS_STANDARD)
        assert set(result.keys()) == CALLERS_ESSENTIAL

    def test_callees_quiet_mode(self):
        data = {
            'name': 'calculate_total',
            'entity_type': 'function',
            'file': 'src/utils/math.py',
            'line': 42,
            'callees': ['Decimal.normalize'],
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), CALLEES_ESSENTIAL, CALLEES_STANDARD)
        assert set(result.keys()) == CALLEES_ESSENTIAL


class TestCallGraphVerbosity:
    def test_call_graph_quiet_mode(self):
        data = {
            'nodes': ['A', 'B'],
            'edges': [('A', 'B')],
            'entry_points': ['A'],
            'stats': {'depth': 3},
            'metadata': {'rendered': True},
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), CALL_GRAPH_ESSENTIAL, CALL_GRAPH_STANDARD)
        assert 'metadata' not in result
        assert set(result.keys()) == CALL_GRAPH_ESSENTIAL


class TestContextVerbosity:
    def test_context_quiet_mode(self):
        data = {
            'name': 'AuthService',
            'entity_type': 'class',
            'file': 'src/services/auth.py',
            'line': 10,
            'summary': 'Handles login',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), CONTEXT_DOC_QUERY_ESSENTIAL, CONTEXT_DOC_QUERY_STANDARD)
        assert set(result.keys()) == CONTEXT_DOC_QUERY_ESSENTIAL


class TestTraceEntryVerbosity:
    def test_trace_entry_quiet_mode(self):
        data = {
            'entry_point': 'api.orders.process',
            'call_depth': 5,
            'execution_paths': [['api', 'service', 'db']],
            'total_functions': 20,
            'leaf_functions': 5,
            'notes': 'complex',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), TRACE_ENTRY_ESSENTIAL, TRACE_ENTRY_STANDARD)
        assert 'notes' not in result
        assert set(result.keys()) == TRACE_ENTRY_ESSENTIAL


class TestTraceDataVerbosity:
    def test_trace_data_quiet_mode(self):
        data = {
            'data_item': 'UserSession',
            'lifecycle_stages': ['created', 'cached'],
            'read_locations': ['src/api/session.py'],
            'write_locations': ['src/api/auth.py'],
            'total_references': 10,
            'notes': 'PII',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), TRACE_DATA_ESSENTIAL, TRACE_DATA_STANDARD)
        assert 'notes' not in result
        assert set(result.keys()) == TRACE_DATA_ESSENTIAL


class TestImpactVerbosity:
    def test_impact_quiet_mode(self):
        data = {
            'target': 'UserController',
            'direct_impact': ['api/users.py'],
            'indirect_impact': ['services/email.py'],
            'affected_modules': ['api.users'],
            'affected_classes': ['UserController'],
            'affected_functions': ['send_notification'],
            'risk_level': 'HIGH',
            'total_affected': 5,
            'notes': 'High touch',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), IMPACT_ESSENTIAL, IMPACT_STANDARD)
        assert 'notes' not in result
        assert set(result.keys()) == IMPACT_ESSENTIAL


class TestRefactorCandidatesVerbosity:
    def test_refactor_candidates_quiet_mode(self):
        data = {
            'candidates': ['utils.math'],
            'total_candidates': 1,
            'high_priority': ['utils.math'],
            'medium_priority': ['utils.logging'],
            'low_priority': ['utils.misc'],
            'metadata': {'generated_at': 'today'},
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET), REFACTOR_CANDIDATES_ESSENTIAL, REFACTOR_CANDIDATES_STANDARD
        )
        assert 'metadata' not in result
        assert set(result.keys()) == REFACTOR_CANDIDATES_ESSENTIAL


class TestListFunctionsVerbosity:
    def test_list_functions_quiet_mode(self):
        data = {
            'name': 'calculate_total',
            'file': 'src/utils/math.py',
            'line': 42,
            'complexity': 5,
            'params': ['items'],
            'docstring': 'Sum items',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), LIST_FUNCTIONS_ESSENTIAL, LIST_FUNCTIONS_STANDARD)
        assert set(result.keys()) == LIST_FUNCTIONS_ESSENTIAL
