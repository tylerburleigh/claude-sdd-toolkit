"""Integration tests for sdd-validate CLI.

Note: Tests updated to use unified CLI (sdd validate) instead of legacy sdd-validate.
"""

import json
import pytest
import subprocess
import sys
import shutil
from pathlib import Path


# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sdd_validate"
CLEAN_SPEC = FIXTURES_DIR / "clean_spec.json"
WARNINGS_SPEC = FIXTURES_DIR / "warnings_spec.json"
ERRORS_SPEC = FIXTURES_DIR / "errors_spec.json"
AUTOFIX_SPEC = FIXTURES_DIR / "auto_fix_spec.json"
DEPENDENCY_SPEC = FIXTURES_DIR / "dependency_spec.json"
DEEP_HIERARCHY_SPEC = FIXTURES_DIR / "deep_hierarchy_spec.json"


def run_cli(*args, check=False):
    """Helper to run sdd CLI with unified command (sdd-validate commands)."""
    # Try unified CLI first
    if shutil.which("sdd"):
        cmd = ["sdd"] + list(args)
    else:
        # Fallback to python -m
        cmd = [sys.executable, "-m", "claude_skills.cli.sdd"] + list(args)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check,
    )
    return result


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_clean_spec_exit_0(self):
        """Clean spec should exit with code 0."""
        result = run_cli("validate", str(CLEAN_SPEC))
        assert result.returncode == 0
        assert "Validation PASSED" in result.stdout or "✅" in result.stdout

    def test_validate_warnings_spec_exit_1(self):
        """Warnings-only spec should exit with code 1."""
        result = run_cli("validate", str(WARNINGS_SPEC))
        assert result.returncode == 1
        assert "warnings" in result.stderr.lower()

    def test_validate_errors_spec_exit_2(self):
        """Spec with errors should exit with code 2."""
        result = run_cli("validate", str(ERRORS_SPEC))
        assert result.returncode == 2
        assert "FAILED" in result.stderr or "❌" in result.stderr

    def test_validate_json_output(self):
        """Test --json output format."""
        result = run_cli("--json", "validate", str(CLEAN_SPEC))
        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert "spec_id" in data
        assert "errors" in data
        assert "warnings" in data
        assert "status" in data
        assert data["status"] in ["valid", "warnings", "errors"]

    def test_validate_json_verbose(self):
        """Test --json --verbose output includes issues array."""
        result = run_cli("--json", "--verbose", "validate", str(WARNINGS_SPEC))

        data = json.loads(result.stdout)
        assert "issues" in data
        assert isinstance(data["issues"], list)

    def test_validate_verbose_output(self):
        """Test --verbose flag shows detailed output."""
        result = run_cli("--verbose", "validate", str(WARNINGS_SPEC))
        # Verbose should show more details
        assert "ERROR" in result.stdout or "WARN" in result.stdout or len(result.stdout) > 100

    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file returns exit 2."""
        result = run_cli("validate", "/nonexistent/file.json")
        assert result.returncode == 2
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_validate_with_report(self, tmp_path):
        """Test --report flag generates report file."""
        # Copy spec to temp dir so report can be written alongside
        import shutil
        spec_copy = tmp_path / "test_spec.json"
        shutil.copy(CLEAN_SPEC, spec_copy)

        result = run_cli("validate", str(spec_copy), "--report")
        assert result.returncode == 0

        # Check that report was created
        report_file = tmp_path / "test_spec-validation-report.md"
        assert report_file.exists()

    def test_validate_with_report_json_format(self, tmp_path):
        """Test --report with --report-format json."""
        import shutil
        spec_copy = tmp_path / "test_spec.json"
        shutil.copy(CLEAN_SPEC, spec_copy)

        result = run_cli("validate", str(spec_copy), "--report", "--report-format", "json")
        assert result.returncode == 0

        report_file = tmp_path / "test_spec-validation-report.json"
        assert report_file.exists()

        with open(report_file) as f:
            data = json.load(f)
            assert "summary" in data
            assert "dependencies" in data


class TestFixCommand:
    """Tests for the fix command."""

    def test_fix_preview_clean_spec(self):
        """Preview on clean spec shows no actions."""
        result = run_cli("fix", str(CLEAN_SPEC), "--preview")
        assert result.returncode == 0
        assert "No auto-fixable issues" in result.stdout or "0" in result.stdout

    def test_fix_preview_with_issues(self):
        """Preview on spec with issues shows actions."""
        result = run_cli("fix", str(AUTOFIX_SPEC), "--preview")
        assert result.returncode == 0
        assert "auto-fixable" in result.stdout.lower() or "issue" in result.stdout.lower()

    def test_fix_preview_json(self):
        """Test fix preview with --json output."""
        result = run_cli("--json", "fix", str(AUTOFIX_SPEC), "--preview")
        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert "actions" in data or "skipped" in data
        assert "status" in data

    def test_fix_dry_run(self):
        """Test --dry-run is alias for --preview."""
        result = run_cli("fix", str(AUTOFIX_SPEC), "--dry-run")
        assert result.returncode == 0

    def test_fix_apply_creates_backup(self, tmp_path):
        """Test that fix creates backup by default."""
        import shutil
        spec_copy = tmp_path / "test_spec.json"
        shutil.copy(AUTOFIX_SPEC, spec_copy)

        result = run_cli("fix", str(spec_copy))

        # Backup should be created
        backup_file = tmp_path / "test_spec.json.backup"
        assert backup_file.exists()

    def test_fix_apply_no_backup(self, tmp_path):
        """Test --no-backup flag skips backup creation."""
        import shutil
        spec_copy = tmp_path / "test_spec.json"
        shutil.copy(AUTOFIX_SPEC, spec_copy)

        result = run_cli("fix", str(spec_copy), "--no-backup")

        # No backup should be created
        backup_file = tmp_path / "test_spec.json.backup"
        assert not backup_file.exists()

    def test_fix_apply_json_output(self, tmp_path):
        """Test fix with --json output."""
        import shutil
        spec_copy = tmp_path / "test_spec.json"
        shutil.copy(AUTOFIX_SPEC, spec_copy)

        result = run_cli("--json", "fix", str(spec_copy), "--no-backup")

        data = json.loads(result.stdout)
        assert "applied_action_count" in data or "skipped_action_count" in data


class TestReportCommand:
    """Tests for the report command."""

    def test_report_markdown(self, tmp_path):
        """Test generating markdown report."""
        output_file = tmp_path / "report.md"
        result = run_cli("report", str(CLEAN_SPEC), "--output", str(output_file))
        assert result.returncode == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "# Validation Report" in content

    def test_report_json(self, tmp_path):
        """Test generating JSON report."""
        output_file = tmp_path / "report.json"
        result = run_cli("report", str(CLEAN_SPEC), "--format", "json", "--output", str(output_file))
        assert result.returncode == 0
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)
            assert "summary" in data
            assert "stats" in data
            assert "dependencies" in data

    def test_report_stdout(self):
        """Test report to stdout with --output -"""
        result = run_cli("report", str(CLEAN_SPEC), "--output", "-")
        assert result.returncode == 0
        assert "# Validation Report" in result.stdout

    def test_report_with_dependencies(self):
        """Test report includes dependency analysis."""
        result = run_cli("report", str(DEPENDENCY_SPEC), "--output", "-")
        assert result.returncode == 0
        assert "Dependency" in result.stdout or "dependencies" in result.stdout.lower()

    def test_report_json_stdout(self):
        """Test JSON report to stdout."""
        result = run_cli("report", str(CLEAN_SPEC), "--format", "json", "--output", "-")
        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert "summary" in data

    def test_report_with_bottleneck_threshold(self, tmp_path):
        """Test report with custom bottleneck threshold."""
        output_file = tmp_path / "report.md"
        result = run_cli(
            "report",
            str(DEPENDENCY_SPEC),
            "--output",
            str(output_file),
            "--bottleneck-threshold",
            "2",
        )
        assert result.returncode == 0


class TestStatsCommand:
    """Tests for the stats command."""

    def test_stats_basic(self):
        """Test basic stats output."""
        result = run_cli("stats", str(CLEAN_SPEC))
        assert result.returncode == 0
        assert "Spec ID" in result.stdout or "spec_id" in result.stdout

    def test_stats_json(self):
        """Test stats with --json output."""
        result = run_cli("--json", "stats", str(CLEAN_SPEC))
        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert "spec_id" in data
        assert "totals" in data
        assert "max_depth" in data
        assert "progress" in data

    def test_stats_deep_hierarchy(self):
        """Test stats on deep hierarchy spec."""
        result = run_cli("--json", "stats", str(DEEP_HIERARCHY_SPEC))
        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert data["max_depth"] >= 4  # Should detect deep nesting

    def test_stats_verification_coverage(self):
        """Test verification coverage calculation."""
        result = run_cli("--json", "stats", str(DEEP_HIERARCHY_SPEC))
        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert "verification_coverage" in data
        assert 0 <= data["verification_coverage"] <= 1.0


class TestCheckDepsCommand:
    """Tests for the check-deps command."""

    def test_check_deps_clean_spec(self):
        """Test check-deps on clean spec with no issues."""
        result = run_cli("analyze-deps", str(CLEAN_SPEC))
        assert result.returncode == 0

    def test_check_deps_with_cycles(self):
        """Test check-deps detects cycles."""
        result = run_cli("analyze-deps", str(DEPENDENCY_SPEC))
        assert result.returncode == 1  # Issues found
        assert "cycle" in result.stdout.lower() or "Cycles" in result.stdout

    def test_check_deps_json(self):
        """Test check-deps with --json output."""
        result = run_cli("--json", "analyze-deps", str(DEPENDENCY_SPEC))

        data = json.loads(result.stdout)
        assert "cycles" in data
        assert "orphaned" in data
        assert "deadlocks" in data
        assert "bottlenecks" in data
        assert "status" in data

    def test_check_deps_with_bottleneck_threshold(self):
        """Test check-deps with custom bottleneck threshold."""
        result = run_cli("analyze-deps", str(DEPENDENCY_SPEC), "--bottleneck-threshold", "2")
        # Should still run successfully
        assert result.returncode in [0, 1]  # 0 if no issues, 1 if issues found

    def test_check_deps_orphaned(self):
        """Test check-deps detects orphaned dependencies."""
        result = run_cli("analyze-deps", str(DEPENDENCY_SPEC))
        assert "orphan" in result.stdout.lower() or "missing" in result.stdout.lower()


class TestGlobalFlags:
    """Tests for global flags."""

    def test_quiet_flag(self):
        """Test --quiet suppresses progress messages."""
        result = run_cli("--quiet", "validate", str(CLEAN_SPEC))
        # Quiet mode should have minimal output
        assert len(result.stdout) < 500

    def test_no_color_flag(self):
        """Test --no-color flag."""
        result = run_cli("--no-color", "validate", str(CLEAN_SPEC))
        # Should still work, just without color codes
        assert result.returncode == 0

    def test_verbose_flag(self):
        """Test --verbose flag shows more details."""
        result = run_cli("--verbose", "validate", str(WARNINGS_SPEC))
        # Verbose should have more output
        assert len(result.stdout) > 100

    def test_help_flag(self):
        """Test --help shows usage information."""
        result = run_cli("--help")
        assert result.returncode == 0 or result.returncode == 1  # Some CLIs use 0, some use 1 for help
        assert "usage" in result.stdout.lower() or "sdd-validate" in result.stdout.lower()


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_command(self):
        """Test invalid command returns error."""
        result = run_cli("invalid-command", str(CLEAN_SPEC))
        assert result.returncode != 0

    def test_missing_spec_file_argument(self):
        """Test missing spec file argument."""
        result = run_cli("validate")
        assert result.returncode != 0

    def test_invalid_json_file(self, tmp_path):
        """Test validation of invalid JSON file."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{invalid json}")

        result = run_cli("validate", str(bad_json))
        assert result.returncode == 2
        assert "json" in result.stderr.lower() or "json" in result.stdout.lower()
