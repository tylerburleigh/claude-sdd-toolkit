"""
Unit tests for apply-modifications CLI command.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from claude_skills.sdd_spec_mod.cli import cmd_apply_modifications


class TestCmdApplyModifications:
    """Test the cmd_apply_modifications CLI command."""

    @pytest.fixture
    def mock_printer(self):
        """Create a mock PrettyPrinter."""
        printer = Mock()
        printer.info = Mock()
        printer.error = Mock()
        printer.success = Mock()
        printer.detail = Mock()
        printer.warning = Mock()
        printer.header = Mock()
        return printer

    @pytest.fixture
    def sample_spec(self):
        """Create a sample spec data structure."""
        return {
            "spec_id": "test-spec-001",
            "title": "Test Specification",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "children": ["phase-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0
                },
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "parent": "spec-root",
                    "children": ["task-1-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0
                },
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1.1",
                    "parent": "phase-1",
                    "children": [],
                    "status": "pending",
                    "description": "Original description",
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []}
                }
            }
        }

    @pytest.fixture
    def sample_modifications(self):
        """Create a sample modifications file content."""
        return {
            "modifications": [
                {
                    "operation": "update_node_field",
                    "node_id": "task-1-1",
                    "field": "description",
                    "value": "Updated description"
                }
            ]
        }

    @patch('claude_skills.sdd_spec_mod.cli.find_specs_directory')
    @patch('claude_skills.sdd_spec_mod.cli.find_spec_file')
    def test_specs_directory_not_found(self, mock_find_spec, mock_find_specs_dir, mock_printer):
        """Test error when specs directory not found."""
        mock_find_specs_dir.return_value = None
        args = Mock(spec_id="test-spec-001", from_file="mods.json", specs_dir=None, path='.')

        result = cmd_apply_modifications(args, mock_printer)

        assert result == 1
        mock_printer.error.assert_called_with("Specs directory not found")

    @patch('claude_skills.sdd_spec_mod.cli.find_specs_directory')
    @patch('claude_skills.sdd_spec_mod.cli.find_spec_file')
    def test_spec_file_not_found(self, mock_find_spec, mock_find_specs_dir, mock_printer):
        """Test error when spec file not found."""
        mock_find_specs_dir.return_value = Path("/fake/specs")
        mock_find_spec.return_value = None
        args = Mock(spec_id="missing-spec", from_file="mods.json", specs_dir=None, path='.')

        result = cmd_apply_modifications(args, mock_printer)

        assert result == 1
        mock_printer.error.assert_called_with("Spec file not found for: missing-spec")

    @patch('claude_skills.sdd_spec_mod.cli.find_specs_directory')
    @patch('claude_skills.sdd_spec_mod.cli.find_spec_file')
    def test_modifications_file_not_found(self, mock_find_spec, mock_find_specs_dir, mock_printer):
        """Test error when modifications file not found."""
        mock_find_specs_dir.return_value = Path("/fake/specs")
        mock_find_spec.return_value = Path("/fake/specs/active/test-spec-001.json")
        args = Mock(
            spec_id="test-spec-001",
            from_file="/nonexistent/mods.json",
            specs_dir=None,
            path='.'
        )

        result = cmd_apply_modifications(args, mock_printer)

        assert result == 1
        mock_printer.error.assert_called_with("Modifications file not found: /nonexistent/mods.json")

    @patch('claude_skills.sdd_spec_mod.cli.find_specs_directory')
    @patch('claude_skills.sdd_spec_mod.cli.find_spec_file')
    @patch('claude_skills.sdd_spec_mod.cli.load_json_spec')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_dry_run_mode(self, mock_file, mock_path_cls, mock_load_spec, mock_find_spec, mock_find_specs_dir, mock_printer, sample_spec, sample_modifications):
        """Test dry-run mode previews changes without applying."""
        mock_find_specs_dir.return_value = Path("/fake/specs")
        mock_find_spec.return_value = Path("/fake/specs/active/test-spec-001.json")
        mock_load_spec.return_value = sample_spec

        # Mock Path.exists() to return True for modifications file
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        # Mock file reading for modifications
        mock_file.return_value.read.return_value = json.dumps(sample_modifications)
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(sample_modifications)

        args = Mock(
            spec_id="test-spec-001",
            from_file="/fake/mods.json",
            dry_run=True,
            output=None,
            specs_dir=None,
            path='.'
        )

        result = cmd_apply_modifications(args, mock_printer)

        assert result == 0
        # Verify no changes message
        assert any("No changes were made" in str(call) for call in mock_printer.info.call_args_list)

    @patch('claude_skills.sdd_spec_mod.cli.find_specs_directory')
    @patch('claude_skills.sdd_spec_mod.cli.find_spec_file')
    @patch('claude_skills.sdd_spec_mod.cli.load_json_spec')
    @patch('claude_skills.sdd_spec_mod.cli.apply_modifications')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_successful_application(self, mock_file, mock_path_cls, mock_apply, mock_load_spec, mock_find_spec, mock_find_specs_dir, mock_printer, sample_spec):
        """Test successful application of modifications."""
        mock_find_specs_dir.return_value = Path("/fake/specs")
        spec_file_path = Path("/fake/specs/active/test-spec-001.json")
        mock_find_spec.return_value = spec_file_path
        mock_load_spec.return_value = sample_spec

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        # Mock successful apply_modifications result
        mock_apply.return_value = {
            "success": True,
            "total_operations": 1,
            "successful": 1,
            "failed": 0,
            "results": [
                {
                    "operation": {"operation": "update_node_field"},
                    "success": True,
                    "message": "Updated field"
                }
            ]
        }

        args = Mock(
            spec_id="test-spec-001",
            from_file="/fake/mods.json",
            dry_run=False,
            output=None,
            specs_dir=None,
            path='.'
        )

        result = cmd_apply_modifications(args, mock_printer)

        assert result == 0
        mock_printer.success.assert_called()

    @patch('claude_skills.sdd_spec_mod.cli.find_specs_directory')
    @patch('claude_skills.sdd_spec_mod.cli.find_spec_file')
    @patch('claude_skills.sdd_spec_mod.cli.load_json_spec')
    @patch('claude_skills.sdd_spec_mod.cli.apply_modifications')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    def test_partial_failure(self, mock_path_cls, mock_apply, mock_load_spec, mock_find_spec, mock_find_specs_dir, mock_printer, sample_spec):
        """Test handling of partial failures."""
        mock_find_specs_dir.return_value = Path("/fake/specs")
        mock_find_spec.return_value = Path("/fake/specs/active/test-spec-001.json")
        mock_load_spec.return_value = sample_spec

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        # Mock partial failure result
        mock_apply.return_value = {
            "success": False,
            "total_operations": 2,
            "successful": 1,
            "failed": 1,
            "results": [
                {
                    "operation": {"operation": "update_node_field"},
                    "success": True
                },
                {
                    "operation": {"operation": "add_node"},
                    "success": False,
                    "error": "Node already exists"
                }
            ]
        }

        args = Mock(
            spec_id="test-spec-001",
            from_file="/fake/mods.json",
            dry_run=False,
            output=None,
            specs_dir=None,
            path='.'
        )

        with patch('builtins.open', mock_open()):
            result = cmd_apply_modifications(args, mock_printer)

        assert result == 1
        mock_printer.warning.assert_called()
        mock_printer.error.assert_called()  # For failed operations
