"""Verbosity tests for sdd-update command field sets."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    UPDATE_STATUS_ESSENTIAL,
    UPDATE_STATUS_STANDARD,
    MARK_BLOCKED_ESSENTIAL,
    MARK_BLOCKED_STANDARD,
    UNBLOCK_TASK_ESSENTIAL,
    UNBLOCK_TASK_STANDARD,
    ADD_JOURNAL_ESSENTIAL,
    ADD_JOURNAL_STANDARD,
    MOVE_SPEC_ESSENTIAL,
    MOVE_SPEC_STANDARD,
    ACTIVATE_SPEC_ESSENTIAL,
    ACTIVATE_SPEC_STANDARD,
    COMPLETE_SPEC_ESSENTIAL,
    COMPLETE_SPEC_STANDARD,
    SYNC_METADATA_ESSENTIAL,
    SYNC_METADATA_STANDARD,
    UPDATE_TASK_METADATA_ESSENTIAL,
    UPDATE_TASK_METADATA_STANDARD,
)


def _quiet_args():
    return argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)


def _verbose_args():
    return argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)


class TestUpdateStatusVerbosity:
    def test_quiet_mode_only_returns_new_status(self):
        data = {
            'success': True,
            'task_id': 'task-1-2',
            'new_status': 'completed',
            'old_status': 'in_progress',
            'spec_id': 'spec-123',
            'status_note': 'Done',
            'updated_at': '2025-11-18T10:00:00Z',
        }
        result = prepare_output(data, _quiet_args(), UPDATE_STATUS_ESSENTIAL, UPDATE_STATUS_STANDARD)
        assert set(result.keys()) == UPDATE_STATUS_ESSENTIAL

    def test_verbose_mode_includes_metadata(self):
        data = {
            'success': True,
            'task_id': 'task-1-2',
            'new_status': 'completed',
            'old_status': 'in_progress',
            'spec_id': 'spec-123',
            'status_note': 'Done',
            'updated_at': '2025-11-18T10:00:00Z',
        }
        result = prepare_output(data, _verbose_args(), UPDATE_STATUS_ESSENTIAL, UPDATE_STATUS_STANDARD)
        assert 'old_status' in result
        assert 'status_note' in result
        assert 'spec_id' in result


class TestBlockerCommandsVerbosity:
    def test_mark_blocked_quiet_mode(self):
        data = {
            'success': True,
            'task_id': 'task-3-1',
            'spec_id': 'spec-1',
            'blocked_by': ['task-2-1'],
            'reason': 'Waiting on schema',
            'marked_at': '2025-11-17T09:00:00Z',
        }
        result = prepare_output(data, _quiet_args(), MARK_BLOCKED_ESSENTIAL, MARK_BLOCKED_STANDARD)
        assert set(result.keys()) == MARK_BLOCKED_ESSENTIAL

    def test_unblock_task_quiet_mode(self):
        data = {
            'success': True,
            'task_id': 'task-3-1',
            'spec_id': 'spec-1',
            'unblocked_at': '2025-11-18T12:00:00Z',
            'previously_blocked_by': ['task-2-1'],
        }
        result = prepare_output(data, _quiet_args(), UNBLOCK_TASK_ESSENTIAL, UNBLOCK_TASK_STANDARD)
        assert set(result.keys()) == UNBLOCK_TASK_ESSENTIAL


class TestJournalVerbosity:
    def test_add_journal_quiet(self):
        data = {
            'success': True,
            'entry_id': 'journal-10',
            'spec_id': 'spec-2',
            'task_id': 'task-2-1',
            'timestamp': '2025-11-18T10:00:00Z',
            'entry_text': 'Documented decision',
        }
        result = prepare_output(data, _quiet_args(), ADD_JOURNAL_ESSENTIAL, ADD_JOURNAL_STANDARD)
        assert set(result.keys()) == ADD_JOURNAL_ESSENTIAL


class TestSpecStateVerbosity:
    def test_move_spec_quiet_mode(self):
        data = {
            'success': True,
            'spec_id': 'spec-3',
            'new_location': 'active',
            'old_location': 'pending',
            'moved_at': '2025-11-18T13:00:00Z',
            'backup_created': True,
        }
        result = prepare_output(data, _quiet_args(), MOVE_SPEC_ESSENTIAL, MOVE_SPEC_STANDARD)
        assert set(result.keys()) == MOVE_SPEC_ESSENTIAL

    def test_activate_spec_quiet_mode(self):
        data = {
            'success': True,
            'spec_id': 'spec-3',
            'old_folder': 'pending',
            'new_folder': 'active',
            'activated_at': '2025-11-18T13:05:00Z',
        }
        result = prepare_output(data, _quiet_args(), ACTIVATE_SPEC_ESSENTIAL, ACTIVATE_SPEC_STANDARD)
        assert set(result.keys()) == ACTIVATE_SPEC_ESSENTIAL

    def test_complete_spec_quiet_mode(self):
        data = {
            'success': True,
            'spec_id': 'spec-3',
            'completed_at': '2025-11-18T13:10:00Z',
            'total_tasks': 40,
            'completion_time': '7d',
            'moved_to': 'completed',
        }
        result = prepare_output(data, _quiet_args(), COMPLETE_SPEC_ESSENTIAL, COMPLETE_SPEC_STANDARD)
        assert set(result.keys()) == COMPLETE_SPEC_ESSENTIAL


class TestMetadataVerbosity:
    def test_sync_metadata_quiet_mode(self):
        data = {
            'success': True,
            'spec_id': 'spec-4',
            'synced_fields': ['time_tracking'],
            'updated_at': '2025-11-18T14:00:00Z',
            'changes_made': 3,
        }
        result = prepare_output(data, _quiet_args(), SYNC_METADATA_ESSENTIAL, SYNC_METADATA_STANDARD)
        assert set(result.keys()) == SYNC_METADATA_ESSENTIAL

    def test_update_task_metadata_quiet_mode(self):
        data = {
            'success': True,
            'task_id': 'task-4-1',
            'spec_id': 'spec-4',
            'updated_fields': ['metadata.notes'],
            'updated_at': '2025-11-18T14:05:00Z',
            'metadata': {'notes': 'Need review'},
        }
        result = prepare_output(data, _quiet_args(), UPDATE_TASK_METADATA_ESSENTIAL, UPDATE_TASK_METADATA_STANDARD)
        assert set(result.keys()) == UPDATE_TASK_METADATA_ESSENTIAL
