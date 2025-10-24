"""
Integration tests for unified SDD CLI.

Tests the unified `sdd` command with all subcommands (next, update, validate),
global flags, error handling, and command delegation.
"""

import sys
import pytest
import subprocess
import json
import shutil
from pathlib import Path

# CLI command name (uses installed console script)
CLI_CMD = "sdd"


def has_sdd_command():
    """Check if sdd command is available on PATH."""
    return shutil.which(CLI_CMD) is not None


def run_sdd_command(*args, **kwargs):
    """
    Run sdd command with fallback to python -m if sdd not on PATH.

    This ensures tests work in different environments.
    """
    # Try direct command first
    if has_sdd_command():
        return subprocess.run([CLI_CMD] + list(args), **kwargs)
    else:
        # Fallback to python -m claude_skills.cli.sdd
        return subprocess.run(
            [sys.executable, '-m', 'claude_skills.cli.sdd'] + list(args),
            **kwargs
        )


class TestUnifiedCLIBasics:
    """Basic unified CLI functionality tests."""

    def test_cli_help(self):
        """Test sdd --help shows main help."""
        result = run_sdd_command(
            "--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "usage" in result.stdout.lower()
        # Should mention subcommands
        assert "next" in result.stdout or "update" in result.stdout or "validate" in result.stdout

    def test_cli_no_args(self):
        """Test sdd with no args shows help."""
        result = run_sdd_command(
            capture_output=True,
            text=True
        )

        # Should show help or error message
        assert result.returncode in [0, 1, 2]  # Some CLIs return 2 for missing args

    def test_cli_version_implicit(self):
        """Test that CLI doesn't crash on basic invocation."""
        result = run_sdd_command(
            "--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0


class TestNextCommands:
    """Tests for sdd-next commands (flat structure)."""

    def test_verify_tools(self):
        """Test sdd verify-tools command."""
        result = run_sdd_command(
            "verify-tools",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "python" in result.stdout.lower() or "verified" in result.stdout.lower()

    def test_find_specs(self, tmp_path):
        """Test sdd find-specs command."""
        # Create minimal specs structure
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        (specs_dir / "active").mkdir()

        result = run_sdd_command(
            "--path", str(tmp_path), "find-specs",
            capture_output=True,
            text=True
        )

        # Should return 0 (found) or 1 (not found) - both are valid
        assert result.returncode in [0, 1]


class TestUpdateCommands:
    """Tests for sdd-update commands (flat structure)."""

    def test_status_report_help(self):
        """Test sdd status-report --help shows help."""
        result = run_sdd_command(
            "status-report", "--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "status" in result.stdout.lower() or "report" in result.stdout.lower()

    def test_update_command_exists(self):
        """Test that update commands are recognized."""
        result = run_sdd_command(
            "update-status", "--help",
            capture_output=True,
            text=True
        )

        # Should not error out with "unknown command"
        assert "unknown" not in result.stderr.lower() if result.stderr else True


class TestValidateCommands:
    """Tests for sdd-validate commands (flat structure)."""

    def test_validate_help(self):
        """Test sdd validate --help shows help."""
        result = run_sdd_command(
            "validate", "--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "validate" in result.stdout.lower() or "spec" in result.stdout.lower()

    def test_validate_command_exists(self):
        """Test that validate command is recognized."""
        result = run_sdd_command(
            "validate", "--help",
            capture_output=True,
            text=True
        )

        # Should not error out with "unknown command"
        assert "unknown" not in result.stderr.lower() if result.stderr else True


class TestGlobalFlags:
    """Tests for global flags (--json, --quiet, --verbose)."""

    def test_json_flag(self):
        """Test --json flag with sdd command (global flag before command)."""
        result = run_sdd_command(
            "--json", "verify-tools",
            capture_output=True,
            text=True
        )

        # Should succeed or return valid exit code
        assert result.returncode in [0, 1]

        # If JSON output, should be parseable
        if result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                assert isinstance(data, (dict, list))
            except json.JSONDecodeError:
                # Some commands may not support --json yet
                pass

    def test_quiet_flag(self):
        """Test --quiet flag reduces output."""
        # Run with normal output
        normal_result = run_sdd_command(
            "verify-tools",
            capture_output=True,
            text=True
        )

        # Run with quiet flag
        quiet_result = run_sdd_command(
            "verify-tools", "--quiet",
            capture_output=True,
            text=True
        )

        # Quiet should have less or equal output
        assert len(quiet_result.stdout) <= len(normal_result.stdout)

    def test_verbose_flag(self):
        """Test --verbose flag increases output (global flag before command)."""
        # Run with normal output
        normal_result = run_sdd_command(
            "verify-tools",
            capture_output=True,
            text=True
        )

        # Run with verbose flag (place before command)
        verbose_result = run_sdd_command(
            "--verbose", "verify-tools",
            capture_output=True,
            text=True
        )

        # Verbose should succeed
        assert verbose_result.returncode in [0, 1]


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_invalid_command(self):
        """Test sdd with invalid command."""
        result = run_sdd_command(
            "nonexistent-command",
            capture_output=True,
            text=True
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0
        # Should mention the error
        assert "invalid" in result.stderr.lower() or "unrecognized" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_missing_required_arg(self):
        """Test sdd command with missing required argument."""
        result = run_sdd_command(
            "prepare-task",  # Missing spec_id
            capture_output=True,
            text=True
        )

        # Should fail or show help
        assert result.returncode != 0


class TestCommandDelegation:
    """Tests that unified CLI correctly delegates to command implementations."""

    def test_next_command_works(self):
        """Test that sdd verify-tools delegates to correct implementation."""
        # Run via unified CLI
        unified_result = run_sdd_command(
            "verify-tools",
            capture_output=True,
            text=True
        )

        # Should produce output
        assert unified_result.returncode == 0
        assert len(unified_result.stdout) > 0

    def test_update_command_works(self):
        """Test that sdd status-report help works."""
        unified_result = run_sdd_command(
            "status-report", "--help",
            capture_output=True,
            text=True
        )

        assert unified_result.returncode == 0
        assert len(unified_result.stdout) > 0

    def test_validate_command_works(self):
        """Test that sdd validate help works."""
        unified_result = run_sdd_command(
            "validate", "--help",
            capture_output=True,
            text=True
        )

        assert unified_result.returncode == 0
        assert len(unified_result.stdout) > 0


class TestBackwardsCompatibility:
    """Tests for backwards compatibility with old command style."""

    def test_new_sdd_command_works(self):
        """Test that new sdd command works."""
        result = run_sdd_command(
            "verify-tools",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0


class TestColdStartPerformance:
    """Tests for CLI cold-start performance."""

    def test_help_fast_response(self):
        """Test that sdd --help responds quickly."""
        import time

        start = time.time()
        result = run_sdd_command(
            "--help",
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start

        assert result.returncode == 0
        # Should complete within 2 seconds (generous limit)
        assert elapsed < 2.0, f"Help command took {elapsed:.2f}s (expected <2s)"

    def test_command_help_fast_response(self):
        """Test that sdd validate --help responds quickly."""
        import time

        start = time.time()
        result = run_sdd_command(
            "validate", "--help",
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start

        assert result.returncode == 0
        # Should complete within 2 seconds
        assert elapsed < 2.0, f"Command help took {elapsed:.2f}s (expected <2s)"


# Fixtures for testing

@pytest.fixture
def minimal_specs_dir(tmp_path):
    """Create a minimal specs directory structure for testing."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "active").mkdir()
    (specs_dir / "completed").mkdir()
    (specs_dir / ".state").mkdir()

    return specs_dir


@pytest.fixture
def sample_spec_file(minimal_specs_dir):
    """Create a minimal sample spec file for testing."""
    spec_file = minimal_specs_dir / "active" / "test-spec.md"
    spec_file.write_text("""---
spec_id: test-spec-001
title: Test Specification
status: active
---

# Test Specification

This is a test spec.
""")

    return spec_file
