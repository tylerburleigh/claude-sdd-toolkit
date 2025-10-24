"""
Unit tests for sdd_start_helper.py enhanced session resumption features.

Tests the integration of get_session_state() in the sdd_start_helper script,
specifically the new get_session_info command and enhanced format_output.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add dev_tools to path for imports
dev_tools_path = Path(__file__).parent.parent.parent.parent / "dev_tools"
sys.path.insert(0, str(dev_tools_path))

import sdd_start_helper


class TestGetSessionInfo:
    """Tests for get_session_info command."""

    @patch("sdd_start_helper.get_session_state")
    def test_get_session_info_with_last_task(self, mock_get_state, tmp_path, capsys):
        """Test get_session_info returns session state with last task."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        # Mock get_session_state return value
        mock_get_state.return_value = {
            "active_specs": [
                {
                    "spec_id": "test-001",
                    "title": "Test Feature",
                    "status": "in_progress",
                    "in_progress_tasks": 2
                }
            ],
            "last_task": {
                "spec_id": "test-001",
                "task_id": "task-1-1",
                "title": "Implement auth",
                "modified": "2025-10-23T14:30:00"
            },
            "timestamp": "2025-10-23T14:30:00",
            "in_progress_count": 2
        }

        # Execute command
        result = sdd_start_helper.get_session_info(str(tmp_path))

        # Check result
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["has_specs"] is True
        assert output["last_task"]["task_id"] == "task-1-1"
        assert output["in_progress_count"] == 2
        assert len(output["active_specs"]) == 1
        assert result == 0

    @patch("sdd_start_helper.get_session_state")
    def test_get_session_info_no_last_task(self, mock_get_state, tmp_path, capsys):
        """Test get_session_info when no in-progress tasks exist."""
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        # Mock get_session_state with no last task
        mock_get_state.return_value = {
            "active_specs": [
                {
                    "spec_id": "test-001",
                    "title": "Test Feature",
                    "status": "pending",
                    "in_progress_tasks": 0
                }
            ],
            "last_task": None,
            "timestamp": None,
            "in_progress_count": 0
        }

        result = sdd_start_helper.get_session_info(str(tmp_path))

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["has_specs"] is True
        assert output["last_task"] is None
        assert output["in_progress_count"] == 0
        assert result == 0

    def test_get_session_info_no_specs_dir(self, tmp_path, capsys):
        """Test get_session_info when specs directory doesn't exist."""
        result = sdd_start_helper.get_session_info(str(tmp_path))

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["has_specs"] is False
        assert "No specs directory found" in output["message"]
        assert result == 0


class TestFormatOutputEnhanced:
    """Tests for enhanced format_output with last-accessed task info."""

    @patch("sdd_start_helper.get_session_state")
    def test_format_output_shows_last_task(self, mock_get_state, tmp_path, capsys):
        """Test that format_output displays last-accessed task info."""
        # Setup test directories
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create test spec file
        spec_file = active_dir / "test-001.json"
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "spec-root": {
                    "title": "Test Feature",
                    "completed_tasks": 3,
                    "total_tasks": 10,
                    "status": "in_progress"
                }
            }
        }
        spec_file.write_text(json.dumps(spec_data))

        # Mock get_session_state
        mock_get_state.return_value = {
            "active_specs": [
                {
                    "spec_id": "test-001",
                    "title": "Test Feature",
                    "status": "in_progress",
                    "in_progress_tasks": 1
                }
            ],
            "last_task": {
                "spec_id": "test-001",
                "task_id": "task-1-1",
                "title": "Implement auth",
                "modified": "2025-10-23T14:30:00"
            },
            "timestamp": "2025-10-23T14:30:00",
            "in_progress_count": 1
        }

        # Execute command
        result = sdd_start_helper.format_output(str(tmp_path))

        # Check output
        captured = capsys.readouterr()
        output = captured.out

        assert "Test Feature" in output
        assert "test-001" in output
        assert "3/10 tasks (30%)" in output
        assert "🕐 Last accessed task:" in output
        assert "task-1-1 - Implement auth" in output
        assert "💡 1 task currently in progress" in output
        assert result == 0

    @patch("sdd_start_helper.get_session_state")
    def test_format_output_no_last_task(self, mock_get_state, tmp_path, capsys):
        """Test format_output when no last-accessed task exists."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create test spec file
        spec_file = active_dir / "test-001.json"
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "spec-root": {
                    "title": "Test Feature",
                    "completed_tasks": 0,
                    "total_tasks": 5,
                    "status": "pending"
                }
            }
        }
        spec_file.write_text(json.dumps(spec_data))

        # Mock get_session_state with no last task
        mock_get_state.return_value = {
            "active_specs": [],
            "last_task": None,
            "timestamp": None,
            "in_progress_count": 0
        }

        result = sdd_start_helper.format_output(str(tmp_path))

        captured = capsys.readouterr()
        output = captured.out

        # Should show spec but not last task info
        assert "Test Feature" in output
        assert "🕐 Last accessed task:" not in output
        assert "💡" not in output or "0 task" not in output
        assert result == 0

    def test_format_output_no_active_specs(self, tmp_path, capsys):
        """Test format_output when no active specs exist."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        result = sdd_start_helper.format_output(str(tmp_path))

        captured = capsys.readouterr()
        output = captured.out

        assert "No active SDD work found" in output
        assert result == 0

    def test_format_output_no_specs_directory(self, tmp_path, capsys):
        """Test format_output when specs directory doesn't exist."""
        result = sdd_start_helper.format_output(str(tmp_path))

        captured = capsys.readouterr()
        output = captured.out

        assert "No active SDD work found" in output
        assert result == 0


class TestIntegrationWithGetSessionState:
    """Integration tests to ensure sdd_start_helper properly uses get_session_state."""

    @patch("sdd_start_helper.get_session_state")
    def test_get_session_state_called_with_correct_path(self, mock_get_state, tmp_path):
        """Test that get_session_state is called with the correct specs directory."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        mock_get_state.return_value = {
            "active_specs": [],
            "last_task": None,
            "timestamp": None,
            "in_progress_count": 0
        }

        # Call both commands
        sdd_start_helper.get_session_info(str(tmp_path))
        sdd_start_helper.format_output(str(tmp_path))

        # Verify get_session_state was called with correct path
        assert mock_get_state.call_count == 2
        calls = mock_get_state.call_args_list
        assert str(specs_dir) in calls[0][0][0]
        assert str(specs_dir) in calls[1][0][0]

    @patch("sdd_start_helper.get_session_state")
    def test_multiple_in_progress_tasks_display(self, mock_get_state, tmp_path, capsys):
        """Test displaying multiple in-progress tasks."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create test spec
        spec_file = active_dir / "test-001.json"
        spec_data = {
            "spec_id": "test-001",
            "hierarchy": {
                "spec-root": {
                    "title": "Test Feature",
                    "completed_tasks": 5,
                    "total_tasks": 15,
                    "status": "in_progress"
                }
            }
        }
        spec_file.write_text(json.dumps(spec_data))

        mock_get_state.return_value = {
            "active_specs": [
                {
                    "spec_id": "test-001",
                    "title": "Test Feature",
                    "status": "in_progress",
                    "in_progress_tasks": 3
                }
            ],
            "last_task": {
                "spec_id": "test-001",
                "task_id": "task-2-1",
                "title": "Implement feature X",
                "modified": "2025-10-23T10:00:00"
            },
            "timestamp": "2025-10-23T10:00:00",
            "in_progress_count": 3
        }

        sdd_start_helper.format_output(str(tmp_path))

        captured = capsys.readouterr()
        output = captured.out

        assert "💡 3 tasks currently in progress" in output
        assert "task-2-1 - Implement feature X" in output
