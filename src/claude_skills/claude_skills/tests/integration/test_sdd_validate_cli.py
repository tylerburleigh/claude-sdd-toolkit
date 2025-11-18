"""Integration tests for sdd-validate CLI.

Note: Tests updated to use unified CLI (sdd validate) instead of legacy sdd-validate.
"""

import builtins
import json
import shutil
import sys
from pathlib import Path

import pytest

from claude_skills.common import hierarchy_validation
from .cli_runner import run_cli
def run_cli_no_json(*args: object):
    """Invoke CLI with global --no-json flag to force text output."""
    return run_cli("--no-json", *args)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sdd_validate"
CLEAN_SPEC = FIXTURES_DIR / "clean_spec.json"
WARNINGS_SPEC = FIXTURES_DIR / "warnings_spec.json"
ERRORS_SPEC = FIXTURES_DIR / "errors_spec.json"
AUTOFIX_SPEC = FIXTURES_DIR / "auto_fix_spec.json"
DEPENDENCY_SPEC = FIXTURES_DIR / "dependency_spec.json"
DEEP_HIERARCHY_SPEC = FIXTURES_DIR / "deep_hierarchy_spec.json"
class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_clean_spec_exit_0(self):
        """Clean spec should exit with code 0."""
        result = run_cli_no_json("validate", str(CLEAN_SPEC))
        assert result.returncode == 0
        combined_output = "".join(part or "" for part in (result.stdout, result.stderr))
        assert "Validation PASSED" in combined_output or "✅" in combined_output

    def test_validate_warnings_spec_exit_1(self):
        """Warnings-only spec should exit with code 1."""
        result = run_cli_no_json("validate", str(WARNINGS_SPEC))
        assert result.returncode == 1
        combined_output = "".join(part or "" for part in (result.stdout, result.stderr))
        assert "warnings" in combined_output.lower()

    def test_validate_errors_spec_exit_2(self):
        """Spec with errors should exit with code 2."""
        result = run_cli_no_json("validate", str(ERRORS_SPEC))
        assert result.returncode == 2
        combined_output = "".join(part or "" for part in (result.stdout, result.stderr))
        assert "failed" in combined_output.lower() or "❌" in combined_output

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
        assert "schema" in data
        assert "source" in data["schema"]

    def test_validate_compact_vs_pretty(self):
        """Validate command should honor compact flags."""
        compact_result = run_cli("--json", "--compact", "validate", str(CLEAN_SPEC))
        assert compact_result.returncode == 0
        assert len(compact_result.stdout.strip().splitlines()) == 1
        compact_data = json.loads(compact_result.stdout)

        pretty_result = run_cli("--json", "--no-compact", "validate", str(CLEAN_SPEC))
        assert pretty_result.returncode == 0
        assert len(pretty_result.stdout.strip().splitlines()) > 1
        assert json.loads(pretty_result.stdout) == compact_data

    def test_validate_json_verbose(self):
        """Test --json --verbose output includes issues array."""
        result = run_cli("--json", "--verbose", "validate", str(WARNINGS_SPEC))

        data = json.loads(result.stdout)
        assert "issues" in data
        assert isinstance(data["issues"], list)

    def test_validate_verbose_output(self):
        """Test --verbose flag shows detailed output."""
        result = run_cli_no_json("--verbose", "validate", str(WARNINGS_SPEC))
        # Verbose should show more details
        assert "ERROR" in result.stdout or "WARN" in result.stdout or len(result.stdout) > 100

    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file returns exit 3."""
        result = run_cli_no_json("validate", "/nonexistent/file.json")
        assert result.returncode == 3
        combined_output = "".join(part or "" for part in (result.stdout, result.stderr))
        assert "not found" in combined_output.lower()

    def test_validate_with_report(self, tmp_path):
        """Test --report flag generates report file."""
        # Copy spec to temp dir so report can be written alongside
        import shutil
        spec_copy = tmp_path / "test_spec.json"
        shutil.copy(CLEAN_SPEC, spec_copy)

        result = run_cli_no_json("validate", str(spec_copy), "--report")
        assert result.returncode == 0

        # Check that report was created
        report_file = tmp_path / "test_spec-validation-report.md"
        assert report_file.exists()

    def test_validate_with_report_json_format(self, tmp_path):
        """Test --report with --report-format json."""
        import shutil
        spec_copy = tmp_path / "test_spec.json"
        shutil.copy(CLEAN_SPEC, spec_copy)

        result = run_cli_no_json("validate", str(spec_copy), "--report", "--report-format", "json")
        assert result.returncode == 0

        report_file = tmp_path / "test_spec-validation-report.json"
        assert report_file.exists()

        with open(report_file) as f:
            data = json.load(f)
            assert "summary" in data
            assert "dependencies" in data

    def test_validate_report_json_includes_schema_details(self, tmp_path):
        """Report output should embed schema source and issues."""
        spec_copy = tmp_path / "schema_spec.json"
        spec_data = json.loads(CLEAN_SPEC.read_text())
        # Introduce schema violations to trigger error reporting
        spec_data["hierarchy"] = []  # invalid type (should be object)
        spec_copy.write_text(json.dumps(spec_data))

        result = run_cli_no_json(
            "validate",
            str(spec_copy),
            "--report",
            "--report-format",
            "json",
        )

        # Schema errors should propagate to exit status
        assert result.returncode == 2

        report_file = spec_copy.with_name("schema_spec-validation-report.json")
        assert report_file.exists()

        report_data = json.loads(report_file.read_text())
        schema_section = report_data.get("schema", {})
        assert schema_section.get("errors")
        assert schema_section.get("source")

    def test_validate_gracefully_handles_missing_jsonschema(self, monkeypatch):
        """Missing optional dependency should emit warning but not fail validation."""

        orig_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("mock missing jsonschema")
            return orig_import(name, *args, **kwargs)

        monkeypatch.delitem(sys.modules, "jsonschema", raising=False)
        monkeypatch.setattr(builtins, "__import__", fake_import)

        # Ensure schema loader still returns a schema so we exercise the fallback path.
        monkeypatch.setattr(
            hierarchy_validation,
            "load_json_schema",
            lambda name: ({"type": "object"}, "package://schema", None),
        )

        result = run_cli_no_json("validate", str(CLEAN_SPEC))
        assert result.returncode == 0

        combined = (result.stdout or "") + (result.stderr or "")
        assert "Validation PASSED" in combined

    def test_validate_cli_surfaces_schema_errors(self, tmp_path):
        """Schema failures should be reported to the user."""
        spec_copy = tmp_path / "invalid_schema.json"
        spec_data = json.loads(CLEAN_SPEC.read_text())
        spec_data["hierarchy"] = []  # invalid type to trigger schema error
        spec_copy.write_text(json.dumps(spec_data))

        result = run_cli_no_json("validate", str(spec_copy))

        assert result.returncode == 2
        combined_output = "".join(part or "" for part in (result.stdout, result.stderr))
        assert "Schema source:" in combined_output
        assert ("Schema validation errors" in combined_output or "Schema violation" in combined_output or "Issues:" in combined_output)
        assert "Schema violation" in combined_output

    def test_validate_json_includes_schema_details(self, tmp_path):
        """JSON output should include schema source and issues."""

        spec_copy = tmp_path / "schema_warning.json"
        spec_data = json.loads(CLEAN_SPEC.read_text())
        # Introduce schema issue to trigger warnings/errors
        spec_data["hierarchy"] = []  # invalid type
        spec_copy.write_text(json.dumps(spec_data))

        result = run_cli("--json", "validate", str(spec_copy))
        assert result.returncode == 2

        data = json.loads(result.stdout)
        assert data["schema"]["source"].endswith("sdd-spec-schema.json") or data["schema"]["source"].startswith("package:")
        assert data["schema"]["errors"] or data["schema"]["warnings"]

    def test_validate_pending_only_directory(self, tmp_path):
        """Test that specs directory with only pending/ subdirectory is recognized."""
        # Create a specs directory with only pending/ subdirectory
        specs_dir = tmp_path / "specs"
        pending_dir = specs_dir / "pending"
        pending_dir.mkdir(parents=True)

        # Copy a clean spec to the pending directory
        spec_copy = pending_dir / "test_spec.json"
        shutil.copy(CLEAN_SPEC, spec_copy)

        # Should be able to find and validate the spec by name from the tmp_path directory
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = run_cli_no_json("validate", "test_spec")
            assert result.returncode == 0
        finally:
            os.chdir(original_dir)

    def test_fix_pending_only_directory_save(self, tmp_path):
        """Test that fix can save to specs directory with only pending/ subdirectory."""
        # Create a specs directory with only pending/ subdirectory
        specs_dir = tmp_path / "specs"
        pending_dir = specs_dir / "pending"
        pending_dir.mkdir(parents=True)

        # Copy a fixable spec to the pending directory
        spec_copy = pending_dir / "test_spec.json"
        shutil.copy(AUTOFIX_SPEC, spec_copy)

        # Apply fixes
        result = run_cli_no_json("fix", str(spec_copy), "--no-backup")

        # Should succeed without "Spec file not found" error
        assert result.returncode == 0
        combined_output = "".join(part or "" for part in (result.stdout, result.stderr))
        assert "Spec file not found" not in combined_output


class TestFixCommand:
    """Tests for the fix command."""

    def test_fix_preview_clean_spec(self):
        """Preview on clean spec shows no actions."""
        result = run_cli_no_json("fix", str(CLEAN_SPEC), "--preview")
        assert result.returncode == 0
        assert "No auto-fixable issues" in result.stdout or "0" in result.stdout

    def test_fix_preview_with_issues(self):
        """Preview on spec with issues shows actions."""
        result = run_cli_no_json("fix", str(AUTOFIX_SPEC), "--preview")
        assert result.returncode == 0
        assert "auto-fixable" in result.stdout.lower() or "issue" in result.stdout.lower()

    def test_fix_preview_json(self):
        """Test fix preview with --json output."""
        result = run_cli("--json", "fix", str(AUTOFIX_SPEC), "--preview")
        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert "actions" in data or "skipped" in data
        assert "status" in data

    def test_fix_preview_compact_json(self):
        """Fix preview should emit compact JSON when requested."""
        result = run_cli("--json", "--compact", "fix", str(AUTOFIX_SPEC), "--preview")
        assert result.returncode == 0
        assert len(result.stdout.strip().splitlines()) == 1
        data = json.loads(result.stdout)
        assert data["status"] in {"preview", "dry_run"}

    def test_fix_dry_run(self):
        """Test --dry-run is alias for --preview."""
        result = run_cli_no_json("fix", str(AUTOFIX_SPEC), "--dry-run")
        assert result.returncode == 0

    def test_fix_apply_creates_backup(self, tmp_path):
        """Test that fix creates backup by default."""
        import shutil
        spec_copy = tmp_path / "test_spec.json"
        shutil.copy(AUTOFIX_SPEC, spec_copy)

        result = run_cli_no_json("fix", str(spec_copy))

        # Backup should be created
        backup_file = tmp_path / "test_spec.json.backup"
        assert backup_file.exists()

    def test_fix_apply_no_backup(self, tmp_path):
        """Test --no-backup flag skips backup creation."""
        import shutil
        spec_copy = tmp_path / "test_spec.json"
        shutil.copy(AUTOFIX_SPEC, spec_copy)

        result = run_cli_no_json("fix", str(spec_copy), "--no-backup")

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
        result = run_cli("report", str(CLEAN_SPEC), "--format", "markdown", "--output", str(output_file))
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
        result = run_cli("report", str(CLEAN_SPEC), "--format", "markdown", "--output", "-")
        assert result.returncode == 0
        assert "# Validation Report" in result.stdout

    def test_report_with_dependencies(self):
        """Test report includes dependency analysis."""
        result = run_cli("report", str(DEPENDENCY_SPEC), "--format", "markdown", "--output", "-")
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
            "--format",
            "markdown",
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

    def test_stats_compact_vs_pretty(self):
        """Stats output should respect compact flags."""
        compact_result = run_cli("--json", "--compact", "stats", str(CLEAN_SPEC))
        assert compact_result.returncode == 0
        assert len(compact_result.stdout.strip().splitlines()) == 1
        compact_data = json.loads(compact_result.stdout)

        pretty_result = run_cli("--json", "--no-compact", "stats", str(CLEAN_SPEC))
        assert pretty_result.returncode == 0
        assert len(pretty_result.stdout.strip().splitlines()) > 1
        assert json.loads(pretty_result.stdout) == compact_data

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

    def test_check_deps_compact_vs_pretty(self):
        """check-deps should emit compact JSON on demand."""
        compact_result = run_cli("--json", "--compact", "analyze-deps", str(DEPENDENCY_SPEC))
        assert compact_result.returncode in (0, 1)
        assert len(compact_result.stdout.strip().splitlines()) == 1
        compact_data = json.loads(compact_result.stdout)

        pretty_result = run_cli("--json", "--no-compact", "analyze-deps", str(DEPENDENCY_SPEC))
        assert pretty_result.returncode in (0, 1)
        assert len(pretty_result.stdout.strip().splitlines()) > 1
        assert json.loads(pretty_result.stdout) == compact_data

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
        combined_output = "".join(part or "" for part in (result.stdout, result.stderr))
        assert "json" in combined_output.lower()
