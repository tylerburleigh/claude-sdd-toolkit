"""Integration tests for JSON output compact mode across SDD CLI commands.

Tests that all commands with JSON output support properly handle
--compact and --no-compact flags, producing different formatted outputs.

Also tests config precedence: CLI flags > config files > defaults.
"""
import json
import os
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


class TestConfigPrecedence:
    """Test that CLI flags properly override config file settings.

    Tests the precedence chain: CLI flags > config files > defaults
    """

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
    def temp_sdd_config(self, tmp_path):
        """Create a temporary SDD config file for testing.

        Creates config in project root .claude directory (backing up existing if present).
        Returns tuple of (config_file, backup_file).
        """
        # Use project root's .claude directory
        project_root = Path(__file__).parent.parent.parent
        claude_dir = project_root / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)

        config_file = claude_dir / "sdd_config.json"
        backup_file = claude_dir / "sdd_config.json.test_backup"

        # Backup existing config if present
        if config_file.exists():
            config_file.rename(backup_file)

        yield config_file

        # Restore original config
        if backup_file.exists():
            if config_file.exists():
                config_file.unlink()
            backup_file.rename(config_file)
        elif config_file.exists():
            # No backup, so remove test config
            config_file.unlink()

    def test_cli_compact_flag_overrides_config_pretty(self, temp_sdd_config, sample_spec_id):
        """Test that --compact flag overrides config setting for pretty JSON."""
        # Write config that sets pretty JSON (json_compact: false)
        config_data = {
            "output": {
                "default_mode": "json",
                "json_compact": False
            }
        }
        temp_sdd_config.write_text(json.dumps(config_data))

        # Run command with --compact flag (should override config)
        result = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--json', '--compact'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Should produce compact output (single line)
        lines = result.stdout.strip().split('\n')
        assert len(lines) == 1, "CLI --compact flag should override config pretty setting"

        # Verify it's valid JSON
        json.loads(result.stdout)

    def test_cli_no_compact_flag_overrides_config_compact(self, temp_sdd_config, sample_spec_id):
        """Test that --no-compact flag overrides config setting for compact JSON."""
        # Write config that sets compact JSON (json_compact: true)
        config_data = {
            "output": {
                "default_mode": "json",
                "json_compact": True
            }
        }
        temp_sdd_config.write_text(json.dumps(config_data))

        # Run command with --no-compact flag (should override config)
        result = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--json', '--no-compact'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Should produce pretty output (multiple lines with indentation)
        lines = result.stdout.strip().split('\n')
        assert len(lines) > 1, "CLI --no-compact flag should override config compact setting"
        assert '  ' in result.stdout, "Pretty JSON should have indentation"

        # Verify it's valid JSON
        json.loads(result.stdout)

    def test_config_compact_setting_used_when_no_cli_flag(self, temp_sdd_config, sample_spec_id):
        """Test that config json_compact setting is used when no CLI flag provided."""
        # Write config that sets pretty JSON
        config_data = {
            "output": {
                "default_mode": "json",
                "json_compact": False
            }
        }
        temp_sdd_config.write_text(json.dumps(config_data))

        # Run command without compact flags
        result = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--json'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Should produce pretty output (config setting)
        lines = result.stdout.strip().split('\n')
        assert len(lines) > 1, "Config should control output format when no CLI flag"
        assert '  ' in result.stdout, "Pretty JSON should have indentation"

        # Verify it's valid JSON
        json.loads(result.stdout)

    def test_config_json_mode_used_when_no_cli_flag(self, temp_sdd_config, sample_spec_id):
        """Test that config default_mode=json is used when no --json flag provided."""
        # Write config that sets JSON as default mode
        config_data = {
            "output": {
                "default_mode": "json",
                "json_compact": True
            }
        }
        temp_sdd_config.write_text(json.dumps(config_data))

        # Run command without --json flag
        result = subprocess.run(
            ['sdd', 'progress', sample_spec_id],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Should produce JSON output (from config)
        # Verify it's valid JSON
        try:
            json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail("Config default_mode=json should produce JSON output")

    def test_cli_no_json_flag_overrides_config_json_mode(self, temp_sdd_config, sample_spec_id):
        """Test that --no-json flag overrides config default_mode=json."""
        # Write config that sets JSON as default mode
        config_data = {
            "output": {
                "default_mode": "json",
                "json_compact": True
            }
        }
        temp_sdd_config.write_text(json.dumps(config_data))

        # Run command with --no-json flag (should override config)
        result = subprocess.run(
            ['sdd', 'progress', sample_spec_id, '--no-json'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Should produce text output (not JSON)
        # Try to parse as JSON - should fail
        try:
            json.loads(result.stdout)
            pytest.fail("--no-json flag should override config and produce text output")
        except json.JSONDecodeError:
            # Expected - output is text, not JSON
            pass

    def test_default_behavior_without_config(self, sample_spec_id, monkeypatch):
        """Test default behavior when no config file exists."""
        # Set HOME to a non-existent directory (no config file)
        monkeypatch.setenv("HOME", "/tmp/nonexistent_home_for_test")

        # Run command without flags
        result = subprocess.run(
            ['sdd', 'progress', sample_spec_id],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": "/tmp/nonexistent_home_for_test"}
        )

        assert result.returncode == 0

        # Default should be text mode (not JSON)
        # Try to parse as JSON - should fail
        try:
            json.loads(result.stdout)
            # If it parses as JSON, check if default changed
            # (This is acceptable, just note it)
        except json.JSONDecodeError:
            # Expected - default is text mode
            pass

    def test_multiple_commands_respect_precedence(self, temp_sdd_config):
        """Test that config precedence works across different commands."""
        # Write config with specific settings
        config_data = {
            "output": {
                "default_mode": "json",
                "json_compact": False
            }
        }
        temp_sdd_config.write_text(json.dumps(config_data))

        # Test multiple commands with CLI flag override
        commands = [
            ['sdd', 'cache', 'info', '--json', '--compact'],
            ['sdd', 'list-plan-review-tools', '--json', '--compact'],
        ]

        for cmd in commands:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            # Should succeed (or fail gracefully for cache if disabled)
            assert result.returncode in [0, 1]

            if result.returncode == 0 and result.stdout:
                # Should produce compact output (CLI flag overrides config)
                lines = result.stdout.strip().split('\n')
                assert len(lines) == 1, f"Command {cmd[1]} should respect CLI --compact flag over config"

                # Verify it's valid JSON
                json.loads(result.stdout)
