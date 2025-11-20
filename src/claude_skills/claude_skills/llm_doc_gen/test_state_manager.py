"""
Tests for state_manager module.
"""

import pytest
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime

from .state_manager import (
    StateManager,
    DocumentationState,
    FileProcessingState,
    ProcessingStatus,
    create_state_manager
)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def state_manager(temp_output_dir):
    """Create a StateManager instance."""
    return StateManager(temp_output_dir, verbose=False)


class TestFileProcessingState:
    """Tests for FileProcessingState."""

    def test_to_dict(self):
        """Test converting FileProcessingState to dictionary."""
        state = FileProcessingState(
            file_path="/path/to/file.py",
            status=ProcessingStatus.COMPLETED,
            language="python",
            entity_count=5
        )
        result = state.to_dict()

        assert result['file_path'] == "/path/to/file.py"
        assert result['status'] == "completed"
        assert result['language'] == "python"
        assert result['entity_count'] == 5

    def test_from_dict(self):
        """Test creating FileProcessingState from dictionary."""
        data = {
            'file_path': "/path/to/file.py",
            'status': "pending",
            'language': "python",
            'entity_count': 3
        }
        state = FileProcessingState.from_dict(data)

        assert state.file_path == "/path/to/file.py"
        assert state.status == ProcessingStatus.PENDING
        assert state.language == "python"
        assert state.entity_count == 3

    def test_round_trip(self):
        """Test converting to dict and back."""
        original = FileProcessingState(
            file_path="/test/file.js",
            status=ProcessingStatus.IN_PROGRESS,
            language="javascript"
        )
        data = original.to_dict()
        restored = FileProcessingState.from_dict(data)

        assert restored.file_path == original.file_path
        assert restored.status == original.status
        assert restored.language == original.language


class TestDocumentationState:
    """Tests for DocumentationState."""

    def test_to_dict(self, temp_project_dir, temp_output_dir):
        """Test converting DocumentationState to dictionary."""
        state = DocumentationState(
            project_root=str(temp_project_dir),
            output_folder=str(temp_output_dir),
            session_id="test_session",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )

        file_state = FileProcessingState(
            file_path="test.py",
            status=ProcessingStatus.COMPLETED
        )
        state.files["test.py"] = file_state
        state.languages_detected = ["python"]
        state.total_files = 1

        result = state.to_dict()

        assert result['session_id'] == "test_session"
        assert "test.py" in result['files']
        assert result['languages_detected'] == ["python"]
        assert result['total_files'] == 1

    def test_from_dict(self, temp_project_dir, temp_output_dir):
        """Test creating DocumentationState from dictionary."""
        data = {
            'project_root': str(temp_project_dir),
            'output_folder': str(temp_output_dir),
            'session_id': "test_session",
            'created_at': "2024-01-01T00:00:00",
            'updated_at': "2024-01-01T00:00:00",
            'files': {
                'test.py': {
                    'file_path': 'test.py',
                    'status': 'completed',
                    'language': 'python',
                    'entity_count': 5
                }
            },
            'languages_detected': ['python'],
            'total_files': 1
        }

        state = DocumentationState.from_dict(data)

        assert state.session_id == "test_session"
        assert "test.py" in state.files
        assert state.files["test.py"].status == ProcessingStatus.COMPLETED
        assert state.languages_detected == ['python']
        assert state.total_files == 1


class TestStateManager:
    """Tests for StateManager."""

    def test_initialization(self, temp_output_dir):
        """Test StateManager initialization."""
        manager = StateManager(temp_output_dir)

        assert manager.output_folder.resolve() == temp_output_dir.resolve()
        assert manager.state_file.resolve() == (temp_output_dir / "doc-gen-state.json").resolve()
        assert temp_output_dir.exists()

    def test_create_new_state(self, state_manager, temp_project_dir):
        """Test creating a new state."""
        state = state_manager.create_new_state(
            project_root=temp_project_dir,
            session_id="test_123",
            exclude_patterns=["*.pyc", "__pycache__"]
        )

        assert state.session_id == "test_123"
        assert state.project_root == str(temp_project_dir.resolve())
        assert state.exclude_patterns == ["*.pyc", "__pycache__"]
        assert state.total_files == 0
        assert state.completed_files == 0

    def test_save_and_load_state(self, state_manager, temp_project_dir):
        """Test saving and loading state."""
        # Create and save state
        state = state_manager.create_new_state(
            project_root=temp_project_dir,
            session_id="test_save_load"
        )
        state.total_files = 10
        state.languages_detected = ["python", "javascript"]

        state_manager.save_state(state)
        assert state_manager.state_file.exists()

        # Load state
        loaded_state = state_manager.load_state()

        assert loaded_state is not None
        assert loaded_state.session_id == "test_save_load"
        assert loaded_state.total_files == 10
        assert loaded_state.languages_detected == ["python", "javascript"]

    def test_state_exists(self, state_manager, temp_project_dir):
        """Test checking if state exists."""
        assert not state_manager.state_exists()

        # Create and save state
        state = state_manager.create_new_state(temp_project_dir)
        state_manager.save_state(state)

        assert state_manager.state_exists()

    def test_load_nonexistent_state(self, state_manager):
        """Test loading when no state file exists."""
        state = state_manager.load_state()
        assert state is None

    def test_atomic_write_with_backup(self, state_manager, temp_project_dir):
        """Test that saves create backups."""
        # Create and save initial state
        state = state_manager.create_new_state(temp_project_dir)
        state.total_files = 5
        state_manager.save_state(state)

        # Modify and save again
        state.total_files = 10
        state_manager.save_state(state)

        # Backup should exist
        assert state_manager.backup_file.exists()

        # Load backup and verify it has old value
        with open(state_manager.backup_file, 'r') as f:
            backup_data = json.load(f)
        assert backup_data['total_files'] == 5

    def test_delete_state(self, state_manager, temp_project_dir):
        """Test deleting state file."""
        # Create and save state
        state = state_manager.create_new_state(temp_project_dir)
        state_manager.save_state(state)
        assert state_manager.state_file.exists()

        # Delete state (keeping backup)
        state_manager.delete_state(keep_backup=True)
        assert not state_manager.state_file.exists()
        assert state_manager.backup_file.exists()

    def test_update_file_status(self, state_manager, temp_project_dir):
        """Test updating file status."""
        state = state_manager.create_new_state(temp_project_dir)
        state.total_files = 1

        # Update to in_progress
        state_manager.update_file_status(
            state,
            file_path="test.py",
            status=ProcessingStatus.IN_PROGRESS
        )

        assert "test.py" in state.files
        assert state.files["test.py"].status == ProcessingStatus.IN_PROGRESS
        assert state.files["test.py"].processing_started is not None

        # Update to completed
        state_manager.update_file_status(
            state,
            file_path="test.py",
            status=ProcessingStatus.COMPLETED,
            entity_count=5
        )

        assert state.files["test.py"].status == ProcessingStatus.COMPLETED
        assert state.files["test.py"].processing_completed is not None
        assert state.files["test.py"].entity_count == 5
        assert state.completed_files == 1

    def test_update_file_status_with_error(self, state_manager, temp_project_dir):
        """Test updating file status with error."""
        state = state_manager.create_new_state(temp_project_dir)
        state.total_files = 1

        state_manager.update_file_status(
            state,
            file_path="broken.py",
            status=ProcessingStatus.FAILED,
            error_message="Parse error"
        )

        assert state.files["broken.py"].status == ProcessingStatus.FAILED
        assert state.files["broken.py"].error_message == "Parse error"
        assert state.failed_files == 1

    def test_get_resumable_files(self, state_manager, temp_project_dir):
        """Test getting resumable files."""
        state = state_manager.create_new_state(temp_project_dir)

        # Add files with different statuses
        state.files["completed.py"] = FileProcessingState(
            file_path="completed.py",
            status=ProcessingStatus.COMPLETED
        )
        state.files["pending.py"] = FileProcessingState(
            file_path="pending.py",
            status=ProcessingStatus.PENDING
        )
        state.files["failed.py"] = FileProcessingState(
            file_path="failed.py",
            status=ProcessingStatus.FAILED
        )
        state.files["skipped.py"] = FileProcessingState(
            file_path="skipped.py",
            status=ProcessingStatus.SKIPPED
        )

        resumable = state_manager.get_resumable_files(state)

        assert len(resumable) == 2
        assert "pending.py" in resumable
        assert "failed.py" in resumable
        assert "completed.py" not in resumable
        assert "skipped.py" not in resumable

    def test_get_progress_summary(self, state_manager, temp_project_dir):
        """Test getting progress summary."""
        state = state_manager.create_new_state(temp_project_dir)
        state.total_files = 10
        state.completed_files = 6
        state.failed_files = 2
        state.skipped_files = 1
        state.languages_detected = ["python", "javascript"]
        state.current_phase = "parsing"
        state.phases_completed = ["discovery"]

        summary = state_manager.get_progress_summary(state)

        assert summary['total_files'] == 10
        assert summary['completed'] == 6
        assert summary['failed'] == 2
        assert summary['skipped'] == 1
        assert summary['pending'] == 1
        assert summary['percentage'] == 60.0
        assert summary['languages'] == ["python", "javascript"]
        assert summary['current_phase'] == "parsing"
        assert summary['phases_completed'] == ["discovery"]

    def test_restore_from_backup(self, state_manager, temp_project_dir):
        """Test restoring from backup when main state is corrupted."""
        # Create and save valid state (this creates no backup yet)
        state = state_manager.create_new_state(temp_project_dir, session_id="backup_test")
        state.total_files = 42
        state_manager.save_state(state)

        # Save again to create a backup
        state.total_files = 50
        state_manager.save_state(state)

        # Now backup exists with total_files=42, current has total_files=50
        # Verify backup was created
        assert state_manager.backup_file.exists()

        # Corrupt the main state file
        with open(state_manager.state_file, 'w') as f:
            f.write("{ invalid json")

        # Load should restore from backup (which has total_files=42)
        loaded_state = state_manager.load_state()

        assert loaded_state is not None
        assert loaded_state.session_id == "backup_test"
        assert loaded_state.total_files == 42


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_state_manager(self, temp_output_dir):
        """Test create_state_manager convenience function."""
        manager = create_state_manager(str(temp_output_dir), verbose=True)

        assert isinstance(manager, StateManager)
        assert manager.output_folder.resolve() == temp_output_dir.resolve()
        assert manager.verbose is True


class TestWorkflowTracking:
    """Tests for workflow progress tracking."""

    def test_start_workflow_step(self, state_manager, temp_project_dir):
        """Test starting a workflow step."""
        state = state_manager.create_new_state(temp_project_dir)

        state_manager.start_workflow_step(state, "discovery")

        assert state.current_step == "discovery"
        assert "discovery" not in state.completed_steps

    def test_complete_workflow_step(self, state_manager, temp_project_dir):
        """Test completing a workflow step."""
        state = state_manager.create_new_state(temp_project_dir)

        state_manager.start_workflow_step(state, "discovery")
        state_manager.complete_workflow_step(state)

        assert state.current_step is None
        assert "discovery" in state.completed_steps
        assert "discovery" in state.step_timestamps

    def test_complete_specific_step(self, state_manager, temp_project_dir):
        """Test completing a specific step by name."""
        state = state_manager.create_new_state(temp_project_dir)

        state_manager.start_workflow_step(state, "step1")
        state_manager.start_workflow_step(state, "step2")
        state_manager.complete_workflow_step(state, "step1")

        assert state.current_step == "step2"
        assert "step1" in state.completed_steps
        assert "step2" not in state.completed_steps

    def test_complete_without_current_step_raises(self, state_manager, temp_project_dir):
        """Test that completing without a step raises error."""
        state = state_manager.create_new_state(temp_project_dir)

        with pytest.raises(ValueError, match="No step name provided"):
            state_manager.complete_workflow_step(state)

    def test_add_finding(self, state_manager, temp_project_dir):
        """Test adding a finding."""
        state = state_manager.create_new_state(temp_project_dir)
        state_manager.start_workflow_step(state, "analysis")

        state_manager.add_finding(
            state,
            finding_type="insight",
            description="Found 50 Python files",
            details={"file_count": 50}
        )

        assert len(state.findings) == 1
        finding = state.findings[0]
        assert finding['type'] == "insight"
        assert finding['description'] == "Found 50 Python files"
        assert finding['step'] == "analysis"
        assert finding['details']['file_count'] == 50
        assert 'timestamp' in finding

    def test_add_finding_with_explicit_step(self, state_manager, temp_project_dir):
        """Test adding a finding with explicit step name."""
        state = state_manager.create_new_state(temp_project_dir)

        state_manager.add_finding(
            state,
            finding_type="warning",
            description="Skipped binary files",
            step_name="scanning"
        )

        assert len(state.findings) == 1
        assert state.findings[0]['step'] == "scanning"

    def test_get_workflow_progress(self, state_manager, temp_project_dir):
        """Test getting workflow progress."""
        state = state_manager.create_new_state(temp_project_dir)

        # Simulate workflow
        state_manager.start_workflow_step(state, "step1")
        state_manager.complete_workflow_step(state)

        state_manager.start_workflow_step(state, "step2")
        state_manager.add_finding(state, "insight", "Found patterns")
        state_manager.add_finding(state, "warning", "Large file detected")
        state_manager.complete_workflow_step(state)

        progress = state_manager.get_workflow_progress(state)

        assert progress['current_step'] is None
        assert progress['completed_steps'] == ["step1", "step2"]
        assert progress['total_steps_completed'] == 2
        assert len(progress['step_timestamps']) == 2
        assert progress['findings_count'] == 2
        assert progress['findings_by_type'] == {"insight": 1, "warning": 1}

    def test_workflow_state_persistence(self, state_manager, temp_project_dir):
        """Test that workflow state persists across save/load."""
        state = state_manager.create_new_state(temp_project_dir)

        # Set up workflow state
        state_manager.start_workflow_step(state, "parsing")
        state_manager.complete_workflow_step(state, "discovery")
        state_manager.add_finding(state, "metric", "100 files found", {"count": 100})

        state_manager.save_state(state)

        # Load and verify
        loaded_state = state_manager.load_state()

        assert loaded_state.current_step == "parsing"
        assert "discovery" in loaded_state.completed_steps
        assert "discovery" in loaded_state.step_timestamps
        assert len(loaded_state.findings) == 1
        assert loaded_state.findings[0]['type'] == "metric"


class TestResumeDetection:
    """Tests for resume detection and user prompts."""

    def test_check_resume_available_no_state(self, state_manager):
        """Test resume check when no state exists."""
        assert not state_manager.check_resume_available()

    def test_check_resume_available_with_state(self, state_manager, temp_project_dir):
        """Test resume check when valid state exists."""
        state = state_manager.create_new_state(temp_project_dir)
        state_manager.save_state(state)

        assert state_manager.check_resume_available()

    def test_check_resume_available_corrupted_state(self, state_manager, temp_project_dir):
        """Test resume check with corrupted state file."""
        # Create corrupted state file
        with open(state_manager.state_file, 'w') as f:
            f.write("{ corrupted json")

        assert not state_manager.check_resume_available()

    def test_get_resume_info_no_state(self, state_manager):
        """Test getting resume info when no state exists."""
        info = state_manager.get_resume_info()
        assert info is None

    def test_get_resume_info_with_state(self, state_manager, temp_project_dir):
        """Test getting resume info with existing state."""
        state = state_manager.create_new_state(temp_project_dir, session_id="test_resume")
        state.total_files = 10
        state.completed_files = 6
        state.failed_files = 1
        state.languages_detected = ["python", "javascript"]

        # Add some workflow data
        state_manager.start_workflow_step(state, "parsing")
        state_manager.complete_workflow_step(state, "discovery")
        state_manager.add_finding(state, "insight", "Found patterns")

        # Add resumable files
        state.files["pending.py"] = FileProcessingState(
            file_path="pending.py",
            status=ProcessingStatus.PENDING
        )

        state_manager.save_state(state)

        info = state_manager.get_resume_info()

        assert info is not None
        assert info['session_id'] == "test_resume"
        assert info['can_resume'] is True
        assert info['progress']['total_files'] == 10
        assert info['progress']['completed'] == 6
        assert info['workflow']['current_step'] == "parsing"
        assert "discovery" in info['workflow']['completed_steps']
        assert 'time_ago' in info

    def test_get_resume_info_completed_session(self, state_manager, temp_project_dir):
        """Test resume info for a completed session."""
        state = state_manager.create_new_state(temp_project_dir)
        state.total_files = 2
        state.completed_files = 2

        # All files completed
        state.files["file1.py"] = FileProcessingState(
            file_path="file1.py",
            status=ProcessingStatus.COMPLETED
        )
        state.files["file2.py"] = FileProcessingState(
            file_path="file2.py",
            status=ProcessingStatus.COMPLETED
        )

        state_manager.save_state(state)

        info = state_manager.get_resume_info()

        assert info is not None
        assert info['can_resume'] is False  # No pending or failed files

    def test_format_resume_prompt_no_state(self, state_manager):
        """Test formatting resume prompt when no state exists."""
        prompt = state_manager.format_resume_prompt()
        assert prompt == ""

    def test_format_resume_prompt_with_state(self, state_manager, temp_project_dir):
        """Test formatting resume prompt with existing state."""
        state = state_manager.create_new_state(temp_project_dir, session_id="test_123")
        state.total_files = 20
        state.completed_files = 15
        state.failed_files = 2
        state.skipped_files = 1
        state.languages_detected = ["python", "javascript"]

        state_manager.start_workflow_step(state, "generation")
        state_manager.complete_workflow_step(state, "parsing")
        state_manager.add_finding(state, "insight", "Pattern detected")
        state_manager.add_finding(state, "warning", "Large file")

        # Add resumable file
        state.files["pending.py"] = FileProcessingState(
            file_path="pending.py",
            status=ProcessingStatus.PENDING
        )

        state_manager.save_state(state)

        prompt = state_manager.format_resume_prompt()

        assert prompt != ""
        assert "test_123" in prompt
        assert "15/20 completed" in prompt
        assert "python, javascript" in prompt
        assert "generation" in prompt  # current step
        assert "parsing" in prompt  # completed step
        assert "1 insight, 1 warning" in prompt or "1 warning, 1 insight" in prompt
        assert "Session can be resumed" in prompt

    def test_format_resume_prompt_completed_session(self, state_manager, temp_project_dir):
        """Test formatting prompt for completed session."""
        state = state_manager.create_new_state(temp_project_dir)
        state.total_files = 5
        state.completed_files = 5

        # All completed
        for i in range(5):
            state.files[f"file{i}.py"] = FileProcessingState(
                file_path=f"file{i}.py",
                status=ProcessingStatus.COMPLETED
            )

        state_manager.save_state(state)

        prompt = state_manager.format_resume_prompt()

        assert "All files processed - session appears complete" in prompt


class TestIntegration:
    """Integration tests for full workflows."""

    def test_full_workflow(self, state_manager, temp_project_dir):
        """Test complete workflow from creation to completion."""
        # Create new state
        state = state_manager.create_new_state(
            project_root=temp_project_dir,
            session_id="integration_test",
            exclude_patterns=["*.pyc"]
        )

        # Set up initial files
        files = ["file1.py", "file2.py", "file3.js"]
        state.total_files = len(files)

        for file in files:
            state.files[file] = FileProcessingState(
                file_path=file,
                status=ProcessingStatus.PENDING
            )

        state_manager.save_state(state)

        # Simulate processing
        state_manager.update_file_status(state, "file1.py", ProcessingStatus.IN_PROGRESS)
        state_manager.save_state(state)

        state_manager.update_file_status(
            state,
            "file1.py",
            ProcessingStatus.COMPLETED,
            entity_count=10
        )
        state_manager.save_state(state)

        state_manager.update_file_status(state, "file2.py", ProcessingStatus.IN_PROGRESS)
        state_manager.update_file_status(
            state,
            "file2.py",
            ProcessingStatus.FAILED,
            error_message="Parse error"
        )
        state_manager.save_state(state)

        # Check progress
        summary = state_manager.get_progress_summary(state)
        assert summary['completed'] == 1
        assert summary['failed'] == 1
        assert summary['pending'] == 1

        # Get resumable files
        resumable = state_manager.get_resumable_files(state)
        assert len(resumable) == 2  # file2.py (failed) and file3.js (pending)

        # Reload state from disk
        loaded_state = state_manager.load_state()
        assert loaded_state.session_id == "integration_test"
        assert loaded_state.completed_files == 1
        assert loaded_state.failed_files == 1
        assert "file1.py" in loaded_state.files
        assert loaded_state.files["file1.py"].entity_count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
