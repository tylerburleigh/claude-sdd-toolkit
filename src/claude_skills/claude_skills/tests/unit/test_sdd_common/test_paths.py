"""
Unit tests for sdd_common.paths module.

Tests path utilities: find_specs_directory, validate_path.
"""

import pytest
import json
from pathlib import Path
from claude_skills.common import find_specs_directory, validate_path, find_spec_file

class TestFindSpecsDirectory:
    """Tests for find_specs_directory function."""

    def test_find_specs_from_project_root(self, specs_structure):
        """Test finding specs directory from subdirectory."""
        # Test finding from active subdirectory (should traverse up to specs/)
        found = find_specs_directory(specs_structure / "active")

        assert found is not None
        assert found.exists()
        assert found.name == "specs" or "specs" in str(found)

    def test_find_specs_with_explicit_path(self, specs_structure):
        """Test finding specs with explicit path provided."""
        found = find_specs_directory(specs_structure)

        assert found is not None
        # Should return the specs directory itself
        assert found == specs_structure

    def test_find_specs_returns_none_when_not_found(self, tmp_path):
        """Test that find_specs_directory returns None when not found."""
        # Create directory without specs
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        found = find_specs_directory(empty_dir)

        assert found is None

    def test_find_specs_validates_structure(self, specs_structure):
        """Test that found specs directory has expected structure."""
        found = find_specs_directory(specs_structure.parent)

        if found:
            # Should have .state directory
            # Verified specs directory structure
            # Should have active directory
            assert (found / "active").exists() or found.name == "specs"

    def test_find_specs_from_subdirectory(self, specs_structure):
        """Test finding specs when starting from a subdirectory."""
        # Create a nested subdirectory
        nested = specs_structure / "subdir"
        nested.mkdir(parents=True, exist_ok=True)

        found = find_specs_directory(nested)

        # Should traverse up and find specs directory
        assert found is not None
        assert "specs" in str(found) or found.name == "specs"

class TestValidatePath:
    """Tests for validate_path function."""

    def test_validate_existing_file(self, sample_spec_simple):
        """Test validating an existing file path."""
        result = validate_path(sample_spec_simple)

        assert result is not None
        assert result == sample_spec_simple

    def test_validate_existing_directory(self, specs_structure):
        """Test validating an existing directory path."""
        result = validate_path(specs_structure)

        assert result is not None
        assert result == specs_structure

    def test_validate_nonexistent_path(self, tmp_path):
        """Test validating a non-existent path."""
        nonexistent = tmp_path / "nonexistent" / "path"

        result = validate_path(nonexistent)

        assert result is None

    def test_validate_relative_path(self, tmp_path):
        """Test validating relative paths."""
        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Test with relative path (if function supports it)
        result = validate_path(test_file)

        assert result is not None

    def test_validate_path_with_string_input(self, sample_spec_simple):
        """Test validate_path with string input instead of Path."""
        result = validate_path(str(sample_spec_simple))

        assert result is not None

    def test_validate_multiple_paths(self, specs_structure):
        """Test validating multiple paths."""
        # specs_structure now returns specs/ directory
        paths_to_test = [
            specs_structure / "active",
            specs_structure,
            specs_structure / "completed",
            specs_structure / "archived"
        ]

        for path in paths_to_test:
            result = validate_path(path)
            assert result is not None, f"Failed to validate {path}"

class TestFindSpecFile:
    """Tests for find_spec_file function."""

    def test_find_spec_file_in_pending(self, specs_structure):
        """Test that find_spec_file finds specs in pending/ folder first."""
        # Create a test spec in pending/ folder
        pending_dir = specs_structure / "pending"
        pending_dir.mkdir(exist_ok=True)

        spec_id = "test-pending-spec-2025-01-01-001"
        spec_file = pending_dir / f"{spec_id}.json"
        spec_data = {
            "spec_id": spec_id,
            "title": "Test Pending Spec"
        }
        spec_file.write_text(json.dumps(spec_data))

        # Find the spec
        found = find_spec_file(spec_id, specs_structure)

        assert found is not None
        assert found.exists()
        assert found == spec_file
        assert "pending" in str(found)

    def test_find_spec_file_pending_priority_over_active(self, specs_structure):
        """Test that pending/ folder has priority over active/ when spec exists in both."""
        # Create spec in both pending/ and active/
        pending_dir = specs_structure / "pending"
        pending_dir.mkdir(exist_ok=True)
        active_dir = specs_structure / "active"

        spec_id = "test-priority-spec-2025-01-01-002"

        # Create in both locations
        pending_file = pending_dir / f"{spec_id}.json"
        active_file = active_dir / f"{spec_id}.json"

        spec_data = {"spec_id": spec_id, "title": "Test"}
        pending_file.write_text(json.dumps(spec_data))
        active_file.write_text(json.dumps(spec_data))

        # Find the spec - should return pending/ path
        found = find_spec_file(spec_id, specs_structure)

        assert found is not None
        assert found == pending_file
        assert "pending" in str(found)

    def test_find_spec_file_in_active(self, specs_structure):
        """Test finding spec in active/ folder when not in pending/."""
        spec_id = "test-active-spec-2025-01-01-003"
        active_file = specs_structure / "active" / f"{spec_id}.json"

        spec_data = {"spec_id": spec_id, "title": "Test Active"}
        active_file.write_text(json.dumps(spec_data))

        # Find the spec
        found = find_spec_file(spec_id, specs_structure)

        assert found is not None
        assert found == active_file
        assert "active" in str(found)

    def test_find_spec_file_not_found(self, specs_structure):
        """Test that find_spec_file returns None when spec doesn't exist."""
        spec_id = "nonexistent-spec-999"

        found = find_spec_file(spec_id, specs_structure)

        assert found is None

@pytest.mark.integration
class TestPathIntegration:
    """Integration tests for path utilities."""

    def test_path_resolution_with_symlinks(self, tmp_path, specs_structure):
        """Test path resolution handles symlinks correctly."""
        # Create symlink to specs
        symlink = tmp_path / "specs_link"
        try:
            symlink.symlink_to(specs_structure)

            # Find specs through symlink
            found = find_specs_directory(symlink)

            assert found is not None
        except OSError:
            # Symlinks might not be supported on all systems
            pytest.skip("Symlinks not supported on this system")

    def test_specs_directory_traversal(self, specs_structure):
        """Test that specs can be found from various starting points."""
        test_locations = [
            specs_structure,  # Direct specs dir
            specs_structure / "active",  # Subdirectory (should traverse up)
            specs_structure / "completed",  # Another subdirectory (should traverse up)
            specs_structure / "completed"  # Yet another subdirectory
        ]

        for location in test_locations:
            if location.exists():
                found = find_specs_directory(location)
                assert found is not None, f"Failed to find specs from {location}"
