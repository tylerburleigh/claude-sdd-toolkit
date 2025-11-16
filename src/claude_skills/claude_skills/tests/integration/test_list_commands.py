"""
Integration tests for list commands with Rich table output.

Tests all list commands:
- list-specs: List all specifications with Rich.Table
- query-tasks: Query tasks with Rich.Table
- list-phases: List phases with Rich.Table
- check-deps: Show dependencies with Rich.Tree

Tests cover:
- Text/Rich output format (default)
- JSON output format (--json)
- Output correctness and structure
- Empty result handling
"""

import json

import pytest

from .cli_runner import run_cli


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
        result = run_cli("--no-json", "--path", str(specs_dir), "list-specs",
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

        # Run list-specs command with the global --json flag
        result = run_cli("--json", "list-specs", "--path", str(specs_dir),
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

    def test_list_specs_compact_json_output(self, tmp_path):
        """Test list-specs with compact JSON output."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "Compact Test"},
            "hierarchy": {
                "phase-1": {"type": "phase", "status": "in_progress", "children": ["task-1-1"]}
            }
        }
        (active_dir / "compact-001.json").write_text(json.dumps(spec_data, indent=2))

        result = run_cli("--json", "--compact", "list-specs", "--path", str(specs_dir),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert len(result.stdout.strip().splitlines()) == 1
        data = json.loads(result.stdout)
        assert data[0]["spec_id"] == "compact-001"

    def test_list_specs_pretty_json_output(self, tmp_path):
        """Test list-specs with --no-compact flag."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "Pretty Test"},
            "hierarchy": {
                "phase-1": {"type": "phase", "status": "in_progress", "children": ["task-1-1"]}
            }
        }
        (active_dir / "pretty-001.json").write_text(json.dumps(spec_data, indent=2))

        result = run_cli("--json", "--no-compact", "list-specs", "--path", str(specs_dir),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) > 1
        data = json.loads(result.stdout)
        assert data[0]["spec_id"] == "pretty-001"

    def test_list_specs_empty_directory(self, tmp_path):
        """Test list-specs with empty specs directory."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Run list-specs on empty directory
        result = run_cli("--no-json", "--path", str(specs_dir), "list-specs",
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
        result = run_cli("--json", "list-specs", "--path", str(specs_dir), "--status", "active",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert len(output_data) == 1
        assert output_data[0]["status"] == "active"

        # List only completed specs
        result = run_cli("--json", "list-specs", "--path", str(specs_dir), "--status", "completed",
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
        result = run_cli("--json", "list-specs", "--path", str(specs_dir),
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

        # Run with --detailed and the global --json flag for easy verification
        result = run_cli("--json", "list-specs", "--path", str(specs_dir), "--detailed",
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
        result = run_cli("--json", "list-specs", "--path", str(specs_dir),
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

    def test_list_specs_json_no_ansi_codes(self, tmp_path):
        """Test that JSON output contains no ANSI escape codes."""
        import re

        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create spec with status that might trigger colored output
        spec_data = {
            "metadata": {
                "title": "ANSI Test Spec",
                "version": "1.0.0"
            },
            "hierarchy": {
                "task-1": {"type": "task", "status": "completed"},
                "task-2": {"type": "task", "status": "in_progress"},
                "task-3": {"type": "task", "status": "pending"},
            }
        }

        (active_dir / "ansi-test-001.json").write_text(json.dumps(spec_data))

        # Run list-specs with JSON output
        result = run_cli("--json", "list-specs", "--path", str(specs_dir),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # ANSI escape code pattern: ESC [ followed by parameters and a final byte
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

        # Verify no ANSI codes in output
        assert not ansi_pattern.search(result.stdout), \
            "JSON output should not contain ANSI escape codes"

        # Verify it's valid JSON (would fail if ANSI codes present)
        output_data = json.loads(result.stdout)
        assert isinstance(output_data, list)

        # Verify no ANSI codes in any string values
        for spec_info in output_data:
            for key, value in spec_info.items():
                if isinstance(value, str):
                    assert not ansi_pattern.search(value), \
                        f"Field '{key}' contains ANSI codes: {value}"


@pytest.mark.integration
class TestQueryTasksCLI:
    """Tests for query-tasks command with Rich table output."""

    def test_query_tasks_help(self):
        """Test query-tasks shows help text."""
        result = run_cli("query-tasks", "--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "query-tasks" in result.stdout.lower()

    def test_query_tasks_text_output(self, tmp_path):
        """Test query-tasks with default text/Rich output."""
        # Create a spec with tasks
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "Query Test"},
            "hierarchy": {
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "status": "in_progress",
                    "children": ["task-1-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0
                },
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "pending",
                    "parent": "phase-1",
                    "total_tasks": 1,
                    "completed_tasks": 0
                }
            }
        }

        (active_dir / "query-001.json").write_text(json.dumps(spec_data))

        # Run query-tasks (text output is default)
        result = run_cli("query-tasks", "--path", str(specs_dir), "query-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Check for Rich table output elements
        assert "Tasks" in result.stdout or "task-1-1" in result.stdout

    def test_query_tasks_json_output(self, tmp_path):
        """Test query-tasks with JSON output format."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "JSON Query Test"},
            "hierarchy": {
                "task-1": {
                    "type": "task",
                    "title": "First Task",
                    "status": "pending",
                    "total_tasks": 1,
                    "completed_tasks": 0
                },
                "task-2": {
                    "type": "task",
                    "title": "Second Task",
                    "status": "completed",
                    "total_tasks": 1,
                    "completed_tasks": 1
                }
            }
        }

        (active_dir / "json-query-001.json").write_text(json.dumps(spec_data))

        # Run query-tasks with the global --json flag
        result = run_cli("--json", "query-tasks", "--path", str(specs_dir), "json-query-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Parse JSON output
        output_data = json.loads(result.stdout)
        assert isinstance(output_data, list)
        assert len(output_data) == 2

        # Verify task information
        task_ids = [task["id"] for task in output_data]
        assert "task-1" in task_ids
        assert "task-2" in task_ids

    def test_query_tasks_filter_by_status(self, tmp_path):
        """Test query-tasks with status filtering."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "Filter Test"},
            "hierarchy": {
                "task-1": {"type": "task", "title": "Pending Task", "status": "pending"},
                "task-2": {"type": "task", "title": "In Progress Task", "status": "in_progress"},
                "task-3": {"type": "task", "title": "Completed Task", "status": "completed"}
            }
        }

        (active_dir / "filter-001.json").write_text(json.dumps(spec_data))

        # Query only pending tasks
        result = run_cli("--json", "query-tasks", "--path", str(specs_dir), "filter-001", "--status", "pending",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert len(output_data) == 1
        assert output_data[0]["id"] == "task-1"
        assert output_data[0]["status"] == "pending"

    def test_query_tasks_filter_by_type(self, tmp_path):
        """Test query-tasks with type filtering."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "Type Filter Test"},
            "hierarchy": {
                "phase-1": {"type": "phase", "title": "Phase 1", "status": "in_progress"},
                "task-1": {"type": "task", "title": "Task 1", "status": "pending", "parent": "phase-1"},
                "verify-1": {"type": "verify", "title": "Verify 1", "status": "pending", "parent": "phase-1"}
            }
        }

        (active_dir / "type-filter-001.json").write_text(json.dumps(spec_data))

        # Query only tasks (not phases or verifications)
        result = run_cli("--json", "query-tasks", "--path", str(specs_dir), "type-filter-001", "--type", "task",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert len(output_data) == 1
        assert output_data[0]["id"] == "task-1"
        assert output_data[0]["type"] == "task"

    def test_query_tasks_filter_by_parent(self, tmp_path):
        """Test query-tasks with parent filtering."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "Parent Filter Test"},
            "hierarchy": {
                "phase-1": {"type": "phase", "title": "Phase 1", "status": "in_progress"},
                "phase-2": {"type": "phase", "title": "Phase 2", "status": "pending"},
                "task-1-1": {"type": "task", "title": "Task 1.1", "status": "pending", "parent": "phase-1"},
                "task-1-2": {"type": "task", "title": "Task 1.2", "status": "completed", "parent": "phase-1"},
                "task-2-1": {"type": "task", "title": "Task 2.1", "status": "pending", "parent": "phase-2"}
            }
        }

        (active_dir / "parent-filter-001.json").write_text(json.dumps(spec_data))

        # Query only tasks in phase-1
        result = run_cli("--json", "query-tasks", "--path", str(specs_dir), "parent-filter-001", "--parent", "phase-1",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)
        assert len(output_data) == 2

        task_ids = [task["id"] for task in output_data]
        assert "task-1-1" in task_ids
        assert "task-1-2" in task_ids
        assert "task-2-1" not in task_ids

    def test_query_tasks_empty_result(self, tmp_path):
        """Test query-tasks with no matching tasks."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "Empty Test"},
            "hierarchy": {
                "task-1": {"type": "task", "title": "Only Task", "status": "pending"}
            }
        }

        (active_dir / "empty-001.json").write_text(json.dumps(spec_data))

        # Query for completed tasks (none exist)
        result = run_cli("--json", "query-tasks", "--path", str(specs_dir), "empty-001", "--status", "completed",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Empty results may return empty string or empty array
        if result.stdout.strip():
            output_data = json.loads(result.stdout)
            assert len(output_data) == 0
        # If no output, that's also acceptable for empty results

    def test_query_tasks_json_no_ansi_codes(self, tmp_path):
        """Test that JSON output contains no ANSI escape codes."""
        import re

        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create spec with tasks with different statuses that might trigger colored output
        spec_data = {
            "metadata": {
                "title": "ANSI Test Query Tasks",
                "version": "1.0.0"
            },
            "hierarchy": {
                "task-1": {"type": "task", "title": "Completed Task", "status": "completed"},
                "task-2": {"type": "task", "title": "In Progress Task", "status": "in_progress"},
                "task-3": {"type": "task", "title": "Pending Task", "status": "pending"},
                "task-4": {"type": "task", "title": "Blocked Task", "status": "blocked"}
            }
        }

        (active_dir / "ansi-query-001.json").write_text(json.dumps(spec_data))

        # Run query-tasks with JSON output
        result = run_cli("--json", "query-tasks", "--path", str(specs_dir), "ansi-query-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # ANSI escape code pattern: ESC [ followed by parameters and a final byte
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

        # Verify no ANSI codes in output
        assert not ansi_pattern.search(result.stdout), \
            "JSON output should not contain ANSI escape codes"

        # Verify it's valid JSON (would fail if ANSI codes present)
        output_data = json.loads(result.stdout)
        assert isinstance(output_data, list)

        # Verify no ANSI codes in any string values
        for task_info in output_data:
            for key, value in task_info.items():
                if isinstance(value, str):
                    assert not ansi_pattern.search(value), \
                        f"Field '{key}' contains ANSI codes: {value}"


@pytest.mark.integration
class TestCheckDepsCLI:
    """Tests for check-deps command with Rich.Tree output."""

    def test_check_deps_help(self):
        """Test check-deps shows help text."""
        result = run_cli("check-deps", "--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "check-deps" in result.stdout.lower()

    def test_check_deps_text_output(self, tmp_path):
        """Test check-deps with default text/Rich.Tree output."""
        # Create a spec with task dependencies
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "Dependency Test"},
            "hierarchy": {
                "task-1": {
                    "type": "task",
                    "title": "First Task",
                    "status": "completed",
                    "dependencies": {"blocks": ["task-2"], "blocked_by": [], "depends": []}
                },
                "task-2": {
                    "type": "task",
                    "title": "Second Task",
                    "status": "pending",
                    "dependencies": {"blocks": [], "blocked_by": ["task-1"], "depends": []}
                }
            }
        }

        (active_dir / "deps-001.json").write_text(json.dumps(spec_data))

        # Run check-deps with Rich.Tree output (--no-json)
        result = run_cli("check-deps", "--path", str(specs_dir), "deps-001", "task-1", "--no-json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Check for Rich tree structure elements
        assert "task-1" in result.stdout
        # Tree structure indicators
        assert "└──" in result.stdout or "├──" in result.stdout

    def test_check_deps_json_output(self, tmp_path):
        """Test check-deps with JSON output format."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "JSON Deps Test"},
            "hierarchy": {
                "task-1": {
                    "type": "task",
                    "title": "First Task",
                    "status": "pending",
                    "dependencies": {"blocks": ["task-2"], "blocked_by": [], "depends": []}
                },
                "task-2": {
                    "type": "task",
                    "title": "Second Task",
                    "status": "pending",
                    "dependencies": {"blocks": [], "blocked_by": ["task-1"], "depends": []}
                }
            }
        }

        (active_dir / "json-deps-001.json").write_text(json.dumps(spec_data))

        # Run check-deps with JSON format (default or explicit --json)
        result = run_cli("check-deps", "--path", str(specs_dir), "json-deps-001", "task-1", "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Parse JSON output
        output_data = json.loads(result.stdout)
        assert isinstance(output_data, dict)

        # Verify dependency information
        assert output_data["task_id"] == "task-1"
        assert "can_start" in output_data
        assert "blocked_by" in output_data
        assert "blocks" in output_data

    def test_check_deps_with_blocked_task(self, tmp_path):
        """Test check-deps shows blocked status correctly."""
        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        spec_data = {
            "metadata": {"title": "Blocked Task Test"},
            "hierarchy": {
                "task-1": {
                    "type": "task",
                    "title": "Prerequisite Task",
                    "status": "pending",
                    "dependencies": {"blocks": ["task-2"], "blocked_by": [], "depends": []}
                },
                "task-2": {
                    "type": "task",
                    "title": "Dependent Task",
                    "status": "pending",
                    "dependencies": {"blocks": [], "blocked_by": ["task-1"], "depends": []}
                }
            }
        }

        (active_dir / "blocked-001.json").write_text(json.dumps(spec_data))

        # Check task-2 which is blocked by task-1
        result = run_cli("check-deps", "--path", str(specs_dir), "blocked-001", "task-2", "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output_data = json.loads(result.stdout)

        # task-2 should be blocked by task-1
        assert output_data["can_start"] == False
        assert len(output_data["blocked_by"]) == 1
        assert output_data["blocked_by"][0]["id"] == "task-1"

    def test_check_deps_json_no_ansi_codes(self, tmp_path):
        """Test that JSON output contains no ANSI escape codes."""
        import re

        specs_dir = tmp_path / "specs"
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True)

        # Create spec with tasks with different dependency statuses that might trigger colored output
        spec_data = {
            "metadata": {
                "title": "ANSI Test Check Deps",
                "version": "1.0.0"
            },
            "hierarchy": {
                "task-1": {
                    "type": "task",
                    "title": "Completed Prerequisite",
                    "status": "completed",
                    "dependencies": {"blocks": ["task-2", "task-3"], "blocked_by": [], "depends": []}
                },
                "task-2": {
                    "type": "task",
                    "title": "In Progress Task",
                    "status": "in_progress",
                    "dependencies": {"blocks": ["task-4"], "blocked_by": ["task-1"], "depends": []}
                },
                "task-3": {
                    "type": "task",
                    "title": "Pending Task",
                    "status": "pending",
                    "dependencies": {"blocks": [], "blocked_by": ["task-1"], "depends": []}
                },
                "task-4": {
                    "type": "task",
                    "title": "Blocked Task",
                    "status": "pending",
                    "dependencies": {"blocks": [], "blocked_by": ["task-2"], "depends": []}
                }
            }
        }

        (active_dir / "ansi-deps-001.json").write_text(json.dumps(spec_data))

        # Run check-deps with JSON output on a task with mixed dependency statuses
        result = run_cli("check-deps", "--path", str(specs_dir), "ansi-deps-001", "task-2", "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # ANSI escape code pattern: ESC [ followed by parameters and a final byte
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

        # Verify no ANSI codes in output
        assert not ansi_pattern.search(result.stdout), \
            "JSON output should not contain ANSI escape codes"

        # Verify it's valid JSON (would fail if ANSI codes present)
        output_data = json.loads(result.stdout)
        assert isinstance(output_data, dict)

        # Verify no ANSI codes in any string values (recursively check nested structures)
        def check_for_ansi(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    check_for_ansi(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_for_ansi(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                assert not ansi_pattern.search(obj), \
                    f"Field '{path}' contains ANSI codes: {obj}"

        check_for_ansi(output_data, "root")
