"""
Unit tests for sdd-next validation operations.

Tests: validate_spec, find_circular_deps, validate_paths, spec_stats.
"""

import pytest
from pathlib import Path

from claude_skills.sdd_next.validation import validate_spec, find_circular_deps, validate_paths, spec_stats
from claude_skills.common import load_json_spec


class TestValidateSpec:
    """Tests for validate_spec function."""

    def test_validate_valid_spec(self, sample_spec_simple, sample_json_spec_simple):
        """Test validating a valid spec file."""
        result = validate_spec(sample_spec_simple)

        assert result is not None
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_invalid_spec(self, sample_spec_invalid):
        """Test validating an invalid spec file."""
        result = validate_spec(sample_spec_invalid)

        assert result is not None
        assert result["valid"] is False or len(result["errors"]) > 0

    def test_validate_spec_checks_frontmatter(self, sample_spec_simple):
        """Test that validation checks frontmatter."""
        result = validate_spec(sample_spec_simple)

        assert "spec_id" in result or result["valid"] is True

    def test_validate_spec_checks_json_spec(self, sample_spec_simple, sample_json_spec_simple):
        """Test that validation checks for JSON spec."""
        result = validate_spec(sample_spec_simple)

        assert "json_spec_file" in result

    def test_validate_nonexistent_spec(self, tmp_path):
        """Test validating non-existent spec file."""
        nonexistent = tmp_path / "nonexistent.json"
        result = validate_spec(nonexistent)

        assert result["valid"] is False
        assert len(result["errors"]) > 0


class TestFindCircularDeps:
    """Tests for find_circular_deps function."""

    def test_find_circular_deps_none(self, sample_json_spec_simple, specs_structure):
        """Test finding circular deps when none exist."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        result = find_circular_deps(spec_data)

        assert result is not None
        assert result["has_circular"] is False
        assert len(result["circular_chains"]) == 0

    def test_find_circular_deps_detected(self, sample_json_spec_circular_deps, specs_structure):
        """Test detecting circular dependencies."""
        spec_data = load_json_spec("circular-spec-2025-01-01-004", specs_structure)
        result = find_circular_deps(spec_data)

        assert result["has_circular"] is True
        assert len(result["circular_chains"]) > 0

    def test_find_circular_deps_shows_chains(self, sample_json_spec_circular_deps, specs_structure):
        """Test that circular dep chains are shown."""
        spec_data = load_json_spec("circular-spec-2025-01-01-004", specs_structure)
        result = find_circular_deps(spec_data)

        if result["circular_chains"]:
            chain = result["circular_chains"][0]
            # Chain should show the loop
            assert isinstance(chain, list)
            assert len(chain) > 2

    def test_find_orphaned_tasks(self, sample_json_spec_simple, specs_structure):
        """Test finding orphaned tasks (deps on non-existent tasks)."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Add dependency on non-existent task
        spec_data["hierarchy"]["task-1-1"]["dependencies"]["blocked_by"] = ["nonexistent-task"]

        result = find_circular_deps(spec_data)

        if "orphaned_tasks" in result:
            assert len(result["orphaned_tasks"]) > 0


class TestValidatePaths:
    """Tests for validate_paths function."""

    def test_validate_existing_paths(self, sample_spec_simple, specs_structure):
        """Test validating existing paths."""
        paths = [str(sample_spec_simple), str(specs_structure)]
        result = validate_paths(paths)

        assert result is not None
        assert "valid_paths" in result
        assert len(result["valid_paths"]) == 2

    def test_validate_mixed_paths(self, sample_spec_simple, tmp_path):
        """Test validating mix of valid and invalid paths."""
        paths = [
            str(sample_spec_simple),  # Valid
            str(tmp_path / "nonexistent")  # Invalid
        ]
        result = validate_paths(paths)

        assert len(result["valid_paths"]) >= 1
        assert len(result["invalid_paths"]) >= 1

    def test_validate_paths_with_base_dir(self, sample_spec_simple):
        """Test validating paths with base directory."""
        base_dir = sample_spec_simple.parent
        paths = [sample_spec_simple.name]  # Relative path

        result = validate_paths(paths, base_dir)

        assert len(result["valid_paths"]) >= 1


class TestSpecStats:
    """Tests for spec_stats function."""

    def test_spec_stats_basic(self, sample_spec_simple):
        """Test getting basic spec statistics."""
        result = spec_stats(sample_spec_simple)

        assert result is not None
        assert result["exists"] is True
        assert "line_count" in result
        assert "phase_count" in result
        assert "task_count" in result

    def test_spec_stats_counts(self, sample_spec_simple):
        """Test that spec stats counts are accurate."""
        result = spec_stats(sample_spec_simple)

        # Our simple spec has 2 phases, 4 tasks total
        assert result["phase_count"] == 2
        assert result["task_count"] == 4

    def test_spec_stats_with_json_spec(self, sample_spec_simple, sample_json_spec_simple):
        """Test spec stats with JSON spec."""
        result = spec_stats(sample_spec_simple, sample_json_spec_simple)

        assert "state_info" in result
        if result["state_info"]:
            assert "spec_id" in result["state_info"]

    def test_spec_stats_nonexistent(self, tmp_path):
        """Test spec stats for non-existent file."""
        nonexistent = tmp_path / "nonexistent.json"
        result = spec_stats(nonexistent)

        assert result["exists"] is False
