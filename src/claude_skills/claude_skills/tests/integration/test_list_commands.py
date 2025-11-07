"""
Integration tests for list commands with Rich table output.

Tests all list commands:
- list-specs: List all specifications with Rich.Table
- query-tasks: Query tasks with Rich.Table
- list-phases: List phases with Rich.Table
- check-deps: Show dependencies with Rich.Tree

Tests cover:
- Text/Rich output format (default)
- JSON output format (--format json)
- Output correctness and structure
- Empty result handling
"""

import sys
import pytest
import subprocess
import json
import shutil
from pathlib import Path

# Unified CLI command
CLI_CMD = "sdd"


def run_cli(*args, **kwargs):
    """
    Run sdd command with fallback to python -m if sdd not on PATH.

    Automatically reorders arguments to put global flags before subcommands.
    Global flags: --path, --specs-dir, --quiet, --json, --debug, --verbose, --no-color
    """
    # Define global flags that must come before subcommands
    global_flags_with_values = {'--path', '--specs-dir'}
    global_flags_boolean = {'--quiet', '-q', '--json', '--debug', '--verbose', '-v', '--no-color'}
    all_global_flags = global_flags_with_values | global_flags_boolean

    args_list = list(args)

    # Scan all args and separate global flags from subcommand and its args
    global_args = []
    non_global_args = []

    i = 0
    while i < len(args_list):
        arg = args_list[i]

        if arg in global_flags_with_values and i + 1 < len(args_list):
            # This is a global flag with a value
            global_args.append(arg)
            global_args.append(args_list[i + 1])
            i += 2
        elif arg in global_flags_boolean:
            # This is a boolean global flag
            global_args.append(arg)
            i += 1
        else:
            # This is not a global flag - could be subcommand or subcommand arg
            non_global_args.append(arg)
            i += 1

    # Build final command: global_flags + subcommand + non-global args
    final_args = global_args + non_global_args

    if shutil.which(CLI_CMD):
        return subprocess.run([CLI_CMD] + final_args, **kwargs)
    else:
        return subprocess.run(
            [sys.executable, '-m', 'claude_skills.cli.sdd'] + final_args,
            **kwargs
        )


@pytest.mark.integration
class TestListSpecsCLI:
    """Tests for list-specs command with Rich table output."""

    def test_list_specs_help(self):
        """Test list-specs shows help text."""
        result = run_cli("list-specs", "--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "list-specs" in result.stdout.lower()

    def test_list_specs_text_output(self, tmp_path):
        """Test list-specs with default text/Rich output."""
        # Create a temporary spec
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create a simple spec JSON file
        spec_data = {
            "metadata": {
                "title": "Test Specification",
                "version": "1.0.0",
                "created_at": "2025-11-06T00:00:00Z",
                "updated_at": "2025-11-06T12:00:00Z",
                "current_phase": "phase-1"
            },
            "hierarchy": {
                "phase-1": {
                    "type": "phase",
                    "status": "in_progress",
                    "children": ["task-1-1"]
                },
                "task-1-1": {
                    "type": "task",
                    "status": "completed",
                    "parent": "phase-1"
                }
            }
        }

        spec_file = active_dir / "test-spec-001.json"
        spec_file.write_text(json.dumps(spec_data, indent=2))

        # Run list-specs command (text output is default)
        result = run_cli("--path", str(specs_dir), "list-specs",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Check for Rich table elements
        assert "Specifications" in result.stdout or "test-spec-001" in result.stdout

    def test_list_specs_json_output(self, tmp_path):
        """Test list-specs with JSON output format."""
        # Create a temporary spec
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create a simple spec JSON file
        spec_data = {
            "metadata": {
                "title": "JSON Output Test",
                "version": "1.0.0",
                "created_at": "2025-11-06T00:00:00Z",
                "updated_at": "2025-11-06T12:00:00Z",
                "current_phase": "phase-1"
            },
            "hierarchy": {
                "phase-1": {
                    "type": "phase",
                    "status": "in_progress",
                    "children": ["task-1-1", "task-1-2"]
                },
                "task-1-1": {
                    "type": "task",
                    "status": "completed",
                    "parent": "phase-1"
                },
                "task-1-2": {
                    "type": "task",
                    "status": "pending",
                    "parent": "phase-1"
                }
            }
        }

        spec_file = active_dir / "json-test-001.json"
        spec_file.write_text(json.dumps(spec_data, indent=2))

        # Run list-specs command with JSON format
        result = run_cli("list-specs", "--path", str(specs_dir), "--format", "json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Parse JSON output
        output_data = json.loads(result.stdout)
        assert isinstance(output_data, list)
        assert len(output_data) == 1

        # Verify spec information
        spec_info = output_data[0]
        assert spec_info["spec_id"] == "json-test-001"
        assert spec_info["title"] == "JSON Output Test"
        assert spec_info["status"] == "active"
        assert spec_info["total_tasks"] == 3  # phase + 2 tasks
        assert spec_info["completed_tasks"] == 1
        assert "progress_percentage" in spec_info

    def test_list_specs_empty_directory(self, tmp_path):
        """Test list-specs with empty specs directory."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Run list-specs on empty directory
        result = run_cli("--path", str(specs_dir), "list-specs",
            capture_output=True,
            text=True
        )

        # Should succeed with empty message
        assert result.returncode == 0
        assert "No specifications found" in result.stdout or result.stdout.strip() == ""

    def test_list_specs_filter_by_status(self, tmp_path):
        """Test list-specs with status filtering."""
        # Create specs in different status folders
        specs_dir = tmp_path / "specs"

        # Active spec
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)
        active_spec = {
            "metadata": {"title": "Active Spec"},
            "hierarchy": {}
        }
        (active_dir / "active-001.json").write_text(json.dumps(active_spec))

        # Completed spec
        completed_dir = specs_dir / "completed"
        completed_dir.mkdir(parents=True)
        completed_spec = {
            "metadata": {"title": "Completed Spec"},
            "hierarchy": {}
        }
        (completed_dir / "completed-001.json").write_text(json.dumps(completed_spec))

        # List only active specs
        result = run_cli("list-specs", "--path", str(specs_dir), "--status", "active", "--format", "json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert len(output_data) == 1
        assert output_data[0]["status"] == "active"

        # List only completed specs
        result = run_cli("list-specs", "--path", str(specs_dir), "--status", "completed", "--format", "json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert len(output_data) == 1
        assert output_data[0]["status"] == "completed"

    def test_list_specs_progress_calculation(self, tmp_path):
        """Test list-specs calculates progress correctly."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create spec with mixed task statuses
        spec_data = {
            "metadata": {
                "title": "Progress Test",
                "version": "1.0.0"
            },
            "hierarchy": {
                "task-1": {"type": "task", "status": "completed"},
                "task-2": {"type": "task", "status": "completed"},
                "task-3": {"type": "task", "status": "pending"},
                "task-4": {"type": "task", "status": "pending"},
            }
        }

        (active_dir / "progress-test-001.json").write_text(json.dumps(spec_data))

        # Run list-specs with JSON output
        result = run_cli("list-specs", "--path", str(specs_dir), "--format", "json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        spec_info = output_data[0]

        # Verify progress calculation: 2 completed out of 4 total = 50%
        assert spec_info["total_tasks"] == 4
        assert spec_info["completed_tasks"] == 2
        assert spec_info["progress_percentage"] == 50

    def test_list_specs_verbose_output(self, tmp_path):
        """Test list-specs with --detailed flag."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create spec with metadata
        spec_data = {
            "metadata": {
                "title": "Verbose Test",
                "description": "Test description",
                "author": "Test Author",
                "version": "2.0.0",
                "created_at": "2025-11-01T00:00:00Z"
            },
            "hierarchy": {}
        }

        (active_dir / "verbose-001.json").write_text(json.dumps(spec_data))

        # Run with --detailed and JSON format for easy verification
        result = run_cli("list-specs", "--path", str(specs_dir), "--detailed", "--format", "json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        spec_info = output_data[0]

        # Detailed mode should include additional fields
        assert "description" in spec_info
        assert spec_info["description"] == "Test description"
        assert "author" in spec_info
        assert spec_info["author"] == "Test Author"
        assert "file_path" in spec_info

    def test_list_specs_multiple_specs(self, tmp_path):
        """Test list-specs with multiple specifications."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create multiple specs
        for i in range(1, 4):
            spec_data = {
                "metadata": {
                    "title": f"Spec {i}",
                    "version": "1.0.0"
                },
                "hierarchy": {
                    "task-1": {"type": "task", "status": "pending"}
                }
            }
            (active_dir / f"spec-{i:03d}.json").write_text(json.dumps(spec_data))

        # Run list-specs
        result = run_cli("list-specs", "--path", str(specs_dir), "--format", "json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert len(output_data) == 3

        # Verify all specs are listed
        spec_ids = [spec["spec_id"] for spec in output_data]
        assert "spec-001" in spec_ids
        assert "spec-002" in spec_ids
        assert "spec-003" in spec_ids
