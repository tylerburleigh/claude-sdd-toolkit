"""Verbosity tests for sdd-update task/lifecycle helper commands."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    ADD_ASSUMPTION_ESSENTIAL,
    ADD_ASSUMPTION_STANDARD,
    LIST_ASSUMPTIONS_ESSENTIAL,
    LIST_ASSUMPTIONS_STANDARD,
    ADD_REVISION_ESSENTIAL,
    ADD_REVISION_STANDARD,
    ADD_TASK_ESSENTIAL,
    ADD_TASK_STANDARD,
    REMOVE_TASK_ESSENTIAL,
    REMOVE_TASK_STANDARD,
    ADD_VERIFICATION_ESSENTIAL,
    ADD_VERIFICATION_STANDARD,
    EXECUTE_VERIFY_ESSENTIAL,
    EXECUTE_VERIFY_STANDARD,
    BULK_JOURNAL_ESSENTIAL,
    BULK_JOURNAL_STANDARD,
    COMPLETE_TASK_ESSENTIAL,
    COMPLETE_TASK_STANDARD,
    CREATE_TASK_COMMIT_ESSENTIAL,
    CREATE_TASK_COMMIT_STANDARD,
    CHECK_JOURNALING_ESSENTIAL,
    CHECK_JOURNALING_STANDARD,
    CHECK_COMPLETE_ESSENTIAL,
    CHECK_COMPLETE_STANDARD,
    CHECK_ENVIRONMENT_ESSENTIAL,
    CHECK_ENVIRONMENT_STANDARD,
    INIT_ENV_ESSENTIAL,
    INIT_ENV_STANDARD,
    GET_TASK_ESSENTIAL,
    GET_TASK_STANDARD,
    GET_JOURNAL_ESSENTIAL,
    GET_JOURNAL_STANDARD,
    LIST_PHASES_ESSENTIAL,
    LIST_PHASES_STANDARD,
    PHASE_TIME_ESSENTIAL,
    PHASE_TIME_STANDARD,
    STATUS_REPORT_ESSENTIAL,
    STATUS_REPORT_STANDARD,
    TIME_REPORT_ESSENTIAL,
    TIME_REPORT_STANDARD,
    UPDATE_ESTIMATE_ESSENTIAL,
    UPDATE_ESTIMATE_STANDARD,
    UPDATE_FRONTMATTER_ESSENTIAL,
    UPDATE_FRONTMATTER_STANDARD,
    AUDIT_SPEC_ESSENTIAL,
    AUDIT_SPEC_STANDARD,
    RECONCILE_STATE_ESSENTIAL,
    RECONCILE_STATE_STANDARD,
)


def _args(level):
    return argparse.Namespace(verbosity_level=level)


class TestAddAssumptionVerbosity:
    def test_add_assumption_quiet_mode(self):
        data = {
            'success': True,
            'assumption_id': 'assumption-1',
            'spec_id': 'spec-1',
            'task_id': 'task-1',
            'assumption_text': 'Assume service exists',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), ADD_ASSUMPTION_ESSENTIAL, ADD_ASSUMPTION_STANDARD)
        assert set(result.keys()) == ADD_ASSUMPTION_ESSENTIAL

    def test_list_assumptions_verbose_mode(self):
        data = {
            'assumptions': [{'id': 'assumption-1'}],
            'spec_id': 'spec-1',
            'count': 1,
            'filtered': False,
        }
        result = prepare_output(
            data, _args(VerbosityLevel.VERBOSE),
            LIST_ASSUMPTIONS_ESSENTIAL, LIST_ASSUMPTIONS_STANDARD
        )
        assert 'spec_id' in result
        assert 'count' in result


class TestRevisionAndTaskMutationVerbosity:
    def test_add_revision_quiet_mode(self):
        data = {
            'success': True,
            'revision_id': 'rev-1',
            'revision_text': 'Updated description',
            'spec_id': 'spec-1',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), ADD_REVISION_ESSENTIAL, ADD_REVISION_STANDARD)
        assert set(result.keys()) == ADD_REVISION_ESSENTIAL

    def test_add_task_quiet_mode(self):
        data = {
            'success': True,
            'task_id': 'task-2',
            'parent': 'task-1',
            'title': 'Implement tests',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), ADD_TASK_ESSENTIAL, ADD_TASK_STANDARD)
        assert set(result.keys()) == ADD_TASK_ESSENTIAL

    def test_remove_task_quiet_mode(self):
        data = {
            'success': True,
            'task_id': 'task-2',
            'removed_count': 3,
            'spec_id': 'spec-1',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), REMOVE_TASK_ESSENTIAL, REMOVE_TASK_STANDARD)
        assert set(result.keys()) == REMOVE_TASK_ESSENTIAL


class TestVerificationCommandsVerbosity:
    def test_add_verification_quiet_mode(self):
        data = {
            'success': True,
            'verification_id': 'verify-1',
            'spec_id': 'spec-1',
            'verification_type': 'auto',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), ADD_VERIFICATION_ESSENTIAL, ADD_VERIFICATION_STANDARD)
        assert set(result.keys()) == ADD_VERIFICATION_ESSENTIAL

    def test_execute_verify_quiet_mode(self):
        data = {
            'success': True,
            'task_id': 'task-verify',
            'result': 'PASSED',
            'details': 'All checks passed',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), EXECUTE_VERIFY_ESSENTIAL, EXECUTE_VERIFY_STANDARD)
        assert set(result.keys()) == EXECUTE_VERIFY_ESSENTIAL


class TestBulkAndCompleteVerbosity:
    def test_bulk_journal_quiet_mode(self):
        data = {
            'success': True,
            'entries_added': 5,
            'spec_id': 'spec-2',
            'entry_count': 5,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), BULK_JOURNAL_ESSENTIAL, BULK_JOURNAL_STANDARD)
        assert set(result.keys()) == BULK_JOURNAL_ESSENTIAL

    def test_complete_task_quiet_mode(self):
        data = {
            'success': True,
            'task_id': 'task-10',
            'completed_at': '2025-11-20T10:00:00Z',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), COMPLETE_TASK_ESSENTIAL, COMPLETE_TASK_STANDARD)
        assert set(result.keys()) == COMPLETE_TASK_ESSENTIAL

    def test_create_task_commit_quiet_mode(self):
        data = {
            'success': True,
            'commit_hash': 'abc123',
            'task_id': 'task-10',
            'files_committed': ['src/app.py'],
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET),
            CREATE_TASK_COMMIT_ESSENTIAL, CREATE_TASK_COMMIT_STANDARD
        )
        assert set(result.keys()) == CREATE_TASK_COMMIT_ESSENTIAL


class TestMonitoringCommandsVerbosity:
    def test_check_journaling_quiet_mode(self):
        data = {
            'needs_journaling': True,
            'task_count': 3,
            'tasks': ['task-1'],
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET),
            CHECK_JOURNALING_ESSENTIAL, CHECK_JOURNALING_STANDARD
        )
        assert set(result.keys()) == CHECK_JOURNALING_ESSENTIAL

    def test_check_complete_quiet_mode(self):
        data = {
            'complete': False,
            'node_id': 'phase-2',
            'total_tasks': 10,
            'percentage': 80,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), CHECK_COMPLETE_ESSENTIAL, CHECK_COMPLETE_STANDARD)
        assert set(result.keys()) == CHECK_COMPLETE_ESSENTIAL

    def test_check_environment_quiet_mode(self):
        data = {
            'status': 'ok',
            'details': 'All env vars present',
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET),
            CHECK_ENVIRONMENT_ESSENTIAL, CHECK_ENVIRONMENT_STANDARD
        )
        assert set(result.keys()) == CHECK_ENVIRONMENT_ESSENTIAL

    def test_init_env_quiet_mode(self):
        data = {
            'success': True,
            'spec_id': 'spec-1',
            'variables': ['SPEC_ID'],
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), INIT_ENV_ESSENTIAL, INIT_ENV_STANDARD)
        assert set(result.keys()) == INIT_ENV_ESSENTIAL


class TestReportingVerbosity:
    def test_get_task_quiet_mode(self):
        data = {
            'task_id': 'task-1',
            'title': 'Implement login',
            'status': 'pending',
            'metadata': {'file_path': 'src/auth/login.py'},
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), GET_TASK_ESSENTIAL, GET_TASK_STANDARD)
        assert 'metadata' not in result

    def test_get_journal_quiet_mode(self):
        data = {
            'entries': [{'id': 'journal-1'}],
            'spec_id': 'spec-1',
            'count': 1,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), GET_JOURNAL_ESSENTIAL, GET_JOURNAL_STANDARD)
        assert set(result.keys()) == GET_JOURNAL_ESSENTIAL

    def test_list_phases_quiet_mode(self):
        data = {
            'phases': [{'id': 'phase-1'}],
            'spec_id': 'spec-1',
            'total_phases': 3,
            'current_phase': 'phase-2',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), LIST_PHASES_ESSENTIAL, LIST_PHASES_STANDARD)
        assert set(result.keys()) == LIST_PHASES_ESSENTIAL

    def test_phase_time_quiet_mode(self):
        data = {
            'phase_id': 'phase-1',
            'total_hours': 12,
            'estimated_hours': 15,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), PHASE_TIME_ESSENTIAL, PHASE_TIME_STANDARD)
        assert set(result.keys()) == PHASE_TIME_ESSENTIAL

    def test_status_report_quiet_mode(self):
        data = {
            'spec_id': 'spec-1',
            'status': 'in_progress',
            'progress': {'percentage': 40},
            'blockers': [],
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), STATUS_REPORT_ESSENTIAL, STATUS_REPORT_STANDARD)
        assert set(result.keys()) == STATUS_REPORT_ESSENTIAL

    def test_time_report_quiet_mode(self):
        data = {
            'spec_id': 'spec-1',
            'total_hours': 30,
            'estimated_hours': 45,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), TIME_REPORT_ESSENTIAL, TIME_REPORT_STANDARD)
        assert set(result.keys()) == TIME_REPORT_ESSENTIAL


class TestEstimateAndFrontmatterVerbosity:
    def test_update_estimate_quiet_mode(self):
        data = {
            'success': True,
            'task_id': 'task-1',
            'old_estimate': 5,
            'new_estimate': 8,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), UPDATE_ESTIMATE_ESSENTIAL, UPDATE_ESTIMATE_STANDARD)
        assert set(result.keys()) == UPDATE_ESTIMATE_ESSENTIAL

    def test_update_frontmatter_quiet_mode(self):
        data = {
            'success': True,
            'spec_id': 'spec-1',
            'updated_fields': ['title'],
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET),
            UPDATE_FRONTMATTER_ESSENTIAL, UPDATE_FRONTMATTER_STANDARD
        )
        assert set(result.keys()) == UPDATE_FRONTMATTER_ESSENTIAL


class TestAuditAndReconcileVerbosity:
    def test_audit_spec_quiet_mode(self):
        data = {
            'spec_id': 'spec-5',
            'issues': ['missing tasks'],
            'warnings': ['stale metadata'],
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), AUDIT_SPEC_ESSENTIAL, AUDIT_SPEC_STANDARD)
        assert set(result.keys()) == AUDIT_SPEC_ESSENTIAL

    def test_reconcile_state_quiet_mode(self):
        data = {
            'success': True,
            'changes_made': 4,
            'spec_id': 'spec-5',
            'issues_fixed': ['task mismatch'],
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET),
            RECONCILE_STATE_ESSENTIAL, RECONCILE_STATE_STANDARD
        )
        assert set(result.keys()) == RECONCILE_STATE_ESSENTIAL
    AUDIT_SPEC_ESSENTIAL,
    AUDIT_SPEC_STANDARD,
    RECONCILE_STATE_ESSENTIAL,
    RECONCILE_STATE_STANDARD,
