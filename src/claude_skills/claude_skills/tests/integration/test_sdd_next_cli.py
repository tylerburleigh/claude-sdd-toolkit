"""
Integration tests for sdd_next_tools.py CLI.

Tests all CLI commands with various arguments, JSON output, and error handling.

Note: Tests updated to use unified CLI (sdd next) instead of legacy sdd-next.
"""

import json

import pytest

from .cli_runner import run_cli


class TestCLIBasics:
    """Basic CLI functionality tests."""

    def test_cli_help(self):
        """Test CLI shows help."""
        result = run_cli("--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "Spec-Driven" in result.stdout

    def test_cli_version(self):
        """Test CLI version/info."""
        # Some CLIs support --version
        result = run_cli("verify-tools",
            capture_output=True,
            text=True
        )

        # Should succeed (or at least not crash)
        assert result.returncode in [0, 1]


class TestVerifyToolsCommand:
    """Tests for verify-tools command."""

    def test_verify_tools_success(self):
        """Test verify-tools command."""
        result = run_cli("verify-tools",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "python" in result.stdout.lower() or "verified" in result.stdout.lower()


class TestFindSpecsCommand:
    """Tests for find-specs command."""

    def test_find_specs_basic(self, specs_structure):
        """Test find-specs command."""
        result = run_cli("find-specs", "--path", str(specs_structure),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "specs" in result.stdout.lower() or str(specs_structure) in result.stdout

    def test_find_specs_verbose(self, specs_structure, sample_spec_simple):
        """Test find-specs with verbose flag."""
        result = run_cli("find-specs", "--path", str(specs_structure), "-v",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should list spec files
        assert ".json" in result.stdout or "spec" in result.stdout.lower()


class TestNextTaskCommand:
    """Tests for next-task command."""

    def test_next_task_success(self, sample_json_spec_simple, specs_structure):
        """Test next-task command."""
        result = run_cli( "next-task", "simple-spec-2025-01-01-001",
             "--path", str(specs_structure),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "task-1-1" in result.stdout

    def test_next_task_json_output(self, sample_json_spec_simple, specs_structure):
        """Test next-task with JSON output."""
        result = run_cli( "next-task", "simple-spec-2025-01-01-001",
             "--path", str(specs_structure), "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Parse JSON
        data = json.loads(result.stdout)
        assert "task_id" in data
        assert data["task_id"] == "task-1-1"

    def test_next_task_compact_output(self, sample_json_spec_simple, specs_structure):
        """Test next-task respects compact JSON flag."""
        result = run_cli(
            "next-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            "--compact",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert len(result.stdout.strip().splitlines()) == 1
        data = json.loads(result.stdout)
        assert data["task_id"] == "task-1-1"

    def test_next_task_nonexistent_spec(self, specs_structure):
        """Test next-task with non-existent spec."""
        result = run_cli( "next-task", "nonexistent-spec",
             "--path", str(specs_structure),
            capture_output=True,
            text=True
        )

        assert result.returncode == 1


class TestTaskInfoCommand:
    """Tests for task-info command."""

    def test_task_info_success(self, sample_json_spec_simple, specs_structure):
        """Test task-info command."""
        result = run_cli( "task-info", "simple-spec-2025-01-01-001", "task-1-1",
             "--path", str(specs_structure),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "task-1-1" in result.stdout
        assert "pending" in result.stdout.lower()

    def test_task_info_json(self, sample_json_spec_simple, specs_structure):
        """Test task-info with JSON output."""
        result = run_cli( "task-info", "simple-spec-2025-01-01-001", "task-1-1",
             "--path", str(specs_structure), "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert data["id"] == "task-1-1"
        assert "status" in data


class TestCheckDepsCommand:
    """Tests for check-deps command."""

    def test_check_deps_no_blockers(self, sample_json_spec_simple, specs_structure):
        """Test check-deps for task with no blockers."""
        result = run_cli("--no-json", "--path", str(specs_structure),
             "check-deps", "simple-spec-2025-01-01-001", "task-1-1",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "can start" in result.stdout.lower() or "yes" in result.stdout.lower()

    def test_check_deps_with_blockers(self, sample_json_spec_with_deps, specs_structure):
        """Test check-deps for blocked task."""
        result = run_cli("--no-json", "--path", str(specs_structure),
             "check-deps", "deps-spec-2025-01-01-003", "task-2-2",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "blocked" in result.stdout.lower() or "task-2-1" in result.stdout

    def test_check_deps_json(self, sample_json_spec_simple, specs_structure):
        """Test check-deps with JSON output."""
        result = run_cli("--path", str(specs_structure), "--json",
             "check-deps", "simple-spec-2025-01-01-001", "task-1-1",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert "can_start" in data
        assert data["can_start"] is True


class TestProgressCommand:
    """Tests for progress command."""

    def test_progress_command(self, sample_json_spec_simple, specs_structure):
        """Test progress command."""
        result = run_cli("--no-json", "progress", "simple-spec-2025-01-01-001",
             "--path", str(specs_structure),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "progress" in result.stdout.lower() or "tasks" in result.stdout.lower()

    def test_progress_json(self, sample_json_spec_simple, specs_structure):
        """Test progress with JSON output."""
        result = run_cli( "progress", "simple-spec-2025-01-01-001",
             "--path", str(specs_structure), "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "percentage" in data

    def test_progress_compact_and_pretty_output(self, sample_json_spec_simple, specs_structure):
        """Test progress honors compact and no-compact flags."""
        compact_result = run_cli(
            "progress",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            "--compact",
            capture_output=True,
            text=True
        )
        assert compact_result.returncode in (0, 1)
        compact_lines = compact_result.stdout.strip().splitlines()
        assert len(compact_lines) == 1
        compact_data = json.loads(compact_result.stdout)

        pretty_result = run_cli(
            "progress",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            "--no-compact",
            capture_output=True,
            text=True
        )
        assert pretty_result.returncode in (0, 1)
        pretty_lines = pretty_result.stdout.strip().splitlines()
        assert len(pretty_lines) > 1
        assert json.loads(pretty_result.stdout) == compact_data



class TestListPhasesCommand:
    """Tests for list-phases command."""

    def test_list_phases(self, sample_json_spec_simple, specs_structure):
        """Test list-phases command."""
        result = run_cli("--no-json", "list-phases", "simple-spec-2025-01-01-001",
             "--path", str(specs_structure),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "phase" in result.stdout.lower()

    def test_list_phases_json(self, sample_json_spec_simple, specs_structure):
        """Test list-phases with JSON output."""
        result = run_cli("--path", str(specs_structure), "--json",
             "list-phases", "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 2  # Our simple spec has 2 phases


@pytest.mark.integration
class TestCLIWorkflows:
    """End-to-end CLI workflow tests."""

    def test_complete_task_discovery_workflow(self, sample_json_spec_simple, sample_spec_simple, specs_structure):
        """Test complete workflow using CLI commands."""
        # Step 1: Find next task
        result = run_cli("--path", str(specs_structure), "--json",
             "next-task", "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        next_task = json.loads(result.stdout)
        task_id = next_task["task_id"]

        # Step 2: Get task info
        result = run_cli("--path", str(specs_structure),
             "task-info", "simple-spec-2025-01-01-001", task_id,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Step 3: Check dependencies
        result = run_cli("--path", str(specs_structure), "--json",
             "check-deps", "simple-spec-2025-01-01-001", task_id,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        deps = json.loads(result.stdout)
        assert deps["can_start"] is True

        # Step 4: Check progress
        result = run_cli("--path", str(specs_structure),
             "progress", "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0


@pytest.mark.integration
class TestCompletionDetection:
    """Tests for automatic spec completion detection in sdd-next workflow."""

    def test_completion_detection_prepare_task(self, sample_json_spec_completed, specs_structure):
        """Test completion prompt appears when prepare_task finds all tasks complete."""
        from claude_skills.common.spec import load_json_spec, save_json_spec

        spec_id = "completed-spec-2025-01-01-007"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Ensure all tasks are completed
        for node_id, node in spec_data["hierarchy"].items():
            if node.get("type") == "task":
                node["status"] = "completed"

        save_json_spec(spec_id, specs_structure, spec_data)

        # Run prepare-task which should detect completion
        result = run_cli(
            "prepare-task",
            spec_id,
            "--path", str(specs_structure),
            capture_output=True,
            text=True
        )

        # Should show completion message
        assert "complete" in result.stdout.lower() or "all tasks" in result.stdout.lower()

    def test_all_blocked_messaging(self, sample_json_spec_with_blockers, specs_structure):
        """Test that 'all blocked' shows different message than 'all completed'."""
        from claude_skills.common.spec import load_json_spec, save_json_spec

        spec_id = "blocked-spec-2025-01-01-005"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Mark all tasks as either completed or blocked (no pending)
        for node_id, node in spec_data["hierarchy"].items():
            if node.get("type") == "task":
                if node.get("status") != "blocked":
                    node["status"] = "completed"

        save_json_spec(spec_id, specs_structure, spec_data)

        # Run prepare-task
        result = run_cli(
            "prepare-task",
            spec_id,
            "--path", str(specs_structure),
            capture_output=True,
            text=True
        )

        # When there are blocked tasks, should show "remaining" or "no actionable tasks"
        # (blocked tasks count as incomplete/remaining)
        assert "remaining" in result.stdout.lower() or "no actionable" in result.stdout.lower()

    def test_prepare_task_with_completion_and_blockers(self, sample_json_spec_with_blockers, specs_structure):
        """Test prepare-task when spec is complete but has blocked tasks."""
        from claude_skills.common.spec import load_json_spec, save_json_spec

        spec_id = "blocked-spec-2025-01-01-005"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Mark all non-blocked tasks as completed
        for node_id, node in spec_data["hierarchy"].items():
            if node.get("type") == "task" and node.get("status") != "blocked":
                node["status"] = "completed"

        save_json_spec(spec_id, specs_structure, spec_data)

        # Run prepare-task
        result = run_cli(
            "prepare-task",
            spec_id,
            "--path", str(specs_structure),
            capture_output=True,
            text=True
        )

        # Should show that there are remaining tasks (the blocked ones)
        assert "remaining" in result.stdout.lower() or "no actionable" in result.stdout.lower()
        # Should NOT show completion prompt since blocked tasks exist
        assert not ("mark spec as complete" in result.stdout.lower())


class TestUtilityCommands:
    """Tests for misc utility subcommands."""

    def test_find_pattern_compact_and_pretty(self, tmp_path):
        """find-pattern should honor compact flags."""
        target_dir = tmp_path / "project"
        target_dir.mkdir()
        (target_dir / "foo.py").write_text("print('hi')\n")
        (target_dir / "bar.txt").write_text("text")

        compact_result = run_cli(
            "--json",
            "--compact",
            "find-pattern",
            "*.py",
            "--directory", str(target_dir),
            capture_output=True,
            text=True
        )
        assert compact_result.returncode in (0, 1)
        assert len(compact_result.stdout.strip().splitlines()) == 1
        compact_data = json.loads(compact_result.stdout)
        assert compact_data["pattern"] == "*.py"
        assert any(p.endswith("foo.py") for p in compact_data["matches"])

        pretty_result = run_cli(
            "--json",
            "--no-compact",
            "find-pattern",
            "*.py",
            "--directory", str(target_dir),
            capture_output=True,
            text=True
        )
        assert pretty_result.returncode in (0, 1)
        assert len(pretty_result.stdout.strip().splitlines()) > 1
        assert json.loads(pretty_result.stdout) == compact_data

    def test_find_tests_compact_and_pretty(self, tmp_path):
        """find-tests should toggle between compact and pretty JSON."""
        project_dir = tmp_path / "proj"
        src_dir = project_dir / "src"
        tests_dir = project_dir / "tests"
        src_dir.mkdir(parents=True)
        tests_dir.mkdir()
        (src_dir / "example.py").write_text("def example():\n    pass\n")
        (tests_dir / "test_example.py").write_text("def test_example():\n    pass\n")

        compact_result = run_cli(
            "--json",
            "--compact",
            "find-tests",
            "--directory", str(project_dir),
            capture_output=True,
            text=True
        )
        assert compact_result.returncode in (0, 1)
        assert len(compact_result.stdout.strip().splitlines()) == 1
        compact_data = json.loads(compact_result.stdout)
        assert any(path.endswith("test_example.py") for path in compact_data["test_files"])

        pretty_result = run_cli(
            "--json",
            "--no-compact",
            "find-tests",
            "--directory", str(project_dir),
            capture_output=True,
            text=True
        )
        assert pretty_result.returncode in (0, 1)
        assert len(pretty_result.stdout.strip().splitlines()) > 1
        assert json.loads(pretty_result.stdout) == compact_data

    def test_validate_paths_compact_and_pretty(self, tmp_path):
        """validate-paths should honor compact flags."""
        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        sample_file = project_dir / "sample.txt"
        sample_file.write_text("hello\n")

        compact_result = run_cli(
            "--json",
            "--compact",
            "validate-paths",
            "sample.txt",
            "missing.txt",
            "--base-directory", str(project_dir),
            capture_output=True,
            text=True
        )
        assert compact_result.returncode in (0, 1)
        assert len(compact_result.stdout.strip().splitlines()) == 1
        compact_data = json.loads(compact_result.stdout)
        assert "invalid_paths" in compact_data

        pretty_result = run_cli(
            "--json",
            "--no-compact",
            "validate-paths",
            "sample.txt",
            "missing.txt",
            "--base-directory", str(project_dir),
            capture_output=True,
            text=True
        )
        assert pretty_result.returncode in (0, 1)
        assert len(pretty_result.stdout.strip().splitlines()) > 1
        assert json.loads(pretty_result.stdout) == compact_data


class TestInitEnvCommand:
    """Tests for init-env command output modes."""

    def test_init_env_text_output(self, specs_structure):
        """init-env should show human-readable output by default."""
        result = run_cli(
            "--no-json",
            "--path", str(specs_structure),
            "init-env",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Environment initialized" in result.stdout

    def test_init_env_json_compact(self, specs_structure):
        """init-env should respect --json and --compact flags."""
        result = run_cli(
            "--path", str(specs_structure),
            "init-env",
            "--json", "--compact",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert len(result.stdout.strip().splitlines()) == 1
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["specs_dir"].endswith("specs")
        assert data["active_dir"].endswith("active")
        assert data["state_dir"].endswith(".state")
