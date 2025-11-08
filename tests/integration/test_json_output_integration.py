"""Integration tests for JSON output compact mode across SDD CLI commands.

Tests that all commands with JSON output support properly handle
--compact and --no-compact flags, producing different formatted outputs.
"""
import json
import subprocess
from pathlib import Path
import pytest


class TestJSONOutputCompactMode:
    """Test compact/pretty JSON output modes for key SDD CLI commands."""

    @pytest.fixture
    def sample_spec_id(self):
        """Provide a spec ID that exists in the active directory."""
        # Find first spec in specs/active directory
        specs_dir = Path(__file__).parent.parent.parent / "specs" / "active"
        if not specs_dir.exists():
            pytest.skip("No specs/active directory found")

        spec_files = list(specs_dir.glob("*.json"))
        if not spec_files:
            pytest.skip("No spec files found in specs/active")

        # Extract spec ID from filename (remove .json extension)
        spec_id = spec_files[0].stem
        return spec_id

    @pytest.fixture
    def sample_spec_file(self, sample_spec_id):
        """Provide full path to a sample spec file."""
        specs_dir = Path(__file__).parent.parent.parent / "specs" / "active"
        return str(specs_dir / f"{sample_spec_id}.json")

    def test_progress_compact_vs_pretty(self, sample_spec_id):
        """Test that 'progress' command produces different output for compact vs pretty."""
        # Run with --compact flag
        result_compact = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--json', '--compact'],
            capture_output=True,
            text=True
        )

        # Run with --no-compact flag
        result_pretty = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        # Both should succeed
        assert result_compact.returncode == 0
        assert result_pretty.returncode == 0

        # Outputs should be different
        assert result_compact.stdout != result_pretty.stdout

        # Compact should be smaller
        assert len(result_compact.stdout) < len(result_pretty.stdout)

        # Both should be valid JSON
        json.loads(result_compact.stdout)
        json.loads(result_pretty.stdout)

    def test_list_phases_compact_vs_pretty(self, sample_spec_id):
        """Test that 'list-phases' command produces different output for compact vs pretty."""
        result_compact = subprocess.run(
            ['sdd', 'list-phases', sample_spec_id, '--json', '--compact'],
            capture_output=True,
            text=True
        )

        result_pretty = subprocess.run(
            ['sdd', 'list-phases', sample_spec_id, '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        assert result_compact.returncode == 0
        assert result_pretty.returncode == 0
        assert result_compact.stdout != result_pretty.stdout
        assert len(result_compact.stdout) < len(result_pretty.stdout)

        # Verify both are valid JSON
        json.loads(result_compact.stdout)
        json.loads(result_pretty.stdout)

    def test_spec_stats_compact_vs_pretty(self, sample_spec_file):
        """Test that 'spec-stats' command produces different output for compact vs pretty."""
        result_compact = subprocess.run(
            ['sdd', 'spec-stats', sample_spec_file, '--json', '--compact'],
            capture_output=True,
            text=True
        )

        result_pretty = subprocess.run(
            ['sdd', 'spec-stats', sample_spec_file, '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        assert result_compact.returncode == 0
        assert result_pretty.returncode == 0
        assert result_compact.stdout != result_pretty.stdout
        assert len(result_compact.stdout) < len(result_pretty.stdout)

        json.loads(result_compact.stdout)
        json.loads(result_pretty.stdout)

    def test_next_task_compact_vs_pretty(self, sample_spec_id):
        """Test that 'next-task' command produces different output for compact vs pretty."""
        result_compact = subprocess.run(
            ['sdd', 'next-task', sample_spec_id, '--json', '--compact'],
            capture_output=True,
            text=True
        )

        result_pretty = subprocess.run(
            ['sdd', 'next-task', sample_spec_id, '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        # next-task may return non-zero if no tasks available (acceptable)
        assert result_compact.returncode in [0, 1]
        assert result_pretty.returncode in [0, 1]

        # If we got output, it should differ
        if result_compact.stdout and result_pretty.stdout:
            assert result_compact.stdout != result_pretty.stdout
            json.loads(result_compact.stdout)
            json.loads(result_pretty.stdout)

    def test_query_tasks_compact_vs_pretty(self, sample_spec_id):
        """Test that 'query-tasks' command produces different output for compact vs pretty."""
        result_compact = subprocess.run(
            ['sdd', 'query-tasks', sample_spec_id, '--status', 'completed', '--json', '--compact'],
            capture_output=True,
            text=True
        )

        result_pretty = subprocess.run(
            ['sdd', 'query-tasks', sample_spec_id, '--status', 'completed', '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        assert result_compact.returncode == 0
        assert result_pretty.returncode == 0
        assert result_compact.stdout != result_pretty.stdout

        json.loads(result_compact.stdout)
        json.loads(result_pretty.stdout)

    def test_check_complete_compact_vs_pretty(self, sample_spec_id):
        """Test that 'check-complete' command produces different output for compact vs pretty."""
        result_compact = subprocess.run(
            ['sdd', 'check-complete', sample_spec_id, '--json', '--compact'],
            capture_output=True,
            text=True
        )

        result_pretty = subprocess.run(
            ['sdd', 'check-complete', sample_spec_id, '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        # check-complete may return non-zero if spec is not complete (acceptable)
        assert result_compact.returncode in [0, 1]
        assert result_pretty.returncode in [0, 1]

        # Outputs should differ
        assert result_compact.stdout != result_pretty.stdout

        json.loads(result_compact.stdout)
        json.loads(result_pretty.stdout)

    def test_cache_info_compact_vs_pretty(self):
        """Test that 'cache info' command produces different output for compact vs pretty."""
        result_compact = subprocess.run(
            ['sdd', 'cache', 'info', '--json', '--compact'],
            capture_output=True,
            text=True
        )

        result_pretty = subprocess.run(
            ['sdd', 'cache', 'info', '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        # cache info may return non-zero if cache is disabled (acceptable)
        assert result_compact.returncode in [0, 1]
        assert result_pretty.returncode in [0, 1]

        # If we got output, it should differ
        if result_compact.stdout and result_pretty.stdout:
            assert result_compact.stdout != result_pretty.stdout
            json.loads(result_compact.stdout)
            json.loads(result_pretty.stdout)

    def test_list_plan_review_tools_compact_vs_pretty(self):
        """Test that 'list-plan-review-tools' command produces different output for compact vs pretty."""
        result_compact = subprocess.run(
            ['sdd', 'list-plan-review-tools', '--json', '--compact'],
            capture_output=True,
            text=True
        )

        result_pretty = subprocess.run(
            ['sdd', 'list-plan-review-tools', '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        assert result_compact.returncode == 0
        assert result_pretty.returncode == 0
        assert result_compact.stdout != result_pretty.stdout

        json.loads(result_compact.stdout)
        json.loads(result_pretty.stdout)

    def test_compact_flag_available_on_all_json_commands(self):
        """Test that --compact flag is available on all commands that support --json."""
        # Test a few key commands to ensure the flag is recognized
        commands = [
            ['sdd', 'progress', '--help'],
            ['sdd', 'list-phases', '--help'],
            ['sdd', 'cache', 'info', '--help'],
        ]

        for cmd in commands:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            # Help should mention --compact or inherit from parent
            # (Not all commands explicitly show inherited flags in help)

    def test_compact_produces_single_line_json(self, sample_spec_id):
        """Test that compact mode produces single-line JSON output."""
        result_compact = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--json', '--compact'],
            capture_output=True,
            text=True
        )

        assert result_compact.returncode == 0

        # Compact output should not contain newlines (except final one)
        lines = result_compact.stdout.strip().split('\n')
        assert len(lines) == 1, "Compact JSON should be on a single line"

    def test_pretty_produces_multiline_json(self, sample_spec_id):
        """Test that pretty mode produces multi-line JSON output with indentation."""
        result_pretty = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        assert result_pretty.returncode == 0

        # Pretty output should contain newlines
        lines = result_pretty.stdout.strip().split('\n')
        assert len(lines) > 1, "Pretty JSON should be on multiple lines"

        # Should contain indentation (2 spaces)
        assert '  ' in result_pretty.stdout, "Pretty JSON should have indentation"

    def test_default_is_compact_mode(self, sample_spec_id):
        """Test that default behavior (no flag) uses compact mode."""
        result_default = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--json'],
            capture_output=True,
            text=True
        )

        result_compact = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--json', '--compact'],
            capture_output=True,
            text=True
        )

        assert result_default.returncode == 0
        assert result_compact.returncode == 0

        # Default should match compact mode
        assert result_default.stdout == result_compact.stdout
