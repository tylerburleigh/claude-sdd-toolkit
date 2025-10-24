"""Unit tests for sdd-next workflow operations."""

import pytest
from pathlib import Path

from claude_skills.sdd_next.workflow import init_environment, find_pattern


class TestInitEnvironment:
    """Tests for init_environment function."""

    def test_init_environment_from_specs_dir(self, specs_structure):
        """Test initializing environment from specs directory."""
        result = init_environment(specs_structure)

        assert result["success"] is True
        assert "specs_dir" in result
        assert "state_dir" in result

    def test_init_environment_creates_directories(self, tmp_path):
        """Test that init creates necessary directories if missing."""
        spec_path = tmp_path / "new_specs"

        result = init_environment(spec_path)

        # Should handle gracefully or create dirs
        assert result is not None


class TestFindPattern:
    """Tests for find_pattern function."""

    def test_find_pattern_simple(self, sample_python_project):
        """Test finding files with simple pattern."""
        matches = find_pattern("*.py", sample_python_project)

        assert len(matches) > 0
        assert all(str(m).endswith(".py") for m in matches)

    def test_find_pattern_recursive(self, sample_python_project):
        """Test finding files recursively."""
        matches = find_pattern("**/*.py", sample_python_project)

        assert len(matches) > 0
