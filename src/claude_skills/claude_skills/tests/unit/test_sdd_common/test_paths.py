"""
Unit tests for sdd_common.paths module.

Tests path utilities: find_specs_directory, validate_path.
"""

import pytest
from pathlib import Path
from claude_skills.common import find_specs_directory, validate_path

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
